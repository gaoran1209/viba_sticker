import aiohttp
import base64
import json
import logging
import asyncio
import time
import io
from PIL import Image
from config import GEMINI_API_KEY, GEMINI_IMAGE_MODEL, GEMINI_IMAGE_MODEL_FALLBACK

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.api_key = GEMINI_API_KEY
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
        self._session = None

    async def get_session(self):
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def download_image(self, url: str) -> bytes:
        """Downloads image from a URL."""
        session = await self.get_session()
        try:
            async with session.get(url, timeout=30) as response:
                if response.status == 200:
                    return await response.read()
                else:
                    raise Exception(f"Failed to download image. Status: {response.status}")
        except Exception as e:
            logger.error(f"Error downloading image: {e}")
            raise e

    def optimize_image(self, image_bytes: bytes, max_size=(1024, 1024), quality=85) -> bytes:
        """Resizes and compresses image to reduce payload size."""
        try:
            img = Image.open(io.BytesIO(image_bytes))
            # Convert to RGB if necessary for JPEG
            if img.mode in ("RGBA", "P"):
                # Use white background for transparent images when converting to JPEG
                background = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "RGBA":
                    background.paste(img, mask=img.split()[3])
                else:
                    background.paste(img)
                img = background
            elif img.mode != "RGB":
                img = img.convert("RGB")
            
            # Thumbnail keeps aspect ratio
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            output = io.BytesIO()
            img.save(output, format="JPEG", quality=quality, optimize=True)
            optimized_bytes = output.getvalue()
            
            logger.info(f"Image optimized: {len(image_bytes)/1024:.1f}KB -> {len(optimized_bytes)/1024:.1f}KB")
            return optimized_bytes
        except Exception as e:
            logger.warning(f"Failed to optimize image: {e}. Using original.")
            return image_bytes

    async def _call_generate_api(self, model: str, payload: dict, timeout: int = 60) -> bytes:
        url = f"{self.base_url}/{model}:generateContent?key={self.api_key}"
        
        session = await self.get_session()
        client_timeout = aiohttp.ClientTimeout(total=timeout)
        
        try:
            async with session.post(url, json=payload, timeout=client_timeout) as response:
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
                                return await self.download_image(text_content)
                            else:
                                logger.info(f"Received text instead of image: {text_content}")
                    
                    keys_found = [list(p.keys()) for p in parts]
                    logger.error(f"No image data found. Parts keys: {keys_found}. Full response: {json.dumps(data)}")
                    raise Exception("No image data found in response")
                    
                except Exception as e:
                    logger.error(f"Failed to parse image response: {e}")
                    if "Full response" not in str(e):
                        logger.debug(f"Response data: {data}")
                    raise e
        except asyncio.TimeoutError:
            logger.error(f"Timeout calling Gemini API ({model}) after {timeout}s")
            raise Exception(f"Timeout calling Gemini API ({model})")
        except Exception as e:
            logger.error(f"Error calling Gemini API ({model}): {e}")
            raise e

    async def generate_sticker(self, sticker_prompt: str, reference_image_bytes: bytes, mime_type: str = "image/png") -> bytes:
        """
        Calls Gemini to generate the sticker with optimized timeout and fallback.
        """
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not set")
        
        # Optimize image before sending to API
        optimized_image_bytes = self.optimize_image(reference_image_bytes)
        image_b64 = base64.b64encode(optimized_image_bytes).decode('utf-8')
        
        payload = {
            "contents": [{
                "parts": [
                    {"text": f"Generate a sticker based on this prompt: {sticker_prompt}"},
                    {
                        "inlineData": {
                            "mimeType": "image/jpeg", # Since we optimized to JPEG
                            "data": image_b64
                        }
                    }
                ]
            }],
            "generationConfig": {
                "responseModalities": ["TEXT", "IMAGE"]
            }
        }

        # Attempt 1: Primary Model with short timeout
        primary_timeout = 40 
        start_time = time.time()
        try:
            logger.info(f"Attempt 1: Generating with {GEMINI_IMAGE_MODEL} (timeout={primary_timeout}s)...")
            return await self._call_generate_api(GEMINI_IMAGE_MODEL, payload, timeout=primary_timeout)
        except Exception as e:
            elapsed = time.time() - start_time
            logger.warning(f"Attempt 1 failed ({GEMINI_IMAGE_MODEL}): {e}. Elapsed: {elapsed:.2f}s")
            
            # If it failed quickly (e.g. rate limit), try one more time or fallback
            if elapsed < 5:
                try:
                    logger.info(f"Attempt 2: Quick retry with {GEMINI_IMAGE_MODEL}...")
                    return await self._call_generate_api(GEMINI_IMAGE_MODEL, payload, timeout=primary_timeout)
                except Exception as e2:
                    logger.warning(f"Attempt 2 failed: {e2}. Falling back to {GEMINI_IMAGE_MODEL_FALLBACK}...")
            else:
                logger.warning(f"Attempt 1 took > 5s or timed out, falling back to {GEMINI_IMAGE_MODEL_FALLBACK}...")

        # Final Attempt: Fallback Model
        fallback_timeout = 60
        try:
            logger.info(f"Attempt 3: Generating with {GEMINI_IMAGE_MODEL_FALLBACK} (timeout={fallback_timeout}s)...")
            return await self._call_generate_api(GEMINI_IMAGE_MODEL_FALLBACK, payload, timeout=fallback_timeout)
        except Exception as e:
            logger.error(f"All attempts failed. Last error: {e}")
            raise Exception(f"Failed to generate sticker. Please try again later.")
