"""
General Commands Cog (Fixed Version)

This module provides general-purpose commands for the bot.
It follows the compatibility layer implementation for py-cord.
"""
import logging
import datetime
from typing import Optional, Dict, Any, Union

from discord_compat_layer import (
    Embed, Color, commands, Member, Interaction, slash_command,
    User, app_commands
)

logger = logging.getLogger("discord_bot")

class GeneralCog(commands.Cog):
    """General purpose commands for the bot"""
    
    def __init__(self, bot):
        self.bot = bot
        # Use the database from the bot instance
        self.db = bot.db if hasattr(bot, "db") else None
        logger.info("General Fixed cog initialized")
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Called when the cog is ready"""
        logger.info("General Fixed cog ready")
    
    @slash_command(name="ping", description="Check the bot's latency")
    async def ping(self, ctx: Interaction):
        """Check the bot's latency"""
        # Defer the response to avoid timeout
        await ctx.response.defer()
        
        # Calculate latency in milliseconds
        latency = round(self.bot.latency * 1000) if hasattr(self.bot, "latency") else 0
        
        embed = Embed(
            title="Bot Latency",
            description=f"🏓 Pong! Bot latency: **{latency}ms**",
            color=Color.green()
        )
        
        await ctx.followup.send(embed=embed)
        
        # Track command usage if database is available
        if self.db:
            try:
                await self.bot.update_one(
                    "bot_stats", 
                    {"_id": "stats"}, 
                    {"$inc": {"ping_command_count": 1, "total_commands": 1}},
                    upsert=True
                )
            except Exception as e:
                logger.error(f"Error tracking command usage: {e}")
    
    @slash_command(name="userinfo", description="Display information about a user")
    async def userinfo(self, ctx: Interaction, member: Optional[Member] = None):
        """Display information about a user"""
        # Defer the response to avoid timeout
        await ctx.response.defer()
        
        # Use provided member or command user if not specified
        member = member or ctx.user
        
        # Initialize user data
        user_data = {"command_count": 0, "message_count": 0, "joined_at": None}
        
        # Get user data from database if available
        if self.db:
            try:
                user_result = await self.bot.find_one("users", {"user_id": str(member.id)})
                if user_result.success and user_result.data:
                    user_data = user_result.data
            except Exception as e:
                logger.error(f"Error retrieving user data: {e}")
        
        # Format join date
        joined_date = member.joined_at.strftime("%Y-%m-%d %H:%M:%S UTC") if hasattr(member, "joined_at") and member.joined_at else "Unknown"
        
        # Format account creation date
        created_date = member.created_at.strftime("%Y-%m-%d %H:%M:%S UTC") if hasattr(member, "created_at") and member.created_at else "Unknown"
        
        # Create the embed
        embed = Embed(
            title=f"User Info - {member.display_name}",
            color=member.color if hasattr(member, "color") else Color.blue()
        )
        
        # Set user avatar as thumbnail
        if hasattr(member, "display_avatar") and member.display_avatar:
            embed.set_thumbnail(url=member.display_avatar.url)
        
        # Add user details
        embed.add_field(name="User ID", value=member.id, inline=True)
        embed.add_field(name="Created Account", value=created_date, inline=True)
        
        if hasattr(member, "joined_at") and member.joined_at:
            embed.add_field(name="Joined Server", value=joined_date, inline=True)
        
        # Add role info if available
        if hasattr(member, "roles") and member.roles:
            # Skip the @everyone role which is always at index 0
            roles = [role.mention for role in member.roles[1:]] if len(member.roles) > 1 else ["No roles"]
            embed.add_field(name=f"Roles ({len(member.roles) - 1})", value=" ".join(roles), inline=False)
        
        # Add database stats if available
        if user_data:
            embed.add_field(name="Commands Used", value=user_data.get("command_count", 0), inline=True)
            embed.add_field(name="Messages Sent", value=user_data.get("message_count", 0), inline=True)
        
        # Add footer with timestamp
        embed.set_footer(text=f"Requested by {ctx.user.display_name}")
        embed.timestamp = datetime.datetime.now()
        
        await ctx.followup.send(embed=embed)
        
        # Track command usage if database is available
        if self.db:
            try:
                await self.bot.update_one(
                    "users", 
                    {"user_id": str(ctx.user.id)}, 
                    {"$inc": {"command_count": 1}},
                    upsert=True
                )
                
                await self.bot.update_one(
                    "bot_stats", 
                    {"_id": "stats"}, 
                    {"$inc": {"userinfo_command_count": 1, "total_commands": 1}},
                    upsert=True
                )
            except Exception as e:
                logger.error(f"Error tracking command usage: {e}")
    
    @slash_command(name="serverinfo", description="Display information about the current server")
    async def serverinfo(self, ctx: Interaction):
        """Display information about the current server"""
        # Defer the response to avoid timeout
        await ctx.response.defer()
        
        # Check if in a guild
        if not ctx.guild:
            await ctx.followup.send("This command can only be used in a server.")
            return
        
        guild = ctx.guild
        
        # Create the embed
        embed = Embed(
            title=f"Server Info - {guild.name}",
            color=Color.blue()
        )
        
        # Set server icon as thumbnail
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        # Add server details
        embed.add_field(name="Server ID", value=guild.id, inline=True)
        embed.add_field(name="Owner", value=f"<@{guild.owner_id}>" if hasattr(guild, "owner_id") else "Unknown", inline=True)
        embed.add_field(name="Created On", value=guild.created_at.strftime("%Y-%m-%d %H:%M:%S UTC"), inline=True)
        
        # Member stats
        member_count = guild.member_count if hasattr(guild, "member_count") else len(guild.members)
        embed.add_field(name="Members", value=member_count, inline=True)
        
        # Channel stats
        text_channels = len([c for c in guild.channels if hasattr(c, "type") and str(c.type) == "text"])
        voice_channels = len([c for c in guild.channels if hasattr(c, "type") and str(c.type) == "voice"])
        embed.add_field(name="Text Channels", value=text_channels, inline=True)
        embed.add_field(name="Voice Channels", value=voice_channels, inline=True)
        
        # Role stats
        embed.add_field(name="Roles", value=len(guild.roles), inline=True)
        
        # Add footer with timestamp
        embed.set_footer(text=f"Requested by {ctx.user.display_name}")
        embed.timestamp = datetime.datetime.now()
        
        await ctx.followup.send(embed=embed)
        
        # Track command usage if database is available
        if self.db:
            try:
                await self.bot.update_one(
                    "bot_stats", 
                    {"_id": "stats"}, 
                    {"$inc": {"serverinfo_command_count": 1, "total_commands": 1}},
                    upsert=True
                )
            except Exception as e:
                logger.error(f"Error tracking command usage: {e}")
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Process each message sent in channels the bot can see"""
        # Ignore messages from bots
        if message.author.bot:
            return
        
        # Log message activity to the database if available
        if self.db:
            try:
                await self.bot.update_one(
                    "users", 
                    {"user_id": str(message.author.id)}, 
                    {
                        "$inc": {"message_count": 1},
                        "$set": {"last_active": datetime.datetime.now()},
                        "$setOnInsert": {"joined_at": datetime.datetime.now()}
                    },
                    upsert=True
                )
                
                await self.bot.update_one(
                    "message_stats", 
                    {"guild_id": str(message.guild.id if message.guild else "dm")}, 
                    {
                        "$inc": {"message_count": 1},
                        "$set": {"last_message": datetime.datetime.now()}
                    },
                    upsert=True
                )
            except Exception as e:
                logger.error(f"Error logging message activity: {e}")

async def setup(bot):
    """Set up the general cog"""
    await bot.add_cog(GeneralCog(bot))
    logger.info("General Fixed commands cog loaded")