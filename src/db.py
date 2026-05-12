import os
import re
from typing import List, Dict, Any, Optional
from sqlalchemy import create_engine, MetaData, inspect, text
from sqlalchemy.exc import SQLAlchemyError
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.db_url = os.environ.get("DATABASE_URL")
        if not self.db_url:
            raise ValueError("DATABASE_URL environment variable is missing.")
            
        self.allow_mutations = os.environ.get("ALLOW_MUTATIONS", "false").lower() == "true"
        self.max_rows = int(os.environ.get("MAX_ROWS", "100"))
        
        try:
            self.engine = create_engine(self.db_url)
            self.inspector = inspect(self.engine)
            logger.info(f"Successfully connected to database. Dialect: {self.engine.dialect.name}")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    def get_dialect_info(self) -> str:
        """Returns the database dialect to help the LLM generate correct SQL."""
        return self.engine.dialect.name

    def list_tables(self) -> List[str]:
        """Lists all tables in the database."""
        try:
            return self.inspector.get_table_names()
        except SQLAlchemyError as e:
            logger.error(f"Error listing tables: {e}")
            return []

    def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """Returns detailed schema for a table, including columns and foreign keys."""
        try:
            if not self.inspector.has_table(table_name):
                return {"error": f"Table '{table_name}' not found."}
                
            columns = self.inspector.get_columns(table_name)
            pk = self.inspector.get_pk_constraint(table_name)
            fks = self.inspector.get_foreign_keys(table_name)
            
            schema = {
                "columns": [{"name": col["name"], "type": str(col["type"]), "nullable": col["nullable"]} for col in columns],
                "primary_key": pk.get("constrained_columns", []),
                "foreign_keys": fks
            }
            return schema
        except SQLAlchemyError as e:
            logger.error(f"Error getting schema for {table_name}: {e}")
            return {"error": str(e)}

    def is_safe_query(self, query: str) -> tuple[bool, str]:
        """Validates if a query is safe to run when ALLOW_MUTATIONS=false."""
        if self.allow_mutations:
            return True, "Mutations allowed"
            
        # Basic SQL injection/mutation prevention check
        # This checks for starting words or anywhere in the query (simple regex)
        dangerous_keywords = [
            r"\bINSERT\b", r"\bUPDATE\b", r"\bDELETE\b", r"\bDROP\b", 
            r"\bTRUNCATE\b", r"\bALTER\b", r"\bGRANT\b", r"\bREVOKE\b"
        ]
        
        upper_query = query.upper()
        for kw in dangerous_keywords:
            if re.search(kw, upper_query):
                return False, f"Query blocked: contains forbidden keyword {kw.replace(r'\b', '')}. Server is running with ALLOW_MUTATIONS=false."
                
        return True, "Safe"

    def execute_query(self, query: str) -> Dict[str, Any]:
        """Executes a query and returns up to MAX_ROWS."""
        is_safe, msg = self.is_safe_query(query)
        if not is_safe:
            return {"error": msg}

        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(query))
                
                # If it's not a read query (no rows returned), handle safely
                if not result.returns_rows:
                    if self.allow_mutations:
                        conn.commit()
                        return {"success": True, "message": f"Query executed successfully. Rows affected: {result.rowcount}"}
                    return {"success": True, "message": "Query executed, but no rows returned."}

                # Fetch results up to MAX_ROWS + 1 to detect truncation
                rows = result.fetchmany(self.max_rows + 1)
                
                columns = list(result.keys())
                
                # Format to list of dicts
                data = [dict(zip(columns, row)) for row in rows[:self.max_rows]]
                
                response = {
                    "columns": columns,
                    "rows": data,
                    "row_count": len(data)
                }
                
                if len(rows) > self.max_rows:
                    response["warning"] = f"Result truncated. Query returned more than {self.max_rows} rows."
                    
                return response
                
        except SQLAlchemyError as e:
            logger.error(f"Error executing query: {e}")
            return {"error": str(e)}
