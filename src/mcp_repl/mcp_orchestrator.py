from contextlib import AsyncExitStack
from typing import Dict, Any, List
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from pydantic import BaseModel
import json
from pathlib import Path


class MCPServerConfig(BaseModel):
    """Represents an MCP server"""
    path: str
    name: str
    description: str

class MCPOrchestrator:
    """Handles connections to MCP servers and tool execution"""

    def __init__(self):
        self.tools = []
        self.available_tools = []
        self.sessions = {}
        self.exit_stack = AsyncExitStack()

    @classmethod
    async def from_config(cls, config_path: str) -> 'MCPOrchestrator':
        """Create MCPOrchestrator instance from a config file and connect to all servers"""
        with open(config_path, "r") as f:
            config = json.load(f)
            print(f"config: {config}")
            servers = []
            for server in config:
                if Path(server["path"]).is_absolute() or Path(server["path"]).exists():
                    server["path"] = str(Path(server["path"]))
                else:
                    resolved_path = (Path(config_path).parent / server["path"]).resolve()
                    if not resolved_path.exists():
                        raise ValueError(
                            f"Server path '{server['path']}' not found. "
                            f"Path should be either absolute or relative to the config file location: {Path(config_path).parent}"
                        )
                    server["path"] = str(resolved_path)
                servers.append(MCPServerConfig(**server))
            
            if not servers:
                raise ValueError("No servers configured")
                
            orchestrator = cls()
            
            for server in servers:
                await orchestrator.connect_to_server(server.path)
                
            return orchestrator
                
    async def connect_to_server(self, server_script_path: str):
        """Connect to an MCP server

        Args:
            server_script_path: Path to the server script (.py or .js)
        """
        is_python = server_script_path.endswith(".py")
        is_js = server_script_path.endswith(".js")
        if not (is_python or is_js):
            raise ValueError("Server script must be a .py or .js file")

        server_name = server_script_path.split("/")[-1].split(".")[0]
        if server_name.endswith("_mcp"):
            server_name = server_name[:-4]

        command = "python" if is_python else "node"
        server_params = StdioServerParameters(
            command=command, args=[server_script_path], env=None
        )

        stdio_transport = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        stdio, write = stdio_transport
        session = await self.exit_stack.enter_async_context(ClientSession(stdio, write))

        await session.initialize()

        response = await session.list_tools()
        server_tools = response.tools

        self.sessions[server_script_path] = {
            "session": session,
            "tools": server_tools,
            "server_name": server_name,
        }

        self._update_available_tools()
        return [f"{server_name}_{tool.name}" for tool in server_tools]

    def _update_available_tools(self):
        """Update the combined list of available tools from all servers"""
        self.tools = []
        self.available_tools = []

        for server_path, server_data in self.sessions.items():
            server_name = server_data.get("server_name", "")
            for tool in server_data["tools"]:
                unique_name = f"{server_name}_{tool.name}"
                description = f"[{server_name.upper()}] {tool.description}"

                self.available_tools.append(
                    {
                        "name": unique_name,
                        "description": description,
                        "input_schema": tool.inputSchema,
                    }
                )

                self.tools.append((unique_name, server_path, tool.name))

    async def call_tool(self, tool_name: str, tool_args: Dict[str, Any]):
        """Call a tool and return the result"""
        for unique_name, server_path, original_name in self.tools:
            if unique_name == tool_name:
                server_data = self.sessions[server_path]
                return await server_data["session"].call_tool(original_name, tool_args)

        raise ValueError(f"Tool '{tool_name}' not found in any connected server")

    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()
