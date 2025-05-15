"""
Error Handler

This cog handles errors from commands and interactions in a user-friendly way.
"""

import logging
import traceback
from typing import Optional, Union, Any

import discord
from discord.ext import commands
from utils.discord_patches import app_commands

# Set up logging
logger = logging.getLogger(__name__)

class ErrorHandler(commands.Cog):
    """Global error handling cog"""
    
    def __init__(self, bot):
        """Initialize the error handler cog"""
        self.bot = bot
        logger.info("Error Handler cog initialized")
        
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
        
        logger.debug("Global error handlers set up")
    
    async def _on_command_error(self, ctx, error):
        """Handle command errors"""
        # Log the error
        if hasattr(ctx.command, 'qualified_name'):
            cmd_name = ctx.command.qualified_name
        else:
            cmd_name = str(ctx.command)
            
        logger.error(f"Error in command '{cmd_name}': {error}")
        
        # Get original error if it's wrapped
        error = getattr(error, "original", error)
        
        # Handle specific error types
        if isinstance(error, commands.CommandNotFound):
            return  # Ignore command not found errors
        
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"⚠️ Missing required argument: `{error.param.name}`")
            if ctx.command.help:
                await ctx.send(f"Usage: `{ctx.prefix}{ctx.command.qualified_name} {ctx.command.signature}`")
            return
            
        elif isinstance(error, commands.BadArgument):
            await ctx.send(f"⚠️ Bad argument: {str(error)}")
            return
            
        elif isinstance(error, commands.MissingPermissions):
            missing = [perm.replace('_', ' ').replace('guild', 'server').title() for perm in error.missing_permissions]
            await ctx.send(f"⚠️ You need the following permissions to run this command: `{', '.join(missing)}`")
            return
            
        elif isinstance(error, commands.BotMissingPermissions):
            missing = [perm.replace('_', ' ').replace('guild', 'server').title() for perm in error.missing_permissions]
            await ctx.send(f"⚠️ I need the following permissions to run this command: `{', '.join(missing)}`")
            return
            
        elif isinstance(error, commands.NotOwner):
            await ctx.send("⚠️ This command is only available to the bot owner.")
            return
            
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"⚠️ This command is on cooldown. Try again in {error.retry_after:.1f} seconds.")
            return
        
        # Default error handling
        try:
            embed = discord.Embed(
                title="Command Error",
                description=f"An error occurred with the `{cmd_name}` command.",
                color=discord.Color.red()
            )
            
            # Add error message
            embed.add_field(
                name="Error",
                value=f"```{str(error)[:1000]}```",
                inline=False
            )
            
            # Add command usage if available
            if ctx.command and ctx.command.signature:
                embed.add_field(
                    name="Usage",
                    value=f"`{ctx.prefix}{ctx.command.qualified_name} {ctx.command.signature}`",
                    inline=False
                )
                
            await ctx.send(embed=embed)
            
            # Log the full error for debugging
            logger.error(f"Command '{cmd_name}' error details:", exc_info=error)
            
        except Exception as e:
            # If sending the error message fails, log it
            logger.error(f"Failed to send error message: {e}")
            try:
                await ctx.send(f"An error occurred with the command. Please check logs.")
            except:
                pass
    
    async def _on_app_command_error(self, interaction, error):
        """Handle application command errors"""
        # Log the error
        cmd_name = interaction.command.name if interaction.command else "Unknown"
        logger.error(f"Error in app command '{cmd_name}': {error}")
        
        # Get original error if it's wrapped
        error = getattr(error, "original", error)
        
        # Check if the interaction has already been responded to
        try:
            if interaction.response.is_done():
                followup = True
            else:
                followup = False
        except:
            followup = True  # Default to followup if we can't check
        
        # Handle specific error types
        if isinstance(error, app_commands.CommandOnCooldown):
            msg = f"⚠️ This command is on cooldown. Try again in {error.retry_after:.1f} seconds."
            if followup:
                await interaction.followup.send(msg, ephemeral=True)
            else:
                await interaction.response.send_message(msg, ephemeral=True)
            return
            
        elif isinstance(error, app_commands.MissingPermissions):
            missing = [perm.replace('_', ' ').replace('guild', 'server').title() for perm in error.missing_permissions]
            msg = f"⚠️ You need the following permissions to run this command: `{', '.join(missing)}`"
            if followup:
                await interaction.followup.send(msg, ephemeral=True)
            else:
                await interaction.response.send_message(msg, ephemeral=True)
            return
            
        # Default error handling
        try:
            embed = discord.Embed(
                title="Command Error",
                description=f"An error occurred with the `{cmd_name}` command.",
                color=discord.Color.red()
            )
            
            # Add error message
            embed.add_field(
                name="Error",
                value=f"```{str(error)[:1000]}```",
                inline=False
            )
            
            # Send the error message
            if followup:
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)
            
            # Log the full error for debugging
            logger.error(f"App Command '{cmd_name}' error details:", exc_info=error)
            
        except Exception as e:
            # If sending the error message fails, log it
            logger.error(f"Failed to send error message: {e}")
            try:
                if followup:
                    await interaction.followup.send("An error occurred with the command. Please check logs.", ephemeral=True)
                else:
                    await interaction.response.send_message("An error occurred with the command. Please check logs.", ephemeral=True)
            except:
                pass
    
    def cog_unload(self):
        """Called when the cog is unloaded"""
        # Restore original error handlers if available
        if self.original_command_error:
            self.bot.on_command_error = self.original_command_error
            
        if hasattr(self.bot, 'tree') and self.original_tree_error:
            self.bot.tree.on_error = self.original_tree_error
            
        logger.info("Error Handler cog unloaded, original handlers restored")

async def setup(bot):
    """Setup function for the error handler cog"""
    await bot.add_cog(ErrorHandler(bot))
    logger.info("Error Handler cog loaded")