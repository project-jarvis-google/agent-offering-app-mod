# GitHub to GCS Ingestion Service

This service parses GitHub repository contents and streams them to a specified Google Cloud Storage bucket. It is built with FastAPI and leverages modern asynchronous Python patterns.

---

## Local Setup & Running

### 1. Prerequisites
Make sure you have `uv` installed. If not, the Makefile will install it automatically during target execution.

### 2. Install Dependencies
Initialize the virtual environment and install dependencies:
```bash
make install
```

### 3. Environment Configuration
Create your local `.env` file from the sample:
```bash
cp .env.sample .env
```

Configure the database for your preferred local setup:
- **SQLite Local Setup (Recommended / Simplest)**:
  Set `LOCAL_TESTING="true"` in your `.env`. This uses a lightweight local `db.sqlite3` database file so you do not need Cloud SQL or a proxy connection.
- **GCP Cloud SQL Setup (Proxy)**:
  Comment out or set `LOCAL_TESTING="false"`. You must run the Cloud SQL Auth Proxy locally on the Unix socket path specified in `INSTANCE_CONNECTION_NAME` for connections to succeed.

For remote deployments, environment variables are referenced from these dedicated config files:
- **Development (`-dev`)**: Configurations are in `.env.dev.yaml`.
- **Production**: Configurations are in `.env.prod.yaml`.


### 4. Google Cloud Authentication (Required for GCS)
Since the service streams data directly to a Google Cloud Storage (GCS) bucket, you must authenticate your local machine to access Google Cloud resources:
1. Run the Application Default Credentials (ADC) login command:
   ```bash
   gcloud auth application-default login
   ```
2. Ensure your Google Cloud account has the appropriate access permissions (specifically, read and write access, such as the **Storage Object Admin** role) for the GCS bucket defined in `INSIGHTWAVE_WORKSPACE_BUCKET` in your `.env` file.

### 5. Run Local Server
Start the hot-reloading dev server:
```bash
make dev
```
The API docs will be available locally at `http://localhost:8080/docs`.

### 6. Run Unit Tests
Execute the automated test suite:
```bash
make test
```

### 7. Code Linting & Type Checks
Run `ruff` linter, formatter, and `mypy` typechecker:
```bash
make lint
```

---

## Deployment & CI/CD

The deployment is fully streamlined and operates similarly to the `app-mod-agent` service, supporting both production and development environments.

### Automated Deploy (Cloud Build)
The automated pipeline defined in `cloudbuild.yaml` runs linting, typechecks, and unit tests, and then deploys the app based on the active branch:
- **Pushes/Merges to `main` branch**: Deploys to the **Production** environment (Cloud Run service: `iw-ingestion-svc`).
- **Pushes/Merges to `dev` branch**: Deploys to the **Development** environment (Cloud Run service: `iw-ingestion-svc-dev`).

The steps executed in the pipeline are:
1. **Lint & Typecheck (`lint-and-typecheck`)**: Runs formatting, lint checks, and mypy typecheck checks.
2. **Unit Tests (`unit-tests`)**: Runs the pytest suite.
3. **Deploy Service (`deploy-service`)**: Deploys the service to Google Cloud Run as `iw-ingestion-svc` or `iw-ingestion-svc-dev`.

### Manual Deploy
To manually deploy the service to Google Cloud Run in the current active GCP project:

- **Production Environment (`iw-ingestion-svc`)**:
  ```bash
  make deploy
  ```
  Production environment variables are configured inside `.env.prod.yaml`. Sensitive secrets (like `DB_PASS`) are securely loaded directly from GCP Secret Manager (`iw-ingestion-svc-db-password:latest`).

- **Development Environment (`iw-ingestion-svc-dev`)**:
  ```bash
  make deploy-dev
  ```
  Development environment variables are configured inside `.env.dev.yaml`. Sensitive secrets (like `DB_PASS`) are securely loaded directly from GCP Secret Manager (`iw-ingestion-svc-dev-db-password:latest`).