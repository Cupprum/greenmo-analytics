# Databricks notebook source

import os
from pyspark import pipelines as dp
from pyspark.sql.functions import col, current_timestamp, to_timestamp, count, sum as spark_sum

RAW_DATA_VOLUME_PATH = "/Volumes/workspace/default/greenmo_raw_data/"

@dp.materialized_view(
    name="greenmo_vouchers_bronze",
    comment="Raw voucher data from JSON files",
    table_properties={
        "delta.columnMapping.mode": "name"
    }
)
def greenmo_vouchers_bronze():
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
            col("voucherableCode").alias("voucher_id"), # Use 'voucherableCode' as unique identifier for voucher
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

@dp.materialized_view(
    name="greenmo_vouchers_gold_charging",
    comment="Summary of vouchers received by charging cars"
)
def greenmo_vouchers_gold_charging():
    return (
        spark.read.table("greenmo_vouchers_silver")
        .filter(col("voucher_name").contains("Charging reward"))
        .agg(
            count("voucher_id").alias("total_charging_vouchers"),
            spark_sum("value_gross").alias("total_value_gross"),
            spark_sum("value_net").alias("total_value_net")
        )
    )
