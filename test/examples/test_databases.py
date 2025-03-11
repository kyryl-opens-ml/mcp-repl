import json
import os
import subprocess
import time
from pathlib import Path

import pytest


@pytest.fixture
def config_path():
    """Fixture to ensure the config file exists."""
    path = "./examples/databases/config.json"
    if not os.path.exists(path):
        pytest.skip(f"Config file not found at {path}")
    return path


@pytest.fixture
def chat_history_dir():
    """Fixture to set up the chat history directory."""
    os.makedirs("chat_history", exist_ok=True)
    return "chat_history"


@pytest.fixture
def mcp_process(config_path, chat_history_dir):
    """Fixture to start and stop the MCP REPL process."""
    cmd = [
        "python",
        "-m",
        "src.mcp_repl.repl",
        "--config",
        config_path,
        "--auto-approve-tools",
        "--always-show-full-output",
    ]

    process = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        universal_newlines=True,
    )

    time.sleep(5)

    yield process

    process.terminate()
    process.wait(timeout=5)


def test_mcp_repl_databases(mcp_process, chat_history_dir):
    """
    Test the MCP REPL application by running it as a subprocess and interacting with it.
    """
    process = mcp_process

    test_queries = ["find all tables in posgress and mysql", "q!"]

    for query in test_queries:
        process.stdin.write(f"{query}\n")
        process.stdin.flush()

        time.sleep(60)

        output = ""
        while process.stdout.readable() and not process.stdout.closed:
            try:
                line = process.stdout.readline()
                if not line:
                    break
                output += line
            except Exception as e:
                print(f"Error reading output: {e}")
                break

            if len(output) > 5000 or "Query ❯" in line:
                break

    chat_files = list(Path(chat_history_dir).glob("*.json"))
    assert chat_files, "No chat history files were created"

    latest_chat = max(chat_files, key=os.path.getctime)

    with open(latest_chat, "r") as f:
        chat_data = json.load(f)
        print("\nchat_data")
        print(chat_data)
        print("\nchat_data")
        assert len(chat_data) > 0, "Chat history is empty"

        # Check if expected tables are in the chat history
        chat_history_text = json.dumps(chat_data)
        expected_tables = [
            "customers",
            "employees",
            "inventory",
            "orders",
            "products",
            "users",
            "posts",
            "comments",
            "categories",
            "tags",
        ]
        tables_in_history = [
            table for table in expected_tables if table in chat_history_text
        ]

        missing_tables = set(expected_tables) - set(tables_in_history)
        assert not missing_tables, f"Missing tables in chat history: {missing_tables}"
