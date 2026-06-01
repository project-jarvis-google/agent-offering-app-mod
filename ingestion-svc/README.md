# GitHub to GCS Ingestion Service

This service parses GitHub repository contents and streams them to a specified Google Cloud Storage bucket. It is built with FastAPI and leverages modern asynchronous Python patterns.

---

## Getting Started

### Prerequisites
Make sure you have `uv` installed. If not, the Makefile will install it automatically during target execution.

### 1. Install Dependencies
Initialize virtual environment and install dependencies:
```bash
make install
```

### 2. Environment Configuration

Create your local `.env` file from the sample:
```bash
cp .env.sample .env
```

Configure the database for your preferred setup:
- **SQLite Local Setup (Recommended / Simplest)**:
  Set `LOCAL_TESTING="true"` in your `.env`. This uses a lightweight local `db.sqlite3` database so you do not need Cloud SQL or a proxy connection.
- **GCP Cloud SQL Setup (Proxy)**:
  Comment out or set `LOCAL_TESTING="false"`. You must run the Cloud SQL Auth Proxy locally on the Unix socket path specified in `INSTANCE_CONNECTION_NAME` for connections to succeed.

### 3. Local Development Run
Start the hot-reloading dev server:
```bash
make dev
```
The API docs will be available locally at `http://localhost:8080/docs`.

### 4. Run Tests
Execute the automated test suite using the SQLite in-memory database:
```bash
make test
```

### 5. Code Linting & Type Checks
Run `ruff` formatter, linter, and `mypy` typechecker checks:
```bash
make lint
```

---

## CI/CD & Deployment Pipeline

The deployment is fully streamlined and operates similarly to the `app-mod-agent` service.

### Automated Deploy (Cloud Build)
Every commit pushed or merged to the `main` branch triggers the automated pipeline defined in `cloudbuild.yaml`:
1. **Lint & Typecheck (`lint-and-typecheck`)**: Runs formatting, lint checks, and mypy typecheck checks.
2. **Unit Tests (`unit-tests`)**: Runs the pytest suite.
3. **Deploy Service (`deploy-service`)**: Deploys the app to Google Cloud Run as the `iw-ingestion-svc` service.

### Manual Deploy
To manually deploy the service to Google Cloud Run in the current active active GCP project, run:
```bash
make deploy
```

Production environment variables are configured inside `.env.prod.yaml`. Sensitive secrets (like `DB_PASS`) are securely loaded directly from GCP Secret Manager (`iw-ingestion-svc-db-password:latest`).