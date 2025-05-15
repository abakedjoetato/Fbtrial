"""
Setup commands for configuring servers and channels (Enhanced)

This version is compatible with py-cord 2.6.1 and resolves the Interaction.respond issue.
"""

import logging
import asyncio
from typing import Optional, Dict, List, Union, Any

import discord
from discord.ext import commands
from utils.discord_patches import app_commands

# Configure logging
logger = logging.getLogger(__name__)

class SetupEnhanced(commands.Cog, name="Setup"):
    """Setup commands for configuring servers and channels"""
    
    def __init__(self, bot):
        """Initialize the setup cog"""
        self.bot = bot
        logger.info("Setup Enhanced cog initialized")

    setup_group = app_commands.Group(name="setup", description="Server setup commands")
    
    @setup_group.command(name="add_server")
    @commands.has_permissions(administrator=True)
    async def add_server(
        self, 
        ctx,
        server_name: str,
        host: str,
        port: int,
        username: str,
        password: str,
        log_path: str,
        enabled: bool = True,
        sync_frequency: int = 5
    ):
        """Add a game server to track via SFTP"""
        # Ensure this is used in a guild
        if not ctx.guild:
            await ctx.send("This command can only be used in a server.")
            return
            
        try:
            # Check if premium features are available
            if hasattr(self.bot, 'premium_manager') and self.bot.premium_manager:
                has_premium = await self.bot.premium_manager.has_feature(ctx.guild.id, "sftp")
                if not has_premium:
                    embed = discord.Embed(
                        title="Premium Feature",
                        description="SFTP tracking requires a premium subscription.",
                        color=discord.Color.gold()
                    )
                    await ctx.send(embed=embed)
                    return
                    
            # Store server details in database
            if self.bot.db:
                # Create a unique ID for the server
                server_id = f"{server_name}_{host}_{port}".lower().replace(" ", "_")
                
                # Create server data document
                server_data = {
                    "server_id": server_id,
                    "guild_id": ctx.guild.id,
                    "server_name": server_name,
                    "host": host,
                    "port": port,
                    "username": username,
                    "password": password,  # In production, this should be encrypted
                    "log_path": log_path,
                    "enabled": enabled,
                    "sync_frequency": sync_frequency,
                    "added_by": ctx.author.id,
                    "added_at": discord.utils.utcnow().isoformat()
                }
                
                # Save to database
                result = await self.bot.db.servers.update_one(
                    {"server_id": server_id, "guild_id": ctx.guild.id},
                    {"$set": server_data},
                    upsert=True
                )
                
                if result.modified_count > 0 or result.upserted_id:
                    await ctx.send(f"✅ Server `{server_name}` has been added for tracking.")
                else:
                    await ctx.send("❌ Failed to add server. Please try again.")
            else:
                await ctx.send("❌ Database not available. Server settings cannot be saved.")
                
        except Exception as e:
            logger.error(f"Error adding server: {e}")
            await ctx.send(f"❌ An error occurred: {str(e)}")

    @setup_group.command(name="remove_server")
    @commands.has_permissions(administrator=True)
    async def remove_server(
        self, 
        ctx,
        server_id: str
    ):
        """Remove a game server from tracking"""
        # Ensure this is used in a guild
        if not ctx.guild:
            await ctx.send("This command can only be used in a server.")
            return
            
        try:
            if self.bot.db:
                # Delete the server from the database
                result = await self.bot.db.servers.delete_one({
                    "server_id": server_id,
                    "guild_id": ctx.guild.id
                })
                
                if result.deleted_count > 0:
                    await ctx.send(f"✅ Server `{server_id}` has been removed from tracking.")
                else:
                    await ctx.send(f"❌ Server `{server_id}` not found or you don't have permission to remove it.")
            else:
                await ctx.send("❌ Database not available. Server settings cannot be modified.")
                
        except Exception as e:
            logger.error(f"Error removing server: {e}")
            await ctx.send(f"❌ An error occurred: {str(e)}")

    @setup_group.command(name="list_servers")
    @commands.has_permissions(administrator=True)
    async def list_servers(self, ctx):
        """List all configured game servers"""
        # Ensure this is used in a guild
        if not ctx.guild:
            await ctx.send("This command can only be used in a server.")
            return
            
        try:
            if self.bot.db:
                # Find all servers for this guild
                servers = await self.bot.db.servers.find({"guild_id": ctx.guild.id}).to_list(None)
                
                if not servers:
                    await ctx.send("No servers have been configured for this guild.")
                    return
                    
                # Create an embed with server information
                embed = discord.Embed(
                    title="Configured Servers",
                    description=f"This guild has {len(servers)} configured server(s).",
                    color=discord.Color.blue()
                )
                
                for server in servers:
                    embed.add_field(
                        name=server.get("server_name", "Unknown"),
                        value=(
                            f"ID: `{server.get('server_id', 'Unknown')}`\n"
                            f"Host: `{server.get('host', 'Unknown')}`\n"
                            f"Enabled: `{server.get('enabled', False)}`\n"
                            f"Sync Frequency: `{server.get('sync_frequency', 5)} minutes`"
                        ),
                        inline=False
                    )
                
                await ctx.send(embed=embed)
            else:
                await ctx.send("❌ Database not available. Server settings cannot be retrieved.")
                
        except Exception as e:
            logger.error(f"Error listing servers: {e}")
            await ctx.send(f"❌ An error occurred: {str(e)}")

async def setup(bot):
    """Setup function for the setup_fixed_enhanced cog"""
    await bot.add_cog(SetupEnhanced(bot))
    logger.info("Setup Enhanced cog loaded")