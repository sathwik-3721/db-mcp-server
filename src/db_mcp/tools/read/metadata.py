from typing import List, Dict, Any, Optional
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from src.db_mcp.core.db import db_manager
from src.db_mcp.core.logger import setup_logger

logger = setup_logger(__name__)

def get_database_info() -> Dict[str, Any]:
    """Returns server/database metadata (dialect, version, machine name)."""
    return db_manager.get_database_info()

def check_db_connection() -> Dict[str, str]:
    """Health check for database connectivity."""
    return db_manager.check_connection()

def list_schemas() -> List[str]:
    """List all database schemas."""
    if not db_manager.engine:
        return []
    try:
        return db_manager.inspector.get_schema_names()
    except NotImplementedError:
        # Some dialects (like SQLite) don't support schemas in the same way
        return ["default"]
    except SQLAlchemyError as e:
        logger.error(f"Error listing schemas: {e}")
        return []

def list_tables(schema: Optional[str] = None, limit: int = 200) -> List[str]:
    """List tables with optional schema filter."""
    if not db_manager.engine:
        return []
    try:
        tables = db_manager.inspector.get_table_names(schema=schema)
        return tables[:limit]
    except SQLAlchemyError as e:
        logger.error(f"Error listing tables: {e}")
        return []

def schema_discovery(schema: Optional[str] = None) -> Dict[str, Any]:
    """Get full schema metadata (tables, columns, types) for a given schema."""
    if not db_manager.engine:
        return {"error": "Database not connected"}
        
    discovery = {}
    try:
        tables = db_manager.inspector.get_table_names(schema=schema)
        for table in tables:
            columns = db_manager.inspector.get_columns(table, schema=schema)
            pk = db_manager.inspector.get_pk_constraint(table, schema=schema)
            fks = db_manager.inspector.get_foreign_keys(table, schema=schema)
            
            discovery[table] = {
                "columns": [{"name": col["name"], "type": str(col["type"]), "nullable": col["nullable"]} for col in columns],
                "primary_key": pk.get("constrained_columns", []),
                "foreign_keys": fks
            }
        return discovery
    except SQLAlchemyError as e:
        logger.error(f"Error during schema discovery: {e}")
        return {"error": str(e)}
