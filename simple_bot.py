"""
Simple Discord Bot (Fallback Bot)

This module provides a simple Discord bot implementation
when the main bot.py fails to load.
"""
import os
import logging
import asyncio
import traceback
import discord
from discord.ext import commands

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SimpleBot(commands.Bot):
    """Simple Discord bot as a fallback"""
    
    def __init__(self):
        """Initialize the bot with necessary intents"""
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        
        super().__init__(
            command_prefix="!",  # Command prefix
            intents=intents,     # Required intents
            description="Simple Discord Bot (Fallback)"
        )
    
    async def setup_hook(self):
        """Called before the bot starts running"""
        logger.info("Setting up simple bot...")
        
        # Try to load some basic commands
        try:
            await self.load_basic_commands()
        except Exception as e:
            logger.error(f"Error loading basic commands: {e}")
    
    async def load_basic_commands(self):
        """Load basic commands"""
        @self.command(name="ping")
        async def ping_command(ctx):
            """Simple ping command to test bot responsiveness"""
            await ctx.send(f"Pong! Latency: {round(self.latency * 1000)}ms")
        
        @self.command(name="info")
        async def info_command(ctx):
            """Display basic bot information"""
            embed = discord.Embed(
                title="Bot Information",
                description="This is a simple fallback bot running when the main bot fails to load.",
                color=discord.Color.blue()
            )
            embed.add_field(name="Running Mode", value="Fallback Simple Bot", inline=False)
            embed.add_field(name="Python Discord Version", value=discord.__version__, inline=False)
            
            await ctx.send(embed=embed)
    
    async def on_ready(self):
        """Called when the bot is ready"""
        if self.user:
            logger.info(f"Logged in as {self.user.name} (ID: {self.user.id})")
        else:
            logger.info("Bot is ready but user information is not available")
        logger.info("------")
        logger.info("Simple bot is ready!")
        
        try:
            # Set the bot activity
            activity = discord.Game(name="Fallback Mode")
            await self.change_presence(activity=activity)
        except Exception as e:
            logger.error(f"Error setting activity: {e}")
    
    async def on_error(self, event_method, *args, **kwargs):
        """Global error handler"""
        import traceback
        logger.error(f"Error in {event_method}: {traceback.format_exc()}")

async def main():
    """Main entry point"""
    # Get the Discord token
    token = os.environ.get('DISCORD_TOKEN')
    if not token:
        logger.error("DISCORD_TOKEN environment variable not set")
        return
    
    # Create and run the bot
    bot = SimpleBot()
    
    try:
        logger.info("Starting simple bot...")
        await bot.start(token)
    except Exception as e:
        logger.error(f"Error running bot: {e}")
    finally:
        if not bot.is_closed():
            await bot.close()
            
if __name__ == "__main__":
    asyncio.run(main())