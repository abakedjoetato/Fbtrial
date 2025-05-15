"""
Custom Commands Cog (Fixed Version)

This module provides functionality for creating and managing custom commands.
It follows the compatibility layer implementation for py-cord.
"""
import logging
import re
import datetime
import json
from typing import Optional, Dict, Any, List, Union

from discord_compat_layer import (
    Embed, Color, commands, Member, Interaction, slash_command,
    User, app_commands
)

from utils.premium_verification import premium_feature_required

logger = logging.getLogger("discord_bot")

# Define variable patterns for substitution
VARIABLE_PATTERNS = {
    "{user}": lambda ctx: ctx.user.display_name if hasattr(ctx, "user") else "User",
    "{user.mention}": lambda ctx: ctx.user.mention if hasattr(ctx, "user") else "@User",
    "{user.id}": lambda ctx: str(ctx.user.id) if hasattr(ctx, "user") else "000000000000000000",
    "{server}": lambda ctx: ctx.guild.name if hasattr(ctx, "guild") and ctx.guild else "DM",
    "{server.id}": lambda ctx: str(ctx.guild.id) if hasattr(ctx, "guild") and ctx.guild else "000000000000000000",
    "{server.count}": lambda ctx: str(ctx.guild.member_count) if hasattr(ctx, "guild") and ctx.guild and hasattr(ctx.guild, "member_count") else "0",
    "{channel}": lambda ctx: ctx.channel.name if hasattr(ctx, "channel") and ctx.channel else "DM",
    "{channel.mention}": lambda ctx: ctx.channel.mention if hasattr(ctx, "channel") and ctx.channel else "#channel",
    "{channel.id}": lambda ctx: str(ctx.channel.id) if hasattr(ctx, "channel") and ctx.channel else "000000000000000000",
    "{date}": lambda ctx: datetime.datetime.now().strftime("%Y-%m-%d"),
    "{time}": lambda ctx: datetime.datetime.now().strftime("%H:%M:%S"),
    "{datetime}": lambda ctx: datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
}

class CustomCommandsCog(commands.Cog):
    """Custom commands for the bot"""
    
    def __init__(self, bot):
        self.bot = bot
        # Use the database from the bot instance
        self.db = bot.db if hasattr(bot, "db") else None
        logger.info("Custom Commands Fixed cog initialized")
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Called when the cog is ready"""
        logger.info("Custom Commands Fixed cog ready")
        
        # Create custom commands collection if it doesn't exist
        if self.db:
            try:
                # Check if the collection exists
                collections = await self.db.list_collection_names()
                if "custom_commands" not in collections:
                    # Create the collection
                    await self.db.create_collection("custom_commands")
                    logger.info("Created custom_commands collection")
                    
                    # Create indexes for faster lookups
                    await self.db.custom_commands.create_index([("guild_id", 1), ("name", 1)], unique=True)
                    logger.info("Created indexes for custom_commands collection")
            except Exception as e:
                logger.error(f"Error setting up custom commands collection: {e}")
    
    @slash_command(name="cmd", description="Custom commands management")
    async def cmd(self, ctx: Interaction):
        """Custom commands management group"""
        pass  # This is just the command group, subcommands handle functionality
    
    @cmd.command(name="add", description="Create a custom command")
    @premium_feature_required(feature_name="custom_commands")
    @app_commands.describe(
        name="Name of the custom command",
        response="Response for the command (can include variables like {user}, {server}, etc.)"
    )
    async def cmd_add(self, ctx: Interaction, name: str, response: str):
        """Create a custom command"""
        await ctx.response.defer(ephemeral=True)
        
        # Validate input
        if not name or not response:
            await ctx.followup.send("Command name and response are required.", ephemeral=True)
            return
        
        # Check if in guild
        if not ctx.guild:
            await ctx.followup.send("This command can only be used in a server.", ephemeral=True)
            return
        
        # Sanitize command name
        name = name.lower().strip()
        
        # Check if name is valid (alphanumeric with underscores)
        if not re.match(r'^[a-z0-9_]+$', name):
            await ctx.followup.send("Command name must only contain lowercase letters, numbers, and underscores.", ephemeral=True)
            return
        
        # Check for reserved names
        if name in ["help", "add", "edit", "delete", "list", "info"]:
            await ctx.followup.send("That name is reserved and cannot be used for custom commands.", ephemeral=True)
            return
        
        # Check if command exists
        if self.db:
            try:
                existing_cmd = await self.db.custom_commands.find_one({
                    "guild_id": str(ctx.guild.id),
                    "name": name
                })
                
                if existing_cmd:
                    await ctx.followup.send(f"A command with the name `{name}` already exists. Use `/cmd edit` to modify it.", ephemeral=True)
                    return
                
                # Insert new command
                await self.db.custom_commands.insert_one({
                    "guild_id": str(ctx.guild.id),
                    "name": name,
                    "response": response,
                    "created_by": str(ctx.user.id),
                    "created_at": datetime.datetime.now(),
                    "uses": 0
                })
                
                # Show success message with preview
                embed = Embed(
                    title=f"Custom Command Created: {name}",
                    description="Your command has been created successfully.",
                    color=Color.green()
                )
                
                # Show response preview
                embed.add_field(name="Response Template", value=response, inline=False)
                
                # Show example with variables replaced
                example = self._replace_variables(response, ctx)
                embed.add_field(name="Example Output", value=example, inline=False)
                
                # Add usage info
                embed.add_field(name="Usage", value=f"`/custom {name}`", inline=False)
                
                # Show available variables
                variables = ", ".join([f"`{var}`" for var in VARIABLE_PATTERNS.keys()])
                embed.add_field(name="Available Variables", value=variables, inline=False)
                
                await ctx.followup.send(embed=embed, ephemeral=True)
                
                # Track command usage
                await self._track_command_usage(ctx, "cmd_add")
                
            except Exception as e:
                logger.error(f"Error creating custom command: {e}")
                await ctx.followup.send(f"An error occurred while creating the command: {str(e)}", ephemeral=True)
        else:
            await ctx.followup.send("Custom commands are not available without database connection.", ephemeral=True)
    
    @cmd.command(name="edit", description="Edit an existing custom command")
    @premium_feature_required(feature_name="custom_commands")
    @app_commands.describe(
        name="Name of the custom command to edit",
        response="New response for the command"
    )
    async def cmd_edit(self, ctx: Interaction, name: str, response: str):
        """Edit an existing custom command"""
        await ctx.response.defer(ephemeral=True)
        
        # Validate input
        if not name or not response:
            await ctx.followup.send("Command name and response are required.", ephemeral=True)
            return
        
        # Check if in guild
        if not ctx.guild:
            await ctx.followup.send("This command can only be used in a server.", ephemeral=True)
            return
        
        # Sanitize command name
        name = name.lower().strip()
        
        if self.db:
            try:
                # Find the command
                existing_cmd = await self.db.custom_commands.find_one({
                    "guild_id": str(ctx.guild.id),
                    "name": name
                })
                
                if not existing_cmd:
                    await ctx.followup.send(f"No command found with the name `{name}`. Use `/cmd add` to create it.", ephemeral=True)
                    return
                
                # Update the command
                await self.db.custom_commands.update_one(
                    {
                        "guild_id": str(ctx.guild.id),
                        "name": name
                    },
                    {
                        "$set": {
                            "response": response,
                            "updated_by": str(ctx.user.id),
                            "updated_at": datetime.datetime.now()
                        }
                    }
                )
                
                # Show success message with preview
                embed = Embed(
                    title=f"Custom Command Updated: {name}",
                    description="Your command has been updated successfully.",
                    color=Color.blue()
                )
                
                # Show response preview
                embed.add_field(name="Response Template", value=response, inline=False)
                
                # Show example with variables replaced
                example = self._replace_variables(response, ctx)
                embed.add_field(name="Example Output", value=example, inline=False)
                
                # Add usage info
                embed.add_field(name="Usage", value=f"`/custom {name}`", inline=False)
                
                await ctx.followup.send(embed=embed, ephemeral=True)
                
                # Track command usage
                await self._track_command_usage(ctx, "cmd_edit")
                
            except Exception as e:
                logger.error(f"Error editing custom command: {e}")
                await ctx.followup.send(f"An error occurred while editing the command: {str(e)}", ephemeral=True)
        else:
            await ctx.followup.send("Custom commands are not available without database connection.", ephemeral=True)
    
    @cmd.command(name="delete", description="Delete a custom command")
    @premium_feature_required(feature_name="custom_commands")
    @app_commands.describe(
        name="Name of the custom command to delete"
    )
    async def cmd_delete(self, ctx: Interaction, name: str):
        """Delete a custom command"""
        await ctx.response.defer(ephemeral=True)
        
        # Validate input
        if not name:
            await ctx.followup.send("Command name is required.", ephemeral=True)
            return
        
        # Check if in guild
        if not ctx.guild:
            await ctx.followup.send("This command can only be used in a server.", ephemeral=True)
            return
        
        # Sanitize command name
        name = name.lower().strip()
        
        if self.db:
            try:
                # Find the command
                existing_cmd = await self.db.custom_commands.find_one({
                    "guild_id": str(ctx.guild.id),
                    "name": name
                })
                
                if not existing_cmd:
                    await ctx.followup.send(f"No command found with the name `{name}`.", ephemeral=True)
                    return
                
                # Delete the command
                await self.db.custom_commands.delete_one({
                    "guild_id": str(ctx.guild.id),
                    "name": name
                })
                
                # Show success message
                embed = Embed(
                    title=f"Custom Command Deleted: {name}",
                    description="The command has been deleted successfully.",
                    color=Color.red()
                )
                
                await ctx.followup.send(embed=embed, ephemeral=True)
                
                # Track command usage
                await self._track_command_usage(ctx, "cmd_delete")
                
            except Exception as e:
                logger.error(f"Error deleting custom command: {e}")
                await ctx.followup.send(f"An error occurred while deleting the command: {str(e)}", ephemeral=True)
        else:
            await ctx.followup.send("Custom commands are not available without database connection.", ephemeral=True)
    
    @cmd.command(name="list", description="List all custom commands for this server")
    @app_commands.describe(
        page="Page number to view (default: 1)"
    )
    async def cmd_list(self, ctx: Interaction, page: int = 1):
        """List all custom commands for this server"""
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
                
                # Count total commands
                total_commands = await self.db.custom_commands.count_documents({
                    "guild_id": str(ctx.guild.id)
                })
                
                if total_commands == 0:
                    await ctx.followup.send("No custom commands have been created for this server yet.")
                    return
                
                # Calculate total pages
                total_pages = (total_commands + per_page - 1) // per_page
                
                # Validate page number
                if page < 1 or page > total_pages:
                    await ctx.followup.send(f"Invalid page number. Please specify a page between 1 and {total_pages}.")
                    return
                
                # Get commands for current page
                commands_cursor = self.db.custom_commands.find({
                    "guild_id": str(ctx.guild.id)
                }).sort("name", 1).skip(skip).limit(per_page)
                
                commands_list = []
                async for cmd in commands_cursor:
                    commands_list.append(cmd)
                
                # Create embed
                embed = Embed(
                    title=f"Custom Commands for {ctx.guild.name}",
                    description=f"List of custom commands (Page {page}/{total_pages})",
                    color=Color.blue()
                )
                
                # Add commands to embed
                for cmd in commands_list:
                    uses = cmd.get("uses", 0)
                    creator_id = cmd.get("created_by", "Unknown")
                    
                    embed.add_field(
                        name=f"{cmd['name']} ({uses} uses)",
                        value=f"Created by: <@{creator_id}>\nResponse: {cmd['response'][:50]}{'...' if len(cmd['response']) > 50 else ''}",
                        inline=False
                    )
                
                # Add pagination footer
                embed.set_footer(text=f"Page {page}/{total_pages} • {total_commands} total commands")
                
                await ctx.followup.send(embed=embed)
                
                # Track command usage
                await self._track_command_usage(ctx, "cmd_list")
                
            except Exception as e:
                logger.error(f"Error listing custom commands: {e}")
                await ctx.followup.send(f"An error occurred while listing commands: {str(e)}")
        else:
            await ctx.followup.send("Custom commands are not available without database connection.")
    
    @cmd.command(name="info", description="Get detailed information about a custom command")
    @app_commands.describe(
        name="Name of the custom command"
    )
    async def cmd_info(self, ctx: Interaction, name: str):
        """Get detailed information about a custom command"""
        await ctx.response.defer()
        
        # Validate input
        if not name:
            await ctx.followup.send("Command name is required.")
            return
        
        # Check if in guild
        if not ctx.guild:
            await ctx.followup.send("This command can only be used in a server.")
            return
        
        # Sanitize command name
        name = name.lower().strip()
        
        if self.db:
            try:
                # Find the command
                cmd = await self.db.custom_commands.find_one({
                    "guild_id": str(ctx.guild.id),
                    "name": name
                })
                
                if not cmd:
                    await ctx.followup.send(f"No command found with the name `{name}`.")
                    return
                
                # Create embed
                embed = Embed(
                    title=f"Custom Command: {name}",
                    color=Color.blue()
                )
                
                # Add command details
                embed.add_field(name="Response", value=cmd["response"], inline=False)
                
                # Example with variables replaced
                example = self._replace_variables(cmd["response"], ctx)
                embed.add_field(name="Example Output", value=example, inline=False)
                
                # Add metadata
                embed.add_field(name="Created By", value=f"<@{cmd.get('created_by', 'Unknown')}>", inline=True)
                embed.add_field(name="Uses", value=str(cmd.get("uses", 0)), inline=True)
                
                # Add creation timestamp
                created_at = cmd.get("created_at")
                if created_at:
                    if isinstance(created_at, str):
                        embed.add_field(name="Created At", value=created_at, inline=True)
                    else:
                        embed.add_field(name="Created At", value=created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=True)
                
                # Add update info if available
                if cmd.get("updated_at"):
                    updated_at = cmd.get("updated_at")
                    if isinstance(updated_at, str):
                        embed.add_field(name="Last Updated", value=updated_at, inline=True)
                    else:
                        embed.add_field(name="Last Updated", value=updated_at.strftime("%Y-%m-%d %H:%M:%S"), inline=True)
                    
                    embed.add_field(name="Updated By", value=f"<@{cmd.get('updated_by', 'Unknown')}>", inline=True)
                
                # Add usage info
                embed.add_field(name="Usage", value=f"`/custom {name}`", inline=False)
                
                await ctx.followup.send(embed=embed)
                
                # Track command usage
                await self._track_command_usage(ctx, "cmd_info")
                
            except Exception as e:
                logger.error(f"Error getting custom command info: {e}")
                await ctx.followup.send(f"An error occurred while fetching command info: {str(e)}")
        else:
            await ctx.followup.send("Custom commands are not available without database connection.")
    
    @slash_command(name="custom", description="Execute a custom command")
    @app_commands.describe(
        command="The custom command to execute"
    )
    async def custom(self, ctx: Interaction, command: str):
        """Execute a custom command"""
        await ctx.response.defer()
        
        # Check if in guild
        if not ctx.guild:
            await ctx.followup.send("Custom commands can only be used in a server.")
            return
        
        # Sanitize command name
        command = command.lower().strip()
        
        if self.db:
            try:
                # Find the command
                cmd = await self.db.custom_commands.find_one({
                    "guild_id": str(ctx.guild.id),
                    "name": command
                })
                
                if not cmd:
                    await ctx.followup.send(f"No custom command found with the name `{command}`.")
                    return
                
                # Replace variables in the response
                response = self._replace_variables(cmd["response"], ctx)
                
                # Send the response
                await ctx.followup.send(response)
                
                # Update usage count
                await self.db.custom_commands.update_one(
                    {
                        "guild_id": str(ctx.guild.id),
                        "name": command
                    },
                    {
                        "$inc": {
                            "uses": 1
                        }
                    }
                )
                
                # Track command usage
                await self._track_command_usage(ctx, "custom_command_executed")
                
            except Exception as e:
                logger.error(f"Error executing custom command: {e}")
                await ctx.followup.send(f"An error occurred while executing the command: {str(e)}")
        else:
            await ctx.followup.send("Custom commands are not available without database connection.")
    
    def _replace_variables(self, text: str, ctx: Interaction) -> str:
        """Replace variables in the text with their actual values"""
        result = text
        
        for pattern, replacer in VARIABLE_PATTERNS.items():
            if pattern in result:
                try:
                    value = replacer(ctx)
                    result = result.replace(pattern, value)
                except Exception as e:
                    logger.error(f"Error replacing variable {pattern}: {e}")
        
        return result
    
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
    """Set up the custom commands cog"""
    await bot.add_cog(CustomCommandsCog(bot))
    logger.info("Custom Commands Fixed cog loaded")