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
    def github_token(self) -> str:
        """Get the GitHub token for vault writes."""
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            raise ValueError("GITHUB_TOKEN environment variable is not set")
        return token

    @property
    def github_repo(self) -> str:
        """Get the GitHub repo (owner/repo) for the vault."""
        repo = os.getenv("GITHUB_REPO")
        if not repo:
            raise ValueError("GITHUB_REPO environment variable is not set")
        return repo

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