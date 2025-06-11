# mcp-server-mysql: A MySQL MCP Server

> The [Model Context Protocol (MCP)](https://modelcontextprotocol.io/introduction) is an open protocol that enables seamless integration between LLM applications and external data sources and tools. Whether you're building an AI-powered IDE, enhancing a chat interface, or creating custom AI workflows, MCP provides a standardized way to connect LLMs with the context they need.

This repository is an example of how to create an MCP server for managing MySQL databases.

[![PyPI version](https://badge.fury.io/py/mcp-server-mysql.svg)](https://pypi.org/project/mcp-server-mysql/)

## Overview

A Model Context Protocol server for interacting with a MySQL database. It provides tools for executing queries, creating and describing tables, inserting and fetching data, as well as listing existing tables.

## Components

### Tools

The server implements the following tools:

#### Query Execution
- `execute_query`: Execute an arbitrary SQL query.
  - Takes a SQL string (`query`)
  - Returns query results for SELECT/SHOW/DESCRIBE, or a success message for other commands

#### Table Management
- `list_tables`: List all tables in the current database
  - Returns JSON array of table names

- `create_table`: Create a new table
  - Takes `name` (table name) and `schema` (column definitions)
  - Creates the specified table

- `describe_table`: Show the structure of a specific table
  - Takes `table` (name of the table)
  - Returns information about columns and data types

#### Data Manipulation
- `insert_data`: Insert new row into a table
  - Takes `table` (target table name) and `data` (dict of column values)
  - Inserts data into the specified table

- `fetch_data`: Fetch data by executing a SELECT query
  - Takes a SQL string (`query`)
  - Returns rows matching the query

## Configuration

The MCP server connects to a MySQL database using environment variables. You need to set the following environment variables before running the server:

- `MYSQL_HOST`: MySQL server hostname
- `MYSQL_PORT`: MySQL server port
- `MYSQL_USER`: MySQL username
- `MYSQL_PASSWORD`: MySQL password
- `MYSQL_DATABASE`: MySQL database name

These settings are loaded using Pydantic's BaseSettings, which will raise an error if the required environment variables are not set.

## Quickstart

#### Claude Desktop

On MacOS: `~/Library/Application\ Support/Claude/claude_desktop_config.json`  
On Windows: `%APPDATA%/Claude/claude_desktop_config.json`

```json
{
  "mysql": {
    "command": "uvx",
    "args": [
      "mcp-server-mysql"
    ]
  }
}
```

## Development

### Building and Publishing

To prepare the package for distribution:

1. Sync dependencies and update lockfile:
```bash
uv sync
```

2. Build package distributions:
```bash
uv build
```

This will create source and wheel distributions in the `dist/` directory.

3. Publish to PyPI:
```bash
uv publish
```

Note: You'll need to set PyPI credentials via environment variables or command flags:
- Token: `--token` or `UV_PUBLISH_TOKEN`
- Or username/password: `--username`/`UV_PUBLISH_USERNAME` and `--password`/`UV_PUBLISH_PASSWORD`

### Debugging

Since MCP servers run over stdio, debugging can be challenging. For the best debugging
experience, we strongly recommend using the [MCP Inspector](https://github.com/modelcontextprotocol/inspector).

You can launch the MCP Inspector via [`npm`](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm) with this command:
```bash
npx @modelcontextprotocol/inspector uv --directory $(PWD) run mcp-server-mysql
```

Upon launching, the Inspector will display a URL that you can access in your browser to begin debugging.