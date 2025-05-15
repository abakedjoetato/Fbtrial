"""
Template Cog with py-cord 2.6.1 Compatibility (Simplified)

This is a simplified version of the template cog that demonstrates
proper command usage with py-cord 2.6.1.
"""

import logging
from typing import Optional
import sys

# Make sure discord_compat_layer is in the path
sys.path.insert(0, ".")

# Use our compatibility layer instead of importing discord directly

from discord_compat_layer import (
    Embed, Color, commands, Interaction, app_commands, 
    slash_command, SlashCommandGroup, Option
)

# Import compatibility utilities
from utils.interaction_handlers import safely_respond_to_interaction
from utils.command_handlers import command_handler, defer_interaction

# Set up logging
logger = logging.getLogger(__name__)

class SimpleTemplateCog(commands.Cog):
    """A simplified template cog for py-cord 2.6.1"""
    
    def __init__(self, bot):
        self.bot = bot
        logger.info(f"{self.__class__.__name__} cog initialized")
    
    # Individual slash commands instead of a group
    @slash_command(
        name="simple_ping", 
        description="Check if the bot is responsive"
    )
    @command_handler()
    async def ping_command(self, ctx: Interaction):
        """Check if the bot is responsive"""
        await safely_respond_to_interaction(
            ctx, 
            f"Pong! Bot latency: {round(self.bot.latency * 1000)}ms"
        )
    
    @slash_command(
        name="simple_echo", 
        description="Echo back a message"
    )
    @command_handler()
    async def echo_command(
        self, 
        ctx: Interaction,
        message: str
    ):
        """Echo back a message"""
        await safely_respond_to_interaction(
            ctx, 
            f"You said: {message}"
        )
    
    # Normal prefixed command
    @commands.command(name="simple_test", help="Test prefixed command")
    async def test_prefix_command(self, ctx):
        """Test prefixed command implementation"""
        await ctx.send("Simple prefix command working!")


async def setup(bot):
    """Add the cog to the bot"""
    bot.add_cog(SimpleTemplateCog(bot))
    logger.info(f"{SimpleTemplateCog.__name__} cog loaded")