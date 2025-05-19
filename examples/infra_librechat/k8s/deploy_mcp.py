from kubernetes import client, config
from kubernetes.client.rest import ApiException
import argparse

def cleanup_resources():
    # Load Kubernetes configuration
    config.load_kube_config()
    
    # Create API clients
    api_client = client.ApiClient()
    core_v1 = client.CoreV1Api(api_client)
    apps_v1 = client.AppsV1Api(api_client)
    rbac_v1 = client.RbacAuthorizationV1Api(api_client)
    
    namespace = "default"
    
    # Delete Deployment
    try:
        apps_v1.delete_namespaced_deployment("k8s-manager", namespace)
        print("Deployment deleted successfully")
    except ApiException as e:
        if e.status == 404:
            print("Deployment does not exist")
        else:
            print(f"Error deleting deployment: {e}")
    
    # Delete Service
    try:
        core_v1.delete_namespaced_service("k8s-manager", namespace)
        print("Service deleted successfully")
    except ApiException as e:
        if e.status == 404:
            print("Service does not exist")
        else:
            print(f"Error deleting service: {e}")
    
    # Delete ConfigMap
    try:
        core_v1.delete_namespaced_config_map("k8s-manager-script", namespace)
        print("ConfigMap deleted successfully")
    except ApiException as e:
        if e.status == 404:
            print("ConfigMap does not exist")
        else:
            print(f"Error deleting configmap: {e}")
    
    # Delete ClusterRoleBinding
    try:
        rbac_v1.delete_cluster_role_binding("k8s-manager-binding")
        print("ClusterRoleBinding deleted successfully")
    except ApiException as e:
        if e.status == 404:
            print("ClusterRoleBinding does not exist")
        else:
            print(f"Error deleting clusterrolebinding: {e}")
    
    # Delete ClusterRole
    try:
        rbac_v1.delete_cluster_role("k8s-manager-role")
        print("ClusterRole deleted successfully")
    except ApiException as e:
        if e.status == 404:
            print("ClusterRole does not exist")
        else:
            print(f"Error deleting clusterrole: {e}")
    
    # Delete ServiceAccount
    try:
        core_v1.delete_namespaced_service_account("k8s-manager", namespace)
        print("ServiceAccount deleted successfully")
    except ApiException as e:
        if e.status == 404:
            print("ServiceAccount does not exist")
        else:
            print(f"Error deleting serviceaccount: {e}")

def create_k8s_manager_deployment(mcp_script_path):
    # Load Kubernetes configuration
    config.load_kube_config()
    
    # Create API clients
    api_client = client.ApiClient()
    core_v1 = client.CoreV1Api(api_client)
    apps_v1 = client.AppsV1Api(api_client)
    rbac_v1 = client.RbacAuthorizationV1Api(api_client)
    
    namespace = "default"
    
    # Create ServiceAccount
    service_account = client.V1ServiceAccount(
        metadata=client.V1ObjectMeta(
            name="k8s-manager",
            namespace=namespace
        )
    )
    
    try:
        core_v1.create_namespaced_service_account(namespace, service_account)
        print("ServiceAccount created successfully")
    except ApiException as e:
        if e.status == 409:
            print("ServiceAccount already exists")
        else:
            raise
    
    # Create ClusterRole
    cluster_role = client.V1ClusterRole(
        metadata=client.V1ObjectMeta(
            name="k8s-manager-role"
        ),
        rules=[
            client.V1PolicyRule(
                api_groups=[""],
                resources=["pods", "services", "configmaps", "secrets"],
                verbs=["get", "list", "watch", "create", "update", "patch", "delete"]
            ),
            client.V1PolicyRule(
                api_groups=["apps"],
                resources=["deployments"],
                verbs=["get", "list", "watch", "create", "update", "patch", "delete"]
            )
        ]
    )
    
    try:
        rbac_v1.create_cluster_role(cluster_role)
        print("ClusterRole created successfully")
    except ApiException as e:
        if e.status == 409:
            print("ClusterRole already exists")
        else:
            raise
    
    # Create ClusterRoleBinding
    cluster_role_binding = client.V1ClusterRoleBinding(
        metadata=client.V1ObjectMeta(
            name="k8s-manager-binding"
        ),
        subjects=[
            client.RbacV1Subject(
                kind="ServiceAccount",
                name="k8s-manager",
                namespace=namespace
            )
        ],
        role_ref=client.V1RoleRef(
            kind="ClusterRole",
            name="k8s-manager-role",
            api_group="rbac.authorization.k8s.io"
        )
    )
    
    try:
        rbac_v1.create_cluster_role_binding(cluster_role_binding)
        print("ClusterRoleBinding created successfully")
    except ApiException as e:
        if e.status == 409:
            print("ClusterRoleBinding already exists")
        else:
            raise
    
    # Create ConfigMap for mcp_k8s.py
    with open(mcp_script_path, "r") as f:
        mcp_k8s_content = f.read()
    
    mcp_code_map = client.V1ConfigMap(
        metadata=client.V1ObjectMeta(
            name="k8s-manager-code",
            namespace=namespace
        ),
        data={
            "mcp_k8s.py": mcp_k8s_content
        }
    )
    
    try:
        core_v1.create_namespaced_config_map(namespace, mcp_code_map)
        print("Code ConfigMap created successfully")
    except ApiException as e:
        if e.status == 409:
            print("Code ConfigMap already exists")
        else:
            raise
    
    # Create ConfigMap for runner script
    run_script = """
import sys
import os

# Add the directory with mcp_k8s.py to Python path
sys.path.append('/app')

# Import the KubernetesManagerMCP from the mounted file
from mcp_k8s import KubernetesManagerMCP

# Create instance and run the server
k8s_mcp = KubernetesManagerMCP(name='K8sMCP', namespace='default')
k8s_mcp.mcp.run(transport='sse')
"""
    
    config_map = client.V1ConfigMap(
        metadata=client.V1ObjectMeta(
            name="k8s-manager-script",
            namespace=namespace
        ),
        data={
            "run.py": run_script
        }
    )
    
    try:
        core_v1.create_namespaced_config_map(namespace, config_map)
        print("Script ConfigMap created successfully")
    except ApiException as e:
        if e.status == 409:
            print("Script ConfigMap already exists")
        else:
            raise
    
    # Create Deployment
    container = client.V1Container(
        name="k8s-manager",
        image="ghcr.io/astral-sh/uv:python3.12-bookworm-slim",
        ports=[client.V1ContainerPort(container_port=8000)],
        volume_mounts=[
            client.V1VolumeMount(
                name="code-volume",
                mount_path="/app/mcp_k8s.py",
                sub_path="mcp_k8s.py"
            ),
            client.V1VolumeMount(
                name="script-volume",
                mount_path="/app/run.py",
                sub_path="run.py"
            )
        ],
        command=["/bin/sh", "-c"],
        args=["cd /app && python -m pip install kubernetes mcp[cli] && python run.py"]
    )
    
    template = client.V1PodTemplateSpec(
        metadata=client.V1ObjectMeta(labels={"app": "k8s-manager"}),
        spec=client.V1PodSpec(
            service_account_name="k8s-manager",
            containers=[container],
            volumes=[
                client.V1Volume(
                    name="code-volume",
                    config_map=client.V1ConfigMapVolumeSource(
                        name="k8s-manager-code"
                    )
                ),
                client.V1Volume(
                    name="script-volume",
                    config_map=client.V1ConfigMapVolumeSource(
                        name="k8s-manager-script"
                    )
                )
            ]
        )
    )
    
    deployment = client.V1Deployment(
        metadata=client.V1ObjectMeta(
            name="k8s-manager",
            namespace=namespace
        ),
        spec=client.V1DeploymentSpec(
            replicas=1,
            selector=client.V1LabelSelector(
                match_labels={"app": "k8s-manager"}
            ),
            template=template
        )
    )
    
    try:
        apps_v1.create_namespaced_deployment(namespace, deployment)
        print("Deployment created successfully")
    except ApiException as e:
        if e.status == 409:
            print("Deployment already exists")
        else:
            raise
    
    # Create Service
    service = client.V1Service(
        metadata=client.V1ObjectMeta(
            name="k8s-manager",
            namespace=namespace
        ),
        spec=client.V1ServiceSpec(
            selector={"app": "k8s-manager"},
            ports=[client.V1ServicePort(port=8000, target_port=8000)],
            type="ClusterIP"
        )
    )
    
    try:
        core_v1.create_namespaced_service(namespace, service)
        print("Service created successfully")
    except ApiException as e:
        if e.status == 409:
            print("Service already exists")
        else:
            raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Deploy Kubernetes Manager MCP')
    parser.add_argument('--mcp_script', type=str, default="mcp-servers/mcp_k8s.py",
                        help='Path to the mcp_k8s.py script (default: mcp-servers/mcp_k8s.py)')
    args = parser.parse_args()
    
    # First clean up existing resources
    cleanup_resources()
    
    # Then create the new ones
    create_k8s_manager_deployment(args.mcp_script)
    print(f"K8s Manager deployment completed with script: {args.mcp_script}")