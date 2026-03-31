# GreenMobility Data Ingestion and Analytics

This project provides a system to ingest and analyze data related to GreenMobility services. It fetches data from the GreenMobility API and processes it into a structured format for analysis.

The system includes three main components:
1.  **Data Fetching Script (`src/get_data.py`)**: This script retrieves raw data for rentals, vouchers, and invoices from the GreenMobility API.
2.  **Databricks Ingestion Pipeline (`src/ingestion_pipeline.py`)**: This script processes the raw data into different layers (Bronze, Silver, Gold) within Databricks.
3.  **Databricks Deployment Script (`databricks.sh`)**: This script manages the deployment, data upload, and execution of the Databricks pipeline.

## Data Storage Structure

After running the data fetching script locally, data is stored in the following directory structure within the `data/` folder:

-   `data/rentals/`: Stores raw rental data, paginated into individual JSON files (e.g., `rentals_0.json`, `rentals_1.json`).
-   `data/vouchers/`: Stores raw voucher data, paginated into individual JSON files (e.g., `vouchers_0.json`, `vouchers_1.json`).
-   `data/invoices/`: Stores raw invoice data, paginated into individual JSON files (e.g., `invoices_0.json`, `invoices_1.json`).

During deployment, this data is uploaded to a Databricks Unity Catalog Volume at `/Volumes/workspace/default/greenmo_raw_data/` with subdirectories for each data type.

## Data Processing Layers (Databricks)

The Databricks pipeline processes data through the following layers:

-   **Bronze Layer**: Contains the raw, ingested JSON data as stored in the Databricks Volume. Tables: `greenmo_rentals_bronze`, `greenmo_vouchers_bronze`, `greenmo_invoices_bronze`.
-   **Silver Layer**: Contains cleaned, validated, and transformed data. Fields are aliased for clarity and consistency, and data quality checks are applied. Tables: `greenmo_rentals_silver`, `greenmo_vouchers_silver`, `greenmo_invoices_silver`.
-   **Gold Layer**: Contains aggregated and summarized data optimized for analytics. Tables: `greenmo_rentals_gold_daily`, `greenmo_rentals_gold_summary`.

## APIs and How to Call Them

The system interacts with the GreenMobility API. Ensure you have your `GREENMO_API_TOKEN` set as an environment variable.

### 1. Rentals API

Fetches details about completed rentals.

**Curl Example:**
```bash
curl -H "Authorization: Bearer $GREENMO_API_TOKEN" 
    https://platform.api.gourban.services/v1/hb98ga69/front/rentals?page=0&size=50&state=ENDED
```

**Returns:** A JSON array of rental objects, each containing details like `id`, `startTime`, `endTime`, `distance`, `vehicle`, `price`, etc.

### 2. Vouchers API

Fetches details about available and used vouchers.

**Curl Example:**
```bash
curl -H "Authorization: Bearer $GREENMO_API_TOKEN" 
    https://platform.api.gourban.services/v1/hb98ga69/front/vouchers?branchId=100&page=0&size=50
```

**Returns:** A JSON array of voucher objects, each with properties like `id`, `name`, `voucherType`, `valueNet`, `valueGross`, `validFrom`, `validUntil`, `status`.

### 3. Invoices API

Fetches details about customer invoices.

**Curl Example:**
```bash
curl -H "Authorization: Bearer $GREENMO_API_TOKEN" 
    "https://platform.api.gourban.services/v1/hb98ga69/front/invoices?branchId=100&page=0&size=50"
```

**Returns:** A JSON array of invoice objects, including `id`, `createdAt`, `invoiceId`, `branchId`, `state`, `invoiceDate`, `price` (with `netPrice`, `containedTax`, `grossPrice`), and `currency`.

## Usage

### 1. Set Environment Variables

Create a `.env` in the root of the project:
```
DATABRICKS_HOST=xxx
DATABRICKS_TOKEN=xxx
GREENMO_API_TOKEN=xxx
```

### 2. Fetch Data Locally

Run the Python script to download raw data from the API:
```bash
./databricks.sh get-data
```
This will create the `data/rentals`, `data/vouchers`, and `data/invoices` directories with paginated JSON files.

### 3. Deploy to Databricks

Upload the data and deploy the Databricks pipeline:
```bash
./databricks.sh deploy
```
This command will:
- Create necessary Databricks resources (Volume, directories).
- Upload the local data to the Databricks Volume.
- Deploy the Databricks bundle.
- Run the ingestion pipeline.

### 4. Delete Databricks Resources

To clean up all created resources on Databricks:
```bash
./databricks.sh delete
```
This will delete the schema, data volume, and the bundle.
