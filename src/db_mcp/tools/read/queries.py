import re
from typing import Dict, Any
from src.db_mcp.core.db import db_manager
from src.db_mcp.core.logger import setup_logger

logger = setup_logger(__name__)

def is_read_only(query: str) -> bool:
    """Basic validation to ensure query does not contain mutation keywords."""
    dangerous_keywords = [
        r"\bINSERT\b", r"\bUPDATE\b", r"\bDELETE\b", r"\bDROP\b", 
        r"\bTRUNCATE\b", r"\bALTER\b", r"\bGRANT\b", r"\bREVOKE\b",
        r"\bREPLACE\b", r"\bCREATE\b"
    ]
    
    upper_query = query.upper()
    for kw in dangerous_keywords:
        if re.search(kw, upper_query):
            return False
    return True

def execute_read_query(query: str) -> Dict[str, Any]:
    """Executes a strictly read-only SQL query against the database."""
    if not is_read_only(query):
        logger.warning(f"Blocked potential mutation in read-only route: {query}")
        return {"error": "Query blocked: Mutation keywords detected."}
        
    return db_manager.execute_raw_sql(query)
