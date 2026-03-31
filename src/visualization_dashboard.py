# Databricks notebook source
# MAGIC %md
# MAGIC # GreenMobility Usage Dashboard

# COMMAND ----------

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from databricks.sdk.runtime import *

# Helper to load table as pandas
def load_table(name):
    return spark.read.table(f"greenmobility.{name}").toPandas()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Global Summaries

# COMMAND ----------

# Load summaries
rentals_summary = load_table("rentals_gold_summary")
invoices_summary = load_table("invoices_gold_summary")

total_km = rentals_summary["total_distance_km"].iloc[0]
total_min = rentals_summary["total_drive_duration_minutes"].iloc[0]
total_spent = invoices_summary["total_spent_gross"].iloc[0]

# Display as big text using HTML
displayHTML(f"""
<div style="display: flex; justify-content: space-around; padding: 20px; background-color: #f8f9fa; border-radius: 10px; border: 1px solid #dee2e6;">
    <div style="text-align: center;">
        <h2 style="color: #6c757d; font-size: 1.2em;">Total Distance</h2>
        <p style="font-size: 3em; font-weight: bold; color: #28a745; margin: 0;">{total_km:,.1f} <span style="font-size: 0.4em;">km</span></p>
    </div>
    <div style="text-align: center;">
        <h2 style="color: #6c757d; font-size: 1.2em;">Total Duration</h2>
        <p style="font-size: 3em; font-weight: bold; color: #007bff; margin: 0;">{total_min:,.0f} <span style="font-size: 0.4em;">min</span></p>
    </div>
    <div style="text-align: center;">
        <h2 style="color: #6c757d; font-size: 1.2em;">Total Spent</h2>
        <p style="font-size: 3em; font-weight: bold; color: #dc3545; margin: 0;">{total_spent:,.2f} <span style="font-size: 0.4em;">DKK</span></p>
    </div>
</div>
""")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Monthly Driving Activity (Distance & Duration)

# COMMAND ----------

rentals_monthly = load_table("rentals_gold_monthly")
rentals_monthly["period"] = rentals_monthly["rental_year"].astype(str) + "-" + rentals_monthly["rental_month"].astype(str).str.zfill(2)
rentals_monthly = rentals_monthly.sort_values("period")

# Plot Distance
fig_dist = px.bar(rentals_monthly, x="period", y="total_distance_km", 
                  title="Total Kilometers Driven per Month",
                  labels={"total_distance_km": "Distance (km)", "period": "Month"},
                  color_discrete_sequence=["#28a745"])
fig_dist.update_layout(xaxis_type='category', dragmode='pan')
fig_dist.show()

# Plot Duration
fig_dur = px.bar(rentals_monthly, x="period", y="avg_duration_min", 
                 title="Average Duration (min) per Month",
                 labels={"avg_duration_min": "Avg Duration (min)", "period": "Month"},
                 color_discrete_sequence=["#007bff"])
fig_dur.update_layout(xaxis_type='category', dragmode='pan')
fig_dur.show()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Monthly Financials (Invoices & Vouchers)

# COMMAND ----------

invoices_monthly = load_table("invoices_gold_monthly")
invoices_monthly["period"] = invoices_monthly["year"].astype(str) + "-" + invoices_monthly["month"].astype(str).str.zfill(2)
invoices_monthly = invoices_monthly.sort_values("period")

fig_inv = px.line(invoices_monthly, x="period", y="total_spent_gross", 
                  title="Total Spending per Month (Gross)",
                  labels={"total_spent_gross": "Amount (DKK)", "period": "Month"},
                  markers=True, color_discrete_sequence=["#dc3545"])
fig_inv.update_layout(xaxis_type='category')
fig_inv.show()

# Vouchers
vouchers_monthly = load_table("vouchers_gold_charging_monthly")
if not vouchers_monthly.empty:
    vouchers_monthly["period"] = vouchers_monthly["voucher_year"].astype(str) + "-" + vouchers_monthly["voucher_month"].astype(str).str.zfill(2)
    vouchers_monthly = vouchers_monthly.sort_values("period")

    fig_vouch = px.bar(vouchers_monthly, x="period", y="total_value_gross", 
                       title="Charging Vouchers Value per Month",
                       labels={"total_value_gross": "Voucher Value (DKK)", "period": "Month"},
                       color_discrete_sequence=["#ffc107"])
    fig_vouch.update_layout(xaxis_type='category')
    fig_vouch.show()
else:
    print("No voucher data available for charting.")
