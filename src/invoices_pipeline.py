# Databricks notebook source

import os
from pyspark import pipelines as dp
from pyspark.sql.functions import col, current_timestamp, to_timestamp, year, month, sum as spark_sum, count, when
from pyspark.sql.types import StructType, StructField, DoubleType

RAW_DATA_VOLUME_PATH = "/Volumes/workspace/default/greenmo_raw_data/"


@dp.materialized_view(
    name="greenmo_invoices_bronze",
    comment="Raw invoice data from JSON files",
    table_properties={
        "delta.columnMapping.mode": "name"
    }
)
def greenmo_invoices_bronze():
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

@dp.materialized_view(
    name="greenmo_invoices_gold_yearly",
    comment="Spending aggregation by year"
)
def greenmo_invoices_gold_yearly():
    return (
        spark.read.table("greenmo_invoices_silver")
        .withColumn("year", year(col("invoice_date")))
        .groupBy("year")
        .agg(
            spark_sum("grossPrice").alias("total_spent_gross"),
            spark_sum("netPrice").alias("total_spent_net"),
            count("invoice_primary_id").alias("invoice_count")
        )
        .orderBy("year")
    )

@dp.materialized_view(
    name="greenmo_invoices_gold_monthly",
    comment="Spending aggregation by year and month"
)
def greenmo_invoices_gold_monthly():
    return (
        spark.read.table("greenmo_invoices_silver")
        .withColumn("year", year(col("invoice_date")))
        .withColumn("month", month(col("invoice_date")))
        .groupBy("year", "month")
        .agg(
            spark_sum("grossPrice").alias("total_spent_gross"),
            spark_sum("netPrice").alias("total_spent_net"),
            count("invoice_primary_id").alias("invoice_count")
        )
        .orderBy("year", "month")
    )

@dp.materialized_view(
    name="greenmo_invoices_gold_trips",
    comment="Spending analysis on minutes and long trips"
)
def greenmo_invoices_gold_trips():
    invoices = spark.read.table("greenmo_invoices_silver")
    rentals = spark.read.table("greenmo_rentals_silver")
    
    # Note: Using left join as some invoices might be for buying minutes (no rental)
    joined = invoices.join(rentals, invoices.invoice_primary_id == rentals.invoice_id, "left")
    
    return (
        joined.select(
            invoices.invoice_primary_id,
            invoices.grossPrice,
            rentals.rental_drive_duration_minutes,
            when(rentals.rental_id.isNull(), "minute_purchase")
            .when(rentals.rental_drive_duration_minutes >= 180, "long_trip")
            .otherwise("regular_trip")
            .alias("category")
        )
        .groupBy("category")
        .agg(
            spark_sum("grossPrice").alias("total_spent_gross"),
            count("invoice_primary_id").alias("count")
        )
    )
