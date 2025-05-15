#!/usr/bin/env python3
"""
Workflow Runner Script

This script starts the Discord bot workflow.
"""

import logging
import os
import subprocess
import sys

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

def main():
    """Main entry point."""
    logger.info("Starting Discord bot workflow...")
    
    try:
        # Run the main Python script
        process = subprocess.Popen(
            ["python", "main.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,  # Line buffered
            universal_newlines=True
        )
        
        # Print output in real-time
        if process and process.stdout:
            for line in process.stdout:
                print(line, end="")
        else:
            logger.error("Process or stdout not available")
        
        # Wait for process to complete
        process.wait()
        
        if process.returncode != 0:
            logger.error(f"Bot process exited with code {process.returncode}")
            return process.returncode
        
        return 0
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        return 0
    except Exception as e:
        logger.error(f"Error starting workflow: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())