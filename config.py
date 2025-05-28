import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional

class Config:
    """Configuration manager for the SecondBrain bot."""
    
    def __init__(self):
        self.env = os.getenv("ENV", "development")
        self._load_environment()
        
    def _load_environment(self):
        """Load environment variables based on the current environment."""
        if self.env == "development":
            # Load from .env file in development
            env_path = Path(__file__).parent / ".env"
            if not env_path.exists():
                raise FileNotFoundError(
                    "No .env file found. Please create one with your development credentials."
                )
            load_dotenv(env_path)
    
    @property
    def telegram_token(self) -> str:
        """Get the Telegram bot token."""
        token = os.getenv("TG_TOKEN")
        if not token:
            raise ValueError("TG_TOKEN environment variable is not set")
        return token
    
    @property
    def telegram_chat_id(self) -> Optional[str]:
        """Get the Telegram chat ID."""
        return os.getenv("TG_CHAT_ID")
    
    @property
    def notion_token(self) -> str:
        """Get the Notion integration token."""
        token = os.getenv("NOTION_TOKEN")
        if not token:
            raise ValueError("NOTION_TOKEN environment variable is not set")
        return token
    
    @property
    def notion_database_id(self) -> str:
        """Get the Notion database ID."""
        db_id = os.getenv("NOTION_DB_ID")
        if not db_id:
            raise ValueError("NOTION_DB_ID environment variable is not set")
        return db_id
    
    @property
    def openai_api_key(self) -> str:
        """Get the OpenAI API key."""
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        return key
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.env == "production"

# Create a global config instance
config = Config() 