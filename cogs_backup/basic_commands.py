"""
Basic Commands Cog

This cog provides essential basic commands for the Discord bot.
"""

import time
import platform
import discord
from discord.ext import commands
import psutil
import sys
import os
import logging

logger = logging.getLogger(__name__)

class BasicCommands(commands.Cog):
    """Essential commands for the Discord bot"""
    
    def __init__(self, bot):
        self.bot = bot
        self.start_time = time.time()
    
    @commands.command(name="ping")
    async def ping(self, ctx):
        """Check the bot's latency"""
        latency = round(self.bot.latency * 1000)
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"Bot latency: **{latency}ms**",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    
    @commands.command(name="uptime")
    async def uptime(self, ctx):
        """Check how long the bot has been running"""
        uptime_seconds = int(time.time() - self.start_time)
        days, remainder = divmod(uptime_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        uptime_str = []
        if days > 0:
            uptime_str.append(f"{days} days")
        if hours > 0:
            uptime_str.append(f"{hours} hours")
        if minutes > 0:
            uptime_str.append(f"{minutes} minutes")
        if seconds > 0 or len(uptime_str) == 0:
            uptime_str.append(f"{seconds} seconds")
        
        embed = discord.Embed(
            title="⏱️ Bot Uptime",
            description=f"Bot has been online for: **{', '.join(uptime_str)}**",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)
    
    @commands.command(name="info", aliases=["about", "botinfo"])
    async def info(self, ctx):
        """Display information about the bot"""
        # Get system information
        python_version = platform.python_version()
        discord_version = discord.__version__
        os_info = f"{platform.system()} {platform.release()}"
        
        # Get memory usage
        process = psutil.Process(os.getpid())
        memory_usage = process.memory_info().rss / 1024 / 1024  # Convert to MB
        
        # Create the embed
        embed = discord.Embed(
            title=f"About {self.bot.user.name}",
            description="A Discord bot with modular functionality",
            color=discord.Color.blue()
        )
        
        # Add bot information
        embed.add_field(name="Bot Version", value="1.0.0", inline=True)
        embed.add_field(name="Servers", value=str(len(self.bot.guilds)), inline=True)
        embed.add_field(name="Users", value=str(sum(guild.member_count for guild in self.bot.guilds)), inline=True)
        
        # Add technical information
        embed.add_field(name="Python Version", value=python_version, inline=True)
        embed.add_field(name="Discord.py Version", value=discord_version, inline=True)
        embed.add_field(name="Memory Usage", value=f"{memory_usage:.2f} MB", inline=True)
        embed.add_field(name="Operating System", value=os_info, inline=True)
        
        # Set bot avatar as thumbnail if available
        if self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)
        
        # Add footer with timestamp
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
        embed.timestamp = ctx.message.created_at
        
        await ctx.send(embed=embed)
    
    @commands.command(name="invite")
    async def invite(self, ctx):
        """Get an invite link for the bot"""
        # Generate bot invite link with necessary permissions
        permissions = discord.Permissions(
            send_messages=True,
            embed_links=True,
            attach_files=True,
            read_messages=True,
            read_message_history=True,
            add_reactions=True,
            use_external_emojis=True,
            manage_messages=True
        )
        
        # Create invite URL manually since oauth_url may not be available in all versions
        invite_url = f"https://discord.com/api/oauth2/authorize?client_id={self.bot.user.id}&permissions={permissions.value}&scope=bot"
        
        embed = discord.Embed(
            title="🔗 Invite Link",
            description=f"[Click here to invite the bot to your server]({invite_url})",
            color=discord.Color.green()
        )
        
        embed.set_footer(text="The bot will request only necessary permissions")
        
        await ctx.send(embed=embed)
    
    @commands.command(name="prefix")
    async def prefix(self, ctx):
        """Show the bot's command prefix"""
        if isinstance(self.bot.command_prefix, str):
            prefix = self.bot.command_prefix
        else:
            prefix = "!"  # Default prefix if it's a callable or complex prefix
            
        embed = discord.Embed(
            title="📋 Command Prefix",
            description=f"My command prefix is: `{prefix}`",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="Example",
            value=f"Use `{prefix}help` to see the list of available commands.",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @commands.is_owner()
    @commands.command(name="shutdown", hidden=True)
    async def shutdown(self, ctx):
        """Shut down the bot (owner only)"""
        embed = discord.Embed(
            title="Shutting Down",
            description="The bot is now shutting down. Goodbye!",
            color=discord.Color.red()
        )
        
        await ctx.send(embed=embed)
        await self.bot.close()
        
    @commands.command(name="serverinfo")
    async def serverinfo(self, ctx):
        """Display information about the current server"""
        guild = ctx.guild
        
        # Count text and voice channels
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        
        # Count roles (excluding @everyone)
        role_count = len(guild.roles) - 1
        
        # Get server creation date
        created_at = guild.created_at.strftime("%B %d, %Y")
        
        # Create embed
        embed = discord.Embed(
            title=f"Server Information: {guild.name}",
            color=discord.Color.blue()
        )
        
        # Add server icon if available
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        # Add server information
        embed.add_field(name="Server ID", value=str(guild.id), inline=True)
        embed.add_field(name="Owner", value=f"{guild.owner}", inline=True)
        embed.add_field(name="Created On", value=created_at, inline=True)
        embed.add_field(name="Members", value=str(guild.member_count), inline=True)
        embed.add_field(name="Roles", value=str(role_count), inline=True)
        embed.add_field(name="Channels", value=f"{text_channels} Text | {voice_channels} Voice", inline=True)
        embed.add_field(name="Verification Level", value=str(guild.verification_level).title(), inline=True)
        
        # Add server features if any
        if guild.features:
            features = ", ".join(f.replace("_", " ").title() for f in guild.features)
            embed.add_field(name="Features", value=features, inline=False)
        
        # Add footer
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
        embed.timestamp = ctx.message.created_at
        
        await ctx.send(embed=embed)

async def setup(bot):
    """Add the cog to the bot"""
    await bot.add_cog(BasicCommands(bot))