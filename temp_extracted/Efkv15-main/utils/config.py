"""
Configuration Module

This module provides configuration settings and constants for the Discord bot.
"""

import os
import logging
from typing import Dict, Any, Optional

# Configure logger
logger = logging.getLogger(__name__)

# Bot Version
VERSION = "1.0.0"

# Default command prefix (will be overridden by environment variable if set)
DEFAULT_PREFIX = "!"

# Default refresh intervals (in seconds)
EVENTS_REFRESH_INTERVAL = int(os.getenv("EVENTS_REFRESH_INTERVAL", "60"))
STATS_REFRESH_INTERVAL = int(os.getenv("STATS_REFRESH_INTERVAL", "300"))
LEADERBOARD_REFRESH_INTERVAL = int(os.getenv("LEADERBOARD_REFRESH_INTERVAL", "900"))

# MongoDB related settings
DEFAULT_MONGODB_URI = "mongodb://localhost:27017"
DEFAULT_DATABASE_NAME = "discord_bot"

class Config:
    """Configuration class for the bot"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        """Singleton pattern implementation"""
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance
        
    def __init__(self):
        """Initialize configuration"""
        # Skip if already initialized (singleton pattern)
        if self._initialized:
            return
            
        self._config = {}
        self._load_from_env()
        self._initialized = True
        
    def _load_from_env(self) -> None:
        """Load configuration from environment variables"""
        # Bot token
        self._config["token"] = os.getenv("DISCORD_TOKEN")
        
        # Command prefix
        self._config["prefix"] = os.getenv("COMMAND_PREFIX", DEFAULT_PREFIX)
        
        # MongoDB settings
        self._config["mongodb_uri"] = os.getenv("MONGODB_URI", DEFAULT_MONGODB_URI)
        self._config["database_name"] = os.getenv("DATABASE_NAME", DEFAULT_DATABASE_NAME)
        
        # Debug mode
        self._config["debug"] = os.getenv("DEBUG", "false").lower() == "true"
        
        # Premium features
        self._config["premium_enabled"] = os.getenv("PREMIUM_ENABLED", "false").lower() == "true"
        
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value"""
        return self._config.get(key, default)
        
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value"""
        self._config[key] = value
        
    @property
    def token(self) -> Optional[str]:
        """Get the bot token"""
        return self.get("token")
        
    @property
    def prefix(self) -> str:
        """Get the command prefix"""
        return self.get("prefix", DEFAULT_PREFIX)
        
    @property
    def mongodb_uri(self) -> str:
        """Get the MongoDB URI"""
        return self.get("mongodb_uri", DEFAULT_MONGODB_URI)
        
    @property
    def database_name(self) -> str:
        """Get the database name"""
        return self.get("database_name", DEFAULT_DATABASE_NAME)
        
    @property
    def debug(self) -> bool:
        """Check if debug mode is enabled"""
        return self.get("debug", False)
        
    @property
    def premium_enabled(self) -> bool:
        """Check if premium features are enabled"""
        return self.get("premium_enabled", False)