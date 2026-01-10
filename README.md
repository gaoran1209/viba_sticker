# viba_sticker

Discord bot that turns your images into stickers using Gemini AI.

## Features

- **Prompt + Image Input**: Refines your prompt and uses your image to generate a sticker.
- **Gemini Powered**: Uses `gemini-3-pro-preview` for prompt refinement and `gemini-3-pro-image-preview` for image generation.
- **Railway Ready**: Easy deployment on Railway.

## Setup

1. **Clone the repository**
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure Environment**:
   - Copy `.env.example` to `.env`
   - Fill in `DISCORD_TOKEN` and `GEMINI_API_KEY`
4. **Run**:
   ```bash
   python bot.py
   ```

## Usage

1. Upload an image to a Discord channel where the bot is present.
2. In the message, mention the bot (`@viba_sticker`) and add a prompt (e.g., "Make this cyberpunk").
3. The bot will reply with the generated sticker.

## Deployment (Railway)

1. Connect your GitHub repository to Railway.
2. Add the environment variables (`DISCORD_TOKEN`, `GEMINI_API_KEY`) in Railway settings.
3. Railway should automatically detect the `Procfile` and start the worker.
