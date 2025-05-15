#!/usr/bin/env python3
"""
Run script for Replit

This script serves as the entry point for running the Discord bot in the Replit workflow.
It ensures proper environment setup before launching the bot.
"""

import os
import sys
import logging
import asyncio
import traceback
import dotenv

# Load environment variables from .env file
dotenv.load_dotenv()

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

def run_bot():
    """Run the Discord bot using asyncio"""
    logger.info("Starting Discord bot...")
    
    # Verify required environment variables
    if not os.environ.get("DISCORD_TOKEN"):
        logger.error("DISCORD_TOKEN not found in environment variables!")
        print("ERROR: DISCORD_TOKEN not found in environment variables!")
        sys.exit(1)
    
    try:
        # Import bot module here to avoid circular imports
        from bot import main
        
        # Run the bot
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by KeyboardInterrupt")
    except ImportError as e:
        logger.error(f"Failed to import bot module: {str(e)}")
        logger.error(traceback.format_exc())
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error in bot: {str(e)}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    run_bot()