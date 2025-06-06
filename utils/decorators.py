"""
Command decorators for the Tower of Temptation PvP Statistics Discord Bot.

This module provides decorators for Discord.py commands to enforce:
1. Guild-based permission checks
2. Premium feature access validation
3. Server validation with cross-guild isolation
4. Error handling and rate limiting
5. Command metrics and performance tracking

These decorators can be applied to both traditional commands and slash commands
with consistent behavior and validation patterns.
"""
import logging
import asyncio
import time
import functools
import traceback
from datetime import datetime, timedelta
from typing import (
    Callable, Optional, List, Dict, Any, Union, TypeVar, 
    Coroutine, cast, Awaitable, Set, Tuple, Generic
)

import discord
from discord.ext import commands
# Use our compatibility layer
from utils.discord_patches import app_commands

from config import PREMIUM_TIERS, COMMAND_PREFIX as PREFIX
from utils.premium import (
    validate_premium_feature, validate_server_limit, 
    get_guild_premium_tier, check_tier_access
)
from utils.server_utils import (
    standardize_server_id, validate_server_id_format,
    get_server_safely, check_server_existence, enforce_guild_isolation,
    validate_server, check_server_exists
)
from utils.helpers import is_home_guild_admin
from models.guild import Guild
from utils.async_utils import AsyncCache, retryable

logger = logging.getLogger(__name__)

# Type variables for generics
T = TypeVar('T')
CommandT = TypeVar('CommandT', bound=Callable[..., Coroutine[Any, Any, Any]])
SlashCommandT = TypeVar('SlashCommandT', bound=Callable[..., Coroutine[Any, Any, Any]])

# Cache configuration
COMMAND_GUILD_CACHE_TTL = 60  # 1 minute
COMMAND_COOLDOWNS = {}  # Map of user IDs to command timestamp
ERROR_TRACKING = {}  # Map of command names to error counts
COMMAND_METRICS = {}  # Map of command names to metrics (invoke count, avg runtime)

# AsyncCache instance for guild objects in commands
guild_cache = AsyncCache(ttl=COMMAND_GUILD_CACHE_TTL)

# Track commands with high error rates
HIGH_ERROR_THRESHOLD = 0.25  # 25% error rate is considered high
ERROR_COUNT_THRESHOLD = 5    # Minimum error count for tracking
MAX_SLOW_COMMANDS = 10       # Number of slow commands to track
SLOW_COMMAND_THRESHOLD = 1.0  # Command is considered slow if it takes more than 1 second

def has_guild_permissions(**perms):
    """Decorator that checks if a user has the required guild permissions.
    
    This works with both traditional commands and application commands (slash commands).
    
    Args:
        **perms: The permissions to check (e.g., manage_guild=True)
        
    Returns:
        Command decorator function
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Determine if this is a traditional command or application command
            is_app_command = False
            ctx = None
            interaction = None
            
            # Check for traditional command context
            if args and len(args) > 1 and isinstance(args[1], commands.Context):
                ctx = args[1]
                is_app_command = False
            # Check for application command interaction
            elif args and len(args) > 1 and isinstance(args[1], discord.Interaction):
                interaction = args[1]
                is_app_command = True
                
            # If we couldn't determine the context/interaction, just run the command
            if not ctx and not interaction:
                return await func(*args, **kwargs)
                
            # Handle traditional commands
            if not is_app_command and ctx:
                # Skip check in DMs (no guild)
                if not ctx.guild:
                    return await func(*args, **kwargs)
                    
                # Get the permissions of the user in the guild
                permissions = ctx.author.guild_permissions
                
                # Check all required permissions
                missing = [perm for perm, value in perms.items() 
                         if value and not getattr(permissions, perm, False)]
                
                if missing:
                    # Return error if permissions are missing
                    raise commands.MissingPermissions(missing)
                
                # Permissions check passed, run the command
                return await func(*args, **kwargs)
                
            # Handle application commands (slash commands)
            if is_app_command and interaction:
                # Skip check in DMs (no guild)
                if not interaction.guild:
                    return await func(*args, **kwargs)
                    
                # Get the permissions of the user in the guild
                if interaction.user:
                    member = interaction.guild.get_member(interaction.user.id)
                    if member:
                        permissions = member.guild_permissions
                        
                        # Check all required permissions
                        missing = [perm for perm, value in perms.items() 
                                 if value and not getattr(permissions, perm, False)]
                        
                        if missing:
                            # Send error message for slash commands
                            try:
                                error_message = f"You are missing required permissions to run this command: {', '.join(missing)}"
                                await interaction.response.send_message(error_message, ephemeral=True)
                            except Exception:
                                # Response might have already been sent
                                pass
                            return None
                
                # Permissions check passed, run the command
                return await func(*args, **kwargs)
                
            # Fallback - just run the command if we couldn't check permissions
            return await func(*args, **kwargs)
            
        return wrapper
    return decorator


def premium_tier(tier_level: int = None):
    """Decorator that requires a specific premium tier level to use a command.
    
    This is a simplified alias for premium_tier_required for improved readability.
    
    Args:
        tier_level: Minimum premium tier level required to use the command
        
    Returns:
        Command decorator function
    """
    return premium_tier_required(tier_level=tier_level)
    
def premium_feature(feature_name: str = None):
    """Decorator that requires access to a specific premium feature to use a command.
    
    This is a simplified alias for premium_tier_required with feature focus.
    
    Args:
        feature_name: Name of the premium feature required to use the command
        
    Returns:
        Command decorator function
    """
    return premium_tier_required(feature_name=feature_name)

def premium_tier_required(tier_level: int = None, feature_name: str = None):
    """
    Decorator to check if the guild has the required premium tier level or feature access.

    This decorator implements tier inheritance, ensuring higher tiers 
    have access to all features from lower tiers.

    This works on both traditional commands and application commands.

    Args:
        tier_level: Minimum tier level required (0-4), or None if using feature_name
        feature_name: Name of the feature to check, or None if using tier_level

    Returns:
        Command decorator
    """
    # Validate arguments - must provide either tier_level or feature_name
    if tier_level is None and feature_name is None:
        raise ValueError("Either tier_level or feature_name must be provided")
        
    # Import here to avoid circular imports
    from utils.premium import PREMIUM_FEATURES
    
    # If feature_name is provided, get the corresponding tier level
    if feature_name is not None:
        if feature_name in PREMIUM_FEATURES:
            tier_level = PREMIUM_FEATURES.get(feature_name, 1)  # Default to tier 1 if not found
        else:
            # If feature not found in mapping, use a safe default
            tier_level = 1
            logger.warning(f"Feature '{feature_name}' not found in PREMIUM_FEATURES mapping. Using tier {tier_level} as default.")
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Determine if this is a traditional command or application command
            if args and hasattr(args[0], 'bot'):
                # Traditional command
                cog = args[0] 
                # For traditional commands, context is the second arg
                if len(args) > 1 and isinstance(args[1], commands.Context):
                    ctx = args[1]

                    # Skip check in DMs (no guild)
                    if ctx and not ctx.guild:
                        return await func(*args, **kwargs)

                    # Get guild model
                    db = cog.bot.db if hasattr(cog.bot, 'db') else None
                    if db is None:
                        logger.error("Cannot check premium tier: bot.db is not available")
                        return await func(*args, **kwargs)

                    # Log what we're checking
                    logger.debug(f"Checking premium tier access for command: {func.__name__}, required tier: {tier_level}")

                    # Import premium_utils here to avoid circular imports
                    from utils.premium_utils import standardize_premium_check
                    
                    # Check premium tier access using the standardized function
                    # This handles tier inheritance, normalization, and proper error formatting
                    has_access, error_message = await standardize_premium_check(
                        db, 
                        str(ctx.guild.id),
                        f"tier_{tier_level}", 
                        error_message=True
                    )

                    # If has_access is False, send the error message
                    if has_access is False:
                        if error_message is not None:
                            await ctx.send(error_message)
                        return None

                    # Access is granted, continue with command
                    return await func(*args, **kwargs)

            elif args and hasattr(args[0], 'client'):
                # Application command
                cog = args[0]
                # For app commands, interaction is the second arg
                if len(args) > 1 and isinstance(args[1], discord.Interaction):
                    interaction = args[1]

                    # Skip check in DMs (no guild)
                    if interaction and not interaction.guild:
                        return await func(*args, **kwargs)

                    # Get guild model
                    db = cog.client.db if hasattr(cog.client, 'db') else None
                    if db is None:
                        logger.error("Cannot check premium tier: client.db is not available")
                        return await func(*args, **kwargs)

                    # Log what we're checking
                    logger.debug(f"Checking premium tier access for slash command: {func.__name__}, required tier: {tier_level}")

                    # Import premium_utils here to avoid circular imports
                    from utils.premium_utils import standardize_premium_check
                    
                    # Check premium tier access using the standardized function
                    # This handles tier inheritance, normalization, and proper error formatting
                    has_access, error_message = await standardize_premium_check(
                        db, 
                        str(interaction.guild_id),
                        f"tier_{tier_level}", 
                        error_message=True
                    )

                    # If has_access is False, send the error message
                    if has_access is False:
                        if error_message is not None:
                            try:
                                await interaction.response.send_message(error_message, ephemeral=True)
                            except Exception as e:
                                logger.error(f"Error sending tier access error: {e}")
                                # Fallback to deferred responses if response already sent
                                try:
                                    await interaction.followup.send(error_message, ephemeral=True)
                                except Exception as e2:
                                    logger.error(f"Failed to send followup message: {e2}")
                        return None

                    # Access is granted, continue with command
                    return await func(*args, **kwargs)

            # If we can't determine the command type or context, just run the command
            return await func(*args, **kwargs)

        return wrapper
    return decorator


def requires_premium_feature(feature_name: str):
    """
    Decorator to check if the guild has access to a premium feature.

    This decorator implements tier inheritance, ensuring higher tiers
    have access to all features from lower tiers.

    This works on both traditional commands and application commands.

    Args:
        feature_name: Name of the feature to check

    Returns:
        Command decorator
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Determine if this is a traditional command or application command
            if args and hasattr(args[0], 'bot'):
                # Traditional command
                cog = args[0] 
                # For traditional commands, context is the second arg
                if len(args) > 1 and isinstance(args[1], commands.Context):
                    ctx = args[1]

                    # Skip check in DMs (no guild)
                    if ctx and not ctx.guild:
                        return await func(*args, **kwargs)

                    # Get guild model
                    db = cog.bot.db if hasattr(cog.bot, 'db') else None
                    if db is None:
                        logger.error("Cannot check premium feature: bot.db is not available")
                        return await func(*args, **kwargs)

                    # Standardize guild_id to string for consistent handling
                    guild_id = str(ctx.guild.id)
                    
                    # Import premium_utils here to avoid circular imports
                    from utils.premium_utils import verify_premium_for_feature, standardize_premium_check
                    
                    # Log what we're checking
                    logger.debug(f"Checking premium feature access for command: {func.__name__}, feature: {feature_name}")
                    
                    # Check premium feature access using the standardized utility
                    # This handles normalization, tier inheritance, and proper error formatting
                    has_access, error_message = await standardize_premium_check(
                        db, 
                        guild_id,
                        feature_name, 
                        error_message=True
                    )

                    # If has_access is False, send the error message
                    if has_access is False:
                        if error_message is not None:
                            await ctx.send(error_message)
                        return None

                    # Access is granted, continue with command
                    return await func(*args, **kwargs)

            elif args and hasattr(args[0], 'client'):
                # Application command
                cog = args[0]
                # For app commands, interaction is the second arg
                if len(args) > 1 and isinstance(args[1], discord.Interaction):
                    interaction = args[1]

                    # Skip check in DMs (no guild)
                    if interaction and not interaction.guild:
                        return await func(*args, **kwargs)

                    # Get guild model
                    db = cog.client.db if hasattr(cog.client, 'db') else None
                    if db is None:
                        logger.error("Cannot check premium feature: client.db is not available")
                        return await func(*args, **kwargs)

                    # Standardize guild_id to string for consistent handling
                    guild_id = str(interaction.guild_id)
                    
                    # Import premium_utils here to avoid circular imports
                    from utils.premium_utils import verify_premium_for_feature, standardize_premium_check
                    
                    # Log what we're checking
                    logger.debug(f"Checking premium feature access for slash command: {func.__name__}, feature: {feature_name}")
                    
                    # Check premium feature access using the standardized utility
                    # This handles normalization, tier inheritance, and proper error formatting
                    has_access, error_message = await standardize_premium_check(
                        db, 
                        guild_id,
                        feature_name, 
                        error_message=True
                    )

                    # If has_access is False, send the error message
                    if has_access is False:
                        if error_message is not None:
                            try:
                                await interaction.response.send_message(error_message, ephemeral=True)
                            except Exception as e:
                                logger.error(f"Error sending feature access error: {e}")
                                # Fallback to deferred responses if response already sent
                                try:
                                    await interaction.followup.send(error_message, ephemeral=True)
                                except Exception as e2:
                                    logger.error(f"Failed to send followup message: {e2}")
                        return None

                    # Access is granted, continue with command
                    return await func(*args, **kwargs)

            # If we can't determine the command type or context, just run the command
            return await func(*args, **kwargs)

        return wrapper
    return decorator


def validate_guild_server(server_id_param: str = "server_id"):
    """
    Decorator to validate server ID belongs to the guild and exists.

    For both traditional commands and application commands.

    Args:
        server_id_param: Name of the parameter containing the server ID

    Returns:
        Command decorator
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Get server_id from kwargs
            server_id = kwargs.get(server_id_param)
            if server_id is None or server_id == "":
                # If server_id not in kwargs, check command args
                for i, arg in enumerate(args):
                    # Skip self/cog
                    if i == 0:
                        continue
                    # Skip context/interaction
                    if i == 1 and isinstance(arg, (commands.Context, discord.Interaction)):
                        continue
                    # Assume next positional arg might be server_id
                    if isinstance(arg, (str, int)):
                        server_id = str(arg)
                        break

            if server_id is None or server_id == "":
                logger.warning(f"Cannot validate server: {server_id_param} not found in args or kwargs")
                return await func(*args, **kwargs)

            # Determine if this is a traditional command or application command
            cog = None
            guild_id = None
            error_callback = None
            db = None

            if args and hasattr(args[0], 'bot'):
                # Traditional command
                cog = args[0]
                if len(args) > 1 and isinstance(args[1], commands.Context):
                    ctx = args[1]
                    # Skip check in DMs (no guild)
                    if ctx and not ctx.guild:
                        return await func(*args, **kwargs)
                    guild_id = str(ctx.guild.id)
                    db = cog.bot.db if hasattr(cog.bot, 'db') else None
                    # Error callback defined as a separate function to allow await
                    async def send_error(msg):
                        await ctx.send(msg)
                    error_callback = send_error

            elif args and hasattr(args[0], 'client'):
                # Application command
                cog = args[0]
                if len(args) > 1 and isinstance(args[1], discord.Interaction):
                    interaction = args[1]
                    # Skip check in DMs (no guild)
                    if interaction and not interaction.guild:
                        return await func(*args, **kwargs)
                    guild_id = str(interaction.guild_id)
                    db = cog.client.db if hasattr(cog.client, 'db') else None
                    # Error callback defined as a separate function to allow await
                    async def send_error(msg):
                        await interaction.response.send_message(msg, ephemeral=True)
                    error_callback = send_error

            # If we can't determine the command type or context, just run the command
            if guild_id is None or guild_id == "" or db is None:
                return await func(*args, **kwargs)

            # Validate server
            guild_model = await Guild.get_by_id(db, guild_id)
            is_valid, error_message = await validate_server(guild_model, server_id)

            if is_valid is None:
                if error_message and error_callback:
                    await error_callback(error_message)
                return

            return await func(*args, **kwargs)

        return wrapper
    return decorator


def requires_home_guild_admin():
    """
    Decorator to check if the user is a home guild admin.

    This works on both traditional commands and application commands.

    Returns:
        Command decorator
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Determine if this is a traditional command or application command
            if args and hasattr(args[0], 'bot'):
                # Traditional command
                cog = args[0]
                # For traditional commands, context is the second arg
                if len(args) > 1 and isinstance(args[1], commands.Context):
                    ctx = args[1]

                    # Skip check in DMs (no guild)
                    if ctx and not ctx.guild:
                        await ctx.send("This command can only be used in a server.")
                        return

                    # Check if user is a home guild admin
                    if not is_home_guild_admin(cog.bot, ctx.author.id):
                        await ctx.send("Only home guild administrators can use this command.")
                        return

                    return await func(*args, **kwargs)

            elif args and hasattr(args[0], 'client'):
                # Application command
                cog = args[0]
                # For app commands, interaction is the second arg
                if len(args) > 1 and isinstance(args[1], discord.Interaction):
                    interaction = args[1]

                    # Skip check in DMs (no guild)
                    if interaction and not interaction.guild:
                        await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
                        return

                    # Check if user is a home guild admin
                    if not is_home_guild_admin(cog.client, interaction.user.id):
                        await interaction.response.send_message("Only home guild administrators can use this command.", ephemeral=True)
                        return

                    return await func(*args, **kwargs)

            # If we can't determine the command type or context, just run the command
            return await func(*args, **kwargs)

        return wrapper
    return decorator


def has_admin_permission():
    """
    Decorator to check if the user has admin permissions.

    This works on both traditional commands and application commands.

    Returns:
        Command decorator
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Determine if this is a traditional command or application command
            if args and hasattr(args[0], 'bot'):
                # Traditional command
                cog = args[0]
                # For traditional commands, context is the second arg
                if len(args) > 1 and isinstance(args[1], commands.Context):
                    ctx = args[1]

                    # Skip check in DMs (no guild)
                    if ctx and not ctx.guild:
                        await ctx.send("This command can only be used in a server.")
                        return

                    # Check if user is admin
                    if ctx.author.guild_permissions.administrator is None:
                        await ctx.send("You need administrator permissions to use this command.")
                        return

                    return await func(*args, **kwargs)

            elif args and hasattr(args[0], 'client'):
                # Application command
                cog = args[0]
                # For app commands, interaction is the second arg
                if len(args) > 1 and isinstance(args[1], discord.Interaction):
                    interaction = args[1]

                    # Skip check in DMs (no guild)
                    if interaction and not interaction.guild:
                        await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
                        return

                    # Check if user is admin
                    member = interaction.guild.get_member(interaction.user.id)
                    if not member or not member.guild_permissions.administrator:
                        await interaction.response.send_message("You need administrator permissions to use this command.", ephemeral=True)
                        return

                    return await func(*args, **kwargs)

            # If we can't determine the command type or context, just run the command
            return await func(*args, **kwargs)

        return wrapper
    return decorator


def has_mod_permission():
    """
    Decorator to check if the user has moderator permissions.

    This works on both traditional commands and application commands.
    Moderator is defined as having either kick_members, ban_members,
    manage_messages, or administrator permissions.

    Returns:
        Command decorator
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Determine if this is a traditional command or application command
            if args and hasattr(args[0], 'bot'):
                # Traditional command
                cog = args[0]
                # For traditional commands, context is the second arg
                if len(args) > 1 and isinstance(args[1], commands.Context):
                    ctx = args[1]

                    # Skip check in DMs (no guild)
                    if ctx and not ctx.guild:
                        await ctx.send("This command can only be used in a server.")
                        return

                    # Check if user has mod permissions
                    permissions = ctx.author.guild_permissions
                    is_mod = (permissions.administrator or 
                             permissions.kick_members or 
                             permissions.ban_members or 
                             permissions.manage_messages)

                    if is_mod is None:
                        await ctx.send("You need moderator permissions to use this command.")
                        return

                    return await func(*args, **kwargs)

            elif args and hasattr(args[0], 'client'):
                # Application command
                cog = args[0]
                # For app commands, interaction is the second arg
                if len(args) > 1 and isinstance(args[1], discord.Interaction):
                    interaction = args[1]

                    # Skip check in DMs (no guild)
                    if interaction and not interaction.guild:
                        await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
                        return

                    # Check if user has mod permissions
                    member = interaction.guild.get_member(interaction.user.id)
                    if member is None:
                        await interaction.response.send_message("Could not find your permissions. Please try again.", ephemeral=True)
                        return

                    permissions = member.guild_permissions
                    is_mod = (permissions.administrator or 
                             permissions.kick_members or 
                             permissions.ban_members or 
                             permissions.manage_messages)

                    if is_mod is None:
                        await interaction.response.send_message("You need moderator permissions to use this command.", ephemeral=True)
                        return

                    return await func(*args, **kwargs)

            # If we can't determine the command type or context, just run the command
            return await func(*args, **kwargs)

        return wrapper
    return decorator


def check_server_limit():
    """
    Decorator to check if the guild has reached its server limit.

    For both traditional commands and application commands.

    Returns:
        Command decorator
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Determine if this is a traditional command or application command
            cog = None
            guild_id = None
            error_callback = None
            db = None

            if args and hasattr(args[0], 'bot'):
                # Traditional command
                cog = args[0]
                if len(args) > 1 and isinstance(args[1], commands.Context):
                    ctx = args[1]
                    # Skip check in DMs (no guild)
                    if ctx and not ctx.guild:
                        return await func(*args, **kwargs)
                    guild_id = str(ctx.guild.id)
                    db = cog.bot.db if hasattr(cog.bot, 'db') else None
                    # Error callback defined as a separate function to allow await
                    async def send_error(msg):
                        await ctx.send(msg)
                    error_callback = send_error

            elif args and hasattr(args[0], 'client'):
                # Application command
                cog = args[0]
                if len(args) > 1 and isinstance(args[1], discord.Interaction):
                    interaction = args[1]
                    # Skip check in DMs (no guild)
                    if interaction and not interaction.guild:
                        return await func(*args, **kwargs)
                    guild_id = str(interaction.guild_id)
                    db = cog.client.db if hasattr(cog.client, 'db') else None
                    # Error callback defined as a separate function to allow await
                    async def send_error(msg):
                        await interaction.response.send_message(msg, ephemeral=True)
                    error_callback = send_error

            # If we can't determine the command type or context, just run the command
            if guild_id is None or guild_id == "" or db is None:
                return await func(*args, **kwargs)

            # Check server limit
            guild_model = await Guild.get_by_id(db, guild_id)
            has_capacity, error_message = await validate_server_limit(guild_model)

            if has_capacity is None:
                if error_message and error_callback:
                    await error_callback(error_message)
                return

            return await func(*args, **kwargs)

        return wrapper
    return decorator


def command_handler(
    premium_feature: Optional[str] = None, 
    server_id_param: Optional[str] = None,
    check_server_limits: bool = False,
    guild_only_command: bool = True,
    cooldown_seconds: Optional[int] = None,
    error_messages: Optional[Dict[str, str]] = None,
    timeout_seconds: int = 10,
    retry_count: int = 2,
    log_metrics: bool = True,
    validate_parameters: bool = True,
    guild_only: bool = None,
    collection_name: Optional[str] = None,
    operation_type: Optional[str] = None
):
    """
    Enhanced command decorator that combines multiple validations and error handling.

    This comprehensive decorator provides bulletproof command handling with:
    1. Guild-only enforcement
    2. Premium feature validation
    3. Server ID validation and guild isolation
    4. Server limit enforcement
    5. Command cooldowns and rate limiting
    6. Automatic error recovery and predictive error handling
    7. Command execution metrics and performance tracking
    8. Timeout protection with configurable retries
    9. Comprehensive logging

    Args:
        premium_feature: Optional premium feature to check
        server_id_param: Optional server ID parameter name to validate
        check_server_limits: Whether to check server limits
        guild_only_command: Whether command requires a guild context
        cooldown_seconds: Optional cooldown in seconds
        error_messages: Optional custom error messages
        timeout_seconds: Timeout for command execution in seconds
        retry_count: Number of times to retry on transient errors
        log_metrics: Whether to log command metrics
        validate_parameters: Whether to validate command parameters

    Returns:
        Command decorator
    """
    # Default error messages
    default_errors = {
        "dm_context": "This command can only be used in a server.",
        "cooldown": "Please wait {seconds} seconds before using this command again.",
        "guild_not_found": "Server not set up. Please run `/setup` first.",
        "database_error": "Database connection error. Please try again later.",
        "timeout": "Command timed out. Please try again.",
        "unknown_error": "An error occurred while processing the command."
    }

    # Combine default and custom error messages
    messages = default_errors.copy()
    if error_messages is not None:
        messages.update(error_messages)

    def decorator(func: CommandT) -> CommandT:
        command_name = func.__name__

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()

            # Initialize tracking for this command if needed
            if command_name not in COMMAND_METRICS:
                COMMAND_METRICS[command_name] = {
                    "invocations": 0,
                    "errors": 0,
                    "avg_runtime": 0,
                    "last_error": None,
                    "success_rate": 1.0
                }

            # Increment invocation counter
            COMMAND_METRICS[command_name]["invocations"] += 1

            # Extract command context
            ctx = None
            interaction = None
            user_id = None
            guild_id = None
            db = None
            bot = None

            # Determine command type and extract context
            is_traditional = False
            is_app_command = False

            if args and hasattr(args[0], 'bot'):
                # Traditional command
                cog = args[0]
                bot = cog.bot
                if len(args) > 1 and isinstance(args[1], commands.Context):
                    ctx = args[1]
                    is_traditional = True
                    user_id = ctx.author.id if ctx.author else None
                    guild_id = ctx.guild.id if ctx.guild else None
                    db = bot.db if hasattr(bot, 'db') else None

            elif args and hasattr(args[0], 'client'):
                # Application command
                cog = args[0]
                bot = cog.client
                if len(args) > 1 and isinstance(args[1], discord.Interaction):
                    interaction = args[1]
                    is_app_command = True
                    user_id = interaction.user.id if interaction.user else None
                    guild_id = interaction.guild_id
                    db = bot.db if hasattr(bot, 'db') else None

            # If we can't determine the command type or context, just run the command
            if not (is_traditional or is_app_command):
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    logger.error(f"Error in {command_name}: {e}")
                    traceback.print_exc()
                    return None

            # Helper function to send error messages
            async def send_error(message: str):
                try:
                    if is_traditional and ctx:
                        await ctx.send(message)
                    elif is_app_command and interaction:
                        # Check if interaction is already responded to
                        if interaction and interaction.response:
                            if not interaction.response.is_done():
                                await interaction.response.send_message(message, ephemeral=True)
                            else:
                                await interaction.followup.send(message, ephemeral=True)
                except Exception as e:
                    logger.error(f"Error sending command error message: {e}")

            # 1. Check if we're in a guild (if required)
            # Use guild_only parameter if provided, otherwise fall back to guild_only_command
            use_guild_only = guild_only if guild_only is not None else guild_only_command
            if use_guild_only and not guild_id:
                await send_error(messages["dm_context"])
                return None

            # 2. Apply cooldown if specified
            if cooldown_seconds and user_id:
                user_key = f"{user_id}:{command_name}"
                now = time.time()

                if user_key in COMMAND_COOLDOWNS:
                    last_use = COMMAND_COOLDOWNS[user_key]
                    time_diff = now - last_use

                    if time_diff < cooldown_seconds:
                        remaining = int(cooldown_seconds - time_diff)
                        cooldown_msg = messages["cooldown"].format(seconds=remaining)
                        await send_error(cooldown_msg)
                        return None

                # Update cooldown timestamp
                COMMAND_COOLDOWNS[user_key] = now

            # Skip remaining checks if no guild (already passed guild_only check)
            if guild_id is None or guild_id == "":
                try:
                    result = await func(*args, **kwargs)

                    # Update metrics
                    runtime = time.time() - start_time
                    metrics = COMMAND_METRICS[command_name]
                    metrics["avg_runtime"] = (metrics["avg_runtime"] * (metrics["invocations"] - 1) + runtime) / metrics["invocations"]

                    return result
                except Exception as e:
                    # Track error
                    COMMAND_METRICS[command_name]["errors"] += 1
                    COMMAND_METRICS[command_name]["last_error"] = str(e)
                    COMMAND_METRICS[command_name]["success_rate"] = (
                        (COMMAND_METRICS[command_name]["invocations"] - COMMAND_METRICS[command_name]["errors"]) / 
                        max(1, COMMAND_METRICS[command_name]["invocations"])
                    )

                    logger.error(f"Error in command {command_name}: {e}")
                    await send_error(messages["unknown_error"])
                    return None

            # 3. Get guild model (needed for all remaining checks)
            guild_model = None
            try:
                # CRITICAL FIX: Ensure guild_id is string for consistent handling
                string_guild_id = str(guild_id)
                cache_key = f"guild:{string_guild_id}"
                guild_model = await guild_cache.get(cache_key)

                # CRITICAL FIX: Fixed reversed logic - only try to fetch from DB if DB is not None
                if guild_model is None and db is not None:
                    logger.info(f"Guild cache miss, fetching from database: {string_guild_id}")
                    # Use get_by_guild_id with consistent string ID handling
                    guild_model = await Guild.get_by_guild_id(db, string_guild_id)
                    if guild_model is not None:
                        logger.info(f"Caching guild model for {string_guild_id}, tier: {guild_model.premium_tier}")
                        await guild_cache.set(cache_key, guild_model)
                    else:
                        logger.warning(f"No guild model found for {string_guild_id}")
                elif db is None:
                    logger.warning(f"Database not available for guild model lookup: {string_guild_id}")
            except Exception as e:
                logger.error(f"Database error getting guild model: {e}")
                await send_error(messages["database_error"])
                return None

            # Enhanced handling for premium validation
            if premium_feature is not None:
                # First check if we have a guild model for checking features
                if guild_model is not None:
                    # If guild_model exists, use the normal validation flow
                    has_access, error_message = await validate_premium_feature(guild_model, premium_feature)
                    if has_access is None:
                        if error_message is not None:
                            await send_error(error_message)
                        return None
                else:
                    # If guild_model doesn't exist, check premium tier directly
                    # This allows premium access without requiring complete guild setup
                    # Get the minimum tier required for this feature
                    from utils.premium import get_minimum_tier_for_feature
                    required_tier = await get_minimum_tier_for_feature(premium_feature)

                    if required_tier is not None:
                        # Directly check premium tier access with the DB
                        has_access, error_message = await check_tier_access(db, guild_id, required_tier)

                        if has_access is not None:
                            # Continue with execution if premium tier is sufficient
                            logger.info(f"Guild {guild_id} has premium access to {premium_feature} without guild model")

                            # Check if this is a server-related feature requiring guild model
                            guild_only_features = {
                                "economy", "gambling", "enhanced_economy", "premium_leaderboards",
                                "custom_embeds", "advanced_statistics"
                            }

                            # For guild-only premium features, we can continue without a server
                            if premium_feature in guild_only_features:
                                # For purely guild-level premium features, we can proceed
                                pass
                            else:
                                # For server-dependent features, we should create a guild model
                                try:
                                    # Try to create guild model on-the-fly
                                    guild_model = await Guild.get_or_create(db, guild_id)
                                    if guild_model is None:
                                        # If still can't create guild, show setup message for server features
                                        await send_error(messages["guild_not_found"])
                                        return None
                                except Exception as e:
                                    logger.error(f"Error creating guild model on-the-fly: {e}")
                                    await send_error(messages["guild_not_found"])
                                    return None
                        else:
                            # Premium check failed, return error message
                            if error_message is not None:
                                await send_error(error_message)
                            return None
                    else:
                        # Feature not found in any tier, show guild setup message
                        await send_error(messages["guild_not_found"])
                        return None
            elif guild_model is None:
                # No premium check but guild model required - show standard error
                await send_error(messages["guild_not_found"])
                return None

            # 5. Check server limits
            if check_server_limits is not None:
                has_capacity, error_message = await validate_server_limit(guild_model)
                if has_capacity is None:
                    if error_message is not None:
                        await send_error(error_message)
                    return None

            # 6. Validate server ID if specified
            if server_id_param is not None:
                # Get server_id from kwargs
                server_id = kwargs.get(server_id_param)
                if server_id is None or server_id == "":
                    # If server_id not in kwargs, check command args
                    for i, arg in enumerate(args):
                        # Skip self/code>
                        if i == 0:
                            continue
                        # Skip context/interaction
                        if i == 1 and isinstance(arg, (commands.Context, discord.Interaction)):
                            continue
                        # Assume next positional arg might be server_id
                        if isinstance(arg, (str, int)):
                            server_id = str(arg)
                            break

                if server_id is not None:
                    # Standardize server ID format
                    server_id = standardize_server_id(server_id)

                    # Validate server format
                    if not validate_server_id_format(server_id):
                        await send_error(f"Invalid server ID format: {server_id}")
                        return None

                    # Validate server exists and belongs to this guild
                    try:
                        # Check guild isolation
                        isolation_valid = await enforce_guild_isolation(db, server_id, guild_id)
                        if isolation_valid is None:
                            await send_error(f"Server '{server_id}' does not belong to this Discord server.")
                            return None

                        # Check server existence
                        server = await get_server_safely(db, server_id, guild_id)
                        if server is None:
                            await send_error(f"Server '{server_id}' not found. Use `/list_servers` to see available servers.")
                            return None
                    except Exception as e:
                        logger.error(f"Error validating server {server_id}: {e}")
                        await send_error(f"Error validating server: {e}")
                        return None

            # All checks passed, run the command with error handling and timeout protection
            retry_attempts = 0
            last_error = None
            transient_errors = (asyncio.TimeoutError, ConnectionError, OSError)

            # Track if we're about to execute a command that's been problematic
            is_problematic = False
            if command_name in COMMAND_METRICS:
                if COMMAND_METRICS[command_name]["invocations"] > 5:
                    success_rate = COMMAND_METRICS[command_name]["success_rate"]
                    if success_rate < 0.75:  # Less than 75% success rate
                        is_problematic = True
                        logger.warning(f"Executing problematic command {command_name} with historical success rate of {success_rate:.1%}")

            while retry_attempts <= retry_count:
                try:
                    # Use timeout for the command if specified
                    if timeout_seconds > 0:
                        async with asyncio.timeout(timeout_seconds):
                            # Add an informational message for retries
                            if retry_attempts > 0:
                                logger.info(f"Retry attempt {retry_attempts}/{retry_count} for command {command_name}")
                                # For problematic commands with retries, inform the user
                                if is_problematic and is_app_command and interaction and interaction.response and not interaction.response.is_done():
                                    await interaction.response.defer(ephemeral=True, thinking=True)

                            # Execute the command
                            result = await func(*args, **kwargs)
                    else:
                        # Execute without timeout
                        result = await func(*args, **kwargs)

                    # Command succeeded, update metrics
                    runtime = time.time() - start_time
                    metrics = COMMAND_METRICS[command_name]
                    metrics["avg_runtime"] = (metrics["avg_runtime"] * (metrics["invocations"] - 1) + runtime) / metrics["invocations"]
                    metrics["success_rate"] = (
                        (metrics["invocations"] - metrics["errors"]) / 
                        max(1, metrics["invocations"])
                    )

                    # Log metrics if enabled
                    if log_metrics and metrics["invocations"] % 10 == 0:  # Log every 10 invocations
                        logger.info(
                            f"Command {command_name} metrics: "
                            f"{metrics['invocations']} invocations, "
                            f"{metrics['errors']} errors, "
                            f"{metrics['success_rate']:.1%} success rate, "
                            f"{metrics['avg_runtime']:.3f}s avg runtime"
                        )

                    return result

                except asyncio.TimeoutError as e:
                    last_error = e
                    retry_attempts += 1
                    logger.warning(f"Command {command_name} timed out (attempt {retry_attempts}/{retry_count+1})")

                    # If this is the last retry, report the error
                    if retry_attempts > retry_count:
                        COMMAND_METRICS[command_name]["errors"] += 1
                        COMMAND_METRICS[command_name]["last_error"] = "Command timed out"
                        COMMAND_METRICS[command_name]["success_rate"] = (
                            (COMMAND_METRICS[command_name]["invocations"] - COMMAND_METRICS[command_name]["errors"]) / 
                            max(1, COMMAND_METRICS[command_name]["invocations"])
                        )

                        logger.error(f"Command {command_name} timed out after {retry_count+1} attempts")
                        await send_error(f"{messages['timeout']} (after {retry_count+1} attempts)")
                        return None

                    # Otherwise wait briefly before retry
                    await asyncio.sleep(0.5 * retry_attempts)  # Progressive backoff

                except (ConnectionError, OSError) as e:
                    # These are network-related errors that might be transient
                    last_error = e
                    retry_attempts += 1
                    logger.warning(f"Network error in command {command_name}: {e} (attempt {retry_attempts}/{retry_count+1})")

                    # If this is the last retry, report the error
                    if retry_attempts > retry_count:
                        COMMAND_METRICS[command_name]["errors"] += 1
                        COMMAND_METRICS[command_name]["last_error"] = f"Network error: {e}"
                        COMMAND_METRICS[command_name]["success_rate"] = (
                            (COMMAND_METRICS[command_name]["invocations"] - COMMAND_METRICS[command_name]["errors"]) / 
                            max(1, COMMAND_METRICS[command_name]["invocations"])
                        )

                        logger.error(f"Network error in command {command_name} after {retry_count+1} attempts: {e}")
                        await send_error("Network error occurred. Please try again later.")
                        return None

                    # Otherwise wait briefly before retry
                    await asyncio.sleep(1.0 * retry_attempts)  # Progressive backoff

                except Exception as e:
                    # Non-transient errors, don't retry
                    COMMAND_METRICS[command_name]["errors"] += 1
                    COMMAND_METRICS[command_name]["last_error"] = str(e)
                    COMMAND_METRICS[command_name]["success_rate"] = (
                        (COMMAND_METRICS[command_name]["invocations"] - COMMAND_METRICS[command_name]["errors"]) / 
                        max(1, COMMAND_METRICS[command_name]["invocations"])
                    )

                    error_details = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
                    logger.error(f"Error in command {command_name}: {e}\n{error_details}")

                    # Analyze error patterns to provide better user feedback
                    user_message = f"{messages['unknown_error']}"

                    if "not found" in str(e).lower() or "does not exist" in str(e).lower():
                        user_message = "The requested item could not be found. Please check your inputs and try again."
                    elif "permission" in str(e).lower() or "access" in str(e).lower():
                        user_message = "You don't have permission to use this command or access this resource."
                    elif "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                        user_message = "This item already exists. Please use a different name or identifier."
                    elif "limit" in str(e).lower() or "exceeded" in str(e).lower() or "too many" in str(e).lower():
                        user_message = "You've reached a limit for this action. Please try again later or contact an administrator."
                    elif "invalid" in str(e).lower() or "format" in str(e).lower():
                        user_message = "One or more values you provided are invalid. Please check your inputs and try again."
                    elif "discord" in str(e).lower() and "api" in str(e).lower():
                        user_message = "Discord API error occurred. Please try again later."
                    elif "database" in str(e).lower() or "mongo" in str(e).lower():
                        user_message = "Database operation failed. Please try again later."
                    else:
                        # Include error details for unexpected errors
                        user_message = f"{messages['unknown_error']} Error: {e}"

                    # Send the error message to the user
                    await send_error(user_message)
                    return None

        # Update wrapper attributes for introspection
        wrapper.premium_feature = premium_feature
        wrapper.server_id_param = server_id_param
        wrapper.check_server_limits = check_server_limits
        wrapper.guild_only_command = guild_only_command
        wrapper.cooldown_seconds = cooldown_seconds
        wrapper.timeout_seconds = timeout_seconds
        wrapper.retry_count = retry_count
        wrapper.log_metrics = log_metrics
        wrapper.validate_parameters = validate_parameters

        return cast(CommandT, wrapper)

    return decorator


def get_command_metrics() -> Dict[str, Dict[str, Any]]:
    """
    Get all command metrics.

    Returns:
        Dict[str, Dict[str, Any]]: Mapping of command names to metrics
    """
    return COMMAND_METRICS


# Database operation decorator
T = TypeVar('T')
DB_OP_METRICS: Dict[str, Dict[str, Any]] = {}

def db_operation(
    operation_type: Optional[str] = None,
    collection_name: Optional[str] = None,
    retry_count: int = 3, 
    timeout_seconds: int = 10,
    log_metrics: bool = True
):
    """
    Decorator for database operations that provides:
    1. Consistent error handling
    2. Retry logic for transient errors
    3. Timeout protection
    4. Logging and metrics
    5. Transaction support
    
    Args:
        operation_type: Type of database operation (for metrics)
        collection_name: Name of the collection being operated on
        retry_count: Number of retries for transient errors
        timeout_seconds: Timeout in seconds for the operation
        log_metrics: Whether to log metrics
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable[..., Coroutine[Any, Any, T]]) -> Callable[..., Coroutine[Any, Any, T]]:
        # Get the operation name from the function if not provided
        op_type = operation_type or func.__name__
        coll_name = collection_name or "unknown"
        
        # Initialize metrics for this operation
        if log_metrics:
            if op_type not in DB_OP_METRICS:
                DB_OP_METRICS[op_type] = {
                    "calls": 0,
                    "errors": 0,
                    "retries": 0,
                    "timeouts": 0,
                    "avg_duration": 0,
                    "call_times": [],
                }
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            start_time = time.time()
            attempt = 0
            last_error = None
            
            # Try operation with retries
            while attempt <= retry_count:
                attempt += 1
                
                try:
                    # Set timeout for the operation
                    result = await asyncio.wait_for(
                        func(*args, **kwargs),
                        timeout=timeout_seconds
                    )
                    
                    # Log metrics on success
                    if log_metrics:
                        duration = time.time() - start_time
                        DB_OP_METRICS[op_type]["calls"] += 1
                        DB_OP_METRICS[op_type]["call_times"].append(duration)
                        
                        # Keep only the last 100 call times
                        if len(DB_OP_METRICS[op_type]["call_times"]) > 100:
                            DB_OP_METRICS[op_type]["call_times"].pop(0)
                            
                        # Recalculate average duration
                        DB_OP_METRICS[op_type]["avg_duration"] = sum(
                            DB_OP_METRICS[op_type]["call_times"]
                        ) / len(DB_OP_METRICS[op_type]["call_times"])
                    
                    return result
                    
                except asyncio.TimeoutError:
                    last_error = f"Database operation timed out after {timeout_seconds}s"
                    if log_metrics:
                        DB_OP_METRICS[op_type]["timeouts"] += 1
                        
                except Exception as e:
                    last_error = str(e)
                    if log_metrics:
                        DB_OP_METRICS[op_type]["errors"] += 1
                
                # If we've reached max retries, log and raise
                if attempt > retry_count:
                    logger.error(
                        f"Database operation {op_type} on {coll_name} failed after {attempt} attempts: {last_error}"
                    )
                    # Re-raise the last exception
                    raise Exception(f"Database operation failed: {last_error}")
                
                # Log retry attempt
                if log_metrics:
                    DB_OP_METRICS[op_type]["retries"] += 1
                
                logger.warning(
                    f"Retrying database operation {op_type} on {coll_name} (attempt {attempt}/{retry_count})"
                )
                
                # Wait before retrying with exponential backoff
                await asyncio.sleep(0.5 * (2 ** (attempt - 1)))
        
        # Store metadata on the function for introspection
        wrapper.operation_type = op_type
        wrapper.collection_name = coll_name
        
        return wrapper
    
    return decorator


def get_problematic_commands() -> List[Dict[str, Any]]:
    """
    Get commands with high error rates.

    Returns:
        List[Dict[str, Any]]: List of problematic commands with their metrics
    """
    problematic = []

    for cmd_name, metrics in COMMAND_METRICS.items():
        # Only consider commands with enough invocations
        if isinstance(metrics, dict) and metrics["invocations"] < ERROR_COUNT_THRESHOLD:
            continue

        # Check error rate
        if isinstance(metrics, dict) and metrics["success_rate"] < (1.0 - HIGH_ERROR_THRESHOLD):
            problematic.append({
                "name": cmd_name,
                "error_rate": 1.0 - metrics["success_rate"],
                "invocations": metrics["invocations"],
                "errors": metrics["errors"],
                "last_error": metrics["last_error"],
                "avg_runtime": metrics["avg_runtime"]
            })

    # Sort by error rate (highest first)
    return sorted(problematic, key=lambda x: x["error_rate"], reverse=True)


def get_slow_commands() -> List[Dict[str, Any]]:
    """
    Get commands with slow execution times.

    Returns:
        List[Dict[str, Any]]: List of slow commands with their metrics
    """
    slow_commands = []

    for cmd_name, metrics in COMMAND_METRICS.items():
        # Only consider commands with enough invocations
        if isinstance(metrics, dict) and metrics["invocations"] < ERROR_COUNT_THRESHOLD:
            continue

        # Check runtime
        if isinstance(metrics, dict) and metrics["avg_runtime"] > SLOW_COMMAND_THRESHOLD:
            slow_commands.append({
                "name": cmd_name,
                "avg_runtime": metrics["avg_runtime"],
                "invocations": metrics["invocations"],
                "success_rate": metrics["success_rate"]
            })

    # Sort by runtime (slowest first)
    sorted_commands = sorted(slow_commands, key=lambda x: x["avg_runtime"], reverse=True)

    # Only return the top N slow commands
    return sorted_commands[:MAX_SLOW_COMMANDS]


def generate_command_metrics_report() -> str:
    """
    Generate a human-readable report of command metrics.

    Returns:
        str: Formatted report
    """
    if COMMAND_METRICS is None:
        return "No command metrics collected yet."

    # Calculate overall stats
    total_invocations = sum(m["invocations"] for m in COMMAND_METRICS.values())
    total_errors = sum(m["errors"] for m in COMMAND_METRICS.values())
    avg_success_rate = sum(m["success_rate"] for m in COMMAND_METRICS.values()) / len(COMMAND_METRICS)

    # Get problematic and slow commands
    problematic = get_problematic_commands()
    slow = get_slow_commands()

    # Build report
    lines = [
        "📊 **Command Metrics Report**",
        f"Total Commands: {len(COMMAND_METRICS)}",
        f"Total Invocations: {total_invocations}",
        f"Overall Success Rate: {avg_success_rate:.2%}",
        f"Total Errors: {total_errors}",
        ""
    ]

    # Top commands by usage
    top_commands = sorted(
        [(name, m["invocations"]) for name, m in COMMAND_METRICS.items()],
        key=lambda x: x[1],
        reverse=True
    )[:5]

    if top_commands is not None:
        lines.append("**Top Commands by Usage:**")
        for i, (name, count) in enumerate(top_commands, 1):
            lines.append(f"{i}. `{name}`: {count} invocations")
        lines.append("")

    # Problematic commands
    if problematic is not None:
        lines.append("⚠️ **Problematic Commands:**")
        for i, cmd in enumerate(problematic, 1):
            lines.append(f"{i}. `{cmd['name']}`: {(1.0 - cmd['success_rate']):.2%} error rate ({cmd['errors']}/{cmd['invocations']})")
            if cmd['last_error']:
                lines.append(f"   Last error: {cmd['last_error']}")
        lines.append("")

    # Slow commands
    if slow is not None:
        lines.append("🐢 **Slow Commands:**")
        for i, cmd in enumerate(slow, 1):
            lines.append(f"{i}. `{cmd['name']}`: {cmd['avg_runtime']:.2f}s avg runtime ({cmd['invocations']} invocations)")
        lines.append("")

    return "\n".join(lines)


def reset_command_metrics():
    """Reset all command metrics."""
    COMMAND_METRICS.clear()
    COMMAND_COOLDOWNS.clear()
    ERROR_TRACKING.clear()


def guild_only():
    """
    Decorator to ensure the command is only used in a guild.

    This works for both traditional commands and application commands.

    Returns:
        Command decorator
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Determine if this is a traditional command or application command
            if args and hasattr(args[0], 'bot'):
                # Traditional command
                if len(args) > 1 and isinstance(args[1], commands.Context):
                    ctx = args[1]
                    if ctx and not ctx.guild:
                        await ctx.send("This command can only be used in a server.")
                        return
                    return await func(*args, **kwargs)

            elif args and hasattr(args[0], 'client'):
                # Application command
                if len(args) > 1 and isinstance(args[1], discord.Interaction):
                    interaction = args[1]
                    if interaction and not interaction.guild:
                        await interaction.response.send_message(
                            "This command can only be used in a server.", ephemeral=True
                        )
                        return
                    return await func(*args, **kwargs)

            # If we can't determine the command type or context, just run the command
            return await func(*args, **kwargs)

        return wrapper
    return decorator