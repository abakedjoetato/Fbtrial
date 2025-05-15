#!/usr/bin/env python3
"""
Test script to verify the Discord bot can start properly
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def test_environment():
    """Test if the environment is set up correctly"""
    logger.info("Testing environment setup...")
    
    # Check for DISCORD_TOKEN
    if os.environ.get("DISCORD_TOKEN"):
        logger.info("✓ DISCORD_TOKEN is set")
    else:
        logger.error("✗ DISCORD_TOKEN is not set!")
        return False
    
    return True

def test_imports():
    """Test if all required modules can be imported"""
    logger.info("Testing imports...")
    
    try:
        import main
        logger.info("✓ main module imported")
        
        import app_enhanced
        logger.info("✓ app_enhanced module imported")
        
        import bot
        logger.info("✓ bot module imported")
        
        import discord_compat_layer
        logger.info("✓ discord_compat_layer module imported")
        
        return True
    except ImportError as e:
        logger.error(f"✗ Import error: {e}")
        return False
    except Exception as e:
        logger.error(f"✗ Error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("Discord Bot Setup Tester")
    print("=" * 50)
    
    # Test environment
    env_ok = test_environment()
    
    # Test imports
    imports_ok = test_imports()
    
    if env_ok and imports_ok:
        print("\n✓ All tests passed!")
        print("The Discord bot is ready to run.")
        print("You can start it with: python start_discord_bot.py")
        sys.exit(0)
    else:
        print("\n✗ Some tests failed. Please fix the issues above.")
        sys.exit(1)