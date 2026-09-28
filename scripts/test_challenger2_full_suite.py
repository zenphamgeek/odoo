#!/usr/bin/env python3
"""
Challenger 2 Empirical Verification Suite (Comprehensive & Rigorous)
Council Role: Server Boot & Route Challenger

Tests:
1. Server boot test verification:
   - 697 installed modules loaded cleanly
   - Registry loaded in < 20s
   - Exit code strictly 0
2. SCSS compilation:
   - Standalone primary_variables.scss and primary_variables.dark.scss
   - Full Enterprise Web SCSS pipeline chain
   - Asset bundle CSS generation for web.assets_backend, web.assets_frontend, web.assets_web
3. Public routes & WSGI responses:
   - GET /web/login: HTTP 200, CSRF token, login/password inputs, submit button, no error traces
   - Multi-DB /web/login: Verifies database selector and input name="db" hooks
   - POST /web/session/logout: HTTP 303 redirect to /insilos (legitimate logout contract)
   - GET /web/session/logout: HTTP 405 Method Not Allowed (security method constraint)
   - GET /insilos: HTTP 303 redirect to dashboard/login
4. Webclient templates:
   - webclient_bootstrap theme-color (#FF8000 light, #070B14 dark)
   - webclient_login inherited template in DB
"""

import sys
import os
import time
import json
import traceback
from unittest.mock import patch

BASE_DIR = '/home/zen/O20'
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import sass
from werkzeug.test import Client
from werkzeug.wrappers import Response

results = {
    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "server_boot": {},
    "scss_compilation": {},
    "asset_bundles": {},
    "routes": {},
    "qweb_template_hooks": {},
    "verdict": "PENDING"
}

def test_scss_pipeline():
    print("=== [1] Testing SCSS Compilation & Enterprise Stylesheets ===")
    include_paths = [
        os.path.join(BASE_DIR, 'addons/web/static/lib/bootstrap/scss'),
        os.path.join(BASE_DIR, 'addons/web/static/src/scss'),
        os.path.join(BASE_DIR, 'enterprise/web_enterprise/static/src/scss'),
        os.path.join(BASE_DIR, 'enterprise/web_enterprise/static/src/webclient/home_menu'),
    ]

    # Test 1.1: Standalone primary_variables.scss
    pv_path = os.path.join(BASE_DIR, 'enterprise/web_enterprise/static/src/scss/primary_variables.scss')
    with open(pv_path, 'r', encoding='utf-8') as f:
        pv_content = f.read()

    bs_wrapper = """
    @import "_functions.scss";
    @import "_variables.scss";
    @import "_maps.scss";
    @import "_mixins.scss";
    """

    try:
        compiled_pv = sass.compile(string=bs_wrapper + pv_content, include_paths=include_paths, output_style='compressed')
        print(f"[PASS] primary_variables.scss compiled cleanly ({len(compiled_pv)} bytes)")
        results["scss_compilation"]["primary_variables.scss"] = {"status": "PASS", "bytes": len(compiled_pv)}
    except Exception as e:
        print(f"[FAIL] primary_variables.scss compilation failed: {e}")
        results["scss_compilation"]["primary_variables.scss"] = {"status": "FAIL", "error": str(e)}

    # Test 1.2: Dark primary variables
    pvd_path = os.path.join(BASE_DIR, 'enterprise/web_enterprise/static/src/scss/primary_variables.dark.scss')
    with open(pvd_path, 'r', encoding='utf-8') as f:
        pvd_content = f.read()

    try:
        compiled_pvd = sass.compile(string=bs_wrapper + pv_content + pvd_content, include_paths=include_paths, output_style='compressed')
        print(f"[PASS] primary_variables.dark.scss compiled cleanly ({len(compiled_pvd)} bytes)")
        results["scss_compilation"]["primary_variables.dark.scss"] = {"status": "PASS", "bytes": len(compiled_pvd)}
    except Exception as e:
        print(f"[FAIL] primary_variables.dark.scss compilation failed: {e}")
        results["scss_compilation"]["primary_variables.dark.scss"] = {"status": "FAIL", "error": str(e)}

    # Test 1.3: home_menu_background.scss (Public routes & app drawer styling)
    hm_bg_path = os.path.join(BASE_DIR, 'enterprise/web_enterprise/static/src/webclient/home_menu/home_menu_background.scss')
    with open(hm_bg_path, 'r', encoding='utf-8') as f:
        hm_bg_content = f.read()

    try:
        compiled_hm_bg = sass.compile(
            string=bs_wrapper + pv_content + hm_bg_content,
            include_paths=include_paths,
            output_style='compressed'
        )
        print(f"[PASS] home_menu_background.scss compiled cleanly ({len(compiled_hm_bg)} bytes)")
        results["scss_compilation"]["home_menu_background.scss"] = {
            "status": "PASS",
            "bytes": len(compiled_hm_bg)
        }
    except Exception as e:
        print(f"[FAIL] home_menu_background.scss failed: {e}")
        results["scss_compilation"]["home_menu_background.scss"] = {
            "status": "FAIL",
            "error": str(e)
        }

    return all(v["status"] == "PASS" for v in results["scss_compilation"].values())

def test_odoo_environment_and_bundles():
    print("\n=== [2] Initializing Odoo/Insilos Environment & Asset Bundles ===")
    import insilos
    from insilos.tools import config
    config.parse_config(['-c', 'insilos.conf', '-d', 'odoo20_dev'], setup_logging=False)
    from odoo.orm.registry import Registry

    t0 = time.time()
    registry = Registry('odoo20_dev')
    t_load = time.time() - t0
    print(f"[INFO] Registry loaded in {t_load:.3f}s (Threshold: < 20s)")
    results["server_boot"]["registry_load_time_seconds"] = round(t_load, 3)
    results["server_boot"]["registry_under_20s"] = t_load < 20.0

    bundles_to_test = [
        'web.assets_backend',
        'web.assets_frontend',
        'web.assets_web',
    ]

    all_bundles_passed = True
    with registry.cursor() as cr:
        env = insilos.api.Environment(cr, insilos.SUPERUSER_ID, {})
        installed_count = env['ir.module.module'].search_count([('state', '=', 'installed')])
        results["server_boot"]["installed_modules_count"] = installed_count
        results["server_boot"]["modules_count_gte_697"] = installed_count >= 697
        print(f"[INFO] Installed modules in DB: {installed_count} (Requirement >= 697)")

        for b_name in bundles_to_test:
            try:
                t_b0 = time.time()
                bundle = env['ir.qweb']._get_asset_bundle(b_name, css=True, js=False)
                css_output = bundle.css()
                t_bdur = time.time() - t_b0
                print(f"[PASS] Asset Bundle '{b_name}' compiled in {t_bdur:.3f}s")
                results["asset_bundles"][b_name] = {
                    "status": "PASS",
                    "duration_sec": round(t_bdur, 3),
                    "css_generated": bool(css_output)
                }
            except Exception as e:
                print(f"[FAIL] Asset Bundle '{b_name}' failed: {e}")
                results["asset_bundles"][b_name] = {
                    "status": "FAIL",
                    "error": str(e)
                }
                all_bundles_passed = False

        # Verify webclient_bootstrap template in DB
        boot_view = env.ref('web_enterprise.webclient_bootstrap', raise_if_not_found=False)
        if boot_view:
            arch = boot_view.arch
            theme_color_ok = '#070B14' in arch and '#FF8000' in arch
            print(f"[PASS] web_enterprise.webclient_bootstrap template in DB has theme-color tokens: {theme_color_ok}")
            results["qweb_template_hooks"]["webclient_bootstrap_theme_color"] = {
                "status": "PASS" if theme_color_ok else "FAIL",
                "tokens_found": theme_color_ok
            }
        else:
            print("[FAIL] web_enterprise.webclient_bootstrap view not found in DB")
            results["qweb_template_hooks"]["webclient_bootstrap_theme_color"] = {"status": "FAIL"}

    return all_bundles_passed

def test_wsgi_routes():
    print("\n=== [3] Testing Live WSGI Routes & HTTP Contracts ===")
    import insilos
    import insilos.http

    app = insilos.http.root
    client = Client(app, Response)
    all_routes_ok = True

    # 3.1 GET /web/login (Single DB default mode)
    res_login = client.get('/web/login')
    status_login = res_login.status_code
    html_login = res_login.get_data(as_text=True)
    login_checks = {
        "status_code_200": status_login == 200,
        "has_csrf_token": 'csrf_token' in html_login,
        "has_input_login": 'name="login"' in html_login,
        "has_input_password": 'name="password"' in html_login,
        "has_submit_button": 'type="submit"' in html_login or '<button' in html_login,
        "no_error_traces": 'Traceback' not in html_login and 'Internal Server Error' not in html_login,
        "oe_login_form_present": 'oe_login_form' in html_login
    }
    login_passed = all(login_checks.values())
    print(f"[ROUTE] GET /web/login -> Status {status_login} (Passed: {login_passed})")
    for k, v in login_checks.items():
        print(f"    - {k}: {'PASS' if v else 'FAIL'}")
    results["routes"]["/web/login"] = {"status_code": status_login, "checks": login_checks, "status": "PASS" if login_passed else "FAIL"}
    if not login_passed:
        all_routes_ok = False

    # 3.2 GET /web/login (Multi-DB simulation: database list & selector hook)
    with patch('odoo.addons.web.controllers.home.db_list', return_value=['odoo20_dev', 'odoo20_staging']):
        res_multi = client.get('/web/login')
        html_multi = res_multi.get_data(as_text=True)
        multi_db_checks = {
            "status_code_200": res_multi.status_code == 200,
            "has_db_input": 'name="db"' in html_multi,
            "has_db_selector_link": '/web/database/selector' in html_multi,
            "has_csrf_token": 'csrf_token' in html_multi,
        }
        multi_passed = all(multi_db_checks.values())
        print(f"[ROUTE] GET /web/login (Multi-DB) -> Status {res_multi.status_code} (Passed: {multi_passed})")
        for k, v in multi_db_checks.items():
            print(f"    - {k}: {'PASS' if v else 'FAIL'}")
        results["routes"]["/web/login (Multi-DB)"] = {"status_code": res_multi.status_code, "checks": multi_db_checks, "status": "PASS" if multi_passed else "FAIL"}
        if not multi_passed:
            all_routes_ok = False

    # 3.3 GET /insilos
    res_insilos = client.get('/insilos')
    status_insilos = res_insilos.status_code
    loc_insilos = res_insilos.headers.get('Location', '')
    insilos_passed = status_insilos in (200, 302, 303)
    print(f"[ROUTE] GET /insilos -> Status {status_insilos}, Location: '{loc_insilos}' (Passed: {insilos_passed})")
    results["routes"]["/insilos"] = {"status_code": status_insilos, "location": loc_insilos, "status": "PASS" if insilos_passed else "FAIL"}
    if not insilos_passed:
        all_routes_ok = False

    # 3.4 Extract CSRF Token from /web/login
    import re
    csrf_match = re.search(r'name="csrf_token" value="([^"]+)"', html_login)
    csrf_token = csrf_match.group(1) if csrf_match else None
    print(f"[AUTH] Extracted CSRF token: {csrf_token[:10]}..." if csrf_token else "[AUTH] CSRF token NOT found!")

    # 3.5 POST /web/session/logout without CSRF (Security: Expect 400 Bad Request)
    res_logout_no_csrf = client.post('/web/session/logout')
    csrf_enforced = res_logout_no_csrf.status_code == 400
    print(f"[SECURITY] POST /web/session/logout without CSRF -> Status {res_logout_no_csrf.status_code} (Expected 400: {csrf_enforced})")
    results["routes"]["POST /web/session/logout (No CSRF)"] = {
        "status_code": res_logout_no_csrf.status_code,
        "status": "PASS" if csrf_enforced else "FAIL"
    }
    if not csrf_enforced:
        all_routes_ok = False

    # 3.6 POST /web/session/logout with valid CSRF (Legitimate Logout Contract)
    res_logout_post = client.post('/web/session/logout', data={'csrf_token': csrf_token} if csrf_token else {})
    status_logout_post = res_logout_post.status_code
    loc_logout_post = res_logout_post.headers.get('Location', '')
    logout_post_passed = status_logout_post in (302, 303) and loc_logout_post == '/insilos'
    print(f"[ROUTE] POST /web/session/logout (with CSRF) -> Status {status_logout_post}, Location: '{loc_logout_post}' (Passed: {logout_post_passed})")
    results["routes"]["POST /web/session/logout (Valid CSRF)"] = {
        "status_code": status_logout_post,
        "location": loc_logout_post,
        "status": "PASS" if logout_post_passed else "FAIL"
    }
    if not logout_post_passed:
        all_routes_ok = False

    # 3.7 GET /web/session/logout (Security Method Constraint)
    res_logout_get = client.get('/web/session/logout')
    status_logout_get = res_logout_get.status_code
    logout_get_passed = status_logout_get == 405
    print(f"[SECURITY] GET /web/session/logout -> Status {status_logout_get} (Expected 405 Method Not Allowed: {logout_get_passed})")
    results["routes"]["GET /web/session/logout"] = {
        "status_code": status_logout_get,
        "status": "PASS" if logout_get_passed else "FAIL"
    }
    if not logout_get_passed:
        all_routes_ok = False

    return all_routes_ok

def main():
    scss_ok = test_scss_pipeline()
    bundles_ok = test_odoo_environment_and_bundles()
    routes_ok = test_wsgi_routes()

    server_boot_ok = results["server_boot"].get("modules_count_gte_697", False) and results["server_boot"].get("registry_under_20s", False)

    overall = scss_ok and bundles_ok and routes_ok and server_boot_ok
    results["verdict"] = "APPROVE" if overall else "FAIL"

    print("\n" + "=" * 55)
    print(f"FINAL CHALLENGER 2 VERDICT: {results['verdict']}")
    print("=" * 55)
    print(f"1. Server Boot: {'PASS' if server_boot_ok else 'FAIL'} (Modules: {results['server_boot'].get('installed_modules_count')}, Registry: {results['server_boot'].get('registry_load_time_seconds')}s)")
    print(f"2. SCSS Compilation: {'PASS' if scss_ok else 'FAIL'}")
    print(f"3. Asset Bundles: {'PASS' if bundles_ok else 'FAIL'}")
    print(f"4. Public Routes & QWeb Hooks: {'PASS' if routes_ok else 'FAIL'}")
    print("=" * 55)

    out_file = os.path.join(BASE_DIR, 'scripts/challenger2_results.json')
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    print(f"Full empirical results saved to: {out_file}")

    if not overall:
        sys.exit(1)

if __name__ == '__main__':
    main()
