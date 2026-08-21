# Agent-X Production Deployment Guide (Google Cloud Platform)

Agent-X infrastructure is 100% managed via declarative Terraform across 8 modular components and 3 decoupled environments (`dev`, `staging`, `prod`).

---

## 🏗️ Architecture Stack

| Service / Resource | GCP Technology | Purpose |
| :--- | :--- | :--- |
| **API Coordinator** | Google Cloud Run v2 (`agent-x-api`) | FastAPI REST, SSE event stream, WebSocket terminal. |
| **Subagent Workers** | Google Cloud Run v2 (`agent-x-worker`) | ADK subagent sandbox & tool execution engine. |
| **Persistence** | Google Cloud Firestore (Native Mode) | World model, mission DAG, claims, and event sourcing. |
| **Event Mesh** | Google Cloud Pub/Sub | Async task dispatch, telemetry, and dead-letter queues. |
| **Evidence Storage** | Google Cloud Storage (GCS) | Immutable Level 1–4 verification proofs and artifacts. |
| **Secret Vault** | Google Secret Manager | Secure dynamic API keys and credentials (Zero Hardcoding). |
| **IAM & Roles** | Google Cloud IAM | Least-privilege service accounts (`sa-agentx-api`, `sa-agentx-worker`). |
| **Monitoring** | Cloud Logging & Cloud Monitoring | Log metrics, 5xx alerts, DLQ spikes, operational dashboards. |

---

## 🚀 Deployment Instructions

### 1. Prerequisites
- Google Cloud SDK (`gcloud`) installed and authenticated:
  ```bash
  gcloud auth login
  gcloud auth application-default login
  gcloud config set project YOUR_GCP_PROJECT_ID
  ```
- Terraform CLI `1.5.0+` installed.

### 2. Configure Environment Variables
Choose your target environment (`dev`, `staging`, or `prod`):

```bash
cd infrastructure/terraform/environments/dev
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars`:
```hcl
project_id         = "your-gcp-project-id"
region             = "us-central1"
notification_email = "ops-team@yourdomain.com"
```

### 3. Provision Cloud Infrastructure
```bash
# Initialize Terraform and download Google provider
terraform init

# Validate configuration and inspect plan
terraform plan

# Apply infrastructure changes
terraform apply -auto-approve
```

### 4. Populate Secret Manager Keys
Populate your Gemini API key and session encryption secret securely:
```bash
gcloud secrets versions add agentx-gemini-api-key-dev --data-file=/path/to/gemini_key.txt
gcloud secrets versions add agentx-session-secret-dev --data-file=/path/to/session_secret.txt
```

### 5. Build and Deploy Container Images
```bash
# Build API container
gcloud builds submit --tag gcr.io/YOUR_GCP_PROJECT_ID/agent-x-api:dev -f services/agent-x/Dockerfile .

# Build Worker container
gcloud builds submit --tag gcr.io/YOUR_GCP_PROJECT_ID/agent-x-worker:dev -f services/agent-x/Dockerfile.worker .
```

### 6. Verify Deployed Services
- Test the Cloud Run API Health endpoint:
  ```bash
  curl https://agent-x-api-dev-xxxx-uc.a.run.app/healthz
  ```
- Access the Next.js Mission Control PWA connected to the live API backend.
