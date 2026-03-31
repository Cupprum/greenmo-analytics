# Databricks notebook source

import os
from pyspark import pipelines as dp
from pyspark.sql.functions import col, current_timestamp, to_timestamp
from pyspark.sql.types import StructType, StructField, DoubleType

# Define base path for raw data volume
RAW_DATA_VOLUME_PATH = "/Volumes/workspace/default/greenmo_raw_data/"

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
