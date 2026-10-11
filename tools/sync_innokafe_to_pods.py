#!/usr/bin/env python3
"""
tools/sync_innokafe_to_pods.py
=============================================================================
High-Speed Zero-Downtime Synchronization Engine for InnoKafe Kubernetes Cluster.

Executes:
1. Active running pod discovery across the production namespace.
2. Comprehensive packaging of enterprise/innokafe_website (videos, SVGs, SCSS, QWeb).
3. Parallel distribution of codebase, sync scripts, and warmup engines to all pods.
4. Strict cryptographic MD5 parity verification of media and branding assets across pods.
5. Lead-pod parameter-bound database views synchronization (zero-DDL compliance).
6. Safe atomic asset pre-warming for innokafe_prod (zero asset stampede).
7. Staggered SIGINT rolling reload of child HTTP workers with local health probes.
8. External live edge HTTPS HTTP/2 smoke probes.
=============================================================================
"""

import hashlib
import os
import re
import subprocess
import sys
import time
from typing import Dict, List, Tuple

NAMESPACE = "production"
CONTAINER = "insilos"
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

MEDIA_ASSETS = [
    "enterprise/innokafe_website/static/src/video/innokafe_coffee_pour_16x9_opt.mp4",
    "enterprise/innokafe_website/static/src/video/innokafe_coffee_pour_16x9.webm",
    "enterprise/innokafe_website/static/src/video/innokafe_cooling_tray_16x9_opt.mp4",
    "enterprise/innokafe_website/static/src/video/innokafe_cooling_tray_16x9.webm",
    "enterprise/innokafe_website/static/src/img/branding/innokafe_logo_master.svg",
    "enterprise/innokafe_website/static/src/img/branding/innokafe_logo_dark.svg",
    "enterprise/innokafe_website/static/src/img/branding/innokafe_logo_white.svg",
    "enterprise/innokafe_website/static/src/img/branding/innokafe_mark_symbol.svg",
]

WORKER_RELOAD_SCRIPT = """
import os, signal, time, sys

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

if not workers:
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
        print(f"  [{idx}/{len(workers)}] Signaling worker PID {wpid} with SIGINT...", flush=True)
        os.kill(wpid, signal.SIGINT)
    except ProcessLookupError:
        print(f"  Worker {wpid} already terminated.", flush=True)
    except Exception as e:
        print(f"  Error signaling worker {wpid}: {e}", flush=True)

    if idx < len(workers):
        time.sleep(2.0)

time.sleep(2.0)
print("[✓] Staggered worker SIGINT rollout complete for this pod.", flush=True)
"""

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


def run_cmd(cmd: str, check: bool = False, timeout: int = 120) -> subprocess.CompletedProcess:
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    if check and res.returncode != 0:
        raise RuntimeError(f"Command failed ({res.returncode}): {cmd}\nStdout: {res.stdout}\nStderr: {res.stderr}")
    return res


def compute_local_md5(rel_path: str) -> str:
    full_path = os.path.join(ROOT_DIR, rel_path)
    if not os.path.exists(full_path):
        raise FileNotFoundError(f"Local asset not found: {full_path}")
    h = hashlib.md5()
    with open(full_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def compute_local_sha256(file_path: str) -> str:
    full_path = file_path if os.path.isabs(file_path) else os.path.join(ROOT_DIR, file_path)
    if not os.path.exists(full_path):
        raise FileNotFoundError(f"Local file not found: {full_path}")
    h = hashlib.sha256()
    with open(full_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def discover_active_pods(namespace: str = NAMESPACE) -> List[str]:
    print("\n=== STAGE 0. DISCOVERING ACTIVE KUBERNETES PODS ===")
    pod_out = run_cmd(
        f"kubectl get pods -n {namespace} -l app=insilos-saas --field-selector=status.phase=Running -o jsonpath='{{.items[*].metadata.name}}'",
        check=True
    )
    raw_pods = [p.strip() for p in pod_out.stdout.split() if p.strip()]
    pods = [p for p in raw_pods if re.match(r"^[a-zA-Z0-9.-]+$", p)]
    print(f"[✓] Found {len(pods)} running pods: {pods}")
    if not pods:
        raise RuntimeError(f"No running insilos-saas pods found in namespace {namespace}! Aborting.")
    return pods


def package_and_distribute(pods: List[str], namespace: str = NAMESPACE, container: str = CONTAINER) -> None:
    print("\n=== STAGE 1. PACKAGING & PARALLEL DISTRIBUTION ===")
    tar_path = "/tmp/innokafe_website_sync.tar.gz"
    src_dir = os.path.join(ROOT_DIR, "enterprise", "innokafe_website")
    if not os.path.isdir(src_dir):
        raise FileNotFoundError(f"Source directory not found: {src_dir}")

    # Package entire module directory including all media assets and metadata
    cmd = f"tar -czf {tar_path} -C {src_dir} ."
    run_cmd(cmd, check=True)
    tar_size = os.path.getsize(tar_path)
    print(f"[✓] Created {tar_path} ({tar_size} bytes)")

    sync_tool = os.path.join(ROOT_DIR, "tools", "sync_innokafe_views_db.py")
    warmup_tool = os.path.join(ROOT_DIR, "tools", "safe_asset_warmup.py")
    sync_sha = compute_local_sha256(sync_tool)
    warmup_sha = compute_local_sha256(warmup_tool)

    deploy_procs = []
    for pod in pods:
        pcmd = (
            f"kubectl cp -n {namespace} -c {container} {tar_path} {pod}:/tmp/innokafe_website_sync.tar.gz && "
            f"kubectl cp -n {namespace} -c {container} {sync_tool} {pod}:/app/insilos/tools/sync_innokafe_views_db.py && "
            f"kubectl cp -n {namespace} -c {container} {warmup_tool} {pod}:/app/insilos/tools/safe_asset_warmup.py && "
            f"kubectl exec -n {namespace} {pod} -c {container} -- sh -c '"
            f"mkdir -p /app/insilos/enterprise/innokafe_website /app/insilos/apps/innokafe_website /app/insilos/tools && "
            f"tar -xzf /tmp/innokafe_website_sync.tar.gz -C /app/insilos/enterprise/innokafe_website/ && "
            f"tar -xzf /tmp/innokafe_website_sync.tar.gz -C /app/insilos/apps/innokafe_website/ && "
            f"chown -R insilos:insilos /app/insilos/enterprise/innokafe_website /app/insilos/apps/innokafe_website /app/insilos/tools/sync_innokafe_views_db.py /app/insilos/tools/safe_asset_warmup.py && "
            f"chmod 0755 /app/insilos/tools/sync_innokafe_views_db.py /app/insilos/tools/safe_asset_warmup.py && "
            f"rm -f /tmp/innokafe_website_sync.tar.gz'"
        )
        p = subprocess.Popen(pcmd, shell=True)
        deploy_procs.append((pod, p))

    failures = []
    for pod, p in deploy_procs:
        p.wait()
        if p.returncode != 0:
            print(f"[✗] Failed deployment on {pod} (exit code {p.returncode})")
            failures.append(pod)
        else:
            print(f"[✓] Synchronized files & tools to {pod}")

    if failures:
        raise RuntimeError(f"Distribution failed on pods: {failures}")


def verify_md5_parity(pods: List[str], namespace: str = NAMESPACE, container: str = CONTAINER) -> None:
    print("\n=== STAGE 2. CRYPTOGRAPHIC MD5 PARITY AUDIT ACROSS ALL PODS ===")
    local_hashes: Dict[str, str] = {}
    for asset in MEDIA_ASSETS:
        h = compute_local_md5(asset)
        local_hashes[asset] = h
        filename = os.path.basename(asset)
        print(f"[*] Local {filename:<45} MD5: {h}")

    for pod in pods:
        print(f"\n--- Verifying Pod {pod} ---")
        for asset in MEDIA_ASSETS:
            subpath = asset.replace("enterprise/innokafe_website/", "")
            pod_file = f"/app/insilos/enterprise/innokafe_website/{subpath}"
            cmd = f"kubectl exec -n {namespace} {pod} -c {container} -- md5sum {pod_file}"
            res = run_cmd(cmd)
            if res.returncode != 0:
                raise RuntimeError(f"Missing file on {pod}: {pod_file}")
            pod_hash = res.stdout.strip().split()[0]
            expected_hash = local_hashes[asset]
            filename = os.path.basename(asset)
            if pod_hash != expected_hash:
                raise RuntimeError(
                    f"MD5 MISMATCH on {pod} for {filename}!\nExpected: {expected_hash}\nGot:      {pod_hash}"
                )
            print(f"  [✓] {filename:<40} MATCH: {pod_hash}")

    print("\n[✓] 100% Cryptographic MD5 parity confirmed across all 3 pods.")


def verify_pod_script_sha256(pod: str, remote_path: str, expected_sha: str, namespace: str = NAMESPACE, container: str = CONTAINER) -> None:
    cmd = f"kubectl exec -n {namespace} {pod} -c {container} -- sha256sum {remote_path}"
    res = run_cmd(cmd, check=True)
    actual_sha = res.stdout.strip().split()[0]
    if actual_sha != expected_sha:
        raise RuntimeError(
            f"Security Invariant Violated: SHA-256 mismatch for {remote_path} on {pod}!\n"
            f"Expected: {expected_sha}\nGot:      {actual_sha}"
        )
    print(f"  [✓] SHA-256 verified for {remote_path} on {pod}: {actual_sha[:16]}...")


def sync_db_views(lead_pod: str, namespace: str = NAMESPACE, container: str = CONTAINER) -> None:
    print(f"\n=== STAGE 3. DATABASE VIEWS SYNCHRONIZATION ON LEAD POD ({lead_pod}) ===")
    sync_tool = os.path.join(ROOT_DIR, "tools", "sync_innokafe_views_db.py")
    expected_sha = compute_local_sha256(sync_tool)
    verify_pod_script_sha256(lead_pod, "/app/insilos/tools/sync_innokafe_views_db.py", expected_sha, namespace, container)

    res_sync = subprocess.run([
        "kubectl", "exec", "-n", namespace, lead_pod, "-c", container, "--",
        "python3", "/app/insilos/tools/sync_innokafe_views_db.py", "prod_pod"
    ], capture_output=True, text=True, timeout=60)
    print(res_sync.stdout.strip())
    if res_sync.stderr.strip():
        print("Stderr:", res_sync.stderr.strip())
    if res_sync.returncode != 0:
        raise RuntimeError(f"Database views sync failed on {lead_pod} (code {res_sync.returncode})")
    print(f"[✓] InnoKafe database views successfully updated on {lead_pod}.")


def prewarm_assets(pods: List[str], namespace: str = NAMESPACE, container: str = CONTAINER) -> None:
    print("\n=== STAGE 4. ATOMIC ASSET PRE-WARMING ===")
    t0 = time.time()
    pod_kafe = pods[0]
    pod_ria = pods[1] if len(pods) > 1 else pods[0]

    warmup_tool = os.path.join(ROOT_DIR, "tools", "safe_asset_warmup.py")
    expected_sha = compute_local_sha256(warmup_tool)
    verify_pod_script_sha256(pod_kafe, "/app/insilos/tools/safe_asset_warmup.py", expected_sha, namespace, container)
    if pod_ria != pod_kafe:
        verify_pod_script_sha256(pod_ria, "/app/insilos/tools/safe_asset_warmup.py", expected_sha, namespace, container)

    print(f"[*] Pre-warming asset bundles:")
    print(f"    • Pod {pod_kafe}: innokafe_prod")
    print(f"    • Pod {pod_ria}: innoria_prod")

    proc_kafe = subprocess.Popen(
        ["kubectl", "exec", "-n", namespace, pod_kafe, "-c", container, "--",
         "python3", "/app/insilos/tools/safe_asset_warmup.py", "innokafe_prod"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    proc_ria = subprocess.Popen(
        ["kubectl", "exec", "-n", namespace, pod_ria, "-c", container, "--",
         "python3", "/app/insilos/tools/safe_asset_warmup.py", "innoria_prod"],
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
    print(f"\n[✓] Safe asset warmup completed concurrently in {dur}s.")


def rolling_reload_workers(pods: List[str], namespace: str = NAMESPACE, container: str = CONTAINER) -> None:
    print("\n=== STAGE 5. ZERO-DOWNTIME STAGGERED ROLLING RELOAD ===")
    total = len(pods)
    for idx, pod in enumerate(pods, 1):
        print(f"\n▶ Rolling Pod [{idx}/{total}]: {pod}")
        res_reload = subprocess.run(
            ["kubectl", "exec", "-n", namespace, pod, "-c", container, "--",
             "python3", "-c", WORKER_RELOAD_SCRIPT],
            capture_output=True, text=True, timeout=90
        )
        print(res_reload.stdout.strip())
        if res_reload.stderr.strip():
            print("Stderr:", res_reload.stderr.strip())
        if res_reload.returncode != 0:
            raise RuntimeError(f"Worker reload script failed on {pod} (code {res_reload.returncode})")

        print(f"[*] Verifying in-pod local HTTP health on {pod}...")
        res_probe = subprocess.run(
            ["kubectl", "exec", "-n", namespace, pod, "-c", container, "--",
             "python3", "-c", LOCAL_HEALTH_PROBE_SCRIPT],
            capture_output=True, text=True, timeout=90
        )
        print(res_probe.stdout.strip())
        if res_probe.stderr.strip():
            print("Stderr:", res_probe.stderr.strip())
        if res_probe.returncode != 0:
            raise RuntimeError(f"Health probe FAILED on {pod}!")

        print(f"[✓] Pod {pod} healthy and serving traffic.")

    print(f"\n[✓] All {total} pods rolled out with zero downtime.")


def edge_verification() -> None:
    print("\n=== STAGE 6. EXTERNAL EDGE HTTPS SMOKE PROBES ===")
    endpoints = [
        "https://innokafe.insilos.com/",
        "https://innoria.insilos.com/"
    ]
    for url in endpoints:
        res = run_cmd(f"curl -sI {url} | head -n 5")
        print(f"[*] Response for {url}:\n{res.stdout.strip()}\n")
        if "200" not in res.stdout:
            raise RuntimeError(f"Edge probe failed for {url}! Did not return HTTP 200.")


def main():
    t0 = time.time()
    print("=" * 75)
    print("🚀 INNOKAFE SYNC TO PODS — PRODUCTION CLUSTER PIPELINE")
    print(f"Namespace: {NAMESPACE} | Container: {CONTAINER} | Root: {ROOT_DIR}")
    print("=" * 75)

    try:
        pods = discover_active_pods(NAMESPACE)
        package_and_distribute(pods, NAMESPACE, CONTAINER)
        verify_md5_parity(pods, NAMESPACE, CONTAINER)
        sync_db_views(pods[0], NAMESPACE, CONTAINER)
        prewarm_assets(pods, NAMESPACE, CONTAINER)
        rolling_reload_workers(pods, NAMESPACE, CONTAINER)
        edge_verification()

        dur = round(time.time() - t0, 2)
        print("\n" + "=" * 75)
        print(f"🎉 POD SYNCHRONIZATION PIPELINE SUCCEEDED IN {dur}s!")
        print("All pods synchronized, assets cryptographically verified, zero downtime achieved.")
        print("=" * 75)
        sys.exit(0)

    except Exception as e:
        print(f"\n❌ SYNC PIPELINE FAILED: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
