# MCP-REPL

A lightweight REPL (Read-Eval-Print Loop) for interacting with various services through MCP (Model Context Protocol).

[![PyPI version](https://badge.fury.io/py/mcp-repl.svg)](https://pypi.org/project/mcp-repl/)
[![Databases Tests](https://github.com/kyryl-opens-ml/mcp-repl/actions/workflows/databases-example-test.yaml/badge.svg)](https://github.com/kyryl-opens-ml/mcp-repl/actions/workflows/databases-example-test.yaml)
[![Infrastructure Tests](https://github.com/kyryl-opens-ml/mcp-repl/actions/workflows/infra-example-test.yaml/badge.svg)](https://github.com/kyryl-opens-ml/mcp-repl/actions/workflows/infra-example-test.yaml)

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

## Usage

Start the REPL:

```bash
uv run mcp-repl --config path/to/config.json
```

## Examples

**🔥 Check out our real-world examples to see mcp-repl in action! 🔥**

- **[Databases](./examples/databases/)** - Database administrators: See how to query, monitor, and manage your databases with natural language
- **[Infrastructure](./examples/infra/)** - DevOps engineers: Explore examples for managing cloud resources, monitoring systems, and automating infrastructure tasks

Each example includes sample configurations and common usage patterns to help you get started quickly.


### Optional Flags

- `--auto-approve-tools`: Automatically approve all tool executions
- `--always-show-full-output`: Always display complete tool outputs
- `--chat-history-dir PATH`: Directory to save chat history (default: `./chat_history`)

### Development Installation

Clone and install in editable mode:

```bash
git clone https://github.com/yourusername/mcp-repl.git
cd mcp-repl
uv venv
```

## Testing

Comprehensive integration tests are included to verify functionality:

Run all tests:

```bash
uv run pytest
```
