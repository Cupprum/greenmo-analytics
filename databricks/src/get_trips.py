# /// script
# dependencies = [
#   "requests",
# ]
# ///

import requests
import json
import os

API_BASE_URL = "https://platform.api.gourban.services/v1/hb98ga69/front/rentals"
API_KEY = os.environ["GREENMO_API_TOKEN"]
PAGE_SIZE = 50
OUTPUT_DIR = "../data/trips"

print("Fetching data from API...")

all_records = []
page = 0

while True:
    print(f"Fetching page {page}...")
    
    url = f"{API_BASE_URL}?page={page}&size={PAGE_SIZE}&state=ENDED"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()
        
    all_records.extend(data if isinstance(data, list) else [data])    
    with open(f"{OUTPUT_DIR}/trips_{page}.json", 'w') as f:
        json.dump(all_records, f, indent=2)

    if len(data) < PAGE_SIZE:
        break
    
    page += 1

print(f"Fetched: {len(all_records)} records")

