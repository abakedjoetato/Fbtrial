"""
Direct Discord Bot Runner

This file runs the Discord bot directly using py-cord,
without going through the compatibility layer.
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Run the Discord bot directly"""
    try:
        # Import the py-cord library
        import discord
        from discord.ext import commands
        
        # Print the version information
        logger.info(f"Discord library version: {discord.__version__}")
        
        # Load environment variables
        load_dotenv()
        
        # Get the token from environment variables
        token = os.getenv("DISCORD_TOKEN")
        if not token:
            logger.error("No Discord token found in environment variables.")
            return 1
        
        # Set up intents (permissions)
        intents = discord.Intents.default()
        intents.message_content = True  # Needed to read message content
        intents.members = True  # Needed for member-related commands
        
        # Initialize the bot with command prefix
        bot = commands.Bot(
            command_prefix="!",
            intents=intents,
            description="A Discord bot running on py-cord"
        )
        
        # Define event handlers
        @bot.event
        async def on_ready():
            logger.info(f"Logged in as {bot.user} (ID: {bot.user.id})")
            logger.info(f"Connected to {len(bot.guilds)} guilds")
            
            # Set bot activity
            activity = discord.Activity(
                type=discord.ActivityType.listening,
                name=f"!help | {len(bot.guilds)} servers"
            )
            await bot.change_presence(activity=activity)
            
            logger.info("Bot is ready!")
        
        # Define a simple ping command
        @bot.command(name="ping")
        async def ping(ctx):
            """Check if the bot is responsive."""
            await ctx.send(f"Pong! Latency: {round(bot.latency * 1000)}ms")
        
        # Run the bot
        logger.info("Starting the bot...")
        await bot.start(token)
    
    except ImportError as e:
        logger.error(f"Failed to import Discord library: {e}")
        return 1
    except Exception as e:
        logger.error(f"Error running bot: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    import asyncio
    exit_code = asyncio.run(main())
    sys.exit(exit_code)