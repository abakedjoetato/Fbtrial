"""
Utility Commands Cog (Fixed Version)

This module provides utility commands for the bot.
It follows the compatibility layer implementation for py-cord.
"""
import logging
import asyncio
import datetime
from typing import Optional, Dict, Any, Union

from discord_compat_layer import (
    Embed, Color, commands, Member, Interaction, slash_command,
    User, app_commands
)

logger = logging.getLogger("discord_bot")

class UtilityCog(commands.Cog):
    """Utility commands for the bot"""
    
    def __init__(self, bot):
        self.bot = bot
        # Use the database from the bot instance
        self.db = bot.db if hasattr(bot, "db") else None
        # Dictionary to store active reminders
        self.active_reminders = {}
        logger.info("Utility Fixed cog initialized")
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Called when the cog is ready"""
        logger.info("Utility Fixed cog ready")
    
    @slash_command(name="echo", description="Repeats your message")
    async def echo(self, ctx: Interaction, *, message: str):
        """Echo a message back to the user"""
        await ctx.response.defer()
        
        embed = Embed(
            title="Echo",
            description=message,
            color=Color.blue()
        )
        
        embed.set_footer(text=f"Requested by {ctx.user.display_name}")
        embed.timestamp = datetime.datetime.now()
        
        await ctx.followup.send(embed=embed)
        
        # Track command usage if database is available
        if self.db:
            try:
                await self.bot.update_one(
                    "bot_stats", 
                    {"_id": "stats"}, 
                    {"$inc": {"echo_command_count": 1, "total_commands": 1}},
                    upsert=True
                )
            except Exception as e:
                logger.error(f"Error tracking command usage: {e}")
    
    @slash_command(name="reminder", description="Set a reminder")
    @app_commands.describe(
        time="Time in minutes",
        message="Reminder message"
    )
    async def reminder(self, ctx: Interaction, time: int, *, message: str):
        """Set a reminder for a specified time"""
        # Validate time
        if time <= 0 or time > 1440:  # Max 24 hours (1440 minutes)
            await ctx.response.send_message("Time must be between 1 and 1440 minutes (24 hours).", ephemeral=True)
            return
        
        await ctx.response.defer()
        
        # Calculate when the reminder will trigger
        reminder_time = datetime.datetime.now() + datetime.timedelta(minutes=time)
        formatted_time = reminder_time.strftime("%H:%M:%S on %Y-%m-%d")
        
        # Store in database if available 
        reminder_id = None
        if self.db:
            try:
                result = await self.bot.insert_one(
                    "reminders",
                    {
                        "user_id": str(ctx.user.id),
                        "channel_id": str(ctx.channel.id) if hasattr(ctx, "channel") and ctx.channel else None,
                        "guild_id": str(ctx.guild.id) if hasattr(ctx, "guild") and ctx.guild else None,
                        "message": message,
                        "created_at": datetime.datetime.now(),
                        "remind_at": reminder_time,
                        "completed": False
                    }
                )
                
                if result.success and result.data:
                    reminder_id = str(result.data)
            except Exception as e:
                logger.error(f"Error storing reminder: {e}")
        
        # Create confirmation embed
        embed = Embed(
            title="Reminder Set",
            description=f"I'll remind you about: **{message}**",
            color=Color.green()
        )
        
        embed.add_field(name="Time", value=f"{time} minutes", inline=True)
        embed.add_field(name="Triggers At", value=formatted_time, inline=True)
        
        embed.set_footer(text=f"Requested by {ctx.user.display_name}")
        embed.timestamp = datetime.datetime.now()
        
        await ctx.followup.send(embed=embed)
        
        # Start the reminder task
        reminder_task = asyncio.create_task(
            self._handle_reminder(ctx.user.id, ctx.channel.id if hasattr(ctx, "channel") and ctx.channel else None, time, message, reminder_id)
        )
        
        # Store the task
        key = f"{ctx.user.id}_{datetime.datetime.now().timestamp()}"
        self.active_reminders[key] = reminder_task
        
        # Track command usage if database is available
        if self.db:
            try:
                await self.bot.update_one(
                    "bot_stats", 
                    {"_id": "stats"}, 
                    {"$inc": {"reminder_command_count": 1, "total_commands": 1}},
                    upsert=True
                )
            except Exception as e:
                logger.error(f"Error tracking command usage: {e}")
    
    async def _handle_reminder(self, user_id, channel_id, minutes, message, reminder_id=None):
        """Handle a reminder after the specified time"""
        try:
            # Wait for the specified time
            await asyncio.sleep(minutes * 60)
            
            # Get the user and channel
            user = await self.bot.get_or_fetch_user(user_id)
            channel = None
            
            if channel_id:
                try:
                    channel = await self.bot.get_or_fetch_channel(channel_id)
                except Exception as e:
                    logger.error(f"Could not fetch channel {channel_id}: {e}")
            
            if not user:
                logger.error(f"Could not fetch user {user_id} for reminder")
                return
            
            # Create reminder embed
            embed = Embed(
                title="Reminder",
                description=message,
                color=Color.blue()
            )
            
            embed.set_footer(text="Your scheduled reminder")
            embed.timestamp = datetime.datetime.now()
            
            # Try to send DM first
            try:
                if hasattr(user, "send"):
                    await user.send(embed=embed)
                    dm_sent = True
                else:
                    dm_sent = False
            except Exception:
                dm_sent = False
            
            # If DM failed and we have a channel, send it there
            if not dm_sent and channel:
                try:
                    await channel.send(content=f"<@{user_id}> Here's your reminder:", embed=embed)
                except Exception as e:
                    logger.error(f"Failed to send reminder to channel: {e}")
            
            # Update database if available
            if reminder_id and self.db:
                try:
                    await self.bot.update_one(
                        "reminders",
                        {"_id": reminder_id},
                        {"$set": {"completed": True, "completed_at": datetime.datetime.now()}}
                    )
                except Exception as e:
                    logger.error(f"Error updating reminder status: {e}")
        
        except asyncio.CancelledError:
            logger.info(f"Reminder for user {user_id} was cancelled")
            # Mark as cancelled in database if needed
            if reminder_id and self.db:
                try:
                    await self.bot.update_one(
                        "reminders",
                        {"_id": reminder_id},
                        {"$set": {"cancelled": True, "cancelled_at": datetime.datetime.now()}}
                    )
                except Exception as e:
                    logger.error(f"Error updating reminder cancellation status: {e}")
        except Exception as e:
            logger.error(f"Error in reminder task: {e}")
    
    @slash_command(name="poll", description="Create a simple poll")
    @app_commands.describe(
        question="The poll question",
        option1="First option",
        option2="Second option",
        option3="Third option (optional)",
        option4="Fourth option (optional)"
    )
    async def poll(self, ctx: Interaction, question: str, option1: str, option2: str, 
                  option3: Optional[str] = None, option4: Optional[str] = None):
        """Create a simple poll with up to 4 options"""
        await ctx.response.defer()
        
        # Define emojis for options
        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]
        
        # Create embed
        embed = Embed(
            title="📊 " + question,
            description="React with the corresponding emoji to vote!",
            color=Color.blurple()
        )
        
        # Add options to embed
        options = [option1, option2]
        if option3:
            options.append(option3)
        if option4:
            options.append(option4)
        
        for i, option in enumerate(options):
            embed.add_field(name=f"{emojis[i]} Option {i+1}", value=option, inline=False)
        
        # Set footer
        embed.set_footer(text=f"Poll created by {ctx.user.display_name}")
        embed.timestamp = datetime.datetime.now()
        
        # Send poll message
        poll_message = await ctx.followup.send(embed=embed)
        
        # Add reaction emojis
        for i in range(len(options)):
            if hasattr(poll_message, "add_reaction"):
                await poll_message.add_reaction(emojis[i])
        
        # Track command usage if database is available
        if self.db:
            try:
                await self.bot.update_one(
                    "bot_stats", 
                    {"_id": "stats"}, 
                    {"$inc": {"poll_command_count": 1, "total_commands": 1}},
                    upsert=True
                )
            except Exception as e:
                logger.error(f"Error tracking command usage: {e}")

async def setup(bot):
    """Set up the utility cog"""
    await bot.add_cog(UtilityCog(bot))
    logger.info("Utility Fixed commands cog loaded")