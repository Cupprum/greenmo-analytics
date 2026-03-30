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
        echo ">>> Running get_trips.py..."
        uv run get_trips.py
        ;;
    deploy)
        echo ">>> [DEPLOY] Starting Databricks Deployment..."

        echo ">>> Ensuring Unity Catalog Volume exists..."
        databricks volumes create workspace default greenmo_raw_data MANAGED 2>/dev/null || echo "Volume already exists."
        databricks fs mkdir dbfs:/Volumes/workspace/default/greenmo_raw_data/trips 2>/dev/null || true

        echo ">>> Uploading data to Volume..."
        databricks fs cp \
            --recursive \
            --overwrite \
            data/trips/ dbfs:/Volumes/workspace/default/greenmo_raw_data/trips/

        echo ">>> Deploying bundle..."
        databricks bundle deploy

        echo ">>> Running Pipeline..."
        databricks bundle run greenmo_pipeline

        echo ">>> Deployment and Execution Successful!"
        ;;
    delete)
        echo ">>> [DELETE] Removing all resources from Databricks..."

        echo ">>> Deleting Schema (Tables & Materialized Views)..."
        databricks schemas delete workspace.greenmo_raw_data --force 2>/dev/null || echo "Schema not found."

        echo ">>> Deleting Data Volume..."
        databricks volumes delete workspace.default.greenmo_raw_data 2>/dev/null || echo "Volume not found."


        echo ">>> Destroying bundle..."
        databricks bundle destroy --auto-approve || echo "Bundle already destroyed or not found."

        echo ">>> Cleanup complete!"
        ;;
    *)
        echo "Usage: $0 {get-data|deploy|delete}"
        exit 1
        ;;
esac
