# AI SQL Query Generator

A powerful Python application that converts natural language to SQL queries using Google Gemini AI and connects to PostgreSQL databases. Features both command-line tools and an interactive chat interface.

## ✨ Key Features

### 🧠 **AI-Powered Intelligence**
- **Smart Table Selection**: AI analyzes your query and intelligently selects the most relevant tables
- **Natural Language Processing**: Convert plain English to optimized SQL queries
- **Iterative Improvement**: Chat with AI to refine and improve your SQL queries
- **High Confidence Scoring**: Get confidence ratings for generated queries

### 🎯 **Multiple Interfaces**
- **Interactive Chat UI**: Web-based chat interface for conversational SQL generation
- **Command Line Interface**: Quick CLI tools for direct query generation
- **REST API**: Programmatic access with auto-documentation
- **Detailed Logging**: Comprehensive logs showing AI decision-making process

### 🛡️ **Enterprise Ready**
- **Query Safety Validation**: Prevents dangerous SQL operations
- **Optimized Performance**: Sub-6 second response times even with 350+ table databases
- **Multiple Execution Modes**: Direct execution, dry-run, or MCP integration
- **Smart Schema Caching**: Intelligent caching for large databases

## 🚀 Quick Start

### 1. **Setup Environment**
```bash
# Clone and navigate to project
git clone <repository>
cd sql-query-generator

# Create virtual environment
python -m venv sql-query-env
source sql-query-env/bin/activate  # On Windows: sql-query-env\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. **Configure Environment**
Create a `.env` file:
```env
# Required: Google Gemini API
GEMINI_API_KEY=your_gemini_api_key_here

# Required: PostgreSQL Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_database
DB_USER=your_username
DB_PASSWORD=your_password

# Optional: Performance tuning
SCHEMA_CACHE_TIMEOUT=1800
MAX_TABLES_DEFAULT=20
```

### 3. **Launch Chat Interface** 🆕
```bash
# Method 1: Direct launch
streamlit run chat_app.py

# Method 2: Using launcher script
python launch_chat.py
```

The chat interface will open at `http://localhost:8501`

## 💬 Interactive Chat Interface

### **Features**
- **Natural Conversation**: Ask questions in plain English
- **Real-time SQL Generation**: See SQL queries generated instantly
- **Query Improvement**: Say things like "add a LEFT JOIN" or "filter for active customers"
- **Detailed Logs**: Expandable logs showing AI reasoning and table selection
- **Query Results**: Execute queries and see results in beautiful tables
- **Conversation History**: Full chat history with SQL queries and explanations

### **Example Conversations**

**User**: "Get all company names with open payment amounts"

**AI**: ✅ **Query Generated Successfully!**

**Explanation**: This query retrieves company names and calculates open payment amounts by joining dl_buyer with dl_payment_history tables.

```sql
SELECT b.company_name,
       SUM(p.payment_amount - COALESCE(p.consumed_amount, 0)) AS open_payment_amount
FROM dl_buyer b
JOIN dl_payment_history p ON b.books_buyer_id = p.books_buyer_id
GROUP BY b.company_name
HAVING SUM(p.payment_amount - COALESCE(p.consumed_amount, 0)) > 0;
```

**User**: "Change that to a LEFT JOIN and include companies with zero amounts"

**AI**: 🔧 **SQL Improved!**

**Changes Made**: Changed INNER JOIN to LEFT JOIN and removed HAVING clause to include companies with zero amounts.

```sql
SELECT b.company_name,
       COALESCE(SUM(p.payment_amount - COALESCE(p.consumed_amount, 0)), 0) AS open_payment_amount
FROM dl_buyer b
LEFT JOIN dl_payment_history p ON b.books_buyer_id = p.books_buyer_id
GROUP BY b.company_name
ORDER BY b.company_name;
```

## 🖥️ Command Line Interface

### **Basic Usage**
```bash
# Generate and execute query
python cli.py generate "get all companies with payments > 1000"

# Generate only (dry run)
python cli.py generate "show me top 10 customers" --mode dry_run

# Interactive mode
python cli.py interactive

# Test database connection
python cli.py test-connection
```

### **Advanced Options**
```bash
# Limit table selection
python cli.py generate "your query" --max-tables 15

# Different table prefix
python cli.py generate "your query" --table-prefix "tbl_"

# Export results
python cli.py generate "your query" --output results.json
```

## 🔍 AI Table Selection

The system now uses **AI-powered table selection** instead of simple keyword matching:

### **How It Works**
1. **Query Analysis**: AI analyzes your natural language request
2. **Context Understanding**: Identifies entities, operations, and relationships needed
3. **Intelligent Selection**: Chooses the most relevant tables with detailed reasoning
4. **Confidence Scoring**: Provides confidence levels for selections

### **Example AI Reasoning**
```
🧠 AI Table Selection Results (confidence: 95.0%):
  1. dl_buyer - This table likely contains company names and is the starting point
  2. dl_payment_history - This table stores payment amounts explicitly mentioned
  3. dl_payment_information - Contains general payment information and status
  4. dl_invoices - Needed to determine invoice totals related to payments
```

## 📊 Performance Optimizations

### **Enterprise Scale Performance**
- **Bulk Schema Queries**: Single query retrieves schema for multiple tables
- **Smart Caching**: Configurable schema caching (default: 30 minutes)
- **Table Limiting**: Intelligent table selection (default: 20 most relevant)
- **AI Optimization**: Reduced from 354 tables → 20 relevant tables in 1.4 seconds

### **Performance Metrics** (354-table database)
- **Database Connection**: ~0.7s
- **AI Table Selection**: ~1.4s (20 tables from 354)
- **Schema Retrieval**: ~0.8s (bulk query)
- **SQL Generation**: ~2.5s (Gemini AI)
- **Total Pipeline**: **~5.8s** (previously 5+ minutes)

## 🔧 API Usage

### **REST API**
```bash
# Start API server
python -m uvicorn api:app --reload

# Generate SQL
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{"query": "get all companies with open payments", "execute": true}'

# API Documentation
open http://localhost:8000/docs
```

### **Python Integration**
```python
from query_generator import SQLQueryGenerator
from database import db_manager

# Initialize
generator = SQLQueryGenerator()

# Generate and execute
result = await generator.generate_and_execute_query(
    "get all companies with payments > 1000",
    execute=True
)

print(f"SQL: {result.sql_query}")
print(f"Confidence: {result.confidence:.1%}")
print(f"Results: {len(result.data)} rows")
```

## 🛠️ Advanced Configuration

### **Execution Modes**
- **`DIRECT`**: Execute queries directly via psycopg2
- **`DRY_RUN`**: Generate SQL without execution  
- **`MCP`**: Execute via Model Context Protocol server

### **Table Selection Tuning**
```python
# Custom table selection
relevant_tables = db_manager.get_relevant_tables(
    user_query="your query",
    table_prefix="dl_",
    max_tables=15
)

# AI-powered schema retrieval
schema = db_manager.get_smart_database_schema(
    user_query="your query",
    table_prefix="custom_",
    max_tables=25
)
```

### **Safety and Validation**
```python
# Query safety validation
if gemini_client.validate_query_safety(sql_query):
    # Safe to execute
    results = db_manager.execute_query(sql_query)
```

## 🔐 Security Features

- **SQL Injection Prevention**: Input validation and parameterized queries
- **Query Safety Validation**: Blocks dangerous operations (DROP, TRUNCATE, etc.)
- **Environment Variable Protection**: Secure credential management
- **Connection Timeouts**: Configurable database timeouts

## 🐛 Troubleshooting

### **Common Issues**

**Chat Interface Won't Load**
```bash
# Check if port is available
lsof -i :8501

# Try different port
streamlit run chat_app.py --server.port 8502
```

**Database Connection Failed**
```bash
# Test connection
python cli.py test-connection

# Check environment variables
python -c "from config import settings; print(settings.db_host)"
```

**AI Table Selection Slow**
```bash
# Reduce table limit
python cli.py generate "your query" --max-tables 10

# Use direct table specification
export MAX_TABLES_DEFAULT=15
```

### **Debug Mode**
```bash
# Enable detailed logging
export LOG_LEVEL=DEBUG
python cli.py generate "your query"
```

## 📈 Monitoring & Logs

The system provides comprehensive logging:

- **🔥 Pipeline Events**: Query generation workflow
- **🧠 AI Decisions**: Table selection reasoning  
- **📊 Performance Metrics**: Timing for each step
- **🎯 Confidence Scores**: AI confidence levels
- **⚡ Execution Results**: Query results and timing

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Google Gemini AI** for natural language processing
- **PostgreSQL** for robust database support
- **Streamlit** for the beautiful chat interface
- **FastAPI** for API framework

---

**Happy querying! 🚀**
