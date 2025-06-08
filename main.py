#!/usr/bin/env python3
"""
SQL Query Generator - Main Entry Point

This is the main entry point for the SQL Query Generator application.
It provides multiple ways to use the application:
1. Command-line interface (CLI)
2. Web API server
3. Interactive mode

Usage:
    python main.py cli generate "show all users"
    python main.py api
    python main.py interactive
"""

import sys
import asyncio
import logging
from typing import Optional

def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None):
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            *([logging.FileHandler(log_file)] if log_file else [])
        ]
    )

def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print_help()
        return
    
    command = sys.argv[1].lower()
    
    # Setup logging
    setup_logging()
    
    if command == "cli":
        # Run CLI interface
        from cli import cli
        sys.argv = sys.argv[1:]  # Remove 'cli' from argv
        cli()
        
    elif command == "api":
        # Run web API server
        import uvicorn
        from api import app
        
        # Parse additional arguments for API server
        host = "0.0.0.0"
        port = 8000
        
        if len(sys.argv) > 2:
            for i, arg in enumerate(sys.argv[2:], 2):
                if arg.startswith("--host="):
                    host = arg.split("=")[1]
                elif arg.startswith("--port="):
                    port = int(arg.split("=")[1])
        
        print(f"🚀 Starting SQL Query Generator API server on {host}:{port}")
        print(f"📖 API docs available at: http://{host}:{port}/docs")
        
        uvicorn.run(app, host=host, port=port)
        
    elif command == "interactive":
        # Run interactive mode
        from cli import interactive
        interactive.callback()
        
    elif command == "test":
        # Run connection test
        from cli import test_connection
        test_connection.callback()
        
    elif command == "schema":
        # Show database schema
        from cli import schema
        table_name = sys.argv[2] if len(sys.argv) > 2 else None
        schema.callback(table=table_name, output="table")
        
    else:
        print(f"❌ Unknown command: {command}")
        print_help()

def print_help():
    """Print help information."""
    help_text = """
🔍 SQL Query Generator - Convert natural language to SQL queries

Usage:
    python main.py <command> [options]

Commands:
    cli          Use command-line interface
    api          Start web API server
    interactive  Start interactive mode
    test         Test database connection
    schema       Show database schema
    help         Show this help message

Examples:
    # Generate query via CLI
    python main.py cli generate "show all users from users table"
    
    # Start API server
    python main.py api --host=0.0.0.0 --port=8000
    
    # Interactive mode
    python main.py interactive
    
    # Test database connection
    python main.py test
    
    # Show database schema
    python main.py schema
    python main.py schema users  # Show specific table

CLI Options (when using 'cli' command):
    generate <query>     Generate SQL from natural language
    test-connection      Test database connection
    schema              Show database schema
    interactive         Start interactive mode

API Options (when using 'api' command):
    --host=<host>       Host to bind to (default: 0.0.0.0)
    --port=<port>       Port to bind to (default: 8000)

Environment Variables:
    GEMINI_API_KEY      Your Google Gemini API key (required)
    DB_HOST             Database host (default: localhost)
    DB_PORT             Database port (default: 5432)
    DB_NAME             Database name
    DB_USER             Database username
    DB_PASSWORD         Database password
    DEBUG               Enable debug mode (default: True)

For more information, visit: https://github.com/your-repo/sql-query-generator
"""
    print(help_text)

if __name__ == "__main__":
    main()
