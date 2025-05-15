#!/bin/bash
# Start script for the Discord bot

echo "========================================"
echo "  TOWER OF TEMPTATION DISCORD BOT"
echo "  Starting Discord bot with run_replit.py"
echo "  $(date)"
echo "========================================"

# Set the Python path to include the current directory
export PYTHONPATH=".:$PYTHONPATH"

# Verify the Discord token is set
if [ -z "$DISCORD_TOKEN" ]; then
  echo "ERROR: DISCORD_TOKEN environment variable is not set!"
  exit 1
fi

# Run the bot
python run_replit.py