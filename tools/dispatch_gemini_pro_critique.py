#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dispatch adversarial critique job to Gemini 3.1 Pro High on Fleet."""
import json
import time
import requests
from pathlib import Path

PROMPT_FILE = Path("/home/zen/O20/tools/prompt_opus_pdca_critique.txt")
prompt_text = PROMPT_FILE.read_text(encoding="utf-8")

payload = {
    "prompt": prompt_text,
    "node_name": "team-3",
    "model": "gemini-3.1-pro-high",
    "timeout": 300
}

print("[*] Submitting Job to AGY Fleet (node: team-3, model: gemini-3.1-pro-high)...")
resp = requests.post("http://localhost:7777/api/fleet/run", json=payload, timeout=30)
resp.raise_for_status()
job_data = resp.json()
job_id = job_data.get("job_id")
print(f"[✓] Job dispatched successfully: {job_id}")

start = time.time()
while time.time() - start < 300:
    time.sleep(5)
    st = requests.get(f"http://localhost:7777/api/fleet/jobs/{job_id}", timeout=10).json()
    status = st.get("status")
    print(f"  • Job status: {status} ({int(time.time() - start)}s elapsed)")
    if status in ("completed", "failed", "cancelled"):
        if status == "completed":
            print(f"[✓] Job completed in {int(time.time() - start)}s!")
            output = st.get("stdout") or st.get("output") or ""
            out_file = Path("/home/zen/O20/docs/OPUS_ADVERSARIAL_CRITIQUE_PDCA_REFINEMENT.md")
            out_file.write_text(output, encoding="utf-8")
            print(f"[✓] Saved critique report to: {out_file}")
            print(f"Report length: {len(output)} characters")
        else:
            print(f"[!] Job ended with status: {status}")
            print(st.get("stderr") or st.get("error"))
        break
