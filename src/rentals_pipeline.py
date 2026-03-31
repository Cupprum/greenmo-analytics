# Databricks notebook source

from pyspark import pipelines as dp
from pyspark.sql.functions import col, current_timestamp, count, avg, sum, max, to_timestamp, round as spark_round, to_date, year, month


@dp.materialized_view(
    name="rentals_bronze",
    comment="Raw rental data from JSON files",
    table_properties={
        "delta.columnMapping.mode": "name"
    }
)
def rentals_bronze():
    return (
        spark.read
        .format("json")
        .option("multiLine", "true")
        .load("/Volumes/workspace/default/greenmo_raw_data/rentals/")
        .withColumn("ingestion_time", current_timestamp())
    )

@dp.materialized_view(
    name="rentals_silver",
    comment="Cleaned and transformed rental data"
)
@dp.expect_or_drop("valid_rental_id", "rental_id IS NOT NULL")
@dp.expect_or_drop("valid_rental_times", "rental_drive_start_time IS NOT NULL AND rental_end_time IS NOT NULL")
def rentals_silver():
    return (
        spark.read.table("rentals_bronze")
        .select(
            col("id").alias("rental_id"),
            to_timestamp(col("driveStartTime")).alias("rental_drive_start_time"),
            to_timestamp(col("endTime")).alias("rental_end_time"),
            col("distance").alias("rental_distance_km")
        )
        .dropDuplicates(["rental_id"])
        .withColumn("rental_drive_duration_minutes", 
            spark_round((col("rental_end_time").cast("long") - col("rental_drive_start_time").cast("long")) / 60, 2))
    )

@dp.materialized_view(
    name="rentals_gold_daily",
    comment="Daily rental aggregations"
)
def rentals_gold_daily():
    return (
        spark.read.table("rentals_silver")
        .withColumn("rental_date", to_date(col("rental_drive_start_time")))
        .groupBy("rental_date")
        .agg(
            count("rental_id").alias("total_rentals"),
            spark_round(avg("rental_distance_km"), 2).alias("avg_distance_km"),
            spark_round(sum("rental_distance_km"), 2).alias("total_distance_km"),
            spark_round(avg("rental_drive_duration_minutes"), 2).alias("avg_duration_min"),
            spark_round(max("rental_drive_duration_minutes"), 2).alias("max_duration_min")
        )
        .orderBy("rental_date")
    )

@dp.materialized_view(
    name="rentals_gold_monthly",
    comment="Monthly rental aggregations"
)
def rentals_gold_monthly():
    return (
        spark.read.table("rentals_silver")
        .withColumn("rental_year", year(col("rental_drive_start_time")))
        .withColumn("rental_month", month(col("rental_drive_start_time")))
        .groupBy("rental_year", "rental_month")
        .agg(
            count("rental_id").alias("total_rentals"),
            spark_round(avg("rental_distance_km"), 2).alias("avg_distance_km"),
            spark_round(sum("rental_distance_km"), 2).alias("total_distance_km"),
            spark_round(avg("rental_drive_duration_minutes"), 2).alias("avg_duration_min"),
            spark_round(max("rental_drive_duration_minutes"), 2).alias("max_duration_min")
        )
        .orderBy("rental_year", "rental_month")
    )

@dp.materialized_view(
    name="rentals_gold_summary",
    comment="Overall rental summary"
)
def rentals_gold_summary():
    return (
        spark.read.table("rentals_silver")
        .agg(
            count("rental_id").alias("total_rentals"),
            spark_round(avg("rental_distance_km"), 2).alias("avg_distance_km"),
            spark_round(sum("rental_distance_km"), 2).alias("total_distance_km"),
            spark_round(avg("rental_drive_duration_minutes"), 2).alias("avg_duration_min")
        )
    )
