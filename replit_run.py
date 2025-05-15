"""
Replit Run Script for Discord Bot

This script is the direct entry point for running the Discord bot on Replit.
It handles both the bot process and web interface.
"""

import os
import sys
import logging
import subprocess
import time
import signal
import threading
import atexit

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("bot.log")
    ]
)
logger = logging.getLogger(__name__)

# Global variables
bot_process = None

def start_bot_process():
    """Start the Discord bot process"""
    global bot_process
    
    # Kill any existing process
    if bot_process and bot_process.poll() is None:
        logger.info("Stopping existing bot process...")
        try:
            os.killpg(os.getpgid(bot_process.pid), signal.SIGTERM)
            time.sleep(1)  # Give it a moment to terminate
        except Exception as e:
            logger.error(f"Error stopping bot process: {e}")
    
    # Ensure we have the token
    if not os.getenv("DISCORD_TOKEN"):
        logger.error("DISCORD_TOKEN not found in environment variables. Bot cannot start.")
        return False
    
    # Start the bot process
    try:
        logger.info("Starting Discord bot process...")
        bot_process = subprocess.Popen(
            ["python", "bot.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            preexec_fn=os.setsid
        )
        
        # Start a thread to log the output
        threading.Thread(target=log_bot_output, daemon=True).start()
        
        logger.info("Discord bot process started")
        return True
    except Exception as e:
        logger.error(f"Failed to start bot process: {e}")
        return False

def log_bot_output():
    """Log the output from the bot process"""
    global bot_process
    
    if not bot_process or not bot_process.stdout:
        return
    
    for line in bot_process.stdout:
        if line.strip():
            logger.info(f"BOT: {line.strip()}")

def cleanup():
    """Clean up resources when script exits"""
    global bot_process
    
    logger.info("Cleaning up resources...")
    
    if bot_process and bot_process.poll() is None:
        try:
            logger.info("Terminating bot process...")
            os.killpg(os.getpgid(bot_process.pid), signal.SIGTERM)
        except Exception as e:
            logger.error(f"Error terminating bot process: {e}")

def main():
    """Main entry point"""
    # Register cleanup handler
    atexit.register(cleanup)
    
    # Start the bot process
    if not start_bot_process():
        logger.error("Failed to start bot process. Exiting.")
        return 1
    
    # Keep the script running and monitor the bot process
    try:
        logger.info("Monitoring bot process...")
        
        while True:
            # Check if the bot process is still running
            if bot_process.poll() is not None:
                exit_code = bot_process.poll()
                logger.warning(f"Bot process exited with code {exit_code}")
                
                # Restart the process after a delay
                logger.info("Restarting bot process in 5 seconds...")
                time.sleep(5)
                
                if not start_bot_process():
                    logger.error("Failed to restart bot process. Exiting.")
                    return 1
            
            # Sleep to avoid consuming too much CPU
            time.sleep(5)
            
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
        return 0
    except Exception as e:
        logger.error(f"Error in main loop: {e}")
        return 1
    finally:
        cleanup()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())