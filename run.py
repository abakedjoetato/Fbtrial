"""
Simple Discord Bot Runner
This script checks that all requirements are met and runs the bot.
"""

import os
import sys
import logging
import subprocess
import importlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger('bot_runner')

def check_dependencies():
    """Check if all required dependencies are installed"""
    required_packages = [
        'py-cord',
        'python-dotenv',
        'motor',
        'pymongo',
        'dnspython',
    ]
    
    missing_packages = []
    
    # Add .pythonlibs to path for Replit environment
    pythonlibs_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.pythonlibs/lib/python3.11/site-packages')
    if os.path.exists(pythonlibs_path) and pythonlibs_path not in sys.path:
        sys.path.insert(0, pythonlibs_path)
        logger.info(f"Added {pythonlibs_path} to Python path")
    
    for package in required_packages:
        try:
            importlib.import_module(package.replace('-', '_'))
            logger.info(f"Found package: {package}")
        except ImportError:
            missing_packages.append(package)
            logger.warning(f"Missing package: {package}")
    
    if missing_packages:
        logger.warning(f"Missing packages: {', '.join(missing_packages)}")
        logger.info("Note: On Replit, use the Packager tool to install packages")
        logger.info("Attempting to continue anyway...")
    
    # Return True even if packages are missing - we'll let the import errors
    # show exactly what's missing when we try to run the bot
    return True

def check_environment():
    """Check if required environment variables are set"""
    if not os.path.exists('.env'):
        logger.warning("No .env file found, creating one...")
        with open('.env', 'w') as f:
            f.write("# Discord Bot Configuration\n")
            f.write("DISCORD_TOKEN=your_token_here\n")
            f.write("COMMAND_PREFIX=!\n")
            f.write("LOG_LEVEL=INFO\n")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    token = os.environ.get('DISCORD_TOKEN')
    if not token or token == 'your_token_here':
        logger.error("No DISCORD_TOKEN found in environment variables")
        logger.error("Please set your Discord bot token in the .env file")
        return False
    
    return True

def main():
    """Main entry point"""
    logger.info("Starting Discord bot setup...")
    
    # Check if all dependencies are installed
    if not check_dependencies():
        logger.error("Failed to install required dependencies")
        return 1
    
    # Check environment variables
    if not check_environment():
        logger.error("Environment check failed")
        return 1
    
    # Run the bot
    logger.info("Running Discord bot...")
    try:
        import main
        logger.info("Bot should be running now")
    except Exception as e:
        logger.error(f"Failed to run bot: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())