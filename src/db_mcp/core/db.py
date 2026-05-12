from typing import Dict, Any
import socket
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import SQLAlchemyError

from src.db_mcp.core.config import config
from src.db_mcp.core.logger import setup_logger

logger = setup_logger(__name__)

class DatabaseManager:
    """Core Database Management."""
    def __init__(self):
        if not config.DATABASE_URL:
            logger.error("DATABASE_URL is missing in environment or config.")
            self.engine = None
            return
            
        try:
            self.engine = create_engine(config.DATABASE_URL)
            self.inspector = inspect(self.engine)
            logger.info(f"Successfully connected. Dialect: {self.engine.dialect.name}")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            self.engine = None

    def check_connection(self) -> Dict[str, str]:
        """Health check for database connectivity."""
        if not self.engine:
            return {"status": "unhealthy", "error": "Engine not initialized."}
            
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return {"status": "healthy"}
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}

    def get_database_info(self) -> Dict[str, Any]:
        """Returns server/database metadata."""
        if not self.engine:
            return {"error": "Engine not initialized."}
            
        info = {
            "dialect": self.engine.dialect.name,
            "machine_name": socket.gethostname()
        }
        
        # Try to get version based on dialect
        try:
            with self.engine.connect() as conn:
                if "postgresql" in info["dialect"]:
                    info["version"] = conn.execute(text("SELECT version()")).scalar()
                elif "mssql" in info["dialect"]:
                    info["version"] = conn.execute(text("SELECT @@VERSION")).scalar()
                elif "mysql" in info["dialect"]:
                    info["version"] = conn.execute(text("SELECT VERSION()")).scalar()
                elif "sqlite" in info["dialect"]:
                    info["version"] = conn.execute(text("SELECT sqlite_version()")).scalar()
                elif "snowflake" in info["dialect"]:
                    info["version"] = conn.execute(text("SELECT CURRENT_VERSION()")).scalar()
                elif "hana" in info["dialect"]:
                    info["version"] = conn.execute(text("SELECT VERSION FROM SYS.M_DATABASE")).scalar()
                elif "bigquery" in info["dialect"]:
                    info["version"] = "Google BigQuery (Managed Service)"
                else:
                    # Generic fallback: try to use SQLAlchemy's internal dialect detection
                    version_info = getattr(self.engine.dialect, "server_version_info", None)
                    info["version"] = str(version_info) if version_info else "Unknown"
        except Exception as e:
            logger.warning(f"Could not fetch database version: {e}")
            info["version"] = "Unknown"
            
        return info

    def execute_raw_sql(self, query: str) -> Dict[str, Any]:
        """Executes a raw SQL statement and returns the result."""
        import time
        if not self.engine:
            return {"error": "Engine not initialized."}
            
        try:
            start_time = time.time()
            with self.engine.connect() as conn:
                # Apply an execution timeout to prevent rogue queries from hanging the server
                # Note: Support for this varies by dialect, but it's safe to pass generically
                conn = conn.execution_options(timeout=30)
                
                result = conn.execute(text(query))
                
                if not result.returns_rows:
                    conn.commit()
                    duration = round(time.time() - start_time, 3)
                    logger.info(f"Write Query executed in {duration}s. Rows affected: {result.rowcount}")
                    return {
                        "success": True, 
                        "message": f"Query executed successfully. Rows affected: {result.rowcount}",
                        "execution_time_seconds": duration
                    }

                rows = result.fetchmany(config.MAX_ROWS + 1)
                columns = list(result.keys())
                
                data = [dict(zip(columns, row)) for row in rows[:config.MAX_ROWS]]
                
                duration = round(time.time() - start_time, 3)
                logger.info(f"Read Query executed in {duration}s. Rows returned: {len(data)}")
                
                response = {
                    "columns": columns,
                    "rows": data,
                    "row_count": len(data),
                    "execution_time_seconds": duration
                }
                
                if len(rows) > config.MAX_ROWS:
                    response["warning"] = f"Result truncated. Query returned more than {config.MAX_ROWS} rows."
                    
                return response
                
        except SQLAlchemyError as e:
            logger.error(f"Error executing query: {e}")
            return {"error": str(e)}

# Singleton instance
db_manager = DatabaseManager()
