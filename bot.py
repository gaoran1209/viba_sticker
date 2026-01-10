import discord
import logging
import asyncio
import io
import re
from config import DISCORD_TOKEN
from ai_service import AIService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("viba_sticker_bot")

class VibaStickerBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.messages = True
        intents.message_content = True
        super().__init__(intents=intents)
        self.ai_service = AIService()

    async def on_ready(self):
        logger.info(f'Logged in as {self.user} (ID: {self.user.id})')
        logger.info('------')

    async def on_message(self, message):
        # Ignore messages from self
        if message.author == self.user:
            return

        # Check if bot is mentioned
        if self.user in message.mentions:
            logger.info(f"Received request from {message.author}: {message.content}")
            
            # Validation: Check for attachments
            if not message.attachments:
                await message.reply("请上传图片并 @我。")
                return

            attachment = message.attachments[0]
            if not attachment.content_type.startswith('image/'):
                await message.reply("请确保附件是图片格式。")
                return

            # Clean content: Remove mention
            # <@123456> or <@!123456>
            content = message.content
            mention_pattern = f"<@!?{self.user.id}>"
            cleaned_prompt = re.sub(mention_pattern, "", content).strip()
            
            if not cleaned_prompt:
                await message.reply("请输入提示词。")
                return

            # Send processing message
            processing_msg = await message.reply("⏳ 正在为您制作 Sticker，请稍候...")

            try:
                # 1. Download Image
                logger.info("Downloading image...")
                image_bytes = await self.ai_service.download_image(attachment.url)
                
                # 2. Refine Prompt
                logger.info("Refining prompt...")
                sticker_prompt = await self.ai_service.refine_prompt(cleaned_prompt, image_bytes, attachment.content_type)
                logger.info(f"Refined Prompt: {sticker_prompt}")

                # 3. Generate Sticker
                logger.info("Generating sticker...")
                generated_image_bytes = await self.ai_service.generate_sticker(sticker_prompt, image_bytes, attachment.content_type)
                
                # 4. Send Result
                logger.info("Sending result...")
                with io.BytesIO(generated_image_bytes) as image_file:
                    image_file.seek(0)
                    file = discord.File(image_file, filename="sticker.png")
                    await message.reply(content=f"✨ 您的贴纸已生成！", file=file)
                
                # Delete processing message
                await processing_msg.delete()
                logger.info("Task completed successfully.")

            except Exception as e:
                logger.error(f"Error processing request: {e}")
                error_message = f"❌ 制作失败，请稍后再试。错误信息: {str(e)}"
                # If it's a known API error, we might want to parse it better, but this is a catch-all
                if "429" in str(e):
                    error_message = "❌ 制作失败，请求速率过高 (Rate Limit)，请稍后再试。"
                
                await processing_msg.edit(content=error_message)

if __name__ == "__main__":
    if not DISCORD_TOKEN:
        logger.error("DISCORD_TOKEN is missing in environment variables.")
        exit(1)
        
    client = VibaStickerBot()
    client.run(DISCORD_TOKEN)
