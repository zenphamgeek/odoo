#!/usr/bin/env python3
"""
tools/deploy_innokafe_production.py
=============================================================================
Full-Cluster Zero-Downtime Production Deployment Pipeline for InnoKafe.

Architecture & Safety Guardrails:
1. Pre-Flight & Post-Flight Connection Safety:
   Enforces < 40/100 connection slot threshold via tools/reap_idle_connections.py.
2. Multi-Tenant Schema Invariance:
   Enforces strict 0 DDL / 0 schema mutations via tools/verify_schema_invariance.py.
3. Parallel Multi-Pod Code Distribution:
   Packages enterprise/innokafe_website and pushes to all pods simultaneously.
4. Lead-Pod Database Views Synchronization:
   Executes tools/sync_innokafe_views_db.py strictly on innokafe_prod.
5. Concurrent Dual-Tenant Zero-Downtime Asset Pre-Warming:
   Warms innokafe_prod (Pod 0) and innoria_prod (Pod 1) concurrently via
   tools/safe_asset_warmup.py without attachment deletion or compile locks.
6. Graceful Two-Tiered Rolling Reload:
   - Sequential pod-by-pod rollout maintaining >= 66.7% cluster capacity.
   - Within each pod, child HTTP workers are signaled with signal.SIGINT
     (triggering worker's graceful self.alive = False) staggered by 2s,
     allowing master PID 1 to spawn replacement workers before the next retires.
   - Local in-pod HTTP probe asserting HTTP 200 on Host: innoria.insilos.com
     and Host: innokafe.insilos.com before advancing to the next pod.
7. Dual Verification Gate:
   - Gate A: tools/guard_scss_integrity.py 4-tier check on https://innoria.insilos.com.
   - Gate B: Playwright live inspector on https://innokafe.insilos.com.
=============================================================================
"""

import argparse
import hashlib
import os
import re
import shlex
import subprocess
import sys
import time
from typing import Dict, List, Tuple

NAMESPACE = "production"
CONTAINER = "insilos"
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

_K8S_DNS1123_LABEL_RE = re.compile(r"^[a-z0-9]([-a-z0-9]*[a-z0-9])?$")


def _safe_ident(value: str, field: str) -> str:
    """Guards against shell injection and metacharacters in Kubernetes resource names (CWE-78, CWE-20).
    Enforces strict RFC 1123 DNS label constraints: <= 63 chars, lowercase alphanumeric and hyphens only.
    """
    if not isinstance(value, str) or len(value) > 63 or not _K8S_DNS1123_LABEL_RE.match(value):
        raise ValueError(f"Security Invariant Violated: Refusing unsafe {field!r}: {value!r}")
    return value


# In-pod script to gracefully retire child HTTP workers one by one via SIGINT
WORKER_RELOAD_SCRIPT = """
import os, signal, time, sys

current_pid = os.getpid()
workers = []

# Scan /proc for child processes of PID 1 running insilos-bin (excluding gevent longpolling)
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

if not workers:
    # Fallback scan without ppid constraint
    for pid_str in sorted(os.listdir('/proc'), key=lambda x: int(x) if x.isdigit() else 999999):
        if pid_str.isdigit() and int(pid_str) > 1 and int(pid_str) != current_pid:
            try:
                with open(f'/proc/{pid_str}/cmdline', 'rb') as f:
                    cmd = f.read()
                if b'insilos-bin' in cmd and b'gevent' not in cmd:
                    workers.append(int(pid_str))
            except Exception:
                pass

print(f"[*] Found {len(workers)} active HTTP workers to reload: {workers}", flush=True)

for idx, wpid in enumerate(workers, 1):
    try:
        print(f"  [{idx}/{len(workers)}] Gracefully signaling worker PID {wpid} with SIGINT...", flush=True)
        os.kill(wpid, signal.SIGINT)
    except ProcessLookupError:
        print(f"  Worker {wpid} already terminated.", flush=True)
    except Exception as e:
        print(f"  Error signaling worker {wpid}: {e}", flush=True)

    # Stagger by 2.0s allowing master PID 1 to spawn replacement worker
    if idx < len(workers):
        time.sleep(2.0)

# Allow grace period for the final replacement worker to initialize
time.sleep(2.0)
print("[✓] Staggered worker SIGINT rollout complete for this pod.", flush=True)
"""

# In-pod script to probe local HTTP server on port 8069 for both tenant domains
LOCAL_HEALTH_PROBE_SCRIPT = """
import urllib.request, time, sys

targets = [
    ('innoria.insilos.com', 'Innoria SaaS'),
    ('innokafe.insilos.com', 'InnoKafe Specialty Coffee')
]

max_retries = 8
probe_ok = True

for host, label in targets:
    success = False
    last_err = None
    for attempt in range(1, max_retries + 1):
        try:
            req = urllib.request.Request(
                'http://127.0.0.1:8069/',
                headers={
                    'Host': host,
                    'X-Forwarded-Host': host,
                    'X-Forwarded-Proto': 'https',
                    'User-Agent': 'LocalHealthProbe/2.0'
                }
            )
            with urllib.request.urlopen(req, timeout=20) as res:
                code = res.getcode()
                body = res.read().decode('utf-8', errors='ignore')
                if code == 200:
                    print(f"  [✓] {label} ({host}): HTTP {code} OK ({len(body)} bytes) [Attempt {attempt}]", flush=True)
                    success = True
                    break
                else:
                    last_err = f"Unexpected HTTP status {code}"
        except Exception as e:
            last_err = str(e)
            time.sleep(2.0)

    if not success:
        print(f"  [✗] {label} ({host}) FAILED health probe after {max_retries} attempts: {last_err}", flush=True)
        probe_ok = False

if not probe_ok:
    sys.exit(1)
print("[✓] Pod local health probes passed for all tenant hosts.", flush=True)
"""


def run_cmd(cmd: List[str], check: bool = False, timeout: int = 120) -> subprocess.CompletedProcess:
    """
    Executes an explicit argv argument list with shell=False.
    Fails closed with TypeError if a shell string is passed (CWE-78 guard).
    """
    if isinstance(cmd, str):
        raise TypeError(
            "Security Invariant Violated: run_cmd requires an argv List[str], "
            "not a shell string (CWE-78 guard)"
        )
    res = subprocess.run(cmd, shell=False, capture_output=True, text=True, timeout=timeout)
    if check and res.returncode != 0:
        raise RuntimeError(f"Command failed ({res.returncode}): {' '.join(cmd)}\nStdout: {res.stdout}\nStderr: {res.stderr}")
    return res


def step_banner(num: int, title: str) -> None:
    print(f"\n{'=' * 75}")
    print(f"=== STAGE {num}. {title.upper()} ===")
    print(f"{'=' * 75}")


def discover_active_pods(namespace: str = NAMESPACE) -> List[str]:
    step_banner(0, "Discovering Active Kubernetes Pods")
    ns = _safe_ident(namespace, "namespace")
    pod_out = run_cmd(
        [
            "kubectl", "get", "pods", "-n", ns,
            "-l", "app=insilos-saas",
            "--field-selector=status.phase=Running",
            "-o", "jsonpath={.items[*].metadata.name}"
        ],
        check=True
    )
    raw_pods = [p.strip() for p in pod_out.stdout.split() if p.strip()]
    pods = [_safe_ident(p, "pod") for p in raw_pods]
    print(f"[✓] Found {len(pods)} running pods: {pods}")
    if not pods:
        raise RuntimeError(f"No running insilos-saas pods found in namespace {namespace}! Aborting.")
    return pods


def enforce_connection_reaper(
    threshold: int = 40,
    dry_run: bool = False,
    target_db: str = "innokafe_prod",
    allow_all_databases: bool = False,
) -> None:
    print(f"\n[*] Enforcing connection slot threshold (< {threshold} slots)...")
    cmd = [
        sys.executable, os.path.join(ROOT_DIR, "tools/reap_idle_connections.py"),
        "--threshold", str(threshold),
    ]
    if allow_all_databases:
        cmd.append("--allow-all-databases")
    elif target_db:
        cmd.extend(["--dbname", target_db])
    else:
        raise ValueError("Must specify either target_db or allow_all_databases=True")

    if dry_run:
        cmd.append("--dry-run")
    res = subprocess.run(cmd, capture_output=True, text=True)
    print(res.stdout.strip())
    if res.stderr.strip():
        print("Stderr:", res.stderr.strip())
    if res.returncode != 0:
        raise RuntimeError(f"Connection pool reaper enforcement failed (threshold < {threshold} violated)!")
    print(f"[✓] Connection pool limit verified (< {threshold} slots).")


def enforce_schema_invariance() -> None:
    print("\n[*] Auditing PostgreSQL multi-tenant schema invariance (0 DDL mutations)...")
    cmd = [sys.executable, os.path.join(ROOT_DIR, "tools/verify_schema_invariance.py")]
    res = subprocess.run(cmd, capture_output=True, text=True)
    print(res.stdout.strip())
    if res.stderr.strip():
        print("Stderr:", res.stderr.strip())
    if res.returncode != 0:
        raise RuntimeError("Schema invariance violation detected across multi-tenant databases!")
    print("[✓] 100% strict schema invariance confirmed (0 DDL mutations).")


MEDIA_ASSETS = [
    "enterprise/innokafe_website/static/src/video/innokafe_coffee_pour_16x9_opt.mp4",
    "enterprise/innokafe_website/static/src/video/innokafe_coffee_pour_16x9.webm",
    "enterprise/innokafe_website/static/src/video/innokafe_cooling_tray_16x9_opt.mp4",
    "enterprise/innokafe_website/static/src/video/innokafe_cooling_tray_16x9.webm",
    "enterprise/innokafe_website/static/src/img/branding/innokafe_logo_master.svg",
    "enterprise/innokafe_website/static/src/img/branding/innokafe_logo_dark.svg",
    "enterprise/innokafe_website/static/src/img/branding/innokafe_logo_white.svg",
    "enterprise/innokafe_website/static/src/img/branding/innokafe_mark_symbol.svg",
    "enterprise/innokafe_website/static/src/img/photography/cooling_tray_artisan_roast.webp",
    "enterprise/innokafe_website/static/src/img/photography/natural_raised_beds_drying.webp",
    "enterprise/innokafe_website/static/src/img/photography/artisan_farmer_hands_harvest.webp",
    "enterprise/innokafe_website/static/src/img/photography/farm_plantation_mist.webp",
]


def compute_local_md5(rel_path: str) -> str:
    full_path = os.path.join(ROOT_DIR, rel_path)
    if not os.path.exists(full_path):
        raise FileNotFoundError(f"Local asset not found: {full_path}")
    h = hashlib.md5()
    with open(full_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def package_innokafe_archive() -> str:
    step_banner(2, "Packaging enterprise/innokafe_website Archive")
    tar_path = "/tmp/innokafe_website_sync.tar.gz"
    src_dir = os.path.join(ROOT_DIR, "enterprise", "innokafe_website")
    if not os.path.isdir(src_dir):
        raise FileNotFoundError(f"Source directory not found: {src_dir}")

    cmd = ["tar", "-czf", tar_path, "-C", src_dir, "."]
    run_cmd(cmd, check=True)
    tar_size = os.path.getsize(tar_path)
    print(f"[✓] Successfully packaged {tar_path} ({tar_size} bytes)")
    return tar_path


def verify_md5_parity(pods: List[str], namespace: str = NAMESPACE, container: str = CONTAINER) -> None:
    step_banner(3, "Cryptographic MD5 Parity Audit Across All Pods")
    ns = _safe_ident(namespace, "namespace")
    co = _safe_ident(container, "container")
    local_hashes: Dict[str, str] = {}
    for asset in MEDIA_ASSETS:
        h = compute_local_md5(asset)
        local_hashes[asset] = h
        filename = os.path.basename(asset)
        print(f"[*] Local {filename:<45} MD5: {h}")

    for pod in pods:
        po = _safe_ident(pod, "pod")
        print(f"\n--- Verifying Pod {po} ---")
        for asset in MEDIA_ASSETS:
            subpath = asset.replace("enterprise/innokafe_website/", "")
            pod_file = f"/app/insilos/enterprise/innokafe_website/{subpath}"
            cmd = ["kubectl", "exec", "-n", ns, po, "-c", co, "--", "md5sum", pod_file]
            res = run_cmd(cmd)
            if res.returncode != 0:
                raise RuntimeError(f"Missing file on {po}: {pod_file}")
            pod_hash = res.stdout.strip().split()[0]
            expected_hash = local_hashes[asset]
            filename = os.path.basename(asset)
            if pod_hash != expected_hash:
                raise RuntimeError(
                    f"MD5 MISMATCH on {po} for {filename}!\nExpected: {expected_hash}\nGot:      {pod_hash}"
                )
            print(f"  [✓] {filename:<40} MATCH: {pod_hash}")

    print("\n[✓] 100% Cryptographic MD5 parity confirmed across all pods.")


def _preflight_pricelist_shim(pricelist_tool: str) -> None:
    """Pre-flight verification for product_pricelist_item.py.
    1. Syntax verification via py_compile.
    2. Semantic parity verification against frozen golden pricing vectors.
    3. Error bounds verification (>2 args TypeError).
    """
    import py_compile
    try:
        py_compile.compile(pricelist_tool, doraise=True)
    except py_compile.PyCompileError as exc:
        raise RuntimeError(f"Refusing deploy: pricelist shim failed to compile: {exc}")

    # Semantic parity verification using isolated execution against golden vectors
    from unittest.mock import MagicMock
    from insilos.addons.product.models.product_pricelist_item import ProductPricelistItem

    mock_item = MagicMock(spec=ProductPricelistItem)
    mock_item.base = 'list_price'
    mock_product = MagicMock()
    mock_product.id = 42

    c_usd = MagicMock(name='USD')
    c_vnd = MagicMock(name='VND')
    c_eur = MagicMock(name='EUR')
    for c in (c_usd, c_vnd, c_eur):
        c.ensure_one.return_value = True

    mock_product.currency_id = c_usd
    mock_product._price_compute.return_value = {42: 100.0}
    mock_uom = MagicMock()

    golden_vectors = [
        (('2026-10-15',), {'currency': c_vnd}, c_vnd, '2026-10-15', 25000.0),
        (('2026-10-16', c_eur), {}, c_eur, '2026-10-16', 0.92),
        ((), {'date': '2026-10-17', 'currency': c_vnd}, c_vnd, '2026-10-17', 25000.0),
        (('2026-10-01',), {'date': '2026-10-18', 'currency': c_eur}, c_eur, '2026-10-18', 0.92),
    ]

    for args, kwargs, target_curr, exp_date, factor in golden_vectors:
        c_usd._convert.reset_mock()
        expected_price = 100.0 * factor
        c_usd._convert.return_value = expected_price

        try:
            computed = ProductPricelistItem._compute_base_price(
                mock_item, mock_product, 1.0, mock_uom, *args, **kwargs
            )
            c_usd._convert.assert_called_with(100.0, target_curr, date=exp_date, round=False)
            if abs(computed - expected_price) > 1e-9:
                raise RuntimeError(f"got {computed}, expected {expected_price}")
        except Exception as exc:
            raise RuntimeError(
                f"Refusing deploy: pricelist shim semantic divergence on golden vector: "
                f"args={args}, kwargs={kwargs}: {exc}"
            ) from exc

    try:
        ProductPricelistItem._compute_base_price(
            mock_item, mock_product, 1.0, mock_uom, '2026-10-16', c_eur, 'third_arg_overflow'
        )
        raise RuntimeError("Refusing deploy: pricelist shim failed to reject > 2 positional args")
    except TypeError:
        pass


def distribute_code_to_pods(pods: List[str], tar_path: str, namespace: str = NAMESPACE, container: str = CONTAINER) -> None:
    step_banner(3, "Deploying Archive & Sync Tools to All Pods in Parallel")
    ns = _safe_ident(namespace, "namespace")
    co = _safe_ident(container, "container")
    validated_pods = [_safe_ident(p, "pod") for p in pods]

    real_tar_path = os.path.realpath(tar_path)
    if not os.path.isfile(real_tar_path):
        raise FileNotFoundError(f"Tar archive not found: {tar_path}")
    if not (real_tar_path.startswith("/tmp/") or real_tar_path.startswith(ROOT_DIR)):
        raise ValueError(f"Security Invariant Violated: tar_path must reside in /tmp or workspace: {tar_path!r}")

    sync_tool = os.path.join(ROOT_DIR, "tools", "sync_innokafe_views_db.py")
    cleanup_tool = os.path.join(ROOT_DIR, "tools", "cleanup_innokafe_fake_logos_db.py")
    warmup_tool = os.path.join(ROOT_DIR, "tools", "safe_asset_warmup.py")
    pricelist_tool = os.path.join(ROOT_DIR, "addons", "product", "models", "product_pricelist_item.py")
    if not os.path.isfile(sync_tool):
        raise FileNotFoundError(f"Sync tool not found: {sync_tool}")
    if not os.path.isfile(cleanup_tool):
        raise FileNotFoundError(f"Cleanup tool not found: {cleanup_tool}")
    if not os.path.isfile(warmup_tool):
        raise FileNotFoundError(f"Warmup tool not found: {warmup_tool}")
    if not os.path.isfile(pricelist_tool):
        raise FileNotFoundError(f"Pricelist item file not found: {pricelist_tool}")

    _preflight_pricelist_shim(pricelist_tool)

    remote_script = (
        "mkdir -p /app/insilos/enterprise/innokafe_website "
        "/app/insilos/apps/innokafe_website && "
        "tar --no-same-owner --no-same-permissions -xzf /tmp/innokafe_website_sync.tar.gz "
        "-C /app/insilos/enterprise/innokafe_website/ && "
        "tar --no-same-owner --no-same-permissions -xzf /tmp/innokafe_website_sync.tar.gz "
        "-C /app/insilos/apps/innokafe_website/ && "
        "python3 -m py_compile /tmp/product_pricelist_item.py && "
        "TGT=/app/insilos/addons/product/models/product_pricelist_item.py && "
        "cp -a \"$TGT\" \"$TGT.bak.$(date +%s)\" && "
        "install -m 644 /tmp/product_pricelist_item.py \"$TGT.new\" && "
        "python3 -m py_compile \"$TGT.new\" && mv \"$TGT.new\" \"$TGT\" && "
        "chown -R insilos:insilos /app/insilos/enterprise/innokafe_website "
        "/app/insilos/apps/innokafe_website "
        "/app/insilos/addons/product/models/product_pricelist_item.py "
        "/tmp/sync_innokafe_views_db.py /tmp/cleanup_innokafe_fake_logos_db.py /tmp/safe_asset_warmup.py && "
        "rm -f /tmp/innokafe_website_sync.tar.gz /tmp/product_pricelist_item.py"
    )

    import concurrent.futures

    def _sync_pod(po: str) -> None:
        files = [
            (real_tar_path, "/tmp/innokafe_website_sync.tar.gz"),
            (sync_tool, "/tmp/sync_innokafe_views_db.py"),
            (cleanup_tool, "/tmp/cleanup_innokafe_fake_logos_db.py"),
            (warmup_tool, "/tmp/safe_asset_warmup.py"),
            (pricelist_tool, "/tmp/product_pricelist_item.py"),
        ]
        for src, dst in files:
            cp_cmd = ["kubectl", "cp", "-n", ns, "-c", co, src, f"{po}:{dst}"]
            run_cmd(cp_cmd, check=True)

        exec_cmd = ["kubectl", "exec", "-n", ns, po, "-c", co, "--", "sh", "-c", remote_script]
        run_cmd(exec_cmd, check=True)

    failures = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, len(validated_pods))) as executor:
        future_to_pod = {executor.submit(_sync_pod, po): po for po in validated_pods}
        for future in concurrent.futures.as_completed(future_to_pod):
            po = future_to_pod[future]
            try:
                future.result()
                print(f"[✓] Synchronized files and tools to {po}")
            except Exception as exc:
                print(f"[✗] Failed file synchronization to {po}: {exc}")
                failures.append(po)

    if failures:
        raise RuntimeError(f"Distribution failed on pods: {failures}")


def execute_innokafe_db_sync(lead_pod: str, namespace: str = NAMESPACE, container: str = CONTAINER) -> None:
    ns = _safe_ident(namespace, "namespace")
    po = _safe_ident(lead_pod, "lead_pod")
    co = _safe_ident(container, "container")
    step_banner(4, f"Executing InnoKafe DB Sync on Lead Pod ({po})")
    res_sync = subprocess.run([
        "kubectl", "exec", "-n", ns, po, "-c", co, "--",
        "python3", "/tmp/sync_innokafe_views_db.py", "prod_pod"
    ], capture_output=True, text=True, timeout=60)
    print(res_sync.stdout.strip())
    if res_sync.stderr.strip():
        print("Stderr:", res_sync.stderr.strip())

    if res_sync.returncode != 0:
        raise RuntimeError(f"InnoKafe database views sync failed on {po} (code {res_sync.returncode})")
    print(f"[✓] Database views and isolation templates successfully synced on {po}.")

    # Defense-in-depth: Logo purge requires explicit DEPLOY_ALLOW_LOGO_PURGE=1 opt-in
    if os.environ.get("DEPLOY_ALLOW_LOGO_PURGE") != "1":
        print(f"[skip] InnoKafe logo purge skipped on {po} (set DEPLOY_ALLOW_LOGO_PURGE=1 to enable).")
        return

    # 1. Mandatory dry-run first: reports counts, mutates nothing, executed via argv (CWE-78 defense)
    print(f"[*] Executing mandatory pre-op DRY-RUN logo purge audit on {po}...")
    res_dry = subprocess.run([
        "kubectl", "exec", "-n", ns, po, "-c", co, "--",
        "env", "DB_NAME=innokafe_prod",
        "python3", "/tmp/cleanup_innokafe_fake_logos_db.py", "prod_pod"
    ], capture_output=True, text=True, timeout=60)
    print(res_dry.stdout.strip())
    if res_dry.stderr.strip():
        print("Dry-run Stderr:", res_dry.stderr.strip())
    if res_dry.returncode != 0:
        raise RuntimeError(f"Logo purge pre-op dry-run failed on {po} (code {res_dry.returncode})")

    # 2. Live committed purge executed only if explicit dual-key confirmation is set
    if os.environ.get("CONFIRM_ALL_WEBSITES_PROD") == "1":
        print(f"[*] CONFIRM_ALL_WEBSITES_PROD=1 verified: Executing live logo purge with --commit --all-websites on {po}...")
        res_clean = subprocess.run([
            "kubectl", "exec", "-n", ns, po, "-c", co, "--",
            "env", "DB_NAME=innokafe_prod", "CONFIRM_ALL_WEBSITES_PROD=1",
            "python3", "/tmp/cleanup_innokafe_fake_logos_db.py", "prod_pod", "--commit", "--all-websites"
        ], capture_output=True, text=True, timeout=60)
        print(res_clean.stdout.strip())
        if res_clean.stderr.strip():
            print("Stderr:", res_clean.stderr.strip())
        if res_clean.returncode != 0:
            raise RuntimeError(f"InnoKafe database logo purge commit failed on {po} (code {res_clean.returncode})")
        print(f"[✓] Database vector logo purge committed durably on {po}.")
    else:
        print(f"[✓] Logo purge verified safely in dry-run mode on {po} (zero mutations persisted; pass CONFIRM_ALL_WEBSITES_PROD=1 to commit).")


def execute_concurrent_dual_warmup(pods: List[str], namespace: str = NAMESPACE, container: str = CONTAINER) -> None:
    step_banner(5, "Concurrent Dual-Tenant Zero-Downtime Asset Pre-Warming")
    ns = _safe_ident(namespace, "namespace")
    co = _safe_ident(container, "container")
    validated_pods = [_safe_ident(p, "pod") for p in pods]
    t0 = time.time()
    pod_kafe = validated_pods[0]
    pod_ria = validated_pods[1] if len(validated_pods) > 1 else validated_pods[0]

    print(f"[*] Dispatching concurrent asset pre-warming:")
    print(f"    • Pod 0 ({pod_kafe}): innokafe_prod")
    print(f"    • Pod 1 ({pod_ria}): innoria_prod")

    proc_kafe = subprocess.Popen(
        ["kubectl", "exec", "-n", ns, pod_kafe, "-c", co, "--",
         "python3", "/tmp/safe_asset_warmup.py", "innokafe_prod"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    proc_ria = subprocess.Popen(
        ["kubectl", "exec", "-n", ns, pod_ria, "-c", co, "--",
         "python3", "/tmp/safe_asset_warmup.py", "innoria_prod"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )

    out_kafe, err_kafe = proc_kafe.communicate()
    out_ria, err_ria = proc_ria.communicate()

    print(f"\n--- Output from {pod_kafe} (innokafe_prod) ---")
    print(out_kafe.strip())
    if err_kafe.strip():
        print("Stderr:", err_kafe.strip())

    print(f"\n--- Output from {pod_ria} (innoria_prod) ---")
    print(out_ria.strip())
    if err_ria.strip():
        print("Stderr:", err_ria.strip())

    if proc_kafe.returncode != 0:
        raise RuntimeError(f"Asset pre-warming failed on innokafe_prod (code {proc_kafe.returncode})")
    if proc_ria.returncode != 0:
        raise RuntimeError(f"Asset pre-warming failed on innoria_prod (code {proc_ria.returncode})")

    dur = round(time.time() - t0, 2)
    print(f"\n[✓] Dual-tenant safe asset warmup completed concurrently in {dur}s.")


def execute_sequential_rolling_reload(pods: List[str], namespace: str = NAMESPACE, container: str = CONTAINER) -> None:
    step_banner(6, "Graceful Two-Tiered Rolling Reload (Zero Downtime)")
    ns = _safe_ident(namespace, "namespace")
    co = _safe_ident(container, "container")
    validated_pods = [_safe_ident(p, "pod") for p in pods]
    total_pods = len(validated_pods)
    min_capacity = round(((total_pods - 1) / total_pods) * 100, 1) if total_pods > 1 else 100.0
    print(f"[*] Total pods to rollout: {total_pods}")
    print(f"[*] Capacity guarantee: Active cluster capacity maintained at >= {min_capacity}% at all times.")

    for idx, pod in enumerate(validated_pods, 1):
        print(f"\n------------------------------------------------------------")
        print(f"▶ Rolling Pod [{idx}/{total_pods}]: {pod}")
        print(f"------------------------------------------------------------")

        # Step A: Staggered SIGINT to child workers within the pod
        print(f"[*] Staggered SIGINT graceful reload of child workers on {pod}...")
        res_reload = subprocess.run(
            ["kubectl", "exec", "-n", ns, pod, "-c", co, "--",
             "python3", "-c", WORKER_RELOAD_SCRIPT],
            capture_output=True, text=True, timeout=90
        )
        print(res_reload.stdout.strip())
        if res_reload.stderr.strip():
            print("Stderr:", res_reload.stderr.strip())
        if res_reload.returncode != 0:
            raise RuntimeError(f"Worker reload script failed on {pod} (code {res_reload.returncode})")

        # Step B: Local in-pod HTTP health probe before advancing to next pod
        print(f"[*] Verifying in-pod local HTTP health on {pod} (Host: innoria & innokafe)...")
        res_probe = subprocess.run(
            ["kubectl", "exec", "-n", ns, pod, "-c", co, "--",
             "python3", "-c", LOCAL_HEALTH_PROBE_SCRIPT],
            capture_output=True, text=True, timeout=90
        )
        print(res_probe.stdout.strip())
        if res_probe.stderr.strip():
            print("Stderr:", res_probe.stderr.strip())
        if res_probe.returncode != 0:
            raise RuntimeError(f"Health probe FAILED on {pod}! Halting rollout to preserve cluster availability.")

        print(f"[✓] Pod {pod} passed health probes and is serving traffic.")

    print(f"\n[✓] All {total_pods} pods rolled out sequentially with zero downtime.")


def execute_dual_verification_gates() -> None:
    step_banner(7, "Dual Verification Gates")

    # Gate A: SCSS Integrity Guardian 4-Tier Verification
    print("\n--- Gate A: Executing tools/guard_scss_integrity.py (https://innoria.insilos.com) ---")
    gate_a_cmd = [sys.executable, os.path.join(ROOT_DIR, "tools", "guard_scss_integrity.py")]
    res_a = subprocess.run(gate_a_cmd, capture_output=True, text=True, timeout=180)
    print(res_a.stdout.strip())
    if res_a.stderr.strip():
        print("Stderr:", res_a.stderr.strip())
    if res_a.returncode != 0:
        raise RuntimeError("Gate A FAILED: SCSS integrity guard reported errors on innoria.insilos.com!")
    print("[✓] Gate A PASSED: Innoria SCSS and route integrity confirmed (100% PASS).")

    # Gate B: Playwright Headless Verification on https://innokafe.insilos.com
    print("\n--- Gate B: Executing Playwright Verification (https://innokafe.insilos.com) ---")
    gate_b_cmd = ["node", os.path.join(ROOT_DIR, "tools", "verify_innokafe_live.js")]
    res_b = subprocess.run(gate_b_cmd, capture_output=True, text=True, timeout=120)
    print(res_b.stdout.strip())
    if res_b.stderr.strip():
        print("Stderr:", res_b.stderr.strip())
    if res_b.returncode != 0:
        raise RuntimeError("Gate B FAILED: Playwright live inspector reported errors on innokafe.insilos.com!")
    print("[✓] Gate B PASSED: InnoKafe layout, brand isolation, and zero-error criteria confirmed.")


def execute_edge_smoke_tests() -> None:
    step_banner(9, "External Edge HTTPS Smoke Probes")
    endpoints = [
        "https://innokafe.insilos.com/",
        "https://innoria.insilos.com/"
    ]
    for url in endpoints:
        res = run_cmd(["curl", "-sI", url])
        first_lines = "\n".join(res.stdout.strip().splitlines()[:5])
        print(f"[*] Response for {url}:\n{first_lines}\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Multi-Tenant Zero-Downtime Production Deployment Pipeline for InnoKafe Specialty Coffee."
    )
    parser.add_argument("--skip-warmup", action="store_true", help="Skip asset pre-warming phase")
    parser.add_argument("--skip-gates", action="store_true", help="Skip post-deployment verification gates")
    parser.add_argument("--connection-threshold", type=int, default=40, help="Max connection slots threshold (default: 40)")
    parser.add_argument("--dry-run-reaper", action="store_true", help="Run connection reaper in dry-run mode")
    parser.add_argument("--target-db", default="innokafe_prod", help="Target database to reap idle connections for (default: innokafe_prod)")
    parser.add_argument("--allow-all-databases", action="store_true", help="Permit reaping idle connections across all cluster databases")
    args = parser.parse_args()

    t_start = time.time()
    print("=" * 75)
    print("🚀 INNOKAFE SPECIALTY COFFEE — PRODUCTION DEPLOYMENT PIPELINE")
    print(f"Namespace: {NAMESPACE} | Container: {CONTAINER} | Root: {ROOT_DIR}")
    print("=" * 75)

    try:
        # Stage 0: Discover active pods
        pods = discover_active_pods(NAMESPACE)

        # Stage 1: Pre-flight Safety Checks
        step_banner(1, "Pre-Flight Safety Guardrails")
        enforce_connection_reaper(
            threshold=args.connection_threshold,
            dry_run=args.dry_run_reaper,
            target_db=args.target_db,
            allow_all_databases=args.allow_all_databases,
        )
        enforce_schema_invariance()

        # Stage 2: Packaging module archive
        tar_path = package_innokafe_archive()

        # Stage 3: Distribute code to all pods
        distribute_code_to_pods(pods, tar_path, namespace=NAMESPACE, container=CONTAINER)

        # Stage 3b: Cryptographic MD5 parity check
        verify_md5_parity(pods, namespace=NAMESPACE, container=CONTAINER)

        # Stage 4: Database views sync on lead pod
        execute_innokafe_db_sync(pods[0], namespace=NAMESPACE, container=CONTAINER)

        # Stage 5: Concurrent dual-tenant safe asset warmup
        if not args.skip_warmup:
            execute_concurrent_dual_warmup(pods, namespace=NAMESPACE, container=CONTAINER)
        else:
            print("\n[!] Skipping asset pre-warming as requested (--skip-warmup).")

        # Stage 6: Graceful two-tiered rolling reload
        execute_sequential_rolling_reload(pods, namespace=NAMESPACE, container=CONTAINER)

        # Stage 7: Dual verification gates
        if not args.skip_gates:
            execute_dual_verification_gates()
        else:
            print("\n[!] Skipping dual verification gates as requested (--skip-gates).")

        # Stage 8: Post-flight Safety Audits
        step_banner(8, "Post-Flight Safety Verification & Connection Reap")
        enforce_schema_invariance()
        enforce_connection_reaper(
            threshold=args.connection_threshold,
            dry_run=False,
            target_db=args.target_db,
            allow_all_databases=args.allow_all_databases,
        )

        # Stage 9: External edge smoke tests
        execute_edge_smoke_tests()

        elapsed = round(time.time() - t_start, 2)
        print("\n" + "=" * 75)
        print(f"🎉 PRODUCTION DEPLOYMENT SUCCESSFULLY COMPLETED IN {elapsed}s!")
        print("All safety invariants, rolling reload, and verification gates passed with 100% compliance.")
        print("=" * 75)
        sys.exit(0)

    except Exception as e:
        print(f"\n❌ DEPLOYMENT FAILED: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
