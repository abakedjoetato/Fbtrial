"""
Discord Compatibility Layer

This module provides compatibility between discord.py and py-cord,
allowing code written for discord.py to work with py-cord with minimal changes.
This follows the implementation guidelines from finish.md.
"""

import sys
import logging
import asyncio
from typing import Any, Callable, Dict, List, Optional, Union, TypeVar, overload

logger = logging.getLogger(__name__)

# Import discord core components
try:
    import discord
    from discord.ext import commands
    logger.info(f"Using Discord library version: {discord.__version__}")

    # Export core discord components
    Client = discord.Client
    
    # For Bot and AutoShardedBot, they could be in different places
    # depending on the library version
    if hasattr(discord, 'Bot'):
        Bot = discord.Bot
        AutoShardedBot = discord.AutoShardedBot
    else:
        Bot = commands.Bot
        AutoShardedBot = commands.AutoShardedBot
    
    # Export commonly used components from discord
    from discord import (
        # Core types
        Intents, Embed, Color, Colour, Message, Asset,
        # User types
        User, Member, ClientUser,
        # Guild types
        Guild, Role, Emoji, Permissions,
        # Channel types
        TextChannel, DMChannel, CategoryChannel, Thread, VoiceChannel, StageChannel, ForumChannel,
        # Status and presence
        Status, Activity, ActivityType, Game,
        # Utility
        Object, AllowedMentions, Attachment, File, ClientException,
        # UI Elements
        ui, ButtonStyle, SelectOption,
        # Interactions
        Interaction, InteractionType, InteractionResponse,
        # Errors
        HTTPException, Forbidden, NotFound, DiscordException
    )
    
    # Import command-related errors from discord.ext.commands
    from discord.ext.commands import (
        CommandNotFound, MissingRequiredArgument, CheckFailure, 
        CommandOnCooldown, MissingPermissions
    )
    
    # Try to add Presence if available
    try:
        from discord import Presence
    except ImportError:
        logger.debug("Presence class not available in this version")

    # Try to import some components that might not exist in all versions
    try:
        from discord import VoiceChannel, StageChannel, ForumChannel
    except ImportError:
        # Create stub classes if needed
        class VoiceChannel(TextChannel):
            pass
        class StageChannel(TextChannel):
            pass
        class ForumChannel(TextChannel):
            pass
        
    # Import app_commands from discord
    try:
        from discord import app_commands
        logger.info("Imported app_commands from discord directly")
    except ImportError:
        logger.warning("Failed to import app_commands from discord directly")
        app_commands = None
    
    # Export common components from app_commands if available
    if app_commands:
        try:
            CommandTree = getattr(app_commands, 'CommandTree', None)
            AppCommand = getattr(app_commands, 'Command', None)
            AppCommandGroup = getattr(app_commands, 'Group', None)
            ContextMenu = getattr(app_commands, 'ContextMenu', None)
            describe = getattr(app_commands, 'describe', None)
            check = getattr(app_commands, 'check', None)
            choices = getattr(app_commands, 'choices', None)
            guild_only = getattr(app_commands, 'guild_only', None)
            Option = getattr(app_commands, 'Option', None)
            Choice = getattr(app_commands, 'Choice', None)
        except Exception as e:
            logger.warning(f"Error importing from app_commands: {e}")
        
        # Add ApplicationContext if not available
        if not hasattr(discord, 'ApplicationContext'):
            class ApplicationContext:
                """Compatibility class for ApplicationContext"""
                def __init__(self, interaction):
                    self.interaction = interaction
                    self.bot = interaction.client
                    self.guild = interaction.guild
                    self.channel = interaction.channel
                    self.author = interaction.user
                    
                async def send(self, content=None, **kwargs):
                    """Send a response to the interaction"""
                    return await self.interaction.response.send_message(content=content, **kwargs)
    
    # Export common components from commands extension
    from discord.ext.commands import (
        # Command types
        Command, Group, CommandError, CommandNotFound, Cog,
        # Converters
        Converter, UserConverter, MemberConverter,
        # Checks and permissions
        check, has_permissions, bot_has_permissions, is_owner,
        # Utility
        Context, Paginator, HelpCommand
    )
    
    # Add custom slash_command support if not available
    if not hasattr(commands, 'slash_command'):
        def slash_command(*args, **kwargs):
            """Compatibility wrapper for slash_command"""
            logger.warning("slash_command not available, using regular command")
            return commands.command(*args, **kwargs)
        commands.slash_command = slash_command
        # Also add to module level
        globals()['slash_command'] = slash_command
        
    # Add SlashCommandGroup support if not available
    if not hasattr(discord, 'SlashCommandGroup'):
        class SlashCommandGroup:
            """Compatibility class for SlashCommandGroup"""
            def __init__(self, name, description=None, **kwargs):
                self.name = name
                self.description = description or "Command group"
                self.subcommands = {}
                self.kwargs = kwargs
                
            def command(self, *args, **kwargs):
                """Create a subcommand in this group"""
                def decorator(func):
                    cmd_name = kwargs.get('name', func.__name__)
                    self.subcommands[cmd_name] = func
                    return commands.command(*args, **kwargs)(func)
                return decorator
                
            def __call__(self, *args, **kwargs):
                """Allow using as a decorator"""
                return self.command(*args, **kwargs)
        
        # Export to discord module for easy import from discord
        discord.SlashCommandGroup = SlashCommandGroup
        
    # Export ApplicationContext, Choice, Option to module level
    if not hasattr(discord, 'ApplicationContext') and 'ApplicationContext' in locals():
        discord.ApplicationContext = locals()['ApplicationContext']
        # Also export at module level for direct import
        globals()['ApplicationContext'] = locals()['ApplicationContext']
        
    # Export Choice and Option
    if app_commands and hasattr(app_commands, 'Choice'):
        Choice = app_commands.Choice
        globals()['Choice'] = Choice
    else:
        # Create a simple Choice class if not available
        class Choice:
            """Compatibility class for Choice"""
            def __init__(self, name, value):
                self.name = name
                self.value = value
                
            def __repr__(self):
                return f"Choice(name='{self.name}', value='{self.value}')"
        globals()['Choice'] = Choice
        discord.Choice = Choice
                
    if app_commands and hasattr(app_commands, 'Option'):
        Option = app_commands.Option
        globals()['Option'] = Option
    else:
        # Create a simple Option class if not available
        class Option:
            """Compatibility class for Option"""
            def __init__(self, type=None, description=None, required=False, choices=None, **kwargs):
                self.type = type
                self.description = description or "No description"
                self.required = required
                self.choices = choices or []
                for key, value in kwargs.items():
                    setattr(self, key, value)
                    
            def __repr__(self):
                return f"Option(type={self.type}, description='{self.description}', required={self.required})"
        globals()['Option'] = Option
        discord.Option = Option
    
    # Export UI components if available
    try:
        import discord.ui
        ui = discord.ui
        # Export UI classes to the global scope
        View = discord.ui.View
        Button = discord.ui.Button
        Select = discord.ui.Select
        Modal = discord.ui.Modal
        TextInput = discord.ui.TextInput
    except ImportError:
        logger.warning("discord.ui module not available in this version")
        # Create a stub ui module
        class StubUI:
            def __init__(self):
                self.View = object
                self.Button = object
                self.Select = object
                self.Modal = object
                self.TextInput = object
        ui = StubUI()
        View = ui.View
        Button = ui.Button
        Select = ui.Select
        Modal = ui.Modal
        TextInput = ui.TextInput
        
    # Export version
    __version__ = discord.__version__

except ImportError as e:
    logger.error(f"Failed to import Discord library: {e}")
    sys.exit(1)

# Define type for context
Context = TypeVar('Context', bound=commands.Context)

# Export command decorators from commands extension for compatibility
command = commands.command
group = commands.group

# Add SlashCommandGroup support for compatibility
class SlashCommandGroup:
    """Compatibility class for slash command groups"""
    def __init__(self, name, description=None, **kwargs):
        self.name = name
        self.description = description or "Command group"
        self.subcommands = {}
        self.kwargs = kwargs
        
    def command(self, *args, **kwargs):
        """Create a subcommand in this group"""
        def decorator(func):
            cmd_name = kwargs.get('name', func.__name__)
            self.subcommands[cmd_name] = func
            return commands.command(*args, **kwargs)(func)
        return decorator
        
    def __call__(self, *args, **kwargs):
        """Allow using as a decorator"""
        return self.command(*args, **kwargs)

# Compatibility decorators for commands
def hybrid_command(*args, **kwargs):
    """Compatibility wrapper for hybrid_command"""
    cmd_fn = getattr(commands, 'hybrid_command', None)
    if cmd_fn is not None:
        return cmd_fn(*args, **kwargs)
    else:
        # Fallback to regular command
        logger.warning("Hybrid commands not available, using regular command instead")
        return commands.command(*args, **kwargs)

def hybrid_group(*args, **kwargs):
    """Compatibility wrapper for hybrid_group"""
    group_fn = getattr(commands, 'hybrid_group', None)
    if group_fn is not None:
        return group_fn(*args, **kwargs)
    else:
        # Fallback to regular group
        logger.warning("Hybrid groups not available, using regular group instead")
        return commands.group(*args, **kwargs)

# Helper functions for common tasks
async def send_embed(ctx, title=None, description=None, color=None, fields=None, footer=None, timestamp=None):
    """Helper to send an embed with common parameters"""
    # Create the embed
    embed = Embed(
        title=title, 
        description=description,
        color=color or Color.blue(),
        timestamp=timestamp
    )
    
    # Add fields if provided
    if fields:
        for name, value, inline in fields:
            embed.add_field(name=name, value=value, inline=inline)
    
    # Add footer if provided
    if footer:
        embed.set_footer(text=footer)
    
    # Send the embed
    return await ctx.send(embed=embed)

async def safe_send(channel, content=None, embed=None, file=None, files=None, **kwargs):
    """Safely send a message, handling common exceptions"""
    try:
        return await channel.send(content=content, embed=embed, file=file, files=files, **kwargs)
    except discord.errors.Forbidden:
        logger.warning(f"Missing permissions to send message in {channel}")
        return None
    except discord.errors.HTTPException as e:
        logger.error(f"Failed to send message: {e}")
        return None
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return None

# Premium feature checking helper
async def check_premium_feature(ctx, premium_manager, feature_name, error_message=None):
    """Check if a guild has access to a premium feature"""
    if not premium_manager:
        logger.warning("Premium manager not available for feature check")
        return False
        
    guild_id = ctx.guild.id if ctx.guild else None
    if not guild_id:
        await ctx.send("This command can only be used in a server.")
        return False
        
    has_access = await premium_manager.has_feature(guild_id, feature_name)
    if not has_access:
        if error_message:
            await ctx.send(error_message)
        else:
            embed = Embed(
                title="Premium Feature", 
                description=f"The `{feature_name}` feature requires a premium subscription.",
                color=Color.gold()
            )
            embed.add_field(
                name="Upgrade", 
                value="Contact the bot owner to upgrade your server.",
                inline=False
            )
            await ctx.send(embed=embed)
        return False
        
    return True

# Database helper functions
async def safe_db_operation(ctx, operation_func, error_message="Database operation failed."):
    """Safely perform a database operation, handling errors"""
    try:
        return await operation_func()
    except Exception as e:
        logger.error(f"Database operation failed: {e}")
        
        # Log the error with telemetry if available
        if hasattr(ctx.bot, 'error_telemetry') and ctx.bot.error_telemetry:
            await ctx.bot.error_telemetry.capture_exception(e, ctx=ctx)
            
        # Send error message to user
        await ctx.send(error_message)
        return None