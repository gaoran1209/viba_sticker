import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Model names
GEMINI_TEXT_MODEL = os.getenv("GEMINI_TEXT_MODEL", "gemini-3-pro-preview")
GEMINI_IMAGE_MODEL = os.getenv("GEMINI_IMAGE_MODEL", "gemini-3-pro-image-preview")
GEMINI_IMAGE_MODEL_FALLBACK = os.getenv("GEMINI_IMAGE_MODEL_FALLBACK", "gemini-2.5-flash-image")

if not DISCORD_TOKEN:
    print("Warning: DISCORD_TOKEN is not set.")

if not GEMINI_API_KEY:
    print("Warning: GEMINI_API_KEY is not set.")
