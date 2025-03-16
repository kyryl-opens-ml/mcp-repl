import os
import shutil
import subprocess
import sys
import tempfile
from typing import Optional

from kubernetes import client, config
from mcp.server.fastmcp import FastMCP

# Check Kubernetes connectivity
try:
    config.load_incluster_config()
except config.ConfigException:
    try:
        config.load_kube_config()
    except Exception as e:
        sys.exit(f"ERROR: Cannot connect to Kubernetes: {str(e)}")

# Check if Helm is installed
if not shutil.which("helm"):
    sys.exit("ERROR: Helm is not installed or not in PATH.")

# Initialize Kubernetes clients and MCP server
mcp = FastMCP(
    "HELM MCP",
    instructions="You are a Helm manager. You can list, install, upgrade, uninstall, and get values for Helm releases.",
)
core_v1 = client.CoreV1Api()
apps_v1 = client.AppsV1Api()
batch_v1 = client.BatchV1Api()


@mcp.tool()
def helm_list_releases(namespace: Optional[str] = None) -> str:
    """
    List Helm releases in the cluster or in a specific namespace.

    Args:
        namespace: Optional namespace to filter releases

    Returns:
        JSON string with Helm releases information
    """
    try:
        cmd = ["helm", "list", "--output", "json"]
        if namespace:
            cmd.extend(["--namespace", namespace])

        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error listing Helm releases: {e.stderr}"
    except Exception as e:
        return f"Error listing Helm releases: {str(e)}"


@mcp.tool()
def helm_install_release(
    release_name: str,
    chart: str,
    namespace: str = "default",
    values: Optional[str] = None,
    version: Optional[str] = None,
    repo: Optional[str] = None,
) -> str:
    """
    Install a Helm chart.

    Args:
        release_name: Name for the release
        chart: Chart name or local path
        namespace: Kubernetes namespace
        values: Optional YAML string with values to override
        version: Optional specific chart version
        repo: Optional chart repository URL

    Returns:
        Result of the installation
    """
    try:
        cmd = ["helm", "install", release_name, chart, "--namespace", namespace]

        # Add repository if specified
        if repo:
            repo_name = f"temp-{release_name}"
            add_repo_cmd = ["helm", "repo", "add", repo_name, repo]
            subprocess.run(add_repo_cmd, capture_output=True, check=True)
            cmd[2] = f"{repo_name}/{chart}"

        # Add version if specified
        if version:
            cmd.extend(["--version", version])

        # Create values file if provided
        if values:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".yaml", delete=False
            ) as temp:
                temp.write(values)
                temp_filename = temp.name

            cmd.extend(["-f", temp_filename])

        result = subprocess.run(cmd, capture_output=True, text=True)

        # Clean up temporary files
        if values:
            os.unlink(temp_filename)

        if result.returncode != 0:
            return f"Error installing Helm chart: {result.stderr}"
        return result.stdout
    except Exception as e:
        return f"Error installing Helm chart: {str(e)}"


@mcp.tool()
def helm_upgrade_release(
    release_name: str,
    chart: str,
    namespace: str = "default",
    values: Optional[str] = None,
    version: Optional[str] = None,
) -> str:
    """
    Upgrade a Helm release.

    Args:
        release_name: Name of the release to upgrade
        chart: Chart name or local path
        namespace: Kubernetes namespace
        values: Optional YAML string with values to override
        version: Optional specific chart version

    Returns:
        Result of the upgrade
    """
    try:
        cmd = ["helm", "upgrade", release_name, chart, "--namespace", namespace]

        # Add version if specified
        if version:
            cmd.extend(["--version", version])

        # Create values file if provided
        if values:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".yaml", delete=False
            ) as temp:
                temp.write(values)
                temp_filename = temp.name

            cmd.extend(["-f", temp_filename])

        result = subprocess.run(cmd, capture_output=True, text=True)

        # Clean up temporary files
        if values:
            os.unlink(temp_filename)

        if result.returncode != 0:
            return f"Error upgrading Helm release: {result.stderr}"
        return result.stdout
    except Exception as e:
        return f"Error upgrading Helm release: {str(e)}"


@mcp.tool()
def helm_uninstall_release(release_name: str, namespace: str = "default") -> str:
    """
    Uninstall a Helm release.

    Args:
        release_name: Name of the release to uninstall
        namespace: Kubernetes namespace

    Returns:
        Result of the uninstallation
    """
    try:
        cmd = ["helm", "uninstall", release_name, "--namespace", namespace]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            return f"Error uninstalling Helm release: {result.stderr}"
        return result.stdout
    except Exception as e:
        return f"Error uninstalling Helm release: {str(e)}"


@mcp.tool()
def helm_get_values(
    release_name: str, namespace: str = "default", all_values: bool = False
) -> str:
    """
    Get values for a Helm release.

    Args:
        release_name: Name of the release
        namespace: Kubernetes namespace
        all_values: Whether to get all values (including defaults)

    Returns:
        YAML string with release values
    """
    try:
        cmd = [
            "helm",
            "get",
            "values",
            release_name,
            "--namespace",
            namespace,
            "--output",
            "yaml",
        ]

        if all_values:
            cmd.append("--all")

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            return f"Error getting Helm release values: {result.stderr}"
        return result.stdout
    except Exception as e:
        return f"Error getting Helm release values: {str(e)}"


@mcp.tool()
def helm_repo_add(repo_name: str, repo_url: str) -> str:
    """
    Add a Helm chart repository.

    Args:
        repo_name: Name for the repository
        repo_url: URL of the repository

    Returns:
        Result of the operation
    """
    try:
        cmd = ["helm", "repo", "add", repo_name, repo_url]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            return f"Error adding Helm repository: {result.stderr}"

        # Update repos after adding
        update_cmd = ["helm", "repo", "update"]
        update_result = subprocess.run(update_cmd, capture_output=True, text=True)

        if update_result.returncode != 0:
            return f"Repository added but update failed: {update_result.stderr}"

        return f"Repository {repo_name} added and updated successfully"
    except Exception as e:
        return f"Error adding Helm repository: {str(e)}"


@mcp.tool()
def helm_search_chart(keyword: str, repo: Optional[str] = None) -> str:
    """
    Search for Helm charts.

    Args:
        keyword: Search term
        repo: Optional repository to search in

    Returns:
        JSON string with search results
    """
    try:
        cmd = ["helm", "search", "repo", keyword, "--output", "json"]

        if repo:
            # Filter by repo in the search term
            cmd[2] = f"{repo}/{keyword}"

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            return f"Error searching for Helm charts: {result.stderr}"
        return result.stdout
    except Exception as e:
        return f"Error searching for Helm charts: {str(e)}"


@mcp.tool()
def apply_manifest_from_url(url: str, namespace: str = "default") -> str:
    """
    Apply a Kubernetes manifest from a URL using the Kubernetes client.

    Args:
        url: URL of the manifest file
        namespace: Kubernetes namespace to apply the manifest to

    Returns:
        Result of the apply operation
    """
    try:
        import tempfile

        import requests

        # Verify URL is accessible and download content
        response = requests.get(url)
        if response.status_code >= 400:
            return f"Error: Unable to access URL {url}, status code: {response.status_code}"

        # Save content to a temporary file
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as temp_file:
            temp_file.write(response.content)
            temp_path = temp_file.name

        try:
            # Use the kubernetes-client utility to create from yaml
            from kubernetes.utils import create_from_yaml

            api_client = client.ApiClient()
            created_objects = create_from_yaml(
                k8s_client=api_client,
                yaml_file=temp_path,
                verbose=False,
                namespace=namespace,
            )

            # Format the response
            results = []
            for obj in created_objects:
                kind = obj.kind
                name = obj.metadata.name
                results.append(f"{kind}/{name} created or configured")

            return (
                "\n".join(results) if results else "No resources created or configured"
            )
        finally:
            # Clean up the temporary file
            os.unlink(temp_path)

    except Exception as e:
        return f"Error applying manifest from URL: {str(e)}"


if __name__ == "__main__":
    mcp.run()
