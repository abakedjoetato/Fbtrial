import logging
from discord_compat_layer import Embed, Color, Cog, command, has_permissions

logger = logging.getLogger("discord_bot")

class Admin(Cog):
    """Administrative commands for the bot"""
    
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db  # Use the database from the bot instance
    
    @command(name="stats")
    @has_permissions(administrator=True)
    async def stats(self, ctx):
        """Display database statistics for the bot"""
        # Get stats from database
        stats_result = await self.bot.find_one("bot_stats", {"_id": "stats"})
        
        # Handle potential errors
        if not stats_result.success:
            logger.error(f"Failed to retrieve bot stats: {stats_result.error}")
            await ctx.send("❌ Failed to retrieve bot statistics. Check the logs for details.")
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
        
        await ctx.send(embed=embed)
    
    @command(name="clearlogs")
    @has_permissions(administrator=True)
    async def clearlogs(self, ctx, days: int = 30):
        """Clear message logs older than specified days (default: 30 days)"""
        import datetime
        
        # Calculate the cutoff date
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days)
        
        # Use the bot's database interface to delete logs
        delete_result = await self.bot.delete_one(
            "message_logs", 
            {"timestamp": {"$lt": cutoff_date}}
        )
        
        if delete_result.success:
            deleted_count = delete_result.data.deleted_count if hasattr(delete_result.data, 'deleted_count') else 0
            await ctx.send(f"✅ Successfully cleared {deleted_count} message logs older than {days} days.")
        else:
            logger.error(f"Failed to clear logs: {delete_result.error}")
            await ctx.send("❌ Failed to clear logs. Check the bot logs for details.")
    
    @command(name="setconfigvalue")
    @has_permissions(administrator=True)
    async def setconfigvalue(self, ctx, key: str, value: str):
        """Set a configuration value in the database"""
        # Use the bot's database interface to update the config
        update_result = await self.bot.update_one(
            "bot_config", 
            {"key": key}, 
            {"$set": {"value": value}},
            upsert=True
        )
        
        if update_result.success:
            await ctx.send(f"✅ Configuration updated: `{key}` set to `{value}`")
        else:
            logger.error(f"Failed to update config: {update_result.error}")
            await ctx.send("❌ Failed to update configuration. Check the logs for details.")
    
    @command(name="getconfigvalue")
    @has_permissions(administrator=True)
    async def getconfigvalue(self, ctx, key: str):
        """Get a configuration value from the database"""
        # Use the bot's database interface to retrieve the config
        config_result = await self.bot.find_one("bot_config", {"key": key})
        
        if config_result.success and config_result.data:
            value = config_result.data.get("value")
            await ctx.send(f"Configuration `{key}` = `{value}`")
        else:
            if not config_result.success:
                logger.error(f"Failed to retrieve config: {config_result.error}")
            await ctx.send(f"❌ Configuration key `{key}` not found.")

async def setup(bot):
    await bot.add_cog(Admin(bot))
    logger.info("Admin commands cog loaded")
