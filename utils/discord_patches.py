"""
Discord Patches and Compatibility Layer

This module provides compatibility patches and utilities to make the code work with different
versions of Discord libraries, specifically py-cord 2.5.x and 2.6.x.
"""

import sys
import logging
import inspect
from typing import Optional, Dict, Any, List, Union, Callable, TypeVar

import discord
from discord.ext import commands

# Set up logging
logger = logging.getLogger(__name__)

# Get discord version
try:
    DISCORD_VERSION = discord.__version__
except AttributeError:
    DISCORD_VERSION = "unknown"

logger.info(f"Detected py-cord {DISCORD_VERSION}, applied compatibility patches")

# Check if we can import app_commands directly
try:
    from discord import app_commands
    HAS_APP_COMMANDS = True
except ImportError:
    HAS_APP_COMMANDS = False
    # Create a compatibility layer for app_commands
    class app_commands:
        """Compatibility layer for app_commands when not available"""
        
        @staticmethod
        def command(**kwargs):
            """Compatibility for slash command decorator"""
            logger.warning("slash_command not available, using regular command")
            return commands.command(**kwargs)
        
        @staticmethod
        def describe(**kwargs):
            """Compatibility for describe decorator"""
            def decorator(func):
                return func
            return decorator
            
        class Group:
            """Compatibility for app_commands.Group"""
            def __init__(self, name: str, description: str, **kwargs):
                self.name = name
                self.description = description
                self._kwargs = kwargs
                
            def command(self, **kwargs):
                """Command decorator for group"""
                logger.warning("slash_command not available, using regular command")
                return commands.command(**kwargs)
                
        class Choice:
            """Compatibility for app_commands.Choice"""
            def __init__(self, name: str, value: Any):
                self.name = name
                self.value = value
                
        class Option:
            """Compatibility for app_commands.Option"""
            def __init__(self, type=None, description=None, required=False, **kwargs):
                self.type = type
                self.description = description or "No description"
                self.required = required
                self.kwargs = kwargs
                
    # Export to the module level for direct import from discord
    if not hasattr(discord, 'Choice') and hasattr(app_commands, 'Choice'):
        discord.Choice = app_commands.Choice
    elif not hasattr(discord, 'Choice'):
        discord.Choice = app_commands.Choice

    if not hasattr(discord, 'Option') and hasattr(app_commands, 'Option'):
        discord.Option = app_commands.Option
    elif not hasattr(discord, 'Option'):
        discord.Option = app_commands.Option


# Add compatibility patches for Interaction objects
def get_interaction_response(interaction):
    """
    Get the response object from an interaction with compatibility for different Discord library versions.
    
    Args:
        interaction: The interaction object
    
    Returns:
        The response object or None
    """
    if not interaction:
        return None
        
    if hasattr(interaction, "response"):
        return interaction.response
    
    # For older versions or different implementations
    for attr_name in dir(interaction):
        if "response" in attr_name.lower() and not attr_name.startswith("__"):
            resp = getattr(interaction, attr_name)
            if resp and hasattr(resp, "send_message"):
                return resp
    
    return None


def wrap_with_error_handler(func):
    """
    Wrap a command function with error handling.
    
    Args:
        func: The command function to wrap
    
    Returns:
        The wrapped function
    """
    async def wrapper(self, ctx, *args, **kwargs):
        try:
            return await func(self, ctx, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error in command {func.__name__}: {e}", exc_info=True)
            try:
                error_message = f"An error occurred: {str(e)}"
                await ctx.send(error_message)
            except:
                logger.error("Failed to send error message", exc_info=True)
    
    # Copy metadata
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    
    return wrapper


# Utility function to create slash commands safely
def create_slash_command(**kwargs):
    """
    Create a slash command with compatibility for different Discord library versions.
    
    Args:
        **kwargs: Keyword arguments for the slash command
    
    Returns:
        Command decorator
    """
    if HAS_APP_COMMANDS:
        # Use native app_commands if available
        return app_commands.command(**kwargs)
    else:
        # Fallback to regular command
        logger.warning("slash_command not available, using regular command")
        return commands.command(**kwargs)