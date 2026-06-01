# Terraform Infrastructure for ingestion-svc

This directory contains the Infrastructure as Code (IaC) configured with Terraform to provision all backing resources required for the **GitHub to GCS Ingestion Service** across both **Development** and **Production** environments.

Using this configuration ensures environment parity, security compliance, and easy migrations to separate Google Cloud projects.

---

## Architecture & Components

The backing infrastructure modules provision:
1. **Google Cloud Storage (GCS) Bucket**: Dedicated bucket for streaming and storing workspace data (`insight-wave-test-appmod-dev` / `insight-wave-test-appmod`).
2. **Cloud SQL Database (PostgreSQL)**: Secure Postgres database instance and users (`iw-ingestion-svc-db-dev` / `iw-ingestion-svc-db`).
3. **Secret Manager Secret**: Secret version for the database password, auto-generated during provisioning (`iw-ingestion-svc-dev-db-password` / `iw-ingestion-svc-db-password`).
4. **IAM Service Account**: Dedicated service account for the Cloud Run service (`iw-ingestion-svc-sa-dev` / `iw-ingestion-svc-sa-prod`) granted:
   - `roles/cloudsql.client` to securely connect to the database.
   - `roles/storage.objectAdmin` restricted to the created workspace storage bucket.
   - `roles/secretmanager.secretAccessor` restricted to the database password secret.

---

## Directory Structure

```
terraform/
├── README.md                     # This documentation
├── modules/
│   └── backing_infra/            # Reusable backing infrastructure module
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
└── environments/
    ├── dev/                      # Development environment definition
    │   ├── main.tf
    │   └── variables.tf
    └── prod/                     # Production environment definition
        ├── main.tf
        └── variables.tf
```

---

## How to Deploy Infrastructure

### Prerequisites
1. Install [Terraform CLI](https://developer.hashicorp.com/terraform/downloads) (v1.0.0+).
2. Authenticate with Google Cloud:
   ```bash
   gcloud auth application-default login
   ```
3. Make sure you have permissions to create resources (IAM roles: Owner, Editor, or specific resource admins) in your targeted GCP project.

### 1. Deploying the Development Environment
Navigate to the dev environment folder:
```bash
cd environments/dev
```

Initialize Terraform plugins and backend:
```bash
terraform init
```

Generate a plan to preview changes (replace `<GCP_PROJECT_ID>` with your actual project):
```bash
terraform plan -var="project_id=<GCP_PROJECT_ID>"
```

Apply the configuration:
```bash
terraform apply -var="project_id=<GCP_PROJECT_ID>"
```

---

### 2. Deploying the Production Environment
Navigate to the prod environment folder:
```bash
cd ../prod
```

Initialize Terraform:
```bash
terraform init
```

Generate a plan:
```bash
terraform plan -var="project_id=<GCP_PROJECT_ID>"
```

Apply the configuration:
```bash
terraform apply -var="project_id=<GCP_PROJECT_ID>"
```

---

## Integration with Cloud Run Deployment

Once your resources are provisioned, copy the output values to update your environment configurations:

1. **`dev_db_connection` / `prod_db_connection`**: Used as `INSTANCE_CONNECTION_NAME` in `.env.dev.yaml` / `.env.prod.yaml`.
2. **`dev_bucket_name` / `prod_bucket_name`**: Used as `INSIGHTWAVE_WORKSPACE_BUCKET` in `.env.dev.yaml` / `.env.prod.yaml`.
3. **Service Account**: When deploying the Cloud Run service, specify the created service account (e.g., `--service-account=<SERVICE_ACCOUNT_EMAIL>`) to ensure your application starts with all required IAM credentials out-of-the-box.
