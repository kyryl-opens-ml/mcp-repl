import os
import subprocess
import time
import json
from pathlib import Path

def test_mcp_repl():
    """
    Test the MCP REPL application by running it as a subprocess and interacting with it.
    """
    # Ensure the config file exists
    config_path = "./examples/databases/config.json"
    if not os.path.exists(config_path):
        print(f"Error: Config file not found at {config_path}")
        return False
    
    # Create chat_history directory if it doesn't exist
    os.makedirs("chat_history", exist_ok=True)
    
    # Start the REPL process
    cmd = ["python", "-m", "src.mcp_repl.repl", "--config", config_path, "--auto-approve-tools", "--always-show-full-output"]
    
    # Use popen to create a subprocess we can write to and read from
    process = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        universal_newlines=True
    )
    
    print("Started MCP REPL process")
    
    # Wait for the application to initialize
    time.sleep(5)
    
    # Test queries to send - only keep the one to get all users
    test_queries = [
        "find all tables in posgress and mysql",
        "quit"
    ]
    
    # Send each query and read the response
    for query in test_queries:
        print(f"\n\nSending query: {query}")
        process.stdin.write(f"{query}\n")
        process.stdin.flush()
        
        # Give time for the application to process and respond
        time.sleep(5)
        
        # Read output
        output = ""
        while process.stdout.readable() and not process.stdout.closed:
            try:
                line = process.stdout.readline()
                if not line:
                    break
                output += line
                print(line, end="")
            except:
                break
            
            if len(output) > 500 or "Query ❯" in line:
                break
    # Check if any chat history files were created
    chat_files = list(Path("chat_history").glob("*.json"))
    if chat_files:
        print(f"\nChat history files created: {len(chat_files)}")
        # Examine the content of the latest chat history
        latest_chat = max(chat_files, key=os.path.getctime)
        print(latest_chat)
        try:
            with open(latest_chat, 'r') as f:
                chat_data = json.load(f)
                print(chat_data)
                print(f"Chat history contains {len(chat_data)} messages")
                
                # Check if expected tables are in the chat history
                chat_history_text = json.dumps(chat_data)
                expected_tables = [
                    "customers", "employees", "inventory", "orders", "products",
                    "users", "posts", "comments", "categories", "tags"
                ]
                tables_in_history = [table for table in expected_tables if table in chat_history_text]
                
                print(f"\nTables found in chat history: {len(tables_in_history)} out of {len(expected_tables)}")
                if len(tables_in_history) != len(expected_tables):
                    missing_tables = set(expected_tables) - set(tables_in_history)
                    print(f"Missing tables in chat history: {missing_tables}")
                else:
                    print("All expected tables were found in the chat history!")
        except Exception as e:
            print(f"Error reading chat history: {e}")
    
    # Clean up
    process.terminate()
    process.wait()
    print("\nTest completed")

if __name__ == "__main__":
    test_mcp_repl() 