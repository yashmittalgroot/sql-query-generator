from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import asyncio
import logging

from query_generator import SQLQueryGenerator, QueryExecutionMode, QueryResult
from database import db_manager
from config import settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="SQL Query Generator API",
    description="Generate SQL queries from natural language using Gemini AI",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class QueryRequest(BaseModel):
    query: str = Field(..., description="Natural language query")
    query_type: str = Field("SELECT", description="SQL query type")
    execution_mode: str = Field("direct", description="Execution mode")
    execute: bool = Field(True, description="Whether to execute the query")

class QueryResponse(BaseModel):
    success: bool
    sql_query: str
    explanation: str
    data: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None
    row_count: Optional[int] = None
    confidence: float = 0.0

# Global query generators
generators = {
    "direct": SQLQueryGenerator(QueryExecutionMode.DIRECT),
    "mcp": SQLQueryGenerator(QueryExecutionMode.MCP),
    "dry-run": SQLQueryGenerator(QueryExecutionMode.DRY_RUN)
}

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "SQL Query Generator API",
        "version": "1.0.0",
        "endpoints": {
            "generate": "/generate",
            "schema": "/schema",
            "health": "/health"
        }
    }

@app.post("/generate", response_model=QueryResponse)
async def generate_query(request: QueryRequest):
    """Generate and optionally execute SQL query."""
    try:
        # Validate execution mode
        if request.execution_mode not in generators:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid execution mode. Choose from: {list(generators.keys())}"
            )
        
        # Get appropriate generator
        generator = generators[request.execution_mode]
        
        # Generate query
        result = await generator.generate_and_execute_query(
            request.query,
            request.query_type,
            request.execute
        )
        
        # Convert to response model
        return QueryResponse(
            success=result.success,
            sql_query=result.sql_query,
            explanation=result.explanation,
            data=result.data,
            error=result.error,
            execution_time=result.execution_time,
            row_count=result.row_count,
            confidence=result.confidence
        )
        
    except Exception as e:
        logger.error(f"Error generating query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/schema")
async def get_schema(table: Optional[str] = None):
    """Get database schema information."""
    try:
        if table:
            schema_info = db_manager.get_table_schema(table)
            if not schema_info:
                raise HTTPException(status_code=404, detail=f"Table '{table}' not found")
            return {"table": table, "columns": schema_info}
        else:
            full_schema = db_manager.get_database_schema()
            return {"schema": full_schema}
            
    except Exception as e:
        logger.error(f"Error retrieving schema: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    db_status = db_manager.test_connection()
    
    return {
        "status": "healthy" if db_status else "unhealthy",
        "database": "connected" if db_status else "disconnected",
        "gemini_api": "configured" if settings.gemini_api_key else "not configured"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 