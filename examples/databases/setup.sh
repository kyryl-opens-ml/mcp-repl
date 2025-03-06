#!/bin/bash
set -e

echo "=== Creating Kind Cluster ==="
# Check if kind is installed
if ! command -v kind &> /dev/null; then
    echo "Kind is not installed. Please install it first."
    echo "Visit: https://kind.sigs.k8s.io/docs/user/quick-start/#installation"
    exit 1
fi

# Create a kind cluster
kind create cluster --name mcp-databases-example

echo "=== Installing Helm (if not already installed) ==="
# Check if helm is installed
if ! command -v helm &> /dev/null; then
    echo "Helm is not installed. Installing Helm..."
    curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
else
    echo "Helm is already installed."
fi

echo "=== Adding Helm repositories ==="
# Add the necessary Helm repositories
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

echo "=== Installing PostgreSQL ==="
# Install PostgreSQL with password: postgres
helm install postgres bitnami/postgresql \
  --set auth.postgresPassword=postgres \
  --set auth.database=postgres

echo "=== Installing MySQL ==="
# Install MySQL
helm install mysql bitnami/mysql \
  --set auth.rootPassword=mysql \
  --set auth.database=mysql

echo "=== Installing Redis ==="
# Install Redis
helm install redis bitnami/redis \
  --set auth.password=redis

echo "=== Waiting for services to be ready ==="
kubectl wait --for=condition=ready --timeout=300s pod -l app.kubernetes.io/name=postgresql,app.kubernetes.io/instance=postgres
kubectl wait --for=condition=ready --timeout=300s pod -l app.kubernetes.io/name=mysql,app.kubernetes.io/instance=mysql
kubectl wait --for=condition=ready --timeout=300s pod -l app.kubernetes.io/name=redis,app.kubernetes.io/instance=redis

echo "=== Setting up port forwarding for databases ==="
# Start port forwarding in the background and save PIDs
echo "Starting port forwarding for PostgreSQL on localhost:5432..."
kubectl port-forward svc/postgres-postgresql 5432:5432 > /dev/null 2>&1 &
PG_PID=$!
echo "PostgreSQL port forwarding PID: $PG_PID"

echo "Starting port forwarding for MySQL on localhost:3306..."
kubectl port-forward svc/mysql 3306:3306 > /dev/null 2>&1 &
MYSQL_PID=$!
echo "MySQL port forwarding PID: $MYSQL_PID"

echo "Starting port forwarding for Redis on localhost:6379..."
kubectl port-forward svc/redis-master 6379:6379 > /dev/null 2>&1 &
REDIS_PID=$!
echo "Redis port forwarding PID: $REDIS_PID"

echo "=== Database Connection Information ==="
echo "PostgreSQL credentials: postgres / postgres"
echo "PostgreSQL connection: localhost:5432/postgres"
echo ""
echo "MySQL credentials: root / mysql"
echo "MySQL connection: localhost:3306/mysql"
echo ""
echo "Redis password: redis"
echo "Redis connection: localhost:6379"
echo ""
echo "Port forwarding is running in the background."
echo "To stop all port forwarding processes, run:"
echo "kill $PG_PID $MYSQL_PID $REDIS_PID"
echo "Or use: pkill -f 'kubectl port-forward'"

echo "=== How to Connect to Databases ==="
echo "PostgreSQL:"
echo "  psql -h localhost -p 5432 -U postgres -d postgres"
echo "  Password: postgres"
echo ""
echo "MySQL:"
echo "  mysql -h 127.0.0.1 -P 3306 -u root -p mysql"
echo "  Password: mysql"
echo ""
echo "Redis:"
echo "  redis-cli -h localhost -p 6379 -a redis"
echo ""
echo "You can also use any database client with the connection information provided above."