import re
from typing import Dict, Any
from src.core.db import db_manager

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
    if not db_manager:
        return {"error": "Database Manager not initialized."}
        
    if not is_read_only(query):
        return {"error": "Query blocked: Mutation keywords detected in read-only operation."}
        
    return db_manager.execute_raw_sql(query)
