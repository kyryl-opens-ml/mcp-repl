import os
import pytest
import asyncio
from pathlib import Path
from src.mcp_repl.mcp_orchestrator import MCPOrchestrator, MCPServerConfig
import json


@pytest.fixture
def config_path(tmp_path):
    """Fixture to create a temporary config file for testing."""
    config_content =  [
            {
                "path": "./examples/infra/k8s_server.py",
                "name": "Test K8s Server",
                "description": "Test server for K8s"
            }
        ]
    
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
    
    result = await orchestrator.call_tool("k8s_server_delete_resource", {"resource_type": "deployment", "name": "nginx-deployment", "namespace": "default"})
    assert not result.isError

    await asyncio.sleep(2)

    result = await orchestrator.call_tool("k8s_server_apply_manifest_from_url", {"url": "https://raw.githubusercontent.com/kubernetes/website/main/content/en/examples/controllers/nginx-deployment.yaml"})
    assert not result.isError

# @pytest.mark.asyncio
# async def test_add_and_remove_mcp():
#     """Test adding and removing an MCP server."""
#     # Create a minimal orchestrator with no initial servers
#     orchestrator = MCPOrchestrator([])
    
#     try:
#         # Create a test server config
#         test_server = MCPServerConfig(
#             path=str(Path("./examples/infra/k8s_server.py").resolve()),
#             name="Test K8s Server",
#             description="Test server for K8s"
#         )
        
#         # Add the server
#         tools = await orchestrator.add_mcp(test_server)
        
#         # Verify server was added and connected
#         assert test_server.path in orchestrator.connected_servers
#         assert len(orchestrator.available_tools) > 0
#         assert len(tools) > 0
        
#         # Remove the server
#         await orchestrator.remove_mcp(test_server.path)
        
#         # Verify server was removed
#         assert test_server.path not in orchestrator.connected_servers
#         assert len(orchestrator.available_tools) == 0
#     finally:
#         await orchestrator.cleanup()


# @pytest.mark.asyncio
# async def test_call_tool(config_path):
#     """Test calling a tool from a connected server."""
#     orchestrator = await MCPOrchestrator.from_config(config_path)
    
#     try:
#         # Verify we have tools available
#         assert len(orchestrator.tools) > 0
        
#         # Get the first tool for testing
#         tool_name, _, _ = orchestrator.tools[0]
        
#         # This is a basic test that just verifies the call doesn't raise an exception
#         # In a real test, you would use a mock server or test-specific tool with known behavior
#         with pytest.raises(Exception):
#             # We expect this to fail since we're not providing valid arguments
#             # but it should fail in a controlled way, not due to connection issues
#             await orchestrator.call_tool(tool_name, {})
#     finally:
#         await orchestrator.cleanup()
