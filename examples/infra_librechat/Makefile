.PHONY: create-all clean-all create-openai-secret create-dashboard

# Default path for MCP script
MCP_SCRIPT ?= servers/mcp_k8s.py

create-all: 
	# @echo "Creating cluster"
	# kind create cluster --name minimum-functionality-test
	
	@echo "Deploying MCP with script: $(MCP_SCRIPT)"
	uv run k8s/deploy_mcp.py --mcp_script $(MCP_SCRIPT)
	
	@echo "Configuring OpenAI secret"
	kubectl create secret generic openai-api-key --from-literal=OPENAI_API_KEY=${OPENAI_API_KEY}

	@echo "Deploying LibreChat"
	kubectl create -f ./k8s/k8s-libre.yaml
	
	@echo "Deploying nginx with error"
	kubectl create -f ./k8s/k8s-error.yaml
	
	@echo "Done!"

clean-all:
	kind delete cluster --name minimum-functionality-test

create-dashboard:
	kubectl apply -f https://raw.githubusercontent.com/kubernetes-sigs/headlamp/main/kubernetes-headlamp.yaml

open-dashboard:
	@echo "Opening dashboard at http://localhost:8080"
	kubectl port-forward svc/headlamp-svc 8080:80 --address 0.0.0.0

open-librechat:
	@echo "Opening LibreChat at http://localhost:3080"
	kubectl port-forward svc/librechat 3080:3080 --address 0.0.0.0

format:
	uv run ruff check --fix .

setup:
	uv sync
