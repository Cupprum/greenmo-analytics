# Databricks notebook source

# MAGIC %md
# MAGIC # GreenMobility Analytics Dashboard

# COMMAND ----------
# MAGIC %md
# MAGIC ## 📊 Key Metrics Summary

# COMMAND ----------
# MAGIC %sql
# MAGIC SELECT 
# MAGIC   total_rentals,
# MAGIC   ROUND(total_distance_km, 0) as total_km,
# MAGIC   avg_distance_km,
# MAGIC   avg_duration_min
# MAGIC FROM workspace.greenmobility.rentals_gold_summary

# COMMAND ----------
# MAGIC %sql
# MAGIC SELECT 
# MAGIC   total_charging_vouchers,
# MAGIC   total_value_gross,
# MAGIC   total_value_net
# MAGIC FROM workspace.greenmobility.vouchers_gold_charging_summary

# COMMAND ----------
# MAGIC %md
# MAGIC ## 📈 Rentals Trends

# COMMAND ----------
# MAGIC %sql
# MAGIC SELECT 
# MAGIC   CONCAT(rental_year, '-', LPAD(rental_month, 2, '0')) as month,
# MAGIC   total_rentals,
# MAGIC   avg_distance_km,
# MAGIC   total_distance_km
# MAGIC FROM workspace.greenmobility.rentals_gold_monthly
# MAGIC ORDER BY rental_year, rental_month

# COMMAND ----------
# MAGIC %md
# MAGIC ## 💰 Invoice Spending Analysis

# COMMAND ----------
# MAGIC %sql
# MAGIC SELECT 
# MAGIC   CONCAT(year, '-', LPAD(month, 2, '0')) as month,
# MAGIC   total_spent_gross,
# MAGIC   total_spent_net,
# MAGIC   invoice_count,
# MAGIC   ROUND(total_spent_gross / invoice_count, 2) as avg_per_invoice
# MAGIC FROM workspace.greenmobility.invoices_gold_monthly
# MAGIC ORDER BY year, month

# COMMAND ----------
# MAGIC %sql
# MAGIC SELECT 
# MAGIC   year,
# MAGIC   total_spent_gross,
# MAGIC   invoice_count
# MAGIC FROM workspace.greenmobility.invoices_gold_yearly
# MAGIC ORDER BY year

# COMMAND ----------
# MAGIC %md
# MAGIC ## 🔋 Charging Vouchers Trends

# COMMAND ----------
# MAGIC %sql
# MAGIC SELECT 
# MAGIC   CONCAT(voucher_year, '-', LPAD(voucher_month, 2, '0')) as month,
# MAGIC   total_charging_vouchers,
# MAGIC   total_value_gross,
# MAGIC   total_value_net
# MAGIC FROM workspace.greenmobility.vouchers_gold_charging_monthly
# MAGIC ORDER BY voucher_year, voucher_month

# COMMAND ----------
# MAGIC %md
# MAGIC ## 📅 Recent Daily Activity (Last 30 Days)

# COMMAND ----------
# MAGIC %sql
# MAGIC SELECT 
# MAGIC   rental_date,
# MAGIC   total_rentals,
# MAGIC   avg_distance_km,
# MAGIC   total_distance_km,
# MAGIC   avg_duration_min
# MAGIC FROM workspace.greenmobility.rentals_gold_daily
# MAGIC ORDER BY rental_date DESC
# MAGIC LIMIT 30