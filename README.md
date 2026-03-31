# GreenMobility Data Ingestion and Analytics

This project ingests and analyzes GreenMobility data. It fetches data from the gourban API and processes it.

It has three main parts:
1.  **Data Fetching Script (`src/get_data.py`)**: Gets raw data for rentals, vouchers, and invoices from the API.
2.  **Databricks Pipelines (`src/*_pipeline.py`)**: Processes raw data into Bronze, Silver, and Gold layers in Databricks using three separate pipelines:
    -   `greenmo_ingestion_rentals` (using `src/rentals_pipeline.py`)
    -   `greenmo_ingestion_vouchers` (using `src/vouchers_pipeline.py`)
    -   `greenmo_ingestion_invoices` (using `src/invoices_pipeline.py`)
3.  **Databricks Script (`databricks.sh`)**: Manages deployment, data upload, and pipeline execution for all three pipelines.

## Data Storage

Local data lands in the `data/` folder after fetching:
-   `data/rentals/`: Raw rental data, paginated into JSON files (e.g., `rentals_0.json`).
-   `data/vouchers/`: Raw voucher data, paginated into JSON files (e.g., `vouchers_0.json`).
-   `data/invoices/`: Raw invoice data, paginated into JSON files (e.g., `invoices_0.json`).

During deployment, this data uploads to Databricks Volume: `/Volumes/workspace/default/greenmo_raw_data/` with subfolders for each type.

## Databricks Processing Layers

The pipelines process data in Databricks:
-   **Rentals Pipeline**:
    -   Bronze: `greenmo_rentals_bronze`
    -   Silver: `greenmo_rentals_silver`
    -   Gold: `greenmo_rentals_gold_daily`, `greenmo_rentals_gold_summary`
-   **Vouchers Pipeline**:
    -   Bronze: `greenmo_vouchers_bronze`
    -   Silver: `greenmo_vouchers_silver`
-   **Invoices Pipeline**:
    -   Bronze: `greenmo_invoices_bronze`
    -   Silver: `greenmo_invoices_silver`

## APIs and Examples

Your `GREENMO_API_TOKEN` must be set as an environment variable.

### 1. Rentals API

Fetches completed rentals.

**CURL Example:**
```bash
curl -H "Authorization: Bearer $GREENMO_API_TOKEN" \
     "https://platform.api.gourban.services/v1/hb98ga69/front/rentals?state=ENDED&page=0&size=50"
```

**Example Return (one object):**
```json
{
  "id": 123456789,
  "rentalId": 0,
  "state": "ENDED",
  "startTime": "2026-03-30T17:18:59.000000Z",
  "driveStartTime": "2026-03-30T17:32:17.000000Z",
  "endTime": "2026-03-30T17:39:06.000000Z",
  "startKilometers": 58325.1,
  "endKilometers": 58327.9,
  "distance": 2.8,
  "startAddress": "Main Street 1, 1000 City, Country",
  "endAddress": "Second Street 2, 2000 City, Country",
  "branchId": 100,
  "currency": "DKK",
  "type": "PERSONAL",
  "vehicle": {
    "licensePlate": "AA00000",
    "code": "ABCDEF",
    "name": "Zoe 250km"
  },
  "invoiceId": 987654321,
  "appliedRebates": [
    {
      "type": "SUBSCRIPTION",
      "name": "GreenStudent",
      "amountNet": 3.28,
      "amountGross": 3.85
    }
  ]
}
```

### 2. Vouchers API

Fetches voucher details.

**CURL Example:**
```bash
curl -H "Authorization: Bearer $GREENMO_API_TOKEN" \
     "https://platform.api.gourban.services/v1/hb98ga69/front/vouchers?branchId=100&page=0&size=50"
```

**Example Return (one object):**
```json
{
  "id": 1234567,
  "type": "ConstraintVoucher",
  "voucherableCode": "voucher-code-placeholder",
  "branchId": 100,
  "name": "Charging reward \uD83D\uDD0B",
  "voucherType": "CASHBACK",
  "currency": "DKK",
  "valueNet": 48.0000,
  "remainingValueNet": -3.0500,
  "valueGross": 60.0000,
  "description": "Charging reward \uD83D\uDD0B",
  "signup": false,
  "validFrom": "2026-03-26T11:46:41.000000Z",
  "validUntil": "2025-05-25T11:46:41.000000Z",
  "status": "USED_UP",
  "applicablePriceType": "TIME_PRICE"
}
```

### 3. Invoices API

Fetches customer invoice details.

**CURL Example:**
```bash
curl -H "Authorization: Bearer $GREENMO_API_TOKEN" \
     "https://platform.api.gourban.services/v1/hb98ga69/front/invoices?branchId=100&page=0&size=50"
```

**Example Return (one object):**
```json
{
  "id": 5555555,
  "createdAt": "2026-03-23T10:41:57Z",
  "invoiceId": "2026-03-23-INV-5555555",
  "branchId": 100,
  "state": "PAID",
  "invoiceState": "SETTLED",
  "invoiceDate": "2026-03-23T10:41:57Z",
  "price": {
    "netPrice": 1440.0000,
    "containedTax": 360.0000,
    "grossPrice": 1800.0000
  },
  "currency": "DKK",
  "paymentId": 9999999,
  "type": "INVOICE",
  "retryable": false
}
```

## Usage

### 1. Set Environment variables

Create a `.env` file:
```
DATABRICKS_HOST=xxx
DATABRICKS_TOKEN=xxx
GREENMO_API_TOKEN=xxx
```

The GreenMobility access token is valid only for one day, i get it using Proxyman.

### 2. Fetch Data Locally

Download raw data from the API:
```bash
./databricks.sh get-data
```
This updates `data/rentals`, `data/vouchers`, and `data/invoices` with JSON files.

### 3. Deploy to Databricks

Upload data and deploy the Databricks pipeline:
```bash
./databricks.sh deploy
```
This:
- Sets up Databricks resources.
- Uploads local data.
- Deploys the bundle.
- Runs the pipeline.

### 4. Run Gemini CLI via Docker

Use Docker to run Gemini CLI in an isolated environment.

**Build the Docker Image:**
```bash
./docker.sh build
```
This creates the `gemini-jail` image.

**Run Gemini Container:**
```bash
./docker.sh run
```
This starts Gemini. Your workspace files are mounted, so you can interact with the project.

### 5. Delete Databricks Resources

Clean up Databricks resources:
```bash
./databricks.sh delete
```
This removes the schema, data volume, and bundle.
