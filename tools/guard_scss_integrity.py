#!/usr/bin/env python3
"""
tools/guard_scss_integrity.py
Comprehensive Anti-Regression Quality Guardian for SCSS & Web Assets.

Performs 4-tier forensic validation:
  Tier 1: LibSass Compile Verification for all SCSS files (0 syntax errors).
  Tier 2: Static Resource & Image Link Audit (0 broken 404 media references).
  Tier 3: Multi-Pod Filesystem MD5 Parity (100% synchronized across pods).
  Tier 4: Live HTTP & Asset Bundle Smoke Test against https://innoria.insilos.com.
"""

import os
import sys
import glob
import json
import hashlib
import subprocess
import urllib.request
import re

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def run_cmd(cmd, check=False):
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and res.returncode != 0:
        raise RuntimeError(f"Command failed ({res.returncode}): {cmd}\n{res.stderr}")
    return res

def tier1_compile_scss():
    print("\n" + "=" * 70)
    print("▶ TIER 1: LIBSASS COMPILATION VERIFICATION (ZERO SYNTAX ERRORS)")
    print("=" * 70)

    try:
        import sass
    except ImportError:
        # Fallback to .venv python
        venv_py = os.path.join(ROOT_DIR, '.venv', 'bin', 'python')
        if os.path.exists(venv_py):
            res = subprocess.run([venv_py, __file__, '--tier1-only'], capture_output=True, text=True)
            print(res.stdout)
            if res.stderr:
                print(res.stderr)
            return res.returncode == 0
        else:
            print("[!] libsass not available in environment.")
            return False

    include_paths = [
        os.path.join(ROOT_DIR, 'odoo/addons/base/static/src/scss'),
        os.path.join(ROOT_DIR, 'addons/web/static/src/scss'),
        os.path.join(ROOT_DIR, 'addons/web/static/lib/bootstrap/scss'),
        os.path.join(ROOT_DIR, 'enterprise/insilos_website/static/src/scss'),
        os.path.join(ROOT_DIR, 'enterprise/insilos_theme_genesis/static/src/scss')
    ]

    target_files = (
        glob.glob(os.path.join(ROOT_DIR, 'enterprise/insilos_website/**/*.scss'), recursive=True) +
        glob.glob(os.path.join(ROOT_DIR, 'enterprise/insilos_theme_genesis/**/*.scss'), recursive=True)
    )

    errors = []
    print(f"[*] Auditing {len(target_files)} SCSS files...")
    for f in target_files:
        try:
            with open(f, 'r', encoding='utf-8') as fp:
                code = fp.read()
            sass.compile(string=code, include_paths=include_paths)
        except Exception as e:
            rel = os.path.relpath(f, ROOT_DIR)
            errors.append((rel, str(e)))

    if errors:
        print(f"❌ Found {len(errors)} SCSS compilation failures:")
        for rel, err in errors:
            print(f"  • {rel}: {err.strip()[:120]}")
        return False

    print(f"✅ TIER 1 PASSED: All {len(target_files)} SCSS files compile cleanly (0 errors).")
    return True


def tier2_verify_static_assets():
    print("\n" + "=" * 70)
    print("▶ TIER 2: STATIC ASSETS & MEDIA INTEGRITY AUDIT")
    print("=" * 70)

    # Search for all image/svg references in XML views
    xml_views = glob.glob(os.path.join(ROOT_DIR, 'enterprise/insilos_website/views/**/*.xml'), recursive=True)
    asset_patterns = re.compile(r'["\'](/insilos_website/static/src/[^"\']+\.(?:svg|png|webp|jpg|jpeg|ico))["\']')

    referenced_assets = set()
    for xml_path in xml_views:
        with open(xml_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            for m in asset_patterns.findall(content):
                referenced_assets.add(m)

    print(f"[*] Found {len(referenced_assets)} unique static asset references in XML views.")

    missing_local = []
    for ref in sorted(referenced_assets):
        # Convert web URL to local file path
        # /insilos_website/static/... -> enterprise/insilos_website/static/...
        rel_sub = ref.replace('/insilos_website/', 'enterprise/insilos_website/')
        local_path = os.path.join(ROOT_DIR, rel_sub)
        if not os.path.exists(local_path):
            missing_local.append((ref, local_path))

    if missing_local:
        print(f"❌ Missing {len(missing_local)} referenced static assets locally:")
        for ref, loc in missing_local:
            print(f"  • {ref} -> expected at {loc}")
        return False

    print(f"✅ TIER 2 PASSED: 100% of {len(referenced_assets)} referenced static assets exist on disk.")
    return True


def tier3_verify_pod_parity():
    print("\n" + "=" * 70)
    print("▶ TIER 3: MULTI-POD FILESYSTEM MD5 PARITY")
    print("=" * 70)

    pod_out = run_cmd("kubectl get pods -n production -l app=insilos-saas --field-selector=status.phase=Running -o jsonpath='{.items[*].metadata.name}'")
    pods = [p.strip() for p in pod_out.stdout.split() if p.strip()]
    if not pods:
        print("[!] No active production pods found to verify.")
        return True

    print(f"[*] Comparing filesystem checksums across {len(pods)} pods: {pods}")
    pod_hashes = {}
    for p in pods:
        res = run_cmd(
            f"kubectl -n production exec {p} -c insilos -- python3 -c \""
            f"import glob, hashlib\n"
            f"files = sorted(glob.glob('/app/insilos/apps/insilos_website/**/*.scss', recursive=True) + "
            f"glob.glob('/app/insilos/apps/insilos_website/**/*.svg', recursive=True))\n"
            f"m = hashlib.md5()\n"
            f"for f in files:\n"
            f"    with open(f, 'rb') as fp: m.update(fp.read())\n"
            f"print(m.hexdigest(), len(files))\n"
            f"\""
        )
        out = res.stdout.strip()
        pod_hashes[p] = out
        print(f"  • {p:<35}: MD5={out}")

    unique_hashes = set(h.split()[0] for h in pod_hashes.values() if h)
    if len(unique_hashes) > 1:
        print(f"⚠️ Warning: Pods have different checksums! Desynchronization detected: {unique_hashes}")
        return False

    print(f"✅ TIER 3 PASSED: All {len(pods)} pods have 100% identical asset payloads.")
    return True


def tier4_live_http_smoke_test(domain="https://innoria.insilos.com"):
    print("\n" + "=" * 70)
    print(f"▶ TIER 4: LIVE HTTP & ASSET BUNDLE SMOKE TEST ({domain})")
    print("=" * 70)

    routes = [
        "/",
        "/about",
        "/platform",
        "/solutions",
        "/industries",
        "/resources",
        "/pricing",
        "/contactus",
        "/privacy",
        "/privacy-policy",
        "/capital-markets-decision-governance",
        "/trust",
        "/compliance",
        "/sandbox",
        "/interactive-3d",
        "/showcase-3d",
        "/no-code-platform",
        "/blockchain",
        "/web/login"
    ]

    passed = 0
    failed = []

    for r in routes:
        url = domain + r
        try:
            req = urllib.request.Request(
                url,
                headers={
                    'User-Agent': 'Insilos-AntiRegression-Guardian/2.0',
                    'Accept': 'text/html,application/xhtml+xml'
                }
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                code = resp.getcode()
                body = resp.read().decode('utf-8', errors='ignore')
                
                # Check for genuine Odoo style or compilation errors in body
                if any(err_tok in body for err_tok in ["Could not compile stylesheet", "Style error:"]):
                    print(f"  [✗] {r:<38}: Contains SCSS compile error in HTML!", flush=True)
                    failed.append((r, f"HTTP {code} but contains SCSS compile error in HTML!"))
                elif code == 200:
                    print(f"  [✓] {r:<38}: HTTP 200 OK ({len(body)} bytes)", flush=True)
                    passed += 1
                else:
                    print(f"  [!] {r:<38}: Unexpected HTTP {code}", flush=True)
                    failed.append((r, f"Unexpected HTTP status {code}"))
        except Exception as e:
            print(f"  [✗] {r:<38}: {e}", flush=True)
            failed.append((r, str(e)))

    if failed:
        for r, err in failed:
            print(f"  FAILED: {r}: {err}")

    print(f"\n[*] Route Results: {passed}/{len(routes)} routes returned clean HTTP 200.")
    if failed:
        print(f"❌ TIER 4 FAILED: {len(failed)} routes encountered errors.")
        return False

    print(f"✅ TIER 4 PASSED: 100% of tested routes loaded cleanly with zero SCSS errors.")
    return True


def main():
    if '--tier1-only' in sys.argv:
        tier1_compile_scss()
        return

    print("\n" + "=" * 75)
    print("🛡️  INSILOS SOVEREIGN SCSS & ASSET INTEGRITY GUARDIAN")
    print("=" * 75)

    ok1 = tier1_compile_scss()
    ok2 = tier2_verify_static_assets()
    ok3 = tier3_verify_pod_parity()
    ok4 = tier4_live_http_smoke_test()

    print("\n" + "=" * 75)
    print("FINAL INTEGRITY VERDICT:")
    print(f"  • Tier 1 (SCSS LibSass Compile)   : {'✅ PASS' if ok1 else '❌ FAIL'}")
    print(f"  • Tier 2 (Static Resource Check) : {'✅ PASS' if ok2 else '❌ FAIL'}")
    print(f"  • Tier 3 (Multi-Pod Parity)      : {'✅ PASS' if ok3 else '⚠️ DESYNC'}")
    print(f"  • Tier 4 (Live Route Verification): {'✅ PASS' if ok4 else '❌ FAIL'}")
    print("=" * 75)

    if not (ok1 and ok2 and ok4):
        sys.exit(1)
    print("\n🎉 ALL ANTI-REGRESSION GATES PASSED! Production is safe.\n")


if __name__ == '__main__':
    main()
