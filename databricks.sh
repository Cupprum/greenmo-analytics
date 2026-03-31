#!/usr/bin/env bash

set -e
set -u
set -o pipefail


load_env_file() {
    local env_file="$1"
    if [[ -f "$env_file" ]]; then
        set -a
        source "$env_file"
        set +a
    else
        echo "Error: $env_file not found" >&2
        return 1
    fi
}

load_env_file "../.env"

if [ -z "$DATABRICKS_HOST" ] || [ -z "$DATABRICKS_TOKEN" ]; then
    echo "Error: DATABRICKS_HOST and DATABRICKS_TOKEN must be set."
    exit 1
fi
case ${1:-} in
    get-data)
        echo ">>> [GET DATA] Getting data from Greenmobility..."

        cd src
        echo ">>> Running get_data.py..."
        uv run get_data.py
        ;;
    deploy)
        echo ">>> [DEPLOY] Starting Databricks Deployment..."

        echo ">>> Ensuring Unity Catalog Volume exists..."
        databricks volumes create workspace default greenmo_raw_data MANAGED 2>/dev/null || echo "Volume 'greenmo_raw_data' already exists or could not be created."
        
        echo ">>> Creating directories in Databricks Volume..."
        databricks fs mkdir dbfs:/Volumes/workspace/default/greenmo_raw_data/rentals 2>/dev/null || echo "Directory 'rentals' already exists."
        databricks fs mkdir dbfs:/Volumes/workspace/default/greenmo_raw_data/vouchers 2>/dev/null || echo "Directory 'vouchers' already exists."
        databricks fs mkdir dbfs:/Volumes/workspace/default/greenmo_raw_data/invoices 2>/dev/null || echo "Directory 'invoices' already exists."

        echo ">>> Uploading data to Volume..."
        echo "Uploading rentals data..."
        databricks fs cp --recursive data/rentals/ dbfs:/Volumes/workspace/default/greenmo_raw_data/rentals/ 2>/dev/null || echo "No new rentals data to upload or error occurred."
        echo "Uploading vouchers data..."
        databricks fs cp --recursive data/vouchers/ dbfs:/Volumes/workspace/default/greenmo_raw_data/vouchers/ 2>/dev/null || echo "No new vouchers data to upload or error occurred."
        echo "Uploading invoices data..."
        databricks fs cp --recursive data/invoices/ dbfs:/Volumes/workspace/default/greenmo_raw_data/invoices/ 2>/dev/null || echo "No new invoices data to upload or error occurred."


        echo ">>> Deploying bundle..."
        databricks bundle deploy

        echo ">>> Running Pipeline..."
        databricks bundle run greenmo_pipeline

        echo ">>> Deployment and Execution Successful!"
        ;;
    delete)
        echo ">>> [DELETE] Removing all resources from Databricks..."

        echo ">>> Deleting Schema (Tables & Materialized Views)..."
        databricks schemas delete workspace.greenmobility --force 2>/dev/null || echo "Schema 'greenmobility' not found or could not be deleted."

        echo ">>> Deleting Data Volume..."
        databricks volumes delete workspace.default.greenmo_raw_data 2>/dev/null || echo "Volume 'greenmo_raw_data' not found or could not be deleted."

        echo ">>> Destroying bundle..."
        databricks bundle destroy --auto-approve 2>/dev/null || echo "Bundle already destroyed or not found."

        echo ">>> Cleanup complete!"
        ;;
    *)
        echo "Usage: $0 {get-data|deploy|delete}"
        exit 1
        ;;
esac
