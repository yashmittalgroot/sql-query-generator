#!/usr/bin/env python3
"""
Test script to demonstrate enhanced conversation context features
"""

from chat_app import ChatSession
from datetime import datetime

def test_conversation_context():
    """Test the conversation context functionality."""
    print("🧪 Testing Enhanced Conversation Context Features")
    print("=" * 60)
    
    # Create a test session
    session = ChatSession()
    
    print("1. 📝 Simulating Initial Query...")
    session.add_message('user', 'get all companies with payment amounts')
    session.add_message('assistant', 'Generated SQL query for companies with payments', {
        'sql_query': 'SELECT c.company_name, SUM(p.payment_amount) AS total_payments FROM dl_buyer c JOIN dl_payment_history p ON c.books_buyer_id = p.books_buyer_id GROUP BY c.company_name ORDER BY total_payments DESC',
        'confidence': 0.95,
        'explanation': 'This query joins companies with payments and shows total payment amounts'
    })
    
    print("2. 🔧 Simulating First Improvement...")
    session.add_message('user', 'change this to LEFT JOIN and include companies with zero payments')
    session.add_message('assistant', 'Updated to LEFT JOIN to include all companies', {
        'sql_query': 'SELECT c.company_name, COALESCE(SUM(p.payment_amount), 0) AS total_payments FROM dl_buyer c LEFT JOIN dl_payment_history p ON c.books_buyer_id = p.books_buyer_id GROUP BY c.company_name ORDER BY total_payments DESC',
        'confidence': 0.92,
        'changes_made': 'Changed INNER JOIN to LEFT JOIN and added COALESCE for zero amounts',
        'explanation': 'Now includes all companies, even those without payments'
    })
    
    print("3. ⚡ Simulating Second Improvement...")
    session.add_message('user', 'add filtering for companies created after 2020')
    session.add_message('assistant', 'Added date filtering for recent companies', {
        'sql_query': 'SELECT c.company_name, COALESCE(SUM(p.payment_amount), 0) AS total_payments FROM dl_buyer c LEFT JOIN dl_payment_history p ON c.books_buyer_id = p.books_buyer_id WHERE c.created_date > \'2020-01-01\' GROUP BY c.company_name ORDER BY total_payments DESC',
        'confidence': 0.89,
        'changes_made': 'Added WHERE clause to filter companies created after 2020-01-01',
        'explanation': 'Query now only shows companies created after 2020'
    })
    
    print("\n📊 Session Statistics:")
    print(f"   Total Messages: {len(session.messages)}")
    print(f"   SQL Versions: {len(session.sql_history)}")
    print(f"   Current SQL: {'Active' if session.current_sql else 'None'}")
    
    print("\n📈 SQL Evolution Summary:")
    print(session.get_sql_evolution_summary())
    
    print("\n💬 Full Conversation Context:")
    print("-" * 40)
    context = session.get_conversation_context()
    # Show first 1000 characters for demo
    print(context[:1000] + "..." if len(context) > 1000 else context)
    
    print("\n✅ Test completed successfully!")
    return session

def test_improvement_context():
    """Test how conversation context helps with improvements."""
    print("\n🔍 Testing Improvement Context Understanding")
    print("=" * 60)
    
    session = test_conversation_context()
    
    # Simulate what the AI would receive for improvements
    print("\n🤖 Context that would be sent to AI for next improvement:")
    print("-" * 50)
    context = session.get_conversation_context()
    
    improvement_request = "optimize this query for better performance"
    schema_info = "Sample schema info here..."
    
    print(f"Improvement Request: '{improvement_request}'")
    print(f"Schema Available: {'Yes' if schema_info else 'No'}")
    print(f"Context Length: {len(context)} characters")
    print(f"SQL History Available: {len(session.sql_history)} versions")
    
    print("\n✨ The AI now has complete context to understand:")
    print("   • Original user intent")
    print("   • All previous modifications")
    print("   • Why each change was made")
    print("   • Current query state")
    print("   • Full conversation flow")

if __name__ == "__main__":
    test_conversation_context()
    test_improvement_context()
    
    print("\n🚀 Enhanced Features Ready!")
    print("=" * 40)
    print("Launch the chat interface to experience:")
    print("✅ Conversation memory across improvements")
    print("✅ SQL evolution tracking")
    print("✅ Context-aware AI responses")
    print("✅ Visual SQL comparison")
    print("✅ Improvement suggestions")
    print("\nRun: streamlit run chat_app.py") 