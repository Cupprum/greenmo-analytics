# Databricks notebook source

from pyspark import pipelines as dp
from pyspark.sql.functions import col, current_timestamp, to_timestamp, year, month, sum as spark_sum, count, when, round as spark_round
from pyspark.sql.types import StructType, StructField, DoubleType


@dp.materialized_view(
    name="invoices_bronze",
    comment="Raw invoice data from JSON files",
    table_properties={
        "delta.columnMapping.mode": "name"
    }
)
def invoices_bronze():
    return (
        spark.read
        .format("json")
        .option("multiLine", "true")
        .load("/Volumes/workspace/default/greenmo_raw_data/invoices/")
        .withColumn("ingestion_time", current_timestamp())
    )

@dp.materialized_view(
    name="invoices_silver",
    comment="Cleaned and transformed invoice data"
)
@dp.expect_or_drop("valid_invoice_primary_id", "invoice_primary_id IS NOT NULL")
def invoices_silver():
    price_schema = StructType([
        StructField("netPrice", DoubleType(), True),
        StructField("containedTax", DoubleType(), True),
        StructField("grossPrice", DoubleType(), True)
    ])

    return (
        spark.read.table("invoices_bronze")
        .select(
            col("id").alias("invoice_primary_id"),
            to_timestamp(col("invoiceDate")).alias("invoice_date"),
            col("price").cast(price_schema).alias("price_details")
        )
        .select(
            "invoice_primary_id",
            "invoice_date",
            "price_details.netPrice",
            "price_details.grossPrice"
        )
        .dropDuplicates(["invoice_primary_id"])
    )

@dp.materialized_view(
    name="invoices_gold_yearly",
    comment="Spending aggregation by year"
)
def invoices_gold_yearly():
    return (
        spark.read.table("invoices_silver")
        .withColumn("year", year(col("invoice_date")))
        .groupBy("year")
        .agg(
            spark_round(spark_sum("grossPrice"), 2).alias("total_spent_gross"),
            spark_round(spark_sum("netPrice"), 2).alias("total_spent_net"),
            count("invoice_primary_id").alias("invoice_count")
        )
        .orderBy("year")
    )

@dp.materialized_view(
    name="invoices_gold_monthly",
    comment="Spending aggregation by year and month"
)
def invoices_gold_monthly():
    return (
        spark.read.table("invoices_silver")
        .withColumn("year", year(col("invoice_date")))
        .withColumn("month", month(col("invoice_date")))
        .groupBy("year", "month")
        .agg(
            spark_round(spark_sum("grossPrice"), 2).alias("total_spent_gross"),
            spark_round(spark_sum("netPrice"), 2).alias("total_spent_net"),
            count("invoice_primary_id").alias("invoice_count")
        )
        .orderBy("year", "month")
    )

@dp.materialized_view(
    name="invoices_gold_summary",
    comment="Overall spending summary"
)
def invoices_gold_summary():
    return (
        spark.read.table("invoices_silver")
        .agg(
            spark_round(spark_sum("grossPrice"), 2).alias("total_spent_gross"),
            spark_round(spark_sum("netPrice"), 2).alias("total_spent_net"),
            count("invoice_primary_id").alias("invoice_count")
        )
    )
