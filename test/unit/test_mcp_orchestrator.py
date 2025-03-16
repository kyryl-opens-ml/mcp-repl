from unittest.mock import AsyncMock, patch

import pytest

from mcp_repl.mcp_orchestrator import MCPOrchestrator, MCPServerConfig


@pytest.mark.asyncio
async def test_mcp_orchestrator_add_server():
    orchestrator = MCPOrchestrator()

    mock_connect_to_server = AsyncMock()
    with patch.object(orchestrator, "connect_to_server", mock_connect_to_server):
        server_config = MCPServerConfig(id="test_server", path="./test_server.py")
        await orchestrator.add_server(server_config)

        mock_connect_to_server.assert_awaited_once_with(
            "./test_server.py", "test_server"
        )


@pytest.mark.asyncio
async def test_mcp_orchestrator_remove_server():
    orchestrator = MCPOrchestrator()
    orchestrator.sessions = {
        "test_server": {
            "session": AsyncMock(),
            "tools": [],
            "server_info": {},
            "server_id": "test_server",
            "server_path": "./test_server.py",
        }
    }

    orchestrator._update_available_tools = AsyncMock()

    await orchestrator.remove_server("test_server")

    assert "test_server" not in orchestrator.sessions
    orchestrator._update_available_tools.assert_called_once()


@pytest.mark.asyncio
async def test_mcp_orchestrator_list_servers():
    orchestrator = MCPOrchestrator()
    orchestrator.sessions = {"server1": {}, "server2": {}}

    servers = orchestrator.list_servers()
    assert len(servers) == 2
    assert "server1" in servers
    assert "server2" in servers


@pytest.mark.asyncio
async def test_mcp_orchestrator_call_tool():
    orchestrator = MCPOrchestrator()
    mock_session = AsyncMock()
    mock_session.call_tool.return_value = "tool_result"

    orchestrator.sessions = {
        "server1": {
            "session": mock_session,
            "tools": [],
            "server_info": {},
            "server_id": "server1",
            "server_path": "./server1.py",
        }
    }
    orchestrator.tools = [("server1_tool1", "server1", "tool1")]

    result = await orchestrator.call_tool("server1_tool1", {"arg1": "value1"})

    mock_session.call_tool.assert_awaited_once_with("tool1", {"arg1": "value1"})
    assert result == "tool_result"


@pytest.mark.asyncio
async def test_mcp_orchestrator_call_tool_not_found():
    orchestrator = MCPOrchestrator()
    orchestrator.tools = []

    with pytest.raises(
        ValueError, match="Tool 'nonexistent_tool' not found in any connected server"
    ):
        await orchestrator.call_tool("nonexistent_tool", {})
