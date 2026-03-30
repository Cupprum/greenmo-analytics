import requests
import json
from datetime import datetime

api_endpoint = "https://api.example.com/data"
api_key = dbutils.secrets.get(scope="greenmo", key="api_key")
table = "workspace.greenmobility.bronze_trips_data"

# === FETCH API DATA ===
headers = {"Authorization": f"Bearer {api_key}"}
response = requests.get(api_endpoint, headers=headers)
data = response.json()

# Make sure it's a list
if not isinstance(data, list):
    data = [data]

# === SAVE TO BRONZE ===
records = [{"raw_data": json.dumps(d), "ingestion_time": datetime.now()} for d in data]
df = spark.createDataFrame(records)
df.write.mode("append").saveAsTable(table)

print(f"Saved {len(records)} records")