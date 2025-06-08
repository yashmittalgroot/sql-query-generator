import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from typing import List, Dict, Any, Optional
import logging
from config import settings
import re

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages PostgreSQL database connections and operations."""
    
    def __init__(self):
        self.connection_params = {
            'host': settings.db_host,
            'port': settings.db_port,
            'database': settings.db_name,
            'user': settings.db_user,
            'password': settings.db_password
        }
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = None
        try:
            conn = psycopg2.connect(**self.connection_params)
            yield conn
        except psycopg2.Error as e:
            logger.error(f"Database connection error: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Execute a SELECT query and return results as list of dictionaries."""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query, params)
                    results = cursor.fetchall()
                    return [dict(row) for row in results]
        except psycopg2.Error as e:
            logger.error(f"Query execution error: {e}")
            raise
    
    def execute_non_query(self, query: str, params: Optional[tuple] = None) -> int:
        """Execute INSERT, UPDATE, DELETE queries and return affected rows count."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
                    conn.commit()
                    return cursor.rowcount
        except psycopg2.Error as e:
            logger.error(f"Non-query execution error: {e}")
            raise
    
    def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """Get schema information for a specific table."""
        query = """
        SELECT 
            column_name,
            data_type,
            is_nullable,
            column_default,
            character_maximum_length
        FROM information_schema.columns 
        WHERE table_name = %s 
        ORDER BY ordinal_position;
        """
        return self.execute_query(query, (table_name,))
    
    def get_all_tables(self) -> List[str]:
        """Get list of all tables in the database."""
        query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name;
        """
        results = self.execute_query(query)
        return [row['table_name'] for row in results]
    
    def get_relevant_tables(self, user_query: str = "", table_prefix: str = "dl_", max_tables: int = 20) -> List[str]:
        """Get tables that are relevant to the user query using AI-powered selection."""
        # Get all tables with the specified prefix
        all_tables = self.get_all_tables()
        prefixed_tables = [table for table in all_tables if table.startswith(table_prefix)]
        
        logger.info(f"📊 Found {len(prefixed_tables)} tables with prefix '{table_prefix}' (out of {len(all_tables)} total)")
        logger.debug(f"🔍 All {table_prefix} tables: {prefixed_tables}")
        
        if not user_query:
            # If no query provided, return first N prefixed tables
            return prefixed_tables[:max_tables]
        
        if len(prefixed_tables) <= max_tables:
            # If we have fewer tables than the limit, return all
            logger.info(f"🎯 Returning all {len(prefixed_tables)} prefixed tables (within limit)")
            return prefixed_tables
        
        # Use AI to select the most relevant tables
        logger.info(f"🤖 Using AI to select {max_tables} most relevant tables from {len(prefixed_tables)} candidates")
        return self._ai_select_relevant_tables(user_query, prefixed_tables, max_tables)
    
    def _ai_select_relevant_tables(self, user_query: str, available_tables: List[str], max_tables: int) -> List[str]:
        """Use Gemini AI to select the most relevant tables for the user query."""
        from gemini_client import gemini_client
        import time
        
        start_time = time.time()
        
        # Create a prompt for table selection
        tables_list = "\n".join([f"- {table}" for table in available_tables])
        
        prompt = f"""
You are a database expert helping to select the most relevant tables for a SQL query.

USER QUERY: "{user_query}"

AVAILABLE TABLES:
{tables_list}

Please analyze the user's request and select the {max_tables} most relevant tables that would be needed to fulfill this query.

Consider:
1. What data entities are mentioned in the query (companies, payments, users, etc.)
2. What operations are requested (joins, aggregations, filtering)
3. Which tables likely contain the required columns
4. Primary tables vs supporting/lookup tables

Respond with a JSON object containing:
{{
    "selected_tables": ["table1", "table2", "table3"],
    "reasoning": {{
        "table1": "Why this table is essential",
        "table2": "Why this table is needed",
        "table3": "Why this table is relevant"
    }},
    "confidence": 0.95
}}

Only return the JSON object, no additional text.
"""
        
        try:
            # Ensure Gemini is initialized
            gemini_client._ensure_initialized()
            
            logger.info(f"🤖 Calling Gemini for table selection...")
            response = gemini_client.model.generate_content(prompt)
            
            # Parse the response
            response_text = response.text.strip()
            if response_text.startswith("```json"):
                response_text = response_text.replace("```json", "").replace("```", "").strip()
            elif response_text.startswith("```"):
                response_text = response_text.replace("```", "").strip()
            
            import json
            result = json.loads(response_text)
            
            selected_tables = result.get("selected_tables", [])
            reasoning = result.get("reasoning", {})
            confidence = result.get("confidence", 0.0)
            
            # Validate that selected tables exist in available tables
            valid_tables = [t for t in selected_tables if t in available_tables]
            
            if len(valid_tables) < max_tables and len(available_tables) > len(valid_tables):
                # Add some additional tables if AI didn't select enough
                remaining = [t for t in available_tables if t not in valid_tables]
                needed = max_tables - len(valid_tables)
                valid_tables.extend(remaining[:needed])
                logger.info(f"📝 Added {needed} additional tables to reach {max_tables} limit")
            
            # Log the AI's reasoning
            logger.info(f"🧠 AI Table Selection Results (confidence: {confidence:.1%}):")
            for i, table in enumerate(valid_tables[:max_tables], 1):
                reason = reasoning.get(table, "Selected by AI")
                logger.info(f"  {i}. {table} - {reason}")
            
            ai_time = time.time() - start_time
            logger.info(f"✅ AI table selection completed in {ai_time:.2f}s")
            
            return valid_tables[:max_tables]
            
        except Exception as e:
            logger.error(f"❌ AI table selection failed: {e}")
            logger.info(f"🔄 Falling back to first {max_tables} tables")
            return available_tables[:max_tables]
    
    def get_smart_database_schema(self, user_query: str = "", table_prefix: str = "dl_", max_tables: int = 20) -> Dict[str, List[Dict[str, Any]]]:
        """Get database schema for tables relevant to the user query."""
        import time
        start_time = time.time()
        logger.info(f"🧠 Starting smart schema retrieval for query: '{user_query}' with prefix '{table_prefix}'")
        
        # Get relevant tables based on query and prefix
        relevant_tables = self.get_relevant_tables(user_query, table_prefix, max_tables)
        
        if not relevant_tables:
            logger.warning(f"⚠️ No tables found with prefix '{table_prefix}'")
            return {}
        
        # Get schema for relevant tables only
        schema_start = time.time()
        schema = self._get_bulk_table_schema(relevant_tables)
        schema_time = time.time() - schema_start
        
        total_time = time.time() - start_time
        logger.info(f"✅ Smart schema retrieval completed: {len(schema)} relevant tables in {total_time:.2f}s")
        
        return schema
    
    def get_database_schema(self, max_tables: int = 50) -> Dict[str, List[Dict[str, Any]]]:
        """Get complete database schema with optimizations for large databases."""
        import time
        start_time = time.time()
        logger.info(f"📊 Starting optimized schema retrieval (max {max_tables} tables)...")
        
        # Get all tables first
        tables = self.get_all_tables()
        logger.info(f"📋 Found {len(tables)} total tables")
        
        # Limit tables for performance with large databases
        if len(tables) > max_tables:
            logger.warning(f"⚠️ Large database detected ({len(tables)} tables). Limiting to {max_tables} tables for performance.")
            tables = tables[:max_tables]
        
        # Get schema for all tables in a single optimized query
        schema_start = time.time()
        schema = self._get_bulk_table_schema(tables)
        schema_time = time.time() - schema_start
        
        total_time = time.time() - start_time
        logger.info(f"✅ Schema retrieval completed: {len(schema)} tables in {total_time:.2f}s")
        
        return schema
    
    def _get_bulk_table_schema(self, table_names: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """Get schema information for multiple tables in a single query."""
        if not table_names:
            return {}
        
        # Create a single query to get all table schemas at once
        placeholders = ','.join(['%s'] * len(table_names))
        query = f"""
        SELECT 
            table_name,
            column_name,
            data_type,
            is_nullable,
            column_default,
            character_maximum_length,
            ordinal_position
        FROM information_schema.columns 
        WHERE table_name IN ({placeholders})
        AND table_schema = 'public'
        ORDER BY table_name, ordinal_position;
        """
        
        logger.info(f"🔍 Executing bulk schema query for {len(table_names)} tables...")
        results = self.execute_query(query, tuple(table_names))
        
        # Group results by table name
        schema = {}
        for row in results:
            table_name = row['table_name']
            if table_name not in schema:
                schema[table_name] = []
            
            # Remove table_name and ordinal_position from the column info
            column_info = {k: v for k, v in row.items() 
                          if k not in ['table_name', 'ordinal_position']}
            schema[table_name].append(column_info)
        
        # Ensure all requested tables are in the result (even if empty)
        for table_name in table_names:
            if table_name not in schema:
                schema[table_name] = []
        
        logger.info(f"📋 Bulk schema query returned {len(results)} columns across {len(schema)} tables")
        return schema
    
    def get_database_schema_full(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get complete database schema for ALL tables (use with caution on large DBs)."""
        tables = self.get_all_tables()
        return self._get_bulk_table_schema(tables)
    
    def test_connection(self) -> bool:
        """Test database connection."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

# Global database manager instance
db_manager = DatabaseManager() 