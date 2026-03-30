# Databricks notebook source
import dlt
from pyspark.sql.functions import from_json, col, current_timestamp, count, avg, sum
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType

# === BRONZE: Load raw JSON files ===
@dlt.table(
    name="greenmo_trips_bronze",
    comment="Raw trip data from JSON files"
)
def bronze_trips_data():
    return (
        spark.read
        .format("json")
        .option("multiLine", "true")
        .load("/Volumes/workspace/default/greenmo_raw_data/trips/")
        .withColumn("ingestion_time", current_timestamp())
    )

# # === SILVER: Clean and parse ===
# @dlt.table(
#     name="silver_trips_data",
#     comment="Cleaned trip data"
# )
# @dlt.expect_or_drop("valid_id", "id IS NOT NULL")
# def silver_trips_data():
#     # TODO: Update schema to match your actual data structure
#     return (
#         dlt.read("bronze_trips_data")
#         .select("*", "ingestion_time")
#         .dropDuplicates(["id"])
#     )

# # === GOLD: Aggregates ===
# @dlt.table(
#     name="gold_trip_metrics",
#     comment="Trip aggregations"
# )
# def gold_trip_metrics():
#     return (
#         dlt.read("silver_trips_data")
#         .groupBy("status")  # TODO: Update grouping to match your needs
#         .agg(
#             count("*").alias("trip_count"),
#             avg("duration").alias("avg_duration")  # TODO: Update fields
#         )
#     )