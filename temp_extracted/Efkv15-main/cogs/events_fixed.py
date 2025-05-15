"""
Events Handler (Fixed Version)

This cog handles various Discord events and provides logging and response functionality.
It follows the compatibility layer implementation for py-cord.
"""

import logging
import datetime
from typing import Optional, Union

from discord_compat_layer import (
    commands, Embed, Color, Member, TextChannel, User, Guild
)

# Set up logging
logger = logging.getLogger(__name__)

class EventsCog(commands.Cog):
    """Event handling for the Discord bot"""
    
    def __init__(self, bot):
        """Initialize the events cog"""
        self.bot = bot
        logger.info("Events Fixed cog initialized")
    
    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        """Called when the bot joins a guild"""
        logger.info(f"Bot joined guild: {guild.name} (ID: {guild.id})")
        
        # Log guild information
        owner = guild.owner
        member_count = guild.member_count
        
        logger.info(f"Guild Info - Owner: {owner}, Members: {member_count}")
        
        # Check if we can find a system channel to send a greeting
        if guild.system_channel and guild.system_channel.permissions_for(guild.me).send_messages:
            try:
                embed = Embed(
                    title="Thanks for adding me!",
                    description="Thank you for adding me to your server. Use `/help` to see available commands.",
                    color=Color.blue()
                )
                
                # Add timestamp
                embed.timestamp = datetime.datetime.now()
                
                # Add bot info
                avatar_url = None
                if hasattr(self.bot.user, 'avatar') and self.bot.user.avatar:
                    avatar_url = self.bot.user.avatar.url
                
                embed.set_footer(text=f"{self.bot.user.name}", icon_url=avatar_url)
                
                await guild.system_channel.send(embed=embed)
            except Exception as e:
                logger.error(f"Failed to send welcome message: {str(e)}")
    
    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        """Called when the bot is removed from a guild"""
        logger.info(f"Bot removed from guild: {guild.name} (ID: {guild.id})")
    
    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Called when a member joins a guild"""
        logger.info(f"Member joined: {member.display_name} (ID: {member.id}) in guild {member.guild.name}")
        
        # Check for auto-role setting in the database
        if hasattr(self.bot, 'db') and self.bot.db:
            try:
                guild_data = await self.bot.db.guilds.find_one({"guild_id": str(member.guild.id)})
                if guild_data and "auto_role_id" in guild_data and guild_data["auto_role_id"]:
                    auto_role_id = int(guild_data["auto_role_id"])
                    role = member.guild.get_role(auto_role_id)
                    if role:
                        await member.add_roles(role)
                        logger.info(f"Added auto-role {role.name} to {member.display_name}")
            except Exception as e:
                logger.error(f"Failed to add auto-role: {str(e)}")
        
        # Check for welcome channel setting in the database
        if hasattr(self.bot, 'db') and self.bot.db:
            try:
                guild_data = await self.bot.db.guilds.find_one({"guild_id": str(member.guild.id)})
                if guild_data and "welcome_channel_id" in guild_data and guild_data["welcome_channel_id"]:
                    welcome_channel_id = int(guild_data["welcome_channel_id"])
                    channel = member.guild.get_channel(welcome_channel_id)
                    if channel and isinstance(channel, TextChannel):
                        embed = Embed(
                            title="Welcome!",
                            description=f"Welcome {member.mention} to {member.guild.name}!",
                            color=Color.green()
                        )
                        embed.timestamp = datetime.datetime.now()
                        
                        # Add member info
                        embed.set_thumbnail(url=member.display_avatar.url if hasattr(member, 'display_avatar') else None)
                        
                        # Add footer
                        embed.set_footer(text=f"Member #{len(member.guild.members)}")
                        
                        await channel.send(embed=embed)
            except Exception as e:
                logger.error(f"Failed to send welcome message: {str(e)}")
    
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Called when a member leaves a guild"""
        logger.info(f"Member left: {member.display_name} (ID: {member.id}) from guild {member.guild.name}")
    
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Global error handler for commands"""
        if isinstance(error, commands.CommandNotFound):
            logger.debug(f"Command not found: {ctx.message.content}")
            return
        
        if isinstance(error, commands.MissingRequiredArgument):
            logger.warning(f"Missing required argument: {error}")
            await ctx.send(f"Missing required argument: {error.param.name}")
            return
        
        if isinstance(error, commands.BadArgument):
            logger.warning(f"Bad argument: {error}")
            await ctx.send(f"Bad argument: {str(error)}")
            return
        
        if isinstance(error, commands.MissingPermissions):
            logger.warning(f"Missing permissions: {error}")
            await ctx.send(f"You don't have permission to use this command.")
            return
        
        if isinstance(error, commands.BotMissingPermissions):
            logger.warning(f"Bot missing permissions: {error}")
            await ctx.send(f"I don't have permission to do that.")
            return
        
        # Log other errors
        logger.error(f"Command error: {error}", exc_info=True)
        
        # Attempt to notify the user
        try:
            await ctx.send(f"An error occurred: {str(error)}")
        except:
            pass

async def setup(bot):
    """Set up the events cog"""
    await bot.add_cog(EventsCog(bot))
    logger.info("Events Fixed cog loaded")