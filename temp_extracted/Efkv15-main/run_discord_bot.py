"""
Discord Bot Runner Script

This script runs the Discord bot directly, handling imports and setup.
"""
import os
import sys
import logging
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("discord_runner")

def run_bot():
    """
    Main function to run the Discord bot
    """
    try:
        # Set up environment for the bot
        logger.info("Starting Discord bot...")
        
        # Add the pythonlibs path if we're in Replit
        pythonlibs_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.pythonlibs/lib/python3.11/site-packages')
        if os.path.exists(pythonlibs_path) and pythonlibs_path not in sys.path:
            sys.path.insert(0, pythonlibs_path)
            logger.info(f"Added {pythonlibs_path} to Python path")
        
        # Import the bot module
        logger.info("Importing bot module...")
        import bot
        import asyncio
        
        # Run the bot (this will be asynchronous)
        logger.info("Starting bot...")
        # Create an event loop and run the bot
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(bot.main())
        except KeyboardInterrupt:
            logger.info("Bot stopped by keyboard interrupt")
        finally:
            loop.close()
        
    except ImportError as e:
        logger.error(f"Import error starting bot: {e}")
        logger.error(traceback.format_exc())
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    run_bot()