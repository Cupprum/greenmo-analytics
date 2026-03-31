#!/usr/bin/env python
# /// script
# dependencies = [
#   "requests",
# ]
# ///

import requests
import json
import os
from urllib.parse import urlencode

# API details
API_KEY = os.environ["GREENMO_API_TOKEN"]
PAGE_SIZE = 50

RENTALS_API_URL = "https://platform.api.gourban.services/v1/hb98ga69/front/rentals"
VOUCHERS_API_URL = "https://platform.api.gourban.services/v1/hb98ga69/front/vouchers"
INVOICES_API_URL = "https://platform.api.gourban.services/v1/hb98ga69/front/invoices"

BASE_DATA_DIR = "../data"

def fetch_and_save_paginated_data(base_url, output_dir, filename_prefix, query_params=None):
    """
    Fetches data from a paginated API and saves each page to a separate JSON file.
    Args:
        base_url (str): The base URL for the API endpoint.
        output_dir (str): The directory to save the JSON files into.
        filename_prefix (str): The prefix for the saved JSON files (e.g., 'rentals').
        query_params (dict, optional): Additional query parameters for the API request.
                                       Defaults to None.
    """
    if query_params is None:
        query_params = {}
        
    os.makedirs(output_dir, exist_ok=True)
    print(f"Fetching data from {base_url} into {output_dir}...")

    page = 0
    while True:
        print(f"Fetching page {page}...")
        
        current_page_params = query_params.copy()
        current_page_params['page'] = page
        current_page_params['size'] = PAGE_SIZE
        
        query_string = urlencode(current_page_params)
        url = f"{base_url}?{query_string}"
        
        headers = {"Authorization": f"Bearer {API_KEY}"}
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()

            filename = f"{filename_prefix}_{page}.json"
            filepath = os.path.join(output_dir, filename)
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"Saved {len(data)} records to {filepath}")

            if len(data) < PAGE_SIZE:
                print("Last page reached.")
                break
            
            page += 1
        except Exception as e:
            print(f"An unexpected error occurred while processing {url}: {e}")
            break

if __name__ == "__main__":
    print("Starting data fetching process...")

    # Fetch and save rentals
    fetch_and_save_paginated_data(
        base_url=RENTALS_API_URL,
        output_dir=os.path.join(BASE_DATA_DIR, "rentals"),
        filename_prefix="rentals",
        query_params={"state": "ENDED"}
    )

    # Fetch and save vouchers
    fetch_and_save_paginated_data(
        base_url=VOUCHERS_API_URL,
        output_dir=os.path.join(BASE_DATA_DIR, "vouchers"),
        filename_prefix="vouchers",
        query_params={"branchId": 100}
    )

    # Fetch and save invoices
    fetch_and_save_paginated_data(
        base_url=INVOICES_API_URL,
        output_dir=os.path.join(BASE_DATA_DIR, "invoices"),
        filename_prefix="invoices",
        query_params={"branchId": 100}
    )

    print("Data fetching process completed.")
