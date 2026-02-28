# Implementation Plan for viba_sticker

This plan outlines the steps to build the `viba_sticker` Discord bot as per the PRD.

## 1. Project Initialization & Configuration
- **Create `requirements.txt`**: Define dependencies (`discord.py`, `aiohttp`, `python-dotenv`).
- **Create `.env`**: Setup template for environment variables (`DISCORD_TOKEN`, `GEMINI_API_KEY`).
- **Create `config.py`**: A centralized configuration module to load and validate environment variables.

## 2. AI Service Module (`ai_service.py`)
- Implement a class `AIService` to handle interactions with the Gemini models.
- **Method `refine_prompt(user_prompt: str, image_url: str) -> str`**:
    - Uses `aiohttp` to call `gemini-3-pro-preview`.
    - Constructs the payload to ask the model to convert the user's request into a stable diffusion/sticker-style prompt.
- **Method `generate_sticker(prompt: str, image_url: str) -> bytes`**:
    - Uses `aiohttp` to call `gemini-3.1-flash-image-preview`.
    - Sends the refined prompt and the original image URL.
    - Returns the binary image data.

## 3. Discord Bot Implementation (`bot.py`)
- Initialize `discord.Client` with appropriate intents (messages, message_content).
- **Event `on_ready`**: Log successful login.
- **Event `on_message`**:
    - **Validation**: Check if the bot is mentioned and if there is an image attachment.
    - **UX**: Send a "⏳ Making your sticker..." temporary message.
    - **Orchestration**:
        - Extract clean text from the message (removing the mention).
        - Call `AIService.refine_prompt`.
        - Call `AIService.generate_sticker`.
    - **Response**: Send the generated image as a reply and delete the temporary message.
    - **Error Handling**: Catch exceptions (timeouts, API errors) and inform the user.

## 4. Deployment Preparation
- **Create `Procfile`** (Optional but good for Railway): Define the worker command (`python bot.py`).
- **Create `README.md`**: Instructions for local setup and deployment.

## 5. Verification
- Run the bot locally (requires valid tokens).
- Mock the API calls if tokens are not available immediately to verify the flow (optional, based on available credentials).
