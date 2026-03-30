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
    deploy)
        echo ">>> [DEPLOY] Starting Databricks Deployment..."
        
        echo ">>> Creating secret..."
        databricks secrets create-scope greenmo
        databricks secrets put-secret greenmo api_token --string-value $GREENMO_API_TOKEN

        echo ">>> Deploying bundle..."
        databricks bundle deploy

        echo ">>> Running Pipeline..."
        databricks bundle run greenmo_pipeline

        echo ">>> Deployment and Execution Successful!"
        ;;
    delete)
        echo ">>> [DELETE] Removing all resources from Databricks..."

        echo ">>> Deleting secret..."
        databricks secrets delete-secret greenmo api_token

        echo ">>> Destroying bundle..."
        databricks bundle destroy --auto-approve || echo "Bundle already destroyed or not found."

        echo ">>> Cleanup complete!"
        ;;
    *)
        echo "Usage: ./$0 {deploy|delete}"
        exit 1
        ;;
esac
