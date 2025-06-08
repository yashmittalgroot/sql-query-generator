import asyncio
import json
from typing import Dict, List, Any, Optional
import logging
import aiohttp
from config import settings

logger = logging.getLogger(__name__)

class MCPClient:
    """Client for communicating with MCP (Model Context Protocol) servers."""
    
    def __init__(self):
        self.server_url = settings.mcp_server_url
        self.server_name = settings.mcp_server_name
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def initialize_connection(self) -> bool:
        """Initialize connection with the MCP server."""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            # Send initialization request
            init_payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "roots": {
                            "listChanged": True
                        },
                        "sampling": {}
                    },
                    "clientInfo": {
                        "name": "sql-query-generator",
                        "version": "1.0.0"
                    }
                }
            }
            
            async with self.session.post(
                f"{self.server_url}/initialize",
                json=init_payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"MCP server initialized: {result}")
                    return True
                else:
                    logger.error(f"Failed to initialize MCP server: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error initializing MCP connection: {e}")
            return False
    
    async def list_resources(self) -> List[Dict[str, Any]]:
        """List available resources from the MCP server."""
        try:
            payload = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "resources/list",
                "params": {}
            }
            
            async with self.session.post(
                f"{self.server_url}/resources/list",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("result", {}).get("resources", [])
                else:
                    logger.error(f"Failed to list resources: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error listing resources: {e}")
            return []
    
    async def read_resource(self, uri: str) -> Optional[str]:
        """Read a specific resource from the MCP server."""
        try:
            payload = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "resources/read",
                "params": {
                    "uri": uri
                }
            }
            
            async with self.session.post(
                f"{self.server_url}/resources/read",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    contents = result.get("result", {}).get("contents", [])
                    if contents:
                        return contents[0].get("text", "")
                    return None
                else:
                    logger.error(f"Failed to read resource: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error reading resource: {e}")
            return None
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Call a tool on the MCP server."""
        try:
            payload = {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
            
            async with self.session.post(
                f"{self.server_url}/tools/call",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("result", {})
                else:
                    logger.error(f"Failed to call tool: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error calling tool: {e}")
            return None
    
    async def get_database_schema_via_mcp(self) -> Optional[Dict[str, Any]]:
        """Get database schema information via MCP server."""
        try:
            # This is an example - actual implementation depends on your MCP server
            schema_result = await self.call_tool("get_schema", {})
            return schema_result
            
        except Exception as e:
            logger.error(f"Error getting schema via MCP: {e}")
            return None
    
    async def execute_query_via_mcp(self, query: str) -> Optional[List[Dict[str, Any]]]:
        """Execute SQL query via MCP server."""
        try:
            result = await self.call_tool("execute_query", {"query": query})
            return result.get("data", []) if result else None
            
        except Exception as e:
            logger.error(f"Error executing query via MCP: {e}")
            return None

class MCPManager:
    """High-level manager for MCP operations."""
    
    def __init__(self):
        self.client = MCPClient()
        self._initialized = False
    
    async def ensure_initialized(self) -> bool:
        """Ensure MCP client is initialized."""
        if not self._initialized:
            async with self.client:
                success = await self.client.initialize_connection()
                self._initialized = success
                return success
        return True
    
    async def get_schema(self) -> Optional[Dict[str, Any]]:
        """Get database schema via MCP."""
        if await self.ensure_initialized():
            async with self.client:
                return await self.client.get_database_schema_via_mcp()
        return None
    
    async def execute_query(self, query: str) -> Optional[List[Dict[str, Any]]]:
        """Execute query via MCP."""
        if await self.ensure_initialized():
            async with self.client:
                return await self.client.execute_query_via_mcp(query)
        return None

# Global MCP manager instance
mcp_manager = MCPManager() 