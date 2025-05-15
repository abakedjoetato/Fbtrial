#!/usr/bin/env python3
"""
Setup Verification Script

This script checks if all required files and environment variables are set up properly.
"""

import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def check_token():
    """Check if the Discord token is set in the environment variables"""
    token = os.environ.get("DISCORD_TOKEN")
    if not token:
        logger.error("DISCORD_TOKEN not found in environment variables!")
        print("❌ DISCORD_TOKEN not found in environment variables")
        return False
    
    logger.info("DISCORD_TOKEN is properly set")
    print("✅ DISCORD_TOKEN is properly set")
    return True

def check_files():
    """Check if all required files are present"""
    required_files = [
        "discord_compat_layer.py",
        "bot.py",
        "run_replit.py",
        "main.py",
        ".replit.workflow",
        "cogs/admin_fixed.py",
        "cogs/help_fixed.py",
        "cogs/basic_fixed.py",
        "cogs/bounties_fixed.py",
        "cogs/guild_settings_fixed.py",
        "cogs/cog_template_fixed.py",
        "utils/interaction_handlers.py",
        "utils/error_handlers.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        logger.error(f"Missing required files: {', '.join(missing_files)}")
        print(f"❌ Missing required files: {', '.join(missing_files)}")
        return False
    
    logger.info("All required files are present")
    print("✅ All required files are present")
    return True

def check_cog_imports():
    """Check if the core cogs are properly importing from discord_compat_layer"""
    cogs_to_check = [
        "cogs/guild_settings_fixed.py",
        "cogs/basic_fixed.py",
        "cogs/bounties_fixed.py",
        "cogs/cog_template_fixed.py"
    ]
    
    problematic_cogs = []
    for cog_path in cogs_to_check:
        if not Path(cog_path).exists():
            continue
            
        with open(cog_path, 'r') as f:
            content = f.read()
            if "import discord" in content and "from discord_compat_layer import" not in content:
                problematic_cogs.append(cog_path)
    
    if problematic_cogs:
        logger.error(f"Cogs with direct discord imports: {', '.join(problematic_cogs)}")
        print(f"❌ Cogs with direct discord imports: {', '.join(problematic_cogs)}")
        return False
    
    logger.info("All checked cogs are using the compatibility layer")
    print("✅ All checked cogs are using the compatibility layer")
    return True

def main():
    """Main check function"""
    print("\n=== Discord Bot Setup Verification ===\n")
    
    token_ok = check_token()
    files_ok = check_files()
    imports_ok = check_cog_imports()
    
    print("\n=== Verification Summary ===")
    
    if token_ok and files_ok and imports_ok:
        print("\n✅ All checks passed! The bot should be ready to run.")
        print("   To start the bot, run: python run_replit.py\n")
        return 0
    else:
        print("\n❌ Some checks failed. Please fix the issues above before running the bot.\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())