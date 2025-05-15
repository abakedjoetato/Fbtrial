"""
Environment variables and configuration management.

This module loads environment variables from .env file and secrets,
and provides access to them.
"""

import os
import logging
from dotenv import load_dotenv

# Set up logging
logger = logging.getLogger(__name__)

# Load .env file if it exists
load_dotenv()

# Environment variable getters with default values
def get_discord_token():
    """Get the Discord bot token"""
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        logger.warning("DISCORD_TOKEN not found in environment")
    return token

def get_mongodb_uri():
    """Get the MongoDB URI"""
    uri = os.getenv("MONGODB_URI")
    if not uri:
        logger.warning("MONGODB_URI not found in environment, database features will be disabled")
    return uri

def get_mongodb_database():
    """Get the MongoDB database name"""
    db_name = os.getenv("MONGODB_DATABASE", "efkalpha")
    return db_name

def get_debug_guilds():
    """Get the debug guild IDs"""
    guilds_str = os.getenv("DEBUG_GUILDS", "")
    if not guilds_str:
        return []
    try:
        guilds = [int(g.strip()) for g in guilds_str.split(",") if g.strip()]
        return guilds
    except ValueError:
        logger.warning("Invalid DEBUG_GUILDS format, should be comma-separated guild IDs")
        return []

def get_log_level():
    """Get the log level"""
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
    if level not in valid_levels:
        logger.warning(f"Invalid LOG_LEVEL: {level}, defaulting to INFO")
        return "INFO"
    return level

def get_owner_ids():
    """Get the bot owner IDs"""
    owners_str = os.getenv("OWNER_IDS", "")
    if not owners_str:
        return []
    try:
        owners = [int(o.strip()) for o in owners_str.split(",") if o.strip()]
        return owners
    except ValueError:
        logger.warning("Invalid OWNER_IDS format, should be comma-separated user IDs")
        return []

def get_sftp_enabled():
    """Check if SFTP is enabled"""
    enabled = os.getenv("SFTP_ENABLED", "False").lower()
    return enabled in ("true", "1", "yes", "y", "t")

def get_sftp_config():
    """Get the SFTP configuration"""
    if not get_sftp_enabled():
        return None
    
    return {
        "host": os.getenv("SFTP_HOST", ""),
        "port": int(os.getenv("SFTP_PORT", "22")),
        "username": os.getenv("SFTP_USERNAME", ""),
        "password": os.getenv("SFTP_PASSWORD", ""),
        "remote_path": os.getenv("SFTP_REMOTE_PATH", "/"),
    }

def get_premium_api_key():
    """Get the premium API key"""
    return os.getenv("PREMIUM_API_KEY", "")

# Configuration dictionary
CONFIG = {
    "discord_token": get_discord_token(),
    "mongodb_uri": get_mongodb_uri(),
    "mongodb_database": get_mongodb_database(),
    "debug_guilds": get_debug_guilds(),
    "log_level": get_log_level(),
    "owner_ids": get_owner_ids(),
    "sftp_enabled": get_sftp_enabled(),
    "sftp_config": get_sftp_config(),
    "premium_api_key": get_premium_api_key(),
}

def get_config():
    """Get the full configuration dictionary"""
    return CONFIG