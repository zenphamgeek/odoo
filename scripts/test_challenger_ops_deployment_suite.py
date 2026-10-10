#!/usr/bin/env python3
"""
scripts/test_challenger_ops_deployment_suite.py
=============================================================================
Challenger 2 Empirical Verification & Adversarial Stress Test Suite
Council Role: Adversarial Cluster Ops Challenger

Adversarially stress-tests:
1. Deployment pipeline invariants in tools/deploy_innokafe_production.py
   - No parallel SIGTERM or blanket worker kill
   - Staggered SIGINT and sequential pod-by-pod rollout
   - Concurrent dual-tenant warmup (innokafe_prod + innoria_prod)
   - Pre-flight and post-flight reaper (< 40 slots) and schema invariance gates
2. PostgreSQL multi-tenant schema invariance across all 3 databases
   - Direct database audits (tables, columns, fields, models, modules, views)
   - verify_schema_invariance.py verification (0 DDL/mutations)
3. PostgreSQL connection pool limits & reaper verification
   - Both cluster (postgres-0) and local (5434) audits
   - innoria_prod connections strictly < 40 slots
   - reap_idle_connections.py --dry-run verification
4. In-pod worker discovery & local health probe verification
5. Live edge HTTP verification and cross-tenant isolation verification
=============================================================================
"""

import ast
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from typing import Dict, Any, List

ROOT_DIR = "/home/zen/O20"
DEPLOY_SCRIPT_PATH = os.path.join(ROOT_DIR, "tools/deploy_innokafe_production.py")
SCHEMA_SCRIPT_PATH = os.path.join(ROOT_DIR, "tools/verify_schema_invariance.py")
REAPER_SCRIPT_PATH = os.path.join(ROOT_DIR, "tools/reap_idle_connections.py")

test_results: Dict[str, Any] = {
    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "deployment_script_inspection": {},
    "schema_invariance_audit": {},
    "connection_pool_audit": {},
    "pod_runtime_verification": {},
    "live_edge_verification": {},
    "overall_verdict": "PENDING"
}


def log_section(title: str):
    print("\n" + "=" * 75)
    print(f"▶ {title.upper()}")
    print("=" * 75)


def test_1_adversarial_inspection_deploy_script() -> bool:
    log_section("1. Adversarial Inspection: tools/deploy_innokafe_production.py")
    passed = True

    if not os.path.exists(DEPLOY_SCRIPT_PATH):
        print(f"[✗] Deploy script missing at {DEPLOY_SCRIPT_PATH}")
        test_results["deployment_script_inspection"]["exists"] = False
        return False

    with open(DEPLOY_SCRIPT_PATH, "r", encoding="utf-8") as f:
        code_text = f.read()

    # 1.1 Assert NO SIGTERM anywhere in the script
    has_sigterm = "SIGTERM" in code_text or "signal.SIGTERM" in code_text
    print(f"  • SIGTERM absent: {not has_sigterm} (Found: {has_sigterm})")
    test_results["deployment_script_inspection"]["no_sigterm"] = not has_sigterm
    if has_sigterm:
        passed = False

    # 1.2 Assert NO blanket worker kills (kill -9, pkill, killall)
    blanket_kills = [m for m in ["pkill", "killall", "SIGKILL", "kill -9"] if m in code_text]
    print(f"  • Blanket kill commands absent: {len(blanket_kills) == 0} (Found: {blanket_kills})")
    test_results["deployment_script_inspection"]["no_blanket_kills"] = len(blanket_kills) == 0
    if blanket_kills:
        passed = False

    # 1.3 Assert staggered SIGINT is implemented
    has_sigint = "signal.SIGINT" in code_text
    has_stagger = "time.sleep(2.0)" in code_text or "time.sleep(2)" in code_text
    print(f"  • Graceful signal.SIGINT present: {has_sigint}")
    print(f"  • Staggered sleep interval present: {has_stagger}")
    test_results["deployment_script_inspection"]["has_sigint"] = has_sigint
    test_results["deployment_script_inspection"]["has_stagger"] = has_stagger
    if not (has_sigint and has_stagger):
        passed = False

    # 1.4 Assert sequential pod rollout (not parallel Popen for pod reload)
    # Check execute_sequential_rolling_reload implementation
    has_sequential_loop = bool(re.search(r"for\s+(?:idx,\s*)?pod\s+in\s+enumerate\(pods", code_text))
    # Ensure in-pod reload uses subprocess.run (synchronous per pod) rather than asynchronous Popen loop
    lines = code_text.splitlines()
    in_reload_func = False
    reload_func_lines = []
    for line in lines:
        if "def execute_sequential_rolling_reload" in line:
            in_reload_func = True
        elif in_reload_func and line.startswith("def "):
            break
        elif in_reload_func:
            reload_func_lines.append(line)
    reload_func_text = "\n".join(reload_func_lines)

    uses_sync_run = "subprocess.run" in reload_func_text
    has_no_async_popen_loop = "Popen" not in reload_func_text
    print(f"  • Sequential pod rollout loop: {has_sequential_loop}")
    print(f"  • Synchronous per-pod reload & probe (subprocess.run): {uses_sync_run}")
    print(f"  • No parallel Popen rollout in rolling reload: {has_no_async_popen_loop}")
    test_results["deployment_script_inspection"]["sequential_pod_rollout"] = (
        has_sequential_loop and uses_sync_run and has_no_async_popen_loop
    )
    if not (has_sequential_loop and uses_sync_run and has_no_async_popen_loop):
        passed = False

    # 1.5 Assert both innokafe_prod and innoria_prod are warmed up
    has_warmup_kafe = "innokafe_prod" in code_text and "safe_asset_warmup.py" in code_text
    has_warmup_ria = "innoria_prod" in code_text and "safe_asset_warmup.py" in code_text
    print(f"  • Pre-warm innokafe_prod present: {has_warmup_kafe}")
    print(f"  • Pre-warm innoria_prod present: {has_warmup_ria}")
    test_results["deployment_script_inspection"]["dual_warmup"] = has_warmup_kafe and has_warmup_ria
    if not (has_warmup_kafe and has_warmup_ria):
        passed = False

    # 1.6 Assert local health probe checks both tenant domains
    has_probe_hosts = "innoria.insilos.com" in code_text and "innokafe.insilos.com" in code_text
    print(f"  • In-pod health probe tests both tenant hosts: {has_probe_hosts}")
    test_results["deployment_script_inspection"]["health_probe_both_hosts"] = has_probe_hosts
    if not has_probe_hosts:
        passed = False

    # 1.7 Assert connection safety reaper and schema invariance gates are wired
    has_reaper_gate = "reap_idle_connections.py" in code_text
    has_schema_gate = "verify_schema_invariance.py" in code_text
    print(f"  • Connection reaper safety gate integrated: {has_reaper_gate}")
    print(f"  • Schema invariance safety gate integrated: {has_schema_gate}")
    test_results["deployment_script_inspection"]["safety_gates_integrated"] = has_reaper_gate and has_schema_gate
    if not (has_reaper_gate and has_schema_gate):
        passed = False

    # 1.8 Bytecode compile validation
    res_compile = subprocess.run([sys.executable, "-m", "py_compile", DEPLOY_SCRIPT_PATH], capture_output=True, text=True)
    compile_ok = res_compile.returncode == 0
    print(f"  • Bytecode compilation: {'PASS' if compile_ok else 'FAIL'}")
    test_results["deployment_script_inspection"]["compile_ok"] = compile_ok
    if not compile_ok:
        passed = False

    test_results["deployment_script_inspection"]["status"] = "PASS" if passed else "FAIL"
    return passed


def test_2_empirical_schema_invariance() -> bool:
    log_section("2. Empirical PostgreSQL Schema Invariance Across Multi-Tenant DBs")
    import psycopg2

    db_configs = {
        "host": "127.0.0.1",
        "port": 5434,
        "user": "odoo",
        "password": "1NN0R1@2026"
    }

    target_dbs = ["odoo20_dev", "insilos20_dev", "innoria_prod"]
    passed = True

    # 2.1 First run verify_schema_invariance.py directly
    print("[*] Executing tools/verify_schema_invariance.py...")
    res_script = subprocess.run([sys.executable, SCHEMA_SCRIPT_PATH], capture_output=True, text=True)
    script_exit_ok = res_script.returncode == 0
    print(f"  • verify_schema_invariance.py returncode: {res_script.returncode} ({'PASS' if script_exit_ok else 'FAIL'})")
    if not script_exit_ok:
        print("  Error output:", res_script.stderr.strip() or res_script.stdout.strip())
        passed = False

    test_results["schema_invariance_audit"]["script_exit_code"] = res_script.returncode

    # 2.2 Deep Direct SQL Invariant Verification
    print("\n[*] Performing independent deep SQL schema inspection across target databases...")
    for db in target_dbs:
        try:
            conn = psycopg2.connect(dbname=db, **db_configs)
            cur = conn.cursor()

            # Check 1: Tables
            cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name LIKE '%innokafe%';")
            leaked_tables = [r[0] for r in cur.fetchall()]

            # Check 2: Columns
            cur.execute("SELECT table_name, column_name FROM information_schema.columns WHERE table_schema='public' AND column_name LIKE '%innokafe%';")
            leaked_columns = [f"{r[0]}.{r[1]}" for r in cur.fetchall()]

            # Check 3: Models
            cur.execute("SELECT model FROM ir_model WHERE model LIKE '%innokafe%';")
            leaked_models = [r[0] for r in cur.fetchall()]

            # Check 4: Fields
            cur.execute("SELECT model, name FROM ir_model_fields WHERE name LIKE '%innokafe%';")
            leaked_fields = [f"{r[0]}.{r[1]}" for r in cur.fetchall()]

            # Check 5: Modules
            cur.execute("SELECT name, state FROM ir_module_module WHERE name LIKE '%innokafe%';")
            leaked_modules = [f"{r[0]}:{r[1]}" for r in cur.fetchall()]

            # Check 6: Views
            cur.execute("SELECT key, name FROM ir_ui_view WHERE key LIKE '%innokafe%' OR name LIKE '%innokafe%';")
            leaked_views = [f"{r[0]}:{r[1]}" for r in cur.fetchall()]

            conn.close()

            db_clean = (
                len(leaked_tables) == 0 and
                len(leaked_columns) == 0 and
                len(leaked_models) == 0 and
                len(leaked_fields) == 0 and
                len(leaked_modules) == 0 and
                len(leaked_views) == 0
            )

            print(f"  • DB '{db}':")
            print(f"      Tables: {len(leaked_tables)}, Columns: {len(leaked_columns)}, Models: {len(leaked_models)}, Fields: {len(leaked_fields)}, Modules: {len(leaked_modules)}, Views: {len(leaked_views)}")
            print(f"      Verdict: {'✅ STRICT INVARIANCE' if db_clean else '❌ LEAKAGE DETECTED'}")

            test_results["schema_invariance_audit"][db] = {
                "clean": db_clean,
                "leaked_tables": leaked_tables,
                "leaked_columns": leaked_columns,
                "leaked_models": leaked_models,
                "leaked_fields": leaked_fields,
                "leaked_modules": leaked_modules,
                "leaked_views": leaked_views
            }

            if not db_clean:
                passed = False

        except Exception as e:
            print(f"  [✗] Error connecting to {db}: {e}")
            test_results["schema_invariance_audit"][db] = {"error": str(e)}
            passed = False

    # 2.3 Verify Reference DB (innokafe_prod) to confirm dedicated schema exists there
    print("\n[*] Auditing reference database (innokafe_prod)...")
    try:
        conn_ref = psycopg2.connect(dbname="innokafe_prod", **db_configs)
        cur_ref = conn_ref.cursor()
        cur_ref.execute("SELECT name, state FROM ir_module_module WHERE name = 'innokafe_website';")
        ref_mod = cur_ref.fetchall()
        cur_ref.execute("SELECT table_name, column_name FROM information_schema.columns WHERE table_schema='public' AND column_name LIKE '%innokafe%';")
        ref_cols = [f"{r[0]}.{r[1]}" for r in cur_ref.fetchall()]
        conn_ref.close()

        ref_ok = len(ref_mod) > 0 and ref_mod[0][1] == 'installed' and len(ref_cols) == 7
        print(f"  • Reference innokafe_prod module installed: {ref_mod}")
        print(f"  • Reference dedicated columns count: {len(ref_cols)} (Expected: 7)")
        test_results["schema_invariance_audit"]["reference_innokafe_prod"] = {
            "module_installed": ref_ok,
            "columns": ref_cols
        }
        if not ref_ok:
            passed = False
    except Exception as e:
        print(f"  [✗] Error auditing innokafe_prod: {e}")
        passed = False

    test_results["schema_invariance_audit"]["status"] = "PASS" if passed else "FAIL"
    return passed


def test_3_empirical_connection_pool_limits() -> bool:
    log_section("3. Empirical PostgreSQL Connection Pool Limits & Reaper Verification")
    passed = True

    # 3.1 Run reap_idle_connections.py --dry-run
    print("[*] Executing tools/reap_idle_connections.py --dry-run...")
    res_reap = subprocess.run([sys.executable, REAPER_SCRIPT_PATH, "--dry-run"], capture_output=True, text=True)
    reap_exit_ok = res_reap.returncode == 0
    print(f"  • reaper returncode: {res_reap.returncode} ({'PASS' if reap_exit_ok else 'FAIL'})")
    if not reap_exit_ok:
        print("  Error output:", res_reap.stderr.strip() or res_reap.stdout.strip())
        passed = False

    # 3.2 Direct audit on local PostgreSQL (port 5434)
    print("\n[*] Auditing local PostgreSQL (127.0.0.1:5434) directly...")
    import psycopg2
    try:
        conn = psycopg2.connect(
            host="127.0.0.1", port=5434, user="odoo", password="1NN0R1@2026", dbname="innoria_prod"
        )
        cur = conn.cursor()
        cur.execute("SELECT count(*) FROM pg_stat_activity;")
        local_total = cur.fetchone()[0]

        cur.execute("SELECT count(*) FROM pg_stat_activity WHERE datname = 'innoria_prod';")
        local_innoria = cur.fetchone()[0]

        cur.execute("SELECT COALESCE(state, 'system/bg'), count(*) FROM pg_stat_activity GROUP BY state;")
        local_breakdown = {r[0]: r[1] for r in cur.fetchall()}

        conn.close()

        local_under_40 = local_innoria < 40 and local_total < 100
        print(f"  • Local Total Connections: {local_total}/100")
        print(f"  • Local innoria_prod Connections: {local_innoria} (< 40 threshold: {'PASS' if local_innoria < 40 else 'FAIL'})")
        print(f"  • Local State Breakdown: {local_breakdown}")

        test_results["connection_pool_audit"]["local"] = {
            "total": local_total,
            "innoria_prod": local_innoria,
            "under_40": local_innoria < 40,
            "breakdown": local_breakdown
        }

        if local_innoria >= 40:
            passed = False

    except Exception as e:
        print(f"  [✗] Local connection audit error: {e}")
        passed = False

    # 3.3 Direct audit on Cluster PostgreSQL (postgres-0)
    print("\n[*] Auditing Cluster PostgreSQL (postgres-0) directly...")
    try:
        cluster_cmd = [
            "kubectl", "exec", "-n", "database", "postgres-0", "--",
            "psql", "-U", "insilos", "-d", "postgres", "-t", "-A", "-c",
            "SELECT count(*) FROM pg_stat_activity WHERE datname = 'innoria_prod';"
        ]
        res_c1 = subprocess.run(cluster_cmd, capture_output=True, text=True, timeout=15)
        cluster_innoria = int(res_c1.stdout.strip()) if res_c1.returncode == 0 and res_c1.stdout.strip().isdigit() else -1

        cluster_cmd_total = [
            "kubectl", "exec", "-n", "database", "postgres-0", "--",
            "psql", "-U", "insilos", "-d", "postgres", "-t", "-A", "-c",
            "SELECT count(*) FROM pg_stat_activity;"
        ]
        res_c2 = subprocess.run(cluster_cmd_total, capture_output=True, text=True, timeout=15)
        cluster_total = int(res_c2.stdout.strip()) if res_c2.returncode == 0 and res_c2.stdout.strip().isdigit() else -1

        cluster_under_40 = cluster_innoria < 40 and cluster_innoria >= 0
        print(f"  • Cluster Total Connections: {cluster_total}/100")
        print(f"  • Cluster innoria_prod Connections: {cluster_innoria} (< 40 threshold: {'PASS' if cluster_under_40 else 'FAIL'})")

        test_results["connection_pool_audit"]["cluster"] = {
            "total": cluster_total,
            "innoria_prod": cluster_innoria,
            "under_40": cluster_under_40
        }

        if not cluster_under_40:
            passed = False

    except Exception as e:
        print(f"  [✗] Cluster connection audit error: {e}")
        passed = False

    test_results["connection_pool_audit"]["status"] = "PASS" if passed else "FAIL"
    return passed


def test_4_pod_runtime_and_health_probes() -> bool:
    log_section("4. In-Pod Worker Discovery & Local Health Probes")
    passed = True

    # 4.1 Discover active pods
    pod_out = subprocess.run(
        "kubectl get pods -n production -l app=insilos-saas --field-selector=status.phase=Running -o jsonpath='{.items[*].metadata.name}'",
        shell=True, capture_output=True, text=True
    )
    pods = [p.strip() for p in pod_out.stdout.split() if p.strip()]
    print(f"[*] Discovered {len(pods)} running pods: {pods}")
    test_results["pod_runtime_verification"]["pods"] = pods
    if not pods:
        return False

    lead_pod = pods[0]
    print(f"\n[*] Testing in-pod worker discovery algorithm on {lead_pod}...")
    discovery_code = """
import os
current_pid = os.getpid()
workers = []
for pid_str in sorted(os.listdir('/proc'), key=lambda x: int(x) if x.isdigit() else 999999):
    if not pid_str.isdigit():
        continue
    pid = int(pid_str)
    if pid <= 1 or pid == current_pid:
        continue
    try:
        with open(f'/proc/{pid}/stat') as f:
            fields = f.read().split()
            ppid = int(fields[3])
        with open(f'/proc/{pid}/cmdline', 'rb') as f:
            cmd = f.read()
        if ppid == 1 and b'insilos-bin' in cmd and b'gevent' not in cmd:
            workers.append(pid)
    except Exception:
        pass
print(workers)
"""
    res_disc = subprocess.run(
        ["kubectl", "exec", "-n", "production", lead_pod, "-c", "insilos", "--", "python3", "-c", discovery_code],
        capture_output=True, text=True, timeout=20
    )
    disc_out = res_disc.stdout.strip()
    try:
        workers = ast.literal_eval(disc_out)
        has_workers = isinstance(workers, list) and len(workers) > 0
        print(f"  • Discovered HTTP Workers: {workers} (Count: {len(workers)}) -> {'PASS' if has_workers else 'FAIL'}")
        test_results["pod_runtime_verification"]["workers"] = workers
        if not has_workers:
            passed = False
    except Exception as e:
        print(f"  [✗] Failed to parse discovered workers: {disc_out} ({e})")
        passed = False

    # 4.2 In-pod local health probe verification
    print(f"\n[*] Executing in-pod local HTTP health probe on port 8069 for both tenant domains...")
    probe_code = """
import urllib.request, sys
targets = [('innoria.insilos.com', 'Innoria'), ('innokafe.insilos.com', 'InnoKafe')]
for host, name in targets:
    req = urllib.request.Request('http://127.0.0.1:8069/', headers={'Host': host, 'X-Forwarded-Host': host, 'X-Forwarded-Proto': 'https'})
    with urllib.request.urlopen(req, timeout=15) as res:
        code = res.getcode()
        body = res.read().decode('utf-8', errors='ignore')
        print(f'{name}:{code}:{len(body)}')
"""
    res_probe = subprocess.run(
        ["kubectl", "exec", "-n", "production", lead_pod, "-c", "insilos", "--", "python3", "-c", probe_code],
        capture_output=True, text=True, timeout=25
    )
    probe_lines = res_probe.stdout.strip().splitlines()
    print("  Probe output:", probe_lines)
    test_results["pod_runtime_verification"]["probe_output"] = probe_lines
    probe_success = False
    if len(probe_lines) >= 2:
        statuses = [l.split(':')[1] for l in probe_lines if ':' in l]
        probe_success = all(s == '200' for s in statuses)
    print(f"  • Both tenant local probes HTTP 200: {'PASS' if probe_success else 'FAIL'}")
    if not probe_success:
        passed = False

    test_results["pod_runtime_verification"]["status"] = "PASS" if passed else "FAIL"
    return passed


def test_5_live_edge_verification_and_isolation() -> bool:
    log_section("5. Live Edge HTTPS Verification & Tenant Isolation")
    passed = True

    endpoints = [
        ("https://innoria.insilos.com/", "Innoria", ["INNORIA", "Tailored Technology"], ["o_innokafe_theme", "Specialty Coffee"]),
        ("https://innokafe.insilos.com/", "InnoKafe", ["InnoKafe", "Cà Phê Việt Nam"], ["Chấm Dứt Ốc Đảo Dữ Liệu", "Năng Lượng & Lưới Điện"])
    ]

    for url, tenant, expected_tokens, forbidden_tokens in endpoints:
        print(f"\n[*] Probing {tenant} Edge URL: {url}...")
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Challenger2-ClusterOps-Auditor/2.0"}
            )
            t0 = time.time()
            with urllib.request.urlopen(req, timeout=30) as resp:
                code = resp.getcode()
                body = resp.read().decode("utf-8", errors="ignore")
                latency = round(time.time() - t0, 3)

            print(f"  • HTTP Status: {code} OK (Latency: {latency}s, Size: {len(body)} bytes)")

            # Check expected tokens
            found_expected = [tok for tok in expected_tokens if tok in body]
            print(f"  • Expected tokens present: {found_expected == expected_tokens} ({found_expected})")

            # Check forbidden tokens (isolation check)
            found_forbidden = [tok for tok in forbidden_tokens if tok in body]
            print(f"  • Zero forbidden leak tokens: {len(found_forbidden) == 0} (Found: {found_forbidden})")

            test_results["live_edge_verification"][tenant] = {
                "url": url,
                "status_code": code,
                "latency_sec": latency,
                "expected_ok": found_expected == expected_tokens,
                "isolation_ok": len(found_forbidden) == 0
            }

            if code != 200 or found_expected != expected_tokens or len(found_forbidden) > 0:
                passed = False

        except Exception as e:
            print(f"  [✗] Error requesting {url}: {e}")
            test_results["live_edge_verification"][tenant] = {"error": str(e)}
            passed = False

    test_results["live_edge_verification"]["status"] = "PASS" if passed else "FAIL"
    return passed


def main():
    t_start = time.time()
    print("=" * 75)
    print("🛡️  CHALLENGER 2: ADVERSARIAL CLUSTER OPS & DEPLOYMENT STRESS HARNESS")
    print("=" * 75)

    ok1 = test_1_adversarial_inspection_deploy_script()
    ok2 = test_2_empirical_schema_invariance()
    ok3 = test_3_empirical_connection_pool_limits()
    ok4 = test_4_pod_runtime_and_health_probes()
    ok5 = test_5_live_edge_verification_and_isolation()

    overall = ok1 and ok2 and ok3 and ok4 and ok5
    elapsed = round(time.time() - t_start, 2)

    verdict = "CONFIRM" if overall else "REJECT"
    test_results["overall_verdict"] = verdict
    test_results["elapsed_seconds"] = elapsed

    print("\n" + "=" * 75)
    print(f"FINAL CHALLENGER 2 VERDICT: {verdict} (Completed in {elapsed}s)")
    print("=" * 75)
    print(f"  1. Deploy Script Adversarial Inspection : {'✅ PASS' if ok1 else '❌ FAIL'}")
    print(f"  2. Multi-Tenant Schema Invariance       : {'✅ PASS' if ok2 else '❌ FAIL'}")
    print(f"  3. Connection Pool Limits (< 40 slots)  : {'✅ PASS' if ok3 else '❌ FAIL'}")
    print(f"  4. Pod Runtime & In-Pod Health Probes   : {'✅ PASS' if ok4 else '❌ FAIL'}")
    print(f"  5. Live Edge HTTPS & Tenant Isolation   : {'✅ PASS' if ok5 else '❌ FAIL'}")
    print("=" * 75)

    res_path = os.path.join(ROOT_DIR, "scripts", "challenger_ops_results.json")
    with open(res_path, "w", encoding="utf-8") as f:
        json.dump(test_results, f, indent=2)
    print(f"Saved full empirical test results to {res_path}")

    sys.exit(0 if overall else 1)


if __name__ == "__main__":
    main()
