from typing import Dict, Any
from src.db_mcp.core.db import db_manager
from src.db_mcp.core.config import config
from src.db_mcp.core.logger import setup_logger

logger = setup_logger(__name__)

def execute_write_query(query: str) -> Dict[str, Any]:
    """Executes a mutation query against the database (INSERT, UPDATE, DELETE).
    Strictly blocked unless ALLOW_MUTATIONS=true in the environment.
    """
    if not config.ALLOW_MUTATIONS:
        logger.warning(f"Blocked mutation query because ALLOW_MUTATIONS is false: {query}")
        return {"error": "Mutation blocked. Server is running with ALLOW_MUTATIONS=false."}
        
    return db_manager.execute_raw_sql(query)
