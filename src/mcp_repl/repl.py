import asyncio
from typing import Optional, List, Dict, Any
from contextlib import AsyncExitStack
import sys
import json
import os
import argparse
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.key_binding import KeyBindings
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text
from rich.console import Group
from rich.syntax import Syntax
from rich.prompt import Confirm
import uuid
import logging
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from anthropic import Anthropic
from dotenv import load_dotenv
from pydantic import BaseModel
class CustomRailwayLogFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "time": self.formatTime(record),
            "level": record.levelname,
            "message": record.getMessage()
        }
        return json.dumps(log_record)

def get_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    formatter = CustomRailwayLogFormatter()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

logger = get_logger()

load_dotenv()

# Define styles for the prompt
style = Style.from_dict(
    {
        "prompt": "ansicyan bold",
        "user-input": "ansigreen",
    }
)

# Create key bindings
kb = KeyBindings()


class LLMClient:
    """Handles interactions with the LLM and tools"""

    def __init__(self):
        self.anthropic = Anthropic()
        self.chat_history = []
        self.tools = []
        self.available_tools = []
        self.sessions = {}  # Dictionary to store multiple sessions
        self.exit_stack = AsyncExitStack()
        self.stdio = None
        self.write = None

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

    async def add_user_message(self, query: str):
        """Add a user message to the chat history"""
        self.chat_history.append({"role": "user", "content": query})

    async def get_llm_response(self):
        """Get a response from the LLM based on the current chat history"""
        system_prompt = """You are Claude, an AI assistant by Anthropic. You can help with a wide range of tasks including:
1. Writing and explaining code in various programming languages
2. Answering general knowledge questions
3. Providing creative content like stories or poems
4. Using the available tools when appropriate

When asked to write code or perform general tasks unrelated to the available tools, you should do so directly. Only use the provided tools when they are specifically relevant to the user's request."""

        response = self.anthropic.messages.create(
            model="claude-3-5-sonnet-20241022",
            system=system_prompt,
            messages=self.chat_history,
            tools=self.available_tools,
            max_tokens=1000,
        )

        return response

    async def call_tool(self, tool_name: str, tool_args: Dict[str, Any]):
        """Call a tool and return the result"""
        # Find which session has this tool
        for server_path, server_data in self.sessions.items():
            for tool in server_data["tools"]:
                if tool.name == tool_name:
                    return await server_data["session"].call_tool(tool_name, tool_args)

        raise ValueError(f"Tool '{tool_name}' not found in any connected server")

    async def add_assistant_message(self, content):
        """Add an assistant message to the chat history"""
        assistant_message = {"role": "assistant", "content": content}
        self.chat_history.append(assistant_message)
        return assistant_message

    async def add_tool_result(self, tool_use_id, result):
        """Add a tool result to the chat history"""
        tool_result_message = {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": tool_use_id,
                    "content": result.content,
                }
            ],
        }
        self.chat_history.append(tool_result_message)

    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()


class RichUI:
    """Handles the Rich UI components and user interaction"""

    def __init__(self, llm_client: LLMClient, auto_approve_tools=False):
        self.llm_client = llm_client
        self.console = Console()
        self.auto_approve_tools = auto_approve_tools

    def print_welcome(self):
        """Print welcome message"""
        self.console.print("[bold blue]MCP Client Started![/bold blue]")
        self.console.print(
            "Type your queries, [bold red]quit[/bold red] to exit, or press [bold red]q[/bold red] to exit directly."
        )

    def print_connected_tools(self, tool_names, server_path):
        """Print connected tools"""
        self.console.print(
            f"\nConnected to server [bold cyan]{server_path}[/bold cyan] with tools:",
            tool_names,
        )

    def print_markdown(self, text):
        """Print markdown text"""
        self.console.print(Markdown(text))

    def print_tool_call(self, tool_name):
        """Print tool call information"""
        self.console.print(f"\n[Tool call: {tool_name}]\n")

    def confirm_tool_execution(self, tool_name, tool_args):
        """Ask for confirmation to execute a tool"""
        # If auto-approve is enabled, return True without asking
        if self.auto_approve_tools:
            self.console.print(f"[bold yellow]Auto-approving tool execution: {tool_name}[/bold yellow]")
            return True
            
        tool_args_str = str(tool_args)
        confirmation_text = Group(
            Text("🛠️  Tool Execution Request", style="bold white"),
            Text(""),
            Text("Tool: ", style="bold cyan") + Text(tool_name, style="bold yellow"),
            Text("Arguments: ", style="bold cyan")
            + Text(tool_args_str, style="italic"),
            Text(""),
            Text("Proceed with execution? (Y/n): ", style="bold green"),
        )

        self.console.print(
            Panel(
                confirmation_text,
                border_style="yellow",
                title="Confirmation Required",
                subtitle="Press Enter to approve",
            )
        )

        # Get user confirmation
        confirm = input()
        self.console.print()  # Add a blank line after input

        return confirm.lower() != "n"

    def display_tool_result(self, tool_name, tool_args, result):
        """Display tool execution result"""
        # Extract the result text
        result_text = result.content
        formatted_result = ""

        if isinstance(result_text, list) and len(result_text) > 0:
            try:
                # Try to parse as JSON
                json_data = json.loads(result_text[0].text)
                formatted_result = json.dumps(json_data, indent=2)
            except (json.JSONDecodeError, AttributeError):
                # If not JSON, use the raw text
                if hasattr(result_text[0], "text"):
                    formatted_result = result_text[0].text
                else:
                    formatted_result = str(result_text)
        else:
            formatted_result = str(result_text)

        header = Group(
            Text("🔧 Tool Call: ", style="bold cyan")
            + Text(tool_name, style="bold yellow"),
            Text("📥 Arguments: ", style="bold cyan")
            + Text(str(tool_args), style="italic"),
            Text("📤 Raw Result:", style="bold cyan"),
            Text(""),  # Empty line for spacing
        )

        # Format the result content based on tool and content type
        if len(formatted_result) > 500:
            # For long outputs, truncate and offer to show full content
            preview_length = 500
            truncated = len(formatted_result) > preview_length
            preview = formatted_result[:preview_length] + ("..." if truncated else "")

            # Display truncated content in panel
            panel_content = Group(header, Text(preview))

            if truncated:
                panel_content.renderables.append(
                    Text(
                        "\n[Output truncated. Full length: "
                        + str(len(formatted_result))
                        + " characters]",
                        style="italic yellow",
                    )
                )

            self.console.print(
                Panel(panel_content, title="Tool Result", border_style="cyan")
            )

            # Offer to show full content
            if truncated:
                show_full = input("\nShow full output? (y/n): ")
                if show_full.lower() == "y":
                    self.console.print("\nFull output:")
                    self.console.print(formatted_result)
        else:
            # For other results, just use the formatted text in a standard panel
            panel_content = Group(header, Text(formatted_result))
            self.console.print(
                Panel(panel_content, title="Tool Result", border_style="cyan")
            )

        self.console.print()

    def print_error(self, error):
        """Print error message"""
        self.console.print(f"\n[bold red]Error:[/bold red] {str(error)}")
        import traceback

        self.console.print(traceback.format_exc())

    def print_interrupted(self):
        """Print interrupted message"""
        self.console.print(
            "\n[bold yellow]Interrupted. Type 'quit' to exit.[/bold yellow]"
        )

    def print_tool_cancelled(self):
        """Print tool cancelled message"""
        self.console.print("[bold red]Tool call cancelled by user[/bold red]")


class MCPClient:
    """Main client that coordinates LLM and UI components"""

    def __init__(self, auto_approve_tools=False):
        self.llm_client = LLMClient()
        self.ui = RichUI(self.llm_client, auto_approve_tools)
        self.connected_servers = []
        self.chat_id = str(uuid.uuid4())  # Generate a unique ID for this chat session
        self.chat_file = f"chat_history/{self.chat_id}.json"
        
        # Create chat history directory if it doesn't exist
        os.makedirs("chat_history", exist_ok=True)
        
        # Initialize the chat history file with an empty list
        with open(self.chat_file, "w") as f:
            json.dump([], f)

    def debug_and_save_chat_history(self):
        try:
            with open(self.chat_file, "w") as f:
                json.dump(self.llm_client.chat_history, f, indent=2, default=str)
        except Exception as e:
            self.ui.console.print(f"[bold red]Error saving chat history: {str(e)}[/bold red]")

    async def connect_to_server(self, server_script_path: str):
        """Connect to an MCP server"""
        tool_names = await self.llm_client.connect_to_server(server_script_path)
        self.connected_servers.append(server_script_path)
        self.ui.print_connected_tools(tool_names, server_script_path)

    async def connect_to_multiple_servers(self, server_paths: List[str]):
        """Connect to multiple MCP servers"""
        for server_path in server_paths:
            await self.connect_to_server(server_path)

    async def process_query(self, query: str):
        """Process a query using Claude and available tools"""
        # Add the new user message to chat history
        await self.llm_client.add_user_message(query)

        # Debug and save chat history
        self.debug_and_save_chat_history()

        # Process the conversation with multiple tool calls if needed
        while True:
            # Show status indicator for API call
            with self.ui.console.status("[bold green]Processing query...[/bold green]"):
                response = await self.llm_client.get_llm_response()

            # Track if any tool was used in this turn
            tool_used = False
            assistant_content = []

            # Process and display the response
            for content in response.content:
                if content.type == "text":
                    self.ui.print_markdown(content.text)
                    assistant_content.append(content)
                elif content.type == "tool_use":
                    tool_used = True
                    tool_name = content.name
                    tool_args = content.input
                    tool_use_id = content.id

                    # Print tool call information
                    self.ui.print_tool_call(tool_name)

                    # Get user confirmation
                    if self.ui.confirm_tool_execution(tool_name, tool_args):
                        # Show status indicator for tool execution
                        with self.ui.console.status(
                            "[bold green]Executing tool...[/bold green]"
                        ):
                            # Execute tool call
                            result = await self.llm_client.call_tool(
                                tool_name, tool_args
                            )

                        # Display the tool result
                        self.ui.display_tool_result(tool_name, tool_args, result)

                        # Add assistant's message with tool use to chat history
                        await self.llm_client.add_assistant_message([content])

                        # Add tool result to chat history
                        await self.llm_client.add_tool_result(tool_use_id, result)
                        
                        # Debug and save chat history after tool result
                        self.debug_and_save_chat_history()
                    else:
                        self.ui.print_tool_cancelled()
                        # Exit the loop if tool execution was cancelled
                        tool_used = False
                        break

            # If no tool was used, add the assistant's message to chat history and exit the loop
            if not tool_used:
                if assistant_content:
                    await self.llm_client.add_assistant_message(assistant_content)
                    # Debug and save chat history after assistant response
                    self.debug_and_save_chat_history()
                break

    async def chat_loop(self):
        """Run an interactive chat loop with improved UI"""
        self.ui.print_welcome()

        # Create prompt session with history
        session = PromptSession(
            history=FileHistory(".mcp_chat_history"),
            style=style,
            key_bindings=kb,
            multiline=True,
            prompt_continuation="... ",
        )

        while True:
            try:
                # Display a fancy prompt
                query = await session.prompt_async(
                    HTML("<prompt>Query</prompt> <user-input>❯</user-input> "),
                    multiline=False,
                )

                # Check for exit commands
                if query.lower() in ("quit", "exit", "q"):
                    break

                # Skip empty queries
                if not query.strip():
                    continue

                # Process the query
                await self.process_query(query)

            except KeyboardInterrupt:
                self.ui.print_interrupted()
            except Exception as e:
                self.ui.print_error(e)

    async def cleanup(self):
        """Clean up resources"""
        await self.llm_client.cleanup()

class MCPServerConfig(BaseModel):
    """Represents an MCP server"""

    path: str
    name: str
    description: str

async def main():
    parser = argparse.ArgumentParser(description="MCP Client")
    parser.add_argument("--config", type=str, help="Path to config file")
    parser.add_argument("--auto-approve-tools", action="store_true", 
                        help="Automatically approve all tool executions without prompting")
    args = parser.parse_args()

    servers = []

    if args.config:
        try:
            with open(args.config, "r") as f:
                config = json.load(f)
                for server in config:
                    server["path"] = str((Path(args.config).parent / server["path"]).resolve())
                    servers.append(MCPServerConfig(**server))
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Error loading config file: {e}")
            sys.exit(1)

    if not servers:
        print("Error: No servers provided in config file.")
        print("Usage: python client.py --config config.json")
        sys.exit(1)

    client = MCPClient(auto_approve_tools=args.auto_approve_tools)
    try:
        logger.info("Connecting to servers...")
        for server in servers:
            await client.connect_to_server(server.path)
        await client.chat_loop()
    finally:
        await client.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
