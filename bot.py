"""
Discord Bot Implementation using compatibility layer
"""

import os
import sys
import time
import logging
import asyncio
from typing import Optional, List, Dict, Any

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("bot.log")
    ]
)

logger = logging.getLogger(__name__)

# Import from compatibility layer to ensure consistent behavior
from discord_compat_layer import (
    Bot as DCBot, Intents, Embed, Color, app_commands, Activity, ActivityType, Game
)

# Import MongoDB client for database functionality
try:
    from motor.motor_asyncio import AsyncIOMotorClient
    MONGODB_AVAILABLE = True
except ImportError:
    logger.warning("MongoDB not available, database functionality will be disabled")
    MONGODB_AVAILABLE = False

# Check if premium features are available
try:
    from premium_config import PremiumManager
    PREMIUM_AVAILABLE = True
except ImportError:
    logger.warning("Premium manager not available, premium features will be disabled")
    PREMIUM_AVAILABLE = False

class Bot(DCBot):
    """A Discord bot implementation using compatibility layer"""
    
    def __init__(self, production=False):
        """Initialize the bot with necessary intents"""
        # Set up intents
        intents = Intents.default()
        intents.message_content = True  # Required for command prefix
        intents.members = True  # Required for member-related features
        
        # Initialize the bot with required intents
        super().__init__(
            command_prefix="!",  # Default command prefix
            intents=intents,
            description="A versatile Discord bot for enhanced server management"
        )
        
        # Set start time
        self.start_time = time.time()
        
        # Flag for production mode
        self.production = production
        
        # Initialize database connection to None (will be set up in init_db)
        self.mongo_client = None
        self.db = None
        
        # Initialize premium manager
        self.premium_manager = None
        
        # Track loaded cogs
        self.loaded_cogs_count = 0
        self.failed_cogs = []
        
        logger.info("Bot initialized")
    
    async def init_db(self):
        """Initialize database connection"""
        if not MONGODB_AVAILABLE:
            logger.warning("MongoDB client not available, database functionality disabled")
            return False
            
        try:
            # Get MongoDB connection string from environment variables
            mongo_uri = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
            db_name = os.environ.get("DB_NAME", "discord_bot")
            
            # Connect to MongoDB
            self.mongo_client = AsyncIOMotorClient(mongo_uri)
            
            # Get database
            self.db = self.mongo_client[db_name]
            
            # Test connection
            await self.mongo_client.admin.command('ping')
            
            logger.info(f"Connected to MongoDB database: {db_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            self.mongo_client = None
            self.db = None
            return False
    
    async def setup_hook(self):
        """Setup hook that's called before the bot starts"""
        # Initialize database
        db_success = await self.init_db()
        
        # Set up premium features if available
        if PREMIUM_AVAILABLE:
            try:
                self.premium_manager = PremiumManager(self)
                await self.premium_manager.initialize()
                logger.info("Premium manager initialized")
            except Exception as e:
                logger.error(f"Failed to initialize premium manager: {e}")
                self.premium_manager = None
                
        # Load all cogs
        await self.load_all_cogs()
    
    async def load_all_cogs(self):
        """Load all cogs from the cogs directory"""
        logger.info("Loading cogs...")
        
        # List of core cogs to load first
        core_cogs = [
            "cogs.debug_fixed",
            "cogs.admin_fixed",
            "cogs.help_fixed",
            "cogs.premium_new_updated_fixed",
            "cogs.basic_fixed",
            "cogs.cog_template_fixed",
            "cogs.bounties_fixed",
            "cogs.guild_settings_fixed"
        ]
        
        # Load core cogs first
        for cog in core_cogs:
            try:
                # Handle both async and sync setup functions
                try:
                    await self.load_extension(cog)
                except TypeError:
                    # For older cogs that don't use async setup
                    self.load_extension(cog)
                self.loaded_cogs_count += 1
                logger.info(f"Loaded core cog: {cog}")
            except Exception as e:
                self.failed_cogs.append(cog)
                logger.error(f"Failed to load core cog {cog}: {e}")
                logger.error(f"Error details: {e}", exc_info=True)
        
        # Load all other cogs from the cogs directory that end with _fixed.py
        cogs_dir = "cogs"
        for filename in os.listdir(cogs_dir):
            # Skip non-Python files and special files
            if not filename.endswith(".py") or filename.startswith("_"):
                continue
                
            # Get cog name (without .py extension)
            cog_name = filename[:-3]
            
            # Skip already loaded core cogs
            full_cog_name = f"cogs.{cog_name}"
            if full_cog_name in core_cogs:
                continue
                
            # Only consider files ending with _fixed.py that aren't already loaded
            if not filename.endswith("_fixed.py"):
                continue
                
            # Skip any cogs that conflict with existing command names
            if cog_name.startswith("bot_"):
                logger.warning(f"Skipping cog {cog_name} - name conflicts with py-cord (starts with 'bot_')")
                self.failed_cogs.append(full_cog_name)
                continue
                
            # Skip original cogs that have fixed versions
            if cog_name in ["help", "admin", "general", "events", "error_handler", "player_links"]:
                logger.info(f"Skipping original cog {cog_name} - fixed version already loaded")
                continue
                
            # Try to load the cog
            try:
                try:
                    await self.load_extension(full_cog_name)
                except TypeError:
                    # For older cogs that don't use async setup
                    self.load_extension(full_cog_name)
                self.loaded_cogs_count += 1
                logger.info(f"Loaded cog: {full_cog_name}")
            except Exception as e:
                self.failed_cogs.append(full_cog_name)
                logger.error(f"Failed to load cog {full_cog_name}: {e}")
                logger.error(f"Error details: {e}", exc_info=True)
                
        logger.info(f"Loaded {self.loaded_cogs_count} cogs, {len(self.failed_cogs)} failed")
    
    async def on_ready(self):
        """Called when the bot is ready"""
        if self.user:
            logger.info(f"Logged in as {self.user.name} (ID: {self.user.id})")
            logger.info(f"Connected to {len(self.guilds)} guilds")
        else:
            logger.info("Bot is ready but user information is not available")
        
        # Set activity
        activity_type = os.environ.get("ACTIVITY_TYPE", "watching")
        activity_name = os.environ.get("ACTIVITY_NAME", "for commands")
        
        if activity_type.lower() == "playing":
            activity = Game(name=activity_name)
        elif activity_type.lower() == "listening":
            activity = Activity(type=ActivityType.listening, name=activity_name)
        elif activity_type.lower() == "competing":
            activity = Activity(type=ActivityType.competing, name=activity_name)
        else:  # Default to watching
            activity = Activity(type=ActivityType.watching, name=activity_name)
            
        await self.change_presence(activity=activity)
        
        # Log failed cogs if any
        if self.failed_cogs:
            logger.warning(f"Failed to load {len(self.failed_cogs)} cogs:")
            for cog in self.failed_cogs:
                logger.warning(f"  - {cog}")
                
        # Log startup complete
        logger.info("Bot is fully ready")

async def main():
    """Main entry point"""
    try:
        # Create bot instance
        bot = Bot()
        
        # Get token from environment variables
        token = os.environ.get("DISCORD_TOKEN")
        
        if not token:
            logger.error("DISCORD_TOKEN is not set in environment variables")
            return
            
        # Start the bot
        await bot.start(token)
    except KeyboardInterrupt:
        logger.info("Bot stopped by keyboard interrupt")
    except Exception as e:
        logger.error(f"Error running bot: {e}")
    finally:
        # Make sure asyncio tasks are properly closed
        for task in asyncio.all_tasks():
            task.cancel()
            
        # Close the event loop
        if asyncio.get_event_loop().is_running():
            asyncio.get_event_loop().stop()
        
        logger.info("Bot shutdown complete")

if __name__ == "__main__":
    """Run the bot"""
    asyncio.run(main())