# ✨ Viba Sticker Bot

A Discord bot that transforms your photos into stunning AI-generated stickers using Google Gemini's image generation capabilities.

![Python](https://img.shields.io/badge/Python-3.10-3776AB?logo=python&logoColor=white)
![Discord.py](https://img.shields.io/badge/discord.py-2.3+-5865F2?logo=discord&logoColor=white)
![Gemini](https://img.shields.io/badge/Google_Gemini-AI-4285F4?logo=google&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

## 🎨 What It Does

Upload any photo, choose a creative style, and let Gemini AI generate a unique sticker for you — all within Discord.

### Available Styles

| Style | Description |
| :--- | :--- |
| **Inner Animal** | Pairs your character with a random animal in an avant-garde editorial style |
| **Raw Nature** | Full fashion editorial with CRT film effects, grain, and Y2K aesthetics |
| **OOTD** | Deconstructed "paper doll" fashion layout with oversized head aesthetic |
| **FishView #35mm** | Vintage 35mm fisheye lens shot with analog grain and chromatic aberration |
| **Selfcast** | Fashion editorial with vintage CRT television interaction |

## ⚡ Features

- **Slash Commands** — Clean `/post` interface with interactive style picker
- **Dual-Model Fallback** — Primary (`gemini-3.1-flash-image-preview`) with automatic fallback to `gemini-2.5-flash-image` for high reliability
- **Image Optimization** — Auto-compresses and resizes uploads for faster generation
- **Smart Retries** — Quick retry on fast failures, multi-attempt fallback strategy
- **Safety Handling** — Graceful error messages for rate limits and content filters

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- [Discord Bot Token](https://discord.com/developers/applications)
- [Google Gemini API Key](https://aistudio.google.com/apikey)

### Installation

```bash
# Clone the repo
git clone https://github.com/gaoran1209/viba_sticker.git
cd viba_sticker

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your tokens
```

### Configuration

Create a `.env` file in the project root:

```env
# Required
DISCORD_TOKEN=your_discord_bot_token
GEMINI_API_KEY=your_gemini_api_key

# Optional (defaults shown)
GEMINI_IMAGE_MODEL=gemini-3.1-flash-image-preview
GEMINI_IMAGE_MODEL_FALLBACK=gemini-2.5-flash-image
```

### Run

```bash
python bot.py
```

## 💬 Usage

1. Invite the bot to your Discord server
2. Use `/post` in any channel
3. Upload a photo and select a style from the dropdown
4. Wait a few seconds — your sticker will appear! ✨

## 🏗️ Architecture

```
viba_sticker/
├── bot.py            # Discord bot entry point & slash command handler
├── ai_service.py     # Gemini API client with fallback & retry logic
├── presets.py        # Style presets and prompt templates
├── config.py         # Environment variable management
├── requirements.txt  # Python dependencies
├── Procfile          # Railway process definition
├── runtime.txt       # Python version specification
├── DEPLOY.md         # Detailed deployment guide
└── .github/
    └── workflows/    # GitHub Actions CI/CD
```

### How It Works

```
User uploads photo ──► Image optimization (resize/compress)
                              │
                              ▼
                       Gemini API (Primary Model)
                              │
                     ┌────────┴────────┐
                     │ Success?        │
                     │                 │
                    Yes               No
                     │                 │
                     ▼                 ▼
              Return sticker   Quick retry / Fallback model
                                       │
                                       ▼
                                Return sticker or error
```

## 📦 Deployment

### Docker on EC2 (Recommended)

The project supports automated deployment via Docker + GitHub Actions.

👉 See [DEPLOY.md](DEPLOY.md) for the full guide, including:
- EC2 server setup
- Docker Compose configuration
- CI/CD workflow (push to `main` → auto-deploy)
- Server maintenance commands

### Railway (Legacy)

1. Connect your GitHub repo to [Railway](https://railway.app)
2. Set `DISCORD_TOKEN` and `GEMINI_API_KEY` in Railway's environment settings
3. Railway auto-detects the `Procfile` and starts the worker

## 🛠️ Tech Stack

| Component | Technology |
| :--- | :--- |
| Runtime | Python 3.10 |
| Discord SDK | discord.py ≥ 2.3.0 |
| HTTP Client | aiohttp ≥ 3.9.0 |
| AI Backend | Google Gemini API |
| Image Processing | Pillow ≥ 10.0.0 |
| Deployment | Docker + GitHub Actions |

## 📄 License

MIT
