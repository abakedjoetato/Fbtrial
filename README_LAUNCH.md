# Discord Bot Launch Instructions

This document explains how to run the Discord bot on Replit.

## Prerequisites

1. Make sure your Discord bot token is set in the Replit Secrets:
   - Look for the key `DISCORD_TOKEN` in the Secrets tab
   - If it's not there, add it with your Discord bot token

## Starting the Bot

There are two ways to start the bot:

### Option 1: Using the Replit Run Button

1. Open the file `run_replit_bot.py` in the editor
2. Click the "Run" button at the top of the Replit interface
3. The bot should start running and connect to Discord

### Option 2: From the Command Line

Run the following command in the Shell tab:

```bash
python run_replit_bot.py
```

## Verifying the Bot is Running

Once started, you should see:
1. A log message saying "Discord bot process is now running in the background"
2. A web interface available at the "Webview" tab showing the bot's status
3. Messages in the console indicating the bot is connecting to Discord

## Troubleshooting

If the bot doesn't start:

1. Verify your `DISCORD_TOKEN` is correctly set in the Secrets tab
2. Check the console for error messages
3. Look at the logs in `bot.log` file for more detailed information

## Stopping the Bot

To stop the bot, simply press the "Stop" button in the Replit interface.