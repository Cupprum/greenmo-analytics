# Databricks notebook source

from pyspark import pipelines as dp
from pyspark.sql.functions import col, current_timestamp, count, avg, sum, min, max, to_timestamp, round as spark_round, to_date
from pyspark.sql.types import StructType, StructField, DoubleType

# Define base path for raw data volume
RAW_DATA_VOLUME_PATH = "/Volumes/workspace/default/greenmo_raw_data/"

# --- Rentals Data Processing ---

@dp.materialized_view(
    name="greenmo_rentals_bronze",
    comment="Raw rental data from JSON files",
    table_properties={
        "delta.columnMapping.mode": "name"
    }
)
def greenmo_rentals_bronze():
    # Assumes data is stored in RAW_DATA_VOLUME_PATH/rentals/
    return (
        spark.read
        .format("json")
        .option("multiLine", "true")
        .load(os.path.join(RAW_DATA_VOLUME_PATH, "rentals/"))
        .withColumn("ingestion_time", current_timestamp())
    )

@dp.materialized_view(
    name="greenmo_rentals_silver",
    comment="Cleaned and transformed rental data"
)
@dp.expect_or_drop("valid_rental_id", "rental_id IS NOT NULL")
@dp.expect_or_drop("valid_rental_times", "rental_drive_start_time IS NOT NULL AND rental_end_time IS NOT NULL")
def greenmo_rentals_silver():
    return (
        spark.read.table("greenmo_rentals_bronze")
        .select(
            col("id").alias("rental_id"),
            col("branchId").alias("branch_id"),
            col("invoiceId").alias("invoice_id"),
            col("state").alias("rental_state"),
            col("type").alias("rental_type"),
            to_timestamp(col("startTime")).alias("rental_start_time"),
            to_timestamp(col("driveStartTime")).alias("rental_drive_start_time"),
            to_timestamp(col("endTime")).alias("rental_end_time"),
            col("distance").alias("rental_distance_km"),
            col("currency"),
            col("startAddress").alias("rental_start_address"),
            col("endAddress").alias("rental_end_address"),
            col("startKilometers").alias("rental_start_km"),
            col("endKilometers").alias("rental_end_km"),
            col("vehicle.licensePlate").alias("vehicle_plate"),
            col("vehicle.name").alias("vehicle_name"),
            col("rideMode").alias("rental_ride_mode"),
            col("ingestion_time")
        )
        .dropDuplicates(["rental_id"]) # Use the new alias for rental_id
        .withColumn("rental_drive_duration_minutes", 
            spark_round((col("rental_end_time").cast("long") - col("rental_drive_start_time").cast("long")) / 60, 2))
    )

@dp.materialized_view(
    name="greenmo_rentals_gold_daily",
    comment="Daily rental aggregations"
)
def greenmo_rentals_gold_daily():
    return (
        spark.read.table("greenmo_rentals_silver")
        .withColumn("rental_date", to_date(col("rental_drive_start_time")))
        .groupBy("rental_date", "branch_id")
        .agg(
            count("rental_id").alias("total_rentals"),
            spark_round(avg("rental_distance_km"), 2).alias("avg_distance_km"),
            spark_round(sum("rental_distance_km"), 2).alias("total_distance_km"),
            spark_round(avg("rental_drive_duration_minutes"), 2).alias("avg_duration_min"),
            spark_round(max("rental_drive_duration_minutes"), 2).alias("max_duration_min")
        )
        .orderBy("rental_date", "branch_id")
    )

@dp.materialized_view(
    name="greenmo_rentals_gold_summary",
    comment="Overall rental summary"
)
def greenmo_rentals_gold_summary():
    return (
        spark.read.table("greenmo_rentals_silver")
        .groupBy("branch_id")
        .agg(
            count("rental_id").alias("total_rentals"),
            spark_round(avg("rental_distance_km"), 2).alias("avg_distance_km"),
            spark_round(sum("rental_distance_km"), 2).alias("total_distance_km"),
            spark_round(avg("rental_drive_duration_minutes"), 2).alias("avg_duration_min"),
            min("rental_drive_start_time").alias("first_rental"),
            max("rental_end_time").alias("last_rental")
        )
    )

# --- Vouchers Data Processing ---

@dp.materialized_view(
    name="greenmo_vouchers_bronze",
    comment="Raw voucher data from JSON files",
    table_properties={
        "delta.columnMapping.mode": "name"
    }
)
def greenmo_vouchers_bronze():
    # Assumes data is stored in RAW_DATA_VOLUME_PATH/vouchers/
    return (
        spark.read
        .format("json")
        .option("multiLine", "true")
        .load(os.path.join(RAW_DATA_VOLUME_PATH, "vouchers/"))
        .withColumn("ingestion_time", current_timestamp())
    )

@dp.materialized_view(
    name="greenmo_vouchers_silver",
    comment="Cleaned and transformed voucher data"
)
@dp.expect_or_drop("valid_voucher_id", "voucher_id IS NOT NULL")
def greenmo_vouchers_silver():
    return (
        spark.read.table("greenmo_vouchers_bronze")
        .select(
            col("id").alias("voucher_id"), # Use 'id' from JSON as unique identifier for voucher
            col("branchId").alias("branch_id"),
            col("name").alias("voucher_name"),
            col("voucherType").alias("voucher_type"),
            col("currency"),
            col("valueNet").alias("value_net"),
            col("remainingValueNet").alias("remaining_value_net"),
            col("valueGross").alias("value_gross"),
            col("description"),
            col("signup"),
            to_timestamp(col("validFrom")).alias("valid_from"),
            to_timestamp(col("validUntil")).alias("valid_until"),
            col("status"),
            col("applicablePriceType").alias("applicable_price_type"),
            col("ingestion_time")
        )
        .dropDuplicates(["voucher_id"])
    )

# --- Invoices Data Processing ---

@dp.materialized_view(
    name="greenmo_invoices_bronze",
    comment="Raw invoice data from JSON files",
    table_properties={
        "delta.columnMapping.mode": "name"
    }
)
def greenmo_invoices_bronze():
    # Assumes data is stored in RAW_DATA_VOLUME_PATH/invoices/
    return (
        spark.read
        .format("json")
        .option("multiLine", "true")
        .load(os.path.join(RAW_DATA_VOLUME_PATH, "invoices/"))
        .withColumn("ingestion_time", current_timestamp())
    )

@dp.materialized_view(
    name="greenmo_invoices_silver",
    comment="Cleaned and transformed invoice data"
)
@dp.expect_or_drop("valid_invoice_primary_id", "invoice_primary_id IS NOT NULL")
def greenmo_invoices_silver():
    # Define schema for nested price object to handle potential variations
    price_schema = StructType([
        StructField("netPrice", DoubleType(), True),
        StructField("containedTax", DoubleType(), True),
        StructField("grossPrice", DoubleType(), True)
    ])

    return (
        spark.read.table("greenmo_invoices_bronze")
        .select(
            col("id").alias("invoice_primary_id"), # Use 'id' from JSON as primary key
            col("createdAt").alias("created_at"),
            col("invoiceId").alias("invoice_reference_id"), # The string invoice ID
            col("branchId").alias("branch_id"),
            col("state").alias("invoice_state_api"), # Differentiate from invoiceState
            col("invoiceState").alias("invoice_state_settlement"),
            to_timestamp(col("invoiceDate")).alias("invoice_date"),
            col("currency"),
            col("paymentId").alias("payment_id"),
            col("type").alias("invoice_type"),
            col("retryable"),
            # Explicitly cast price to schema for robust handling
            col("price").cast(price_schema).alias("price_details"),
            col("ingestion_time")
        )
        .select(
            "invoice_primary_id",
            "created_at",
            "invoice_reference_id",
            "branch_id",
            "invoice_state_api",
            "invoice_state_settlement",
            "invoice_date",
            "currency",
            "payment_id",
            "invoice_type",
            "retryable",
            "price_details.netPrice",
            "price_details.containedTax",
            "price_details.grossPrice",
            "ingestion_time"
        )
        .dropDuplicates(["invoice_primary_id"])
    )
