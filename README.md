# viba_sticker

Discord bot that turns your images into stylized stickers using Google's Gemini AI.

## Features

- **Slash Command Support**: Easy-to-use `/post` command with interactive UI.
- **Style Presets**: Choose from a variety of curated styles (e.g., OOTD, Cyberpunk, Watercolor) to instantly transform your photos.
- **Smart AI Generation**: 
  - Primary: Uses `gemini-3-pro-image-preview` for high-quality generation.
  - Fallback: Automatically switches to `gemini-2.5-flash-image` if the primary model is slow or unavailable, ensuring reliability.
- **Performance Optimized**: 
  - Automatic image compression/resizing to reduce latency.
  - Connection pooling and intelligent timeouts.
  - Real-time progress feedback for users.
- **Railway Ready**: Optimized for easy deployment on Railway.

## Setup

1. **Clone the repository**
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: Includes `Pillow` for image processing and `PyNaCl` for Discord voice support (to suppress warnings).*

3. **Configure Environment**:
   - Create a `.env` file (or set variables in your deployment platform).
   - Required Variables:
     - `DISCORD_TOKEN`: Your Discord Bot Token.
     - `GEMINI_API_KEY`: Your Google Gemini API Key.
   - Optional Variables (Defaults provided in code):
     - `GEMINI_IMAGE_MODEL`: Default `gemini-3-pro-image-preview`
     - `GEMINI_IMAGE_MODEL_FALLBACK`: Default `gemini-2.5-flash-image`

4. **Run**:
   ```bash
   python bot.py
   ```

## Usage

1. **Invite the bot** to your server.
2. Type **`/post`** in any channel where the bot has access.
3. **Upload a photo** when prompted.
4. **Select a Style** from the dropdown menu (the list is dynamically loaded from presets).
5. The bot will process your image and reply with a generated sticker!

## Deployment

This project supports multiple deployment methods:

### Option 1: Docker on EC2 (Recommended)
We use Docker for isolation and GitHub Actions for automated deployment.
👉 **[See detailed DEPLOY.md guide](DEPLOY.md)**

### Option 2: Railway (Legacy)
1. Connect your GitHub repository to Railway.
2. Add the environment variables (`DISCORD_TOKEN`, `GEMINI_API_KEY`) in Railway settings.
3. Railway should automatically detect the `Procfile` and start the worker.

## Project Structure

- `bot.py`: Main entry point, handles Discord interactions and slash commands.
- `ai_service.py`: Handles Gemini API communication, image processing, and fallback logic.
- `presets.py`: Defines the available sticker styles and their corresponding prompts.
- `config.py`: Environment variable management.
