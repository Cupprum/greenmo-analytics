# Databricks notebook source

from pyspark import pipelines as dp
from pyspark.sql.functions import col, current_timestamp, count, year, month, sum as spark_sum


@dp.materialized_view(
    name="vouchers_bronze",
    comment="Raw voucher data from JSON files",
    table_properties={
        "delta.columnMapping.mode": "name"
    }
)
def vouchers_bronze():
    return (
        spark.read
        .format("json")
        .option("multiLine", "true")
        .load("/Volumes/workspace/default/greenmo_raw_data/vouchers/")
        .withColumn("ingestion_time", current_timestamp())
    )

@dp.materialized_view(
    name="vouchers_silver",
    comment="Cleaned and transformed voucher data"
)
@dp.expect_or_drop("valid_voucher_id", "voucher_id IS NOT NULL")
def vouchers_silver():
    return (
        spark.read.table("vouchers_bronze")
        .select(
            col("voucherableCode").alias("voucher_id"),
            col("name").alias("voucher_name"),
            col("valueNet").alias("value_net"),
            col("valueGross").alias("value_gross"),
            col("validFrom").alias("valid_from")
        )
        .dropDuplicates(["voucher_id"])
    )

@dp.materialized_view(
    name="vouchers_gold_charging_monthly",
    comment="Monthly vouchers for charging aggregations"
)
def vouchers_gold_charging_monthly():
    return (
        spark.read.table("vouchers_silver")
        .filter(col("voucher_name").contains("Charging"))
        .withColumn("voucher_year", year(col("valid_from")))
        .withColumn("voucher_month", month(col("valid_from")))
        .groupBy("voucher_year", "voucher_month")
        .agg(
            count("voucher_id").alias("total_charging_vouchers"),
            spark_sum("value_gross").alias("total_value_gross"),
            spark_sum("value_net").alias("total_value_net")
        )
        .orderBy("voucher_year", "voucher_month")
    )

@dp.materialized_view(
    name="vouchers_gold_charging_summary",
    comment="Summary of vouchers received by charging cars"
)
def vouchers_gold_charging_summary():
    return (
        spark.read.table("vouchers_silver")
        .filter(col("voucher_name").contains("Charging"))
        .agg(
            count("voucher_id").alias("total_charging_vouchers"),
            spark_sum("value_gross").alias("total_value_gross"),
            spark_sum("value_net").alias("total_value_net")
        )
    )