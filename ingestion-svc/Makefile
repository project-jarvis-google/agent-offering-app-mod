.PHONY: install dev test lint deploy deploy-dev

# Version variables
UV_VERSION=0.6.12

# Install dependencies using uv package manager
install:
	@command -v uv >/dev/null 2>&1 || { echo "uv is not installed. Installing uv..."; curl -LsSf https://astral.sh/uv/$(UV_VERSION)/install.sh | sh; }
	uv sync

# Start the ingestion-svc local development server with hot-reloading
dev:
	uv run uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload

# Run the unit tests with LOCAL_TESTING enabled
test:
	LOCAL_TESTING=true uv run pytest tests/

# Run code quality checks (ruff linter, ruff formatter, and mypy typechecker)
lint:
	uv run --with ruff ruff check .
	uv run --with ruff ruff format . --check
	uv run --with mypy mypy .

# Deploy the ingestion service to Google Cloud Run
deploy:
	PROJECT_ID=$$(gcloud config get-value project) && \
	gcloud run deploy iw-ingestion-svc \
		--source . \
		--env-vars-file=./.env.prod.yaml \
		--update-secrets=DB_PASS=iw-ingestion-svc-db-password:latest \
		--service-account=iw-ingestion-svc-sa-prod@$$PROJECT_ID.iam.gserviceaccount.com \
		--memory "4Gi" \
		--cpu "2" \
		--project $$PROJECT_ID \
		--region "us-central1" \
		--labels "created-by=iw-ingestion-svc" \
		--allow-unauthenticated \
		--port 8080

# Deploy the ingestion service to Google Cloud Run (Development Environment)
deploy-dev:
	PROJECT_ID=$$(gcloud config get-value project) && \
	gcloud run deploy iw-ingestion-svc-dev \
		--source . \
		--env-vars-file=./.env.dev.yaml \
		--update-secrets=DB_PASS=iw-ingestion-svc-dev-db-password:latest \
		--service-account=iw-ingestion-svc-sa-dev@$$PROJECT_ID.iam.gserviceaccount.com \
		--memory "4Gi" \
		--cpu "2" \
		--project $$PROJECT_ID \
		--region "us-central1" \
		--labels "created-by=iw-ingestion-svc-dev" \
		--allow-unauthenticated \
		--port 8080

