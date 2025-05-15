"""
Events Handler

This cog handles various Discord events and provides logging and response functionality.
"""

import logging
import datetime
from typing import Optional, Union

import discord
from discord.ext import commands

# Set up logging
logger = logging.getLogger(__name__)

class Events(commands.Cog):
    """Event handling for the Discord bot"""
    
    def __init__(self, bot):
        """Initialize the events cog"""
        self.bot = bot
        logger.info("Events cog initialized")
    
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
                embed = discord.Embed(
                    title="Thanks for adding me!",
                    description="Thank you for adding me to your server. Use `/help` to see available commands.",
                    color=discord.Color.blue()
                )
                
                # Add timestamp
                embed.timestamp = datetime.datetime.now()
                
                # Add bot info
                embed.set_footer(text=f"{self.bot.user.name}", icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None)
                
                await guild.system_channel.send(embed=embed)
                logger.debug(f"Sent welcome message to {guild.name}")
            except Exception as e:
                logger.error(f"Failed to send welcome message: {e}")
    
    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        """Called when the bot leaves a guild"""
        logger.info(f"Bot left guild: {guild.name} (ID: {guild.id})")
    
    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Called when a member joins a guild"""
        guild = member.guild
        logger.debug(f"Member {member.name} (ID: {member.id}) joined guild {guild.name}")
        
        # Check if we have a welcome channel configured
        try:
            if self.bot.db:
                # Try to get guild configuration
                guild_config = await self.bot.db.guild_configs.find_one({"guild_id": guild.id})
                
                if guild_config and guild_config.get("welcome_channel_id"):
                    welcome_channel_id = guild_config["welcome_channel_id"]
                    welcome_channel = guild.get_channel(welcome_channel_id)
                    
                    if welcome_channel and welcome_channel.permissions_for(guild.me).send_messages:
                        # Get welcome message from config or use default
                        welcome_message = guild_config.get("welcome_message", "Welcome to the server, {user_mention}!")
                        
                        # Format the message
                        formatted_message = welcome_message.format(
                            user_mention=member.mention,
                            user_name=member.name,
                            guild_name=guild.name,
                            member_count=guild.member_count
                        )
                        
                        await welcome_channel.send(formatted_message)
                        logger.debug(f"Sent welcome message for {member.name} in {guild.name}")
        except Exception as e:
            logger.error(f"Failed to send member join message: {e}")
    
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Called when a member leaves a guild"""
        guild = member.guild
        logger.debug(f"Member {member.name} (ID: {member.id}) left guild {guild.name}")
        
        # Similar to on_member_join but for leave messages
        try:
            if self.bot.db:
                # Try to get guild configuration
                guild_config = await self.bot.db.guild_configs.find_one({"guild_id": guild.id})
                
                if guild_config and guild_config.get("leave_channel_id"):
                    leave_channel_id = guild_config["leave_channel_id"]
                    leave_channel = guild.get_channel(leave_channel_id)
                    
                    if leave_channel and leave_channel.permissions_for(guild.me).send_messages:
                        # Get leave message from config or use default
                        leave_message = guild_config.get("leave_message", "{user_name} has left the server.")
                        
                        # Format the message
                        formatted_message = leave_message.format(
                            user_name=member.name,
                            guild_name=guild.name,
                            member_count=guild.member_count
                        )
                        
                        await leave_channel.send(formatted_message)
                        logger.debug(f"Sent leave message for {member.name} in {guild.name}")
        except Exception as e:
            logger.error(f"Failed to send member leave message: {e}")
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Called when a message is sent in a channel the bot can see"""
        # Ignore messages from bots
        if message.author.bot:
            return
            
        # Process mentions of the bot
        if self.bot.user in message.mentions:
            logger.debug(f"Bot mentioned by {message.author.name} in {message.guild.name if message.guild else 'DM'}")
            
            # Respond to mentions if configured
            try:
                if hasattr(self.bot, 'mention_responses_enabled') and self.bot.mention_responses_enabled:
                    if message.guild:
                        await message.channel.send(f"Hello {message.author.mention}! Use `/help` to see my commands.")
                    else:
                        await message.channel.send(f"Hello {message.author.mention}! I don't have many DM commands, but you can use `/help` in a server.")
            except Exception as e:
                logger.error(f"Failed to respond to mention: {e}")

async def setup(bot):
    """Setup function for the events cog"""
    await bot.add_cog(Events(bot))
    logger.info("Events cog loaded")