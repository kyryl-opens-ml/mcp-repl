
## Infrastructure Example

This example demonstrates how you can:

- Manage Kubernetes resources directly (pods, deployments, services, jobs)
- Interact with Helm to manage releases and charts
- Control and monitor Modal apps and containers

### Key Features

- Natural language management of Kubernetes resources
- Helm chart installation, upgrade, and management through intuitive commands
- Modal CLI integration for managing apps and containers seamlessly
- Unified REPL interface to interact with Kubernetes, Helm, and Modal simultaneously

### Running the Example

Setup infrastructure (requires `kubectl`, `helm`, and `modal` CLI):

```bash
bash examples/infra/setup.sh
```

Install infrastructure related dependencies:

```bash
uv add mcp-repl['infra']
```

Start the REPL:

```bash
uv run mcp-repl --config examples/infra/config.json --auto-approve-tools
```

### Sample Queries

You can perform operations like:

- "List all pods"
- "Deploy a new nginx service with 3 replicas"
- "Install the prometheus chart with custom values"
- "Scale the auth deployment to 5 replicas"
- "Show logs for the api pod"