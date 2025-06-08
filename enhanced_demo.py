#!/usr/bin/env python3
"""
Enhanced Demo - Showcasing Conversation Context and AI Improvements
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from query_generator import SQLQueryGenerator, QueryExecutionMode
from chat_app import ChatSession, improve_sql_with_ai

async def demo_conversation_improvements():
    """Demonstrate the enhanced conversation context features."""
    print("🚀 ENHANCED SQL QUERY GENERATOR DEMO")
    print("=" * 60)
    print("🎯 New Features:")
    print("✅ AI-Powered Conversation Memory")
    print("✅ Context-Aware SQL Improvements")
    print("✅ SQL Evolution Tracking")
    print("✅ Interactive Chat Interface")
    print("=" * 60)
    
    # Initialize components
    generator = SQLQueryGenerator()
    generator.set_execution_mode(QueryExecutionMode.DRY_RUN)
    session = ChatSession()
    
    print("\n1️⃣ INITIAL QUERY GENERATION")
    print("-" * 40)
    
    # Generate initial query
    initial_query = "get all companies with their payment amounts"
    print(f"🔍 User Query: '{initial_query}'")
    
    try:
        result = generator.generate_sql(initial_query)
        print(f"✅ Generated SQL ({result.confidence:.1%} confidence):")
        print(f"📝 {result.sql_query}")
        print(f"⏱️  Generation Time: {result.execution_time:.2f}s")
        
        # Add to conversation
        session.add_message('user', initial_query)
        session.add_message('assistant', f"Generated SQL query for: {initial_query}", {
            'sql_query': result.sql_query,
            'confidence': result.confidence,
            'explanation': result.explanation
        })
        session.current_sql = result.sql_query
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    print("\n2️⃣ FIRST IMPROVEMENT WITH CONTEXT")
    print("-" * 40)
    
    # First improvement
    improvement1 = "change this to a LEFT JOIN and include companies with zero payments"
    print(f"🔧 User Request: '{improvement1}'")
    
    try:
        # Show conversation context being used
        context = session.get_conversation_context()
        print(f"📊 Context Length: {len(context)} characters")
        print(f"💬 Previous Messages: {len(session.messages)}")
        
        # Improve with context
        improvement_result = await improve_sql_with_ai(
            session.current_sql,
            improvement1,
            "Schema info available",
            context
        )
        
        if improvement_result["success"]:
            print(f"✅ SQL Improved!")
            print(f"📝 Changes: {improvement_result['changes_made']}")
            print(f"🧠 Context Understanding: {improvement_result['context_understood']}")
            print(f"📊 New SQL: {improvement_result['improved_sql'][:100]}...")
            
            # Add to conversation
            session.add_message('user', improvement1)
            session.add_message('assistant', "Improved SQL with LEFT JOIN", {
                'sql_query': improvement_result['improved_sql'],
                'confidence': improvement_result['confidence'],
                'changes_made': improvement_result['changes_made']
            })
            session.current_sql = improvement_result['improved_sql']
        else:
            print(f"❌ Improvement failed: {improvement_result.get('error')}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n3️⃣ SECOND IMPROVEMENT WITH FULL CONTEXT")
    print("-" * 40)
    
    # Second improvement
    improvement2 = "add ordering by amount descending and limit to top 10"
    print(f"🔧 User Request: '{improvement2}'")
    
    try:
        # Show enhanced context
        context = session.get_conversation_context()
        print(f"📊 Context Length: {len(context)} characters")
        print(f"💬 Total Messages: {len(session.messages)}")
        print(f"🔄 SQL Versions: {len(session.sql_history)}")
        
        # Improve with full context
        improvement_result = await improve_sql_with_ai(
            session.current_sql,
            improvement2,
            "Schema info available",
            context
        )
        
        if improvement_result["success"]:
            print(f"✅ SQL Improved Again!")
            print(f"📝 Changes: {improvement_result['changes_made']}")
            print(f"🧠 Context Understanding: {improvement_result['context_understood']}")
            print(f"📊 Final SQL: {improvement_result['improved_sql'][:100]}...")
            
            session.add_message('user', improvement2)
            session.add_message('assistant', "Added ordering and limit", {
                'sql_query': improvement_result['improved_sql'],
                'confidence': improvement_result['confidence'],
                'changes_made': improvement_result['changes_made']
            })
            session.current_sql = improvement_result['improved_sql']
        else:
            print(f"❌ Improvement failed: {improvement_result.get('error')}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n4️⃣ CONVERSATION SUMMARY")
    print("-" * 40)
    
    # Show conversation summary
    print(f"📊 Final Statistics:")
    print(f"   Total Messages: {len(session.messages)}")
    print(f"   SQL Versions: {len(session.sql_history)}")
    print(f"   Conversation Duration: {(datetime.now() - session.messages[0]['timestamp']).total_seconds():.1f}s")
    
    print(f"\n📈 SQL Evolution:")
    print(session.get_sql_evolution_summary())
    
    print(f"\n💡 Key Improvements:")
    print("✅ Each improvement remembers the full conversation history")
    print("✅ AI understands the original intent and all modifications")
    print("✅ Context-aware responses that build on previous changes")
    print("✅ Complete traceability of SQL evolution")
    print("✅ Interactive chat interface for natural conversation")
    
    return session

def demo_chat_interface():
    """Show how to use the chat interface."""
    print("\n5️⃣ INTERACTIVE CHAT INTERFACE")
    print("-" * 40)
    print("🎯 Launch the enhanced chat interface:")
    print("   streamlit run chat_app.py")
    print()
    print("🔧 New Features in Chat Interface:")
    print("   • Conversation memory across improvements")
    print("   • SQL evolution tracking in sidebar")
    print("   • Visual before/after SQL comparison")
    print("   • Improvement suggestions")
    print("   • Context-aware AI responses")
    print("   • Detailed logging with conversation context")
    print()
    print("💬 Example Conversation Flow:")
    print("   1. 'get all companies with payment amounts'")
    print("   2. 'change this to LEFT JOIN'")
    print("   3. 'add WHERE clause for active companies'")
    print("   4. 'order by amount descending'")
    print("   5. 'limit to top 10 results'")
    print()
    print("🧠 The AI remembers everything and provides intelligent improvements!")

async def main():
    """Run the complete demo."""
    try:
        session = await demo_conversation_improvements()
        demo_chat_interface()
        
        print("\n🎉 DEMO COMPLETE!")
        print("=" * 60)
        print("The SQL Query Generator now has:")
        print("✅ AI-powered conversation memory")
        print("✅ Context-aware improvements")
        print("✅ SQL evolution tracking")
        print("✅ Interactive chat interface")
        print("✅ Visual comparison tools")
        print("✅ Detailed logging and analysis")
        print()
        print("🚀 Ready for production use!")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 