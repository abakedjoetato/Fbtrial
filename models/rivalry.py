"""
Rivalry Model

This module provides the Rivalry model for tracking player rivalries.
"""

import logging
from typing import Dict, Any, Optional, List, Union, ClassVar, Tuple
from datetime import datetime

from models.base_model import BaseModel
from models.player import Player

# Set up logging
logger = logging.getLogger(__name__)

class Rivalry(BaseModel):
    """Model for player rivalries"""
    
    # Collection name
    collection_name: ClassVar[str] = "rivalries"
    
    def __init__(self, **kwargs):
        """
        Initialize a rivalry
        
        Args:
            **kwargs: Field values for the rivalry
        """
        # Initialize base fields
        super().__init__(**kwargs)
        
        # Set rivalry fields
        self.player1_id = kwargs.get('player1_id', None)
        self.player2_id = kwargs.get('player2_id', None)
        self.server_id = kwargs.get('server_id', None)
        self.player1_kills = kwargs.get('player1_kills', 0)
        self.player2_kills = kwargs.get('player2_kills', 0)
        self.last_kill_timestamp = kwargs.get('last_kill_timestamp', None)
        self.last_kill_by = kwargs.get('last_kill_by', None)
        self.intensity_score = kwargs.get('intensity_score', 0)
        
    @property
    def total_kills(self) -> int:
        """Get the total number of kills in the rivalry"""
        return self.player1_kills + self.player2_kills
        
    @property
    def is_active(self) -> bool:
        """Check if the rivalry is active (has recent activity)"""
        if not self.last_kill_timestamp:
            return False
            
        # Check if last kill was within 30 days
        now = datetime.utcnow()
        diff = now - self.last_kill_timestamp
        return diff.days < 30
        
    @classmethod
    async def get_by_players(cls, player1_id: str, player2_id: str, 
                          server_id: Optional[str] = None) -> Optional['Rivalry']:
        """
        Get a rivalry between two players
        
        Args:
            player1_id: First player ID
            player2_id: Second player ID
            server_id: Optional server ID
            
        Returns:
            Rivalry or None if not found
        """
        # Build queries (check both directions)
        query1 = {
            'player1_id': player1_id,
            'player2_id': player2_id
        }
        
        query2 = {
            'player1_id': player2_id,
            'player2_id': player1_id
        }
        
        if server_id:
            query1['server_id'] = server_id
            query2['server_id'] = server_id
            
        # Check first direction
        rivalry = await cls.find_one(query1)
        if rivalry:
            return rivalry
            
        # Check second direction
        return await cls.find_one(query2)
        
    @classmethod
    async def get_by_player(cls, player_id: str, 
                         server_id: Optional[str] = None,
                         limit: int = 5) -> List['Rivalry']:
        """
        Get rivalries for a player
        
        Args:
            player_id: Player ID
            server_id: Optional server ID
            limit: Maximum number of rivalries to return
            
        Returns:
            List of rivalries
        """
        # Build query for player as player1
        query1 = {'player1_id': player_id}
        if server_id:
            query1['server_id'] = server_id
            
        # Build query for player as player2
        query2 = {'player2_id': player_id}
        if server_id:
            query2['server_id'] = server_id
            
        # Get rivalries for both queries
        rivalries1 = await cls.find_many(query1, limit=limit, sort=[('intensity_score', -1)])
        rivalries2 = await cls.find_many(query2, limit=limit, sort=[('intensity_score', -1)])
        
        # Combine and sort by intensity
        all_rivalries = rivalries1 + rivalries2
        all_rivalries.sort(key=lambda r: r.intensity_score, reverse=True)
        
        # Return limited number
        return all_rivalries[:limit]
        
    @classmethod
    async def get_top_rivalries(cls, server_id: Optional[str] = None, 
                             limit: int = 10) -> List['Rivalry']:
        """
        Get top rivalries by intensity
        
        Args:
            server_id: Optional server ID
            limit: Maximum number of rivalries to return
            
        Returns:
            List of rivalries
        """
        # Build query
        query = {}
        if server_id:
            query['server_id'] = server_id
            
        # Get rivalries sorted by intensity
        return await cls.find_many(query, limit=limit, sort=[('intensity_score', -1)])
        
    @classmethod
    async def record_kill(cls, killer_id: str, victim_id: str,
                       server_id: Optional[str] = None) -> 'Rivalry':
        """
        Record a kill between players
        
        Args:
            killer_id: Killer player ID
            victim_id: Victim player ID
            server_id: Optional server ID
            
        Returns:
            Updated or created rivalry
        """
        # Get existing rivalry
        rivalry = await cls.get_by_players(killer_id, victim_id, server_id)
        
        # If no rivalry exists, create one
        if not rivalry:
            rivalry = await cls.create(
                player1_id=killer_id,
                player2_id=victim_id,
                server_id=server_id,
                player1_kills=1,
                player2_kills=0,
                last_kill_timestamp=datetime.utcnow(),
                last_kill_by=killer_id
            )
            rivalry.intensity_score = cls.calculate_intensity(1, 0)
            await rivalry.save()
            return rivalry
            
        # Update the rivalry based on the killer
        now = datetime.utcnow()
        
        if rivalry.player1_id == killer_id:
            rivalry.player1_kills += 1
            rivalry.last_kill_by = killer_id
        else:
            rivalry.player2_kills += 1
            rivalry.last_kill_by = killer_id
            
        rivalry.last_kill_timestamp = now
        
        # Update the intensity score
        rivalry.intensity_score = cls.calculate_intensity(
            rivalry.player1_kills, 
            rivalry.player2_kills
        )
        
        # Save changes
        await rivalry.save()
        
        return rivalry
        
    @staticmethod
    def calculate_intensity(kills1: int, kills2: int) -> float:
        """
        Calculate the intensity score for a rivalry
        
        Args:
            kills1: Number of kills by player 1
            kills2: Number of kills by player 2
            
        Returns:
            Intensity score
        """
        # Base score is the total kills
        total = kills1 + kills2
        
        # Bonus for close competition (smaller difference)
        diff = abs(kills1 - kills2)
        if total == 0:
            balance_factor = 0
        else:
            balance_factor = 1 - (diff / total)
            
        # Bonus for higher kill counts
        magnitude = total * 0.5
        
        # Combine factors
        return total + (balance_factor * magnitude)
        
    async def get_player_names(self) -> Tuple[str, str]:
        """
        Get the names of the players in the rivalry
        
        Returns:
            Tuple of (player1_name, player2_name)
        """
        player1 = await Player.get_by_id(self.player1_id)
        player2 = await Player.get_by_id(self.player2_id)
        
        player1_name = player1.name if player1 else "Unknown Player"
        player2_name = player2.name if player2 else "Unknown Player"
        
        return (player1_name, player2_name)