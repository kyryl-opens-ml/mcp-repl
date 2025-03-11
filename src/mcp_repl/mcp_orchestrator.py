import json
import logging
from contextlib import AsyncExitStack
from pathlib import Path
from typing import Any, Dict, List

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class MCPServerConfig(BaseModel):
    """Represents an MCP server"""
    id: str
    path: str


class MCPOrchestrator:
    """Handles connections to MCP servers and tool execution"""

    def __init__(self):
        self.tools = []
        self.available_tools = []
        self.sessions = {}
        self.exit_stack = AsyncExitStack()

    @classmethod
    async def from_server_configs(
        cls, server_configs: List[MCPServerConfig]
    ) -> "MCPOrchestrator":
        """Create MCPOrchestrator instance from a list of server configs"""
        orchestrator = cls()
        for server_config in server_configs:
            await orchestrator.connect_to_server(server_config.path, server_config.id)
        return orchestrator

    @classmethod
    async def from_config(cls, config_path: str) -> "MCPOrchestrator":
        """Create MCPOrchestrator instance from a config file and connect to all servers"""
        with open(config_path, "r") as f:
            config = json.load(f)
            print(f"config: {config}")
            servers = []
            for server in config:
                if Path(server["path"]).is_absolute() or Path(server["path"]).exists():
                    server["path"] = str(Path(server["path"]))
                else:
                    resolved_path = (
                        Path(config_path).parent / server["path"]
                    ).resolve()
                    if not resolved_path.exists():
                        raise ValueError(
                            f"Server path '{server['path']}' not found. "
                            f"Path should be either absolute or relative to the config file location: {Path(config_path).parent}"
                        )
                    server["path"] = str(resolved_path)
                servers.append(MCPServerConfig(**server))

            if not servers:
                logger.warning("No servers configured")

            orchestrator = cls()

            for server in servers:
                await orchestrator.connect_to_server(server.path, server.id)

            return orchestrator

    async def connect_to_server(self, server_script_path: str, server_id: str):
        """Connect to an MCP server

        Args:
            server_script_path: Path to the server script
            server_id: ID of the server
        """

        command = "python"
        server_params = StdioServerParameters(
            command=command, args=[server_script_path], env=None
        )

        stdio_transport = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        stdio, write = stdio_transport
        session: ClientSession = await self.exit_stack.enter_async_context(
            ClientSession(stdio, write)
        )

        server_info = await session.initialize()

        response = await session.list_tools()
        server_tools = response.tools

        self.sessions[server_id] = {
            "session": session,
            "tools": server_tools,
            "server_info": server_info,
            "server_id": server_id,
            "server_path": server_script_path,
        }

        self._update_available_tools()

    def _update_available_tools(self):
        """Update the combined list of available tools from all servers"""
        self.tools = []
        self.available_tools = []

        for server_id, server_data in self.sessions.items():
            for tool in server_data["tools"]:
                unique_name = f"{server_id}_{tool.name}"
                description = f"[{server_id.upper()}] {tool.description}"

                self.available_tools.append(
                    {
                        "name": unique_name,
                        "description": description,
                        "input_schema": tool.inputSchema,
                    }
                )

                self.tools.append((unique_name, server_id, tool.name))

    async def call_tool(self, tool_name: str, tool_args: Dict[str, Any]):
        """Call a tool and return the result"""
        for unique_name, server_id, original_name in self.tools:
            if unique_name == tool_name:
                server_data = self.sessions[server_id]
                return await server_data["session"].call_tool(original_name, tool_args)

        raise ValueError(f"Tool '{tool_name}' not found in any connected server")

    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()

    async def add_server(self, server_config: MCPServerConfig) -> List[str]:
        """Add a new MCP server to the orchestrator

        Args:
            server_config: Configuration for the server to add

        Returns:
            List of tool names available from the added server
        """
        if not Path(server_config.path).exists():
            raise ValueError(f"Server path '{server_config.path}' not found")

        if server_config.id in self.sessions:
            raise ValueError(f"Server at '{server_config.path}' is already connected")

        await self.connect_to_server(server_config.path, server_config.id)
        return [tool.name for tool in self.sessions[server_config.id]["tools"]]

    async def remove_server(self, server_id: str) -> None:
        """Remove an MCP server from the orchestrator

        Args:
            server_id: ID of the server to remove
        """
        if server_id not in self.sessions:
            raise ValueError(f"No server connected with ID '{server_id}'")

        # TODO: Shutdown session
        # server_data = self.sessions[server_id]
        # session = server_data["session"]

        del self.sessions[server_id]
        self._update_available_tools()

    def list_servers(self) -> List[str]:
        """List all connected MCP servers"""
        return list(self.sessions.keys())
