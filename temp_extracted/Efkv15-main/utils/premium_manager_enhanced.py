"""
Premium Manager Enhanced Module

This module provides enhanced premium feature management for the Discord bot.
"""

import logging
import asyncio
import datetime
from typing import Dict, Any, List, Optional, Union, Set

logger = logging.getLogger(__name__)

# Premium tiers
TIER_FREE = 0
TIER_BASIC = 1
TIER_STANDARD = 2
TIER_PRO = 3

# Cache expiration time (in seconds)
CACHE_EXPIRATION = 300  # 5 minutes

class PremiumManager:
    """
    Enhanced premium feature manager for the Discord bot.
    
    This class manages premium features and permissions,
    with support for different tiers and feature flags.
    """
    
    def __init__(self, db=None, collection_name: str = "premium"):
        """
        Initialize the premium manager.
        
        Args:
            db: MongoDB database instance
            collection_name: Collection name for premium data
        """
        self.db = db
        self.collection_name = collection_name
        self.cache = {}
        self.cache_timestamps = {}
        self.feature_requirements = self._init_feature_requirements()
    
    def _init_feature_requirements(self) -> Dict[str, int]:
        """
        Initialize feature requirements.
        
        Returns:
            Dictionary mapping feature names to required tiers
        """
        return {
            # Basic tier features
            "custom_prefix": TIER_BASIC,
            "reaction_roles": TIER_BASIC,
            "welcome_messages": TIER_BASIC,
            
            # Standard tier features
            "automod": TIER_STANDARD,
            "custom_commands": TIER_STANDARD,
            "logging": TIER_STANDARD,
            
            # Pro tier features
            "advanced_stats": TIER_PRO,
            "auto_roles": TIER_PRO,
            "premium_embeds": TIER_PRO
        }
    
    async def get_guild_tier(self, guild_id: int) -> int:
        """
        Get the premium tier for a guild.
        
        Args:
            guild_id: Discord guild ID
            
        Returns:
            Premium tier (0 = free, 1 = basic, 2 = standard, 3 = pro)
        """
        # Check cache first
        cache_key = f"guild_tier_{guild_id}"
        if cache_key in self.cache:
            # Check if cache is still valid
            timestamp = self.cache_timestamps.get(cache_key, 0)
            if timestamp + CACHE_EXPIRATION > asyncio.get_event_loop().time():
                return self.cache[cache_key]
        
        # Not in cache or cache expired, fetch from database
        if self.db:
            try:
                premium_data = await self.db[self.collection_name].find_one({"guild_id": guild_id})
                
                if premium_data:
                    tier = premium_data.get("tier", TIER_FREE)
                    
                    # Check if premium is expired
                    expiry = premium_data.get("expiry")
                    if expiry and datetime.datetime.utcnow() > expiry:
                        tier = TIER_FREE
                else:
                    tier = TIER_FREE
            except Exception as e:
                logger.error(f"Error fetching premium tier for guild {guild_id}: {e}")
                tier = TIER_FREE
        else:
            # No database, return free tier
            tier = TIER_FREE
        
        # Update cache
        self.cache[cache_key] = tier
        self.cache_timestamps[cache_key] = asyncio.get_event_loop().time()
        
        return tier
    
    async def has_feature(self, guild_id: int, feature: str) -> bool:
        """
        Check if a guild has access to a premium feature.
        
        Args:
            guild_id: Discord guild ID
            feature: Feature name
            
        Returns:
            Whether the guild has access to the feature
        """
        # Check if feature exists
        if feature not in self.feature_requirements:
            logger.warning(f"Unknown feature requested: {feature}")
            return False
        
        # Get guild tier
        tier = await self.get_guild_tier(guild_id)
        
        # Check if tier meets requirements
        required_tier = self.feature_requirements[feature]
        return tier >= required_tier
    
    async def get_available_features(self, guild_id: int) -> List[str]:
        """
        Get a list of available premium features for a guild.
        
        Args:
            guild_id: Discord guild ID
            
        Returns:
            List of available feature names
        """
        tier = await self.get_guild_tier(guild_id)
        
        available = []
        for feature, required_tier in self.feature_requirements.items():
            if tier >= required_tier:
                available.append(feature)
        
        return available
    
    async def set_guild_tier(self, guild_id: int, tier: int, 
                           expiry: Optional[datetime.datetime] = None) -> bool:
        """
        Set the premium tier for a guild.
        
        Args:
            guild_id: Discord guild ID
            tier: Premium tier
            expiry: Expiry date (None for no expiry)
            
        Returns:
            Whether the update was successful
        """
        if not self.db:
            logger.error("Cannot set guild tier: database not available")
            return False
        
        try:
            # Prepare data
            update_data = {
                "tier": tier,
                "updated_at": datetime.datetime.utcnow()
            }
            
            if expiry:
                update_data["expiry"] = expiry
            
            # Update database
            await self.db[self.collection_name].update_one(
                {"guild_id": guild_id},
                {"$set": update_data},
                upsert=True
            )
            
            # Update cache
            cache_key = f"guild_tier_{guild_id}"
            self.cache[cache_key] = tier
            self.cache_timestamps[cache_key] = asyncio.get_event_loop().time()
            
            return True
        except Exception as e:
            logger.error(f"Error setting premium tier for guild {guild_id}: {e}")
            return False
    
    def clear_cache(self, guild_id: Optional[int] = None):
        """
        Clear the premium cache.
        
        Args:
            guild_id: Discord guild ID (None to clear all)
        """
        if guild_id:
            # Clear cache for specific guild
            cache_key = f"guild_tier_{guild_id}"
            if cache_key in self.cache:
                del self.cache[cache_key]
            if cache_key in self.cache_timestamps:
                del self.cache_timestamps[cache_key]
        else:
            # Clear all cache
            self.cache.clear()
            self.cache_timestamps.clear()

def get_premium_manager(db=None) -> PremiumManager:
    """
    Create and return a PremiumManager instance.
    
    Args:
        db: MongoDB database instance
        
    Returns:
        PremiumManager instance
    """
    return PremiumManager(db)