"""
Setup Script for Discord Bot

This script sets up the Discord bot environment.
"""

import os
import sys
import logging
import subprocess

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

def check_token():
    """Check if the DISCORD_TOKEN environment variable is set"""
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        logger.warning("DISCORD_TOKEN not found in environment variables")
        return False
    
    logger.info("DISCORD_TOKEN found in environment variables")
    return True

def install_requirements():
    """Install required packages"""
    try:
        logger.info("Installing required packages...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            check=True
        )
        logger.info("Required packages installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install required packages: {e}")
        return False
    except Exception as e:
        logger.error(f"Error installing required packages: {e}")
        return False

def create_bot_run_script():
    """Create a script to run the bot"""
    script_content = """#!/bin/bash
# Run the Discord bot
python main.py
"""
    
    script_path = "run.sh"
    try:
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        os.chmod(script_path, 0o755)  # Make executable
        logger.info(f"Created bot run script at {script_path}")
        return True
    except Exception as e:
        logger.error(f"Error creating bot run script: {e}")
        return False

def main():
    """Main entry point"""
    # Check if DISCORD_TOKEN is set
    if not check_token():
        logger.error("DISCORD_TOKEN environment variable is required but not set")
        logger.error("Please set it in the Replit Secrets tab")
        return 1
    
    # Create bot run script
    if not create_bot_run_script():
        logger.error("Failed to create bot run script")
        return 1
    
    # Display success message
    logger.info("Discord bot setup completed successfully")
    logger.info("You can now run the bot using 'python main.py' or './run.sh'")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())