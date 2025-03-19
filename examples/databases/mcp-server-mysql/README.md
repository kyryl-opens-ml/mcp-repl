# mcp-server-mysql: A MySQL MCP Server

> The [Model Context Protocol (MCP)](https://modelcontextprotocol.io/introduction) is an open protocol that enables seamless integration between LLM applications and external data sources and tools. Whether you're building an AI-powered IDE, enhancing a chat interface, or creating custom AI workflows, MCP provides a standardized way to connect LLMs with the context they need.

This repository is an example of how to create an MCP server for managing MySQL databases.

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

The MCP server automatically connects to a local or remote MySQL database using parameters configured in the code. By default, it looks for environment variables or uses the sample credentials in the server code:
- Host: localhost
- Port: 3306
- User: root
- Password: mysql
- Database: mydatabase

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