import json
from mcp.server.fastmcp import FastMCP
from typing import Optional

from src.db_mcp.tools.read.metadata import (
    get_database_info as get_db_info,
    list_schemas as list_db_schemas,
    list_tables as list_db_tables,
    schema_discovery as do_schema_discovery,
    check_db_connection as check_conn
)
from src.db_mcp.tools.read.queries import execute_read_query, is_read_only
from src.db_mcp.tools.write.mutations import execute_write_query
from src.db_mcp.core.config import config
from src.db_mcp.core.logger import setup_logger

logger = setup_logger(__name__)

# Initialize FastMCP Server
mcp = FastMCP("db-mcp-server")

@mcp.tool()
def execute_sql(sql: str, format: str = "json") -> str:
    """Execute SELECT queries (or write operations if enabled).
    Input: SQL string.
    Output: JSON string or ASCII table string.
    """
    logger.info(f"Executing SQL: {sql}")
    
    if is_read_only(sql):
        result = execute_read_query(sql)
    else:
        result = execute_write_query(sql)
        
    if "error" in result:
        return json.dumps(result, indent=2)
        
    if format.lower() == "table" and "rows" in result:
        # Simple ASCII table formatter for the agent
        rows = result["rows"]
        if not rows:
            return "No rows returned."
        
        columns = result.get("columns", list(rows[0].keys()))
        col_widths = {col: max(len(str(col)), max((len(str(row.get(col, ""))) for row in rows), default=0)) for col in columns}
        
        header = " | ".join(str(col).ljust(col_widths[col]) for col in columns)
        separator = "-+-".join("-" * col_widths[col] for col in columns)
        
        lines = [header, separator]
        for row in rows:
            lines.append(" | ".join(str(row.get(col, "")).ljust(col_widths[col]) for col in columns))
            
        return "\n".join(lines)
        
    # Default to JSON
    return json.dumps(result, default=str, indent=2)

@mcp.tool()
def list_schemas() -> str:
    """List all database schemas."""
    logger.info("Listing schemas")
    return json.dumps(list_db_schemas(), indent=2)

@mcp.tool()
def list_tables(schema: Optional[str] = None, limit: int = 200) -> str:
    """List tables with optional schema filter."""
    logger.info(f"Listing tables (schema={schema}, limit={limit})")
    return json.dumps(list_db_tables(schema=schema, limit=limit), indent=2)

@mcp.tool()
def schema_discovery(schema: Optional[str] = None) -> str:
    """Get full schema metadata (tables, columns, types) for a schema."""
    logger.info(f"Discovering schema metadata (schema={schema})")
    return json.dumps(do_schema_discovery(schema=schema), indent=2)

@mcp.tool()
def get_database_info() -> str:
    """Get server/database metadata."""
    logger.info("Getting database info")
    return json.dumps(get_db_info(), indent=2)

@mcp.tool()
def get_policy_info() -> str:
    """Get current security policy settings."""
    logger.info("Getting policy info")
    policy = {
        "ALLOW_MUTATIONS": config.ALLOW_MUTATIONS,
        "MAX_ROWS_RETURNED": config.MAX_ROWS,
        "LOG_LEVEL": config.LOG_LEVEL
    }
    return json.dumps(policy, indent=2)

@mcp.tool()
def check_db_connection() -> str:
    """Health check for database connectivity."""
    logger.info("Checking database connection")
    return json.dumps(check_conn(), indent=2)
