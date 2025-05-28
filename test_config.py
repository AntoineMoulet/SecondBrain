import os
from config import Config
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_config():
    """Test the configuration system."""
    # Create a new config instance
    config = Config()
    
    # Log the current environment
    logger.info(f"Current environment: {config.env}")
    logger.info(f"Is production: {config.is_production}")
    
    # Test all configuration values
    logger.info("\nConfiguration values:")
    logger.info(f"Telegram Token: {config.telegram_token[:10]}...")
    logger.info(f"Telegram Chat ID: {config.telegram_chat_id}")
    logger.info(f"Notion Token: {config.notion_token[:10]}...")
    logger.info(f"Notion Database ID: {config.notion_database_id}")

if __name__ == "__main__":
    test_config() 