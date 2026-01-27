import aiohttp
import base64
import json
import logging
import asyncio
import time
from config import GEMINI_API_KEY, GEMINI_IMAGE_MODEL, GEMINI_IMAGE_MODEL_FALLBACK

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.api_key = GEMINI_API_KEY
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"

    async def download_image(self, url: str) -> bytes:
        """Downloads image from a URL."""
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.read()
                else:
                    raise Exception(f"Failed to download image. Status: {response.status}")

    async def _call_generate_api(self, model: str, payload: dict) -> bytes:
        url = f"{self.base_url}/{model}:generateContent?key={self.api_key}"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    text = await response.text()
                    logger.error(f"Generate sticker failed ({model}): {text}")
                    raise Exception(f"Gemini API Error (Generate {model}): {response.status}")
                
                data = await response.json()
                
                try:
                    candidates = data.get("candidates", [])
                    if not candidates:
                        prompt_feedback = data.get("promptFeedback", {})
                        block_reason = prompt_feedback.get("blockReason")
                        if block_reason:
                            raise Exception(f"Generation blocked: {block_reason}")
                        logger.error(f"No candidates returned. Full response: {json.dumps(data)}")
                        raise Exception("No candidates returned from Gemini API")

                    parts = candidates[0].get("content", {}).get("parts", [])
                    for part in parts:
                        # Check for both snake_case (Python SDK style) and camelCase (JSON API style)
                        if "inline_data" in part:
                            b64_data = part["inline_data"]["data"]
                            return base64.b64decode(b64_data)
                        
                        if "inlineData" in part:
                            data_obj = part["inlineData"]
                            b64_data = data_obj.get("data")
                            if b64_data:
                                return base64.b64decode(b64_data)

                        if "text" in part:
                            text_content = part["text"]
                            if text_content.startswith("http"):
                                # It might be a URL
                                return await self.download_image(text_content)
                            else:
                                logger.info(f"Received text instead of image: {text_content}")
                    
                    # Log available keys to help debugging
                    keys_found = [list(p.keys()) for p in parts]
                    logger.error(f"No image data found. Parts keys: {keys_found}. Full response: {json.dumps(data)}")
                    raise Exception("No image data found in response")
                    
                except Exception as e:
                    logger.error(f"Failed to parse image response: {e}")
                    # Only log full response if not already logged
                    if "Full response" not in str(e):
                        logger.debug(f"Response data: {data}")
                    raise e

    async def generate_sticker(self, sticker_prompt: str, reference_image_bytes: bytes, mime_type: str = "image/png") -> bytes:
        """
        Calls gemini-3-pro-image-preview to generate the sticker.
        If it fails within 10s, retries immediately.
        If it fails again or takes longer than 10s, falls back to gemini-2.5-flash-image.
        """
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not set")
        
        image_b64 = base64.b64encode(reference_image_bytes).decode('utf-8')
        
        payload = {
            "contents": [{
                "parts": [
                    {"text": f"Generate a sticker based on this prompt: {sticker_prompt}"},
                    {
                        "inlineData": {
                            "mimeType": mime_type,
                            "data": image_b64
                        }
                    }
                ]
            }],
            "generationConfig": {
                "responseModalities": ["TEXT", "IMAGE"]
            }
        }

        # Attempt 1: Primary Model
        start_time = time.time()
        try:
            logger.info(f"Attempt 1: Generating with {GEMINI_IMAGE_MODEL}...")
            return await self._call_generate_api(GEMINI_IMAGE_MODEL, payload)
        except Exception as e:
            elapsed = time.time() - start_time
            logger.warning(f"Attempt 1 failed: {e}. Elapsed: {elapsed:.2f}s")
            
            # Condition for Attempt 2: If failure happened within 10 seconds
            if elapsed < 10:
                try:
                    logger.info(f"Attempt 2: Retrying with {GEMINI_IMAGE_MODEL} (Quick failure detected)...")
                    return await self._call_generate_api(GEMINI_IMAGE_MODEL, payload)
                except Exception as e2:
                    logger.warning(f"Attempt 2 failed: {e2}. Falling back to {GEMINI_IMAGE_MODEL_FALLBACK}...")
            else:
                logger.warning(f"Attempt 1 took > 10s, skipping retry and falling back to {GEMINI_IMAGE_MODEL_FALLBACK}...")

        # Attempt 3: Fallback Model
        try:
            logger.info(f"Attempt 3: Generating with {GEMINI_IMAGE_MODEL_FALLBACK}...")
            return await self._call_generate_api(GEMINI_IMAGE_MODEL_FALLBACK, payload)
        except Exception as e:
            logger.error(f"All attempts failed. Last error: {e}")
            raise Exception(f"Failed to generate sticker after retries and fallback. Last error: {e}")
