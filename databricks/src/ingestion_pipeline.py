# Databricks notebook source

from pyspark import pipelines as dp
from pyspark.sql.functions import col, current_timestamp, count, avg, sum, min, max, to_timestamp, round as spark_round

@dp.materialized_view(
    name="greenmo_trips_bronze",
    comment="Raw trip data from JSON files",
    table_properties={
        "delta.columnMapping.mode": "name"
    }
)
def greenmo_trips_bronze():
    return (
        spark.read
        .format("json")
        .option("multiLine", "true")
        .load("/Volumes/workspace/default/greenmo_raw_data/trips/")
        .withColumn("ingestion_time", current_timestamp())
    )

@dp.materialized_view(
    name="greenmo_trips_silver",
    comment="Cleaned trip data"
)
@dp.expect_or_drop("valid_id", "trip_id IS NOT NULL")
@dp.expect_or_drop("valid_times", "drive_start_time IS NOT NULL AND end_time IS NOT NULL")
def greenmo_trips_silver():
    return (
        spark.read.table("greenmo_trips_bronze")
        .select(
            col("id").alias("trip_id"),
            col("branchId").alias("branch_id"),
            col("invoiceId").alias("invoice_id"),
            col("state"),
            col("type").alias("trip_type"),
            to_timestamp(col("startTime")).alias("start_time"),
            to_timestamp(col("driveStartTime")).alias("drive_start_time"),
            to_timestamp(col("endTime")).alias("end_time"),
            col("distance"),
            col("currency"),
            col("startAddress").alias("start_address"),
            col("endAddress").alias("end_address"),
            col("startKilometers").alias("start_km"),
            col("endKilometers").alias("end_km"),
            col("vehicle.licensePlate").alias("vehicle_plate"),
            col("vehicle.name").alias("vehicle_name"),
            col("rideMode").alias("ride_mode"),
            col("ingestion_time")
        )
        .dropDuplicates(["trip_id"])
        .withColumn("drive_duration_minutes", 
            spark_round((col("end_time").cast("long") - col("drive_start_time").cast("long")) / 60, 2))
    )

@dp.materialized_view(
    name="greenmo_trips_gold_daily",
    comment="Daily trip aggregations"
)
def greenmo_trips_gold_daily():
    from pyspark.sql.functions import to_date
    
    return (
        spark.read.table("greenmo_trips_silver")
        .withColumn("trip_date", to_date(col("drive_start_time")))
        .groupBy("trip_date", "branch_id")
        .agg(
            count("trip_id").alias("total_trips"),
            spark_round(avg("distance"), 2).alias("avg_distance_km"),
            spark_round(sum("distance"), 2).alias("total_distance_km"),
            spark_round(avg("drive_duration_minutes"), 2).alias("avg_duration_min"),
            spark_round(max("drive_duration_minutes"), 2).alias("max_duration_min")
        )
        .orderBy("trip_date", "branch_id")
    )

@dp.materialized_view(
    name="greenmo_trips_gold_summary",
    comment="Overall trip summary"
)
def greenmo_trips_gold_summary():
    return (
        spark.read.table("greenmo_trips_silver")
        .groupBy("branch_id")
        .agg(
            count("trip_id").alias("total_trips"),
            spark_round(avg("distance"), 2).alias("avg_distance_km"),
            spark_round(sum("distance"), 2).alias("total_distance_km"),
            spark_round(avg("drive_duration_minutes"), 2).alias("avg_duration_min"),
            min("drive_start_time").alias("first_trip"),
            max("end_time").alias("last_trip")
        )
    )
