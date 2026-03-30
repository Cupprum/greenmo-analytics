# Specification: GreenMobility Data Analysis (Legacy Go Implementation)

This document summarizes the functionality, data sources, and outcomes of the existing Go-based GreenMobility data analysis tool. This serves as a baseline for migrating the logic to a Databricks data product.

## 1. Overview
The current tool fetches personal usage data from GreenMobility's APIs, processes it to calculate various statistics, and outputs the results to the console. It also caches the raw data in JSON files to avoid redundant API calls.

## 2. API Integrations

### 2.1 Fleetbird REST API (Reservations)
*   **Base URL:** `https://greenmobility.frontend.fleetbird.eu/api/prod/v1.06`
*   **Authentication:** Bearer Token (provided via `GREENMO_TOKEN` environment variable).
*   **Endpoints:**
    *   `GET /me/`: Retrieves basic user information (ID, Reference, Name, Email).
    *   `GET /users/{uid}/reservations/pages/{pageId}/?orderBy=desc`: Paginated list of reservations.
*   **Data Captured:**
    *   `licencePlate`: Car identifier.
    *   `openCallSuccessfulTime`: Start timestamp (Unix).
    *   `closeCallSuccessfulTime`: End timestamp (Unix).

### 2.2 GraphQL API (Financials)
*   **Base URL:** `https://street.greenmobility.com/api`
*   **Authentication:** 
    *   Step 1: `GET /go/drive/account` with user details (Reference, ID, Name, Email) as query parameters to obtain a `driveToken` cookie.
    *   Step 2: Use `driveToken` in subsequent GraphQL POST requests.
*   **Endpoint:** `POST /drive/graphql`
*   **Queries:**
    *   `GetInvoices`: Retrieves a list of invoices with dates and total amounts.
    *   `getCreditVouchers`: Retrieves a list of vouchers with values and grant dates.
*   **Data Captured:**
    *   Invoices: Date and Total Amount (converted to Dkk).
    *   Vouchers: Value (minutes) and Grant Date.

## 3. Data Processing & Logic

### 3.1 Reservation Analytics
*   **Total Reservations:** Count of all fetched reservation records.
*   **Unique Cars:** Count of unique license plates driven.
*   **Trip Categorization:**
    *   **Trips:** Defined as reservations longer than 120 minutes (assumed pre-paid or long-duration packages).
    *   **Pay-As-You-Go:** Defined as reservations of 120 minutes or less.
*   **Temporal Analysis:** Total minutes driven aggregated by year.

### 3.2 Financial Analytics
*   **Total Spent:** Sum of all invoice amounts (in Dkk).
*   **Voucher Categorization:**
    *   **Free Minutes:** Vouchers with a value of 40 minutes or less.
    *   **Bought Minutes:** Vouchers with a value greater than 40 minutes.
*   **Counts:** Total number of invoices and vouchers.

## 4. User-Facing Outcomes
The user interacts with the tool via a CLI. The primary outcomes are:
1.  **Terminal Logs:** Summary statistics including:
    *   Total and unique car counts.
    *   Breakdown of minutes (Trip vs. Pay-As-You-Go).
    *   Yearly driving summaries.
    *   Total spend and voucher balance (Free vs. Bought).
2.  **Data Cache:** Local JSON files (`reservations.json`, `financials.json`) containing the raw API responses.

## 5. Migration Considerations for Databricks
*   **API Changes:** GreenMobility has changed their APIs, necessitating a rewrite of the fetching logic.
*   **Data Ingestion:** Move from local JSON caching to Delta Lake tables.
*   **Processing:** Replace Go logic with PySpark or Spark SQL.
*   **Visualization:** Transition from CLI logs to Databricks Dashboards or Notebook visualizations.
