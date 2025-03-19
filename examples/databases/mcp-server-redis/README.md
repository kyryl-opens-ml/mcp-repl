# mcp-server-k8s: A Kubernetes MCP Server

> The [Model Context Protocol (MCP)](https://modelcontextprotocol.io/introduction) is an open protocol that enables seamless integration between LLM applications and external data sources and tools. Whether you're building an AI-powered IDE, enhancing a chat interface, or creating custom AI workflows, MCP provides a standardized way to connect LLMs with the context they need.

This repository is an example of how to create an MCP server for managing Kubernetes resources.

## Overview

A Model Context Protocol server for interacting with Kubernetes clusters. It provides tools for creating, reading, updating, and deleting Kubernetes resources, as well as observability features like log retrieval and resource inspection.

## Components

### Tools

The server implements the following tools:

#### Resource Management
- `get_resources`: Retrieve Kubernetes resources
  - Takes `resource_type` (pod, deployment, service, job), `namespace` (default: "default"), and optional `name`
  - Returns JSON-formatted resource information

- `create_resource`: Create new Kubernetes resources
  - Takes `resource_type`, `namespace`, and `manifest` (JSON string)
  - Creates the specified resource in the cluster

- `delete_resource`: Remove Kubernetes resources
  - Takes `resource_type`, `name`, and `namespace` (default: "default")
  - Deletes the specified resource

#### Observability
- `get_pod_logs`: Retrieve container logs
  - Takes `pod_name`, `namespace` (default: "default"), optional `container`, and `tail_lines` (default: 100)
  - Returns pod logs

- `describe_resource`: Get detailed resource information
  - Takes `resource_type`, `name`, and `namespace` (default: "default")
  - Returns detailed JSON description of the resource

- `get_namespaces`: List all namespaces
  - Returns JSON array of namespace information

#### Advanced Features
- `apply_manifest_from_url`: Apply Kubernetes manifests from URLs
  - Takes `url` and optional `namespace` (default: "default")
  - Downloads and applies the manifest file

## Configuration

The server automatically configures Kubernetes client using:
1. In-cluster configuration (when running inside Kubernetes)
2. Local kubeconfig file (when running locally)

## Quickstart

#### Claude Desktop

On MacOS: `~/Library/Application\ Support/Claude/claude_desktop_config.json`
On Windows: `%APPDATA%/Claude/claude_desktop_config.json`

```json
{
  "kubernetes": {
    "command": "uvx",
    "args": [
      "mcp-server-k8s"
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
npx @modelcontextprotocol/inspector uv --directory $(PWD) run mcp-server-k8s
```

Upon launching, the Inspector will display a URL that you can access in your browser to begin debugging.