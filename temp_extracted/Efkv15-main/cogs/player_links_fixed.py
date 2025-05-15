"""
Player Links Cog (Fixed Version)

This module provides functionality for linking game players to Discord users.
It helps server admins manage and track player identities across game platforms.
"""
import os
import re
import json
import logging
import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Union, Tuple, cast

import discord
from discord_compat_layer import (
    Embed, Color, Bot, app_commands, Interaction, commands, 
    ui, View, Button, ButtonStyle, slash_command
)

logger = logging.getLogger(__name__)

class PlayerLinksCog(commands.Cog):
    """Cog for managing player links to Discord accounts"""

    def __init__(self, bot: Bot):
        """Initialize the cog with bot instance"""
        self.bot = bot
        logger.info("Player Links Fixed cog initialized")
        
    @commands.Cog.listener()
    async def on_ready(self):
        """Called when the cog is ready"""
        logger.info("Player Links Fixed cog ready")
        
    @slash_command(name="link", description="Link a player name to your Discord account")
    async def link_player_command(
        self, ctx: discord.Interaction, 
        player_name: str
    ):
        """Link a player name to your Discord account"""
        # Defer the response to avoid timeout
        await ctx.response.defer(ephemeral=True)
        
        # Check if the database is available
        if not self.bot.db:
            embed = Embed(
                title="Database Error",
                description="The database is not available. Please try again later.",
                color=Color.red()
            )
            await ctx.followup.send(embed=embed, ephemeral=True)
            return
            
        # Sanitize player name
        player_name = player_name.strip()
        
        # Basic validation
        if len(player_name) < 2 or len(player_name) > 32:
            embed = Embed(
                title="Invalid Player Name",
                description="Player name must be between 2 and 32 characters.",
                color=Color.red()
            )
            await ctx.followup.send(embed=embed, ephemeral=True)
            return
            
        # Get the Discord user
        user_id = ctx.user.id
        
        # Check if user already has a linked player
        collection = self.bot.db.player_links
        existing_link = await collection.find_one({"discord_id": user_id})
        
        if existing_link:
            # User wants to update their link
            old_player_name = existing_link.get("player_name", "Unknown")
            
            # Update the existing link
            await collection.update_one(
                {"discord_id": user_id},
                {"$set": {
                    "player_name": player_name,
                    "updated_at": datetime.now(timezone.utc)
                }}
            )
            
            embed = Embed(
                title="Player Link Updated",
                description=f"Your linked player name has been updated from **{old_player_name}** to **{player_name}**.",
                color=Color.green()
            )
        else:
            # Create a new link
            await collection.insert_one({
                "discord_id": user_id,
                "player_name": player_name,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            })
            
            embed = Embed(
                title="Player Linked",
                description=f"You have successfully linked your Discord account to player **{player_name}**.",
                color=Color.green()
            )
            
        await ctx.followup.send(embed=embed, ephemeral=True)
    
    @slash_command(name="unlink", description="Unlink your Discord account from a player name")
    async def unlink_player_command(self, ctx: discord.Interaction):
        """Unlink your Discord account from a player name"""
        # Defer the response to avoid timeout
        await ctx.response.defer(ephemeral=True)
        
        # Check if the database is available
        if not self.bot.db:
            embed = Embed(
                title="Database Error", 
                description="The database is not available. Please try again later.",
                color=Color.red()
            )
            await ctx.followup.send(embed=embed, ephemeral=True)
            return
            
        # Get the Discord user
        user_id = ctx.user.id
        
        # Check if user has a linked player
        collection = self.bot.db.player_links
        existing_link = await collection.find_one({"discord_id": user_id})
        
        if not existing_link:
            embed = Embed(
                title="No Link Found",
                description="You don't have a linked player name.",
                color=Color.red()
            )
            await ctx.followup.send(embed=embed, ephemeral=True)
            return
            
        # Delete the link
        await collection.delete_one({"discord_id": user_id})
        
        player_name = existing_link.get("player_name", "Unknown")
        embed = Embed(
            title="Player Unlinked",
            description=f"You have successfully unlinked your Discord account from player **{player_name}**.",
            color=Color.green()
        )
        
        await ctx.followup.send(embed=embed, ephemeral=True)
    
    @slash_command(name="mylink", description="View your linked player name")
    async def view_link_command(self, ctx: discord.Interaction):
        """View your linked player name"""
        # Defer the response to avoid timeout
        await ctx.response.defer(ephemeral=True)
        
        # Check if the database is available
        if not self.bot.db:
            embed = Embed(
                title="Database Error",
                description="The database is not available. Please try again later.",
                color=Color.red()
            )
            await ctx.followup.send(embed=embed, ephemeral=True)
            return
            
        # Get the Discord user
        user_id = ctx.user.id
        
        # Check if user has a linked player
        collection = self.bot.db.player_links
        existing_link = await collection.find_one({"discord_id": user_id})
        
        if not existing_link:
            embed = Embed(
                title="No Link Found",
                description="You don't have a linked player name.",
                color=Color.yellow()
            )
            embed.add_field(
                name="How to Link",
                value="Use `/link [player_name]` to link your Discord account to a player name."
            )
        else:
            player_name = existing_link.get("player_name", "Unknown")
            created_at = existing_link.get("created_at", datetime.now(timezone.utc))
            updated_at = existing_link.get("updated_at", datetime.now(timezone.utc))
            
            embed = Embed(
                title="Your Player Link",
                description=f"Your Discord account is linked to player **{player_name}**.",
                color=Color.blue()
            )
            
            # Format dates
            created_str = created_at.strftime("%Y-%m-%d %H:%M:%S UTC") if created_at else "Unknown"
            updated_str = updated_at.strftime("%Y-%m-%d %H:%M:%S UTC") if updated_at else "Unknown"
            
            embed.add_field(name="Linked Since", value=created_str, inline=True)
            if created_at != updated_at:
                embed.add_field(name="Last Updated", value=updated_str, inline=True)
                
        await ctx.followup.send(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot) -> None:
    """Set up the player links cog"""
    await bot.add_cog(PlayerLinksCog(bot))