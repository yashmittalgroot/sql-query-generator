"""
Interactive Chat Interface for SQL Query Generation and Improvement
"""

import streamlit as st
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging
import sys
import io
from contextlib import redirect_stdout, redirect_stderr

# Configure logging to capture all logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Import our modules
from query_generator import SQLQueryGenerator, QueryExecutionMode
from database import db_manager
from gemini_client import gemini_client
from config import settings

class LogCapture:
    """Capture logs for display in the UI."""
    
    def __init__(self):
        self.logs = []
        self.handler = None
        
    def start_capture(self):
        """Start capturing logs."""
        self.logs = []
        self.handler = logging.StreamHandler(io.StringIO())
        self.handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.handler.setFormatter(formatter)
        
        # Add handler to all relevant loggers
        loggers = [
            logging.getLogger('query_generator'),
            logging.getLogger('database'),
            logging.getLogger('gemini_client'),
            logging.getLogger('__main__')
        ]
        
        for logger in loggers:
            logger.addHandler(self.handler)
    
    def get_logs(self) -> List[str]:
        """Get captured logs."""
        if self.handler and hasattr(self.handler, 'stream'):
            log_content = self.handler.stream.getvalue()
            if log_content:
                return log_content.strip().split('\n')
        return []
    
    def stop_capture(self):
        """Stop capturing logs."""
        if self.handler:
            loggers = [
                logging.getLogger('query_generator'),
                logging.getLogger('database'),
                logging.getLogger('gemini_client'),
                logging.getLogger('__main__')
            ]
            
            for logger in loggers:
                logger.removeHandler(self.handler)

class ChatSession:
    """Manages chat session state and conversation history."""
    
    def __init__(self):
        self.messages: List[Dict[str, Any]] = []
        self.current_sql: Optional[str] = None
        self.current_schema: Optional[Dict[str, Any]] = None
        self.sql_history: List[Dict[str, Any]] = []  # Track SQL evolution
        self.query_generator = SQLQueryGenerator()
        
    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        """Add a message to the conversation."""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now(),
            "metadata": metadata or {}
        }
        self.messages.append(message)
        
        # Track SQL changes for context
        if metadata and "sql_query" in metadata:
            sql_entry = {
                "timestamp": datetime.now(),
                "sql": metadata["sql_query"],
                "explanation": metadata.get("explanation", ""),
                "confidence": metadata.get("confidence", 0.0),
                "user_request": self._get_last_user_message(),
                "changes_made": metadata.get("changes_made", "")
            }
            self.sql_history.append(sql_entry)
    
    def _get_last_user_message(self) -> str:
        """Get the last user message."""
        for msg in reversed(self.messages):
            if msg["role"] == "user":
                return msg["content"]
        return ""
    
    def get_conversation_context(self) -> str:
        """Get comprehensive conversation context for AI."""
        context = "=== CONVERSATION HISTORY ===\n\n"
        
        # Add recent conversation (last 10 messages)
        recent_messages = self.messages[-10:] if len(self.messages) > 10 else self.messages
        for i, msg in enumerate(recent_messages):
            timestamp = msg['timestamp'].strftime("%H:%M:%S")
            context += f"[{timestamp}] {msg['role'].upper()}: {msg['content']}\n"
            
            # Add SQL info if available
            if msg.get('metadata', {}).get('sql_query'):
                context += f"    SQL Generated: {msg['metadata']['sql_query'][:100]}...\n"
                if msg['metadata'].get('confidence'):
                    context += f"    Confidence: {msg['metadata']['confidence']:.1%}\n"
            context += "\n"
        
        # Add SQL evolution history
        if self.sql_history:
            context += "\n=== SQL EVOLUTION HISTORY ===\n\n"
            for i, sql_entry in enumerate(self.sql_history[-5:], 1):  # Last 5 SQL changes
                timestamp = sql_entry['timestamp'].strftime("%H:%M:%S")
                context += f"Version {i} [{timestamp}]:\n"
                context += f"  User Request: {sql_entry['user_request']}\n"
                context += f"  Changes Made: {sql_entry.get('changes_made', 'Initial generation')}\n"
                context += f"  SQL: {sql_entry['sql']}\n"
                context += f"  Explanation: {sql_entry['explanation']}\n"
                context += f"  Confidence: {sql_entry['confidence']:.1%}\n\n"
        
        # Add current context
        context += "\n=== CURRENT STATE ===\n"
        context += f"Current SQL: {self.current_sql or 'None'}\n"
        context += f"Total messages in conversation: {len(self.messages)}\n"
        context += f"SQL versions created: {len(self.sql_history)}\n"
        
        return context
    
    def get_sql_evolution_summary(self) -> str:
        """Get a summary of how the SQL has evolved."""
        if not self.sql_history:
            return "No SQL queries generated yet."
        
        summary = f"SQL Evolution ({len(self.sql_history)} versions):\n"
        for i, sql_entry in enumerate(self.sql_history, 1):
            summary += f"  {i}. {sql_entry['user_request'][:50]}{'...' if len(sql_entry['user_request']) > 50 else ''}\n"
            if sql_entry.get('changes_made'):
                summary += f"     Changes: {sql_entry['changes_made'][:60]}{'...' if len(sql_entry['changes_made']) > 60 else ''}\n"
        
        return summary

def init_session_state():
    """Initialize Streamlit session state."""
    if 'chat_session' not in st.session_state:
        st.session_state.chat_session = ChatSession()
    if 'log_capture' not in st.session_state:
        st.session_state.log_capture = LogCapture()

async def generate_sql_with_logs(user_input: str, chat_session: ChatSession, log_capture: LogCapture) -> Dict[str, Any]:
    """Generate SQL query and capture all logs."""
    log_capture.start_capture()
    
    try:
        # Generate SQL query
        result = await chat_session.query_generator.generate_and_execute_query(
            user_input=user_input,
            execute=True
        )
        
        logs = log_capture.get_logs()
        
        return {
            "result": result,
            "logs": logs,
            "success": True
        }
        
    except Exception as e:
        logs = log_capture.get_logs()
        return {
            "result": None,
            "logs": logs,
            "error": str(e),
            "success": False
        }
    finally:
        log_capture.stop_capture()

async def improve_sql_with_ai(current_sql: str, improvement_request: str, schema_info: str, conversation_context: str = "") -> Dict[str, Any]:
    """Use AI to improve existing SQL based on user feedback with conversation context."""
    try:
        prompt = f"""
You are an expert SQL developer. The user has an existing SQL query and wants to improve it. You have access to the conversation history to understand the context better.

CONVERSATION HISTORY:
{conversation_context}

CURRENT SQL:
{current_sql}

USER REQUEST FOR IMPROVEMENT:
"{improvement_request}"

AVAILABLE SCHEMA:
{schema_info}

Please analyze the conversation history, current SQL, and the user's improvement request, then provide an improved version of the SQL query.

Consider:
1. The original intent from the conversation history
2. Previous modifications that were made
3. The specific improvement request
4. How this fits into the overall conversation flow

Respond with a JSON object containing:
{{
    "improved_sql": "The improved SQL query",
    "changes_made": "Description of what changes were made",
    "explanation": "Why these changes improve the query and how they relate to the conversation",
    "confidence": 0.95,
    "context_understood": "Brief summary of what you understood from the conversation history"
}}

Only return the JSON object, no additional text.
"""
        
        gemini_client._ensure_initialized()
        response = gemini_client.model.generate_content(prompt)
        
        # Parse response
        response_text = response.text.strip()
        if response_text.startswith("```json"):
            response_text = response_text.replace("```json", "").replace("```", "").strip()
        elif response_text.startswith("```"):
            response_text = response_text.replace("```", "").strip()
        
        import json
        result = json.loads(response_text)
        
        return {
            "success": True,
            "improved_sql": result.get("improved_sql", current_sql),
            "changes_made": result.get("changes_made", "No changes made"),
            "explanation": result.get("explanation", ""),
            "confidence": result.get("confidence", 0.0),
            "context_understood": result.get("context_understood", "")
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "improved_sql": current_sql
        }

def main():
    """Main Streamlit app."""
    st.set_page_config(
        page_title="AI SQL Chat Assistant",
        page_icon="🤖",
        layout="wide"
    )
    
    init_session_state()
    
    st.title("🤖 AI SQL Query Generator Chat")
    st.markdown("*Generate and improve SQL queries through natural language conversation*")
    
    # Sidebar for settings and status
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Database connection status
        st.subheader("📊 Database Status")
        if st.button("Test Connection"):
            with st.spinner("Testing connection..."):
                if db_manager.test_connection():
                    st.success("✅ Connected to PostgreSQL")
                else:
                    st.error("❌ Connection failed")
        
        # Execution mode
        st.subheader("🚀 Execution Mode")
        execution_mode = st.selectbox(
            "Mode",
            options=["direct", "dry_run"],
            index=0,
            help="Direct: Execute queries, Dry-run: Generate only"
        )
        
        if execution_mode == "direct":
            st.session_state.chat_session.query_generator.set_execution_mode(QueryExecutionMode.DIRECT)
        else:
            st.session_state.chat_session.query_generator.set_execution_mode(QueryExecutionMode.DRY_RUN)
        
        # Conversation context
        st.subheader("💬 Conversation Context")
        total_messages = len(st.session_state.chat_session.messages)
        sql_versions = len(st.session_state.chat_session.sql_history)
        
        st.metric("Messages", total_messages)
        st.metric("SQL Versions", sql_versions)
        
        if st.session_state.chat_session.current_sql:
            st.success("🎯 Active SQL Query")
            if st.button("📋 Show Current SQL"):
                with st.expander("Current SQL Query", expanded=True):
                    st.code(st.session_state.chat_session.current_sql, language="sql")
        
        # SQL Evolution
        if sql_versions > 0:
            st.subheader("📈 SQL Evolution")
            if st.button("📜 Show Evolution History"):
                with st.expander("SQL Evolution Summary", expanded=True):
                    st.text(st.session_state.chat_session.get_sql_evolution_summary())
        
        # Clear conversation
        if st.button("🗑️ Clear Conversation"):
            st.session_state.chat_session = ChatSession()
            st.rerun()
    
    # Main chat interface
    chat_container = st.container()
    
    with chat_container:
        # Display conversation history
        for message in st.session_state.chat_session.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])
                
                # Show metadata if available
                if message["metadata"]:
                    metadata = message["metadata"]
                    
                    # Show SQL query
                    if "sql_query" in metadata:
                        st.code(metadata["sql_query"], language="sql")
                    
                    # Show query results
                    if "data" in metadata and metadata["data"]:
                        st.subheader("📊 Query Results")
                        st.dataframe(metadata["data"][:100])  # Limit to 100 rows
                        st.caption(f"Showing first 100 rows of {len(metadata['data'])} total")
                    
                    # Show execution details
                    if "execution_time" in metadata:
                        st.info(f"⏱️ Execution time: {metadata['execution_time']:.3f}s")
                    
                    if "confidence" in metadata:
                        confidence = metadata["confidence"]
                        color = "green" if confidence > 0.8 else "orange" if confidence > 0.6 else "red"
                        st.markdown(f"🎯 Confidence: <span style='color: {color}'>{confidence:.1%}</span>", unsafe_allow_html=True)
        
        # Chat input
        user_input = st.chat_input("Ask me to generate or improve SQL queries...")
        
        # Show helpful suggestions if there's an active SQL query
        if st.session_state.chat_session.current_sql and not user_input:
            st.info("💡 **You can improve the current SQL by saying:**\n\n"
                   "• 'Change this to a LEFT JOIN'\n"
                   "• 'Add a WHERE clause for active records'\n"
                   "• 'Group the results by date'\n"
                   "• 'Add ordering by amount descending'\n"
                   "• 'Include null values in the results'\n"
                   "• 'Add a HAVING clause to filter groups'\n"
                   "• 'Make this query more efficient'")
        
        if user_input:
            # Add user message
            st.session_state.chat_session.add_message("user", user_input)
            
            with st.chat_message("user"):
                st.write(user_input)
            
            # Determine if this is a new query or an improvement request
            is_improvement = (
                st.session_state.chat_session.current_sql is not None and
                any(word in user_input.lower() for word in [
                    'improve', 'change', 'modify', 'fix', 'add', 'remove', 
                    'alter', 'update', 'better', 'optimize', 'join', 'where'
                ])
            )
            
            with st.chat_message("assistant"):
                if is_improvement:
                    # Improve existing SQL
                    st.write("🔧 Improving the existing SQL query...")
                    
                    with st.spinner("Working on improvements..."):
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            improvement_result = loop.run_until_complete(
                                improve_sql_with_ai(
                                    st.session_state.chat_session.current_sql,
                                    user_input,
                                    str(st.session_state.chat_session.current_schema),
                                    st.session_state.chat_session.get_conversation_context()
                                )
                            )
                        finally:
                            loop.close()
                    
                    if improvement_result["success"]:
                        improved_sql = improvement_result["improved_sql"]
                        changes_made = improvement_result["changes_made"]
                        explanation = improvement_result["explanation"]
                        confidence = improvement_result["confidence"]
                        context_understood = improvement_result.get("context_understood", "")
                        
                        response = f"✅ **SQL Improved!**\n\n**Changes Made:** {changes_made}\n\n**Explanation:** {explanation}"
                        
                        if context_understood:
                            response += f"\n\n**Context Understanding:** {context_understood}"
                        
                        st.write(response)
                        
                        # Show comparison if we have previous SQL
                        if st.session_state.chat_session.current_sql != improved_sql:
                            with st.expander("🔍 SQL Comparison", expanded=False):
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.subheader("Previous SQL")
                                    st.code(st.session_state.chat_session.current_sql, language="sql")
                                with col2:
                                    st.subheader("Improved SQL")
                                    st.code(improved_sql, language="sql")
                        
                        # Show the improved SQL
                        st.code(improved_sql, language="sql")
                        
                        # Update current SQL
                        st.session_state.chat_session.current_sql = improved_sql
                        
                        # Add response to conversation
                        st.session_state.chat_session.add_message(
                            "assistant", 
                            response,
                            {
                                "sql_query": improved_sql,
                                "confidence": confidence,
                                "changes_made": changes_made,
                                "context_understood": context_understood
                            }
                        )
                    else:
                        error_msg = f"❌ Failed to improve SQL: {improvement_result.get('error', 'Unknown error')}"
                        st.error(error_msg)
                        st.session_state.chat_session.add_message("assistant", error_msg)
                
                else:
                    # Generate new SQL
                    st.write("🤖 Generating SQL query...")
                    
                    # Show expandable logs section
                    log_expander = st.expander("📋 View Detailed Logs", expanded=False)
                    
                    with st.spinner("Analyzing your request and generating SQL..."):
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            generation_result = loop.run_until_complete(
                                generate_sql_with_logs(
                                    user_input,
                                    st.session_state.chat_session,
                                    st.session_state.log_capture
                                )
                            )
                        finally:
                            loop.close()
                    
                    # Show logs in expander
                    with log_expander:
                        if generation_result["logs"]:
                            for log_line in generation_result["logs"]:
                                if "ERROR" in log_line:
                                    st.error(log_line)
                                elif "WARNING" in log_line:
                                    st.warning(log_line)
                                elif "INFO" in log_line:
                                    st.info(log_line)
                                else:
                                    st.text(log_line)
                        else:
                            st.text("No logs captured")
                    
                    if generation_result["success"]:
                        result = generation_result["result"]
                        
                        if result.success:
                            # Success response
                            response = f"✅ **Query Generated Successfully!**\n\n**Explanation:** {result.explanation}"
                            st.write(response)
                            
                            # Store current SQL and schema
                            st.session_state.chat_session.current_sql = result.sql_query
                            if not st.session_state.chat_session.current_schema:
                                st.session_state.chat_session.current_schema = "Schema information cached"
                            
                            # Add response to conversation
                            metadata = {
                                "sql_query": result.sql_query,
                                "confidence": result.confidence,
                                "execution_time": result.execution_time,
                                "data": result.data
                            }
                            
                            st.session_state.chat_session.add_message("assistant", response, metadata)
                            
                        else:
                            # Error response
                            error_msg = f"❌ **Query Generation Failed**\n\nError: {result.error}"
                            st.error(error_msg)
                            st.session_state.chat_session.add_message("assistant", error_msg)
                    
                    else:
                        # Generation failed
                        error_msg = f"❌ **SQL Generation Failed**\n\nError: {generation_result.get('error', 'Unknown error')}"
                        st.error(error_msg)
                        st.session_state.chat_session.add_message("assistant", error_msg)
            
            # Rerun to update the conversation
            st.rerun()

if __name__ == "__main__":
    main() 