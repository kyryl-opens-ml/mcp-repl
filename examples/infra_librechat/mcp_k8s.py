from kubernetes import client, config, utils
from typing import Optional
from kubernetes.dynamic import DynamicClient
from mcp.server.fastmcp import FastMCP

class KubernetesManager:
    """
    KubernetesManager provides methods to manage Kubernetes resources such as deployments,
    services, pods, and allows applying YAML configurations directly.
    """

    def __init__(self, namespace: str = "default") -> None:
        """
        Initializes the KubernetesManager with the specified namespace.

        Args:
            namespace (str): Kubernetes namespace to operate in.
        """
        self.namespace = namespace
        self.load_kube_config()

    def load_kube_config(self) -> None:
        """
        Loads Kubernetes configuration from the default kubeconfig file or from within a cluster.
        """
        try:
            config.load_kube_config()
        except config.ConfigException:
            config.load_incluster_config()

    def patch_resource(self, api_version: str, kind: str, name: str, patch_body: dict) -> str:
        """
        Patches a Kubernetes resource with provided patch body.

        Args:
            api_version (str): API version of the resource (e.g., "apps/v1").
            kind (str): Kind of the resource (e.g., "Deployment", "Service").
            name (str): Name of the resource to patch.
            patch_body (dict): JSON patch body defining the changes.
            
        Returns:
            str: Success message.
        """
        api_client = client.ApiClient()
        dynamic_client = DynamicClient(api_client)
        resource = dynamic_client.resources.get(api_version=api_version, kind=kind)
        resource.patch(name=name, namespace=self.namespace, body=patch_body)
        message = f"{kind} '{name}' patched successfully."
        print(message)
        return message

    def apply_yaml(self, yaml_file_path: str) -> str:
        """
        Applies a YAML configuration to the Kubernetes cluster.

        Args:
            yaml_file_path (str): Path to the YAML file to apply.
            
        Returns:
            str: Success message.
        """
        api_client = client.ApiClient()
        utils.create_from_yaml(api_client, yaml_file_path, namespace=self.namespace)
        message = f"YAML '{yaml_file_path}' applied successfully."
        print(message)
        return message

    def get_pod_logs(self, pod_name: str, container: Optional[str] = None) -> str:
        """
        Retrieves logs from a specified pod.

        Args:
            pod_name (str): Name of the pod.
            container (Optional[str]): Specific container name within the pod, if applicable.

        Returns:
            str: Pod logs.
        """
        core_v1 = client.CoreV1Api()
        logs = core_v1.read_namespaced_pod_log(
            name=pod_name, namespace=self.namespace, container=container
        )
        print(logs)
        return logs

    def describe_pod(self, pod_name: str) -> dict:
        """
        Retrieves the description of a specified pod.

        Args:
            pod_name (str): Name of the pod.

        Returns:
            dict: Pod description.
        """
        core_v1 = client.CoreV1Api()
        pod = core_v1.read_namespaced_pod(name=pod_name, namespace=self.namespace)
        pod_dict = client.ApiClient().sanitize_for_serialization(pod)
        print(f"Retrieved information for pod '{pod_name}'")
        return pod_dict

    def describe_service(self, service_name: str) -> dict:
        """
        Retrieves the description of a specified service.

        Args:
            service_name (str): Name of the service.

        Returns:
            dict: Service description.
        """
        core_v1 = client.CoreV1Api()
        svc = core_v1.read_namespaced_service(name=service_name, namespace=self.namespace)
        svc_dict = client.ApiClient().sanitize_for_serialization(svc)
        print(f"Retrieved information for service '{service_name}'")
        return svc_dict

    def describe_deployment(self, deployment_name: str) -> dict:
        """
        Retrieves the description of a specified deployment.

        Args:
            deployment_name (str): Name of the deployment.

        Returns:
            dict: Deployment description.
        """
        apps_v1 = client.AppsV1Api()
        deployment = apps_v1.read_namespaced_deployment(
            name=deployment_name, namespace=self.namespace
        )
        deployment_dict = client.ApiClient().sanitize_for_serialization(deployment)
        print(f"Retrieved information for deployment '{deployment_name}'")
        return deployment_dict

    def list_pods(self) -> list:
        """
        Lists all pods in the current namespace.
        
        Returns:
            list: List of pods.
        """
        core_v1 = client.CoreV1Api()
        pods = core_v1.list_namespaced_pod(namespace=self.namespace)
        pods_list = client.ApiClient().sanitize_for_serialization(pods.items)
        print(f"Retrieved {len(pods_list)} pods in namespace '{self.namespace}'")
        return pods_list
        
    def list_services(self) -> list:
        """
        Lists all services in the current namespace.
        
        Returns:
            list: List of services.
        """
        core_v1 = client.CoreV1Api()
        services = core_v1.list_namespaced_service(namespace=self.namespace)
        services_list = client.ApiClient().sanitize_for_serialization(services.items)
        print(f"Retrieved {len(services_list)} services in namespace '{self.namespace}'")
        return services_list
        
    def list_deployments(self) -> list:
        """
        Lists all deployments in the current namespace.
        
        Returns:
            list: List of deployments.
        """
        apps_v1 = client.AppsV1Api()
        deployments = apps_v1.list_namespaced_deployment(namespace=self.namespace)
        deployments_list = client.ApiClient().sanitize_for_serialization(deployments.items)
        print(f"Retrieved {len(deployments_list)} deployments in namespace '{self.namespace}'")
        return deployments_list
        
    def list_configmaps(self) -> list:
        """
        Lists all configmaps in the current namespace.
        
        Returns:
            list: List of configmaps.
        """
        core_v1 = client.CoreV1Api()
        configmaps = core_v1.list_namespaced_config_map(namespace=self.namespace)
        configmaps_list = client.ApiClient().sanitize_for_serialization(configmaps.items)
        print(f"Retrieved {len(configmaps_list)} configmaps in namespace '{self.namespace}'")
        return configmaps_list
        
    def list_secrets(self) -> list:
        """
        Lists all secrets in the current namespace.
        
        Returns:
            list: List of secrets.
        """
        core_v1 = client.CoreV1Api()
        secrets = core_v1.list_namespaced_secret(namespace=self.namespace)
        secrets_list = client.ApiClient().sanitize_for_serialization(secrets.items)
        print(f"Retrieved {len(secrets_list)} secrets in namespace '{self.namespace}'")
        return secrets_list
        
    def list_resources_by_kind(self, api_version: str, kind: str) -> list:
        """
        Lists all resources of a specific kind in the current namespace.
        
        Args:
            api_version (str): API version of the resource (e.g., "apps/v1").
            kind (str): Kind of the resource (e.g., "Deployment", "Service").
            
        Returns:
            list: List of resources.
        """
        api_client = client.ApiClient()
        dynamic_client = DynamicClient(api_client)
        resource = dynamic_client.resources.get(api_version=api_version, kind=kind)
        resources = resource.get(namespace=self.namespace)
        resources_list = client.ApiClient().sanitize_for_serialization(resources.items)
        print(f"Retrieved {len(resources_list)} {kind} resources in namespace '{self.namespace}'")
        return resources_list


class KubernetesManagerMCP:
    """
    KubernetesManagerMCP provides methods to manage Kubernetes resources as MCP tools.
    """
    
    def __init__(self, name: str = "K8sManager", namespace: str = "default") -> None:
        """
        Initializes the KubernetesManagerMCP with the specified name and namespace.
        
        Args:
            name (str): Name for the MCP server.
            namespace (str): Kubernetes namespace to operate in.
        """
        self.k8s_manager = KubernetesManager(namespace=namespace)
        self.mcp = FastMCP(name, host='0.0.0.0')
        self._register_tools()
    
    def _register_tools(self) -> None:
        """Register all Kubernetes management tools with MCP."""
        
        @self.mcp.tool()
        def patch_resource(api_version: str, kind: str, name: str, patch_body: dict) -> str:
            """
            Patches a Kubernetes resource with provided patch body.

            Args:
                api_version (str): API version of the resource (e.g., "apps/v1").
                kind (str): Kind of the resource (e.g., "Deployment", "Service").
                name (str): Name of the resource to patch.
                patch_body (dict): JSON patch body defining the changes.
                
            Returns:
                str: Success message.
            """
            return self.k8s_manager.patch_resource(api_version, kind, name, patch_body)

        @self.mcp.tool()
        def apply_yaml(yaml_file_path: str) -> str:
            """
            Applies a YAML configuration to the Kubernetes cluster.

            Args:
                yaml_file_path (str): Path to the YAML file to apply.
                
            Returns:
                str: Success message.
            """
            return self.k8s_manager.apply_yaml(yaml_file_path)

        @self.mcp.tool()
        def get_pod_logs(pod_name: str, container: Optional[str] = None) -> str:
            """
            Retrieves logs from a specified pod.

            Args:
                pod_name (str): Name of the pod.
                container (Optional[str]): Specific container name within the pod, if applicable.

            Returns:
                str: Pod logs.
            """
            return self.k8s_manager.get_pod_logs(pod_name, container)

        @self.mcp.tool()
        def describe_pod(pod_name: str) -> dict:
            """
            Retrieves the description of a specified pod.

            Args:
                pod_name (str): Name of the pod.

            Returns:
                dict: Pod description.
            """
            return self.k8s_manager.describe_pod(pod_name)

        @self.mcp.tool()
        def describe_service(service_name: str) -> dict:
            """
            Retrieves the description of a specified service.

            Args:
                service_name (str): Name of the service.

            Returns:
                dict: Service description.
            """
            return self.k8s_manager.describe_service(service_name)

        @self.mcp.tool()
        def describe_deployment(deployment_name: str) -> dict:
            """
            Retrieves the description of a specified deployment.

            Args:
                deployment_name (str): Name of the deployment.

            Returns:
                dict: Deployment description.
            """
            return self.k8s_manager.describe_deployment(deployment_name)

        @self.mcp.tool()
        def list_pods() -> list:
            """
            Lists all pods in the current namespace.
            
            Returns:
                list: List of pods.
            """
            return self.k8s_manager.list_pods()
            
        @self.mcp.tool()
        def list_services() -> list:
            """
            Lists all services in the current namespace.
            
            Returns:
                list: List of services.
            """
            return self.k8s_manager.list_services()
            
        @self.mcp.tool()
        def list_deployments() -> list:
            """
            Lists all deployments in the current namespace.
            
            Returns:
                list: List of deployments.
            """
            return self.k8s_manager.list_deployments()
            
        @self.mcp.tool()
        def list_configmaps() -> list:
            """
            Lists all configmaps in the current namespace.
            
            Returns:
                list: List of configmaps.
            """
            return self.k8s_manager.list_configmaps()
            
        @self.mcp.tool()
        def list_secrets() -> list:
            """
            Lists all secrets in the current namespace.
            
            Returns:
                list: List of secrets.
            """
            return self.k8s_manager.list_secrets()
            
        @self.mcp.tool()
        def list_resources_by_kind(api_version: str, kind: str) -> list:
            """
            Lists all resources of a specific kind in the current namespace.
            
            Args:
                api_version (str): API version of the resource (e.g., "apps/v1").
                kind (str): Kind of the resource (e.g., "Deployment", "Service").
                
            Returns:
                list: List of resources.
            """
            return self.k8s_manager.list_resources_by_kind(api_version, kind)


# Example usage:
if __name__ == "__main__":
    k8s_mcp = KubernetesManagerMCP(name="K8sMCP", namespace="default")
    k8s_mcp.mcp.run(transport="sse")