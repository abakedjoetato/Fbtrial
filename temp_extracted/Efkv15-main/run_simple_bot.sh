#!/bin/bash

# Run script for the simple Discord bot
# This script runs the simple_bot.py file

echo "Starting Simple Discord Bot..."

# Make sure PYTHONPATH includes the current directory
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Check if token exists
if [ -z "$DISCORD_TOKEN" ]; then
    echo "Error: DISCORD_TOKEN environment variable is not set."
    echo "Please set the DISCORD_TOKEN in the Replit Secrets tab."
    exit 1
fi

# Start the bot
python simple_bot.py

# The script should not reach here unless the bot exits
echo "Bot has exited."