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

## 6. New API Specification (GoUrban Platform)

GreenMobility has migrated to the GoUrban platform. The new API is a RESTful service.

### 6.1 Authentication

#### 6.1.1 Login (Email Code)
To obtain an initial `accessToken` and `refreshToken`.
*   **Endpoint:** `POST https://platform.api.gourban.services/v1/hb98ga69/auth/api/hb98ga69/sign-in-email-code`
*   **Curl Example:**
    ```bash
    curl 'https://platform.api.gourban.services/v1/hb98ga69/auth/api/hb98ga69/sign-in-email-code' \
      -X POST \
      -H 'Content-Type: application/json' \
      -H 'app-version: 3.9.30454' \
      -H 'os: iOS' \
      --data-raw '{"email":"USER_EMAIL","code":"VERIFICATION_CODE"}'
    ```

#### 6.1.2 Refreshing the Token
To generate a new `accessToken` once the current one expires.
*   **Endpoint:** `POST https://platform.api.gourban.services/v1/hb98ga69/auth/tokens/refresh` (or similar GoUrban pattern)
*   **Alternative GoUrban Endpoint:** `POST https://api.gourban.co/v1/auth/refresh`
*   **Curl Example (Standard Pattern):**
    ```bash
    curl -X POST \
      --url 'https://platform.api.gourban.services/v1/hb98ga69/auth/tokens/refresh' \
      --header 'Content-Type: application/json' \
      --data '{
        "refresh_token": "YOUR_REFRESH_TOKEN",
        "access_token": "YOUR_CURRENT_OR_EXPIRED_ACCESS_TOKEN"
      }'
    ```
*   **Note:** GoUrban refresh tokens are typically **single-use**. A successful refresh returns a *new* access token and a *new* refresh token.

### 6.2 Key Analytics Endpoints

#### 6.2.1 Overall User Statistics
Provides aggregate data like total rides, kilometers, and CO2 saved.
*   **Endpoint:** `GET https://platform.api.gourban.services/v1/hb98ga69/front/customers`
*   **Curl Example:**
    ```bash
    curl -H "Authorization: Bearer $TOKEN" \
         "https://platform.api.gourban.services/v1/hb98ga69/front/customers"
    ```
*   **Key Data Fields:** `rides`, `ridesKilometers`, `co2SavedInG`, `balances`.

#### 6.2.2 Trip History (Rentals)
Retrieves detailed information about past trips.
*   **Endpoint:** `GET https://platform.api.gourban.services/v1/hb98ga69/front/rentals?page=0&size=20&state=ENDED&state=ENDED_NO_MOVEMENT`
*   **Curl Example:**
    ```bash
    curl -H "Authorization: Bearer $TOKEN" \
         "https://platform.api.gourban.services/v1/hb98ga69/front/rentals?page=0&size=20&state=ENDED&state=ENDED_NO_MOVEMENT"
    ```
*   **Key Data Fields:** `id`, `startTime`, `endTime`, `distance`, `startAddress`, `endAddress`, `vehicle.licensePlate`, `price.priceGross`.

#### 6.2.3 Voucher & Discount History
Lists active vouchers and their remaining values.
*   **Endpoint:** `GET https://platform.api.gourban.services/v1/hb98ga69/front/vouchers?branchId=2&page=0&size=30&active`
*   **Curl Example:**
    ```bash
    curl -H "Authorization: Bearer $TOKEN" \
         "https://platform.api.gourban.services/v1/hb98ga69/front/vouchers?branchId=2&page=0&size=30&active"
    ```
*   **Key Data Fields:** `name`, `voucherType`, `valueGross`, `remainingValueGross`, `validUntil`.

#### 6.2.4 Balance Overview
*   **Endpoint:** `GET https://platform.api.gourban.services/v1/hb98ga69/front/balances?branchId=2`
*   **Curl Example:**
    ```bash
    curl -H "Authorization: Bearer $TOKEN" \
         "https://platform.api.gourban.services/v1/hb98ga69/front/balances?branchId=2"
    ```
*   **Key Data Fields:** `remainingVouchersGrossValue`.

#### 6.2.5 Unpaid Invoices
*   **Endpoint:** `GET https://platform.api.gourban.services/v1/hb98ga69/front/invoices?unpaid=true`
*   **Curl Example:**
    ```bash
    curl -H "Authorization: Bearer $TOKEN" \
         "https://platform.api.gourban.services/v1/hb98ga69/front/invoices?unpaid=true"
    ```

#### 6.2.6 Other Interesting Endpoints
*   **Subscriptions:** `GET https://platform.api.gourban.services/v1/hb98ga69/front/subscriptions`
*   **Packages:** `GET https://platform.api.gourban.services/v1/hb98ga69/front/packages`
*   **Promotions:** `GET https://platform.api.gourban.services/v1/hb98ga69/front/promotions?branchId=2`
*   **Loyalty Cards:** `GET https://platform.api.gourban.services/v1/hb98ga69/front/loyalty-cards`

### 6.3 Analytics Potential
The new API provides richer data per trip than the old one, including:
*   **Distance/Kilometers:** Enables analysis of efficiency (Dkk per km).
*   **Address Data:** Allows for spatial analysis of start/end locations.
*   **Vehicle Details:** More granular data on car categories and specific models used.
*   **CO2 Savings:** Direct metric for environmental impact reporting.
