# Specification: Databricks GreenMobility Analytics (Serverless)

This specification defines a serverless Databricks data product for GreenMobility analytics using Databricks Asset Bundles (DABs). It prioritizes simplicity, security via secrets, and low-cost serverless execution.

## 1. Objective
Automate the ingestion of GreenMobility "Rentals" and "Vouchers" into a Medallion architecture (Bronze -> Silver) using Databricks Serverless compute.

## 2. Infrastructure (Databricks Asset Bundle)
The project is packaged as an Asset Bundle. This ensures the job, tasks, and environment variables are versioned and deployable as a single unit.

### 2.1 Serverless Configuration
To run on the free tier/serverless compute, we omit explicit cluster definitions and use the `compute_key: serverless` or the default serverless task setting.

**Bundle Configuration (`databricks.yml`):**
```yaml
bundle:
  name: greenmo-analytics

resources:
  jobs:
    greenmo_sync:
      name: GreenMobility_Sync_Serverless
      tasks:
        - task_key: ingest_to_bronze
          compute_key: serverless_compute
          notebook_task:
            notebook_path: ./src/ingestion.py
            base_parameters:
              token: "{{sdk.secrets.get('greenmo_scope', 'GREENMO_TOKEN')}}"
        
        - task_key: process_to_silver
          depends_on:
            - task_key: ingest_to_bronze
          compute_key: serverless_compute
          notebook_task:
            notebook_path: ./src/silver_cleanup.py

      compute:
        - compute_key: serverless_compute
          spec:
            kind: serverless
```

## 3. Data Pipeline

### 3.1 Bronze Task (Ingestion)
*   **Logic:** Calls GoUrban APIs with the Bearer token.
*   **Storage:** Saves raw JSON to Delta tables `greenmo_bronze_rentals` and `greenmo_bronze_vouchers`.
*   **Endpoints:**
    *   **Trips:** `GET https://platform.api.gourban.services/v1/hb98ga69/front/rentals?page=0&size=50&state=ENDED`
    *   **Vouchers:** `GET https://platform.api.gourban.services/v1/hb98ga69/front/vouchers?branchId=2&page=0&size=50&active`

### 3.2 Silver Task (Cleanup)
*   **Logic:**
    *   Reads from Bronze.
    *   Parses JSON schema.
    *   Converts timestamps (`startTime`, `endTime`, `validUntil`).
    *   Calculates `duration_minutes` and `cost_dkk`.
    *   Deduplicates by `id`.

## 4. Deployment Logic

### 4.1 Secrets Management
The Bearer token and Databricks access credentials must be defined in a `.env` file at the project root.
Required variables:
*   `DATABRICKS_HOST`: Your Databricks workspace URL.
*   `DATABRICKS_TOKEN`: Personal Access Token for the workspace.
*   `GREENMO_TOKEN`: The GreenMobility API Bearer token.

### 4.2 Automation Script (`deploy.sh`)
This script automates the creation of the secret scope and the deployment of the bundle. It automatically sources the `.env` file.

```bash
#!/bin/bash
# Usage: ./deploy.sh [create|delete]
ACTION=$1

# Source environment variables from .env
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

if [ "$ACTION" == "create" ]; then
    echo "1. Creating Secret Scope..."
    databricks secrets create-scope greenmo_scope
    
    echo "2. Uploading GreenMobility Token..."
    databricks secrets put-secret greenmo_scope GREENMO_TOKEN --string-value "$GREENMO_TOKEN"
    
    echo "3. Deploying Bundle to Serverless..."
    databricks bundle deploy
    
elif [ "$ACTION" == "delete" ]; then
    echo "Deleting Bundle and Secrets..."
    databricks bundle destroy
    databricks secrets delete-scope greenmo_scope
else
    echo "Use 'create' or 'delete'"
fi
```

## 5. Analytics Outcomes
The final Silver tables allow for immediate SQL queries:
*   `SELECT * FROM greenmo_silver_rentals ORDER BY startTime DESC`: Latest trips with distance and cost.
*   `SELECT sum(remainingValueGross) FROM greenmo_silver_vouchers WHERE status = 'ACTIVE'`: Total available voucher balance.
