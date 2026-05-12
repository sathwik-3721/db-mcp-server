from typing import List, Dict, Any
from sqlalchemy.exc import SQLAlchemyError
from src.core.db import db_manager
import logging

logger = logging.getLogger(__name__)

def get_dialect_info() -> str:
    """Returns the type of database connected (e.g., postgresql, mssql, mysql)."""
    if not db_manager:
        return "Error: Database Manager not initialized."
    return db_manager.engine.dialect.name

def list_tables() -> List[str]:
    """Returns a list of all accessible tables in the database."""
    if not db_manager:
        return ["Error: Database Manager not initialized."]
    try:
        return db_manager.inspector.get_table_names()
    except SQLAlchemyError as e:
        logger.error(f"Error listing tables: {e}")
        return []

def get_table_schema(table_name: str) -> Dict[str, Any]:
    """Returns the schema (columns, data types, keys) for a specific table."""
    if not db_manager:
        return {"error": "Database Manager not initialized."}
    try:
        if not db_manager.inspector.has_table(table_name):
            return {"error": f"Table '{table_name}' not found."}
            
        columns = db_manager.inspector.get_columns(table_name)
        pk = db_manager.inspector.get_pk_constraint(table_name)
        fks = db_manager.inspector.get_foreign_keys(table_name)
        
        schema = {
            "columns": [{"name": col["name"], "type": str(col["type"]), "nullable": col["nullable"]} for col in columns],
            "primary_key": pk.get("constrained_columns", []),
            "foreign_keys": fks
        }
        return schema
    except SQLAlchemyError as e:
        logger.error(f"Error getting schema for {table_name}: {e}")
        return {"error": str(e)}
