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
    cmd = ["python", "-m", "src.mcp_repl.repl", "--config", config_path, "--auto-approve-tools"]
    
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
    time.sleep(3)
    
    # Test queries to send - only keep the one to get all users
    test_queries = [
        "get all users from my db",
        "quit"
    ]
    
    # Expected email addresses that should be in the response
    expected_emails = [
        "john.doe@example.com",
        "jane.smith@example.com",
        "bob.wilson@example.com",
        "alice.j@example.com",
        "mike.brown@example.com"
    ]
    
    # Track if all emails were found
    all_emails_found = False
    
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
            
            # Check if we've collected enough output
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
                
                # Check if emails are in the chat history
                chat_history_text = json.dumps(chat_data)
                emails_in_history = [email for email in expected_emails if email in chat_history_text]
                
                print(f"\nEmails found in chat history: {len(emails_in_history)} out of {len(expected_emails)}")
                if len(emails_in_history) != len(expected_emails):
                    missing_emails = set(expected_emails) - set(emails_in_history)
                    print(f"Missing emails in chat history: {missing_emails}")
                else:
                    print("All expected emails were found in the chat history!")
        except Exception as e:
            print(f"Error reading chat history: {e}")
    
    # Clean up
    process.terminate()
    process.wait()
    print("\nTest completed")

if __name__ == "__main__":
    test_mcp_repl() 