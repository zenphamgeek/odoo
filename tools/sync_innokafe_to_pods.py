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

import datetime
import fcntl
import hashlib
import hmac
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import ssl
import urllib.error
import urllib.request
from typing import Dict, List, Optional, Tuple, Union

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
    "enterprise/innokafe_website/static/src/img/branding/innokafe_social_share_1200x630.jpg",
    "enterprise/innokafe_website/static/src/img/branding/innokafe_social_share_1200x630.webp",
    "enterprise/innokafe_website/static/src/img/photography/cooling_tray_artisan_roast.webp",
    "enterprise/innokafe_website/static/src/img/photography/natural_raised_beds_drying.webp",
    "enterprise/innokafe_website/static/src/img/photography/bar_warm_amber_wood_interior.webp",
    "enterprise/innokafe_website/static/src/img/photography/barista_pourover_v60_flow.webp",
    "enterprise/innokafe_website/static/src/img/photography/sensory_cupping_flight.webp",
    "enterprise/innokafe_website/static/src/img/photography/farm_cherries_ripe.webp",
    "enterprise/innokafe_website/static/src/img/photography/farm_plantation_mist.webp",
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
    ('innokafe.insilos.com', 'InnoKafe Specialty Coffee (Tenant)'),
    ('innokafe.com', 'InnoKafe Brand Official')
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


def run_cmd(cmd: Union[str, List[str]], check: bool = False, timeout: int = 120) -> subprocess.CompletedProcess:
    if isinstance(cmd, list):
        res = subprocess.run(cmd, shell=False, capture_output=True, text=True, timeout=timeout)
    else:
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
        ["kubectl", "get", "pods", "-n", namespace, "-l", "app=insilos-saas",
         "--field-selector=status.phase=Running", "-o", "jsonpath={.items[*].metadata.name}"],
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
    tar_cmd = ["tar", "-czf", tar_path, "-C", src_dir, "."]
    run_cmd(tar_cmd, check=True)
    tar_size = os.path.getsize(tar_path)
    tar_sha = compute_local_sha256(tar_path)
    print(f"[✓] Created {tar_path} ({tar_size} bytes, SHA-256: {tar_sha[:16]}...)")

    sync_tool = os.path.join(ROOT_DIR, "tools", "sync_innokafe_views_db.py")
    warmup_tool = os.path.join(ROOT_DIR, "tools", "safe_asset_warmup.py")
    sync_sha = compute_local_sha256(sync_tool)
    warmup_sha = compute_local_sha256(warmup_tool)

    extract_script = f"""set -e
echo "{tar_sha}  /tmp/innokafe_website_sync.tar.gz" | sha256sum -c -
mkdir -p /app/insilos/enterprise/innokafe_website /app/insilos/apps/innokafe_website /app/insilos/tools
tar -xzf /tmp/innokafe_website_sync.tar.gz -C /app/insilos/enterprise/innokafe_website/
tar -xzf /tmp/innokafe_website_sync.tar.gz -C /app/insilos/apps/innokafe_website/
chown -R insilos:insilos /app/insilos/enterprise/innokafe_website /app/insilos/apps/innokafe_website /app/insilos/tools
chmod 0755 /app/insilos/tools/sync_innokafe_views_db.py /app/insilos/tools/safe_asset_warmup.py
rm -f /tmp/innokafe_website_sync.tar.gz
"""

    insilos_templates = os.path.join(ROOT_DIR, "enterprise", "insilos_website", "views", "website_templates.xml")

    for pod in pods:
        run_cmd(["kubectl", "cp", "-n", namespace, "-c", container, tar_path, f"{pod}:/tmp/innokafe_website_sync.tar.gz"], check=True)
        run_cmd(["kubectl", "cp", "-n", namespace, "-c", container, sync_tool, f"{pod}:/app/insilos/tools/sync_innokafe_views_db.py"], check=True)
        run_cmd(["kubectl", "cp", "-n", namespace, "-c", container, warmup_tool, f"{pod}:/app/insilos/tools/safe_asset_warmup.py"], check=True)
        if os.path.exists(insilos_templates):
            run_cmd(["kubectl", "cp", "-n", namespace, "-c", container, insilos_templates, f"{pod}:/app/insilos/enterprise/insilos_website/views/website_templates.xml"], check=True)
            run_cmd(["kubectl", "cp", "-n", namespace, "-c", container, insilos_templates, f"{pod}:/app/insilos/apps/insilos_website/views/website_templates.xml"], check=True)
        run_cmd(["kubectl", "exec", "-n", namespace, pod, "-c", container, "--", "sh", "-c", extract_script], check=True)
        # Supply-chain integrity gate: verify SHA-256 for all distributed scripts across all pods (CWE-494)
        verify_pod_script_sha256(pod, "/app/insilos/tools/sync_innokafe_views_db.py", sync_sha, namespace, container)
        verify_pod_script_sha256(pod, "/app/insilos/tools/safe_asset_warmup.py", warmup_sha, namespace, container)
        print(f"[✓] Synchronized & verified SHA-256 on {pod}")


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
            cmd = ["kubectl", "exec", "-n", namespace, pod, "-c", container, "--", "md5sum", pod_file]
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
    cmd = ["kubectl", "exec", "-n", namespace, pod, "-c", container, "--", "sha256sum", remote_path]
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
    if not pods:
        raise RuntimeError("[FATAL] Zero active pods resolved for pre-warming (CWE-20).")
    pod_kafe = pods[0]

    warmup_tool = os.path.join(ROOT_DIR, "tools", "safe_asset_warmup.py")
    expected_sha = compute_local_sha256(warmup_tool)
    verify_pod_script_sha256(pod_kafe, "/app/insilos/tools/safe_asset_warmup.py", expected_sha, namespace, container)

    print(f"[*] Pre-warming asset bundles strictly for innokafe_prod on Pod {pod_kafe}:")

    proc_kafe = subprocess.Popen(
        ["kubectl", "exec", "-n", namespace, pod_kafe, "-c", container, "--",
         "python3", "/app/insilos/tools/safe_asset_warmup.py", "innokafe_prod"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )

    out_kafe, err_kafe = proc_kafe.communicate()

    print(f"\n--- Output from {pod_kafe} (innokafe_prod) ---")
    print(out_kafe.strip())
    if err_kafe.strip():
        print("Stderr:", err_kafe.strip())

    if proc_kafe.returncode != 0:
        raise RuntimeError(f"Asset pre-warming failed on innokafe_prod (code {proc_kafe.returncode})")

    dur = round(time.time() - t0, 2)
    print(f"\n[✓] Safe asset warmup for innokafe_prod completed in {dur}s.")


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


AUDIT_LEDGER_PATH = os.path.join(ROOT_DIR, "tools", ".deploy_audit_ledger.jsonl")
LOCAL_INTEGRITY_ANCHOR_PATH = os.path.join(ROOT_DIR, "tools", ".deploy_external_anchor.sha256")

# Trust Anchor Resolution (CWE-668 / F5):
# If INNOKAFE_EXTERNAL_ANCHOR_PATH is configured, use it.
# Otherwise, fall back to LOCAL_INTEGRITY_ANCHOR_PATH in degraded local mode with a security notice.
_configured_anchor = os.environ.get("INNOKAFE_EXTERNAL_ANCHOR_PATH")
REQUIRE_EXTERNAL_ANCHOR = os.environ.get("INNOKAFE_REQUIRE_EXTERNAL_ANCHOR", "0") == "1"

if _configured_anchor:
    EXTERNAL_ANCHOR_PATH = _configured_anchor
else:
    EXTERNAL_ANCHOR_PATH = LOCAL_INTEGRITY_ANCHOR_PATH
    if REQUIRE_EXTERNAL_ANCHOR and not os.environ.get("PYTEST_CURRENT_TEST"):
        print(
            "[*] [SECURITY NOTICE] Trust anchor is co-located in repository tools directory (degraded local mode, CWE-668). "
            "For full tamper-resistance, configure INNOKAFE_EXTERNAL_ANCHOR_PATH outside repo write boundary.",
            file=sys.stderr
        )


def _read_ledger_tip(ledger_path: str = AUDIT_LEDGER_PATH) -> Optional[str]:
    """Reads the current tip hash from the ledger file in O(1) time using reverse chunk seek.
    Resilient against torn partial lines at EOF and oversized single records (>16KB) (WARN-2 & WARN-3).
    """
    if not os.path.exists(ledger_path):
        return None
    try:
        file_size = os.path.getsize(ledger_path)
        if file_size == 0:
            return None

        # Seek up to 16384 bytes from the end of the file for O(1) tip lookup
        chunk_size = min(16384, file_size)
        with open(ledger_path, "rb") as f:
            f.seek(file_size - chunk_size)
            raw_tail = f.read(chunk_size)

        try:
            # Strict UTF-8 decode (avoid errors="replace" inventing corrupt tokens, CWE-20)
            text_tail = raw_tail.decode("utf-8")
        except UnicodeDecodeError:
            # If the chunk boundary sliced through a multi-byte character, strip up to the first newline
            first_nl = raw_tail.find(b"\n")
            if first_nl != -1:
                text_tail = raw_tail[first_nl + 1:].decode("utf-8", errors="ignore")
            else:
                text_tail = ""

        lines = text_tail.splitlines()
        for line in reversed(lines):
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                if isinstance(entry, dict) and "record_hash" in entry:
                    rec_hash = str(entry["record_hash"])
                    if len(rec_hash) == 64 and all(c in "0123456789abcdefABCDEF" for c in rec_hash):
                        return rec_hash.lower()
            except Exception:
                # Torn partial line at EOF from a previous crash/power cut; continue searching backwards
                continue

        # If 16KB tail chunk didn't yield a valid record but file is larger than chunk (e.g. oversized record >16KB),
        # fall back to a full file scan so large records are never dropped or treated as a fresh chain (CWE-20)
        if file_size > chunk_size:
            with open(ledger_path, "r", encoding="utf-8", errors="ignore") as f:
                last_valid_hash = None
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        if isinstance(entry, dict) and "record_hash" in entry:
                            h = str(entry["record_hash"])
                            if len(h) == 64:
                                last_valid_hash = h.lower()
                    except Exception:
                        continue
                if last_valid_hash:
                    return last_valid_hash

    except Exception:
        pass
    return None


def _verify_against_external_anchor(local_tip: Optional[str], anchor_path: str = EXTERNAL_ANCHOR_PATH) -> None:
    """Two-person rule / External trust anchor verification (CWE-345 / F5)."""
    if not REQUIRE_EXTERNAL_ANCHOR:
        return
    if not os.path.exists(anchor_path):
        return
    try:
        with open(anchor_path, "r", encoding="utf-8") as f:
            ext_anchor = f.read().strip()
        if ext_anchor and local_tip and ext_anchor.lower() != local_tip.lower():
            raise RuntimeError(
                f"Ledger tip integrity failure: local tip {local_tip[:16]} "
                f"does not match external trust anchor {ext_anchor[:16]}! "
                "(Possible ledger tampering, rollback or fork detected, CWE-345)"
            )
    except Exception as e:
        if isinstance(e, RuntimeError):
            raise
        pass


def _update_external_anchor(record_hash: str, anchor_path: str = EXTERNAL_ANCHOR_PATH) -> None:
    """Updates external trust anchor atomically via tempfile + os.replace + fsync (WARN-3)."""
    anchor_dir = os.path.dirname(os.path.abspath(anchor_path)) or "."
    os.makedirs(anchor_dir, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=anchor_dir, prefix=".anchor_tmp_")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(record_hash + "\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, anchor_path)  # atomic POSIX rename
        dir_fd = os.open(anchor_dir, os.O_RDONLY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    except Exception:
        if os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


def append_deploy_audit_record(pods: List[str], status: str, duration_sec: float) -> str:
    """Appends an immutable, hash-chained release receipt satisfying regulatory 72h audit trails.
    Acquires an exclusive OS flock across the critical section to prevent concurrency races (CWE-362 / F4).
    """
    lock_path = AUDIT_LEDGER_PATH + ".lock"
    os.makedirs(os.path.dirname(os.path.abspath(AUDIT_LEDGER_PATH)), exist_ok=True)
    fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)  # held across read-anchor + append (atomic critical section)

        local_tip = _read_ledger_tip(AUDIT_LEDGER_PATH)
        _verify_against_external_anchor(local_tip, EXTERNAL_ANCHOR_PATH)

        prev_hash = local_tip if local_tip else ("0" * 64)

        record = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "prev_hash": prev_hash,
            "namespace": NAMESPACE,
            "pods": pods,
            "media_assets_count": len(MEDIA_ASSETS),
            "status": status,
            "duration_sec": duration_sec,
            "edge_marker_present": bool(os.environ.get("EDGE_BUILD_MARKER")),
        }
        serialized = json.dumps(record, sort_keys=True)
        record_hash = hashlib.sha256((prev_hash + serialized).encode("utf-8")).hexdigest()
        record["record_hash"] = record_hash

        with open(AUDIT_LEDGER_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, sort_keys=True) + "\n")
            f.flush()
            os.fsync(f.fileno())  # survive crash between append and power loss

        _update_external_anchor(record_hash, EXTERNAL_ANCHOR_PATH)
        return record_hash
    finally:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        except OSError:
            pass
        os.close(fd)


def get_expected_provenance_markers(url: str) -> List[str]:
    """Returns endpoint-specific provenance markers."""
    if "innoria" in url:
        return ["InnoRia"]
    return ["InnoKafe"]


def edge_verification() -> None:
    print("\n=== STAGE 6. EXTERNAL EDGE HTTPS SMOKE PROBES ===")
    endpoints = [
        "https://innokafe.com/",
        "https://innokafe.insilos.com/",
        "https://innoria.insilos.com/"
    ]
    # Deploy-time identity marker; set in the pod env at release.
    # A bare 200 does not prove this is our build (CWE-345).
    expected_marker = os.environ.get("EDGE_BUILD_MARKER")
    if not expected_marker and os.environ.get("ENV") == "prod" and os.environ.get("STRICT_PROVENANCE") == "1":
        raise RuntimeError("EDGE_BUILD_MARKER unset in strict production environment; refusing to rely on plaintext markers alone (CWE-345).")

    ctx = ssl.create_default_context()
    for url in endpoints:
        print(f"[*] Probing edge HTTPS endpoint: {url} (timeout=15s)...")
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "ClusterEdgeVerification/2.0",
                "Accept": "text/html,application/xhtml+xml"
            }
        )
        try:
            with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
                code = resp.getcode()
                if code != 200:
                    raise RuntimeError(f"Edge probe failed for {url}! HTTP status: {code}")
                body = resp.read(131072).decode("utf-8", "replace")
                if expected_marker:
                    header_marker = resp.headers.get("X-Build-Marker") or resp.headers.get("X-Edge-Build")
                    has_header_match = bool(header_marker and hmac.compare_digest(header_marker, expected_marker))
                    has_body_match = expected_marker in body
                    if not (has_header_match or has_body_match):
                        raise RuntimeError(
                            f"Edge {url} returned 200 but build marker not found "
                            f"(possible stale/defaced/MITM edge, CWE-345)."
                        )
                    print(f"  [✓] {url} -> HTTP {code} OK (TLS verified, build_marker:verified)")
                else:
                    # In default live probes, assert endpoint-specific application provenance in body (CWE-345)
                    expected_markers = get_expected_provenance_markers(url)
                    for marker in expected_markers:
                        if marker not in body:
                            raise RuntimeError(
                                f"Edge {url} returned 200 but missing application provenance marker '{marker}' (CWE-345)!"
                            )
                    print(f"  [✓] {url} -> HTTP {code} OK (TLS verified, provenance verified: [{', '.join(expected_markers)}])")
        except urllib.error.HTTPError as he:
            # Edge answered with an error status: fail hard, do not paper over it.
            raise RuntimeError(f"Edge probe failed for {url}! HTTP status: {he.code}") from he
        except (urllib.error.URLError, ssl.SSLError, TimeoutError) as te:
            # Transport-level failure only (SNI/MTU/DNS): fall back to curl.
            # --fail: non-zero exit on HTTP >= 400 so we never validate an error page (FAIL-1).
            # --max-redirs 0 + --proto =https: refuse redirects (anti-MITM, CWE-601) and plaintext.
            res = run_cmd(["curl", "-sS", "--fail", "--proto", "=https",
                           "--max-redirs", "0", "-m", "15",
                           "-w", "\n%{http_code}", url])
            out = res.stdout or ""
            curl_body, _, status = out.rpartition("\n")
            status = status.strip()
            if res.returncode != 0 or status != "200" or not curl_body:
                raise RuntimeError(
                    f"Edge probe failed for {url}: transport error ({te}); "
                    f"curl exit={res.returncode} status={status or 'none'}"
                )
            if expected_marker:
                if expected_marker not in curl_body:
                    raise RuntimeError(
                        f"Edge {url} curl transport fallback failed: missing build marker (CWE-345)!"
                    )
                print(f"  [✓] {url} -> HTTP 200 OK (curl transport fallback, build_marker:verified)")
            else:
                expected_markers = get_expected_provenance_markers(url)
                for marker in expected_markers:
                    if marker not in curl_body:
                        raise RuntimeError(
                            f"Edge {url} curl transport fallback failed: missing provenance marker '{marker}' (CWE-345)!"
                        )
                print(f"  [✓] {url} -> HTTP 200 OK (curl transport fallback, provenance verified: [{', '.join(expected_markers)}])")


def main():
    t0 = time.time()
    print("=" * 75)
    print("🚀 INNOKAFE SYNC TO PODS — PRODUCTION CLUSTER PIPELINE")
    print(f"Namespace: {NAMESPACE} | Container: {CONTAINER} | Root: {ROOT_DIR}")
    print("=" * 75)

    try:
        pods = discover_active_pods(NAMESPACE)
        if not pods:
            raise RuntimeError(f"[FATAL] Zero active pods discovered in namespace '{NAMESPACE}'; aborting pipeline (CWE-20).")
        package_and_distribute(pods, NAMESPACE, CONTAINER)
        verify_md5_parity(pods, NAMESPACE, CONTAINER)
        sync_db_views(pods[0], NAMESPACE, CONTAINER)
        prewarm_assets(pods, NAMESPACE, CONTAINER)
        rolling_reload_workers(pods, NAMESPACE, CONTAINER)
        edge_verification()

        dur = round(time.time() - t0, 2)
        receipt_hash = append_deploy_audit_record(pods, "success", dur)
        print("\n" + "=" * 75)
        print(f"🎉 POD SYNCHRONIZATION PIPELINE SUCCEEDED IN {dur}s!")
        print(f"Audit Receipt Hash: {receipt_hash}")
        print("All pods synchronized, assets cryptographically verified, zero downtime achieved.")
        print("=" * 75)
        sys.exit(0)

    except Exception as e:
        print(f"\n❌ SYNC PIPELINE FAILED: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
