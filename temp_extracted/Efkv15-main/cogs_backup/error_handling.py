"""
Error Handling Cog

This cog provides global error handling for the Discord bot.
"""

import sys
import traceback
import math
import discord
from discord.ext import commands
import logging

logger = logging.getLogger(__name__)

class ErrorHandling(commands.Cog):
    """Handles errors across the bot"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Global error handler for all commands"""
        # Get the original error
        error = getattr(error, 'original', error)
        
        # Log the error
        if hasattr(ctx.command, 'name'):
            logger.error(f"Error in command {ctx.command.name}: {str(error)}")
        else:
            logger.error(f"Error in unknown command: {str(error)}")
        
        # Skip if command has local error handler
        if hasattr(ctx.command, 'on_error'):
            return
        
        # Skip if cog has local error handler
        if ctx.cog and ctx.cog._get_overridden_method(ctx.cog.cog_command_error) is not None:
            return
            
        # Handle common errors
        if isinstance(error, commands.CommandNotFound):
            # Skip command not found
            return
            
        elif isinstance(error, commands.DisabledCommand):
            embed = discord.Embed(
                title="Command Disabled",
                description="This command is currently disabled.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
            
        elif isinstance(error, commands.NoPrivateMessage):
            embed = discord.Embed(
                title="Server Only",
                description="This command cannot be used in private messages.",
                color=discord.Color.red()
            )
            try:
                await ctx.author.send(embed=embed)
            except:
                pass
            return
            
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="Missing Argument",
                description=f"You're missing the required argument: `{error.param.name}`.",
                color=discord.Color.orange()
            )
            
            # Add usage example if available
            if ctx.command.usage:
                embed.add_field(
                    name="Usage",
                    value=f"```{ctx.prefix}{ctx.command.name} {ctx.command.usage}```",
                    inline=False
                )
            else:
                embed.add_field(
                    name="Command Syntax",
                    value=f"```{ctx.prefix}{ctx.command.name} {ctx.command.signature}```",
                    inline=False
                )
                
            await ctx.send(embed=embed)
            return
            
        elif isinstance(error, commands.BadArgument):
            embed = discord.Embed(
                title="Invalid Argument",
                description=str(error),
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
            return
            
        elif isinstance(error, commands.MissingPermissions):
            missing_perms = [p.replace('_', ' ').title() for p in error.missing_permissions]
            perms_str = ', '.join(missing_perms)
            
            embed = discord.Embed(
                title="Missing Permissions",
                description=f"You need the following permission(s) to use this command: **{perms_str}**",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
            
        elif isinstance(error, commands.BotMissingPermissions):
            missing_perms = [p.replace('_', ' ').title() for p in error.missing_permissions]
            perms_str = ', '.join(missing_perms)
            
            embed = discord.Embed(
                title="Bot Missing Permissions",
                description=f"I need the following permission(s) to execute this command: **{perms_str}**",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
            
        elif isinstance(error, commands.CommandOnCooldown):
            cooldown_time = error.retry_after
            
            # Format the time nicely
            if cooldown_time < 60:
                time_str = f"{math.ceil(cooldown_time)} seconds"
            elif cooldown_time < 3600:
                minutes = math.ceil(cooldown_time / 60)
                time_str = f"{minutes} minute{'s' if minutes > 1 else ''}"
            else:
                hours = math.ceil(cooldown_time / 3600)
                time_str = f"{hours} hour{'s' if hours > 1 else ''}"
                
            embed = discord.Embed(
                title="Command Cooldown",
                description=f"This command is on cooldown. Try again in **{time_str}**.",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
            return
            
        elif isinstance(error, commands.CheckFailure):
            embed = discord.Embed(
                title="Permission Error",
                description="You do not have permission to use this command.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # If we get here, the error wasn't handled and should be reported
        # Use error telemetry if available
        if hasattr(self.bot, 'error_telemetry') and self.bot.error_telemetry:
            error_id = await self.bot.error_telemetry.report_error(
                error_type=type(error).__name__,
                error_message=str(error),
                traceback_str=traceback.format_exc(),
                command_name=ctx.command.name if hasattr(ctx.command, 'name') else "Unknown",
                guild_id=ctx.guild.id if ctx.guild else None,
                channel_id=ctx.channel.id,
                user_id=ctx.author.id
            )
            
            # Let the user know an error occurred and has been logged
            embed = discord.Embed(
                title="An Error Occurred",
                description=f"An unexpected error occurred while running the command.\nError ID: `{error_id}`",
                color=discord.Color.red()
            )
        else:
            # No error telemetry available, just create a basic error message
            embed = discord.Embed(
                title="An Error Occurred",
                description="An unexpected error occurred while running the command.",
                color=discord.Color.red()
            )
            
            # Add error details for debugging
            if self.bot.is_owner(ctx.author):
                # Show more details to the bot owner
                embed.add_field(
                    name="Error Details",
                    value=f"```py\n{type(error).__name__}: {str(error)}\n```",
                    inline=False
                )
        
        await ctx.send(embed=embed)
        
        # Log the full traceback to console
        print(f"Ignoring exception in command {ctx.command}:", file=sys.stderr)
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

async def setup(bot):
    """Add the cog to the bot"""
    await bot.add_cog(ErrorHandling(bot))