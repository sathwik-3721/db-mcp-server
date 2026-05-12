from mcp.server.fastmcp import FastMCP

# Import CQRS tools
from src.tools.read.metadata import get_dialect_info, list_tables, get_table_schema
from src.tools.read.queries import execute_read_query
from src.tools.write.mutations import execute_write_query
from src.core.config import config

# Initialize FastMCP Server
mcp = FastMCP("db-mcp-server")

# Register Read Tools (Safe)
@mcp.tool()
def dialect_info() -> str:
    """Returns the database dialect (postgresql, mssql, etc)."""
    return get_dialect_info()

@mcp.tool()
def tables() -> list[str]:
    """Returns a list of all accessible tables in the database."""
    return list_tables()

@mcp.tool()
def table_schema(table_name: str) -> dict:
    """Returns the schema (columns, types, foreign keys) for a table."""
    return get_table_schema(table_name)

@mcp.tool()
def read_query(query: str) -> dict:
    """Executes a strictly read-only SQL query."""
    return execute_read_query(query)

# Register Write Tools (Conditionally exposed or always exposed but blocked internally)
@mcp.tool()
def write_query(query: str) -> dict:
    """Executes a mutation query (INSERT, UPDATE, DELETE). 
    Will fail if the server is not configured to allow mutations.
    """
    return execute_write_query(query)
