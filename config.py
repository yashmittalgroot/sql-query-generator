import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from typing import Optional

# Load environment variables
load_dotenv()

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Gemini API settings
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    
    # Database settings
    db_host: str = os.getenv("DB_HOST", "localhost")
    db_port: int = int(os.getenv("DB_PORT", "5432"))
    db_name: str = os.getenv("DB_NAME", "")
    db_user: str = os.getenv("DB_USER", "")
    db_password: str = os.getenv("DB_PASSWORD", "")
    
    # MCP settings
    mcp_server_url: str = os.getenv("MCP_SERVER_URL", "http://localhost:8080")
    mcp_server_name: str = os.getenv("MCP_SERVER_NAME", "postgres-mcp-server")
    
    # Application settings
    debug: bool = os.getenv("DEBUG", "True").lower() == "true"
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Performance settings
    max_schema_tables: int = int(os.getenv("MAX_SCHEMA_TABLES", "50"))
    schema_cache_timeout: int = int(os.getenv("SCHEMA_CACHE_TIMEOUT", "300"))  # 5 minutes
    
    @property
    def database_url(self) -> str:
        """Generate PostgreSQL connection URL."""
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings() 