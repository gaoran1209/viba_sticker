import discord
import logging
import asyncio
import io
import time
from discord import app_commands
from discord.ext import commands
from config import DISCORD_TOKEN
from ai_service import AIService
from presets import STICKER_PRESETS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("viba_sticker_bot")

class VibaStickerBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.messages = True
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)
        self.ai_service = AIService()

    async def setup_hook(self):
        await self.tree.sync()
        logger.info("Synced slash commands.")

    async def on_ready(self):
        logger.info(f'Logged in as {self.user} (ID: {self.user.id})')
        logger.info('------')

    async def close(self):
        await self.ai_service.close()
        await super().close()

    async def on_message(self, message):
        # Ignore messages from self
        if message.author == self.user:
            return

        # Check if bot is mentioned (Legacy Support)
        if self.user in message.mentions:
            await message.reply("💡 Please use the `/post` command to generate stickers for a better experience!")
            return

client = VibaStickerBot()

# Prepare choices from presets
STYLE_CHOICES = [
    app_commands.Choice(name=name, value=name)
    for name in STICKER_PRESETS.keys()
]

async def send_progress_update(interaction: discord.Interaction):
    """Sends a progress update if generation takes too long."""
    try:
        await asyncio.sleep(15)
        # Check if the interaction is still valid and not already replied to with the final result
        await interaction.followup.send("⏳ Still processing your sticker, thank you for your patience!", ephemeral=True)
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logger.debug(f"Progress update skipped: {e}")

@client.tree.command(name="post", description="Upload a photo and choose a style to generate a sticker")
@app_commands.describe(photo="Please upload your photo", style="Please choose a style")
@app_commands.choices(style=STYLE_CHOICES)
async def post(interaction: discord.Interaction, photo: discord.Attachment, style: app_commands.Choice[str]):
    # Validation
    if not photo.content_type or not photo.content_type.startswith('image/'):
        await interaction.response.send_message("❌ Please upload a valid image file!", ephemeral=True)
        return

    # Defer the response since generation takes time
    await interaction.response.defer(thinking=True)
    
    # Start progress update task
    progress_task = asyncio.create_task(send_progress_update(interaction))
    
    start_time = time.time()
    try:
        # Get the selected preset prompt
        selected_style_name = style.value
        sticker_prompt = STICKER_PRESETS.get(selected_style_name)
        
        if not sticker_prompt:
            await interaction.followup.send(f"❌ Style not found: {selected_style_name}", ephemeral=True)
            return

        # 1. Download Image
        logger.info(f"Downloading image from {photo.url}...")
        image_bytes = await client.ai_service.download_image(photo.url)
        download_time = time.time() - start_time
        
        # 2. Generate Sticker
        logger.info(f"Generating sticker with style: {selected_style_name}")
        gen_start = time.time()
        generated_image_bytes = await client.ai_service.generate_sticker(sticker_prompt, image_bytes, photo.content_type)
        gen_time = time.time() - gen_start
        
        # 3. Send Result
        logger.info(f"Sending result... (Total time: {time.time() - start_time:.2f}s)")
        with io.BytesIO(generated_image_bytes) as image_file:
            image_file.seek(0)
            file = discord.File(image_file, filename="sticker.png")
            await interaction.followup.send(
                content=f"✨ **{selected_style_name}** sticker generated!\nSubmitted by {interaction.user.mention}", 
                file=file
            )
        
        logger.info(f"Task completed successfully. (DL: {download_time:.2f}s, AI: {gen_time:.2f}s)")

    except Exception as e:
        logger.error(f"Error processing slash command: {e}")
        error_message = f"❌ Generation failed. Error: {str(e)}"
        if "429" in str(e):
            error_message = "❌ Rate limit exceeded. Please try again later."
        elif "blocked" in str(e).lower():
            error_message = "❌ Image generation was blocked by safety filters. Please try another image."
        
        try:
            await interaction.followup.send(content=error_message)
        except:
            pass
    finally:
        # Cancel progress task if it's still running
        if not progress_task.done():
            progress_task.cancel()

if __name__ == "__main__":
    if not DISCORD_TOKEN:
        logger.error("DISCORD_TOKEN is missing in environment variables.")
        exit(1)
        
    client.run(DISCORD_TOKEN)
