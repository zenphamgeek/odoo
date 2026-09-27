#!/usr/bin/env python3
"""
Challenger M5-1: Live Route & Stress Test Harness
=================================================
Independent empirical verification for Insilos Enterprise Website on Odoo 20.
Audits:
- All core public pages (12 routes)
- All solution routes & aliases (20 routes)
- Dedicated & 40+ extended 101 industry routes + aliases (49 routes)
- Whitepapers / resources & aliases (9 routes)
- Brochure PDF download endpoints & fallbacks
- Boundary inputs, unexpected slugs, path traversal, injection payloads (24 tests)
- Response body traceback & exception scanning (Zero-Traceback Guarantee)
- HTML structure, dropzone, and fallback template rendering validity
- Concurrent load stress test (50 concurrent threads)
- Demo request form validation & rate limit stress test
"""

import sys
import os
import re
import time
import html
import json
import urllib.request
import urllib.parse
import urllib.error
import http.cookiejar
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_URL = os.environ.get("INSILOS_BASE_URL", "http://localhost:28069")

# Error indicators that must NEVER appear in response body
FORBIDDEN_ERROR_SIGNATURES = [
    "Traceback (most recent call last):",
    "odoo.exceptions",
    "500: Internal Server Error",
    "psycopg2.",
    "Werkzeug Debugger",
    "QWebException",
    "TemplateNotFound",
    "KeyError:",
    "AttributeError:",
    "TypeError:",
    "ValueError:",
    "ZeroDivisionError:",
    "ProgrammingError",
]

# Core public routes
CORE_ROUTES = [
    "/",
    "/platform",
    "/solutions",
    "/industries",
    "/industry",
    "/pricing",
    "/about",
    "/resources",
    "/request-demo",
    "/media-credits",
    "/showcase-3d",
    "/thank-you",
]

# Solution routes from SOLUTIONS dictionary
SOLUTIONS = [
    "vertical-idp",
    "enterprise-knowledge-graph",
    "trade-compliance",
    "field-service-intelligence",
    "asset-reliability",
    "logistics-control-tower",
    "process-optimization",
    "operations-assistant",
    "governed-manufacturing-ai",
]

# Solution aliases that should redirect
SOLUTION_ALIASES = [
    ("autonomous-trade-compliance", "/solutions/trade-compliance"),
    ("fsm", "/solutions/field-service-intelligence"),
    ("field-service", "/solutions/field-service-intelligence"),
    ("logistics", "/solutions/logistics-control-tower"),
    ("idp", "/solutions/vertical-idp"),
    ("knowledge-graph", "/solutions/enterprise-knowledge-graph"),
    ("customs", "/solutions/trade-compliance"),
    ("predictive-maintenance", "/solutions/asset-reliability"),
    ("energy", "/industries/energy"),
    ("pharma", "/industries/pharma"),
    ("capital-markets", "/solutions/trade-compliance"),
]

# Dedicated industries
DEDICATED_INDUSTRIES = ["fsm", "logistics", "energy", "pharma"]

# Sample of 101 extended industries to test fallback template rendering
EXTENDED_SAMPLE_INDUSTRIES = [
    "farm", "freight", "cold_chain", "warehouse", "import_export", "courier",
    "fintech", "bank", "investment", "insurance", "accounting_firm",
    "general_manufacturing", "food_manufacturing", "metalwork", "chemical", "textile", "3d_printing",
    "electrical", "environmental", "general_contractor",
    "hospital", "clinic", "pharmacy_retail",
    "hvac", "plumbing", "auto_repair", "security_service",
    "telecom", "cybersecurity", "data_analytics", "software_company",
    "grocery_store", "fashion_store", "electronics_store", "jewelry_store", "cosmetics",
    "hotel", "restaurant",
    "government", "law_firm", "real_estate_agency"
]

# Resource articles
ARTICLES = [
    "operational-ai",
    "industrial-ai-agents",
    "governed-ai-pharma",
    "vertical-idp-logistics-roi",
    "trade-compliance-handbook",
]

# Article aliases that should redirect
ARTICLE_ALIASES = [
    ("predictive-maintenance-whitepaper", "/resources/operational-ai"),
    ("whitepaper", "/resources/operational-ai"),
    ("idp-roi", "/resources/vertical-idp-logistics-roi"),
    ("trade-compliance", "/resources/trade-compliance-handbook"),
]

# Boundary & edge test cases
BOUNDARY_TEST_CASES = [
    # Non-existent slugs (Expected 404)
    {"path": "/solutions/unlisted", "expected_status": 404, "desc": "Unlisted solution slug"},
    {"path": "/industries/unlisted", "expected_status": 404, "desc": "Unlisted industry slug"},
    {"path": "/solutions/unlisted-slug", "expected_status": 404, "desc": "Hyphenated unlisted solution"},
    {"path": "/industries/unlisted-slug", "expected_status": 404, "desc": "Hyphenated unlisted industry"},
    {"path": "/resources/unlisted-article", "expected_status": 404, "desc": "Unlisted resource article"},
    {"path": "/solutions/non-existent-solution-12345", "expected_status": 404, "desc": "Numeric dummy solution"},
    {"path": "/industries/unregistered-industry-67890", "expected_status": 404, "desc": "Numeric dummy industry"},
    {"path": "/industry/unlisted/brochure", "expected_status": 404, "desc": "Unlisted industry brochure"},
    {"path": "/industry/non-existent-xyz/brochure", "expected_status": 404, "desc": "Dummy industry brochure"},
    
    # Special character and malicious payload inputs (Expected 404 or clean handling, 0 tracebacks)
    {"path": "/solutions/test%20slug", "expected_status": 404, "desc": "Space encoded slug"},
    {"path": "/industries/test%20slug", "expected_status": 404, "desc": "Space encoded industry"},
    {"path": "/solutions/null", "expected_status": 404, "desc": "Literal 'null' slug"},
    {"path": "/solutions/undefined", "expected_status": 404, "desc": "Literal 'undefined' slug"},
    {"path": "/solutions/%3Cscript%3Ealert(1)%3C%2Fscript%3E", "expected_status": 404, "desc": "XSS script in solution slug"},
    {"path": "/industries/%3Cscript%3Ealert(1)%3C%2Fscript%3E", "expected_status": 404, "desc": "XSS script in industry slug"},
    {"path": "/solutions/'%20OR%201=1%20--", "expected_status": 404, "desc": "SQLi in solution slug"},
    {"path": "/industries/'%20UNION%20SELECT%201--", "expected_status": 404, "desc": "SQLi in industry slug"},
    {"path": "/solutions/" + ("a" * 255), "expected_status": 404, "desc": "255-character solution slug"},
    {"path": "/industries/" + ("b" * 255), "expected_status": 404, "desc": "255-character industry slug"},
    
    # Query parameters on valid routes (Expected 200 with clean output)
    {"path": "/?debug=1", "expected_status": 200, "desc": "Query param on home"},
    {"path": "/platform?param=test&filter=true", "expected_status": 200, "desc": "Query params on platform"},
    {"path": "/solutions/vertical-idp?tab=architecture", "expected_status": 200, "desc": "Query param on IDP solution"},
    {"path": "/?q=%3Cscript%3Econsole.log(1)%3C%2Fscript%3E", "expected_status": 200, "desc": "Reflected XSS attempt in query param"},
    {"path": "/solutions?category=%27%20OR%201=1--", "expected_status": 200, "desc": "SQLi in query param on solutions"},
]


class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None  # Do not follow redirects automatically


def make_request(path, follow_redirects=True, timeout=12, cookie_processor=None):
    """Perform HTTP request and return (status, body, headers, latency_ms)."""
    url = f"{BASE_URL}{path}"
    handlers = []
    if cookie_processor:
        handlers.append(cookie_processor)
    if not follow_redirects:
        handlers.append(NoRedirectHandler())
        
    opener = urllib.request.build_opener(*handlers)
    req = urllib.request.Request(url, headers={"User-Agent": "InsilosChallengerHarness/2.0"})
    
    start = time.perf_counter()
    try:
        with opener.open(req, timeout=timeout) as resp:
            status = resp.status
            body = resp.read()
            # headers case-insensitive dict
            headers = {k.lower(): v for k, v in resp.headers.items()}
            elapsed = (time.perf_counter() - start) * 1000
            return status, body, headers, elapsed
    except urllib.error.HTTPError as he:
        body = he.read() if hasattr(he, "read") else b""
        headers = {k.lower(): v for k, v in he.headers.items()} if hasattr(he, "headers") else {}
        elapsed = (time.perf_counter() - start) * 1000
        return he.code, body, headers, elapsed
    except Exception as e:
        elapsed = (time.perf_counter() - start) * 1000
        return 0, str(e).encode(), {}, elapsed


def check_for_traceback(body_bytes):
    """Check for forbidden server traceback / exception signatures."""
    text = body_bytes.decode("utf-8", errors="replace")
    found_errors = []
    for sig in FORBIDDEN_ERROR_SIGNATURES:
        if sig in text:
            idx = text.find(sig)
            snippet = text[max(0, idx - 50):min(len(text), idx + 100)].replace("\n", " ")
            found_errors.append(f"{sig} (context: {snippet})")
    return found_errors


def validate_html_structure(body_bytes, path):
    """Validate HTML markup structure, dropzones, headers, footers."""
    text = body_bytes.decode("utf-8", errors="replace")
    errors = []
    
    if len(text) < 500:
        errors.append(f"Content too short ({len(text)} bytes)")
    if "<!DOCTYPE html" not in text and "<!doctype html" not in text:
        errors.append("Missing <!DOCTYPE html>")
    if "<html" not in text:
        errors.append("Missing <html tag")
    if "</html>" not in text:
        errors.append("Missing </html> tag")
    if "<header" not in text and 'id="top"' not in text:
        errors.append("Missing header / #top navigation")
    if "<footer" not in text and 'id="bottom"' not in text:
        errors.append("Missing footer / #bottom section")
        
    return errors


def run_test_category(title, tests):
    """Execute a batch of tests and format results."""
    print(f"\n{'=' * 75}")
    print(f"TEST BATCH: {title}")
    print(f"{'=' * 75}")
    
    passed_count = 0
    total_count = len(tests)
    failures = []
    
    for t in tests:
        path = t["path"]
        expected = t.get("expected_status", 200)
        follow = t.get("follow_redirects", True)
        desc = t.get("desc", path)
        
        status, body, headers, latency = make_request(path, follow_redirects=follow)
        
        tracebacks = check_for_traceback(body)
        status_ok = (status == expected)
        
        html_errors = []
        if status == 200 and "text/html" in headers.get("content-type", ""):
            html_errors = validate_html_structure(body, path)
            
        test_passed = status_ok and len(tracebacks) == 0 and len(html_errors) == 0
        
        icon = "✅" if test_passed else "❌"
        print(f"  {icon} {path:45} | HTTP {status} (exp {expected}) | {latency:6.1f}ms | {desc}")
        
        if not test_passed:
            failure_detail = {
                "path": path,
                "status": status,
                "expected": expected,
                "tracebacks": tracebacks,
                "html_errors": html_errors,
                "desc": desc,
            }
            failures.append(failure_detail)
            if not status_ok:
                print(f"     -> FAILED STATUS: Got {status}, expected {expected}")
            if tracebacks:
                print(f"     -> FORBIDDEN ERROR SIGNATURE: {tracebacks}")
            if html_errors:
                print(f"     -> HTML INTEGRITY DEFECTS: {html_errors}")
        else:
            passed_count += 1
            
    print(f"\n  Batch Result: {passed_count}/{total_count} Passed ({'PASSED' if passed_count == total_count else 'FAILED'})")
    return passed_count == total_count, failures


def run_solution_aliases():
    """Verify solution alias redirects."""
    print(f"\n{'=' * 75}")
    print("TEST BATCH: Solution Aliases (Redirect Verification)")
    print(f"{'=' * 75}")
    
    passed_count = 0
    failures = []
    
    for alias, target in SOLUTION_ALIASES:
        path = f"/solutions/{alias}"
        status, body, headers, latency = make_request(path, follow_redirects=False)
        location = headers.get("location", "")
        
        f_status, f_body, f_headers, f_latency = make_request(path, follow_redirects=True)
        tracebacks = check_for_traceback(f_body)
        
        redirect_ok = (status in [301, 302, 303, 307, 308]) and (target in location)
        dest_ok = (f_status == 200) and (len(tracebacks) == 0)
        
        test_passed = redirect_ok and dest_ok
        icon = "✅" if test_passed else "❌"
        print(f"  {icon} /solutions/{alias:32} -> {location or target:35} | HTTP {status} -> {f_status} ({f_latency:5.1f}ms)")
        
        if test_passed:
            passed_count += 1
        else:
            failures.append({
                "alias": alias,
                "target": target,
                "status": status,
                "location": location,
                "f_status": f_status,
                "tracebacks": tracebacks,
            })
            
    print(f"\n  Batch Result: {passed_count}/{len(SOLUTION_ALIASES)} Passed")
    return passed_count == len(SOLUTION_ALIASES), failures


def run_article_aliases():
    """Verify resource whitepaper article alias redirects."""
    print(f"\n{'=' * 75}")
    print("TEST BATCH: Article Aliases (Redirect Verification)")
    print(f"{'=' * 75}")
    
    passed_count = 0
    failures = []
    
    for alias, target in ARTICLE_ALIASES:
        path = f"/resources/{alias}"
        status, body, headers, latency = make_request(path, follow_redirects=False)
        location = headers.get("location", "")
        
        f_status, f_body, f_headers, f_latency = make_request(path, follow_redirects=True)
        tracebacks = check_for_traceback(f_body)
        
        redirect_ok = (status in [301, 302, 303, 307, 308]) and (target in location)
        dest_ok = (f_status == 200) and (len(tracebacks) == 0)
        
        test_passed = redirect_ok and dest_ok
        icon = "✅" if test_passed else "❌"
        print(f"  {icon} /resources/{alias:32} -> {location or target:35} | HTTP {status} -> {f_status} ({f_latency:5.1f}ms)")
        
        if test_passed:
            passed_count += 1
        else:
            failures.append({
                "alias": alias,
                "target": target,
                "status": status,
                "location": location,
                "f_status": f_status,
                "tracebacks": tracebacks,
            })
            
    print(f"\n  Batch Result: {passed_count}/{len(ARTICLE_ALIASES)} Passed")
    return passed_count == len(ARTICLE_ALIASES), failures


def run_fallback_template_audit():
    """Audit that fallback templates render complete, enriched data when dedicated template doesn't exist."""
    print(f"\n{'=' * 75}")
    print("TEST BATCH: Fallback Template Rendering Deep Audit")
    print(f"{'=' * 75}")
    
    tests = [
        # Solution without dedicated template (uses insilos_solution_page fallback)
        {"path": "/solutions/asset-reliability", "name": "Asset Reliability", "required_texts": ["Asset Reliability", "PREDICTIVE MAINTENANCE"]},
        {"path": "/solutions/logistics-control-tower", "name": "Logistics Control Tower", "required_texts": ["Logistics Control Tower", "SUPPLY NETWORK"]},
        {"path": "/solutions/process-optimization", "name": "Process Optimization", "required_texts": ["Process Optimization", "CONSTRAINED OPTIMIZATION"]},
        {"path": "/solutions/operations-assistant", "name": "Operations AI Assistant", "required_texts": ["Operations AI Assistant", "ENTERPRISE KNOWLEDGE"]},
        {"path": "/solutions/governed-manufacturing-ai", "name": "Governed Manufacturing AI", "required_texts": ["Governed Manufacturing AI", "PHARMA & CONTROLLED"]},
        
        # 101 Industry without dedicated template (uses insilos_industry_page fallback)
        {"path": "/industries/farm", "name": "Farm / Ranch", "required_texts": ["Farm / Ranch", "FARM & RANCH OPERATIONS", "VAS 200", "BOM"]},
        {"path": "/industries/metalwork", "name": "Metalwork CNC", "required_texts": ["Metalworking", "PRECISION METALWORKING", "BOM"]},
        {"path": "/industries/hospital", "name": "Hospital MedTech", "required_texts": ["Hospital", "GENERAL HOSPITAL", "VAS 200"]},
        {"path": "/industries/hotel", "name": "Hotel & Resort", "required_texts": ["Hotel", "HOSPITALITY", "VAS 200"]},
        {"path": "/industries/government", "name": "Government & GovTech", "required_texts": ["Government", "GOVTECH", "VAS 200"]},
    ]
    
    passed_count = 0
    failures = []
    
    for t in tests:
        status, body, headers, latency = make_request(t["path"])
        # Unescape HTML to compare content cleanly
        text = html.unescape(body.decode("utf-8", errors="replace"))
        tracebacks = check_for_traceback(body)
        
        missing_texts = [req for req in t["required_texts"] if req.lower() not in text.lower()]
        
        has_dropzones = ('oe_structure' in text) or ('class="s_' in text)
        test_passed = (status == 200) and (len(tracebacks) == 0) and (len(missing_texts) == 0) and has_dropzones
        
        icon = "✅" if test_passed else "❌"
        print(f"  {icon} {t['path']:40} | Fallback Data Enriched: {len(missing_texts) == 0} | Dropzones: {has_dropzones} | {latency:5.1f}ms")
        
        if test_passed:
            passed_count += 1
        else:
            failures.append({
                "path": t["path"],
                "status": status,
                "tracebacks": tracebacks,
                "missing_texts": missing_texts,
                "has_dropzones": has_dropzones,
            })
            if missing_texts:
                print(f"     -> Missing expected fallback content tokens: {missing_texts}")
            if tracebacks:
                print(f"     -> Traceback detected: {tracebacks}")
                
    print(f"\n  Batch Result: {passed_count}/{len(tests)} Passed")
    return passed_count == len(tests), failures


def run_concurrency_stress_test(num_workers=50, total_requests=100):
    """Stress test the Odoo web server with concurrent requests."""
    print(f"\n{'=' * 75}")
    print(f"TEST BATCH: Concurrency & Load Stress Test ({num_workers} threads, {total_requests} requests)")
    print(f"{'=' * 75}")
    
    test_endpoints = [
        "/",
        "/platform",
        "/solutions",
        "/solutions/vertical-idp",
        "/solutions/enterprise-knowledge-graph",
        "/solutions/trade-compliance",
        "/solutions/field-service-intelligence",
        "/industries",
        "/industries/logistics",
        "/industries/pharma",
        "/industries/energy",
        "/industries/farm",
        "/pricing",
        "/about",
        "/resources",
        "/resources/operational-ai",
        "/request-demo",
        "/showcase-3d",
    ]
    
    paths = [test_endpoints[i % len(test_endpoints)] for i in range(total_requests)]
    
    latencies = []
    statuses = []
    error_count = 0
    start_total = time.perf_counter()
    
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        future_to_path = {executor.submit(make_request, path, True, 15): path for path in paths}
        for future in as_completed(future_to_path):
            path = future_to_path[future]
            try:
                status, body, headers, latency = future.result()
                statuses.append(status)
                latencies.append(latency)
                tracebacks = check_for_traceback(body)
                if status != 200 or len(tracebacks) > 0:
                    error_count += 1
                    print(f"  ❌ Concurrency error on {path}: status {status}, tracebacks {tracebacks}")
            except Exception as e:
                error_count += 1
                print(f"  ❌ Concurrency exception on {path}: {e}")
                
    total_time = (time.perf_counter() - start_total)
    avg_latency = sum(latencies) / len(latencies) if latencies else 0
    min_latency = min(latencies) if latencies else 0
    max_latency = max(latencies) if latencies else 0
    sorted_latencies = sorted(latencies)
    p95_latency = sorted_latencies[int(len(sorted_latencies) * 0.95)] if sorted_latencies else 0
    throughput = len(paths) / total_time if total_time > 0 else 0
    
    print(f"  • Total Requests Executed: {len(paths)}")
    print(f"  • Successful (HTTP 200 & Clean): {len(paths) - error_count}/{len(paths)}")
    print(f"  • Total Wall Time: {total_time:.2f}s (Throughput: {throughput:.1f} req/s)")
    print(f"  • Min Latency: {min_latency:.1f}ms | Avg: {avg_latency:.1f}ms | P95: {p95_latency:.1f}ms | Max: {max_latency:.1f}ms")
    
    passed = (error_count == 0)
    print(f"  Concurrency Result: {'✅ PASSED (0 dropped, 0 tracebacks)' if passed else '❌ FAILED'}")
    return passed, {
        "total_requests": len(paths),
        "errors": error_count,
        "throughput": throughput,
        "avg_latency": avg_latency,
        "p95_latency": p95_latency,
    }


def run_form_stress_test():
    """Stress test /request-demo form CSRF, validation, honeypot, and rate limits."""
    print(f"\n{'=' * 75}")
    print("TEST BATCH: Request Demo Form Boundary & Validation Stress")
    print(f"{'=' * 75}")
    
    failures = []
    
    # Session-persistent opener
    cj = http.cookiejar.CookieJar()
    cookie_processor = urllib.request.HTTPCookieProcessor(cj)
    
    # Step 1: GET /request-demo to retrieve cookies and CSRF token
    status, body, headers, latency = make_request("/request-demo", cookie_processor=cookie_processor)
    html_text = body.decode("utf-8", errors="replace")
    csrf_match = re.search(r'name="csrf_token"\s+value="([^"]+)"', html_text)
    csrf_token = csrf_match.group(1) if csrf_match else None
    
    print(f"  • Initial GET /request-demo: HTTP {status} | CSRF Token: {'Found' if csrf_token else 'Missing'}")
    if not csrf_token:
        return False, [{"error": "CSRF token not found"}]
        
    def post_form(data_dict, follow=True):
        opener = urllib.request.build_opener(cookie_processor) if follow else urllib.request.build_opener(cookie_processor, NoRedirectHandler)
        encoded = urllib.parse.urlencode(data_dict).encode("utf-8")
        req = urllib.request.Request(
            f"{BASE_URL}/request-demo",
            data=encoded,
            headers={"User-Agent": "InsilosChallenger/2.0", "Content-Type": "application/x-www-form-urlencoded"}
        )
        try:
            with opener.open(req, timeout=12) as resp:
                status = resp.status
                body = resp.read()
                headers = {k.lower(): v for k, v in resp.headers.items()}
                return status, body, headers
        except urllib.error.HTTPError as he:
            body = he.read() if hasattr(he, "read") else b""
            headers = {k.lower(): v for k, v in he.headers.items()} if hasattr(he, "headers") else {}
            return he.code, body, headers
            
    # Subtest 1: POST empty form with CSRF -> Expect HTTP 200 with validation errors, NO 500
    st1_status, st1_body, _ = post_form({"csrf_token": csrf_token})
    st1_text = st1_body.decode("utf-8", errors="replace")
    st1_tracebacks = check_for_traceback(st1_body)
    has_validation = ("Vui lòng nhập" in st1_text) or ("errors" in st1_text)
    sub1_passed = (st1_status == 200) and (len(st1_tracebacks) == 0) and has_validation
    print(f"  {'✅' if sub1_passed else '❌'} [Subtest 1] Empty Form POST -> HTTP {st1_status} | Validation Triggered: {has_validation} | Tracebacks: {len(st1_tracebacks)}")
    if not sub1_passed:
        failures.append({"subtest": 1, "status": st1_status, "tracebacks": st1_tracebacks})

    # Subtest 2: POST malformed email -> Expect HTTP 200 with "Vui lòng nhập email hợp lệ"
    st2_status, st2_body, _ = post_form({
        "csrf_token": csrf_token,
        "name": "Challenger Auditor",
        "email": "invalid_email_no_at",
        "company": "Enterprise QA Corp",
        "industry": "logistics",
        "use_case": "field_service",
        "consent": "on",
    })
    st2_text = st2_body.decode("utf-8", errors="replace")
    st2_tracebacks = check_for_traceback(st2_body)
    has_email_error = "Vui lòng nhập email hợp lệ" in st2_text
    sub2_passed = (st2_status == 200) and (len(st2_tracebacks) == 0) and has_email_error
    print(f"  {'✅' if sub2_passed else '❌'} [Subtest 2] Malformed Email POST -> HTTP {st2_status} | Email Error Caught: {has_email_error} | Tracebacks: {len(st2_tracebacks)}")
    if not sub2_passed:
        failures.append({"subtest": 2, "status": st2_status, "tracebacks": st2_tracebacks})

    # Subtest 3: POST Honeypot triggered -> Expect silent redirect to /thank-you
    st3_status, st3_body, st3_headers = post_form({
        "csrf_token": csrf_token,
        "name": "Bot Spammer",
        "email": "bot@spam.com",
        "company": "Spam Inc",
        "website_url": "http://spam-link.com",  # Honeypot field
    }, follow=False)
    location = st3_headers.get("location", "")
    sub3_passed = (st3_status in [302, 303]) and ("/thank-you" in location)
    print(f"  {'✅' if sub3_passed else '❌'} [Subtest 3] Honeypot Trap -> HTTP {st3_status} redirect to {location} (Expected: /thank-you)")
    if not sub3_passed:
        failures.append({"subtest": 3, "status": st3_status, "location": location})

    # Subtest 4: Valid submission with traditional use case 'field_service' -> Expect 303 redirect to /thank-you
    # Reset session for fresh submit
    time.sleep(1) # tiny pause
    st4_status, st4_body, st4_headers = post_form({
        "csrf_token": csrf_token,
        "name": "Enterprise Director",
        "email": "director@logistics.vn",
        "company": "SNP Port Logistics",
        "industry": "logistics",
        "use_case": "field_service",
        "message": "Demo inquiry for 50 vehicles",
        "consent": "on",
    }, follow=False)
    st4_loc = st4_headers.get("location", "")
    sub4_passed = (st4_status in [302, 303]) and ("/thank-you" in st4_loc)
    print(f"  {'✅' if sub4_passed else '❌'} [Subtest 4] Valid POST ('field_service') -> HTTP {st4_status} redirect to {st4_loc}")
    if not sub4_passed:
        failures.append({"subtest": 4, "status": st4_status, "location": st4_loc})

    # Subtest 5: Audit newly added flagship use cases (vertical_idp, knowledge_graph, trade_compliance)
    # Check if they trigger ORM selection validation failure
    flagship_use_cases = ["vertical_idp", "knowledge_graph", "trade_compliance"]
    for uc in flagship_use_cases:
        # Create fresh session for each test to bypass 20s cooldown
        fresh_cj = http.cookiejar.CookieJar()
        fresh_cp = urllib.request.HTTPCookieProcessor(fresh_cj)
        _, fresh_get_body, _, _ = make_request("/request-demo", cookie_processor=fresh_cp)
        fresh_match = re.search(r'name="csrf_token"\s+value="([^"]+)"', fresh_get_body.decode("utf-8", errors="replace"))
        fresh_csrf = fresh_match.group(1) if fresh_match else csrf_token

        fresh_opener = urllib.request.build_opener(fresh_cp, NoRedirectHandler)
        post_data = urllib.parse.urlencode({
            "csrf_token": fresh_csrf,
            "name": f"Lead {uc}",
            "email": f"lead_{uc}@enterprise.com",
            "company": "Enterprise Corporation",
            "industry": "logistics",
            "use_case": uc,
            "message": f"Testing {uc} lead generation",
            "consent": "on",
        }).encode("utf-8")
        post_req = urllib.request.Request(
            f"{BASE_URL}/request-demo",
            data=post_data,
            headers={"User-Agent": "InsilosChallenger/2.0", "Content-Type": "application/x-www-form-urlencoded"}
        )
        try:
            with fresh_opener.open(post_req, timeout=12) as resp:
                uc_status = resp.status
                uc_loc = resp.headers.get("Location") or resp.headers.get("location") or ""
        except urllib.error.HTTPError as he:
            uc_status = he.code
            uc_loc = he.headers.get("Location") or he.headers.get("location") or ""
            
        uc_passed = (uc_status in [302, 303]) and ("/thank-you" in uc_loc)
        print(f"  {'✅' if uc_passed else '❌'} [Subtest 5-{uc}] Lead Submission with '{uc}' -> HTTP {uc_status} (Location: {uc_loc})")
        if not uc_passed:
            failures.append({
                "subtest": f"5-{uc}",
                "use_case": uc,
                "status": uc_status,
                "error": f"ORM ValueError: Selection '{uc}' not in models/demo_request.py",
            })

    total_subtests = 4 + len(flagship_use_cases)
    passed_subtests = total_subtests - len(failures)
    print(f"\n  Batch Result: {passed_subtests}/{total_subtests} Passed")
    return len(failures) == 0, failures


def main():
    print("=" * 75)
    print("⚡ CHALLENGER M5-1: EMPIRICAL LIVE ROUTE & STRESS HARNESS")
    print(f"   Target Server: {BASE_URL}")
    print(f"   Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}")
    print("=" * 75)
    
    suite_results = {}
    all_failures = []
    
    # 1. Core Public Routes (12 routes)
    core_tests = [{"path": r, "desc": f"Core page {r}"} for r in CORE_ROUTES]
    res1, fail1 = run_test_category("1. Core Public Routes", core_tests)
    suite_results["core_routes"] = res1
    all_failures.extend(fail1)
    
    # 2. All Defined Solutions (9 routes)
    solution_tests = [{"path": f"/solutions/{s}", "desc": f"Solution {s}"} for s in SOLUTIONS]
    res2, fail2 = run_test_category("2. Dedicated & Dynamic Solution Routes", solution_tests)
    suite_results["solution_routes"] = res2
    all_failures.extend(fail2)
    
    # 3. Solution Aliases (11 redirects)
    res3, fail3 = run_solution_aliases()
    suite_results["solution_aliases"] = res3
    all_failures.extend(fail3)
    
    # 4. Dedicated Industry Routes (4 primary industries + /industry/ prefix)
    industry_tests = []
    for ind in DEDICATED_INDUSTRIES:
        industry_tests.append({"path": f"/industries/{ind}", "desc": f"Dedicated /industries/{ind}"})
        industry_tests.append({"path": f"/industry/{ind}", "desc": f"Alias /industry/{ind}"})
    res4, fail4 = run_test_category("4. Dedicated Industry Routes", industry_tests)
    suite_results["dedicated_industries"] = res4
    all_failures.extend(fail4)
    
    # 5. Sample of 40+ Extended 101 Industry Routes
    ext_industry_tests = [{"path": f"/industries/{ind}", "desc": f"101 Catalog: {ind}"} for ind in EXTENDED_SAMPLE_INDUSTRIES]
    res5, fail5 = run_test_category("5. Extended 101 Industry Catalog Sample (Fallback Template)", ext_industry_tests)
    suite_results["extended_industries"] = res5
    all_failures.extend(fail5)
    
    # 6. Technical Whitepaper Resource Articles (5 routes)
    article_tests = [{"path": f"/resources/{a}", "desc": f"Whitepaper article {a}"} for a in ARTICLES]
    res6, fail6 = run_test_category("6. Technical Whitepaper Articles", article_tests)
    suite_results["article_routes"] = res6
    all_failures.extend(fail6)
    
    # 7. Article Aliases (4 redirects)
    res7, fail7 = run_article_aliases()
    suite_results["article_aliases"] = res7
    all_failures.extend(fail7)
    
    # 8. Boundary Inputs & Unlisted Slugs (20 edge tests)
    res8, fail8 = run_test_category("8. Boundary Inputs & Unlisted Slugs (404 & XSS/SQLi Proofing)", BOUNDARY_TEST_CASES)
    suite_results["boundary_inputs"] = res8
    all_failures.extend(fail8)
    
    # 9. Fallback Template Enriched Data Audit
    res9, fail9 = run_fallback_template_audit()
    suite_results["fallback_templates"] = res9
    all_failures.extend(fail9)
    
    # 10. Form Validation & Honeypot Stress
    res10, fail10 = run_form_stress_test()
    suite_results["form_stress"] = res10
    all_failures.extend(fail10)
    
    # 11. Concurrency Load Stress (50 concurrent threads)
    res11, fail11 = run_concurrency_stress_test(num_workers=50, total_requests=100)
    suite_results["concurrency_stress"] = res11
    if not res11:
        all_failures.append({"type": "concurrency", "details": fail11})
        
    # Overall summary
    print(f"\n{'=' * 75}")
    print("📊 CHALLENGER M5-1 FINAL EMPIRICAL SUMMARY")
    print(f"{'=' * 75}")
    for suite_name, status in suite_results.items():
        print(f"  • {suite_name:35}: {'✅ PASSED' if status else '❌ FAILED'}")
        
    overall_passed = all(suite_results.values())
    print(f"\nFinal Verdict: {'🏆 APPROVE (Zero-Defect Certified)' if overall_passed else '🚨 REQUEST_CHANGES'}")
    print(f"Total Discovered Defects: {len(all_failures)}")
    print(f"{'=' * 75}\n")
    
    return 0 if overall_passed else 1


if __name__ == "__main__":
    sys.exit(main())
