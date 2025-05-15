#!/usr/bin/env python3
"""
Entry point script for Discord bot to be run directly from Replit.
This script directly launches the bot without attempting to install dependencies.
"""

import os
import sys
import subprocess
import importlib.util

def run_bot():
    """Run the Discord bot using main.py"""
    try:
        print("Starting Discord bot...")
        # Set environment variable for Python path
        os.environ["PYTHONPATH"] = f".:{os.environ.get('PYTHONPATH', '')}"
        
        print(f"Running with DISCORD_TOKEN: {'Set (value hidden)' if os.environ.get('DISCORD_TOKEN') else 'Not set'}")
        
        # Run the main script directly
        print("Executing main.py...")
        from main import main
        main()
        
    except ImportError:
        print("Error importing main.py. Running it directly as a script...")
        subprocess.run([sys.executable, "main.py"])
    except Exception as e:
        print(f"Error running bot: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    print("=" * 50)
    print("Discord Bot Starter")
    print("=" * 50)
    
    # Run the bot directly
    run_bot()