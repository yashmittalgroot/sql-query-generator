#!/usr/bin/env python3
"""
Launch script for the AI SQL Chat Interface
"""

import subprocess
import sys
import os

def main():
    """Launch the Streamlit chat application."""
    print("🚀 Launching AI SQL Query Generator Chat Interface...")
    print("📝 Make sure your .env file is configured with:")
    print("   - GEMINI_API_KEY")
    print("   - Database connection parameters")
    print()
    
    # Check if running in virtual environment
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("⚠️  Warning: Not running in a virtual environment")
        print("   Consider activating sql-query-env first:")
        print("   source sql-query-env/bin/activate")
        print()
    
    try:
        # Launch Streamlit
        cmd = [sys.executable, "-m", "streamlit", "run", "chat_app.py", "--server.port=8501"]
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n👋 Chat interface stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error launching chat interface: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 