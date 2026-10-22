#!/usr/bin/env python3
"""
High-Performance Parallel MongoDB Catalog Scanner & Reconciliation Inspector
Scans all 456 collections concurrently across multiple worker threads to identify
all business catalogs, document counts, schemas, and Odoo model mappings.
"""

import sys
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pymongo import MongoClient

MONGO_URI = "mongodb://root:3396a9cd47ce06570eb64b39b159c96814d7c400@100.116.104.112:30117/digiforce360-production?authSource=admin"
MONGO_DB = "digiforce360-production"

def scan_collection(c_name):
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000, connectTimeoutMS=5000)
        db = client[MONGO_DB]
        coll = db[c_name]
        cnt = coll.count_documents({})
        sample_keys = []
        if cnt > 0:
            doc = coll.find_one()
            if doc:
                sample_keys = [k for k in doc.keys() if not k.startswith("_")][:10]
        client.close()
        return {"name": c_name, "count": cnt, "sample_keys": sample_keys}
    except Exception as e:
        return {"name": c_name, "count": -1, "error": str(e), "sample_keys": []}

def main():
    print(f"[*] Connecting to MongoDB {MONGO_DB}...")
    root_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=10000)
    db = root_client[MONGO_DB]
    collections = sorted(db.list_collection_names())
    root_client.close()
    print(f"[*] Found {len(collections)} total collections. Starting parallel scan with 32 workers...")

    start_time = time.time()
    results = []
    with ThreadPoolExecutor(max_workers=32) as executor:
        future_to_col = {executor.submit(scan_collection, c): c for c in collections}
        for future in as_completed(future_to_col):
            results.append(future.result())

    elapsed = time.time() - start_time
    print(f"[✓] Parallel scan completed in {elapsed:.2f}s!")

    non_empty = [r for r in results if r["count"] > 0]
    empty = [r for r in results if r["count"] == 0]
    errors = [r for r in results if r["count"] < 0]

    non_empty.sort(key=lambda x: x["count"], reverse=True)

    output = {
        "scan_time": elapsed,
        "total_collections": len(collections),
        "non_empty_count": len(non_empty),
        "empty_count": len(empty),
        "error_count": len(errors),
        "non_empty_catalogs": non_empty
    }

    out_file = "/home/zen/O20/reports/mongodb_catalogs_inventory.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"[✓] Saved catalog inventory to {out_file}")

    print("\n" + "="*80)
    print(f"{'CATALOG / COLLECTION':<35} | {'DOCS':<8} | {'SAMPLE FIELDS'}")
    print("="*80)
    for item in non_empty:
        fields = ", ".join(item["sample_keys"][:6])
        print(f"{item['name']:<35} | {item['count']:<8} | {fields}")
    print("="*80)

if __name__ == "__main__":
    main()
