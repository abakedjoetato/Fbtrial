"""
Interaction Handlers Module

This module provides utility functions for handling Discord interactions.
"""

import logging
import asyncio
from typing import Optional, Any, Callable, Dict, Union

from discord import Interaction, Embed, Color
from discord.errors import NotFound, HTTPException

logger = logging.getLogger(__name__)

async def defer_interaction(interaction: Interaction, *, ephemeral: bool = False) -> bool:
    """
    Defer an interaction's response to avoid timing out.
    
    Args:
        interaction: The interaction to defer
        ephemeral: Whether the deferred response should be ephemeral
        
    Returns:
        Whether the deferral was successful
    """
    if not interaction:
        return False
        
    try:
        if hasattr(interaction, 'response'):
            await interaction.response.defer(ephemeral=ephemeral)
        else:
            # Fallback for different Discord library versions
            defer_method = getattr(interaction, "defer", None)
            if defer_method and callable(defer_method):
                await defer_method(ephemeral=ephemeral)
            else:
                # Try to find similar methods
                for attr_name in dir(interaction):
                    if "defer" in attr_name.lower() and not attr_name.startswith("__"):
                        method = getattr(interaction, attr_name)
                        if callable(method):
                            try:
                                await method(ephemeral=ephemeral)
                                return True
                            except Exception:
                                continue
                return False
        return True
    except Exception as e:
        logger.error(f"Error deferring interaction: {e}")
        return False

async def respond_to_interaction(
    interaction: Interaction, 
    content: Optional[str] = None, 
    embed: Optional[Embed] = None,
    ephemeral: bool = False,
    **kwargs
) -> bool:
    """
    Respond to an interaction with compatibility for different Discord library versions.
    
    Args:
        interaction: The interaction to respond to
        content: Text content for the response
        embed: Embed for the response
        ephemeral: Whether the response should be ephemeral
        **kwargs: Additional kwargs for the response
        
    Returns:
        Whether the response was successful
    """
    if not interaction:
        return False
        
    try:
        if hasattr(interaction, 'response') and hasattr(interaction.response, 'send_message'):
            # Modern response method
            await interaction.response.send_message(
                content=content, 
                embed=embed, 
                ephemeral=ephemeral,
                **kwargs
            )
        else:
            # Try to find similar methods
            for attr_name in dir(interaction):
                if "response" in attr_name.lower() and not attr_name.startswith("__"):
                    response_obj = getattr(interaction, attr_name)
                    if response_obj:
                        for method_name in dir(response_obj):
                            if "send" in method_name.lower() and callable(getattr(response_obj, method_name)):
                                method = getattr(response_obj, method_name)
                                try:
                                    await method(content=content, embed=embed, ephemeral=ephemeral, **kwargs)
                                    return True
                                except Exception:
                                    continue
            
            # Fallback to direct methods on interaction
            for method_name in dir(interaction):
                if "send" in method_name.lower() and callable(getattr(interaction, method_name)):
                    method = getattr(interaction, method_name)
                    try:
                        await method(content=content, embed=embed, ephemeral=ephemeral, **kwargs)
                        return True
                    except Exception:
                        continue
                        
            # Ultimate fallback
            logger.warning(f"Could not find appropriate method to respond to interaction {interaction}")
            return False
            
        return True
    except Exception as e:
        logger.error(f"Error responding to interaction: {e}")
        return False

async def edit_interaction_response(
    interaction: Interaction, 
    content: Optional[str] = None, 
    embed: Optional[Embed] = None,
    **kwargs
) -> bool:
    """
    Edit an interaction response with compatibility for different Discord library versions.
    
    Args:
        interaction: The interaction to edit the response for
        content: New text content for the response
        embed: New embed for the response
        **kwargs: Additional kwargs for the edit
        
    Returns:
        Whether the edit was successful
    """
    if not interaction:
        return False
        
    try:
        # Try modern method
        if hasattr(interaction, 'edit_original_response'):
            await interaction.edit_original_response(content=content, embed=embed, **kwargs)
            return True
            
        # Try response object method
        if hasattr(interaction, 'response') and hasattr(interaction.response, 'edit_message'):
            await interaction.response.edit_message(content=content, embed=embed, **kwargs)
            return True
            
        # Try followup.edit method
        if hasattr(interaction, 'followup') and hasattr(interaction.followup, 'edit_message'):
            try:
                await interaction.followup.edit_message('@original', content=content, embed=embed, **kwargs)
                return True
            except Exception:
                pass
                
        # Try to find similar methods
        for attr_name in dir(interaction):
            if "edit" in attr_name.lower() and not attr_name.startswith("__"):
                method = getattr(interaction, attr_name)
                if callable(method):
                    try:
                        await method(content=content, embed=embed, **kwargs)
                        return True
                    except Exception:
                        continue
        
        logger.warning(f"Could not find appropriate method to edit interaction response {interaction}")
        return False
    except Exception as e:
        logger.error(f"Error editing interaction response: {e}")
        return False

async def send_error_response(
    interaction: Interaction, 
    error_message: str,
    ephemeral: bool = True
) -> bool:
    """
    Send an error response to an interaction.
    
    Args:
        interaction: The interaction to respond to
        error_message: The error message to display
        ephemeral: Whether the response should be ephemeral
        
    Returns:
        Whether the response was successful
    """
    embed = Embed(
        title="Error",
        description=error_message,
        color=Color.red()
    )
    
    try:
        return await respond_to_interaction(
            interaction, 
            embed=embed, 
            ephemeral=ephemeral
        )
    except Exception as e:
        logger.error(f"Error sending error response: {e}")
        return False

async def safely_respond_to_interaction(
    interaction: Interaction, 
    content: Optional[str] = None, 
    embed: Optional[Embed] = None,
    ephemeral: bool = True,
    **kwargs
) -> bool:
    """
    Safely respond to an interaction, handling different states the interaction might be in.
    
    This function checks if the interaction has been responded to already and uses
    the appropriate method (initial response, followup, or edit) based on the state.
    
    Args:
        interaction: The interaction to respond to
        content: Text content for the response
        embed: Embed for the response
        ephemeral: Whether the response should be ephemeral
        **kwargs: Additional kwargs for the response
        
    Returns:
        Whether the response was successful
    """
    if not interaction:
        return False
        
    try:
        # Check if interaction has been responded to already
        if hasattr(interaction, 'response') and hasattr(interaction.response, 'is_done'):
            if interaction.response.is_done():
                # Already responded, use followup or edit
                if hasattr(interaction, 'followup') and hasattr(interaction.followup, 'send'):
                    # Use followup
                    await interaction.followup.send(
                        content=content, 
                        embed=embed, 
                        ephemeral=ephemeral,
                        **kwargs
                    )
                    return True
                else:
                    # Try to edit the original response
                    return await edit_interaction_response(
                        interaction,
                        content=content,
                        embed=embed,
                        **kwargs
                    )
            else:
                # Not responded to yet, use initial response
                return await respond_to_interaction(
                    interaction,
                    content=content,
                    embed=embed,
                    ephemeral=ephemeral,
                    **kwargs
                )
        else:
            # Fallback to regular respond method
            return await respond_to_interaction(
                interaction,
                content=content,
                embed=embed,
                ephemeral=ephemeral,
                **kwargs
            )
    except Exception as e:
        logger.error(f"Error in safely_respond_to_interaction: {e}")
        # Last resort attempt
        try:
            if hasattr(interaction, 'followup') and hasattr(interaction.followup, 'send'):
                await interaction.followup.send(
                    content=content or "An error occurred",
                    embed=embed,
                    ephemeral=ephemeral,
                    **kwargs
                )
                return True
        except Exception:
            pass
        return False