import json
import os
import subprocess
import time

from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "Modal CLI",
    instructions="You are a Modal CLI. You can list, stop, and get logs for Modal apps and containers.",
)


@mcp.tool()
def get_apps():
    """List Modal apps that are currently deployed/running or recently stopped."""
    try:
        result = subprocess.run(
            ["modal", "app", "list", "--json"],
            capture_output=True,
            text=True,
            check=True,
        )
        apps_data = json.loads(result.stdout)

        # Format the data for better readability
        formatted_apps = []
        for app in apps_data:
            formatted_app = {
                "app_id": app.get("App ID"),
                "description": app.get("Description"),
                "state": app.get("State"),
                "tasks": app.get("Tasks"),
                "created_at": app.get("Created at"),
                "stopped_at": app.get("Stopped at"),
            }
            formatted_apps.append(formatted_app)

        return formatted_apps
    except subprocess.CalledProcessError as e:
        return {"error": f"Failed to get apps: {e.stderr}"}
    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}


def read_process_output_with_timeout(command, timeout=3, max_lines=100):
    """Read output from a subprocess with timeout.

    Args:
        command: List containing the command and its arguments
        timeout: Maximum time to wait for output in seconds
        max_lines: Maximum number of lines to collect

    Returns:
        List of output lines
    """
    import queue
    import signal
    import subprocess
    import threading

    output_queue = queue.Queue()

    def read_output(pipe, queue):
        try:
            for line in iter(pipe.readline, ""):
                queue.put(line.strip())
                if queue.qsize() >= max_lines:
                    break
        except Exception as e:
            print(f"Error reading output: {e}")
            pass
        finally:
            pipe.close()

    # Start the process
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        preexec_fn=os.setsid
        if os.name != "nt"
        else None,  # Create a new process group on Unix
    )

    # Start thread to read stdout
    stdout_thread = threading.Thread(
        target=read_output, args=(process.stdout, output_queue)
    )
    stdout_thread.daemon = True
    stdout_thread.start()

    # Collect output with timeout
    start_time = time.time()
    output_lines = []

    while time.time() - start_time < timeout:
        try:
            # Try to get an item from the queue with a timeout
            line = output_queue.get(timeout=0.1)
            output_lines.append(line)
            if len(output_lines) >= max_lines:
                break
        except queue.Empty:
            # Small pause to prevent CPU spinning
            time.sleep(0.1)

    # Kill the process and all its children
    if os.name != "nt":  # Unix-like systems
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        except Exception as e:
            print(f"Error reading output: {e}")
            pass
    else:  # Windows
        try:
            process.terminate()
        except Exception as e:
            print(f"Error reading output: {e}")
            pass

    return output_lines


@mcp.tool()
def get_app_logs(app_id: str):
    """Show logs for a specific Modal app.

    Args:
        app_id: The app ID or name of the Modal app
    """
    try:
        # Use the helper function to get logs with timeout
        logs = read_process_output_with_timeout(
            command=["modal", "app", "logs", app_id], timeout=3, max_lines=100
        )

        # Add a message about the logs
        if logs:
            logs.append("(Output limited to most recent logs)")
        else:
            logs.append("No logs available in the collection timeframe")

        return {"logs": logs}
    except Exception as e:
        return {"error": f"Failed to get logs for app {app_id}: {str(e)}"}


@mcp.tool()
def list_containers():
    """List all Modal containers that are currently running."""
    try:
        # Use the helper function to get container list with timeout
        output_lines = read_process_output_with_timeout(
            command=["modal", "container", "list", "--json"], timeout=3, max_lines=200
        )

        # Parse the JSON output
        if output_lines:
            try:
                # Join all lines and parse as JSON
                json_data = json.loads("".join(output_lines))

                # Format the container data for better readability
                formatted_containers = []
                for container in json_data:
                    formatted_container = {
                        "container_id": container.get("Container ID"),
                        "image": container.get("Image"),
                        "function": container.get("Function"),
                        "app": container.get("App"),
                        "status": container.get("Status"),
                        "started_at": container.get("Started at"),
                    }
                    formatted_containers.append(formatted_container)

                return formatted_containers
            except json.JSONDecodeError:
                return {"error": "Failed to parse container list output as JSON"}
        else:
            return {"message": "No containers found or command timed out"}
    except Exception as e:
        return {"error": f"Failed to list containers: {str(e)}"}


@mcp.tool()
def get_container_logs(container_id: str):
    """Show logs for a specific Modal container.

    Args:
        container_id: The ID of the Modal container
    """
    try:
        # Use the helper function to get container logs with timeout
        logs = read_process_output_with_timeout(
            command=["modal", "container", "logs", container_id],
            timeout=3,
            max_lines=100,
        )

        # Add a message about the logs
        if logs:
            logs.append("(Output limited to most recent logs)")
        else:
            logs.append("No logs available in the collection timeframe")

        return {"logs": logs}
    except Exception as e:
        return {"error": f"Failed to get logs for container {container_id}: {str(e)}"}


@mcp.tool()
def stop_container(container_id: str):
    """Stop a currently-running Modal container.

    Args:
        container_id: The ID of the Modal container to stop
    """
    try:
        # Use the helper function with a shorter timeout since this should be quick
        output_lines = read_process_output_with_timeout(
            command=["modal", "container", "stop", container_id],
            timeout=5,
            max_lines=20,
        )

        # Check if the operation was successful
        success_message = f"Container {container_id} stopped successfully"
        for line in output_lines:
            if "success" in line.lower() or "stopped" in line.lower():
                return {"message": success_message, "details": output_lines}

        # If we didn't find a success message but got output
        if output_lines:
            return {
                "message": "Container stop command completed",
                "details": output_lines,
            }
        else:
            return {"error": "No output received from container stop command"}
    except Exception as e:
        return {"error": f"Failed to stop container {container_id}: {str(e)}"}


if __name__ == "__main__":
    mcp.run()
