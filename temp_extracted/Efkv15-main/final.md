# Discord Bot Setup Guide

## Project Overview
This project contains a Discord bot built using py-cord. The bot can be easily configured and run on Replit.

## Setup Steps Completed
1. ✅ Installed system dependencies including unzip
2. ✅ Extracted Efkalphav2-main.zip archive from attached_assets
3. ✅ Moved all files from the archive to the main directory
4. ✅ Installed Python dependencies with py-cord as the main Discord library
5. ✅ Set up main.py as the entry point for the bot

## How to Start the Bot
The bot is configured to run using main.py as the entry point. Here are the ways to start the bot:

1. **Using the Run Button**: 
   When you press the "Run" button in Replit, the bot will start with the main.py file.

2. **Using the start_bot.sh script**:
   ```bash
   bash start_bot.sh
   ```

3. **Setting up a Workflow** (Recommended):
   To set up a proper workflow for the bot:
   - Click on the "Tools" menu in Replit
   - Select "Workflows"
   - Click "Create Workflow"
   - Name it "discord_bot"
   - In the "Run" field, enter "python main.py"
   - Save the workflow
   - Click "Run" on the workflow to start your bot

The workflow approach is recommended for long-running applications like Discord bots.

## Configuration
The bot is configured using environment variables, which can be set in the .env file:
- `DISCORD_TOKEN` - Your Discord bot token (required)
- `COMMAND_PREFIX` - Command prefix for the bot (default: !)
- `LOG_LEVEL` - Logging level (default: INFO)

### Discord Token
To get a Discord bot token:
1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Navigate to the "Bot" tab
4. Click "Add Bot"
5. Under the "Token" section, click "Copy" to copy your token
6. Paste the token into the .env file

## Project Structure
- `main.py` - Main entry point for the bot
- `bot.py` - Core bot implementation
- `cogs/` - Directory containing command modules (cogs)
- `utils/` - Utility functions and helpers
- `.env` - Environment variables for configuration
- `requirements.txt` - Python dependencies

## Available Commands
Commands are organized into cogs located in the `cogs/` directory. The bot automatically loads all .py files in this directory as command modules.

Use the `!help` command (or your configured prefix) to see a list of available commands.

### Example Commands
Based on the cogs files found in the project:

#### Admin Commands
- `!kick <member> [reason]` - Kick a member from the server
- `!ban <member> [reason]` - Ban a member from the server
- `!mute <member> [duration]` - Mute a member for a specified duration
- `!clear <amount>` - Clear a specified number of messages

#### Fun Commands
- `!joke` - Get a random joke
- `!meme` - Get a random meme
- `!8ball <question>` - Ask the magic 8-ball a question
- `!roll <dice>` - Roll dice (e.g., !roll 2d6)

#### General Commands
- `!help [command]` - Show help for all commands or a specific command
- `!ping` - Check the bot's latency
- `!info` - Get information about the bot
- `!serverinfo` - Get information about the server

Note: The actual available commands may vary based on the implemented cogs.

## Database
The bot has MongoDB integration, which can be enabled by setting:
```
USE_MONGODB=true
MONGODB_URI=your_mongodb_connection_string
```

## Customizing the Bot
To add new commands:
1. Create a new file in the `cogs/` directory
2. Define a class that inherits from `commands.Cog`
3. Add command methods using the `@commands.command()` decorator
4. Add a setup function at the end of the file

Example:
```python
import discord
from discord.ext import commands

class MyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command()
    async def hello(self, ctx):
        """Says hello"""
        await ctx.send("Hello!")

async def setup(bot):
    await bot.add_cog(MyCog(bot))
```

## Troubleshooting
- If the bot fails to start, check the error logs in the Replit console
- Ensure your Discord token is correctly set in the .env file
- Make sure all required permissions are enabled for your bot in the Discord Developer Portal
- Check that the bot has the necessary permissions in your Discord server

## Inviting the Bot to Your Server
To invite your bot to a Discord server:

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Select your application
3. Navigate to the "OAuth2" tab
4. Select "URL Generator" in the sub-menu
5. Under "Scopes", select "bot" and "applications.commands"
6. Under "Bot Permissions", select the permissions your bot needs:
   - For basic functionality: "Send Messages", "Read Message History", "Embed Links"
   - For admin commands: Additional permissions like "Kick Members", "Ban Members", "Manage Messages"
7. Copy the generated URL at the bottom of the page
8. Open the URL in your browser and select the server where you want to add the bot
9. Follow the prompts to authorize the bot

## References
- [py-cord Documentation](https://docs.pycord.dev/en/stable/)
- [Discord Developer Portal](https://discord.com/developers/applications)
- [Discord.py Documentation](https://discordpy.readthedocs.io/en/stable/) (For additional reference)