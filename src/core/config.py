import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Centralized configuration for the database MCP server."""
    
    DATABASE_URL = os.environ.get("DATABASE_URL")
    
    # If ALLOW_MUTATIONS is not explicitly "true", default to False for safety
    ALLOW_MUTATIONS = os.environ.get("ALLOW_MUTATIONS", "false").lower() == "true"
    
    # Limit row count to prevent LLM context overflow
    try:
        MAX_ROWS = int(os.environ.get("MAX_ROWS", "100"))
    except ValueError:
        MAX_ROWS = 100

config = Config()
