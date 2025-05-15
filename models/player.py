"""
Player Model

This module provides models for the Player and PlayerLink collections.
"""

import logging
from typing import Dict, Any, Optional, List, Union, ClassVar
from datetime import datetime

from models.base_model import BaseModel

# Set up logging
logger = logging.getLogger(__name__)

class Player(BaseModel):
    """Player model for in-game players"""
    
    # Collection name
    collection_name: ClassVar[str] = "players"
    
    def __init__(self, **kwargs):
        """
        Initialize a player
        
        Args:
            **kwargs: Field values for the player
        """
        # Initialize base fields
        super().__init__(**kwargs)
        
        # Set default values for player fields
        self.name = kwargs.get('name', '')
        self.server_id = kwargs.get('server_id', None)
        self.level = kwargs.get('level', 1)
        self.experience = kwargs.get('experience', 0)
        self.kills = kwargs.get('kills', 0)
        self.deaths = kwargs.get('deaths', 0)
        self.bounties_claimed = kwargs.get('bounties_claimed', 0)
        self.bounty_value = kwargs.get('bounty_value', 0)
        self.last_seen = kwargs.get('last_seen', self.created_at)
        self.stats = kwargs.get('stats', {})
        
    @property
    def kd_ratio(self) -> float:
        """Calculate the kill/death ratio"""
        if self.deaths == 0:
            return self.kills
        return self.kills / self.deaths
        
    @classmethod
    async def get_by_name(cls, name: str, server_id: Optional[str] = None) -> Optional['Player']:
        """
        Get a player by name
        
        Args:
            name: Player name
            server_id: Optional server ID
            
        Returns:
            Player or None if not found
        """
        # Build query
        query = {'name': name}
        if server_id:
            query['server_id'] = server_id
            
        return await cls.find_one(query)
        
    @classmethod
    async def get_top_players(cls, field: str = 'kills', 
                           limit: int = 10, 
                           server_id: Optional[str] = None) -> List['Player']:
        """
        Get top players by a specific field
        
        Args:
            field: Field to sort by
            limit: Maximum number of players to return
            server_id: Optional server ID
            
        Returns:
            List of players
        """
        # Build query
        query = {}
        if server_id:
            query['server_id'] = server_id
            
        # Sort by field descending
        sort = [(field, -1)]
        
        return await cls.find_many(query, limit=limit, sort=sort)
        
    @classmethod
    async def update_stats(cls, name: str, server_id: Optional[str], 
                         stats_updates: Dict[str, Any]) -> Optional['Player']:
        """
        Update player statistics
        
        Args:
            name: Player name
            server_id: Optional server ID
            stats_updates: Stats to update
            
        Returns:
            Updated player or None if player not found
        """
        # Get player
        player = await cls.get_by_name(name, server_id)
        
        if not player:
            # Create new player
            player = await cls.create(
                name=name,
                server_id=server_id
            )
            
        if not player:
            return None
            
        # Update stats
        for key, value in stats_updates.items():
            if hasattr(player, key):
                # For existing stats, add the value
                current_value = getattr(player, key)
                if isinstance(current_value, (int, float)) and isinstance(value, (int, float)):
                    setattr(player, key, current_value + value)
                else:
                    setattr(player, key, value)
            elif key in player.stats:
                # For stats in the stats dictionary, add the value
                current_value = player.stats[key]
                if isinstance(current_value, (int, float)) and isinstance(value, (int, float)):
                    player.stats[key] = current_value + value
                else:
                    player.stats[key] = value
            else:
                # For new stats, set the value in the stats dictionary
                player.stats[key] = value
                
        # Update last seen timestamp
        player.last_seen = datetime.utcnow()
        
        # Save player
        await player.save()
        
        return player

class PlayerLink(BaseModel):
    """Link between Discord users and in-game players"""
    
    # Collection name
    collection_name: ClassVar[str] = "player_links"
    
    def __init__(self, **kwargs):
        """
        Initialize a player link
        
        Args:
            **kwargs: Field values for the player link
        """
        # Initialize base fields
        super().__init__(**kwargs)
        
        # Set player link fields
        self.discord_id = kwargs.get('discord_id', None)
        self.player_id = kwargs.get('player_id', None)
        self.guild_id = kwargs.get('guild_id', None)
        self.server_id = kwargs.get('server_id', None)
        self.verified = kwargs.get('verified', False)
        self.verification_code = kwargs.get('verification_code', None)
        
    @classmethod
    async def get_by_discord_id(cls, discord_id: Union[str, int], 
                              guild_id: Optional[Union[str, int]] = None) -> Optional['PlayerLink']:
        """
        Get a player link by Discord ID
        
        Args:
            discord_id: Discord user ID
            guild_id: Optional Discord guild ID
            
        Returns:
            PlayerLink or None if not found
        """
        # Convert IDs to strings
        discord_id = str(discord_id)
        guild_id = str(guild_id) if guild_id else None
        
        # Build query
        query = {'discord_id': discord_id}
        if guild_id:
            query['guild_id'] = guild_id
            
        return await cls.find_one(query)
        
    @classmethod
    async def get_by_player_id(cls, player_id: str, 
                             guild_id: Optional[Union[str, int]] = None) -> Optional['PlayerLink']:
        """
        Get a player link by player ID
        
        Args:
            player_id: Player ID
            guild_id: Optional Discord guild ID
            
        Returns:
            PlayerLink or None if not found
        """
        # Convert guild ID to string
        guild_id = str(guild_id) if guild_id else None
        
        # Build query
        query = {'player_id': player_id}
        if guild_id:
            query['guild_id'] = guild_id
            
        return await cls.find_one(query)
        
    @classmethod
    async def link_player(cls, discord_id: Union[str, int], guild_id: Union[str, int],
                        player_id: str, server_id: Optional[str] = None,
                        verified: bool = False) -> 'PlayerLink':
        """
        Link a Discord user to an in-game player
        
        Args:
            discord_id: Discord user ID
            guild_id: Discord guild ID
            player_id: Player ID
            server_id: Optional server ID
            verified: Whether the link is verified
            
        Returns:
            PlayerLink instance
        """
        # Convert IDs to strings
        discord_id = str(discord_id)
        guild_id = str(guild_id)
        
        # Find existing link
        link = await cls.get_by_discord_id(discord_id, guild_id)
        
        if link:
            # Update existing link
            link.player_id = player_id
            link.server_id = server_id
            link.verified = verified
            await link.save()
            return link
        
        # Create new link
        link = await cls.create(
            discord_id=discord_id,
            guild_id=guild_id,
            player_id=player_id,
            server_id=server_id,
            verified=verified
        )
        
        return link
        
    @classmethod
    async def verify_link(cls, discord_id: Union[str, int], 
                        guild_id: Union[str, int],
                        verification_code: str) -> Optional['PlayerLink']:
        """
        Verify a player link with a verification code
        
        Args:
            discord_id: Discord user ID
            guild_id: Discord guild ID
            verification_code: Verification code
            
        Returns:
            PlayerLink if verified, None otherwise
        """
        # Convert IDs to strings
        discord_id = str(discord_id)
        guild_id = str(guild_id)
        
        # Find existing link
        link = await cls.get_by_discord_id(discord_id, guild_id)
        
        if not link or not link.verification_code or link.verification_code != verification_code:
            return None
        
        # Update verification status
        link.verified = True
        link.verification_code = None
        await link.save()
        
        return link