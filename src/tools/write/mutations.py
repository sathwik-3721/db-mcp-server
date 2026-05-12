from typing import Dict, Any
from src.core.db import db_manager
from src.core.config import config

def execute_write_query(query: str) -> Dict[str, Any]:
    """Executes a mutation query against the database (INSERT, UPDATE, DELETE).
    Strictly blocked unless ALLOW_MUTATIONS=true in the environment.
    """
    if not db_manager:
        return {"error": "Database Manager not initialized."}
        
    if not config.ALLOW_MUTATIONS:
        return {"error": "Mutation blocked. Server is running with ALLOW_MUTATIONS=false."}
        
    return db_manager.execute_raw_sql(query)
