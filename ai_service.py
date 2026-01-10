import aiohttp
import base64
import json
import logging
from config import GEMINI_API_KEY, GEMINI_TEXT_MODEL, GEMINI_IMAGE_MODEL

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

    async def refine_prompt(self, user_prompt: str, image_bytes: bytes, mime_type: str = "image/png") -> str:
        """
        Calls gemini-3-pro-preview to refine the user prompt into a sticker prompt.
        """
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not set")

        url = f"{self.base_url}/{GEMINI_TEXT_MODEL}:generateContent?key={self.api_key}"
        
        # Convert image to base64
        image_b64 = base64.b64encode(image_bytes).decode('utf-8')
        
        payload = {
            "contents": [{
                "parts": [
                    {"text": f"You are a sticker design expert. Please convert the following user request and the attached image context into a detailed stable diffusion prompt for generating a high-quality sticker. The style should be consistent with sticker art (die-cut, white border, vector style, expressive). \n\nUser Request: {user_prompt}\n\nOutput only the prompt text, nothing else."},
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": image_b64
                        }
                    }
                ]
            }]
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    text = await response.text()
                    logger.error(f"Refine prompt failed: {text}")
                    raise Exception(f"Gemini API Error (Refine): {response.status}")
                
                data = await response.json()
                try:
                    refined_prompt = data["candidates"][0]["content"]["parts"][0]["text"]
                    return refined_prompt.strip()
                except (KeyError, IndexError) as e:
                    logger.error(f"Unexpected response format: {data}")
                    raise Exception("Failed to parse Gemini response")

    async def generate_sticker(self, sticker_prompt: str, reference_image_bytes: bytes, mime_type: str = "image/png") -> bytes:
        """
        Calls gemini-3-pro-image-preview to generate the sticker.
        Assuming it accepts text + reference image and returns image data (base64) or URL.
        """
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not set")

        url = f"{self.base_url}/{GEMINI_IMAGE_MODEL}:generateContent?key={self.api_key}"
        
        image_b64 = base64.b64encode(reference_image_bytes).decode('utf-8')
        
        # Constructing payload. 
        # Note: This schema assumes the image model accepts the same input structure as the text model
        # but returns image data.
        payload = {
            "contents": [{
                "parts": [
                    {"text": f"Generate a sticker based on this prompt: {sticker_prompt}"},
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": image_b64
                        }
                    }
                ]
            }]
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    text = await response.text()
                    logger.error(f"Generate sticker failed: {text}")
                    raise Exception(f"Gemini API Error (Generate): {response.status}")
                
                data = await response.json()
                
                # Try to extract image from response. 
                # Structure might be candidates -> content -> parts -> inline_data (if base64)
                # Or it might contain a URL.
                try:
                    # Check for inline data (Base64)
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        for part in parts:
                            if "inline_data" in part:
                                b64_data = part["inline_data"]["data"]
                                return base64.b64decode(b64_data)
                            # Sometimes images are returned as separate objects or specific fields
                            # If the model returns a text url?
                            if "text" in part:
                                text_content = part["text"]
                                if text_content.startswith("http"):
                                    # It might be a URL
                                    return await self.download_image(text_content)
                    
                    raise Exception("No image data found in response")
                    
                except Exception as e:
                    logger.error(f"Failed to parse image response: {e}")
                    logger.debug(f"Response data: {data}")
                    raise e
