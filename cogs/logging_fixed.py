"""
Logging Cog (Fixed Version)

This module provides event logging functionality for Discord servers.
It follows the compatibility layer implementation for py-cord.
"""
import logging
import datetime
import re
import asyncio
from typing import Optional, Dict, Any, List, Union

from discord_compat_layer import (
    Embed, Color, commands, Member, Interaction, slash_command,
    User, app_commands, TextChannel, Message, AuditLogEntry,
    discord
)

from utils.premium_verification import premium_feature_required

logger = logging.getLogger("discord_bot")

class LoggingCog(commands.Cog):
    """Event logging system for Discord servers"""
    
    def __init__(self, bot):
        self.bot = bot
        # Use the database from the bot instance
        self.db = bot.db if hasattr(bot, "db") else None
        # Cache for guild logging settings
        self.guild_settings_cache = {}
        # Default log categories
        self.log_categories = [
            "moderation", "messages", "members", "voice", "server", "channels", "roles"
        ]
        logger.info("Logging Fixed cog initialized")
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Called when the cog is ready"""
        logger.info("Logging Fixed cog ready")
        
        # Refresh the guild settings cache
        await self._refresh_guild_settings()
        
        # Create logging_settings collection if it doesn't exist
        if self.db:
            try:
                # Check if the collection exists
                collections = await self.db.list_collection_names()
                if "logging_settings" not in collections:
                    # Create the collection
                    await self.db.create_collection("logging_settings")
                    logger.info("Created logging_settings collection")
                    
                    # Create indexes for faster lookups
                    await self.db.logging_settings.create_index([("guild_id", 1)], unique=True)
                    logger.info("Created indexes for logging_settings collection")
            except Exception as e:
                logger.error(f"Error setting up logging_settings collection: {e}")
    
    @slash_command(name="logging", description="Server event logging configuration")
    async def logging(self, ctx: Interaction):
        """Server event logging configuration group"""
        pass  # This is just the command group, subcommands handle functionality
    
    @logging.command(name="setup", description="Set up event logging for this server")
    @premium_feature_required(feature_name="logging")
    @app_commands.describe(
        log_channel="The channel where log messages will be sent"
    )
    async def logging_setup(self, ctx: Interaction, log_channel: TextChannel):
        """Set up event logging for this server"""
        await ctx.response.defer(ephemeral=True)
        
        # Check if in guild
        if not ctx.guild:
            await ctx.followup.send("This command can only be used in a server.", ephemeral=True)
            return
        
        # Check if bot has permissions to send messages in the channel
        if not log_channel.permissions_for(ctx.guild.me).send_messages:
            await ctx.followup.send("I don't have permission to send messages in that channel. Please grant me the 'Send Messages' permission and try again.", ephemeral=True)
            return
            
        # Check if bot has permissions to embed links
        if not log_channel.permissions_for(ctx.guild.me).embed_links:
            await ctx.followup.send("I don't have permission to embed links in that channel. Please grant me the 'Embed Links' permission and try again.", ephemeral=True)
            return
        
        if self.db:
            try:
                # Check if logging is already set up
                existing = await self.db.logging_settings.find_one({
                    "guild_id": str(ctx.guild.id)
                })
                
                # Determine if this is a new setup or an update
                if existing:
                    # Update existing settings
                    await self.db.logging_settings.update_one(
                        {"guild_id": str(ctx.guild.id)},
                        {
                            "$set": {
                                "log_channel_id": str(log_channel.id),
                                "updated_by": str(ctx.user.id),
                                "updated_at": datetime.datetime.now()
                            }
                        }
                    )
                    action_text = "updated"
                else:
                    # Create default settings with all categories enabled
                    default_categories = {}
                    for category in self.log_categories:
                        default_categories[category] = True
                    
                    # Insert new settings
                    await self.db.logging_settings.insert_one({
                        "guild_id": str(ctx.guild.id),
                        "log_channel_id": str(log_channel.id),
                        "categories": default_categories,
                        "enabled": True,
                        "created_by": str(ctx.user.id),
                        "created_at": datetime.datetime.now()
                    })
                    action_text = "set up"
                
                # Refresh the guild settings cache
                await self._refresh_guild_settings()
                
                # Send a test log message to the channel
                try:
                    test_embed = Embed(
                        title="Logging Setup",
                        description="Event logging has been set up successfully. This is a test message.",
                        color=Color.green()
                    )
                    test_embed.set_footer(text=f"Server ID: {ctx.guild.id}")
                    test_embed.timestamp = datetime.datetime.now()
                    
                    await log_channel.send(embed=test_embed)
                except Exception as e:
                    logger.error(f"Error sending test log message: {e}")
                    await ctx.followup.send(f"Logging was {action_text}, but I couldn't send a test message to the channel. Error: {str(e)}", ephemeral=True)
                    return
                
                # Success message
                embed = Embed(
                    title="Logging Setup",
                    description=f"Event logging has been {action_text} successfully.",
                    color=Color.green()
                )
                
                embed.add_field(name="Log Channel", value=log_channel.mention, inline=True)
                embed.add_field(name="Status", value="Enabled", inline=True)
                
                categories_text = ", ".join([f"`{cat.capitalize()}`" for cat in self.log_categories])
                embed.add_field(name="Enabled Categories", value=categories_text, inline=False)
                
                embed.add_field(name="Note", value="By default, all log categories are enabled. Use `/logging categories` to customize which events are logged.", inline=False)
                
                await ctx.followup.send(embed=embed, ephemeral=True)
                
                # Track command usage
                await self._track_command_usage(ctx, "logging_setup")
                
            except Exception as e:
                logger.error(f"Error setting up logging: {e}")
                await ctx.followup.send(f"An error occurred while setting up logging: {str(e)}", ephemeral=True)
        else:
            await ctx.followup.send("Logging is not available without database connection.", ephemeral=True)
    
    @logging.command(name="status", description="Check the current logging status")
    async def logging_status(self, ctx: Interaction):
        """Check the current logging status"""
        await ctx.response.defer()
        
        # Check if in guild
        if not ctx.guild:
            await ctx.followup.send("This command can only be used in a server.")
            return
        
        if self.db:
            try:
                # Get logging settings
                settings = await self.db.logging_settings.find_one({
                    "guild_id": str(ctx.guild.id)
                })
                
                if not settings:
                    await ctx.followup.send("Logging has not been set up for this server yet. Use `/logging setup` to set it up.")
                    return
                
                # Create embed
                embed = Embed(
                    title="Logging Status",
                    color=Color.blue()
                )
                
                # Add basic info
                channel_id = settings.get("log_channel_id")
                enabled = settings.get("enabled", False)
                
                channel_mention = f"<#{channel_id}>" if channel_id else "Not set"
                status = "Enabled" if enabled else "Disabled"
                
                embed.add_field(name="Log Channel", value=channel_mention, inline=True)
                embed.add_field(name="Status", value=status, inline=True)
                
                # Add categories
                categories = settings.get("categories", {})
                
                enabled_cats = []
                disabled_cats = []
                
                for cat in self.log_categories:
                    if categories.get(cat, False):
                        enabled_cats.append(cat.capitalize())
                    else:
                        disabled_cats.append(cat.capitalize())
                
                if enabled_cats:
                    embed.add_field(name="Enabled Categories", value=", ".join(enabled_cats), inline=False)
                
                if disabled_cats:
                    embed.add_field(name="Disabled Categories", value=", ".join(disabled_cats), inline=False)
                
                await ctx.followup.send(embed=embed)
                
                # Track command usage
                await self._track_command_usage(ctx, "logging_status")
                
            except Exception as e:
                logger.error(f"Error checking logging status: {e}")
                await ctx.followup.send(f"An error occurred while checking logging status: {str(e)}")
        else:
            await ctx.followup.send("Logging is not available without database connection.")
    
    @logging.command(name="toggle", description="Enable or disable logging")
    @premium_feature_required(feature_name="logging")
    @app_commands.describe(
        enabled="Whether logging should be enabled or disabled"
    )
    async def logging_toggle(self, ctx: Interaction, enabled: bool):
        """Enable or disable logging"""
        await ctx.response.defer(ephemeral=True)
        
        # Check if in guild
        if not ctx.guild:
            await ctx.followup.send("This command can only be used in a server.", ephemeral=True)
            return
        
        if self.db:
            try:
                # Check if logging is set up
                settings = await self.db.logging_settings.find_one({
                    "guild_id": str(ctx.guild.id)
                })
                
                if not settings:
                    await ctx.followup.send("Logging has not been set up for this server yet. Use `/logging setup` to set it up.", ephemeral=True)
                    return
                
                # Update logging status
                await self.db.logging_settings.update_one(
                    {"guild_id": str(ctx.guild.id)},
                    {
                        "$set": {
                            "enabled": enabled,
                            "updated_by": str(ctx.user.id),
                            "updated_at": datetime.datetime.now()
                        }
                    }
                )
                
                # Refresh the guild settings cache
                await self._refresh_guild_settings()
                
                # Create response
                status_text = "enabled" if enabled else "disabled"
                
                embed = Embed(
                    title="Logging Status Updated",
                    description=f"Logging has been {status_text} for this server.",
                    color=Color.green() if enabled else Color.red()
                )
                
                await ctx.followup.send(embed=embed, ephemeral=True)
                
                # Track command usage
                await self._track_command_usage(ctx, "logging_toggle")
                
            except Exception as e:
                logger.error(f"Error toggling logging: {e}")
                await ctx.followup.send(f"An error occurred while toggling logging: {str(e)}", ephemeral=True)
        else:
            await ctx.followup.send("Logging is not available without database connection.", ephemeral=True)
    
    @logging.command(name="categories", description="Configure which event categories are logged")
    @premium_feature_required(feature_name="logging")
    @app_commands.describe(
        category="The event category to configure",
        enabled="Whether this category should be logged"
    )
    @app_commands.choices(category=[
        app_commands.Choice(name="Moderation (bans, kicks, mutes)", value="moderation"),
        app_commands.Choice(name="Messages (edits, deletions)", value="messages"),
        app_commands.Choice(name="Members (joins, leaves, updates)", value="members"),
        app_commands.Choice(name="Voice (joins, moves, leaves)", value="voice"),
        app_commands.Choice(name="Server (settings, updates)", value="server"),
        app_commands.Choice(name="Channels (creation, deletion, updates)", value="channels"),
        app_commands.Choice(name="Roles (creation, deletion, updates)", value="roles")
    ])
    async def logging_categories(self, ctx: Interaction, category: str, enabled: bool):
        """Configure which event categories are logged"""
        await ctx.response.defer(ephemeral=True)
        
        # Check if in guild
        if not ctx.guild:
            await ctx.followup.send("This command can only be used in a server.", ephemeral=True)
            return
        
        if self.db:
            try:
                # Check if logging is set up
                settings = await self.db.logging_settings.find_one({
                    "guild_id": str(ctx.guild.id)
                })
                
                if not settings:
                    await ctx.followup.send("Logging has not been set up for this server yet. Use `/logging setup` to set it up.", ephemeral=True)
                    return
                
                # Update category setting
                await self.db.logging_settings.update_one(
                    {"guild_id": str(ctx.guild.id)},
                    {
                        "$set": {
                            f"categories.{category}": enabled,
                            "updated_by": str(ctx.user.id),
                            "updated_at": datetime.datetime.now()
                        }
                    }
                )
                
                # Refresh the guild settings cache
                await self._refresh_guild_settings()
                
                # Create response
                status_text = "enabled" if enabled else "disabled"
                
                embed = Embed(
                    title="Logging Category Updated",
                    description=f"The `{category}` category has been {status_text} for this server.",
                    color=Color.green() if enabled else Color.red()
                )
                
                await ctx.followup.send(embed=embed, ephemeral=True)
                
                # Track command usage
                await self._track_command_usage(ctx, "logging_categories")
                
            except Exception as e:
                logger.error(f"Error configuring logging categories: {e}")
                await ctx.followup.send(f"An error occurred while configuring logging categories: {str(e)}", ephemeral=True)
        else:
            await ctx.followup.send("Logging is not available without database connection.", ephemeral=True)
    
    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Called when a member joins a guild"""
        if not member.guild:
            return
            
        await self._log_event(
            guild_id=member.guild.id,
            category="members",
            title="Member Joined",
            description=f"{member.mention} ({member.name}#{member.discriminator}) joined the server.",
            fields=[
                {"name": "User ID", "value": str(member.id), "inline": True},
                {"name": "Account Created", "value": member.created_at.strftime("%Y-%m-%d %H:%M:%S UTC"), "inline": True}
            ],
            color=Color.green(),
            thumbnail=member.display_avatar.url if hasattr(member, "display_avatar") else None
        )
    
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Called when a member leaves a guild"""
        if not member.guild:
            return
            
        # Try to get audit log to determine if this was a kick
        reason = None
        moderator = None
        is_kick = False
        
        try:
            # Wait a brief moment for audit log to be updated
            await asyncio.sleep(1)
            async for entry in member.guild.audit_logs(limit=5, action=discord.AuditLogAction.kick):
                if entry.target.id == member.id and (datetime.datetime.now() - entry.created_at).total_seconds() < 5:
                    is_kick = True
                    reason = entry.reason
                    moderator = entry.user
                    break
        except Exception as e:
            logger.error(f"Error checking audit logs for kicks: {e}")
        
        if is_kick:
            # Log as a kick
            await self._log_event(
                guild_id=member.guild.id,
                category="moderation",
                title="Member Kicked",
                description=f"{member.mention} ({member.name}#{member.discriminator}) was kicked from the server.",
                fields=[
                    {"name": "User ID", "value": str(member.id), "inline": True},
                    {"name": "Moderator", "value": f"{moderator.mention} ({moderator.name}#{moderator.discriminator})" if moderator else "Unknown", "inline": True},
                    {"name": "Reason", "value": reason or "No reason provided", "inline": False}
                ],
                color=Color.orange(),
                thumbnail=member.display_avatar.url if hasattr(member, "display_avatar") else None
            )
        else:
            # Log as a leave
            await self._log_event(
                guild_id=member.guild.id,
                category="members",
                title="Member Left",
                description=f"{member.mention} ({member.name}#{member.discriminator}) left the server.",
                fields=[
                    {"name": "User ID", "value": str(member.id), "inline": True},
                    {"name": "Joined At", "value": member.joined_at.strftime("%Y-%m-%d %H:%M:%S UTC") if member.joined_at else "Unknown", "inline": True}
                ],
                color=Color.red(),
                thumbnail=member.display_avatar.url if hasattr(member, "display_avatar") else None
            )
    
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        """Called when a message is deleted"""
        if not message.guild or message.author.bot:
            return
        
        # Don't log empty messages or those with only embeds
        if not message.content and not message.attachments:
            return
        
        fields = [
            {"name": "Author", "value": f"{message.author.mention} ({message.author.name}#{message.author.discriminator})", "inline": True},
            {"name": "Channel", "value": message.channel.mention, "inline": True}
        ]
        
        # Add message content if available
        if message.content:
            # Truncate long messages
            content = message.content
            if len(content) > 1024:
                content = content[:1021] + "..."
            fields.append({"name": "Content", "value": content, "inline": False})
        
        # Add attachments if available
        if message.attachments:
            attachment_links = []
            for attachment in message.attachments:
                attachment_links.append(f"[{attachment.filename}]({attachment.url})")
            
            if attachment_links:
                fields.append({"name": "Attachments", "value": "\n".join(attachment_links), "inline": False})
        
        await self._log_event(
            guild_id=message.guild.id,
            category="messages",
            title="Message Deleted",
            description=f"A message was deleted in {message.channel.mention}.",
            fields=fields,
            color=Color.red()
        )
    
    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        """Called when a message is edited"""
        if not before.guild or before.author.bot:
            return
            
        # Ignore if content didn't change (e.g., embed was added)
        if before.content == after.content:
            return
        
        # Ignore empty messages
        if not before.content and not after.content:
            return
        
        fields = [
            {"name": "Author", "value": f"{before.author.mention} ({before.author.name}#{before.author.discriminator})", "inline": True},
            {"name": "Channel", "value": before.channel.mention, "inline": True},
            {"name": "Jump to Message", "value": f"[Click Here]({after.jump_url})", "inline": True}
        ]
        
        # Add before content
        if before.content:
            # Truncate long messages
            content = before.content
            if len(content) > 1024:
                content = content[:1021] + "..."
            fields.append({"name": "Before", "value": content, "inline": False})
        
        # Add after content
        if after.content:
            # Truncate long messages
            content = after.content
            if len(content) > 1024:
                content = content[:1021] + "..."
            fields.append({"name": "After", "value": content, "inline": False})
        
        await self._log_event(
            guild_id=before.guild.id,
            category="messages",
            title="Message Edited",
            description=f"A message was edited in {before.channel.mention}.",
            fields=fields,
            color=Color.blue()
        )
    
    async def _log_event(self, guild_id, category, title, description, fields=None, color=None, thumbnail=None, image=None):
        """Log an event to the configured channel if enabled"""
        if not self.db:
            return
        
        # Check if logging is enabled for this guild and category
        guild_id_str = str(guild_id)
        if guild_id_str not in self.guild_settings_cache:
            # Refresh cache and check again
            await self._refresh_guild_settings()
            if guild_id_str not in self.guild_settings_cache:
                return
        
        settings = self.guild_settings_cache[guild_id_str]
        
        # Check if logging is enabled
        if not settings.get("enabled", False):
            return
            
        # Check if this category is enabled
        categories = settings.get("categories", {})
        if not categories.get(category, False):
            return
            
        # Get the log channel
        channel_id = settings.get("log_channel_id")
        if not channel_id:
            return
            
        try:
            channel = self.bot.get_channel(int(channel_id))
            if not channel:
                channel = await self.bot.fetch_channel(int(channel_id))
            
            if not channel:
                logger.error(f"Could not find logging channel {channel_id} for guild {guild_id}")
                return
                
            # Create the embed
            embed = Embed(
                title=title,
                description=description,
                color=color or Color.blue()
            )
            
            # Add fields
            if fields:
                for field in fields:
                    embed.add_field(name=field["name"], value=field["value"], inline=field.get("inline", False))
            
            # Add thumbnail
            if thumbnail:
                embed.set_thumbnail(url=thumbnail)
                
            # Add image
            if image:
                embed.set_image(url=image)
                
            # Add timestamp and footer
            embed.timestamp = datetime.datetime.now()
            embed.set_footer(text=f"Category: {category.capitalize()}")
            
            # Send the embed
            await channel.send(embed=embed)
        except Exception as e:
            logger.error(f"Error logging event to channel {channel_id}: {e}")
    
    async def _refresh_guild_settings(self):
        """Refresh the guild settings cache from the database"""
        if not self.db:
            logger.warning("Cannot refresh guild settings cache: no database connection")
            return
            
        try:
            # Clear the current cache
            self.guild_settings_cache = {}
            
            # Get all logging settings
            cursor = self.db.logging_settings.find({})
            
            # Index by guild_id
            async for item in cursor:
                guild_id = item.get("guild_id")
                if not guild_id:
                    continue
                    
                self.guild_settings_cache[guild_id] = item
                
            logger.info(f"Refreshed logging settings cache: {len(self.guild_settings_cache)} guilds")
        except Exception as e:
            logger.error(f"Error refreshing guild settings cache: {e}")
    
    async def _track_command_usage(self, ctx: Interaction, command_name: str):
        """Track command usage in database"""
        if not self.db:
            return
            
        try:
            # Update bot stats
            await self.bot.update_one(
                "bot_stats", 
                {"_id": "stats"}, 
                {"$inc": {f"{command_name}_count": 1, "total_commands": 1}},
                upsert=True
            )
            
            # Update user stats
            await self.bot.update_one(
                "users", 
                {"user_id": str(ctx.user.id)}, 
                {"$inc": {"command_count": 1}},
                upsert=True
            )
        except Exception as e:
            logger.error(f"Error tracking command usage: {e}")

async def setup(bot):
    """Set up the logging cog"""
    await bot.add_cog(LoggingCog(bot))
    logger.info("Logging Fixed cog loaded")