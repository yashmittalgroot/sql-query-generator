import click
import asyncio
import logging
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from rich.progress import Progress, SpinnerColumn, TextColumn
import json
from typing import Optional

from query_generator import (
    SQLQueryGenerator, 
    QueryExecutionMode, 
    QueryResult
)
from database import db_manager
from config import settings

# Set up logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

console = Console()

@click.group()
@click.version_option(version="1.0.0")
def cli():
    """SQL Query Generator - Convert natural language to SQL queries."""
    pass

@cli.command()
@click.argument('query', type=str)
@click.option('--mode', '-m', 
              type=click.Choice(['direct', 'mcp', 'dry-run']),
              default='direct',
              help='Execution mode for the query')
@click.option('--type', '-t',
              type=click.Choice(['SELECT', 'INSERT', 'UPDATE', 'DELETE']),
              default='SELECT',
              help='Type of SQL query to generate')
@click.option('--no-execute', '-n',
              is_flag=True,
              help='Generate query without executing it')
@click.option('--output', '-o',
              type=click.Choice(['table', 'json', 'sql']),
              default='table',
              help='Output format')
def generate(query: str, mode: str, type: str, no_execute: bool, output: str):
    """Generate and optionally execute SQL query from natural language."""
    
    # Map mode string to enum
    execution_mode = {
        'direct': QueryExecutionMode.DIRECT,
        'mcp': QueryExecutionMode.MCP,
        'dry-run': QueryExecutionMode.DRY_RUN
    }[mode]
    
    # Create query generator with specified mode
    generator = SQLQueryGenerator(execution_mode)
    
    # Show progress
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Generating SQL query...", total=None)
        
        # Run the async function
        result = asyncio.run(generator.generate_and_execute_query(
            query, type, execute=not no_execute
        ))
        
        progress.remove_task(task)
    
    # Display results
    _display_result(result, output)

@cli.command()
def test_connection():
    """Test database connection."""
    console.print("Testing database connection...", style="blue")
    
    if db_manager.test_connection():
        console.print("✅ Database connection successful!", style="green")
        
        # Show database info
        try:
            tables = db_manager.get_all_tables()
            console.print(f"Found {len(tables)} tables in the database:", style="blue")
            
            if tables:
                table = Table(title="Database Tables")
                table.add_column("Table Name", style="cyan")
                
                for table_name in tables[:10]:  # Show first 10 tables
                    table.add_row(table_name)
                
                if len(tables) > 10:
                    table.add_row(f"... and {len(tables) - 10} more")
                
                console.print(table)
        except Exception as e:
            console.print(f"Error getting table list: {e}", style="red")
    else:
        console.print("❌ Database connection failed!", style="red")
        console.print("Please check your database configuration in .env file", style="yellow")

@cli.command()
@click.option('--table', '-t', help='Show schema for specific table')
@click.option('--output', '-o',
              type=click.Choice(['table', 'json']),
              default='table',
              help='Output format')
def schema(table: Optional[str], output: str):
    """Show database schema information."""
    
    try:
        if table:
            # Show specific table schema
            schema_info = db_manager.get_table_schema(table)
            if not schema_info:
                console.print(f"Table '{table}' not found.", style="red")
                return
            
            if output == 'json':
                console.print(json.dumps(schema_info, indent=2))
            else:
                _display_table_schema(table, schema_info)
        else:
            # Show all tables schema
            full_schema = db_manager.get_database_schema()
            
            if output == 'json':
                console.print(json.dumps(full_schema, indent=2))
            else:
                for table_name, columns in full_schema.items():
                    _display_table_schema(table_name, columns)
                    console.print()  # Add spacing
                    
    except Exception as e:
        console.print(f"Error retrieving schema: {e}", style="red")

@cli.command()
def interactive():
    """Start interactive query generation session."""
    console.print(Panel.fit(
        "🔍 SQL Query Generator - Interactive Mode\n"
        "Type your questions in natural language!\n"
        "Commands: /help, /mode [direct|mcp|dry-run], /quit",
        style="blue"
    ))
    
    generator = SQLQueryGenerator(QueryExecutionMode.DIRECT)
    
    while True:
        try:
            user_input = click.prompt("\n💭 Ask your question", type=str)
            
            if user_input.lower() in ['/quit', '/exit', '/q']:
                console.print("Goodbye! 👋", style="green")
                break
            elif user_input.lower() == '/help':
                _show_help()
                continue
            elif user_input.lower().startswith('/mode'):
                parts = user_input.split()
                if len(parts) == 2 and parts[1] in ['direct', 'mcp', 'dry-run']:
                    mode_map = {
                        'direct': QueryExecutionMode.DIRECT,
                        'mcp': QueryExecutionMode.MCP,
                        'dry-run': QueryExecutionMode.DRY_RUN
                    }
                    generator.set_execution_mode(mode_map[parts[1]])
                    console.print(f"Mode set to: {parts[1]}", style="green")
                else:
                    console.print("Usage: /mode [direct|mcp|dry-run]", style="red")
                continue
            
            # Generate and execute query
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Processing your request...", total=None)
                result = asyncio.run(generator.generate_and_execute_query(user_input))
                progress.remove_task(task)
            
            _display_result(result, 'table')
            
        except KeyboardInterrupt:
            console.print("\nGoodbye! 👋", style="green")
            break

def _display_result(result: QueryResult, output_format: str):
    """Display query result in specified format."""
    
    if not result.success:
        console.print(f"❌ Error: {result.error}", style="red")
        if result.sql_query:
            console.print("\nGenerated SQL:")
            syntax = Syntax(result.sql_query, "sql", theme="monokai")
            console.print(syntax)
        return
    
    # Show success message
    console.print("✅ Query generated successfully!", style="green")
    
    # Show confidence and explanation
    if result.confidence > 0:
        confidence_style = "green" if result.confidence > 0.8 else "yellow" if result.confidence > 0.5 else "red"
        console.print(f"Confidence: {result.confidence:.1%}", style=confidence_style)
    
    if result.explanation:
        console.print(f"Explanation: {result.explanation}", style="blue")
    
    # Show SQL query
    console.print("\nGenerated SQL:")
    syntax = Syntax(result.sql_query, "sql", theme="monokai")
    console.print(syntax)
    
    # Show execution results if available
    if result.data is not None:
        console.print(f"\n📊 Query Results ({result.row_count} rows):")
        
        if output_format == 'json':
            console.print(json.dumps(result.data, indent=2))
        elif output_format == 'table' and result.data:
            _display_data_table(result.data)
        elif output_format == 'sql':
            # Already shown above
            pass
        
        if result.execution_time:
            console.print(f"\n⏱️  Execution time: {result.execution_time:.3f}s", style="dim")

def _display_table_schema(table_name: str, columns: list):
    """Display table schema in a formatted table."""
    table = Table(title=f"Table: {table_name}")
    table.add_column("Column", style="cyan", no_wrap=True)
    table.add_column("Type", style="magenta")
    table.add_column("Nullable", style="green")
    table.add_column("Default", style="yellow")
    
    for column in columns:
        table.add_row(
            column['column_name'],
            column['data_type'],
            str(column['is_nullable']),
            str(column['column_default']) if column['column_default'] else 'None'
        )
    
    console.print(table)

def _display_data_table(data: list):
    """Display query results in a table format."""
    if not data:
        console.print("No data returned.", style="dim")
        return
    
    # Create table with columns from first row
    table = Table()
    columns = list(data[0].keys())
    
    for column in columns:
        table.add_column(str(column), style="cyan")
    
    # Add rows (limit to first 50 for readability)
    for row in data[:50]:
        table.add_row(*[str(row.get(col, '')) for col in columns])
    
    if len(data) > 50:
        table.add_row(*[f"... ({len(data) - 50} more rows)" if i == 0 else "" 
                        for i in range(len(columns))])
    
    console.print(table)

def _show_help():
    """Show help information for interactive mode."""
    help_text = """
Available Commands:
- /help          Show this help message
- /mode <mode>   Set execution mode (direct, mcp, dry-run)
- /quit          Exit interactive mode

Example Questions:
- "Show all users from the users table"
- "Find orders placed in the last 30 days"
- "Count products by category"
- "Update user email where id is 123"
"""
    console.print(Panel(help_text, title="Help", style="blue"))

if __name__ == '__main__':
    cli() 