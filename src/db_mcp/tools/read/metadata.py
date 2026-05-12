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

def search_schema(keyword: str, schema: Optional[str] = None) -> Dict[str, Any]:
    """Search for tables or columns containing a specific keyword."""
    if not db_manager.engine:
        return {"error": "Database not connected"}
        
    keyword_lower = keyword.lower()
    matches = {}
    try:
        tables = db_manager.inspector.get_table_names(schema=schema)
        for table in tables:
            # If the table name matches, include it entirely
            if keyword_lower in table.lower():
                columns = db_manager.inspector.get_columns(table, schema=schema)
                matches[table] = {
                    "columns": [{"name": col["name"], "type": str(col["type"])} for col in columns]
                }
            else:
                # Otherwise, check if any columns match
                columns = db_manager.inspector.get_columns(table, schema=schema)
                matching_cols = [col for col in columns if keyword_lower in col["name"].lower()]
                if matching_cols:
                    matches[table] = {
                        "columns": [{"name": col["name"], "type": str(col["type"])} for col in matching_cols]
                    }
        return matches
    except SQLAlchemyError as e:
        logger.error(f"Error searching schema: {e}")
        return {"error": str(e)}

def get_table_ddl(table: str, schema: Optional[str] = None) -> str:
    """Generate CREATE TABLE DDL for a specific table."""
    if not db_manager.engine:
        return "Database not connected"
        
    from sqlalchemy.schema import CreateTable, Table, MetaData
    try:
        metadata = MetaData(schema=schema)
        tbl = Table(table, metadata, autoload_with=db_manager.engine)
        ddl = str(CreateTable(tbl).compile(db_manager.engine))
        return ddl
    except SQLAlchemyError as e:
        logger.error(f"Error getting DDL for table {table}: {e}")
        return f"Error: {e}"

def profile_column(table: str, column: str, schema: Optional[str] = None) -> Dict[str, Any]:
    """Profile a column to get min, max, null percentage, and distinct count."""
    if not db_manager.engine:
        return {"error": "Database not connected"}
    
    from sqlalchemy import Table, MetaData, select, func
    try:
        metadata = MetaData(schema=schema)
        tbl = Table(table, metadata, autoload_with=db_manager.engine)
        
        if column not in tbl.columns:
            return {"error": f"Column '{column}' not found in table '{table}'"}
            
        col = tbl.columns[column]
        
        # Build query safely using SQLAlchemy Core to prevent injection
        total_rows_query = select(func.count()).select_from(tbl)
        stats_query = select(
            func.min(col).label("min_val"),
            func.max(col).label("max_val"),
            func.count(func.distinct(col)).label("distinct_count"),
            func.count(col).label("non_null_count")
        ).select_from(tbl)
        
        with db_manager.engine.connect() as conn:
            total_rows = conn.execute(total_rows_query).scalar()
            
            if not total_rows or total_rows == 0:
                return {"status": "Empty table", "total_rows": 0}
                
            stats = conn.execute(stats_query).fetchone()
            
            null_count = total_rows - stats.non_null_count
            null_percentage = round((null_count / total_rows) * 100, 2)
            
            return {
                "table": table,
                "column": column,
                "total_rows": total_rows,
                "min": str(stats.min_val),
                "max": str(stats.max_val),
                "distinct_count": stats.distinct_count,
                "null_count": null_count,
                "null_percentage": f"{null_percentage}%"
            }
    except SQLAlchemyError as e:
        logger.error(f"Error profiling column {table}.{column}: {e}")
        return {"error": str(e)}
