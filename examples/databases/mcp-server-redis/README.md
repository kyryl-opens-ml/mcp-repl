# mcp-server-redis: A Redis MCP Server

> The [Model Context Protocol (MCP)](https://modelcontextprotocol.io/introduction) is an open protocol that enables seamless integration between LLM applications and external data sources and tools. Whether you're building an AI-powered IDE, enhancing a chat interface, or creating custom AI workflows, MCP provides a standardized way to connect LLMs with the context they need.

This repository is an example of how to create an MCP server for managing Redis data.

[![PyPI version](https://badge.fury.io/py/mcp-server-redis.svg)](https://pypi.org/project/mcp-server-redis/)

## Overview

A Model Context Protocol server for interacting with Redis. It provides tools for setting, retrieving, listing, and deleting keys in Redis.

## Components

### Tools

The server implements the following tools:

- `set_value`: Set a specified key to a given value
  - Takes a `key` (string) and a `value` (string)
  - Returns a confirmation message upon success

- `get_value`: Retrieve the value of a specified key
  - Takes a `key` (string)
  - Returns the value as a string, or `None` if the key does not exist

- `list_keys`: List Redis keys matching a given pattern
  - Takes a `pattern` (default: "*")
  - Returns a list of matching keys

- `delete_key`: Delete a specified key
  - Takes a `key` (string)
  - Returns the number of keys deleted (0 or 1)

## Configuration

The server connects to Redis using the following environment variables (all are required):

- `REDIS_HOST`: Redis host  
- `REDIS_PORT`: Redis port  
- `REDIS_DB`: Redis database number  
- `REDIS_PASSWORD`: Redis password  

If any of these variables are missing, the server will raise an error during startup. Make sure to set each of these before running the server.

## Quickstart

#### Claude Desktop

On MacOS: `~/Library/Application\ Support/Claude/claude_desktop_config.json`  
On Windows: `%APPDATA%/Claude/claude_desktop_config.json`

```json
{
  "redis": {
    "command": "uvx",
    "args": [
      "mcp-server-redis"
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
npx @modelcontextprotocol/inspector uv --directory $(PWD) run mcp-server-redis
```

Upon launching, the Inspector will display a URL that you can access in your browser to begin debugging.