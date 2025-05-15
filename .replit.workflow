[workflow.discord_bot]
run = "python start_discord_bot.py"
onBoot = "pip install python-dotenv motor pymongo dnspython paramiko matplotlib numpy pandas psutil aiohttp aiofiles pytz asyncio asyncssh pillow pydantic requests flask py-cord==2.6.1"