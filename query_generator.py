import asyncio
import logging
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
import sqlparse

from database import db_manager
from gemini_client import gemini_client
from mcp_client import mcp_manager
from config import settings

logger = logging.getLogger(__name__)

class QueryExecutionMode(Enum):
    """Execution modes for queries."""
    DIRECT = "direct"  # Execute directly via psycopg2
    MCP = "mcp"       # Execute via MCP server
    DRY_RUN = "dry_run"  # Just generate, don't execute

@dataclass
class QueryResult:
    """Result of a query generation and execution."""
    success: bool
    sql_query: str
    explanation: str
    data: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None
    row_count: Optional[int] = None
    confidence: float = 0.0
    tables_used: List[str] = None

class SQLQueryGenerator:
    """Main class for generating and executing SQL queries."""
    
    def __init__(self, execution_mode: QueryExecutionMode = QueryExecutionMode.DIRECT):
        self.execution_mode = execution_mode
        self._schema_cache: Optional[Dict[str, Any]] = None
        self._schema_cache_timestamp = 0
    
    async def generate_and_execute_query(
        self, 
        user_input: str, 
        query_type: str = "SELECT",
        execute: bool = True
    ) -> QueryResult:
        """
        Generate SQL query from natural language and optionally execute it.
        
        Args:
            user_input: Natural language description of the query
            query_type: Type of SQL query (SELECT, INSERT, UPDATE, DELETE)
            execute: Whether to execute the generated query
            
        Returns:
            QueryResult containing the generated query and execution results
        """
        import time
        start_time = time.time()
        logger.info(f"🔥 Starting query generation pipeline for: '{user_input}'")
        
        try:
            # Get database schema
            schema_start = time.time()
            logger.info("📊 Retrieving database schema...")
            schema = await self._get_database_schema(user_input)
            schema_time = time.time() - schema_start
            
            if not schema:
                logger.error(f"❌ Schema retrieval failed after {schema_time:.2f}s")
                return QueryResult(
                    success=False,
                    sql_query="",
                    explanation="Failed to retrieve database schema",
                    error="Schema retrieval failed"
                )
            
            logger.info(f"📋 Schema retrieved in {schema_time:.2f}s ({len(schema)} tables)")
            
            # Generate SQL query using Gemini
            gemini_start = time.time()
            logger.info("🤖 Calling Gemini for SQL generation...")
            query_info = gemini_client.generate_sql_query(
                user_input, schema, query_type
            )
            gemini_time = time.time() - gemini_start
            logger.info(f"🎯 Gemini completed in {gemini_time:.2f}s")
            
            if "error" in query_info:
                logger.error(f"❌ Gemini generation failed: {query_info['error']}")
                return QueryResult(
                    success=False,
                    sql_query="",
                    explanation="Failed to generate query",
                    error=query_info["error"]
                )
            
            sql_query = query_info["sql_query"]
            
            # Validate query safety
            safety_start = time.time()
            if not gemini_client.validate_query_safety(sql_query):
                logger.warning(f"🛡️ Query failed safety validation after {time.time() - safety_start:.2f}s")
                return QueryResult(
                    success=False,
                    sql_query=sql_query,
                    explanation="Query failed safety validation",
                    error="Potentially unsafe query detected"
                )
            logger.info(f"🛡️ Query safety validated in {time.time() - safety_start:.2f}s")
            
            # Format the SQL query
            format_start = time.time()
            formatted_query = self._format_sql_query(sql_query)
            logger.info(f"✨ Query formatted in {time.time() - format_start:.2f}s")
            
            result = QueryResult(
                success=True,
                sql_query=formatted_query,
                explanation=query_info.get("explanation", ""),
                confidence=query_info.get("confidence", 0.0),
                tables_used=query_info.get("tables_used", [])
            )
            
            # Execute query if requested and not in dry run mode
            if execute and self.execution_mode != QueryExecutionMode.DRY_RUN:
                exec_start = time.time()
                logger.info(f"🚀 Executing query in {self.execution_mode.value} mode...")
                execution_result = await self._execute_query(formatted_query, query_type)
                exec_time = time.time() - exec_start
                logger.info(f"⚡ Query executed in {exec_time:.2f}s")
                
                result.data = execution_result.get("data")
                result.execution_time = execution_result.get("execution_time")
                result.row_count = execution_result.get("row_count")
                
                if execution_result.get("error"):
                    result.error = execution_result["error"]
                    result.success = False
            
            total_time = time.time() - start_time
            logger.info(f"🎉 Complete pipeline finished in {total_time:.2f}s")
            return result
            
        except Exception as e:
            total_time = time.time() - start_time
            logger.error(f"❌ Pipeline error after {total_time:.2f}s: {e}")
            return QueryResult(
                success=False,
                sql_query="",
                explanation="Unexpected error occurred",
                error=str(e)
            )
    
    async def _get_database_schema(self, user_query: str = "") -> Optional[Dict[str, Any]]:
        """Get database schema with caching and smart filtering."""
        import time
        current_time = time.time()
        
        # Use cached schema if it's less than configured timeout
        cache_timeout = settings.schema_cache_timeout
        if (self._schema_cache and 
            current_time - self._schema_cache_timestamp < cache_timeout):
            logger.info(f"📋 Using cached schema (less than {cache_timeout/60:.1f} minutes old)")
            return self._schema_cache
        
        try:
            if self.execution_mode == QueryExecutionMode.MCP:
                # Try to get schema via MCP first
                mcp_start = time.time()
                logger.info("🔗 Attempting schema retrieval via MCP...")
                schema = await mcp_manager.get_schema()
                if schema:
                    mcp_time = time.time() - mcp_start
                    logger.info(f"🔗 MCP schema retrieved in {mcp_time:.2f}s")
                    self._schema_cache = schema
                    self._schema_cache_timestamp = current_time
                    return schema
                else:
                    logger.warning(f"⚠️ MCP schema retrieval failed after {time.time() - mcp_start:.2f}s")
            
            # Fallback to direct database connection
            db_start = time.time()
            logger.info("🗄️ Testing database connection...")
            if db_manager.test_connection():
                logger.info(f"✅ Database connection successful in {time.time() - db_start:.2f}s")
                
                schema_start = time.time()
                logger.info(f"🧠 Using smart schema retrieval for query: '{user_query}'")
                schema = db_manager.get_smart_database_schema(
                    user_query=user_query, 
                    table_prefix="dl_", 
                    max_tables=20
                )
                schema_time = time.time() - schema_start
                logger.info(f"📋 Smart schema retrieved: {len(schema)} tables in {schema_time:.2f}s")
                
                self._schema_cache = schema
                self._schema_cache_timestamp = current_time
                return schema
            else:
                logger.error(f"❌ Database connection failed after {time.time() - db_start:.2f}s")
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting database schema: {e}")
            return None
    
    async def _execute_query(
        self, 
        sql_query: str, 
        query_type: str
    ) -> Dict[str, Any]:
        """Execute SQL query based on the execution mode."""
        import time
        
        start_time = time.time()
        
        try:
            if self.execution_mode == QueryExecutionMode.MCP:
                # Execute via MCP server
                data = await mcp_manager.execute_query(sql_query)
                execution_time = time.time() - start_time
                
                return {
                    "data": data,
                    "execution_time": execution_time,
                    "row_count": len(data) if data else 0
                }
            
            elif self.execution_mode == QueryExecutionMode.DIRECT:
                # Execute directly via psycopg2
                if query_type.upper() == "SELECT":
                    data = db_manager.execute_query(sql_query)
                    execution_time = time.time() - start_time
                    
                    return {
                        "data": data,
                        "execution_time": execution_time,
                        "row_count": len(data)
                    }
                else:
                    # For non-SELECT queries
                    row_count = db_manager.execute_non_query(sql_query)
                    execution_time = time.time() - start_time
                    
                    return {
                        "data": None,
                        "execution_time": execution_time,
                        "row_count": row_count
                    }
            
            return {"error": "Invalid execution mode"}
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Query execution error: {e}")
            return {
                "error": str(e),
                "execution_time": execution_time
            }
    
    def _format_sql_query(self, sql_query: str) -> str:
        """Format SQL query for better readability."""
        try:
            return sqlparse.format(
                sql_query, 
                reindent=True, 
                keyword_case='upper',
                identifier_case='lower'
            )
        except:
            return sql_query
    
    def set_execution_mode(self, mode: QueryExecutionMode):
        """Set the execution mode for queries."""
        self.execution_mode = mode
        logger.info(f"Execution mode set to: {mode.value}")
    
    def clear_schema_cache(self):
        """Clear the cached database schema."""
        self._schema_cache = None
        self._schema_cache_timestamp = 0
        logger.info("Schema cache cleared")

# Global query generator instances for different modes
query_generator_direct = SQLQueryGenerator(QueryExecutionMode.DIRECT)
query_generator_mcp = SQLQueryGenerator(QueryExecutionMode.MCP)
query_generator_dry_run = SQLQueryGenerator(QueryExecutionMode.DRY_RUN) 