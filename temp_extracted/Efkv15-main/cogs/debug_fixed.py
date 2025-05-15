"""
Debug commands for development and troubleshooting (Fixed)

This module contains utility commands for bot developers to diagnose issues
and perform administrative tasks. It's been modified to work with py-cord 2.6.1.
"""

import os
import sys
import time
import logging
import asyncio
import platform
import traceback
from typing import Optional, Dict, List, Union, Any

import discord
from discord.ext import commands
from utils.discord_patches import app_commands

# Configure logging
logger = logging.getLogger(__name__)

class DebugFixed(commands.Cog, name="Debug"):
    """Debug commands for bot development and administration"""
    
    def __init__(self, bot):
        """Initialize the debug cog"""
        self.bot = bot
        logger.info("Debug Fixed cog initialized")
    
    # Owner-only check for debug commands
    async def cog_check(self, ctx):
        """Check if user is a bot owner"""
        if not await self.bot.is_owner(ctx.author):
            await ctx.send("⚠️ These commands are only available to bot owners.")
            return False
        return True
    
    debug_group = app_commands.Group(name="debug", description="Debug and development commands")
    
    @debug_group.command(name="system_info")
    async def system_info(self, ctx):
        """Display system information"""
        embed = discord.Embed(
            title="System Information",
            color=discord.Color.blue()
        )
        
        # Python info
        embed.add_field(
            name="Python",
            value=f"```\nVersion: {platform.python_version()}\nImpl: {platform.python_implementation()}\n```",
            inline=False
        )
        
        # OS info
        embed.add_field(
            name="Operating System",
            value=f"```\n{platform.system()} {platform.release()}\n{platform.version()}\n```",
            inline=False
        )
        
        # Discord.py info
        embed.add_field(
            name="Discord Library",
            value=f"```\nVersion: {discord.__version__}\nAsync: {asyncio.__version__}\n```",
            inline=False
        )
        
        # Bot info
        embed.add_field(
            name="Bot",
            value=(
                f"```\nUptime: {self._get_uptime()}\n"
                f"Guilds: {len(self.bot.guilds)}\n"
                f"Commands: {len(self.bot.commands)}\n```"
            ),
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @debug_group.command(name="ping")
    async def ping(self, ctx):
        """Check bot latency"""
        start_time = time.time()
        message = await ctx.send("Pinging...")
        
        end_time = time.time()
        round_trip = (end_time - start_time) * 1000
        websocket_latency = self.bot.latency * 1000
        
        embed = discord.Embed(
            title="🏓 Pong!",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="API Latency",
            value=f"{round_trip:.2f} ms",
            inline=True
        )
        
        embed.add_field(
            name="WebSocket Latency",
            value=f"{websocket_latency:.2f} ms",
            inline=True
        )
        
        await message.edit(content=None, embed=embed)
    
    @debug_group.command(name="guild_info")
    async def guild_info(self, ctx, guild_id: Optional[str] = None):
        """Display information about a guild"""
        # Use the current guild if no ID is provided
        if guild_id:
            try:
                guild = self.bot.get_guild(int(guild_id))
                if not guild:
                    await ctx.send(f"❌ Guild with ID {guild_id} not found.")
                    return
            except ValueError:
                await ctx.send("❌ Invalid guild ID. Please provide a valid numeric ID.")
                return
        else:
            guild = ctx.guild
            if not guild:
                await ctx.send("❌ Not in a guild. Please provide a guild ID.")
                return
        
        # Create embed
        embed = discord.Embed(
            title=f"Guild Information: {guild.name}",
            color=discord.Color.blue()
        )
        
        # Set guild icon if available
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        # Basic info
        embed.add_field(
            name="Basic Info",
            value=(
                f"**ID:** {guild.id}\n"
                f"**Owner:** {guild.owner.mention if guild.owner else 'Unknown'}\n"
                f"**Created:** <t:{int(guild.created_at.timestamp())}:R>\n"
                f"**Region:** {guild.region if hasattr(guild, 'region') else 'Unknown'}\n"
                f"**Verification Level:** {guild.verification_level}"
            ),
            inline=False
        )
        
        # Member stats
        embed.add_field(
            name="Members",
            value=(
                f"**Total:** {guild.member_count}\n"
                f"**Humans:** {sum(1 for m in guild.members if not m.bot)}\n"
                f"**Bots:** {sum(1 for m in guild.members if m.bot)}"
            ),
            inline=True
        )
        
        # Channel stats
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)
        
        embed.add_field(
            name="Channels",
            value=(
                f"**Text:** {text_channels}\n"
                f"**Voice:** {voice_channels}\n"
                f"**Categories:** {categories}"
            ),
            inline=True
        )
        
        # Role stats
        embed.add_field(
            name="Roles",
            value=f"**Count:** {len(guild.roles)}"
        )
        
        await ctx.send(embed=embed)
    
    @debug_group.command(name="reload")
    async def reload(self, ctx, cog_name: str):
        """Reload a specific cog"""
        try:
            # Make sure the cog name includes the cogs directory
            if not cog_name.startswith("cogs."):
                cog_name = f"cogs.{cog_name}"
                
            # Attempt to reload the cog
            await self.bot.reload_extension(cog_name)
            
            await ctx.send(f"✅ Cog `{cog_name}` reloaded successfully.")
            logger.info(f"Cog {cog_name} reloaded by {ctx.author}")
        except Exception as e:
            logger.error(f"Error reloading cog {cog_name}: {e}")
            await ctx.send(f"❌ Error reloading cog `{cog_name}`:\n```py\n{str(e)}\n```")
            
    @debug_group.command(name="load")
    async def load_extension(self, ctx, cog_name: str):
        """Load a specific cog"""
        try:
            # Make sure the cog name includes the cogs directory
            if not cog_name.startswith("cogs."):
                cog_name = f"cogs.{cog_name}"
                
            # Attempt to load the cog
            await self.bot.load_extension(cog_name)
            
            await ctx.send(f"✅ Cog `{cog_name}` loaded successfully.")
            logger.info(f"Cog {cog_name} loaded by {ctx.author}")
        except Exception as e:
            logger.error(f"Error loading cog {cog_name}: {e}")
            await ctx.send(f"❌ Error loading cog `{cog_name}`:\n```py\n{str(e)}\n```")
    
    @debug_group.command(name="unload")
    async def unload_extension(self, ctx, cog_name: str):
        """Unload a specific cog"""
        try:
            # Make sure the cog name includes the cogs directory
            if not cog_name.startswith("cogs."):
                cog_name = f"cogs.{cog_name}"
                
            # Don't allow unloading the debug cog
            if cog_name.lower() in ["cogs.debug_fixed", "cogs.debug"]:
                await ctx.send("⚠️ Cannot unload the debug cog.")
                return
                
            # Attempt to unload the cog
            await self.bot.unload_extension(cog_name)
            
            await ctx.send(f"✅ Cog `{cog_name}` unloaded successfully.")
            logger.info(f"Cog {cog_name} unloaded by {ctx.author}")
        except Exception as e:
            logger.error(f"Error unloading cog {cog_name}: {e}")
            await ctx.send(f"❌ Error unloading cog `{cog_name}`:\n```py\n{str(e)}\n```")
    
    @debug_group.command(name="list_cogs")
    async def list_cogs(self, ctx):
        """List all loaded cogs"""
        # Get loaded cogs
        loaded_cogs = list(self.bot.cogs.keys())
        loaded_cogs.sort()
        
        # Get all available cogs
        available_cogs = []
        for filename in os.listdir("cogs"):
            if filename.endswith(".py") and not filename.startswith("_"):
                available_cogs.append(filename[:-3])  # Remove .py extension
        available_cogs.sort()
        
        # Create embed
        embed = discord.Embed(
            title="Cog Status",
            description=f"**Loaded:** {len(loaded_cogs)} | **Available:** {len(available_cogs)}",
            color=discord.Color.blue()
        )
        
        # Add loaded cogs
        loaded_value = "\n".join(f"✅ {cog}" for cog in loaded_cogs) or "None"
        embed.add_field(
            name="Loaded Cogs",
            value=f"```\n{loaded_value}\n```",
            inline=False
        )
        
        # Add unloaded cogs (available but not loaded)
        unloaded_cogs = [cog for cog in available_cogs if cog not in [c.lower() for c in loaded_cogs]]
        unloaded_value = "\n".join(f"❌ {cog}" for cog in unloaded_cogs) or "None"
        embed.add_field(
            name="Unloaded Cogs",
            value=f"```\n{unloaded_value}\n```",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @debug_group.command(name="eval")
    async def eval_code(self, ctx, *, code: str):
        """Evaluate Python code (use with caution)"""
        # Only allow bot owner to use this command
        if not await self.bot.is_owner(ctx.author):
            await ctx.send("⚠️ This command is only available to bot owners.")
            return
            
        # Remove code block formatting if present
        if code.startswith("```") and code.endswith("```"):
            code = "\n".join(code.split("\n")[1:-1])
        
        # Add return for expression evaluation
        if not code.strip().startswith("return") and not any(x in code for x in [";\n", ";\r", ";"]):
            code = f"return {code}"
            
        # Create the function to execute the code
        env = {
            'ctx': ctx,
            'bot': self.bot,
            'discord': discord,
            'commands': commands,
            'guild': ctx.guild,
            'channel': ctx.channel,
            'author': ctx.author,
            'message': ctx.message
        }
        
        # Add global and local variables
        env.update(globals())
        
        # Create the async function
        exec_function = f"async def _eval():\n"
        for line in code.split("\n"):
            exec_function += f"    {line}\n"
            
        try:
            # Execute the code
            exec(exec_function, env)
            result = await env["_eval"]()
            
            # Format the result
            if result is None:
                await ctx.send("✅ Code executed successfully with no result.")
            else:
                # Convert result to string
                result_str = str(result)
                
                # Truncate if too long
                if len(result_str) > 1990:
                    result_str = result_str[:1990] + "..."
                    
                await ctx.send(f"✅ Result:\n```py\n{result_str}\n```")
                
        except Exception as e:
            # Get the full traceback
            trace = traceback.format_exception(type(e), e, e.__traceback__)
            trace_str = "".join(trace)
            
            # Truncate if too long
            if len(trace_str) > 1990:
                trace_str = trace_str[:1990] + "..."
                
            await ctx.send(f"❌ Error:\n```py\n{trace_str}\n```")
    
    def _get_uptime(self):
        """Get the bot's uptime as a string"""
        # Get uptime in seconds
        uptime_seconds = time.time() - self.bot.start_time
        
        # Convert to days, hours, minutes, seconds
        days, remainder = divmod(uptime_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        # Format string
        parts = []
        if days > 0:
            parts.append(f"{int(days)}d")
        if hours > 0:
            parts.append(f"{int(hours)}h")
        if minutes > 0:
            parts.append(f"{int(minutes)}m")
        if seconds > 0 or not parts:
            parts.append(f"{int(seconds)}s")
            
        return " ".join(parts)

async def setup(bot):
    """Setup function for the debug_fixed cog"""
    # Set start time if not already set
    if not hasattr(bot, 'start_time'):
        bot.start_time = time.time()
        
    await bot.add_cog(DebugFixed(bot))
    logger.info("Debug Fixed cog loaded")