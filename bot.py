import discord
import logging
import asyncio
import io
import re
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

    async def on_message(self, message):
        # Ignore messages from self
        if message.author == self.user:
            return

        # Check if bot is mentioned (Legacy Support)
        if self.user in message.mentions:
            # Only process if it's NOT a slash command interaction (which are handled separately)
            # However, message.mentions usually come from normal text messages.
            # We'll keep this for legacy text-based support if needed, or we can guide users to slash commands.
            
            # Simple reply to guide user to slash command
            await message.reply("💡 请使用 `/post` 指令来生成贴纸，体验更好哦！")
            return

client = VibaStickerBot()

# Prepare choices from presets
STYLE_CHOICES = [
    app_commands.Choice(name=name, value=name)
    for name in STICKER_PRESETS.keys()
]

@client.tree.command(name="post", description="上传图片并选择风格生成贴纸")
@app_commands.describe(photo="请上传你的图片", style="请选择图片风格")
@app_commands.choices(style=STYLE_CHOICES)
async def post(interaction: discord.Interaction, photo: discord.Attachment, style: app_commands.Choice[str]):
    # Validation
    if not photo.content_type.startswith('image/'):
        await interaction.response.send_message("❌ 请上传图片文件！", ephemeral=True)
        return

    # Defer the response since generation takes time
    await interaction.response.defer(thinking=True)

    try:
        # Get the selected preset prompt
        selected_style_name = style.value
        sticker_prompt = STICKER_PRESETS.get(selected_style_name)
        
        if not sticker_prompt:
            await interaction.followup.send(f"❌ 未找到风格: {selected_style_name}", ephemeral=True)
            return

        # 1. Download Image
        logger.info(f"Downloading image from {photo.url}...")
        image_bytes = await client.ai_service.download_image(photo.url)
        
        # 2. Generate Sticker
        logger.info(f"Generating sticker with style: {selected_style_name}")
        generated_image_bytes = await client.ai_service.generate_sticker(sticker_prompt, image_bytes, photo.content_type)
        
        # 3. Send Result
        logger.info("Sending result...")
        with io.BytesIO(generated_image_bytes) as image_file:
            image_file.seek(0)
            file = discord.File(image_file, filename="sticker.png")
            await interaction.followup.send(
                content=f"✨ **{selected_style_name}** 风格贴纸已生成！\n由 {interaction.user.mention} 提交", 
                file=file
            )
        
        logger.info("Task completed successfully.")

    except Exception as e:
        logger.error(f"Error processing slash command: {e}")
        error_message = f"❌ 制作失败，请稍后再试。错误信息: {str(e)}"
        if "429" in str(e):
            error_message = "❌ 制作失败，请求速率过高 (Rate Limit)，请稍后再试。"
        
        await interaction.followup.send(content=error_message)

if __name__ == "__main__":
    if not DISCORD_TOKEN:
        logger.error("DISCORD_TOKEN is missing in environment variables.")
        exit(1)
        
    client.run(DISCORD_TOKEN)
