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
    session.add_message('user', 'get all employees with their total work hours')
    session.add_message('assistant', 'Generated SQL query for employees with work hours', {
        'sql_query': 'SELECT e.employee_name, SUM(t.hours_worked) AS total_hours FROM emp_employees e JOIN emp_timesheets t ON e.employee_id = t.employee_id GROUP BY e.employee_name ORDER BY total_hours DESC',
        'confidence': 95.0,
        'explanation': 'This query joins employees with timesheets and shows total work hours'
    })
    
    print("2. 🔧 Simulating First Improvement...")
    session.add_message('user', 'change this to LEFT JOIN and include employees with zero hours')
    session.add_message('assistant', 'Updated to LEFT JOIN to include all employees', {
        'sql_query': 'SELECT e.employee_name, COALESCE(SUM(t.hours_worked), 0) AS total_hours FROM emp_employees e LEFT JOIN emp_timesheets t ON e.employee_id = t.employee_id GROUP BY e.employee_name ORDER BY total_hours DESC',
        'changes_made': 'Changed INNER JOIN to LEFT JOIN and added COALESCE for zero hours',
        'explanation': 'Now includes all employees, even those without recorded hours'
    })
    
    print("3. ⚡ Simulating Second Improvement...")
    session.add_message('user', 'add filtering for employees hired after 2020')
    session.add_message('assistant', 'Added date filtering for recent employees', {
        'sql_query': 'SELECT e.employee_name, COALESCE(SUM(t.hours_worked), 0) AS total_hours FROM emp_employees e LEFT JOIN emp_timesheets t ON e.employee_id = t.employee_id WHERE e.hire_date > \'2020-01-01\' GROUP BY e.employee_name ORDER BY total_hours DESC',
        'changes_made': 'Added WHERE clause to filter employees hired after 2020-01-01',
        'explanation': 'Query now only shows employees hired after 2020'
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