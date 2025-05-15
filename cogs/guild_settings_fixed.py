"""
Guild Settings Cog (Fixed Version)

This module implements guild settings management with compatibility for py-cord
using our compatibility layer.
"""

import logging
import datetime
from typing import Dict, List, Optional, Union, Literal, Any

from discord_compat_layer import (
    Embed, Color, commands, Interaction, app_commands, 
    slash_command, Member, TextChannel, Role
)

logger = logging.getLogger(__name__)

class GuildSettingsCog(commands.Cog):
    """
    Guild settings management cog with compatibility for py-cord.
    
    Provides commands for configuring guild-specific settings for the bot,
    including log channels, auto-role assignments, and server IDs.
    """
    
    def __init__(self, bot):
        self.bot = bot
        logger.info("Guild Settings Fixed cog initialized")
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Called when the cog is ready"""
        logger.info("Guild Settings Fixed cog ready")
    
    @slash_command(name="setup", description="Set up the bot for this server")
    @commands.has_permissions(administrator=True)
    async def setup_command(self, ctx: Interaction):
        """Set up the bot for this server"""
        # Defer the response to avoid timeout
        await ctx.response.defer()
        
        # Create a setup embed with instructions
        embed = Embed(
            title="Bot Setup",
            description="Let's configure the bot for your server!",
            color=Color.blue()
        )
        
        embed.add_field(
            name="Setting Log Channel",
            value="Use `/set_log_channel #channel` to set where logs will be sent.",
            inline=False
        )
        
        embed.add_field(
            name="Setting Welcome Channel",
            value="Use `/set_welcome_channel #channel` to set where welcome messages will be sent.",
            inline=False
        )
        
        embed.add_field(
            name="Setting Auto Roles",
            value="Use `/set_auto_role @role` to set a role that will be auto-assigned to new members.",
            inline=False
        )
        
        embed.add_field(
            name="Linking Game Servers",
            value="Use `/add_server server_id` to link a game server to this Discord.",
            inline=False
        )
        
        embed.set_footer(text="You must have Administrator permissions to use these commands.")
        
        await ctx.followup.send(embed=embed)
    
    @slash_command(name="set_log_channel", description="Set the channel for bot logs")
    @commands.has_permissions(administrator=True)
    async def set_log_channel(self, ctx: Interaction, channel: TextChannel):
        """Set the channel for bot logs"""
        # Defer the response to avoid timeout
        await ctx.response.defer()
        
        if not ctx.guild:
            await ctx.followup.send("This command can only be used in a server.")
            return
        
        guild_id = str(ctx.guild.id)
        channel_id = str(channel.id)
        
        # Update guild settings in the database
        try:
            update_result = await self.bot.update_one(
                "guilds",
                {"guild_id": guild_id},
                {
                    "$set": {
                        "log_channel_id": channel_id,
                        "updated_at": datetime.datetime.utcnow().isoformat()
                    },
                    "$setOnInsert": {
                        "created_at": datetime.datetime.utcnow().isoformat(),
                        "guild_name": ctx.guild.name
                    }
                },
                upsert=True
            )
            
            if update_result.success:
                embed = Embed(
                    title="Log Channel Set",
                    description=f"Bot logs will now be sent to {channel.mention}.",
                    color=Color.green()
                )
                await ctx.followup.send(embed=embed)
            else:
                logger.error(f"Error setting log channel: {update_result.error}")
                await ctx.followup.send("Failed to set log channel. Please try again later.")
                
        except Exception as e:
            logger.error(f"Error setting log channel: {e}")
            await ctx.followup.send("An error occurred while setting the log channel.")
    
    @slash_command(name="set_welcome_channel", description="Set the channel for welcome messages")
    @commands.has_permissions(administrator=True)
    async def set_welcome_channel(self, ctx: Interaction, channel: TextChannel):
        """Set the channel for welcome messages"""
        # Defer the response to avoid timeout
        await ctx.response.defer()
        
        if not ctx.guild:
            await ctx.followup.send("This command can only be used in a server.")
            return
        
        guild_id = str(ctx.guild.id)
        channel_id = str(channel.id)
        
        # Update guild settings in the database
        try:
            update_result = await self.bot.update_one(
                "guilds",
                {"guild_id": guild_id},
                {
                    "$set": {
                        "welcome_channel_id": channel_id,
                        "updated_at": datetime.datetime.utcnow().isoformat()
                    },
                    "$setOnInsert": {
                        "created_at": datetime.datetime.utcnow().isoformat(),
                        "guild_name": ctx.guild.name
                    }
                },
                upsert=True
            )
            
            if update_result.success:
                embed = Embed(
                    title="Welcome Channel Set",
                    description=f"Welcome messages will now be sent to {channel.mention}.",
                    color=Color.green()
                )
                await ctx.followup.send(embed=embed)
            else:
                logger.error(f"Error setting welcome channel: {update_result.error}")
                await ctx.followup.send("Failed to set welcome channel. Please try again later.")
                
        except Exception as e:
            logger.error(f"Error setting welcome channel: {e}")
            await ctx.followup.send("An error occurred while setting the welcome channel.")
    
    @slash_command(name="set_auto_role", description="Set a role to auto-assign to new members")
    @commands.has_permissions(administrator=True)
    async def set_auto_role(self, ctx: Interaction, role: Role):
        """Set a role to auto-assign to new members"""
        # Defer the response to avoid timeout
        await ctx.response.defer()
        
        if not ctx.guild:
            await ctx.followup.send("This command can only be used in a server.")
            return
        
        guild_id = str(ctx.guild.id)
        role_id = str(role.id)
        
        # Update guild settings in the database
        try:
            update_result = await self.bot.update_one(
                "guilds",
                {"guild_id": guild_id},
                {
                    "$set": {
                        "auto_role_id": role_id,
                        "updated_at": datetime.datetime.utcnow().isoformat()
                    },
                    "$setOnInsert": {
                        "created_at": datetime.datetime.utcnow().isoformat(),
                        "guild_name": ctx.guild.name
                    }
                },
                upsert=True
            )
            
            if update_result.success:
                embed = Embed(
                    title="Auto Role Set",
                    description=f"New members will now be automatically assigned the {role.mention} role.",
                    color=Color.green()
                )
                await ctx.followup.send(embed=embed)
            else:
                logger.error(f"Error setting auto role: {update_result.error}")
                await ctx.followup.send("Failed to set auto role. Please try again later.")
                
        except Exception as e:
            logger.error(f"Error setting auto role: {e}")
            await ctx.followup.send("An error occurred while setting the auto role.")
    
    @slash_command(name="add_server", description="Link a game server to this Discord")
    @commands.has_permissions(administrator=True)
    async def add_server(self, ctx: Interaction, server_id: str, server_name: Optional[str] = None):
        """Link a game server to this Discord"""
        # Defer the response to avoid timeout
        await ctx.response.defer()
        
        if not ctx.guild:
            await ctx.followup.send("This command can only be used in a server.")
            return
        
        guild_id = str(ctx.guild.id)
        
        # Sanitize and validate server ID
        server_id = server_id.strip()
        if not server_id:
            await ctx.followup.send("Server ID cannot be empty.")
            return
        
        # Use provided server name or default to the ID
        display_name = server_name or f"Server {server_id}"
        
        # Update guild settings in the database
        try:
            # First check if the server is already linked
            guild_result = await self.bot.find_one("guilds", {"guild_id": guild_id})
            
            if guild_result.success and guild_result.data:
                guild_data = guild_result.data
                servers = guild_data.get("servers", [])
                
                if server_id in servers:
                    await ctx.followup.send(f"Server ID `{server_id}` is already linked to this Discord.")
                    return
            
            # Add the server to the guild document
            update_result = await self.bot.update_one(
                "guilds",
                {"guild_id": guild_id},
                {
                    "$addToSet": {"servers": server_id},
                    "$set": {
                        f"server_info.{server_id}": {
                            "name": display_name,
                            "added_at": datetime.datetime.utcnow().isoformat()
                        },
                        "updated_at": datetime.datetime.utcnow().isoformat()
                    },
                    "$setOnInsert": {
                        "created_at": datetime.datetime.utcnow().isoformat(),
                        "guild_name": ctx.guild.name
                    }
                },
                upsert=True
            )
            
            if update_result.success:
                embed = Embed(
                    title="Server Linked",
                    description=f"Game server `{server_id}` has been linked to this Discord.",
                    color=Color.green()
                )
                
                if server_name:
                    embed.add_field(name="Server Name", value=server_name, inline=False)
                
                await ctx.followup.send(embed=embed)
            else:
                logger.error(f"Error adding server: {update_result.error}")
                await ctx.followup.send("Failed to link server. Please try again later.")
                
        except Exception as e:
            logger.error(f"Error adding server: {e}")
            await ctx.followup.send("An error occurred while linking the server.")
    
    @slash_command(name="remove_server", description="Unlink a game server from this Discord")
    @commands.has_permissions(administrator=True)
    async def remove_server(self, ctx: Interaction, server_id: str):
        """Unlink a game server from this Discord"""
        # Defer the response to avoid timeout
        await ctx.response.defer()
        
        if not ctx.guild:
            await ctx.followup.send("This command can only be used in a server.")
            return
        
        guild_id = str(ctx.guild.id)
        
        # Sanitize server ID
        server_id = server_id.strip()
        if not server_id:
            await ctx.followup.send("Server ID cannot be empty.")
            return
        
        # Update guild settings in the database
        try:
            # First check if the server is linked
            guild_result = await self.bot.find_one("guilds", {"guild_id": guild_id})
            
            if not guild_result.success or not guild_result.data:
                await ctx.followup.send("No game servers are linked to this Discord.")
                return
            
            guild_data = guild_result.data
            servers = guild_data.get("servers", [])
            
            if server_id not in servers:
                await ctx.followup.send(f"Server ID `{server_id}` is not linked to this Discord.")
                return
            
            # Remove the server from the guild document
            update_result = await self.bot.update_one(
                "guilds",
                {"guild_id": guild_id},
                {
                    "$pull": {"servers": server_id},
                    "$unset": {f"server_info.{server_id}": ""},
                    "$set": {"updated_at": datetime.datetime.utcnow().isoformat()}
                }
            )
            
            if update_result.success:
                embed = Embed(
                    title="Server Unlinked",
                    description=f"Game server `{server_id}` has been unlinked from this Discord.",
                    color=Color.green()
                )
                
                await ctx.followup.send(embed=embed)
            else:
                logger.error(f"Error removing server: {update_result.error}")
                await ctx.followup.send("Failed to unlink server. Please try again later.")
                
        except Exception as e:
            logger.error(f"Error removing server: {e}")
            await ctx.followup.send("An error occurred while unlinking the server.")
    
    @slash_command(name="list_servers", description="List all game servers linked to this Discord")
    @commands.has_permissions(administrator=True)
    async def list_servers(self, ctx: Interaction):
        """List all game servers linked to this Discord"""
        # Defer the response to avoid timeout
        await ctx.response.defer()
        
        if not ctx.guild:
            await ctx.followup.send("This command can only be used in a server.")
            return
        
        guild_id = str(ctx.guild.id)
        
        # Get guild settings from the database
        try:
            guild_result = await self.bot.find_one("guilds", {"guild_id": guild_id})
            
            if not guild_result.success or not guild_result.data:
                await ctx.followup.send("No game servers are linked to this Discord.")
                return
            
            guild_data = guild_result.data
            servers = guild_data.get("servers", [])
            server_info = guild_data.get("server_info", {})
            
            if not servers:
                await ctx.followup.send("No game servers are linked to this Discord.")
                return
            
            # Create an embed with the server list
            embed = Embed(
                title="Linked Game Servers",
                description=f"There are {len(servers)} server(s) linked to this Discord.",
                color=Color.blue()
            )
            
            for server_id in servers:
                info = server_info.get(server_id, {})
                name = info.get("name", f"Server {server_id}")
                added_at = info.get("added_at", "Unknown")
                
                # Format the date if it exists
                if added_at and added_at != "Unknown":
                    try:
                        # Parse the ISO format date
                        date_obj = datetime.datetime.fromisoformat(added_at)
                        # Format it to a more readable format
                        added_at = date_obj.strftime("%Y-%m-%d %H:%M:%S UTC")
                    except:
                        # Keep it as is if parsing fails
                        pass
                
                embed.add_field(
                    name=name,
                    value=f"ID: `{server_id}`\nAdded: {added_at}",
                    inline=True
                )
            
            await ctx.followup.send(embed=embed)
                
        except Exception as e:
            logger.error(f"Error listing servers: {e}")
            await ctx.followup.send("An error occurred while retrieving the server list.")

async def setup(bot):
    """Set up the guild settings cog"""
    await bot.add_cog(GuildSettingsCog(bot))
    logger.info("Guild Settings Fixed commands cog loaded")