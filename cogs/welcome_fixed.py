"""
Welcome Cog (Fixed Version)

This module provides welcome and farewell message functionality for Discord servers.
It follows the compatibility layer implementation for py-cord.
"""
import logging
import datetime
import asyncio
import re
from typing import Optional, Dict, Any, List, Union

from discord_compat_layer import (
    Embed, Color, commands, Member, Interaction, slash_command,
    User, app_commands, TextChannel, discord
)

from utils.premium_verification import premium_feature_required

logger = logging.getLogger("discord_bot")

# Default templates
DEFAULT_WELCOME = "Welcome to {server}, {user.mention}! We hope you enjoy your stay!"
DEFAULT_FAREWELL = "Goodbye, {user.name}! We're sorry to see you go."

# Variable patterns for substitution
VARIABLE_PATTERNS = {
    "{user}": lambda member: member.display_name if hasattr(member, "display_name") else "User",
    "{user.mention}": lambda member: member.mention if hasattr(member, "mention") else "@User",
    "{user.name}": lambda member: member.name if hasattr(member, "name") else "User",
    "{user.id}": lambda member: str(member.id) if hasattr(member, "id") else "000000000000000000",
    "{server}": lambda guild: guild.name if hasattr(guild, "name") else "Server",
    "{server.id}": lambda guild: str(guild.id) if hasattr(guild, "id") else "000000000000000000",
    "{server.count}": lambda guild: str(guild.member_count) if hasattr(guild, "member_count") else "0",
    "{date}": lambda _: datetime.datetime.now().strftime("%Y-%m-%d"),
    "{time}": lambda _: datetime.datetime.now().strftime("%H:%M:%S"),
    "{datetime}": lambda _: datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
}

class WelcomeCog(commands.Cog):
    """Welcome message system for Discord servers"""
    
    def __init__(self, bot):
        self.bot = bot
        # Use the database from the bot instance
        self.db = bot.db if hasattr(bot, "db") else None
        # Cache for welcome settings
        self.welcome_settings_cache = {}
        logger.info("Welcome Fixed cog initialized")
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Called when the cog is ready"""
        logger.info("Welcome Fixed cog ready")
        
        # Refresh the welcome settings cache
        await self._refresh_settings_cache()
        
        # Create welcome_settings collection if it doesn't exist
        if self.db:
            try:
                # Check if the collection exists
                collections = await self.db.list_collection_names()
                if "welcome_settings" not in collections:
                    # Create the collection
                    await self.db.create_collection("welcome_settings")
                    logger.info("Created welcome_settings collection")
                    
                    # Create indexes for faster lookups
                    await self.db.welcome_settings.create_index([("guild_id", 1)], unique=True)
                    logger.info("Created indexes for welcome_settings collection")
            except Exception as e:
                logger.error(f"Error setting up welcome_settings collection: {e}")
    
    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Called when a member joins a guild"""
        if not member.guild:
            return
            
        # Check if welcome messages are enabled
        await self._send_welcome_message(member)
    
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Called when a member leaves a guild"""
        if not member.guild:
            return
            
        # Check for kicks by looking at audit logs
        is_kick = False
        
        try:
            await asyncio.sleep(1)  # Wait a bit for audit log to update
            async for entry in member.guild.audit_logs(limit=5, action=discord.AuditLogAction.kick):
                if entry.target.id == member.id and (datetime.datetime.utcnow() - entry.created_at).total_seconds() < 5:
                    is_kick = True
                    break
        except Exception as e:
            logger.error(f"Error checking audit logs: {e}")
        
        # Don't send farewell message for kicks
        if is_kick:
            return
            
        # Send farewell message
        await self._send_farewell_message(member)
    
    @slash_command(name="welcome", description="Welcome message configuration")
    async def welcome(self, ctx: Interaction):
        """Welcome message configuration group"""
        pass  # This is just the command group, subcommands handle functionality
    
    @welcome.command(name="setup", description="Set up welcome messages for this server")
    @premium_feature_required(feature_name="welcome")
    @app_commands.describe(
        welcome_channel="The channel where welcome messages will be sent",
        farewell_channel="The channel where farewell messages will be sent (optional)"
    )
    async def welcome_setup(self, ctx: Interaction, welcome_channel: TextChannel, 
                           farewell_channel: Optional[TextChannel] = None):
        """Set up welcome messages for this server"""
        await ctx.response.defer(ephemeral=True)
        
        # Check if in guild
        if not ctx.guild:
            await ctx.followup.send("This command can only be used in a server.", ephemeral=True)
            return
        
        # Check if bot has permissions to send messages in the welcome channel
        if not welcome_channel.permissions_for(ctx.guild.me).send_messages:
            await ctx.followup.send("I don't have permission to send messages in the welcome channel. Please grant me the 'Send Messages' permission and try again.", ephemeral=True)
            return
            
        # Check if bot has permissions to send messages in the farewell channel
        if farewell_channel and not farewell_channel.permissions_for(ctx.guild.me).send_messages:
            await ctx.followup.send("I don't have permission to send messages in the farewell channel. Please grant me the 'Send Messages' permission and try again.", ephemeral=True)
            return
        
        if self.db:
            try:
                # Check if welcome messages are already set up
                existing = await self.db.welcome_settings.find_one({
                    "guild_id": str(ctx.guild.id)
                })
                
                # Determine if this is a new setup or an update
                if existing:
                    # Update existing settings
                    update_data = {
                        "welcome_channel_id": str(welcome_channel.id),
                        "updated_by": str(ctx.user.id),
                        "updated_at": datetime.datetime.now()
                    }
                    
                    # Only update farewell channel if provided
                    if farewell_channel:
                        update_data["farewell_channel_id"] = str(farewell_channel.id)
                    
                    await self.db.welcome_settings.update_one(
                        {"guild_id": str(ctx.guild.id)},
                        {"$set": update_data}
                    )
                    action_text = "updated"
                else:
                    # Create default settings
                    insert_data = {
                        "guild_id": str(ctx.guild.id),
                        "welcome_channel_id": str(welcome_channel.id),
                        "welcome_enabled": True,
                        "welcome_message": DEFAULT_WELCOME,
                        "welcome_embed": True,
                        "welcome_color": "5865F2",  # Discord Blurple
                        "created_by": str(ctx.user.id),
                        "created_at": datetime.datetime.now()
                    }
                    
                    # Add farewell settings if channel provided
                    if farewell_channel:
                        insert_data.update({
                            "farewell_channel_id": str(farewell_channel.id),
                            "farewell_enabled": True,
                            "farewell_message": DEFAULT_FAREWELL,
                            "farewell_embed": True,
                            "farewell_color": "ED4245"  # Discord Red
                        })
                    
                    await self.db.welcome_settings.insert_one(insert_data)
                    action_text = "set up"
                
                # Refresh the settings cache
                await self._refresh_settings_cache()
                
                # Create response
                embed = Embed(
                    title="Welcome Messages Setup",
                    description=f"Welcome messages have been {action_text} successfully.",
                    color=Color.green()
                )
                
                embed.add_field(name="Welcome Channel", value=welcome_channel.mention, inline=True)
                
                if farewell_channel:
                    embed.add_field(name="Farewell Channel", value=farewell_channel.mention, inline=True)
                    
                # Add note about customization
                embed.add_field(
                    name="Next Steps",
                    value="You can customize the welcome and farewell messages using `/welcome message` and `/welcome farewell`.",
                    inline=False
                )
                
                # Show available variables
                variables = ", ".join([f"`{var}`" for var in VARIABLE_PATTERNS.keys()])
                embed.add_field(
                    name="Available Variables",
                    value=f"You can use these variables in your messages: {variables}",
                    inline=False
                )
                
                await ctx.followup.send(embed=embed, ephemeral=True)
                
                # Send example messages
                try:
                    # Example welcome message
                    welcome_embed = Embed(
                        title="Example Welcome Message",
                        description=self._replace_variables(DEFAULT_WELCOME, ctx.user, ctx.guild),
                        color=Color.blurple()
                    )
                    
                    if hasattr(ctx.user, "display_avatar") and ctx.user.display_avatar:
                        welcome_embed.set_thumbnail(url=ctx.user.display_avatar.url)
                        
                    welcome_embed.set_footer(text="This is an example of how welcome messages will appear.")
                    
                    await welcome_channel.send(embed=welcome_embed)
                    
                    # Example farewell message if channel provided
                    if farewell_channel:
                        farewell_embed = Embed(
                            title="Example Farewell Message",
                            description=self._replace_variables(DEFAULT_FAREWELL, ctx.user, ctx.guild),
                            color=Color.red()
                        )
                        
                        if hasattr(ctx.user, "display_avatar") and ctx.user.display_avatar:
                            farewell_embed.set_thumbnail(url=ctx.user.display_avatar.url)
                            
                        farewell_embed.set_footer(text="This is an example of how farewell messages will appear.")
                        
                        await farewell_channel.send(embed=farewell_embed)
                except Exception as e:
                    logger.error(f"Error sending example messages: {e}")
                    await ctx.followup.send(f"Setup completed, but I couldn't send example messages. Error: {str(e)}", ephemeral=True)
                
                # Track command usage
                await self._track_command_usage(ctx, "welcome_setup")
                
            except Exception as e:
                logger.error(f"Error setting up welcome messages: {e}")
                await ctx.followup.send(f"An error occurred while setting up welcome messages: {str(e)}", ephemeral=True)
        else:
            await ctx.followup.send("Welcome messages are not available without database connection.", ephemeral=True)
    
    @welcome.command(name="message", description="Customize the welcome message")
    @premium_feature_required(feature_name="welcome")
    @app_commands.describe(
        message="The welcome message template (use {user.mention}, {server}, etc.)",
        use_embed="Whether to use an embed for the message",
        color="Hex color code for the embed (e.g., FF0000 for red)"
    )
    async def welcome_message(self, ctx: Interaction, message: str, use_embed: Optional[bool] = True, 
                             color: Optional[str] = None):
        """Customize the welcome message"""
        await ctx.response.defer(ephemeral=True)
        
        # Check if in guild
        if not ctx.guild:
            await ctx.followup.send("This command can only be used in a server.", ephemeral=True)
            return
        
        # Validate color if provided
        if color:
            # Remove # if present
            color = color.strip().lstrip('#')
            
            # Check if valid hex color
            if not re.match(r'^(?:[0-9a-fA-F]{3}){1,2}$', color):
                await ctx.followup.send("Invalid color format. Please provide a hex color code (e.g., FF0000 for red).", ephemeral=True)
                return
        
        if self.db:
            try:
                # Check if welcome messages are set up
                settings = await self.db.welcome_settings.find_one({
                    "guild_id": str(ctx.guild.id)
                })
                
                if not settings:
                    await ctx.followup.send("Welcome messages are not set up for this server yet. Use `/welcome setup` to set them up.", ephemeral=True)
                    return
                
                # Update settings
                update_data = {
                    "welcome_message": message,
                    "welcome_embed": use_embed,
                    "updated_by": str(ctx.user.id),
                    "updated_at": datetime.datetime.now()
                }
                
                # Update color if provided
                if color:
                    update_data["welcome_color"] = color
                
                await self.db.welcome_settings.update_one(
                    {"guild_id": str(ctx.guild.id)},
                    {"$set": update_data}
                )
                
                # Refresh the settings cache
                await self._refresh_settings_cache()
                
                # Create response
                embed = Embed(
                    title="Welcome Message Updated",
                    description="Your welcome message has been updated successfully.",
                    color=Color.green()
                )
                
                embed.add_field(name="Message Template", value=message, inline=False)
                embed.add_field(name="Use Embed", value="Yes" if use_embed else "No", inline=True)
                
                if color:
                    embed.add_field(name="Embed Color", value=f"#{color.upper()}", inline=True)
                    # Set the embed color to the specified color for preview
                    try:
                        embed.color = int(color, 16)
                    except ValueError:
                        pass
                
                # Preview with variables replaced
                preview = self._replace_variables(message, ctx.user, ctx.guild)
                embed.add_field(name="Example Preview", value=preview, inline=False)
                
                await ctx.followup.send(embed=embed, ephemeral=True)
                
                # Track command usage
                await self._track_command_usage(ctx, "welcome_message")
                
            except Exception as e:
                logger.error(f"Error updating welcome message: {e}")
                await ctx.followup.send(f"An error occurred while updating the welcome message: {str(e)}", ephemeral=True)
        else:
            await ctx.followup.send("Welcome messages are not available without database connection.", ephemeral=True)
    
    @welcome.command(name="farewell", description="Customize the farewell message")
    @premium_feature_required(feature_name="welcome")
    @app_commands.describe(
        message="The farewell message template (use {user.name}, {server}, etc.)",
        use_embed="Whether to use an embed for the message",
        color="Hex color code for the embed (e.g., FF0000 for red)"
    )
    async def farewell_message(self, ctx: Interaction, message: str, use_embed: Optional[bool] = True, 
                              color: Optional[str] = None):
        """Customize the farewell message"""
        await ctx.response.defer(ephemeral=True)
        
        # Check if in guild
        if not ctx.guild:
            await ctx.followup.send("This command can only be used in a server.", ephemeral=True)
            return
        
        # Validate color if provided
        if color:
            # Remove # if present
            color = color.strip().lstrip('#')
            
            # Check if valid hex color
            if not re.match(r'^(?:[0-9a-fA-F]{3}){1,2}$', color):
                await ctx.followup.send("Invalid color format. Please provide a hex color code (e.g., FF0000 for red).", ephemeral=True)
                return
        
        if self.db:
            try:
                # Check if welcome messages are set up
                settings = await self.db.welcome_settings.find_one({
                    "guild_id": str(ctx.guild.id)
                })
                
                if not settings:
                    await ctx.followup.send("Welcome messages are not set up for this server yet. Use `/welcome setup` to set them up.", ephemeral=True)
                    return
                
                # Check if farewell channel is set
                if not settings.get("farewell_channel_id"):
                    await ctx.followup.send("Farewell messages are not set up for this server. Use `/welcome setup` to set up a farewell channel.", ephemeral=True)
                    return
                
                # Update settings
                update_data = {
                    "farewell_message": message,
                    "farewell_embed": use_embed,
                    "updated_by": str(ctx.user.id),
                    "updated_at": datetime.datetime.now()
                }
                
                # Update color if provided
                if color:
                    update_data["farewell_color"] = color
                
                await self.db.welcome_settings.update_one(
                    {"guild_id": str(ctx.guild.id)},
                    {"$set": update_data}
                )
                
                # Refresh the settings cache
                await self._refresh_settings_cache()
                
                # Create response
                embed = Embed(
                    title="Farewell Message Updated",
                    description="Your farewell message has been updated successfully.",
                    color=Color.green()
                )
                
                embed.add_field(name="Message Template", value=message, inline=False)
                embed.add_field(name="Use Embed", value="Yes" if use_embed else "No", inline=True)
                
                if color:
                    embed.add_field(name="Embed Color", value=f"#{color.upper()}", inline=True)
                    # Set the embed color to the specified color for preview
                    try:
                        embed.color = int(color, 16)
                    except ValueError:
                        pass
                
                # Preview with variables replaced
                preview = self._replace_variables(message, ctx.user, ctx.guild)
                embed.add_field(name="Example Preview", value=preview, inline=False)
                
                await ctx.followup.send(embed=embed, ephemeral=True)
                
                # Track command usage
                await self._track_command_usage(ctx, "farewell_message")
                
            except Exception as e:
                logger.error(f"Error updating farewell message: {e}")
                await ctx.followup.send(f"An error occurred while updating the farewell message: {str(e)}", ephemeral=True)
        else:
            await ctx.followup.send("Welcome messages are not available without database connection.", ephemeral=True)
    
    @welcome.command(name="toggle", description="Enable or disable welcome/farewell messages")
    @premium_feature_required(feature_name="welcome")
    @app_commands.describe(
        welcome_enabled="Whether welcome messages should be enabled",
        farewell_enabled="Whether farewell messages should be enabled"
    )
    async def welcome_toggle(self, ctx: Interaction, welcome_enabled: Optional[bool] = None, 
                            farewell_enabled: Optional[bool] = None):
        """Enable or disable welcome/farewell messages"""
        await ctx.response.defer(ephemeral=True)
        
        # Check if in guild
        if not ctx.guild:
            await ctx.followup.send("This command can only be used in a server.", ephemeral=True)
            return
        
        # Check if at least one parameter is provided
        if welcome_enabled is None and farewell_enabled is None:
            await ctx.followup.send("Please specify at least one option to toggle.", ephemeral=True)
            return
        
        if self.db:
            try:
                # Check if welcome messages are set up
                settings = await self.db.welcome_settings.find_one({
                    "guild_id": str(ctx.guild.id)
                })
                
                if not settings:
                    await ctx.followup.send("Welcome messages are not set up for this server yet. Use `/welcome setup` to set them up.", ephemeral=True)
                    return
                
                # Prepare update data
                update_data = {
                    "updated_by": str(ctx.user.id),
                    "updated_at": datetime.datetime.now()
                }
                
                # Update welcome status if provided
                if welcome_enabled is not None:
                    update_data["welcome_enabled"] = welcome_enabled
                
                # Update farewell status if provided
                if farewell_enabled is not None:
                    # Check if farewell channel is set
                    if farewell_enabled and not settings.get("farewell_channel_id"):
                        await ctx.followup.send("Cannot enable farewell messages: no farewell channel is set. Use `/welcome setup` to set one.", ephemeral=True)
                        return
                    
                    update_data["farewell_enabled"] = farewell_enabled
                
                # Update settings
                await self.db.welcome_settings.update_one(
                    {"guild_id": str(ctx.guild.id)},
                    {"$set": update_data}
                )
                
                # Refresh the settings cache
                await self._refresh_settings_cache()
                
                # Create response
                embed = Embed(
                    title="Welcome Settings Updated",
                    description="Your welcome/farewell settings have been updated.",
                    color=Color.green()
                )
                
                if welcome_enabled is not None:
                    embed.add_field(
                        name="Welcome Messages", 
                        value="Enabled" if welcome_enabled else "Disabled", 
                        inline=True
                    )
                
                if farewell_enabled is not None:
                    embed.add_field(
                        name="Farewell Messages", 
                        value="Enabled" if farewell_enabled else "Disabled", 
                        inline=True
                    )
                
                await ctx.followup.send(embed=embed, ephemeral=True)
                
                # Track command usage
                await self._track_command_usage(ctx, "welcome_toggle")
                
            except Exception as e:
                logger.error(f"Error toggling welcome/farewell messages: {e}")
                await ctx.followup.send(f"An error occurred while updating settings: {str(e)}", ephemeral=True)
        else:
            await ctx.followup.send("Welcome messages are not available without database connection.", ephemeral=True)
    
    @welcome.command(name="test", description="Test welcome and farewell messages")
    @premium_feature_required(feature_name="welcome")
    @app_commands.describe(
        message_type="Which message type to test"
    )
    @app_commands.choices(message_type=[
        app_commands.Choice(name="Welcome Message", value="welcome"),
        app_commands.Choice(name="Farewell Message", value="farewell")
    ])
    async def welcome_test(self, ctx: Interaction, message_type: str = "welcome"):
        """Test welcome and farewell messages"""
        await ctx.response.defer(ephemeral=True)
        
        # Check if in guild
        if not ctx.guild:
            await ctx.followup.send("This command can only be used in a server.", ephemeral=True)
            return
        
        if self.db:
            try:
                # Check if welcome messages are set up
                settings = await self.db.welcome_settings.find_one({
                    "guild_id": str(ctx.guild.id)
                })
                
                if not settings:
                    await ctx.followup.send("Welcome messages are not set up for this server yet. Use `/welcome setup` to set them up.", ephemeral=True)
                    return
                
                if message_type == "welcome":
                    # Check if welcome messages are enabled
                    if not settings.get("welcome_enabled", False):
                        await ctx.followup.send("Welcome messages are disabled. Enable them with `/welcome toggle`.", ephemeral=True)
                        return
                    
                    # Get channel
                    channel_id = settings.get("welcome_channel_id")
                    if not channel_id:
                        await ctx.followup.send("No welcome channel is set. Use `/welcome setup` to set one.", ephemeral=True)
                        return
                    
                    channel = self.bot.get_channel(int(channel_id))
                    if not channel:
                        await ctx.followup.send(f"Could not find welcome channel with ID {channel_id}. The channel may have been deleted.", ephemeral=True)
                        return
                    
                    # Send test message
                    message_template = settings.get("welcome_message", DEFAULT_WELCOME)
                    use_embed = settings.get("welcome_embed", True)
                    color_hex = settings.get("welcome_color", "5865F2")
                    
                    await self._send_formatted_message(
                        channel=channel,
                        template=message_template,
                        member=ctx.user,
                        guild=ctx.guild,
                        use_embed=use_embed,
                        color_hex=color_hex,
                        is_test=True,
                        message_type="welcome"
                    )
                    
                    await ctx.followup.send(f"Test welcome message sent to {channel.mention}.", ephemeral=True)
                else:  # farewell
                    # Check if farewell messages are enabled
                    if not settings.get("farewell_enabled", False):
                        await ctx.followup.send("Farewell messages are disabled. Enable them with `/welcome toggle`.", ephemeral=True)
                        return
                    
                    # Get channel
                    channel_id = settings.get("farewell_channel_id")
                    if not channel_id:
                        await ctx.followup.send("No farewell channel is set. Use `/welcome setup` to set one.", ephemeral=True)
                        return
                    
                    channel = self.bot.get_channel(int(channel_id))
                    if not channel:
                        await ctx.followup.send(f"Could not find farewell channel with ID {channel_id}. The channel may have been deleted.", ephemeral=True)
                        return
                    
                    # Send test message
                    message_template = settings.get("farewell_message", DEFAULT_FAREWELL)
                    use_embed = settings.get("farewell_embed", True)
                    color_hex = settings.get("farewell_color", "ED4245")
                    
                    await self._send_formatted_message(
                        channel=channel,
                        template=message_template,
                        member=ctx.user,
                        guild=ctx.guild,
                        use_embed=use_embed,
                        color_hex=color_hex,
                        is_test=True,
                        message_type="farewell"
                    )
                    
                    await ctx.followup.send(f"Test farewell message sent to {channel.mention}.", ephemeral=True)
                
                # Track command usage
                await self._track_command_usage(ctx, "welcome_test")
                
            except Exception as e:
                logger.error(f"Error testing welcome/farewell message: {e}")
                await ctx.followup.send(f"An error occurred while testing the message: {str(e)}", ephemeral=True)
        else:
            await ctx.followup.send("Welcome messages are not available without database connection.", ephemeral=True)
    
    async def _send_welcome_message(self, member):
        """Send a welcome message when a member joins"""
        if not self.db or not member.guild:
            return
            
        guild_id = str(member.guild.id)
        
        # Check if guild is in cache
        if guild_id not in self.welcome_settings_cache:
            # Refresh cache and check again
            await self._refresh_settings_cache()
            if guild_id not in self.welcome_settings_cache:
                return
                
        settings = self.welcome_settings_cache[guild_id]
        
        # Check if welcome messages are enabled
        if not settings.get("welcome_enabled", False):
            return
            
        # Get channel
        channel_id = settings.get("welcome_channel_id")
        if not channel_id:
            return
            
        try:
            channel = self.bot.get_channel(int(channel_id))
            if not channel:
                channel = await self.bot.fetch_channel(int(channel_id))
                
            if not channel:
                logger.error(f"Could not find welcome channel {channel_id} for guild {guild_id}")
                return
                
            # Get message template and settings
            message_template = settings.get("welcome_message", DEFAULT_WELCOME)
            use_embed = settings.get("welcome_embed", True)
            color_hex = settings.get("welcome_color", "5865F2")
            
            # Send the formatted message
            await self._send_formatted_message(
                channel=channel,
                template=message_template,
                member=member,
                guild=member.guild,
                use_embed=use_embed,
                color_hex=color_hex,
                message_type="welcome"
            )
        except Exception as e:
            logger.error(f"Error sending welcome message: {e}")
    
    async def _send_farewell_message(self, member):
        """Send a farewell message when a member leaves"""
        if not self.db or not member.guild:
            return
            
        guild_id = str(member.guild.id)
        
        # Check if guild is in cache
        if guild_id not in self.welcome_settings_cache:
            # Refresh cache and check again
            await self._refresh_settings_cache()
            if guild_id not in self.welcome_settings_cache:
                return
                
        settings = self.welcome_settings_cache[guild_id]
        
        # Check if farewell messages are enabled
        if not settings.get("farewell_enabled", False):
            return
            
        # Get channel
        channel_id = settings.get("farewell_channel_id")
        if not channel_id:
            return
            
        try:
            channel = self.bot.get_channel(int(channel_id))
            if not channel:
                channel = await self.bot.fetch_channel(int(channel_id))
                
            if not channel:
                logger.error(f"Could not find farewell channel {channel_id} for guild {guild_id}")
                return
                
            # Get message template and settings
            message_template = settings.get("farewell_message", DEFAULT_FAREWELL)
            use_embed = settings.get("farewell_embed", True)
            color_hex = settings.get("farewell_color", "ED4245")
            
            # Send the formatted message
            await self._send_formatted_message(
                channel=channel,
                template=message_template,
                member=member,
                guild=member.guild,
                use_embed=use_embed,
                color_hex=color_hex,
                message_type="farewell"
            )
        except Exception as e:
            logger.error(f"Error sending farewell message: {e}")
    
    async def _send_formatted_message(self, channel, template, member, guild, use_embed=True, 
                                     color_hex="5865F2", is_test=False, message_type="welcome"):
        """Send a formatted message to the specified channel"""
        try:
            # Replace variables in the template
            content = self._replace_variables(template, member, guild)
            
            if use_embed:
                # Parse color
                try:
                    color_int = int(color_hex.strip().lstrip('#'), 16)
                except (ValueError, AttributeError):
                    color_int = 0x5865F2  # Discord Blurple
                
                # Create embed
                embed = Embed(
                    description=content,
                    color=color_int
                )
                
                # Set appropriate title
                if is_test:
                    title = f"Test {message_type.capitalize()} Message"
                    embed.set_footer(text="This is a test message.")
                else:
                    title = "Welcome to the server!" if message_type == "welcome" else "Member Left"
                
                embed.title = title
                
                # Add user avatar as thumbnail
                if hasattr(member, "display_avatar") and member.display_avatar:
                    embed.set_thumbnail(url=member.display_avatar.url)
                    
                # Send with embed
                await channel.send(embed=embed)
            else:
                # Send as plain text
                if is_test:
                    await channel.send(f"**Test {message_type.capitalize()} Message:**\n{content}")
                else:
                    await channel.send(content)
        except Exception as e:
            logger.error(f"Error sending formatted message: {e}")
            raise
    
    def _replace_variables(self, template, member, guild):
        """Replace variables in the template with actual values"""
        result = template
        
        for pattern, replacer in VARIABLE_PATTERNS.items():
            if pattern in result:
                try:
                    # Determine which object to pass to the replacer
                    if pattern.startswith("{user"):
                        value = replacer(member)
                    elif pattern.startswith("{server"):
                        value = replacer(guild)
                    else:
                        value = replacer(None)  # For date/time patterns
                        
                    result = result.replace(pattern, value)
                except Exception as e:
                    logger.error(f"Error replacing variable {pattern}: {e}")
                    # Replace with a safe default if there's an error
                    if pattern.startswith("{user"):
                        result = result.replace(pattern, "User")
                    elif pattern.startswith("{server"):
                        result = result.replace(pattern, "Server")
                    else:
                        result = result.replace(pattern, "")
        
        return result
    
    async def _refresh_settings_cache(self):
        """Refresh the welcome settings cache from the database"""
        if not self.db:
            logger.warning("Cannot refresh welcome settings cache: no database connection")
            return
            
        try:
            # Clear the current cache
            self.welcome_settings_cache = {}
            
            # Get all welcome settings
            cursor = self.db.welcome_settings.find({})
            
            # Index by guild_id
            async for item in cursor:
                guild_id = item.get("guild_id")
                if not guild_id:
                    continue
                    
                self.welcome_settings_cache[guild_id] = item
                
            logger.info(f"Refreshed welcome settings cache: {len(self.welcome_settings_cache)} guilds")
        except Exception as e:
            logger.error(f"Error refreshing welcome settings cache: {e}")
    
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
    """Set up the welcome cog"""
    await bot.add_cog(WelcomeCog(bot))
    logger.info("Welcome Fixed cog loaded")