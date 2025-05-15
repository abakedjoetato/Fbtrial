"""
Debug script for bounties_fixed.py to help identify import issues
"""

import traceback
import sys
import importlib
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("debug")

def debug_import(module_name, detailed=True):
    """Debug import of a module to see where it fails"""
    try:
        logger.info(f"Trying to import {module_name}...")
        module = importlib.import_module(module_name)
        logger.info(f"Successfully imported {module_name}")
        if detailed:
            if hasattr(module, "__dict__"):
                for key in module.__dict__:
                    if not key.startswith("_"):
                        logger.info(f"  {key}: {type(module.__dict__[key])}")
        return True
    except Exception as e:
        logger.error(f"Failed to import {module_name}: {e}")
        if detailed:
            logger.error(traceback.format_exc())
        return False

def main():
    """Main debug function"""
    logger.info("===== Debugging bounties_fixed.py imports =====")
    
    # First check if discord_compat_layer can be imported
    if not debug_import("discord_compat_layer"):
        logger.error("Cannot import discord_compat_layer - this is a fundamental requirement")
        return
    
    # Try to import each component from discord_compat_layer that bounties_fixed uses
    components = [
        "Embed", "Color", "commands", "Interaction", "app_commands", 
        "slash_command", "ui", "View", "Button", "ButtonStyle", "Member",
        "SlashCommandGroup", "Guild"
    ]
    
    for component in components:
        try:
            logger.info(f"Checking if {component} is available in discord_compat_layer...")
            module = importlib.import_module("discord_compat_layer")
            if hasattr(module, component):
                logger.info(f"  ✓ {component} is available")
            else:
                logger.error(f"  ✗ {component} is NOT available in discord_compat_layer")
        except Exception as e:
            logger.error(f"Error checking for {component}: {e}")
    
    # Try other imports used by bounties_fixed
    debug_import("utils.command_handlers")
    debug_import("utils.safe_mongodb")
    debug_import("utils.interaction_handlers")
    debug_import("utils.error_telemetry")
    
    # Finally try to import bounties_fixed itself
    debug_import("cogs.bounties_fixed")

if __name__ == "__main__":
    main()