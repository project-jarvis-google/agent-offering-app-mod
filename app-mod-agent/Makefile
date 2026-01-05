.PHONY: install dev dev-backend dev-frontend playground backend-deploy frontend-deploy frontend-deploy-new local-backend setup-dev-env test lint lint-codespell lint-frontend lint-backend checks-github checks-pylint

# Version variables
NODE_VERSION=20
UV_VERSION=0.6.12
NVM_VERSION=v0.39.3

# Install dependencies using uv package manager
install:
	@command -v uv >/dev/null 2>&1 || { echo "uv is not installed. Installing uv..."; curl -LsSf https://astral.sh/uv/$(UV_VERSION)/install.sh | sh; }
	@command -v npm >/dev/null 2>&1 || { echo "npm is not installed. Installing nvm and Node.js v$(NODE_VERSION)..."; curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/$(NVM_VERSION)/install.sh | bash; export NVM_DIR="$$HOME/.nvm"; [ -s "$$NVM_DIR/nvm.sh" ] && . "$$NVM_DIR/nvm.sh"; nvm install $(NODE_VERSION); nvm use $(NODE_VERSION); }

	uv sync --dev --extra jupyter --extra lint && npm --prefix frontend/vite-project install

# Start the ADK API server and React frontend development server simultaneously
dev:
	make dev-backend & make dev-frontend

# Start the ADK API server
dev-backend:
	ALLOW_ORIGINS="*" uv run uvicorn app.server:app --host 0.0.0.0 --port 8000 --reload

# Start the React frontend development server
dev-frontend:
	npm --prefix frontend/vite-project run dev

# Launch local dev playground
playground:
	@echo "==============================================================================="
	@echo "| 🚀 Starting your agent playground...                                        |"
	@echo "|                                                                             |"
	@echo "| 💡 Try asking: A report on the latest Google I/O event                      |"
	@echo "|                                                                             |"
	@echo "| 🔍 IMPORTANT: Select the 'app' folder to interact with your agent.          |"
	@echo "==============================================================================="
	uv run adk web --port 8501

# Deploy the agent remotely
# Usage: make backend [PORT=8080] - Set IAP=true to enable Identity-Aware Proxy, PORT to specify container port
backend-deploy:
	PROJECT_ID=$$(gcloud config get-value project) && \
	gcloud run deploy app-mod-agent-backend \
		--source . \
		--env-vars-file=./.env.prod.yaml \
		--update-secrets=GEMINI_API_KEY=app-mod-agent-GEMINI_API_KEY:latest \
		--memory "4Gi" \
		--project $$PROJECT_ID \
		--region "us-central1" \
		--labels "created-by=app-mod-agent" \
		--allow-unauthenticated \
		--port 8080

frontend-deploy:
	PROJECT_ID=$$(gcloud config get-value project) && \
	cd frontend/vite-project && \
	gcloud run deploy app-mod-agent-frontend \
	--source . \
	--memory "4Gi" \
	--project $$PROJECT_ID \
	--region "us-central1" \
	--labels "created-by=app-mod-agent" \
	--allow-unauthenticated \
	--port 8080

# Launch local development server with hot-reload
local-backend:
	uv run uvicorn app.server:app --host 0.0.0.0 --port 8000 --reload

# Set up development environment resources using Terraform
setup-dev-env:
	PROJECT_ID=$$(gcloud config get-value project) && \
	(cd deployment/terraform/dev && terraform init && terraform apply --var-file vars/env.tfvars --var dev_project_id=$$PROJECT_ID --auto-approve)

# Run unit and integration tests
test:
	uv run pytest tests/unit && uv run pytest tests/integration

# Run code quality checks (codespell, ruff, mypy)
lint: lint-codespell lint-frontend lint-backend

lint-codespell:
	uv run codespell

lint-frontend:
	npm --prefix frontend/vite-project install
	npm --prefix frontend/vite-project run lint

lint-backend:
	uv run ruff check . --diff
	uv run ruff format . --check --diff
	uv run mypy .

checks-github:
	@command -v uv >/dev/null 2>&1 || { echo "uv is not installed. Installing uv..."; curl -LsSf https://astral.sh/uv/$(UV_VERSION)/install.sh | sh; }
	uv sync --dev --extra jupyter && npm --prefix frontend install

checks-pylint:
	pylint . --ignore-paths='app-mod-agent/app/utils/*' --disable=unexpected-keyword-arg,missing-kwoa
