# mcp-repl

A REPL interface for interacting with various services through MCP (Model Control Protocol).

## Description

mcp-repl provides a lightweight REPL (Read-Eval-Print Loop) for testing and developing MCP servers. It's designed to be significantly easier to use than the Cloud Desktop app, allowing developers to quickly test their MCP implementations, debug tool calls, and develop new MCP services.

The REPL provides an interactive command-line interface where you can:
- Send queries to MCP servers
- View tool execution details
- Automatically save chat history
- Test multiple MCP services simultaneously

## Setup

You can install mcp-repl using pip or uv:

pip install mcp-repl

uv add mcp-repl

bash
Clone the repository
git clone https://github.com/yourusername/mcp-repl.git
cd mcp-repl
Install in development mode
pip install -e .



## Usage 

To start the REPL, run:
bash
python -m src.mcp_repl.repl --config path/to/config.json

Optional flags:
- `--auto-approve-tools`: Automatically approve all tool executions
- `--always-show-full-output`: Always display complete tool outputs
- `--chat-history-dir PATH`: Specify a directory for saving chat history (default: ./chat_history)

Example:

bash
python -m src.mcp_repl.repl --config examples/databases/config.json --auto-approve-tools
## Databases example 

The repository includes a comprehensive example of using mcp-repl with multiple database services simultaneously. This example demonstrates how to:

1. Set up a local Kubernetes cluster with PostgreSQL, MySQL, and Redis
2. Generate mock data for testing
3. Create MCP servers for each database
4. Query all databases through a single REPL interface

This is particularly powerful as it allows you to:
- Query multiple databases with natural language
- Compare data across different database systems
- Perform complex operations without switching contexts

To run the databases example:
bash
Set up the infrastructure (requires kind and helm)
bash examples/databases/setup.sh
Generate mock data
python examples/databases/generate_mock_data.py
Start the REPL
python -m src.mcp_repl.repl --config examples/databases/config.json --auto-approve-tools


Then you can ask questions like:
- "Find all tables in PostgreSQL and MySQL"
- "Compare the structure of the 'users' table in PostgreSQL with the 'customers' table in MySQL"
- "Count the number of records in each database"

## Testing 

The project includes comprehensive integration tests to ensure everything works correctly:


bash
Run all tests
pytest
Run specific integration tests
pytest ./test/integration/