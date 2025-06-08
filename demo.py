#!/usr/bin/env python3
"""
Demo script showcasing AI-powered SQL query generation capabilities
"""

import asyncio
import time
from query_generator import SQLQueryGenerator, QueryExecutionMode
from database import db_manager

async def demo_ai_table_selection():
    """Demonstrate AI-powered table selection."""
    print("🤖 AI-Powered Table Selection Demo")
    print("=" * 50)
    
    # Test different types of queries
    queries = [
        "get all company names with open payment amounts",
        "find users who placed orders in the last month", 
        "show invoice totals by customer",
        "list all buyers with credit limits above 50000"
    ]
    
    for query in queries:
        print(f"\n🔍 Query: {query}")
        print("-" * 30)
        
        # Get AI-selected tables
        relevant_tables = db_manager.get_relevant_tables(
            user_query=query,
            table_prefix="dl_",
            max_tables=10
        )
        
        print(f"📊 AI selected {len(relevant_tables)} relevant tables")
        time.sleep(1)

async def demo_sql_generation():
    """Demonstrate SQL generation with full pipeline."""
    print("\n\n🚀 Full SQL Generation Pipeline Demo")
    print("=" * 50)
    
    generator = SQLQueryGenerator(QueryExecutionMode.DRY_RUN)
    
    # Example business query
    business_query = "get all company names with open payment amount (payment amount - consumed amount), joining dl_buyer with payment"
    
    print(f"\n📝 Business Query: {business_query}")
    print("-" * 40)
    
    start_time = time.time()
    
    result = await generator.generate_and_execute_query(
        user_input=business_query,
        execute=False  # Dry run
    )
    
    total_time = time.time() - start_time
    
    print(f"\n✅ Results:")
    print(f"   Success: {result.success}")
    print(f"   Confidence: {result.confidence:.1%}")
    print(f"   Total Time: {total_time:.2f}s")
    print(f"   Tables Used: {result.tables_used}")
    
    print(f"\n📋 Generated SQL:")
    print("```sql")
    print(result.sql_query)
    print("```")
    
    print(f"\n💡 Explanation: {result.explanation}")

async def demo_interactive_features():
    """Demonstrate features available in chat interface."""
    print("\n\n💬 Interactive Chat Features")
    print("=" * 50)
    
    print("The chat interface supports:")
    print("✅ Natural language queries")
    print("✅ Real-time SQL generation") 
    print("✅ Query improvement suggestions")
    print("✅ Detailed AI reasoning logs")
    print("✅ Query execution with results")
    print("✅ Conversation history")
    
    print("\n🎯 Example Chat Flow:")
    print("User: 'Get all companies with payments > 1000'")
    print("AI: [Generates SQL with JOIN between dl_buyer and dl_payment_history]")
    print("User: 'Change that to a LEFT JOIN'")
    print("AI: [Updates SQL to use LEFT JOIN]")
    print("User: 'Add a filter for active companies only'")
    print("AI: [Adds WHERE clause for active status]")

def main():
    """Run all demos."""
    print("🎭 AI SQL Query Generator - Feature Demo")
    print("=" * 60)
    print("This demo showcases the AI-powered features of the SQL Query Generator")
    print()
    
    try:
        # Test database connection first
        print("🔌 Testing database connection...")
        if db_manager.test_connection():
            print("✅ Database connection successful!")
        else:
            print("❌ Database connection failed. Check your .env configuration.")
            return
        
        # Run demos
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(demo_ai_table_selection())
            loop.run_until_complete(demo_sql_generation())
            loop.run_until_complete(demo_interactive_features())
        finally:
            loop.close()
        
        print("\n\n🚀 Ready to Try?")
        print("=" * 30)
        print("1. Launch Chat Interface: streamlit run chat_app.py")
        print("2. Command Line: python cli.py generate 'your query'")
        print("3. API Mode: python -m uvicorn api:app --reload")
        
    except KeyboardInterrupt:
        print("\n👋 Demo stopped by user")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")

if __name__ == "__main__":
    main() 