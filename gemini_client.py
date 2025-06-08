import google.generativeai as genai
from typing import Dict, List, Any, Optional
import logging
import json
from config import settings
import time
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class QueryResult:
    """Result of SQL query generation."""
    sql_query: str
    explanation: str
    confidence: float
    
class GeminiSQLGenerator:
    """Generates SQL queries using Google's Gemini AI."""
    
    def __init__(self):
        """Initialize Gemini client with API key."""
        self.model = None
        self._initialized = False
    
    def _ensure_initialized(self):
        """Ensure the Gemini client is initialized."""
        if self._initialized:
            return
            
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        genai.configure(api_key=settings.gemini_api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        self._initialized = True
    
    def generate_sql_query(self, natural_query: str, schema_info: str, query_type: str = "SELECT") -> Dict[str, Any]:
        """Generate SQL query from natural language using Gemini."""
        start_time = time.time()
        logger.info(f"🚀 Starting SQL query generation for: '{natural_query}'")
        
        # Ensure initialized
        self._ensure_initialized()
        
        # Format schema for prompt (handle both string and dict inputs)
        schema_start = time.time()
        if isinstance(schema_info, str):
            formatted_schema = schema_info
            # Count tables in string format
            table_count = len([line for line in schema_info.split('\n') if line.startswith('TABLE:')])
        else:
            formatted_schema = self._format_schema_for_prompt(schema_info)
            table_count = len(schema_info)
        
        logger.info(f"📋 Schema formatted in {time.time() - schema_start:.2f}s ({table_count} tables)")
        
        # Log detailed schema tables being sent to AI
        tables_in_schema = []
        for line in formatted_schema.split('\n'):
            if line.startswith('TABLE:') or line.startswith('Table:'):
                table_name = line.replace('TABLE:', '').replace('Table:', '').strip()
                tables_in_schema.append(table_name)
        
        logger.info(f"📋 Tables being sent to Gemini AI:")
        for i, table in enumerate(tables_in_schema, 1):
            logger.info(f"  {i}. {table}")
        
        # Create prompt
        prompt_start = time.time()
        prompt = self._create_sql_generation_prompt(natural_query, formatted_schema, query_type)
        logger.info(f"📝 Prompt created in {time.time() - prompt_start:.2f}s ({len(prompt)} chars)")
        
        # Log a sample of what table info looks like in the prompt
        logger.debug(f"🔍 Sample schema in prompt (first 500 chars): {formatted_schema[:500]}...")
        
        try:
            # Call Gemini API
            api_start = time.time()
            logger.info(f"🤖 Calling Gemini API...")
            
            response = self.model.generate_content(prompt)
            
            logger.info(f"🎯 Gemini API responded in {time.time() - api_start:.2f}s")
            
            # Parse response
            parse_start = time.time()
            result = self._parse_gemini_response(response.text)
            logger.info(f"🔍 Response parsed in {time.time() - parse_start:.2f}s")
            
            # Log what tables Gemini actually used in the SQL
            sql_query = result.get("sql_query", "")
            used_tables = []
            for table in tables_in_schema:
                if table.lower() in sql_query.lower():
                    used_tables.append(table)
            
            logger.info(f"🎯 Tables Gemini chose to use in SQL:")
            for i, table in enumerate(used_tables, 1):
                logger.info(f"  {i}. {table}")
            
            if not used_tables:
                logger.warning(f"⚠️ No recognized tables found in generated SQL!")
            
            # Log detailed analysis of table choices
            if "dl_buyer" in sql_query.lower() and "dl_buyer_address" in sql_query.lower():
                logger.info(f"🔍 ANALYSIS: Both dl_buyer and dl_buyer_address found in query")
            elif "dl_buyer_address" in sql_query.lower():
                logger.info(f"🔍 ANALYSIS: Only dl_buyer_address found in query")
                logger.info(f"🔍 ANALYSIS: Checking if dl_buyer was in available tables: {'dl_buyer' in [t.lower() for t in tables_in_schema]}")
            elif "dl_buyer" in sql_query.lower():
                logger.info(f"🔍 ANALYSIS: Only dl_buyer found in query (this is expected)")
            
            logger.info(f"✅ SQL generation completed in {time.time() - start_time:.2f}s total")
            return result
                
        except Exception as e:
            error_msg = f"Failed to generate SQL: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return {
                "sql_query": "-- Error: Could not generate SQL query",
                "explanation": error_msg,
                "confidence": 0.0,
                "tables_used": []
            }
    
    def _format_schema_for_prompt(self, schema: Dict[str, List[Dict[str, Any]]]) -> str:
        """Format database schema for inclusion in the prompt."""
        schema_text = "Database Schema:\n"
        
        for table_name, columns in schema.items():
            schema_text += f"\nTable: {table_name}\n"
            schema_text += "Columns:\n"
            
            for column in columns:
                column_info = f"  - {column['column_name']} ({column['data_type']}"
                if column['character_maximum_length']:
                    column_info += f"({column['character_maximum_length']})"
                column_info += f", nullable: {column['is_nullable']}"
                if column['column_default']:
                    column_info += f", default: {column['column_default']}"
                column_info += ")\n"
                schema_text += column_info
        
        return schema_text
    
    def _create_sql_generation_prompt(
        self, 
        user_query: str, 
        schema_context: str, 
        query_type: str
    ) -> str:
        """Create a comprehensive prompt for SQL generation."""
        
        prompt = f"""
You are an expert SQL query generator. Your task is to convert natural language requests into accurate PostgreSQL queries.

{schema_context}

User Request: "{user_query}"
Expected Query Type: {query_type}

Instructions:
1. Generate a PostgreSQL-compatible SQL query that fulfills the user's request
2. Use only the tables and columns from the provided schema
3. Follow PostgreSQL syntax and best practices
4. Include appropriate WHERE clauses, JOINs, and other necessary SQL constructs
5. For SELECT queries, choose appropriate columns based on the request
6. Ensure the query is safe and doesn't include any harmful operations

Please respond with a JSON object containing:
{{
    "sql_query": "The generated SQL query",
    "explanation": "Brief explanation of what the query does",
    "confidence": 0.95,
    "tables_used": ["list", "of", "table", "names", "used"]
}}

Only return the JSON object, no additional text.
"""
        
        return prompt
    
    def _parse_gemini_response(self, response_text: str) -> Dict[str, Any]:
        """Parse Gemini's response and extract structured data."""
        try:
            # Try to extract JSON from the response
            response_text = response_text.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith("```json"):
                response_text = response_text.replace("```json", "").replace("```", "").strip()
            elif response_text.startswith("```"):
                response_text = response_text.replace("```", "").strip()
            
            # Parse JSON
            result = json.loads(response_text)
            
            # Validate required fields
            required_fields = ["sql_query", "explanation", "confidence", "tables_used"]
            for field in required_fields:
                if field not in result:
                    result[field] = "" if field in ["sql_query", "explanation"] else []
            
            return result
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON response: {e}")
            
            # Fallback: try to extract SQL query manually
            lines = response_text.split('\n')
            sql_query = ""
            
            for line in lines:
                if any(keyword in line.upper() for keyword in ['SELECT', 'INSERT', 'UPDATE', 'DELETE']):
                    sql_query = line.strip()
                    break
            
            return {
                "sql_query": sql_query,
                "explanation": "Parsed from non-JSON response",
                "confidence": 0.5,
                "tables_used": []
            }
    
    def validate_query_safety(self, sql_query: str) -> bool:
        """Basic validation to ensure query safety."""
        dangerous_keywords = [
            'DROP', 'TRUNCATE', 'DELETE FROM', 'ALTER', 'CREATE', 
            'GRANT', 'REVOKE', '--', ';--', '/*', '*/'
        ]
        
        query_upper = sql_query.upper()
        for keyword in dangerous_keywords:
            if keyword in query_upper:
                logger.warning(f"Potentially dangerous keyword found: {keyword}")
                return False
        
        return True

# Global Gemini client instance
gemini_client = GeminiSQLGenerator() 