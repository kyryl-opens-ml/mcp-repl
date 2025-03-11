import argparse
import asyncio
import json
import logging
import os
import sys
import traceback
import uuid
from enum import StrEnum
from itertools import groupby

from dotenv import load_dotenv
from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style
from rich.console import Console, Group
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from mcp_repl.llm_client import LLMClient
from mcp_repl.mcp_orchestrator import MCPOrchestrator, MCPServerConfig


class CustomLogFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "time": self.formatTime(record),
            "level": record.levelname,
            "message": record.getMessage(),
        }
        return json.dumps(log_record)


def get_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    formatter = CustomLogFormatter()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


logger = get_logger()

load_dotenv()

style = Style.from_dict(
    {
        "prompt": "ansicyan bold",
        "user-input": "ansigreen",
    }
)

kb = KeyBindings()


class REPLCommands(StrEnum):
    EXIT = "q!"
    RELOAD = "r!"
    HELP = "h!"
    LIST_MCP = "l!"
    CLEAR = "c!"
    ADD_SERVER = "add!"
    REMOVE_SERVER = "remove!"
    LIST_SERVERS = "servers!"


class RichUI:
    """Handles the Rich UI components and user interaction"""

    def __init__(
        self,
        llm_client: LLMClient,
        mcp_client: MCPOrchestrator,
        auto_approve_tools=False,
        always_show_full_output=False,
    ):
        self.llm_client = llm_client
        self.mcp_client = mcp_client
        self.console = Console()
        self.auto_approve_tools = auto_approve_tools
        self.always_show_full_output = always_show_full_output
        self.chat_id = str(uuid.uuid4())
        self.chat_file = f"chat_history/{self.chat_id}.json"

        os.makedirs("chat_history", exist_ok=True)
        with open(self.chat_file, "w") as f:
            json.dump([], f)

    def print_welcome(self):
        """Print welcome message"""
        self.console.print("[bold blue]MCP Client Started![/bold blue]")
        self.console.print(
            "Available commands:\n"
            f"• [bold red]{REPLCommands.EXIT}[/bold red] to exit\n"
            f"• [bold yellow]{REPLCommands.RELOAD}[/bold yellow] to reload\n"
            f"• [bold green]{REPLCommands.HELP}[/bold green] for help\n"
            f"• [bold cyan]{REPLCommands.CLEAR}[/bold cyan] to clear screen\n"
            f"• [bold magenta]{REPLCommands.LIST_MCP}[/bold magenta] to list available tools\n"
            f"• [bold blue]{REPLCommands.ADD_SERVER}[/bold blue] to add a new MCP server\n"
            f"• [bold red]{REPLCommands.REMOVE_SERVER}[/bold red] to remove an MCP server\n"
            f"• [bold green]{REPLCommands.LIST_SERVERS}[/bold green] to list connected servers"
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
        if self.auto_approve_tools:
            self.console.print(
                f"[bold yellow]Auto-approving tool execution: {tool_name}[/bold yellow]"
            )
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

        confirm = input()
        self.console.print()

        return confirm.lower() != "n"

    def display_tool_result(self, tool_name, tool_args, result):
        """Display tool execution result"""
        result_text = result.content
        formatted_result = ""

        if isinstance(result_text, list) and len(result_text) > 0:
            try:
                json_data = json.loads(result_text[0].text)
                formatted_result = json.dumps(json_data, indent=2)
            except (json.JSONDecodeError, AttributeError):
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
            Text(""),
        )

        if len(formatted_result) > 500 and not self.always_show_full_output:
            preview_length = 500
            truncated = len(formatted_result) > preview_length
            preview = formatted_result[:preview_length] + ("..." if truncated else "")
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
            if truncated:
                show_full = input("\nShow full output? (y/n): ")
                if show_full.lower() == "y":
                    self.console.print("\nFull output:")
                    self.console.print(formatted_result)
        else:
            panel_content = Group(header, Text(formatted_result))
            self.console.print(
                Panel(panel_content, title="Tool Result", border_style="cyan")
            )

        self.console.print()

    def print_error(self, error):
        """Print error message"""
        self.console.print(f"\n[bold red]Error:[/bold red] {str(error)}")

        self.console.print(traceback.format_exc())

    def print_interrupted(self):
        """Print interrupted message"""
        self.console.print(
            "\n[bold yellow]Interrupted. Type 'quit' to exit.[/bold yellow]"
        )

    def print_tool_cancelled(self):
        """Print tool cancelled message"""
        self.console.print("[bold red]Tool call cancelled by user[/bold red]")

    def debug_and_save_chat_history(self):
        try:
            with open(self.chat_file, "w") as f:
                json.dump(self.llm_client.chat_history, f, indent=2, default=str)
        except Exception as e:
            self.console.print(
                f"[bold red]Error saving chat history: {str(e)}[/bold red]"
            )

    async def process_query(self, query: str):
        """Process a query using Claude and available tools"""
        await self.llm_client.add_user_message(query)

        self.debug_and_save_chat_history()

        while True:
            with self.console.status("[bold green]Processing query...[/bold green]"):
                response = await self.llm_client.get_llm_response(
                    self.mcp_client.available_tools
                )

            tool_used = False
            assistant_content = []

            for content in response.content:
                if content.type == "text":
                    self.print_markdown(content.text)
                    assistant_content.append(content)
                elif content.type == "tool_use":
                    tool_used = True
                    tool_name = content.name
                    tool_args = content.input
                    tool_use_id = content.id

                    self.print_tool_call(tool_name)

                    if self.confirm_tool_execution(tool_name, tool_args):
                        with self.console.status(
                            "[bold green]Executing tool...[/bold green]"
                        ):
                            result = await self.mcp_client.call_tool(
                                tool_name, tool_args
                            )

                        self.display_tool_result(tool_name, tool_args, result)

                        await self.llm_client.add_assistant_message([content])

                        await self.llm_client.add_tool_result(tool_use_id, result)

                        self.debug_and_save_chat_history()

                    else:
                        self.print_tool_cancelled()
                        tool_used = False
                        break

            if not tool_used:
                if assistant_content:
                    await self.llm_client.add_assistant_message(assistant_content)
                    self.debug_and_save_chat_history()
                break

    async def add_new_server(self):
        """Add a new MCP server"""
        self.console.print("[bold blue]Adding a new MCP server[/bold blue]")

        server_id = input("Enter server ID: ").strip()
        if not server_id:
            self.console.print("[bold red]Server ID cannot be empty[/bold red]")
            return

        server_path = input("Enter server script path: ").strip()
        if not server_path:
            self.console.print("[bold red]Server path cannot be empty[/bold red]")
            return

        try:
            server_config = MCPServerConfig(id=server_id, path=server_path)
            with self.console.status(
                "[bold green]Connecting to server...[/bold green]"
            ):
                tool_names = await self.mcp_client.add_server(server_config)

            self.console.print(
                f"[bold green]Successfully added server '{server_id}'[/bold green]"
            )
            self.console.print(
                f"Available tools from this server: {', '.join(tool_names)}"
            )
        except Exception as e:
            self.console.print(f"[bold red]Error adding server: {str(e)}[/bold red]")

    async def remove_server(self):
        """Remove an MCP server"""
        servers = self.mcp_client.list_servers()

        if not servers:
            self.console.print("[bold yellow]No servers connected[/bold yellow]")
            return

        self.console.print("[bold blue]Connected servers:[/bold blue]")
        for i, server_id in enumerate(servers, 1):
            self.console.print(f"{i}. {server_id}")

        choice = input("\nEnter server number to remove (or 'cancel'): ").strip()

        if choice.lower() == "cancel":
            return

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(servers):
                server_id = servers[idx]
                with self.console.status(
                    f"[bold yellow]Removing server '{server_id}'...[/bold yellow]"
                ):
                    await self.mcp_client.remove_server(server_id)
                self.console.print(
                    f"[bold green]Successfully removed server '{server_id}'[/bold green]"
                )
            else:
                self.console.print("[bold red]Invalid server number[/bold red]")
        except ValueError:
            self.console.print("[bold red]Please enter a valid number[/bold red]")
        except Exception as e:
            self.console.print(f"[bold red]Error removing server: {str(e)}[/bold red]")

    def list_servers(self):
        """List all connected MCP servers"""
        servers = self.mcp_client.list_servers()

        if not servers:
            self.console.print("[bold yellow]No servers connected[/bold yellow]")
            return

        table = Table(title="Connected MCP Servers", show_header=True)
        table.add_column("Server ID", style="cyan")
        table.add_column("Server Path", style="green")
        table.add_column("Tools Count", style="yellow")

        for server_id in servers:
            server_data = self.mcp_client.sessions[server_id]
            server_path = server_data["server_path"]
            tools_count = len(server_data["tools"])

            table.add_row(server_id, server_path, str(tools_count))

        self.console.print("\n")
        self.console.print(table)
        self.console.print("\n")

    async def chat_loop(self):
        """Run an interactive chat loop with improved UI"""
        self.print_welcome()

        session = PromptSession(
            history=FileHistory(".mcp_chat_history"),
            style=style,
            key_bindings=kb,
            multiline=True,
            prompt_continuation="... ",
        )

        while True:
            try:
                query = await session.prompt_async(
                    HTML("<prompt>Query</prompt> <user-input>❯</user-input> "),
                    multiline=False,
                )

                print(f"query: {query}")
                if query.lower().strip() == REPLCommands.EXIT:
                    return {"action": REPLCommands.EXIT}

                if query.lower().strip() == REPLCommands.RELOAD:
                    self.console.print("[bold yellow]Reloading REPL...[/bold yellow]")
                    return {"action": REPLCommands.RELOAD}

                if not query.strip():
                    continue

                if query.lower().strip() == REPLCommands.LIST_MCP:
                    self.print_available_tools()
                    continue

                if query.lower().strip() == REPLCommands.HELP:
                    self.print_welcome()
                    continue

                if query.lower().strip() == REPLCommands.CLEAR:
                    self.console.clear()
                    continue

                if query.lower().strip() == REPLCommands.ADD_SERVER:
                    await self.add_new_server()
                    continue

                if query.lower().strip() == REPLCommands.REMOVE_SERVER:
                    await self.remove_server()
                    continue

                if query.lower().strip() == REPLCommands.LIST_SERVERS:
                    self.list_servers()
                    continue

                await self.process_query(query)

            except KeyboardInterrupt:
                self.print_interrupted()
            except Exception as e:
                self.print_error(e)

    def print_available_tools(self):
        """Print available tools in a table format"""

        def get_server_type(tool):
            desc = tool["description"]
            if "[" in desc and "]" in desc:
                return desc[desc.find("[") + 1 : desc.find("]")]
            return "Other"

        sorted_tools = sorted(self.mcp_client.available_tools, key=get_server_type)
        grouped_tools = groupby(sorted_tools, key=get_server_type)

        for server_type, tools in grouped_tools:
            table = Table(title=f"{server_type} Tools", show_header=True, expand=True)
            table.add_column("Tool Name", style="cyan", no_wrap=True)
            table.add_column("Description", style="green")
            table.add_column("Arguments", style="yellow")

            for tool in tools:
                # Get all properties and mark required ones with *
                args = []
                properties = tool["input_schema"].get("properties", {})
                required = tool["input_schema"].get("required", [])

                for prop_name, prop_data in properties.items():
                    arg_str = f"{prop_name}"
                    if prop_name in required:
                        arg_str += "*"
                    if "default" in prop_data:
                        arg_str += f"={prop_data['default']}"
                    args.append(arg_str)

                args_str = ", ".join(args) if args else "None"

                # Clean up description - remove any prefix in square brackets and whitespace
                description = tool["description"]
                if "]" in description:
                    description = description.split("]", 1)[1]
                description = description.strip()

                # Take first line of description
                short_description = description.split("\n")[0].strip()

                # Remove server prefix from tool name if it exists
                tool_name = tool["name"]
                if server_type != "Other":
                    prefix = f"{server_type.lower()}_"
                    if tool_name.startswith(prefix):
                        tool_name = tool_name[len(prefix) :]

                table.add_row(tool_name, short_description, args_str)

            self.console.print("\n")
            self.console.print(table)

        self.console.print("\n* Required argument")
        self.console.print("\n")


def cli_main():
    """Entry point for the CLI command."""
    asyncio.run(main())


async def main():
    parser = argparse.ArgumentParser(description="MCP Client")
    parser.add_argument("--config", type=str, help="Path to config file")
    parser.add_argument(
        "--auto-approve-tools",
        action="store_true",
        help="Automatically approve all tool executions without prompting",
    )
    parser.add_argument(
        "--always-show-full-output",
        action="store_true",
        help="Always show full tool output without truncating or prompting",
    )
    args = parser.parse_args()

    while True:
        llm_client = LLMClient()
        try:
            mcp_orchestrator = await MCPOrchestrator.from_config(args.config)
        except ValueError as e:
            print(f"Error: {e}")
            print("Usage: python client.py --config config.json")
            sys.exit(1)

        ui = RichUI(
            llm_client,
            mcp_orchestrator,
            auto_approve_tools=args.auto_approve_tools,
            always_show_full_output=args.always_show_full_output,
        )

        try:
            ui.print_available_tools()

            result = await ui.chat_loop()
            if result["action"] == REPLCommands.EXIT:
                break
        finally:
            await mcp_orchestrator.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
