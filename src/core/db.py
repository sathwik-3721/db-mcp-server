from typing import Dict, Any
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import SQLAlchemyError
import logging
from src.core.config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Core Database Management.
    Does not contain MCP routing logic or explicit read/write checks.
    """
    def __init__(self):
        if not config.DATABASE_URL:
            raise ValueError("DATABASE_URL is missing in environment or config.")
            
        try:
            self.engine = create_engine(config.DATABASE_URL)
            self.inspector = inspect(self.engine)
            logger.info(f"Successfully connected. Dialect: {self.engine.dialect.name}")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    def execute_raw_sql(self, query: str) -> Dict[str, Any]:
        """Executes a raw SQL statement and returns the result."""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(query))
                
                # Handling queries that don't return rows (like INSERT/UPDATE)
                if not result.returns_rows:
                    conn.commit()
                    return {"success": True, "message": f"Query executed successfully. Rows affected: {result.rowcount}"}

                # Handling queries that return rows (like SELECT)
                # We fetch one extra row to detect if truncation is needed based on MAX_ROWS
                rows = result.fetchmany(config.MAX_ROWS + 1)
                columns = list(result.keys())
                
                # Format to list of dicts, truncating to MAX_ROWS
                data = [dict(zip(columns, row)) for row in rows[:config.MAX_ROWS]]
                
                response = {
                    "columns": columns,
                    "rows": data,
                    "row_count": len(data)
                }
                
                if len(rows) > config.MAX_ROWS:
                    response["warning"] = f"Result truncated. Query returned more than {config.MAX_ROWS} rows."
                    
                return response
                
        except SQLAlchemyError as e:
            logger.error(f"Error executing query: {e}")
            return {"error": str(e)}

# Singleton instance
db_manager = None
try:
    db_manager = DatabaseManager()
except Exception:
    pass # Error logged in __init__
