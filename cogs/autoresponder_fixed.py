"""
Autoresponder Cog (Fixed Version)

This module provides functionality for creating and managing automated responses to triggers.
It follows the compatibility layer implementation for py-cord.
"""
import logging
import re
import datetime
import random
from typing import Optional, Dict, Any, List, Union

from discord_compat_layer import (
    Embed, Color, commands, Member, Interaction, slash_command,
    User, app_commands, Message
)

from utils.premium_verification import premium_feature_required

logger = logging.getLogger("discord_bot")

class AutoresponderCog(commands.Cog):
    """Autoresponder system for the bot"""
    
    def __init__(self, bot):
        self.bot = bot
        # Use the database from the bot instance
        self.db = bot.db if hasattr(bot, "db") else None
        # Cache for autoresponders to avoid database lookups on every message
        self.autoresponder_cache = {}
        logger.info("Autoresponder Fixed cog initialized")
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Called when the cog is ready"""
        logger.info("Autoresponder Fixed cog ready")
        
        # Load autoresponders into cache
        await self._reload_cache()
        
        # Create autoresponder collection if it doesn't exist
        if self.db:
            try:
                # Check if the collection exists
                collections = await self.db.list_collection_names()
                if "autoresponders" not in collections:
                    # Create the collection
                    await self.db.create_collection("autoresponders")
                    logger.info("Created autoresponders collection")
                    
                    # Create indexes for faster lookups
                    await self.db.autoresponders.create_index([("guild_id", 1), ("trigger", 1)], unique=True)
                    logger.info("Created indexes for autoresponders collection")
            except Exception as e:
                logger.error(f"Error setting up autoresponders collection: {e}")
    
    @commands.Cog.listener()
    async def on_message(self, message: Message):
        """Process each message to check for autoresponder triggers"""
        # Ignore messages from bots (including self)
        if message.author.bot:
            return
            
        # Ignore DMs
        if not message.guild:
            return
            
        # Get guild ID
        guild_id = str(message.guild.id)
        
        # Check if we have autoresponders for this guild
        if guild_id not in self.autoresponder_cache:
            # No autoresponders for this guild
            return
            
        # Get the message content
        content = message.content.lower()
        
        # Check each autoresponder
        for responder in self.autoresponder_cache[guild_id]:
            trigger = responder["trigger"].lower()
            match_type = responder.get("match_type", "contains")
            
            is_match = False
            
            # Check based on match type
            if match_type == "contains":
                is_match = trigger in content
            elif match_type == "exact":
                is_match = content == trigger
            elif match_type == "startswith":
                is_match = content.startswith(trigger)
            elif match_type == "endswith":
                is_match = content.endswith(trigger)
            elif match_type == "regex":
                try:
                    is_match = bool(re.search(trigger, content))
                except Exception as e:
                    logger.error(f"Invalid regex pattern '{trigger}': {e}")
            
            # If we have a match, send the response
            if is_match:
                try:
                    # Get a random response if multiple are defined
                    responses = responder["responses"]
                    response = random.choice(responses) if isinstance(responses, list) else responses
                    
                    # Send the response
                    await message.channel.send(response)
                    
                    # Update usage count
                    if self.db:
                        await self.db.autoresponders.update_one(
                            {
                                "guild_id": guild_id,
                                "trigger": responder["trigger"]
                            },
                            {
                                "$inc": {"uses": 1}
                            }
                        )
                        
                        # Update the cache
                        responder["uses"] = responder.get("uses", 0) + 1
                        
                    # Only trigger once per message
                    break
                except Exception as e:
                    logger.error(f"Error sending autoresponder: {e}")
    
    @slash_command(name="autoresp", description="Autoresponder management")
    async def autoresp(self, ctx: Interaction):
        """Autoresponder management group"""
        pass  # This is just the command group, subcommands handle functionality
    
    @autoresp.command(name="add", description="Create a new autoresponder")
    @premium_feature_required(feature_name="autoresponder")
    @app_commands.describe(
        trigger="The text that will trigger the response",
        response="The response message",
        match_type="How to match the trigger text"
    )
    @app_commands.choices(match_type=[
        app_commands.Choice(name="Contains", value="contains"),
        app_commands.Choice(name="Exact Match", value="exact"),
        app_commands.Choice(name="Starts With", value="startswith"),
        app_commands.Choice(name="Ends With", value="endswith"),
        app_commands.Choice(name="Regex Pattern", value="regex")
    ])
    async def autoresp_add(self, ctx: Interaction, trigger: str, response: str, match_type: str = "contains"):
        """Create a new autoresponder"""
        await ctx.response.defer(ephemeral=True)
        
        # Validate input
        if not trigger or not response:
            await ctx.followup.send("Trigger and response are required.", ephemeral=True)
            return
        
        # Check if in guild
        if not ctx.guild:
            await ctx.followup.send("This command can only be used in a server.", ephemeral=True)
            return
        
        # Validate regex pattern if applicable
        if match_type == "regex":
            try:
                re.compile(trigger)
            except re.error:
                await ctx.followup.send("Invalid regex pattern. Please provide a valid regular expression.", ephemeral=True)
                return
        
        if self.db:
            try:
                # Check if trigger already exists
                existing = await self.db.autoresponders.find_one({
                    "guild_id": str(ctx.guild.id),
                    "trigger": trigger
                })
                
                if existing:
                    await ctx.followup.send(f"An autoresponder with this trigger already exists. Use `/autoresp edit` to modify it.", ephemeral=True)
                    return
                
                # Insert new autoresponder
                await self.db.autoresponders.insert_one({
                    "guild_id": str(ctx.guild.id),
                    "trigger": trigger,
                    "responses": [response],
                    "match_type": match_type,
                    "created_by": str(ctx.user.id),
                    "created_at": datetime.datetime.now(),
                    "uses": 0
                })
                
                # Reload cache
                await self._reload_cache()
                
                # Show success message
                embed = Embed(
                    title="Autoresponder Created",
                    description="Your autoresponder has been created successfully.",
                    color=Color.green()
                )
                
                embed.add_field(name="Trigger", value=trigger, inline=True)
                embed.add_field(name="Match Type", value=match_type.capitalize(), inline=True)
                embed.add_field(name="Response", value=response, inline=False)
                
                await ctx.followup.send(embed=embed, ephemeral=True)
                
                # Track command usage
                await self._track_command_usage(ctx, "autoresp_add")
                
            except Exception as e:
                logger.error(f"Error creating autoresponder: {e}")
                await ctx.followup.send(f"An error occurred while creating the autoresponder: {str(e)}", ephemeral=True)
        else:
            await ctx.followup.send("Autoresponders are not available without database connection.", ephemeral=True)
    
    @autoresp.command(name="edit", description="Edit an existing autoresponder")
    @premium_feature_required(feature_name="autoresponder")
    @app_commands.describe(
        trigger="The trigger text of the autoresponder to edit",
        response="The new response message",
        match_type="How to match the trigger text"
    )
    @app_commands.choices(match_type=[
        app_commands.Choice(name="Contains", value="contains"),
        app_commands.Choice(name="Exact Match", value="exact"),
        app_commands.Choice(name="Starts With", value="startswith"),
        app_commands.Choice(name="Ends With", value="endswith"),
        app_commands.Choice(name="Regex Pattern", value="regex")
    ])
    async def autoresp_edit(self, ctx: Interaction, trigger: str, response: str, match_type: Optional[str] = None):
        """Edit an existing autoresponder"""
        await ctx.response.defer(ephemeral=True)
        
        # Validate input
        if not trigger or not response:
            await ctx.followup.send("Trigger and response are required.", ephemeral=True)
            return
        
        # Check if in guild
        if not ctx.guild:
            await ctx.followup.send("This command can only be used in a server.", ephemeral=True)
            return
        
        # Validate regex pattern if applicable
        if match_type == "regex":
            try:
                re.compile(trigger)
            except re.error:
                await ctx.followup.send("Invalid regex pattern. Please provide a valid regular expression.", ephemeral=True)
                return
        
        if self.db:
            try:
                # Find the autoresponder
                existing = await self.db.autoresponders.find_one({
                    "guild_id": str(ctx.guild.id),
                    "trigger": trigger
                })
                
                if not existing:
                    await ctx.followup.send(f"No autoresponder found with the trigger `{trigger}`. Use `/autoresp add` to create it.", ephemeral=True)
                    return
                
                # Prepare update data
                update_data = {
                    "responses": [response],
                    "updated_by": str(ctx.user.id),
                    "updated_at": datetime.datetime.now()
                }
                
                # Include match_type if provided
                if match_type:
                    update_data["match_type"] = match_type
                
                # Update the autoresponder
                await self.db.autoresponders.update_one(
                    {
                        "guild_id": str(ctx.guild.id),
                        "trigger": trigger
                    },
                    {
                        "$set": update_data
                    }
                )
                
                # Reload cache
                await self._reload_cache()
                
                # Show success message
                embed = Embed(
                    title="Autoresponder Updated",
                    description="Your autoresponder has been updated successfully.",
                    color=Color.blue()
                )
                
                embed.add_field(name="Trigger", value=trigger, inline=True)
                embed.add_field(name="Match Type", value=match_type.capitalize() if match_type else existing.get("match_type", "contains").capitalize(), inline=True)
                embed.add_field(name="Response", value=response, inline=False)
                
                await ctx.followup.send(embed=embed, ephemeral=True)
                
                # Track command usage
                await self._track_command_usage(ctx, "autoresp_edit")
                
            except Exception as e:
                logger.error(f"Error editing autoresponder: {e}")
                await ctx.followup.send(f"An error occurred while editing the autoresponder: {str(e)}", ephemeral=True)
        else:
            await ctx.followup.send("Autoresponders are not available without database connection.", ephemeral=True)
    
    @autoresp.command(name="delete", description="Delete an autoresponder")
    @premium_feature_required(feature_name="autoresponder")
    @app_commands.describe(
        trigger="The trigger text of the autoresponder to delete"
    )
    async def autoresp_delete(self, ctx: Interaction, trigger: str):
        """Delete an autoresponder"""
        await ctx.response.defer(ephemeral=True)
        
        # Validate input
        if not trigger:
            await ctx.followup.send("Trigger is required.", ephemeral=True)
            return
        
        # Check if in guild
        if not ctx.guild:
            await ctx.followup.send("This command can only be used in a server.", ephemeral=True)
            return
        
        if self.db:
            try:
                # Find the autoresponder
                existing = await self.db.autoresponders.find_one({
                    "guild_id": str(ctx.guild.id),
                    "trigger": trigger
                })
                
                if not existing:
                    await ctx.followup.send(f"No autoresponder found with the trigger `{trigger}`.", ephemeral=True)
                    return
                
                # Delete the autoresponder
                await self.db.autoresponders.delete_one({
                    "guild_id": str(ctx.guild.id),
                    "trigger": trigger
                })
                
                # Reload cache
                await self._reload_cache()
                
                # Show success message
                embed = Embed(
                    title="Autoresponder Deleted",
                    description=f"The autoresponder with trigger `{trigger}` has been deleted successfully.",
                    color=Color.red()
                )
                
                await ctx.followup.send(embed=embed, ephemeral=True)
                
                # Track command usage
                await self._track_command_usage(ctx, "autoresp_delete")
                
            except Exception as e:
                logger.error(f"Error deleting autoresponder: {e}")
                await ctx.followup.send(f"An error occurred while deleting the autoresponder: {str(e)}", ephemeral=True)
        else:
            await ctx.followup.send("Autoresponders are not available without database connection.", ephemeral=True)
    
    @autoresp.command(name="list", description="List all autoresponders for this server")
    @app_commands.describe(
        page="Page number to view (default: 1)"
    )
    async def autoresp_list(self, ctx: Interaction, page: int = 1):
        """List all autoresponders for this server"""
        await ctx.response.defer()
        
        # Check if in guild
        if not ctx.guild:
            await ctx.followup.send("This command can only be used in a server.")
            return
        
        if self.db:
            try:
                # Calculate pagination
                per_page = 10
                skip = (page - 1) * per_page
                
                # Count total autoresponders
                total = await self.db.autoresponders.count_documents({
                    "guild_id": str(ctx.guild.id)
                })
                
                if total == 0:
                    await ctx.followup.send("No autoresponders have been created for this server yet.")
                    return
                
                # Calculate total pages
                total_pages = (total + per_page - 1) // per_page
                
                # Validate page number
                if page < 1 or page > total_pages:
                    await ctx.followup.send(f"Invalid page number. Please specify a page between 1 and {total_pages}.")
                    return
                
                # Get autoresponders for current page
                cursor = self.db.autoresponders.find({
                    "guild_id": str(ctx.guild.id)
                }).sort("trigger", 1).skip(skip).limit(per_page)
                
                results = []
                async for item in cursor:
                    results.append(item)
                
                # Create embed
                embed = Embed(
                    title=f"Autoresponders for {ctx.guild.name}",
                    description=f"List of autoresponders (Page {page}/{total_pages})",
                    color=Color.blue()
                )
                
                # Add autoresponders to embed
                for item in results:
                    uses = item.get("uses", 0)
                    match_type = item.get("match_type", "contains").capitalize()
                    responses = item.get("responses", ["No response set"])
                    response_preview = responses[0] if responses else "No response"
                    
                    if len(response_preview) > 50:
                        response_preview = response_preview[:47] + "..."
                    
                    embed.add_field(
                        name=f"{item['trigger']} ({uses} uses)",
                        value=f"Match: {match_type}\nResponse: {response_preview}",
                        inline=False
                    )
                
                # Add pagination footer
                embed.set_footer(text=f"Page {page}/{total_pages} • {total} total autoresponders")
                
                await ctx.followup.send(embed=embed)
                
                # Track command usage
                await self._track_command_usage(ctx, "autoresp_list")
                
            except Exception as e:
                logger.error(f"Error listing autoresponders: {e}")
                await ctx.followup.send(f"An error occurred while listing autoresponders: {str(e)}")
        else:
            await ctx.followup.send("Autoresponders are not available without database connection.")
    
    @autoresp.command(name="info", description="Get detailed information about an autoresponder")
    @app_commands.describe(
        trigger="The trigger text of the autoresponder"
    )
    async def autoresp_info(self, ctx: Interaction, trigger: str):
        """Get detailed information about an autoresponder"""
        await ctx.response.defer()
        
        # Validate input
        if not trigger:
            await ctx.followup.send("Trigger is required.")
            return
        
        # Check if in guild
        if not ctx.guild:
            await ctx.followup.send("This command can only be used in a server.")
            return
        
        if self.db:
            try:
                # Find the autoresponder
                item = await self.db.autoresponders.find_one({
                    "guild_id": str(ctx.guild.id),
                    "trigger": trigger
                })
                
                if not item:
                    await ctx.followup.send(f"No autoresponder found with the trigger `{trigger}`.")
                    return
                
                # Create embed
                embed = Embed(
                    title=f"Autoresponder: {trigger}",
                    color=Color.blue()
                )
                
                # Add autoresponder details
                match_type = item.get("match_type", "contains").capitalize()
                embed.add_field(name="Match Type", value=match_type, inline=True)
                embed.add_field(name="Uses", value=str(item.get("uses", 0)), inline=True)
                
                # Add responses
                responses = item.get("responses", ["No response set"])
                for i, response in enumerate(responses):
                    embed.add_field(name=f"Response {i+1}", value=response, inline=False)
                
                # Add metadata
                created_by = item.get("created_by", "Unknown")
                embed.add_field(name="Created By", value=f"<@{created_by}>", inline=True)
                
                created_at = item.get("created_at")
                if created_at:
                    if isinstance(created_at, str):
                        embed.add_field(name="Created At", value=created_at, inline=True)
                    else:
                        embed.add_field(name="Created At", value=created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=True)
                
                # Add update info if available
                if item.get("updated_at"):
                    updated_at = item.get("updated_at")
                    if isinstance(updated_at, str):
                        embed.add_field(name="Last Updated", value=updated_at, inline=True)
                    else:
                        embed.add_field(name="Last Updated", value=updated_at.strftime("%Y-%m-%d %H:%M:%S"), inline=True)
                    
                    updated_by = item.get("updated_by", "Unknown")
                    embed.add_field(name="Updated By", value=f"<@{updated_by}>", inline=True)
                
                await ctx.followup.send(embed=embed)
                
                # Track command usage
                await self._track_command_usage(ctx, "autoresp_info")
                
            except Exception as e:
                logger.error(f"Error getting autoresponder info: {e}")
                await ctx.followup.send(f"An error occurred while fetching autoresponder info: {str(e)}")
        else:
            await ctx.followup.send("Autoresponders are not available without database connection.")
    
    async def _reload_cache(self):
        """Reload the autoresponder cache from the database"""
        if not self.db:
            logger.warning("Cannot reload autoresponder cache: no database connection")
            return
            
        try:
            # Clear the current cache
            self.autoresponder_cache = {}
            
            # Get all autoresponders
            cursor = self.db.autoresponders.find({})
            
            # Group by guild_id
            async for item in cursor:
                guild_id = item.get("guild_id")
                if not guild_id:
                    continue
                    
                if guild_id not in self.autoresponder_cache:
                    self.autoresponder_cache[guild_id] = []
                    
                self.autoresponder_cache[guild_id].append(item)
                
            logger.info(f"Reloaded autoresponder cache: {sum(len(v) for v in self.autoresponder_cache.values())} total autoresponders")
        except Exception as e:
            logger.error(f"Error reloading autoresponder cache: {e}")
    
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
    """Set up the autoresponder cog"""
    await bot.add_cog(AutoresponderCog(bot))
    logger.info("Autoresponder Fixed cog loaded")