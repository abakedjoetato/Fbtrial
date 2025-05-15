"""
Discord Bot Starter
This script initializes and runs a simplified Discord bot for Replit using py-cord.
"""

import os
import sys
import asyncio
import logging
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Import py-cord
try:
    import discord
    from discord.ext import commands
    logger.info(f"Using py-cord version: {discord.__version__}")
except ImportError as e:
    logger.error(f"Failed to import py-cord: {e}")
    sys.exit(1)

class BasicBot(commands.Bot):
    """A basic Discord bot implementation"""
    
    def __init__(self):
        """Initialize the bot with necessary intents"""
        # Set up intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        
        # Get command prefix from environment or use default
        prefix = os.environ.get("COMMAND_PREFIX", "!")
        
        # Initialize the bot
        super().__init__(
            command_prefix=prefix,
            intents=intents,
            case_insensitive=True
        )
    
    async def setup_hook(self):
        """Setup hook that's called before the bot starts"""
        # Load cogs from the cogs directory
        await self.load_all_cogs()
    
    async def load_all_cogs(self):
        """Load all cogs from the cogs directory"""
        cogs_dir = 'cogs'
        if not os.path.isdir(cogs_dir):
            logger.warning(f"Cogs directory '{cogs_dir}' not found")
            return
        
        for filename in os.listdir(cogs_dir):
            if filename.endswith('.py') and not filename.startswith('_'):
                cog_name = f"{cogs_dir}.{filename[:-3]}"
                try:
                    await self.load_extension(cog_name)
                    logger.info(f"Loaded cog: {cog_name}")
                except Exception as e:
                    logger.error(f"Failed to load cog {cog_name}: {e}")
    
    async def on_ready(self):
        """Called when the bot is ready"""
        logger.info(f"Logged in as {self.user.name} ({self.user.id})")
        logger.info(f"Connected to {len(self.guilds)} guilds")
        logger.info(f"Bot is ready!")
        
        # Bot is already online by default in on_ready, no need to set status
    
    async def on_command_error(self, ctx, error):
        """Handle command errors"""
        # Check if command has its own error handler
        if hasattr(ctx.command, 'on_error'):
            return
        
        # Try to get a dedicated error handling cog
        error_cog = ctx.bot.get_cog('ErrorHandling')
        if error_cog:
            return  # Let the cog handle it
        
        # Default error handling
        if isinstance(error, commands.CommandNotFound):
            return  # Ignore command not found errors
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing required argument. Use `{self.command_prefix}help {ctx.command}` for help.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send(f"Invalid argument. Use `{self.command_prefix}help {ctx.command}` for help.")
        else:
            await ctx.send(f"An error occurred: {str(error)}")
            logger.error(f"Error in command {ctx.command}: {error}")

async def main():
    """Main entry point for the bot"""
    # Load environment variables
    load_dotenv()
    
    # Get the Discord token
    token = os.environ.get("DISCORD_TOKEN")
    if not token:
        logger.error("DISCORD_TOKEN not found in environment variables")
        return 1
    
    # Create and run the bot
    bot = BasicBot()
    
    try:
        logger.info("Starting bot...")
        await bot.start(token)
    except KeyboardInterrupt:
        logger.info("Bot stopped by keyboard interrupt")
    except Exception as e:
        logger.error(f"Error running bot: {e}")
        return 1
    finally:
        if not bot.is_closed():
            await bot.close()
    
    return 0

if __name__ == "__main__":
    """Run the bot"""
    exit_code = asyncio.run(main())
    sys.exit(exit_code)