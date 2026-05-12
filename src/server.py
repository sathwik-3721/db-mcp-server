import os
import argparse
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env if it exists
load_dotenv()

from mcp.server.fastmcp import FastMCP
from db import DatabaseManager

# Initialize FastMCP Server
mcp = FastMCP("db-mcp-server")

# Initialize Database Manager
try:
    db_manager = DatabaseManager()
except Exception as e:
    print(f"Failed to initialize Database Manager: {e}")
    print("Ensure DATABASE_URL is set correctly in your environment or .env file.")
    exit(1)


@mcp.tool()
def get_dialect_info() -> str:
    """Returns the type of database connected (e.g., postgresql, mssql, mysql).
    This helps the agent write the correct SQL syntax for the underlying database.
    """
    return db_manager.get_dialect_info()

@mcp.tool()
def list_tables() -> List[str]:
    """Returns a list of all accessible tables in the database."""
    return db_manager.list_tables()

@mcp.tool()
def get_table_schema(table_name: str) -> Dict[str, Any]:
    """Returns the schema (columns, data types, primary and foreign keys) for a specific table.
    Crucial for understanding how to write correct JOINs and filters for the table.
    """
    return db_manager.get_table_schema(table_name)

@mcp.tool()
def execute_read_query(query: str) -> Dict[str, Any]:
    """Executes a SQL query against the database and returns the results as JSON.
    The query will be blocked if it attempts to mutate data (unless ALLOW_MUTATIONS=true).
    Results are truncated to MAX_ROWS (default 100) to prevent context overflow.
    """
    return db_manager.execute_query(query)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Database Agnostic MCP Server")
    parser.add_argument(
        "--transport", 
        choices=["stdio", "sse"], 
        default="stdio",
        help="Transport protocol to use (default: stdio)"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=8000,
        help="Port to use for SSE transport (default: 8000)"
    )
    
    args = parser.parse_args()
    
    if args.transport == "sse":
        print(f"Starting MCP Server on SSE transport (Port {args.port})...")
        mcp.run(transport="sse", port=args.port)
    else:
        # For stdio, logging should be minimal to avoid corrupting the JSON-RPC stream
        import logging
        logging.getLogger().setLevel(logging.ERROR)
        mcp.run(transport="stdio")
