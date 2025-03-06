# MCP-REPL

A lightweight REPL (Read-Eval-Print Loop) for interacting with various services through MCP (Model Control Protocol).

## Overview

`mcp-repl` is designed for efficient development, debugging, and testing of MCP servers. It provides an intuitive command-line interface that's simpler than using the Cloud Desktop app, allowing developers to quickly:

- Send queries to MCP servers
- View detailed tool execution
- Automatically save chat history
- Test multiple MCP services simultaneously

## Installation

Install via pip or uv:

```bash
uv add mcp-repl
```

### Development Installation

Clone and install in editable mode:

```bash
git clone https://github.com/yourusername/mcp-repl.git
cd mcp-repl
uv venv
```

## Databases Example

This example demonstrates how you can:

- Set up 3 databases (PostgreSQL, MySQL, Redis) in Kubernetes with mock data
- Run MCP servers for each dataset
- Interact with all databases from a single REPL

### Key Features

- Natural language queries across multiple databases
- Comparison of data structures across systems
- Execution of complex operations seamlessly

### Running the Example

Setup infrastructure (requires `kind` and `helm`):

```bash
bash examples/databases/setup.sh
```

Generate mock data:

```bash
python examples/databases/generate_mock_data.py
```

Start the REPL:

```bash
python -m src.mcp_repl.repl --config examples/databases/config.json --auto-approve-tools
```

### Sample Queries

You can perform queries like:

- "Find all tables in PostgreSQL and MySQL"
- "Compare the structure of the 'users' table in PostgreSQL with the 'customers' table in MySQL"
- "Count the number of records in each database"

## Usage

Start the REPL:

```bash
python -m src.mcp_repl.repl --config path/to/config.json
```

### Optional Flags

- `--auto-approve-tools`: Automatically approve all tool executions
- `--always-show-full-output`: Always display complete tool outputs
- `--chat-history-dir PATH`: Directory to save chat history (default: `./chat_history`)

## Testing

Comprehensive integration tests are included to verify functionality:

Run all tests:

```bash
pytest
```

Run specific integration tests:

```bash
pytest ./test/integration/
```

