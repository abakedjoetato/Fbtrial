# Discord Bot on Replit

This is a versatile Discord bot built with py-cord, designed to enhance server interactions and provide dynamic user experiences.

## Key Components

- Python-based Discord integration using py-cord
- Secure token-based authentication
- Modular command handling system
- Flexible bot configuration
- Web interface for monitoring and control

## Project Structure

- `main.py`: Main entry point for running the bot
- `simple_bot.py`: Simplified implementation of the Discord bot
- `run_simple_bot.py`: Runner script with web interface
- `setup.py`: Setup script for the environment
- `bot.py`: Full-featured bot implementation with compatibility layer
- `discord_compat_layer.py`: Compatibility layer between discord.py and py-cord
- `cogs/`: Directory containing command modules (cogs)
- `utils/`: Utility modules for various bot functionalities

## Setup Guide

1. Make sure your Discord bot token is set in the Replit Secrets tab with the key `DISCORD_TOKEN`
2. Run the setup script to create necessary files:
   ```
   python setup.py
   ```
3. Start the bot using one of the following methods:
   - Using the main entry point: `python main.py`
   - Using the run script: `./run.sh`

## Web Interface

The bot includes a web interface accessible at port 5000, which allows you to:
- Monitor the bot's status
- Start, stop, and restart the bot
- View uptime information

## Command System

The bot supports a prefix-based command system. By default, commands start with `!` (e.g., `!ping`).

Basic commands:
- `!ping`: Check if the bot is responsive
- `!info`: Get information about the bot
- `!hello`: Say hello to the bot

The full implementation includes more advanced commands loaded from the `cogs/` directory.

## Customization

You can customize the bot by:
- Adding new commands to `simple_bot.py` or as cogs in the `cogs/` directory
- Modifying the command prefix by setting the `COMMAND_PREFIX` environment variable
- Extending the web interface in `run_simple_bot.py`

## Deployment

The bot is designed to be run on Replit, which provides hosting and keeps the bot online.

## Troubleshooting

If you encounter issues:
1. Check that your `DISCORD_TOKEN` is correctly set in Replit Secrets
2. Look for error messages in the console or bot.log file
3. Restart the bot using the web interface or by restarting the Replit