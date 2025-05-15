"""
Error Telemetry Module

This module provides error tracking and reporting functionality for the Discord bot.
"""

import datetime
import logging
import os
import uuid
import traceback
from typing import Dict, Any, Optional, Union

logger = logging.getLogger(__name__)

class ErrorTelemetry:
    """
    Error tracking and reporting system for the Discord bot.
    
    This class provides methods to report and log errors,
    generating unique error IDs for tracking purposes.
    """
    
    def __init__(self, bot, collection_name: str = "errors"):
        """
        Initialize the error telemetry system.
        
        Args:
            bot: The Discord bot instance
            collection_name: MongoDB collection name for storing errors
        """
        self.bot = bot
        self.collection_name = collection_name
        self.db_enabled = hasattr(bot, 'db') and bot.db is not None
        
        # Create error log directory if it doesn't exist
        self.log_dir = os.path.join(os.getcwd(), "error_logs")
        if not os.path.exists(self.log_dir):
            try:
                os.makedirs(self.log_dir)
            except Exception as e:
                logger.error(f"Failed to create error log directory: {e}")
    
    async def report_error(self, error_type: str, error_message: str, 
                          traceback_str: str, command_name: str = "",
                          guild_id: Optional[int] = None, channel_id: Optional[int] = None, 
                          user_id: Optional[int] = None, additional_data: Optional[Dict[str, Any]] = None) -> str:
        """
        Report an error and generate a unique error ID.
        
        Args:
            error_type: Type of the error
            error_message: Error message
            traceback_str: Error traceback as string
            command_name: Name of the command that caused the error
            guild_id: ID of the guild where the error occurred
            channel_id: ID of the channel where the error occurred
            user_id: ID of the user who triggered the error
            additional_data: Any additional data to store with the error
            
        Returns:
            Unique error ID
        """
        # Generate a unique error ID
        error_id = str(uuid.uuid4())[:8]
        
        # Create error data dictionary
        timestamp = datetime.datetime.utcnow()
        error_data = {
            "error_id": error_id,
            "timestamp": timestamp,
            "error_type": error_type,
            "error_message": error_message,
            "traceback": traceback_str,
            "command_name": command_name,
            "guild_id": guild_id,
            "channel_id": channel_id,
            "user_id": user_id,
        }
        
        # Add additional data if provided
        if additional_data:
            error_data.update(additional_data)
        
        # Log to database if enabled
        if self.db_enabled:
            try:
                await self.bot.db[self.collection_name].insert_one(error_data)
                logger.info(f"Error {error_id} logged to database")
            except Exception as e:
                logger.error(f"Failed to log error to database: {e}")
        
        # Always log to file as backup
        self._log_to_file(error_id, error_data, traceback_str)
        
        return error_id
    
    def _log_to_file(self, error_id: str, error_data: Dict[str, Any], traceback_str: str) -> None:
        """
        Log error to a file.
        
        Args:
            error_id: Unique error ID
            error_data: Error data dictionary
            traceback_str: Error traceback as string
        """
        try:
            # Create a file with the error ID
            timestamp_str = error_data["timestamp"].strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp_str}_{error_id}.log"
            file_path = os.path.join(self.log_dir, filename)
            
            with open(file_path, 'w') as f:
                # Write error details
                f.write(f"Error ID: {error_id}\n")
                f.write(f"Timestamp: {error_data['timestamp']}\n")
                f.write(f"Error Type: {error_data['error_type']}\n")
                f.write(f"Error Message: {error_data['error_message']}\n")
                f.write(f"Command: {error_data['command_name']}\n")
                f.write(f"Guild ID: {error_data['guild_id']}\n")
                f.write(f"Channel ID: {error_data['channel_id']}\n")
                f.write(f"User ID: {error_data['user_id']}\n")
                f.write("\n--- Traceback ---\n")
                f.write(traceback_str)
            
            logger.info(f"Error {error_id} logged to file: {file_path}")
        except Exception as e:
            logger.error(f"Failed to log error to file: {e}")
    
    async def get_error(self, error_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve error information by ID from the database.
        
        Args:
            error_id: Unique error ID
            
        Returns:
            Error data dictionary or None if not found
        """
        if not self.db_enabled:
            return None
            
        try:
            error_data = await self.bot.db[self.collection_name].find_one({"error_id": error_id})
            return error_data
        except Exception as e:
            logger.error(f"Failed to retrieve error {error_id}: {e}")
            return None

def get_error_telemetry(bot) -> ErrorTelemetry:
    """
    Create and return an ErrorTelemetry instance.
    
    Args:
        bot: The Discord bot instance
        
    Returns:
        ErrorTelemetry instance
    """
    return ErrorTelemetry(bot)