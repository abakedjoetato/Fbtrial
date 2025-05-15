"""
Discord Bot Main Entry Point

This script serves as the entry point for the Discord bot when launched from Replit.
It will start both the bot process and a simple status web page.
"""

import os
import sys
import logging
from app_enhanced import start_server

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log')
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Main entry point for the Discord bot"""
    logger.info("Starting Discord bot via app_enhanced.py")
    
    # Verify required environment variables
    if not os.environ.get("DISCORD_TOKEN"):
        logger.error("DISCORD_TOKEN not found in environment variables!")
        print("ERROR: DISCORD_TOKEN not found in environment variables!")
        return 1
        
    # Start the bot and web server
    start_server()
    return 0

if __name__ == "__main__":
    sys.exit(main())