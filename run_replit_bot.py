#!/usr/bin/env python3
"""
Main entry point for running the Discord bot in Replit
This file is intended to be run directly from the Replit run button
"""

import os
import sys
import subprocess
import time

def main():
    """Main function to run the Discord bot"""
    print("=" * 50)
    print("Discord Bot Launcher")
    print("=" * 50)
    
    # Verify DISCORD_TOKEN is set
    if not os.environ.get("DISCORD_TOKEN"):
        print("ERROR: DISCORD_TOKEN environment variable is not set!")
        print("Please set it in the Secrets tab in Replit.")
        return 1
    
    print("Starting Discord bot with main.py...")
    
    # Set PYTHONPATH
    os.environ["PYTHONPATH"] = f".:{os.environ.get('PYTHONPATH', '')}"
    
    # Run the bot using Python subprocess
    try:
        # Execute main.py directly
        subprocess.run([sys.executable, "main.py"], check=True)
    except KeyboardInterrupt:
        print("Bot stopped by user.")
    except subprocess.CalledProcessError as e:
        print(f"Error running bot: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())