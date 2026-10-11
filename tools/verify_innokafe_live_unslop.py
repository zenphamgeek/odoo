#!/usr/bin/env python3
"""
tools/verify_innokafe_live_unslop.py
Comprehensive live HTTP verification of InnoKafe routes on port 28071:
- Verifies HTTP 200
- Verifies 0 decorative emojis
- Verifies 0 border-opacity classes
- Verifies 0 em-dashes (—)
- Verifies 0 AI slop vocabulary
"""

import sys
import re
import urllib.request
import urllib.error

BASE_URL = "http://127.0.0.1:28071"

ROUTES = [
    "/",
    "/story",
    "/products",
    "/taste-profiler",
    "/solutions-b2b",
    "/contactus"
]

# Common emoji unicode ranges
EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport & map symbols
    "\U0001F1E0-\U0001F1FF"  # flags (iOS)
    "\U00002702-\U000027B0"  # dingbats
    "\U000024C2-\U0001F251"
    "\U0001F900-\U0001F9FF"  # supplemental symbols
    "\U0001FA70-\U0001FAFF"
    "\U00002600-\U000026FF"  # misc symbols
    "]+",
    flags=re.UNICODE
)

SLOP_PATTERNS = [
    ("border-opacity", "Harsh mechanical border-opacity class"),
    ("—", "Em-dash (—)"),
    ("Khúc giao hòa", "AI cliché: Khúc giao hòa"),
    ("Bản giao hưởng", "AI cliché: Bản giao hưởng"),
    ("★★★★★", "Unicode raw star glyphs"),
]

def audit_route(route):
    url = f"{BASE_URL}{route}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 InnoKafe-PDCA-Auditor"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            status = resp.status
            html = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"[✗] {route} FAILED to load: {e}")
        return False

    if status != 200:
        print(f"[✗] {route} returned HTTP {status}")
        return False

    errors = []

    # Check emojis (exclude Odoo backend debug widgets if any, but in production frontend there shouldn't be any)
    emojis = EMOJI_PATTERN.findall(html)
    if emojis:
        # Check if they are in frontend content
        errors.append(f"Found {len(emojis)} emojis: {emojis[:5]}")

    for pat, desc in SLOP_PATTERNS:
        matches = html.count(pat)
        if matches > 0:
            errors.append(f"Found {matches} instances of {desc} ('{pat}')")

    if errors:
        print(f"[✗] {route} (HTTP {status}) - {len(errors)} slop violations found:")
        for err in errors:
            print(f"      - {err}")
        return False
    else:
        print(f"[✓] {route} (HTTP {status}) - 0 Emojis, 0 Border-opacity, 0 Em-dashes, 0 AI Clichés (CLEAN)")
        return True

def main():
    print(f"=== INNOKAFE LIVE UNSLOP AUDIT: {BASE_URL} ===")
    all_clean = True
    for r in ROUTES:
        clean = audit_route(r)
        if not clean:
            all_clean = False

    print("\n" + "="*50)
    if all_clean:
        print("[✓✓✓] ALL 6 ROUTES ARE 100% CLEAN OF AI SLOP (ZERO DEFECTS)!")
        return 0
    else:
        print("[!] Violations detected in live routes.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
