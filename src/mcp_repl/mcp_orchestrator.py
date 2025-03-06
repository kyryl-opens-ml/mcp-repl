from contextlib import AsyncExitStack
from typing import Dict, Any, List
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class MCPClient:
    """Handles connections to MCP servers and tool execution"""

    def __init__(self):
        self.tools = []
        self.available_tools = []
        self.sessions = {}  # Dictionary to store multiple sessions
        self.exit_stack = AsyncExitStack()
        self.stdio = None
        self.write = None
        self.connected_servers = []

    async def connect_to_server(self, server_script_path: str):
        """Connect to an MCP server

        Args:
            server_script_path: Path to the server script (.py or .js)
        """
        is_python = server_script_path.endswith(".py")
        is_js = server_script_path.endswith(".js")
        if not (is_python or is_js):
            raise ValueError("Server script must be a .py or .js file")

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

        # List available tools
        response = await session.list_tools()
        server_tools = response.tools

        # Store session with a unique identifier (using the script path as key)
        self.sessions[server_script_path] = {"session": session, "tools": server_tools}

        # Update available tools from all connected servers
        self._update_available_tools()
        
        self.connected_servers.append(server_script_path)

        return [tool.name for tool in server_tools]

    def _update_available_tools(self):
        """Update the combined list of available tools from all servers"""
        self.tools = []
        self.available_tools = []

        # Collect tools from all sessions
        for server_path, server_data in self.sessions.items():
            self.tools.extend(server_data["tools"])

        # Update the available tools list for Claude
        self.available_tools = [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.inputSchema,
            }
            for tool in self.tools
        ]

    async def call_tool(self, tool_name: str, tool_args: Dict[str, Any]):
        """Call a tool and return the result"""
        # Find which session has this tool
        for server_path, server_data in self.sessions.items():
            for tool in server_data["tools"]:
                if tool.name == tool_name:
                    return await server_data["session"].call_tool(tool_name, tool_args)

        raise ValueError(f"Tool '{tool_name}' not found in any connected server")

    async def connect_to_multiple_servers(self, server_paths: List[str]):
        """Connect to multiple MCP servers"""
        for server_path in server_paths:
            await self.connect_to_server(server_path)

    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()

