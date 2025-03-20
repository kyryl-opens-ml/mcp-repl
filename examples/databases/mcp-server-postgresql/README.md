# mcp-server-postgresql: A PostgreSQL MCP Server

> The [Model Context Protocol (MCP)](https://modelcontextprotocol.io/introduction) is an open protocol that enables seamless integration between LLM applications and external data sources and tools. Whether you're building an AI-powered IDE, enhancing a chat interface, or creating custom AI workflows, MCP provides a standardized way to connect LLMs with the context they need.

This repository is an example of how to create an MCP server for managing PostgreSQL databases.

[![PyPI version](https://badge.fury.io/py/mcp-server-postgresql.svg)](https://pypi.org/project/mcp-server-postgresql/)

## Overview

A Model Context Protocol server for interacting with PostgreSQL. It provides tools for executing queries, creating tables, inserting rows of data, and retrieving results.

## Components

### Tools

The server implements the following tools:

- `execute_query`: Execute an arbitrary SQL query
  - Takes a `query` string
  - Returns results for SELECT-like statements, or a success message for others

- `create_table`: Create a new table
  - Takes a `name` and a `schema` (column definitions)
  - Creates the specified table

- `insert_data`: Insert a row of data into a table
  - Takes a `table` name and a `data` dict of column values
  - Inserts the specified row

- `fetch_data`: Fetch data by executing a SELECT query
  - Takes a `query` string
  - Returns matching rows as a result set

## Configuration

The server connects to PostgreSQL using the following environment variables (all are required):

- `PG_HOST`: PostgreSQL host  
- `PG_PORT`: PostgreSQL port  
- `PG_USER`: PostgreSQL user  
- `PG_PASSWORD`: PostgreSQL password  
- `PG_DATABASE`: PostgreSQL database name  

If any of these variables are missing, the server will raise an error during startup. Make sure to set each of these before running the server.

## Quickstart

#### Claude Desktop

On MacOS: `~/Library/Application\ Support/Claude/claude_desktop_config.json`  
On Windows: `%APPDATA%/Claude/claude_desktop_config.json`

```json
{
  "postgresql": {
    "command": "uvx",
    "args": [
      "mcp-server-postgresql"
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
npx @modelcontextprotocol/inspector uv --directory $(PWD) run mcp-server-postgresql
```

Upon launching, the Inspector will display a URL that you can access in your browser to begin debugging.
