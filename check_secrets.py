"""
Check Secrets Module

This module checks if all required environment secrets are set.
"""

import os
import logging
from typing import List, Dict, Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Define required secrets
REQUIRED_SECRETS = [
    "DISCORD_TOKEN",  # Discord bot token
]

# Define optional secrets with descriptions
OPTIONAL_SECRETS = {
    "MONGODB_URI": "MongoDB connection string (for database functionality)",
    "COMMAND_PREFIX": "Custom command prefix (defaults to !)",
}

def check_secrets() -> bool:
    """
    Check if all required secrets are set.
    
    Returns:
        Whether all required secrets are set
    """
    # Check required secrets
    missing_secrets = []
    for secret in REQUIRED_SECRETS:
        if not os.getenv(secret):
            missing_secrets.append(secret)
    
    if missing_secrets:
        logger.error("Missing required secrets:")
        for secret in missing_secrets:
            logger.error(f"  - {secret}")
        
        logger.info("Please add these secrets to your Replit environment variables.")
        logger.info("Go to 'Secrets' tab and add them as key-value pairs.")
        return False
    
    # Check optional secrets
    missing_optional = []
    for secret, description in OPTIONAL_SECRETS.items():
        if not os.getenv(secret):
            missing_optional.append((secret, description))
    
    if missing_optional:
        logger.warning("Optional secrets not set:")
        for secret, description in missing_optional:
            logger.warning(f"  - {secret}: {description}")
    
    return True

def get_missing_secrets() -> List[str]:
    """
    Get a list of missing required secrets.
    
    Returns:
        List of missing required secret names
    """
    missing = []
    for secret in REQUIRED_SECRETS:
        if not os.getenv(secret):
            missing.append(secret)
    return missing

def get_secret_status() -> Dict[str, bool]:
    """
    Get the status of all secrets.
    
    Returns:
        Dictionary mapping secret names to whether they are set
    """
    status = {}
    
    # Check required secrets
    for secret in REQUIRED_SECRETS:
        status[secret] = bool(os.getenv(secret))
    
    # Check optional secrets
    for secret in OPTIONAL_SECRETS:
        status[secret] = bool(os.getenv(secret))
    
    return status

if __name__ == "__main__":
    # Run the check
    if check_secrets():
        logger.info("All required secrets are set.")
    else:
        logger.error("Missing required secrets. Please set them before running the bot.")