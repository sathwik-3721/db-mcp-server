import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Centralized configuration for the database MCP server."""
    
    DATABASE_URL = os.environ.get("DATABASE_URL")
    
    # Security Policies
    ALLOW_MUTATIONS = os.environ.get("ALLOW_MUTATIONS", "false").lower() == "true"
    
    # Pagination / Context limits
    try:
        MAX_ROWS = int(os.environ.get("MAX_ROWS", "100"))
    except ValueError:
        MAX_ROWS = 100

    # Logging
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
    LOG_FORMAT = os.environ.get("LOG_FORMAT", "text").lower()

config = Config()
