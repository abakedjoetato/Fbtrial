"""
Basic Commands Cog - Fixed for py-cord 2.6.1 compatibility

This cog provides basic commands for the Discord bot.
"""

import logging
import sys
from typing import Optional
import datetime

# Make sure discord_compat_layer is in the path
sys.path.insert(0, ".")

# Import from our compatibility layer instead of directly from discord
from discord_compat_layer import (
    Embed, Color, commands, Interaction, app_commands, 
    slash_command, SlashCommandGroup, Option
)

# Import compatibility utilities
from utils.interaction_handlers import safely_respond_to_interaction
from utils.command_handlers import command_handler, defer_interaction

# Configure logger
logger = logging.getLogger("cogs.basic")

class Basic(commands.Cog):
    """
    Basic bot commands
    
    This cog provides basic functionality and commands.
    """
    
    def __init__(self, bot):
        """
        Initialize the cog
        
        Args:
            bot: The Discord bot instance
        """
        self.bot = bot
        self.start_time = datetime.datetime.now()
        logger.info("Basic cog initialized")
    
    @slash_command(name="latency", description="Check the bot's latency")
    @command_handler()
    async def ping_slash(self, ctx):
        """
        Check the bot's latency
        
        This command responds with the bot's WebSocket latency.
        """
        latency = round(self.bot.latency * 1000)
        await safely_respond_to_interaction(ctx, f"🏓 Pong! Latency: {latency}ms")
    
    @commands.command(name="latency", aliases=["pong"])
    async def ping(self, ctx):
        """
        Check the bot's latency
        
        This command responds with the bot's WebSocket latency.
        """
        latency = round(self.bot.latency * 1000)
        await ctx.send(f"🏓 Pong! Latency: {latency}ms")
    
    @slash_command(name="uptime", description="Check the bot's uptime")
    @command_handler()
    async def uptime_slash(self, ctx):
        """
        Check the bot's uptime
        
        This command shows how long the bot has been running.
        """
        uptime = datetime.datetime.now() - self.start_time
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        uptime_str = f"{days}d {hours}h {minutes}m {seconds}s"
        await safely_respond_to_interaction(ctx, f"⏱️ Bot uptime: {uptime_str}")
    
    @commands.command(name="uptime")
    async def uptime(self, ctx):
        """
        Check the bot's uptime
        
        This command shows how long the bot has been running.
        """
        uptime = datetime.datetime.now() - self.start_time
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        uptime_str = f"{days}d {hours}h {minutes}m {seconds}s"
        await ctx.send(f"⏱️ Bot uptime: {uptime_str}")
    
    @slash_command(name="info", description="Show information about the bot")
    @command_handler()
    async def info_slash(self, ctx):
        """
        Show information about the bot
        
        This command shows general information about the bot.
        """
        embed = Embed(
            title="Bot Information",
            description="General bot information and statistics",
            color=Color.blue()
        )
        
        # Bot information
        embed.add_field(
            name="Bot Version",
            value="1.0.0",
            inline=True
        )
        
        # Library information
        try:
            from discord import __version__ as discord_version
        except ImportError:
            discord_version = "Unknown"
        
        embed.add_field(
            name="Library",
            value=f"py-cord {discord_version}",
            inline=True
        )
        
        # Bot statistics
        total_guilds = len(self.bot.guilds)
        total_members = sum(guild.member_count for guild in self.bot.guilds)
        
        embed.add_field(
            name="Servers",
            value=str(total_guilds),
            inline=True
        )
        
        embed.add_field(
            name="Members",
            value=str(total_members),
            inline=True
        )
        
        # Uptime
        uptime = datetime.datetime.now() - self.start_time
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        uptime_str = f"{days}d {hours}h {minutes}m {seconds}s"
        
        embed.add_field(
            name="Uptime",
            value=uptime_str,
            inline=True
        )
        
        # Add footer
        if hasattr(ctx, 'author') and ctx.author:
            embed.set_footer(text=f"Requested by {ctx.author.name}")
        elif hasattr(ctx, 'user') and ctx.user:
            embed.set_footer(text=f"Requested by {ctx.user.name}")
        
        await safely_respond_to_interaction(ctx, embed=embed)
    
    @commands.command(name="info")
    async def info(self, ctx):
        """
        Show information about the bot
        
        This command shows general information about the bot.
        """
        embed = Embed(
            title="Bot Information",
            description="General bot information and statistics",
            color=Color.blue()
        )
        
        # Bot information
        embed.add_field(
            name="Bot Version",
            value="1.0.0",
            inline=True
        )
        
        # Library information
        try:
            from discord import __version__ as discord_version
        except ImportError:
            discord_version = "Unknown"
        
        embed.add_field(
            name="Library",
            value=f"py-cord {discord_version}",
            inline=True
        )
        
        # Bot statistics
        total_guilds = len(self.bot.guilds)
        total_members = sum(guild.member_count for guild in self.bot.guilds)
        
        embed.add_field(
            name="Servers",
            value=str(total_guilds),
            inline=True
        )
        
        embed.add_field(
            name="Members",
            value=str(total_members),
            inline=True
        )
        
        # Uptime
        uptime = datetime.datetime.now() - self.start_time
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        uptime_str = f"{days}d {hours}h {minutes}m {seconds}s"
        
        embed.add_field(
            name="Uptime",
            value=uptime_str,
            inline=True
        )
        
        # Add footer
        embed.set_footer(text=f"Requested by {ctx.author.name}")
        
        await ctx.send(embed=embed)
    
    @slash_command(name="commands", description="Show list of available commands")
    @command_handler()
    async def commands_slash(self, ctx, command_name: Optional[str] = None):
        """
        Show list of available commands
        
        This command shows help for all commands or a specific command.
        
        Args:
            command_name: Optional name of the command to get help for
        """
        if command_name:
            # Get help for a specific command
            command = self.bot.get_command(command_name)
            
            if not command:
                await safely_respond_to_interaction(ctx, f"❌ Command `{command_name}` not found.")
                return
                
            embed = Embed(
                title=f"Help: {command.name}",
                description=command.help or "No description available.",
                color=Color.blue()
            )
            
            # Command usage
            # For slash commands, use / instead of the prefix
            usage = f"/{command.name}"
            if hasattr(command, 'signature') and command.signature:
                usage += f" {command.signature}"
            
            embed.add_field(
                name="Usage",
                value=f"`{usage}`",
                inline=False
            )
            
            # Command aliases
            if hasattr(command, 'aliases') and command.aliases:
                aliases = ", ".join(f"`{alias}`" for alias in command.aliases)
                embed.add_field(
                    name="Aliases",
                    value=aliases,
                    inline=False
                )
                
            await safely_respond_to_interaction(ctx, embed=embed)
        else:
            # List all commands grouped by cog
            embed = Embed(
                title="Bot Commands",
                description="Here are all available commands:",
                color=Color.blue()
            )
            
            # Group commands by cog
            cogs = {}
            for command in self.bot.commands:
                if hasattr(command, 'hidden') and command.hidden:
                    continue
                    
                cog_name = command.cog.qualified_name if command.cog else "No Category"
                
                if cog_name not in cogs:
                    cogs[cog_name] = []
                    
                cogs[cog_name].append(command)
                
            # Add fields for each cog
            for cog_name, commands_list in cogs.items():
                # Create field value
                field_value = ""
                for command in sorted(commands_list, key=lambda x: x.name):
                    # Get short description (first line of help)
                    short_desc = ""
                    if hasattr(command, 'help') and command.help:
                        short_desc = command.help.split('\n')[0]
                    else:
                        short_desc = "No description"
                    field_value += f"**/{command.name}**: {short_desc}\n"
                    
                embed.add_field(
                    name=cog_name,
                    value=field_value,
                    inline=False
                )
                
            # Add footer
            embed.set_footer(text=f"Use /commands <command> for more info on a command.")
            
            await safely_respond_to_interaction(ctx, embed=embed)

async def setup(bot):
    """
    Set up the basic cog
    
    Args:
        bot: The Discord bot instance
    """
    bot.add_cog(Basic(bot))
    logger.info("Basic cog loaded")