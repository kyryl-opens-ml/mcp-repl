#!/bin/bash
set -e

echo "=== Creating Kind Cluster ==="
# Check if kind is installed
if ! command -v kind &> /dev/null; then
    echo "Kind is not installed. Please install it first."
    echo "Visit: https://kind.sigs.k8s.io/docs/user/quick-start/#installation"
    exit 1
fi

# Create a kind cluster with ingress support
kind create cluster --name mcp-infra-playground

echo "=== Installing Helm (if not already installed) ==="
# Check if helm is installed
if ! command -v helm &> /dev/null; then
    echo "Helm is not installed. Installing Helm..."
    curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
else
    echo "Helm is already installed."
fi

echo "=== Adding Helm repositories ==="
# Add the PostgreSQL, MinIO and ngrok Helm repositories
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo add minio https://charts.min.io/
helm repo add ngrok https://charts.ngrok.com
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update
