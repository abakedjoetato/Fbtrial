"""
Premium Feature Access Module

This module handles access control for premium features of the bot.
"""

import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

# Premium tiers definition
PREMIUM_TIERS = {
    0: "Standard (Free)",
    1: "Bronze",
    2: "Silver",
    3: "Gold",
    4: "Platinum"
}

# Feature tier requirements
FEATURE_TIER_REQUIREMENTS = {
    "advanced_analytics": 1,      # Bronze
    "custom_charts": 2,           # Silver
    "data_export": 1,             # Bronze
    "advanced_moderation": 1,     # Bronze
    "auto_moderation": 2,         # Silver
    "custom_log_filters": 2,      # Silver
    "unlimited_logs": 3,          # Gold
    "custom_commands": 1,         # Bronze
    "custom_embeds": 2,           # Silver
    "scheduled_commands": 3,      # Gold
    "reaction_roles": 1,          # Bronze
    "advanced_roles": 2,          # Silver
    "role_management": 1,         # Bronze
    "auto_roles": 1,              # Bronze
    "welcome_messages": 0,        # Free
    "custom_welcome": 1,          # Bronze
    "leave_messages": 1,          # Bronze
    "member_verification": 2,     # Silver
    "boost_tracking": 1,          # Bronze
    "voice_tracking": 2,          # Silver
    "csv_processor": 2,           # Silver
    "advanced_csv": 3,            # Gold
    "sftp_access": 3,             # Gold
    "database_export": 4,         # Platinum
    "premium_support": 1,         # Bronze
    "priority_support": 3,        # Gold
    "custom_bot_avatar": 4,       # Platinum
}

def get_feature_tier_requirement(feature_name: str) -> int:
    """
    Get the premium tier required for a specific feature.
    
    Args:
        feature_name: The name of the feature to check
        
    Returns:
        The premium tier required (0 = free, 1-4 = premium tiers)
    """
    return FEATURE_TIER_REQUIREMENTS.get(feature_name, 0)
    
async def verify_premium_tier(bot, guild_id: int, tier: int) -> bool:
    """
    Verify that a guild has at least the specified premium tier.
    
    Args:
        bot: The Discord bot instance
        guild_id: The Discord guild ID
        tier: The minimum premium tier required (0-4)
        
    Returns:
        True if the guild has the required premium tier, False otherwise
    """
    # If tier is 0 (free), always return True
    if tier == 0:
        return True
    
    # Check if the guild has premium status
    if hasattr(bot, 'premium_manager') and bot.premium_manager:
        guild_tier = await bot.premium_manager.get_guild_tier(guild_id)
        return guild_tier >= tier
    
    # If no premium manager is available, default to free tier only
    return tier == 0
    
async def verify_premium_feature(bot, guild_id: int, feature_name: str) -> bool:
    """
    Verify that a guild has the required premium tier for a specific feature.
    
    Args:
        bot: The Discord bot instance
        guild_id: The Discord guild ID
        feature_name: The name of the feature to check
        
    Returns:
        True if the guild has the required premium tier, False otherwise
    """
    # Default to True for testing (can be modified based on actual premium logic)
    # In a production environment, this would check against a premium database
    required_tier = get_feature_tier_requirement(feature_name)
    
    if required_tier == 0:
        # Feature is available in the free tier
        return True
    
    # Check if the guild has premium status
    if hasattr(bot, 'premium_manager') and bot.premium_manager:
        return await bot.premium_manager.has_feature(guild_id, feature_name)
    
    # If no premium manager is available, default to free tier only
    return required_tier == 0

# Server limits for premium vs non-premium users
SERVER_LIMITS = {
    "standard": {
        "max_log_entries": 500,
        "max_commands": 10,
        "max_custom_roles": 5,
        "max_auto_roles": 3,
        "max_analytics_days": 7,
        "max_factions": 2,
        "max_bounties": 5,
        "max_economy_items": 10,
        "max_sftp_connections": 1,
        "allowed_csv_formats": ["basic"],
        "max_scheduled_events": 2
    },
    "premium": {
        "max_log_entries": 5000,
        "max_commands": 50,
        "max_custom_roles": 20,
        "max_auto_roles": 10,
        "max_analytics_days": 30,
        "max_factions": 10,
        "max_bounties": 25,
        "max_economy_items": 50,
        "max_sftp_connections": 5,
        "allowed_csv_formats": ["basic", "advanced", "custom"],
        "max_scheduled_events": 10
    }
}

# List of available premium features
PREMIUM_FEATURES = {
    # Analysis features
    "advanced_analytics": "Access to advanced analytics and reporting",
    "custom_charts": "Ability to create custom charts and visualizations",
    "data_export": "Export data in various formats",
    
    # Server management
    "advanced_moderation": "Advanced moderation tools",
    "auto_roles": "Automatic role assignment based on events",
    "custom_welcome": "Customizable welcome messages",
    
    # Economy and game features
    "economy_system": "Complete economy system with currency and shop",
    "faction_wars": "Faction wars system for guild competition",
    "bounty_system": "Bounty system for tracking player achievements",
    
    # Utility features
    "scheduled_events": "Schedule automated events and reminders",
    "custom_commands": "Create custom commands specific to your server",
    "sftp_integration": "SFTP integration for server file management"
}

class PremiumFeatureManager:
    """
    Handles access control for premium features
    """
    def __init__(self, db=None):
        """
        Initialize the premium feature manager
        
        Args:
            db: Database instance for premium status checking
        """
        self.db = db
        
    async def is_premium_guild(self, guild_id: int) -> bool:
        """
        Check if a guild has premium status
        
        Args:
            guild_id: Discord guild ID
            
        Returns:
            Whether the guild has premium status
        """
        if not self.db:
            logger.warning("Database not available for premium status check")
            return False
            
        try:
            premium_collection = self.db.get_collection("premium_guilds")
            result = await premium_collection.find_one({"guild_id": guild_id})
            return bool(result and result.get("active", False))
        except Exception as e:
            logger.error(f"Error checking premium status: {e}")
            return False
            
    async def get_guild_tier(self, guild_id: int) -> int:
        """
        Get the premium tier of a guild
        
        Args:
            guild_id: Discord guild ID
            
        Returns:
            The premium tier (0 = free, 1-4 = premium tiers)
        """
        if not self.db:
            logger.warning("Database not available for premium tier check")
            return 0
            
        try:
            premium_collection = self.db.get_collection("premium_guilds")
            result = await premium_collection.find_one({"guild_id": guild_id})
            
            if not result or not result.get("active", False):
                return 0
                
            # Return the tier from the database, or default to tier 1 for premium guilds
            return result.get("tier", 1)
        except Exception as e:
            logger.error(f"Error checking premium tier: {e}")
            return 0
    
    async def has_feature(self, guild_id: int, feature_name: str) -> bool:
        """
        Check if a guild has access to a specific premium feature
        
        Args:
            guild_id: Discord guild ID
            feature_name: Name of the premium feature to check
            
        Returns:
            Whether the guild has access to the feature
        """
        # First check if the feature exists
        if feature_name not in PREMIUM_FEATURES:
            logger.warning(f"Attempted to check unknown premium feature: {feature_name}")
            return False
        
        # Check if the guild has premium status
        is_premium = await self.is_premium_guild(guild_id)
        if not is_premium:
            return False
            
        # Check if the guild has access to this specific feature
        try:
            premium_collection = self.db.get_collection("premium_features")
            result = await premium_collection.find_one(
                {"guild_id": guild_id, "features": feature_name}
            )
            # If we find a specific record, check it
            if result:
                return result.get("enabled", False)
                
            # Otherwise, all premium guilds have access to basic premium features
            return True
        except Exception as e:
            logger.error(f"Error checking feature access: {e}")
            return False
    
    async def get_guild_features(self, guild_id: int) -> List[str]:
        """
        Get a list of premium features enabled for a guild
        
        Args:
            guild_id: Discord guild ID
            
        Returns:
            List of enabled feature names
        """
        if not await self.is_premium_guild(guild_id):
            return []
            
        try:
            premium_collection = self.db.get_collection("premium_features")
            result = await premium_collection.find_one({"guild_id": guild_id})
            if result and "features" in result:
                return [feature for feature in result["features"] if feature in PREMIUM_FEATURES]
            
            # If no specific features are set, return all basic features
            return list(PREMIUM_FEATURES.keys())
        except Exception as e:
            logger.error(f"Error getting guild features: {e}")
            return []
    
    async def add_premium_guild(self, guild_id: int) -> bool:
        """
        Add a guild to the premium list
        
        Args:
            guild_id: Discord guild ID
            
        Returns:
            Whether the operation was successful
        """
        if not self.db:
            logger.warning("Database not available for premium guild addition")
            return False
            
        try:
            premium_collection = self.db.get_collection("premium_guilds")
            
            # Check if the guild is already premium
            existing = await premium_collection.find_one({"guild_id": guild_id})
            if existing and existing.get("active", False):
                logger.info(f"Guild {guild_id} is already premium")
                return True
                
            # Insert or update guild record
            await premium_collection.update_one(
                {"guild_id": guild_id},
                {"$set": {"active": True}},
                upsert=True
            )
            
            logger.info(f"Added guild {guild_id} to premium list")
            return True
        except Exception as e:
            logger.error(f"Error adding premium guild: {e}")
            return False
    
    async def remove_premium_guild(self, guild_id: int) -> bool:
        """
        Remove a guild from the premium list
        
        Args:
            guild_id: Discord guild ID
            
        Returns:
            Whether the operation was successful
        """
        if not self.db:
            logger.warning("Database not available for premium guild removal")
            return False
            
        try:
            premium_collection = self.db.get_collection("premium_guilds")
            
            # Update guild record
            await premium_collection.update_one(
                {"guild_id": guild_id},
                {"$set": {"active": False}}
            )
            
            logger.info(f"Removed guild {guild_id} from premium list")
            return True
        except Exception as e:
            logger.error(f"Error removing premium guild: {e}")
            return False
            
    async def enable_feature(self, guild_id: int, feature_name: str) -> bool:
        """
        Enable a specific premium feature for a guild
        
        Args:
            guild_id: Discord guild ID
            feature_name: Name of the feature to enable
            
        Returns:
            Whether the operation was successful
        """
        if feature_name not in PREMIUM_FEATURES:
            logger.warning(f"Attempted to enable unknown premium feature: {feature_name}")
            return False
            
        if not await self.is_premium_guild(guild_id):
            logger.warning(f"Attempted to enable premium feature for non-premium guild: {guild_id}")
            return False
            
        try:
            premium_collection = self.db.get_collection("premium_features")
            
            # Enable the feature
            await premium_collection.update_one(
                {"guild_id": guild_id},
                {"$addToSet": {"features": feature_name}},
                upsert=True
            )
            
            logger.info(f"Enabled premium feature {feature_name} for guild {guild_id}")
            return True
        except Exception as e:
            logger.error(f"Error enabling premium feature: {e}")
            return False
    
    async def disable_feature(self, guild_id: int, feature_name: str) -> bool:
        """
        Disable a specific premium feature for a guild
        
        Args:
            guild_id: Discord guild ID
            feature_name: Name of the feature to disable
            
        Returns:
            Whether the operation was successful
        """
        if feature_name not in PREMIUM_FEATURES:
            logger.warning(f"Attempted to disable unknown premium feature: {feature_name}")
            return False
            
        try:
            premium_collection = self.db.get_collection("premium_features")
            
            # Disable the feature
            await premium_collection.update_one(
                {"guild_id": guild_id},
                {"$pull": {"features": feature_name}}
            )
            
            logger.info(f"Disabled premium feature {feature_name} for guild {guild_id}")
            return True
        except Exception as e:
            logger.error(f"Error disabling premium feature: {e}")
            return False

# Helper decorator for premium feature requirements
def requires_premium_feature(feature_name, error_message=None):
    """
    Decorator to check if a guild has access to a premium feature before running a command
    
    Args:
        feature_name: Name of the premium feature to check
        error_message: Optional custom error message to show if feature not available
        
    Returns:
        Command check decorator
    """
    from discord.ext import commands
    
    async def predicate(ctx):
        # Skip check in DMs
        if not ctx.guild:
            return False
            
        # Get premium manager
        premium_manager = getattr(ctx.bot, 'premium_manager', None)
        if not premium_manager:
            if error_message:
                await ctx.send(error_message)
            else:
                await ctx.send(f"The `{feature_name}` feature requires premium access.")
            return False
            
        # Check if feature is available
        has_access = await premium_manager.has_feature(ctx.guild.id, feature_name)
        if not has_access:
            if error_message:
                await ctx.send(error_message)
            else:
                await ctx.send(f"The `{feature_name}` feature requires premium access.")
            return False
            
        return True
        
    return commands.check(predicate)

# For backwards compatibility
PremiumManager = PremiumFeatureManager