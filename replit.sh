#!/bin/bash
# Script to start the Discord bot from the Replit run button

echo "========================================"
echo "  STARTING DISCORD BOT"
echo "  $(date)"
echo "========================================"

# Install required dependencies
echo "Installing dependencies..."
pip install python-dotenv motor pymongo dnspython paramiko matplotlib numpy pandas psutil aiohttp aiofiles pytz asyncio asyncssh pillow pydantic requests flask py-cord==2.6.1

# Set the Python path to include the current directory
export PYTHONPATH=".:$PYTHONPATH"

# Run the bot
echo "Starting bot with main.py..."
python main.py