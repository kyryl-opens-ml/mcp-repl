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

echo "=== Installing PostgreSQL ==="
# Install PostgreSQL with password: postgres
helm install postgres bitnami/postgresql \
  --set auth.postgresPassword=postgres \
  --set auth.database=postgres

echo "=== Installing MinIO ==="
# Install MinIO
helm install \
  --set resources.requests.memory=512Mi \
  --set replicas=1 \
  --set persistence.enabled=true \
  --set mode=standalone \
  --set rootUser=minioadmin,rootPassword=minioadmin \
  --generate-name minio/minio

echo "=== Installing NGINX Ingress Controller ==="
# Install NGINX Ingress Controller
helm install ingress-nginx ingress-nginx/ingress-nginx

echo "=== Waiting for NGINX Ingress Controller to be ready ==="
echo "Waiting for NGINX Ingress Controller pods to be ready..."
kubectl wait --namespace default \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=180s

echo "Waiting for NGINX Ingress Controller admission webhook to be ready..."
# Wait for the admission webhook to be ready
sleep 30

echo "=== Creating Python HTTP Server Deployments and Services ==="
# Create Python HTTP Server 1
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: python-http-server-1
spec:
  replicas: 1
  selector:
    matchLabels:
      app: python-http-server-1
  template:
    metadata:
      labels:
        app: python-http-server-1
    spec:
      containers:
      - name: python-http-server
        image: python:3.9-alpine
        command: ["python", "-m", "http.server", "8080"]
        ports:
        - containerPort: 8080
---
apiVersion: v1
kind: Service
metadata:
  name: python-http-service-1
spec:
  selector:
    app: python-http-server-1
  ports:
  - port: 8080
    targetPort: 8080
EOF

# Create Python HTTP Server 2
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: python-http-server-2
spec:
  replicas: 1
  selector:
    matchLabels:
      app: python-http-server-2
  template:
    metadata:
      labels:
        app: python-http-server-2
    spec:
      containers:
      - name: python-http-server
        image: python:3.9-alpine
        command: ["python", "-m", "http.server", "8080"]
        ports:
        - containerPort: 8080
---
apiVersion: v1
kind: Service
metadata:
  name: python-http-service-2
spec:
  selector:
    app: python-http-server-2
  ports:
  - port: 8080
    targetPort: 8080
EOF

# Create Python HTTP Server 3
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: python-http-server-3
spec:
  replicas: 1
  selector:
    matchLabels:
      app: python-http-server-3
  template:
    metadata:
      labels:
        app: python-http-server-3
    spec:
      containers:
      - name: python-http-server
        image: python:3.9-alpine
        command: ["python", "-m", "http.server", "8080"]
        ports:
        - containerPort: 8080
---
apiVersion: v1
kind: Service
metadata:
  name: python-http-service-3
spec:
  selector:
    app: python-http-server-3
  ports:
  - port: 8080
    targetPort: 8080
EOF

echo "=== Patching NGINX Ingress Controller Service ==="
# Remove appProtocol from the NGINX Ingress Controller service
kubectl patch service ingress-nginx-controller --type='json' -p='[{"op": "remove", "path": "/spec/ports/0/appProtocol"}]'

echo "=== Creating Fanout Ingress ==="
# Create a fanout ingress
cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: fanout-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  ingressClassName: nginx
  rules:
  - http:
      paths:
      - path: /foo
        pathType: Prefix
        backend:
          service:
            name: python-http-service-1
            port:
              number: 8080
      - path: /bar
        pathType: Prefix
        backend:
          service:
            name: python-http-service-2
            port:
              number: 8080
      - path: /foobar
        pathType: Prefix
        backend:
          service:
            name: python-http-service-3
            port:
              number: 8080
EOF

echo "=== Installing ngrok Ingress Controller ==="
# Set ngrok credentials
export NGROK_AUTHTOKEN=2tgzOt9xLSK8CjaBBMrKC2wYrHK_Ak5zsPNSUMStj2PywXqP
export NGROK_API_KEY=2th1mnz9NrR14YGaCZZELc0zF5m_2Pg2UMuzLuRDmTqwD3R6i

# Install ngrok ingress controller
helm install ngrok-ingress-controller ngrok/kubernetes-ingress-controller \
  --set credentials.apiKey=$NGROK_API_KEY \
  --set credentials.authtoken=$NGROK_AUTHTOKEN

echo "=== Creating ngrok Ingress ==="
# Create ngrok ingress that points to the NGINX Ingress Controller
cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ngrok-ingress
  annotations:
    ngrok.ingress.kubernetes.io/modules: '{"http": {"domain": "merry-gently-yak.ngrok-free.app"}}'
spec:
  ingressClassName: ngrok
  rules:
    - host: merry-gently-yak.ngrok-free.app
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: ingress-nginx-controller
                port:
                  number: 80
EOF

echo "=== Waiting for services to be ready ==="
kubectl wait --for=condition=available --timeout=300s deployment/python-http-server-1
kubectl wait --for=condition=available --timeout=300s deployment/python-http-server-2
kubectl wait --for=condition=available --timeout=300s deployment/python-http-server-3

echo "=== Setup Complete ==="
echo "Your services are now accessible through ngrok at merry-gently-yak.ngrok-free.app"
echo "Python HTTP Server 1: https://merry-gently-yak.ngrok-free.app/foo"
echo "Python HTTP Server 2: https://merry-gently-yak.ngrok-free.app/bar"
echo "Python HTTP Server 3: https://merry-gently-yak.ngrok-free.app/foobar"
echo ""
echo "You can also access them locally at:"
echo "Python HTTP Server 1: http://localhost/foo"
echo "Python HTTP Server 2: http://localhost/bar"
echo "Python HTTP Server 3: http://localhost/foobar"
echo ""
echo "Note: It may take a few minutes for the ngrok tunnel to be fully established"

echo "=== Setting up port forwarding for MinIO and PostgreSQL ==="
# Get the MinIO service names (they have generated names)
MINIO_API_SERVICE=$(kubectl get svc -l app=minio -o jsonpath='{.items[0].metadata.name}')
MINIO_CONSOLE_SERVICE="${MINIO_API_SERVICE}-console"

# Start port forwarding in the background
echo "Starting port forwarding for MinIO API on localhost:9000..."
kubectl port-forward svc/$MINIO_API_SERVICE 9000:9000 &

echo "Starting port forwarding for MinIO UI on localhost:9001..."
kubectl port-forward svc/$MINIO_CONSOLE_SERVICE 9001:9001 &

echo "MinIO credentials: minioadmin / minioadmin"
echo "MinIO UI: http://localhost:9001"
echo "MinIO API: http://localhost:9000"

echo "Starting port forwarding for PostgreSQL on localhost:5432..."
kubectl port-forward svc/postgres-postgresql 5432:5432 &
echo "PostgreSQL credentials: postgres / postgres"
echo "PostgreSQL connection: localhost:5432/postgres"

echo "Port forwarding is running in the background. To stop it, find and kill the processes."
echo "You can use: pkill -f 'kubectl port-forward'"

echo "=== Running PostgreSQL Data Migration Script ==="
POSTGRES_DB_NAME=retail_db python pg_data.py

# Set AWS credentials as environment variables
export AWS_ACCESS_KEY_ID=minioadmin
export AWS_SECRET_ACCESS_KEY=minioadmin
export AWS_ENDPOINT_URL=http://localhost:9000

# List buckets to verify connection
echo "Listing MinIO buckets to verify connection:"
aws s3 ls --endpoint-url $AWS_ENDPOINT_URL