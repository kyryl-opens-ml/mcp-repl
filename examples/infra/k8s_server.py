from mcp.server.fastmcp import FastMCP
from kubernetes import client, config
import json
from typing import Optional, List, Dict, Any
import subprocess
import tempfile
import os
import yaml
import sys
import shutil
import requests
import kubernetes.utils

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
mcp = FastMCP("Kubernetes Manager")
core_v1 = client.CoreV1Api()
apps_v1 = client.AppsV1Api()
batch_v1 = client.BatchV1Api()

@mcp.tool()
def get_resources(
    resource_type: str, namespace: str = "default", name: Optional[str] = None
) -> str:
    """
    Get Kubernetes resources of specified type.

    Args:
        resource_type: Type of resource (pod, deployment, service, job)
        namespace: Kubernetes namespace
        name: Optional specific resource name

    Returns:
        JSON string with resource information
    """
    try:
        if resource_type.lower() == "pod":
            if name:
                result = core_v1.read_namespaced_pod(name, namespace)
                return json.dumps(client.ApiClient().sanitize_for_serialization(result))
            else:
                result = core_v1.list_namespaced_pod(namespace)
                items = [
                    {"name": i.metadata.name, "status": i.status.phase}
                    for i in result.items
                ]
                return json.dumps(items)

        elif resource_type.lower() == "deployment":
            if name:
                result = apps_v1.read_namespaced_deployment(name, namespace)
                return json.dumps(client.ApiClient().sanitize_for_serialization(result))
            else:
                result = apps_v1.list_namespaced_deployment(namespace)
                items = [
                    {"name": i.metadata.name, "replicas": i.spec.replicas}
                    for i in result.items
                ]
                return json.dumps(items)

        elif resource_type.lower() == "service":
            if name:
                result = core_v1.read_namespaced_service(name, namespace)
                return json.dumps(client.ApiClient().sanitize_for_serialization(result))
            else:
                result = core_v1.list_namespaced_service(namespace)
                items = [
                    {
                        "name": i.metadata.name,
                        "type": i.spec.type,
                        "cluster_ip": i.spec.cluster_ip,
                    }
                    for i in result.items
                ]
                return json.dumps(items)

        elif resource_type.lower() == "job":
            if name:
                result = batch_v1.read_namespaced_job(name, namespace)
                return json.dumps(client.ApiClient().sanitize_for_serialization(result))
            else:
                result = batch_v1.list_namespaced_job(namespace)
                items = [
                    {"name": i.metadata.name, "completions": i.spec.completions}
                    for i in result.items
                ]
                return json.dumps(items)
        else:
            return f"Unsupported resource type: {resource_type}"
    except Exception as e:
        return f"Error retrieving {resource_type}: {str(e)}"


@mcp.tool()
def create_resource(resource_type: str, namespace: str, manifest: str) -> str:
    """
    Create a Kubernetes resource from a JSON manifest.

    Args:
        resource_type: Type of resource (pod, deployment, service, job)
        namespace: Kubernetes namespace
        manifest: JSON string with resource definition

    Returns:
        Result of creation operation
    """
    try:
        manifest_dict = json.loads(manifest)
        if resource_type.lower() == "pod":
            result = core_v1.create_namespaced_pod(namespace, manifest_dict)
            return f"Pod {result.metadata.name} created"

        elif resource_type.lower() == "deployment":
            result = apps_v1.create_namespaced_deployment(namespace, manifest_dict)
            return f"Deployment {result.metadata.name} created"

        elif resource_type.lower() == "service":
            result = core_v1.create_namespaced_service(namespace, manifest_dict)
            return f"Service {result.metadata.name} created"

        elif resource_type.lower() == "job":
            result = batch_v1.create_namespaced_job(namespace, manifest_dict)
            return f"Job {result.metadata.name} created"
        else:
            return f"Unsupported resource type: {resource_type}"
    except Exception as e:
        return f"Error creating {resource_type}: {str(e)}"


@mcp.tool()
def delete_resource(resource_type: str, name: str, namespace: str = "default") -> str:
    """
    Delete a Kubernetes resource.

    Args:
        resource_type: Type of resource (pod, deployment, service, job)
        name: Name of the resource to delete
        namespace: Kubernetes namespace

    Returns:
        Result of deletion operation
    """
    try:
        if resource_type.lower() == "pod":
            core_v1.delete_namespaced_pod(name, namespace)
            return f"Pod {name} deleted"

        elif resource_type.lower() == "deployment":
            apps_v1.delete_namespaced_deployment(name, namespace)
            return f"Deployment {name} deleted"

        elif resource_type.lower() == "service":
            core_v1.delete_namespaced_service(name, namespace)
            return f"Service {name} deleted"

        elif resource_type.lower() == "job":
            batch_v1.delete_namespaced_job(name, namespace)
            return f"Job {name} deleted"
        else:
            return f"Unsupported resource type: {resource_type}"
    except Exception as e:
        return f"Error deleting {resource_type}: {str(e)}"


# ---- Observability ----


@mcp.tool()
def get_pod_logs(
    pod_name: str,
    namespace: str = "default",
    container: Optional[str] = None,
    tail_lines: int = 100,
) -> str:
    """
    Get logs from a pod.

    Args:
        pod_name: Name of the pod
        namespace: Kubernetes namespace
        container: Optional container name (if pod has multiple containers)
        tail_lines: Number of lines to return from the end

    Returns:
        Pod logs
    """
    try:
        return core_v1.read_namespaced_pod_log(
            name=pod_name,
            namespace=namespace,
            container=container,
            tail_lines=tail_lines,
        )
    except Exception as e:
        return f"Error getting logs for pod {pod_name}: {str(e)}"


@mcp.tool()
def describe_resource(resource_type: str, name: str, namespace: str = "default") -> str:
    """
    Get detailed information about a Kubernetes resource.

    Args:
        resource_type: Type of resource (pod, deployment, service, job)
        name: Name of the resource
        namespace: Kubernetes namespace

    Returns:
        Detailed description of the resource
    """
    try:
        if resource_type.lower() == "pod":
            result = core_v1.read_namespaced_pod(name, namespace)
        elif resource_type.lower() == "deployment":
            result = apps_v1.read_namespaced_deployment(name, namespace)
        elif resource_type.lower() == "service":
            result = core_v1.read_namespaced_service(name, namespace)
        elif resource_type.lower() == "job":
            result = batch_v1.read_namespaced_job(name, namespace)
        else:
            return f"Unsupported resource type: {resource_type}"

        # Convert to dict and then to formatted JSON
        resource_dict = client.ApiClient().sanitize_for_serialization(result)
        return json.dumps(resource_dict, indent=2)
    except Exception as e:
        return f"Error describing {resource_type} {name}: {str(e)}"


@mcp.tool()
def get_namespaces() -> str:
    """
    List all namespaces in the cluster.

    Returns:
        JSON string with namespace information
    """
    try:
        result = core_v1.list_namespace()
        namespaces = [
            {"name": item.metadata.name, "status": item.status.phase}
            for item in result.items
        ]
        return json.dumps(namespaces)
    except Exception as e:
        return f"Error listing namespaces: {str(e)}"


# ---- Helm Operations ----

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
    repo: Optional[str] = None
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
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp:
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
    version: Optional[str] = None
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
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp:
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
def helm_get_values(release_name: str, namespace: str = "default", all_values: bool = False) -> str:
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
        cmd = ["helm", "get", "values", release_name, "--namespace", namespace, "--output", "yaml"]
        
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
        import requests
        import tempfile
        
        # Verify URL is accessible and download content
        response = requests.get(url)
        if response.status_code >= 400:
            return f"Error: Unable to access URL {url}, status code: {response.status_code}"
        
        # Save content to a temporary file
        with tempfile.NamedTemporaryFile(suffix='.yaml', delete=False) as temp_file:
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
                namespace=namespace
            )
            
            # Format the response
            results = []
            for obj in created_objects:
                kind = obj.kind
                name = obj.metadata.name
                results.append(f"{kind}/{name} created or configured")
            
            return "\n".join(results) if results else "No resources created or configured"
        finally:
            # Clean up the temporary file
            os.unlink(temp_path)
            
    except Exception as e:
        return f"Error applying manifest from URL: {str(e)}"

if __name__ == "__main__":
    mcp.run()
