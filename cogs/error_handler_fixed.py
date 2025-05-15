"""
Error Handler (Fixed Version)

This cog handles errors from commands and interactions in a user-friendly way.
It follows the compatibility layer implementation for py-cord.
"""

import logging
import traceback
from typing import Optional, Union, Any, cast

import discord
from discord.ext import commands
from discord import app_commands
from discord_compat_layer import (
    Embed, Color, Interaction
)

# Set up logging
logger = logging.getLogger(__name__)

class ErrorHandlerCog(commands.Cog):
    """Global error handling cog with py-cord compatibility"""
    
    def __init__(self, bot):
        """Initialize the error handler cog"""
        self.bot = bot
        logger.info("Error Handler Fixed cog initialized")
        
        # Set up global error handler
        self._set_up_global_error_handlers()
    
    def _set_up_global_error_handlers(self):
        """Set up global error handlers"""
        # Store original error handler first
        if hasattr(self.bot, 'on_command_error'):
            self.original_command_error = self.bot.on_command_error
        else:
            self.original_command_error = None
            
        # Override with our error handler
        self.bot.on_command_error = self._on_command_error
        
        # Handle app command errors if available
        if hasattr(self.bot, 'tree'):
            # Store original handler
            if hasattr(self.bot.tree, 'on_error'):
                self.original_tree_error = self.bot.tree.on_error
            else:
                self.original_tree_error = None
                
            # Override with our handler
            self.bot.tree.on_error = self._on_app_command_error
    
    async def _on_command_error(self, ctx, error):
        """Handle errors from prefix commands"""
        # Get command name
        cmd_name = ctx.command.name if ctx.command else "unknown"
        
        # Log the error
        logger.error(f"Error in command {cmd_name}: {str(error)}", exc_info=error)
        
        # Check for specific error types and handle accordingly
        if isinstance(error, commands.CommandNotFound):
            # Ignore command not found errors
            return
            
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"⚠️ This command is on cooldown. Try again in {error.retry_after:.1f} seconds.")
            return
            
        if isinstance(error, commands.CheckFailure):
            await ctx.send("⚠️ You don't have permission to use this command.")
            return
            
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"⚠️ Missing required argument: `{error.param.name}`")
            return
        
        # Default error handling
        try:
            embed = Embed(
                title="Command Error",
                description=f"An error occurred with the `{cmd_name}` command.",
                color=Color.red()
            )
            
            # Add error message
            embed.add_field(
                name="Error",
                value=str(error)[:1024],  # Truncate if too long
                inline=False
            )
            
            # Add help information
            embed.add_field(
                name="Need help?",
                value="Use the `/help` command to see how to use this command correctly.",
                inline=False
            )
            
            # Send the error message
            await ctx.send(embed=embed)
        except:
            # If all else fails, try a simple message
            try:
                await ctx.send("An error occurred with the command. Please check logs.")
            except:
                pass
                
        # If original handler exists, call it as well
        if self.original_command_error:
            await self.original_command_error(ctx, error)
    
    async def _on_app_command_error(self, interaction, error):
        """Handle errors from application (slash) commands"""
        # Get command name
        cmd_name = "unknown"
        if hasattr(interaction, 'command') and interaction.command:
            cmd_name = interaction.command.name
        elif hasattr(interaction, 'data') and hasattr(interaction.data, 'name'):
            cmd_name = interaction.data.name
        
        # Log the error
        logger.error(f"Error in app command {cmd_name}: {str(error)}", exc_info=error)
        
        # Check if the interaction has been responded to
        followup = False
        if hasattr(interaction, 'response') and hasattr(interaction.response, 'is_done'):
            followup = interaction.response.is_done()
        else:
            followup = True  # Default to followup if we can't check
        
        # Handle specific error types
        if isinstance(error, commands.CommandOnCooldown):
            msg = f"⚠️ This command is on cooldown. Try again in {error.retry_after:.1f} seconds."
            if followup:
                await interaction.followup.send(msg, ephemeral=True)
            else:
                await interaction.response.send_message(msg, ephemeral=True)
            return
            
        elif isinstance(error, commands.MissingPermissions):
            missing = [perm.replace('_', ' ').replace('guild', 'server').title() for perm in error.missing_permissions]
            msg = f"⚠️ You need the following permissions to run this command: `{', '.join(missing)}`"
            if followup:
                await interaction.followup.send(msg, ephemeral=True)
            else:
                await interaction.response.send_message(msg, ephemeral=True)
            return
            
        # Default error handling
        try:
            embed = Embed(
                title="Command Error",
                description=f"An error occurred with the `{cmd_name}` command.",
                color=Color.red()
            )
            
            # Add error message
            embed.add_field(
                name="Error",
                value=str(error)[:1024],  # Truncate if too long
                inline=False
            )
            
            # Add help information
            embed.add_field(
                name="Need help?",
                value="Use the `/help` command to see how to use this command correctly.",
                inline=False
            )
            
            # Send the error message
            if followup:
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            # If all else fails, try a simple message
            logger.error(f"Failed to send error embed: {str(e)}")
            try:
                if followup:
                    await interaction.followup.send("An error occurred with the command. Please check logs.", ephemeral=True)
                else:
                    await interaction.response.send_message("An error occurred with the command. Please check logs.", ephemeral=True)
            except:
                pass
    
    async def cog_unload(self):
        """Called when the cog is unloaded"""
        # Restore original error handlers if available
        if self.original_command_error:
            self.bot.on_command_error = self.original_command_error
            
        if hasattr(self.bot, 'tree') and self.original_tree_error:
            self.bot.tree.on_error = self.original_tree_error
            
        logger.info("Error Handler Fixed cog unloaded, original handlers restored")

async def setup(bot):
    """Setup function for the error handler cog"""
    await bot.add_cog(ErrorHandlerCog(bot))
    logger.info("Error Handler Fixed cog loaded")