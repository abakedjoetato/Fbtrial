"""
Admin Commands Cog (Fixed Version)

This module provides administrative commands for bot owners and server administrators.
It follows the compatibility layer implementation for py-cord.
"""
import logging
import datetime
from typing import Optional

from discord_compat_layer import (
    Embed, Color, Cog, slash_command, commands, 
    has_permissions, is_owner, Interaction, app_commands
)

logger = logging.getLogger("discord_bot")

class AdminCog(commands.Cog):
    """Administrative commands for the bot"""
    
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db  # Use the database from the bot instance
        logger.info("Admin Fixed cog initialized")
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Called when the cog is ready"""
        logger.info("Admin Fixed cog ready")
    
    @slash_command(name="admin_stats", description="Display database statistics for the bot")
    @has_permissions(administrator=True)
    async def admin_stats(self, ctx: Interaction):
        """Display database statistics for the bot"""
        # Defer the response to avoid timeout
        await ctx.response.defer()
        
        # Get stats from database
        stats_result = await self.bot.find_one("bot_stats", {"_id": "stats"})
        
        # Handle potential errors
        if not stats_result.success:
            logger.error(f"Failed to retrieve bot stats: {stats_result.error}")
            await ctx.followup.send("❌ Failed to retrieve bot statistics. Check the logs for details.")
            return
            
        stats = stats_result.data or {}
        
        embed = Embed(
            title="Bot Statistics",
            color=Color.blue(),
            description="Statistics from the database"
        )
        
        # Use .get() with default values for safer dict access
        # Convert integer values to strings for embed fields
        embed.add_field(name="Total Users", value=str(stats.get("user_count", 0)), inline=True)
        embed.add_field(name="Total Servers", value=str(stats.get("server_count", 0)), inline=True)
        embed.add_field(name="Total Commands Used", value=str(stats.get("total_commands", 0)), inline=True)
        embed.add_field(name="Total Messages Logged", value=str(stats.get("message_count", 0)), inline=True)
        
        await ctx.followup.send(embed=embed)
    
    @slash_command(name="clearlogs", description="Clear message logs older than specified days")
    @has_permissions(administrator=True)
    async def clearlogs(self, ctx: Interaction, days: int = 30):
        """Clear message logs older than specified days (default: 30 days)"""
        # Defer the response to avoid timeout
        await ctx.response.defer()
        
        # Calculate the cutoff date
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days)
        
        # Use the bot's database interface to delete logs
        delete_result = await self.bot.delete_one(
            "message_logs", 
            {"timestamp": {"$lt": cutoff_date}}
        )
        
        if delete_result.success:
            deleted_count = delete_result.data.deleted_count if hasattr(delete_result.data, 'deleted_count') else 0
            await ctx.followup.send(f"✅ Successfully cleared {deleted_count} message logs older than {days} days.")
        else:
            logger.error(f"Failed to clear logs: {delete_result.error}")
            await ctx.followup.send("❌ Failed to clear logs. Check the bot logs for details.")
    
    @slash_command(name="setconfig", description="Set a configuration value in the database")
    @has_permissions(administrator=True)
    async def setconfig(self, ctx: Interaction, key: str, value: str):
        """Set a configuration value in the database"""
        # Defer the response to avoid timeout
        await ctx.response.defer()
        
        # Use the bot's database interface to update the config
        update_result = await self.bot.update_one(
            "bot_config", 
            {"key": key}, 
            {"$set": {"value": value}},
            upsert=True
        )
        
        if update_result.success:
            await ctx.followup.send(f"✅ Configuration updated: `{key}` set to `{value}`")
        else:
            logger.error(f"Failed to update config: {update_result.error}")
            await ctx.followup.send("❌ Failed to update configuration. Check the logs for details.")
    
    @slash_command(name="getconfig", description="Get a configuration value from the database")
    @has_permissions(administrator=True)
    async def getconfig(self, ctx: Interaction, key: str):
        """Get a configuration value from the database"""
        # Defer the response to avoid timeout
        await ctx.response.defer()
        
        # Use the bot's database interface to retrieve the config
        config_result = await self.bot.find_one("bot_config", {"key": key})
        
        if config_result.success and config_result.data:
            value = config_result.data.get("value")
            await ctx.followup.send(f"Configuration `{key}` = `{value}`")
        else:
            if not config_result.success:
                logger.error(f"Failed to retrieve config: {config_result.error}")
            await ctx.followup.send(f"❌ Configuration key `{key}` not found.")
    
    @slash_command(name="bot_version", description="Display the bot version information")
    @has_permissions(administrator=True)
    async def show_version(self, ctx: Interaction):
        """Display the bot version information"""
        # Defer the response to avoid timeout
        await ctx.response.defer()
        
        embed = Embed(
            title="Bot Version Information",
            color=Color.blue(),
            description="Current running version details"
        )
        
        # Get library versions from imports
        try:
            import discord
            import sys
            import platform
            
            embed.add_field(name="Bot Version", value="1.0.0", inline=True)
            embed.add_field(name="Discord Library", value=f"py-cord {discord.__version__}", inline=True)
            embed.add_field(name="Python Version", value=platform.python_version(), inline=True)
            embed.add_field(name="Platform", value=platform.platform(), inline=True)
            
            # Get uptime if available
            if hasattr(self.bot, 'start_time'):
                uptime = datetime.datetime.now() - self.bot.start_time
                days, remainder = divmod(uptime.total_seconds(), 86400)
                hours, remainder = divmod(remainder, 3600)
                minutes, seconds = divmod(remainder, 60)
                
                uptime_str = f"{int(days)}d {int(hours)}h {int(minutes)}m {int(seconds)}s"
                embed.add_field(name="Uptime", value=uptime_str, inline=True)
            
        except Exception as e:
            logger.error(f"Error getting version info: {e}")
            embed.add_field(name="Error", value="Could not retrieve all version details", inline=False)
        
        await ctx.followup.send(embed=embed)

async def setup(bot):
    """Set up the admin cog"""
    await bot.add_cog(AdminCog(bot))
    logger.info("Admin Fixed commands cog loaded")