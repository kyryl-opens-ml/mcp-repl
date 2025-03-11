import asyncio
import json
from pathlib import Path

import pytest

from src.mcp_repl.mcp_orchestrator import MCPOrchestrator, MCPServerConfig


@pytest.fixture
def config_path(tmp_path):
    """Fixture to create a temporary config file for testing."""
    config_content = [{"path": "./examples/infra/k8s_server.py", "id": "k8s_server"}]

    config_file = tmp_path / "test_config.json"
    config_file.write_text(json.dumps(config_content))

    return str(config_file)


@pytest.mark.asyncio
async def test_orchestrator_from_config_available_tools(config_path):
    """Test creating an orchestrator from config file."""
    orchestrator = await MCPOrchestrator.from_config(config_path)

    expected_tools_file = Path("./test/integration/data/available_tools.json")
    with open(expected_tools_file, "r") as f:
        expected_tools = json.load(f)

    assert len(orchestrator.available_tools) > 0, "No tools were loaded"
    assert orchestrator.available_tools == expected_tools


@pytest.mark.asyncio
async def test_orchestrator_from_config_call_tool(config_path):
    """Test creating an orchestrator from config file."""
    orchestrator = await MCPOrchestrator.from_config(config_path)

    result = await orchestrator.call_tool(
        "k8s_server_delete_resource",
        {
            "resource_type": "deployment",
            "name": "nginx-deployment",
            "namespace": "default",
        },
    )
    assert not result.isError

    await asyncio.sleep(2)

    result = await orchestrator.call_tool(
        "k8s_server_apply_manifest_from_url",
        {
            "url": "https://raw.githubusercontent.com/kubernetes/website/main/content/en/examples/controllers/nginx-deployment.yaml"
        },
    )
    assert not result.isError


@pytest.mark.asyncio
async def test_orchestrator_add_and_remove_servers(config_path):
    """Test adding and removing servers from the orchestrator."""
    orchestrator = await MCPOrchestrator.from_server_configs(
        [MCPServerConfig(path="./examples/infra/k8s_server.py", id="k8s_server_1")]
    )

    assert len(orchestrator.list_servers()) == 1
    assert len(orchestrator.available_tools) == 7

    new_server = MCPServerConfig(
        path="./examples/infra/helm_server.py", id="helm_server_1"
    )
    await orchestrator.add_server(new_server)

    assert len(orchestrator.list_servers()) == 2
    assert len(orchestrator.available_tools) == 15

    await orchestrator.remove_server("helm_server_1")
    await orchestrator.remove_server("k8s_server_1")

    assert len(orchestrator.list_servers()) == 0
    assert len(orchestrator.available_tools) == 0
