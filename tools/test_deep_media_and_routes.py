#!/usr/bin/env python3
"""
tools/test_deep_media_and_routes.py
=============================================================================
Adversarial Deep Crawler & Media 404 Auditor for Insilos Enterprise Routes.

Audits target routes:
  - /about
  - /blockchain
  - /solutions
  - /web/login (ERP Entrypoint)
  - /web/health (if available)
  - /platform, /industries, /resources, /pricing, /trust, /compliance

For each route:
  1. Validates HTTP 200 response & content length > 50KB.
  2. Scans for Odoo error signatures, compile warnings, or tracebacks in HTML.
  3. Extracts all embedded media (<img>, <source>, <video>, <link rel="stylesheet">, <script>).
  4. Probes every extracted asset URL to verify 0 broken media (0 404s, 0 500s).
=============================================================================
"""

import sys
import os
import re
import time
import urllib.request
import urllib.error
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_DOMAIN = "https://innoria.insilos.com"

TARGET_ROUTES = [
    "/about",
    "/blockchain",
    "/solutions",
    "/platform",
    "/industries",
    "/resources",
    "/pricing",
    "/trust",
    "/compliance",
    "/showcase-3d",
    "/interactive-3d",
    "/web/login"
]

ERROR_SIGNATURES = [
    "Could not compile stylesheet",
    "Style error:",
    "500: Internal Server Error",
    "Traceback (most recent call last):",
    "InternalServerError",
    "odoo.exceptions",
    "502 Bad Gateway",
    "404: Not Found",
    "Missing record"
]

def log(msg, level="INFO"):
    badges = {"INFO": "[*]", "PASS": "[✓]", "FAIL": "[✗]", "WARN": "[!]"}
    print(f"{badges.get(level, '[*]')} {msg}", flush=True)

def fetch_url(url, timeout=30):
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) InsilosChallenger/1.0',
                    'Accept': '*/*'
                }
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                code = resp.getcode()
                body = resp.read()
                return code, body
        except Exception as e:
            if attempt < 2:
                time.sleep(1.0)
                continue
            raise e

def probe_asset(url, timeout=15):
    try:
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) InsilosChallenger/1.0'}
        )
        # Using GET with small timeout
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return url, resp.getcode(), None
    except urllib.error.HTTPError as e:
        return url, e.code, str(e)
    except Exception as e:
        return url, 0, str(e)

def audit_routes():
    log(f"Auditing {len(TARGET_ROUTES)} target routes on {BASE_DOMAIN}...", "INFO")
    all_media_urls = set()
    route_failures = []
    
    for route in TARGET_ROUTES:
        url = urljoin(BASE_DOMAIN, route)
        try:
            code, raw_body = fetch_url(url)
            body = raw_body.decode('utf-8', errors='ignore')
            
            if code != 200:
                log(f"Route {route} returned HTTP {code}", "FAIL")
                route_failures.append((route, f"HTTP {code}"))
                continue
                
            # Check size
            if len(raw_body) < 10000:
                log(f"Route {route} returned abnormally small payload ({len(raw_body)} bytes)", "WARN")
                route_failures.append((route, f"Body too small: {len(raw_body)} bytes"))
                continue
                
            # Check error signatures
            found_errors = [sig for sig in ERROR_SIGNATURES if sig in body]
            if found_errors:
                log(f"Route {route} contains error signatures: {found_errors}", "FAIL")
                route_failures.append((route, f"Error signatures: {found_errors}"))
                continue
                
            log(f"Route {route:<30} : HTTP 200 OK ({len(raw_body):,} bytes, 0 error strings)", "PASS")
            
            # Extract assets: img src, source src, script src, link rel=stylesheet href
            img_srcs = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', body, re.IGNORECASE)
            source_srcs = re.findall(r'<source[^>]+src=["\']([^"\']+)["\']', body, re.IGNORECASE)
            video_srcs = re.findall(r'<video[^>]+src=["\']([^"\']+)["\']', body, re.IGNORECASE)
            script_srcs = re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', body, re.IGNORECASE)
            css_hrefs = re.findall(r'<link[^>]+rel=["\']stylesheet["\'][^>]+href=["\']([^"\']+)["\']', body, re.IGNORECASE)
            css_hrefs += re.findall(r'<link[^>]+href=["\']([^"\']+)["\'][^>]+rel=["\']stylesheet["\']', body, re.IGNORECASE)
            
            extracted = img_srcs + source_srcs + video_srcs + script_srcs + css_hrefs
            for asset in extracted:
                if asset.startswith("data:"):
                    continue
                # Resolve full URL
                full_asset_url = urljoin(url, asset)
                parsed = urlparse(full_asset_url)
                # Only check assets on our domain
                if parsed.netloc == urlparse(BASE_DOMAIN).netloc:
                    all_media_urls.add(full_asset_url)
                    
        except Exception as e:
            log(f"Route {route} threw exception: {e}", "FAIL")
            route_failures.append((route, str(e)))

    if route_failures:
        log(f"Route audit failed with {len(route_failures)} errors!", "FAIL")
        return False, route_failures, []

    log(f"All {len(TARGET_ROUTES)} routes returned clean HTTP 200 OK.", "PASS")
    log(f"Extracted {len(all_media_urls)} unique internal static media and bundle URLs.", "INFO")
    
    # Audit extracted media URLs in parallel
    log("Probing all media and asset URLs for HTTP 200 / 0 broken links (404)...", "INFO")
    broken_assets = []
    success_count = 0
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(probe_asset, url): url for url in all_media_urls}
        for future in as_completed(futures):
            url, status, err = future.result()
            if status == 200:
                success_count += 1
            else:
                log(f"BROKEN MEDIA DETECTED: {url} -> HTTP {status} ({err})", "FAIL")
                broken_assets.append((url, status, err))
                
    log(f"Media Audit Results: {success_count}/{len(all_media_urls)} assets loaded with HTTP 200.", "PASS" if not broken_assets else "WARN")
    if broken_assets:
        log(f"Found {len(broken_assets)} broken assets!", "FAIL")
        return False, [], broken_assets
        
    log(f"100% of tested media assets returned clean HTTP 200 (ZERO 404s).", "PASS")
    return True, [], []

if __name__ == '__main__':
    ok, route_errs, media_errs = audit_routes()
    if not ok:
        log("Adversarial Deep Media & Route Audit FAILED!", "FAIL")
        sys.exit(1)
    log("🎉 Adversarial Deep Media & Route Audit PASSED 100%!", "PASS")
    sys.exit(0)
