#!/usr/bin/env python3
"""
Full-cluster production deployment and synchronization script for InnoKafe Specialty Coffee.
Packages module, deploys to all Kubernetes pods in parallel, executes DB sync on innokafe_prod,
pre-warms asset bundles, gracefully reloads worker processes, and performs multi-layer probes.
"""

import subprocess
import time
import os
import sys

NAMESPACE = "production"
CONTAINER = "insilos"

def run_cmd(cmd, check=False):
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and res.returncode != 0:
        raise RuntimeError(f"Command failed ({res.returncode}): {cmd}\n{res.stderr}")
    return res

print("=== 0. DISCOVERING ACTIVE RUNNING PODS ===")
pod_out = run_cmd(f"kubectl get pods -n {NAMESPACE} -l app=insilos-saas --field-selector=status.phase=Running -o jsonpath='{{.items[*].metadata.name}}'")
pods = [p.strip() for p in pod_out.stdout.split() if p.strip()]
print(f"[✓] Found {len(pods)} running pods: {pods}")

if not pods:
    print("[!] No running insilos-saas pods found! Aborting.")
    sys.exit(1)

print("\n=== 1. PACKAGING enterprise/innokafe_website ARCHIVE ===")
tar_path = "/tmp/innokafe_website_sync.tar.gz"
run_cmd(
    f"tar -czf {tar_path} -C enterprise/innokafe_website "
    f"__init__.py __manifest__.py controllers data models static tools views",
    check=True
)
tar_size = os.path.getsize(tar_path)
print(f"[✓] Created {tar_path} ({tar_size} bytes)")

print("\n=== 2. DEPLOYING ARCHIVE & SYNC TOOLS TO ALL PODS IN PARALLEL ===")
deploy_procs = []
for pod in pods:
    cmd = (
        f"kubectl cp -n {NAMESPACE} -c {CONTAINER} {tar_path} {pod}:/tmp/innokafe_website_sync.tar.gz && "
        f"kubectl cp -n {NAMESPACE} -c {CONTAINER} tools/sync_innokafe_views_db.py {pod}:/tmp/sync_innokafe_views_db.py && "
        f"kubectl cp -n {NAMESPACE} -c {CONTAINER} tools/safe_asset_warmup.py {pod}:/tmp/safe_asset_warmup.py && "
        f"kubectl exec -n {NAMESPACE} {pod} -c {CONTAINER} -- sh -c '"
        f"mkdir -p /app/insilos/enterprise/innokafe_website /app/insilos/apps/innokafe_website && "
        f"tar -xzf /tmp/innokafe_website_sync.tar.gz -C /app/insilos/enterprise/innokafe_website/ && "
        f"tar -xzf /tmp/innokafe_website_sync.tar.gz -C /app/insilos/apps/innokafe_website/ && "
        f"chown -R insilos:insilos /app/insilos/enterprise/innokafe_website /app/insilos/apps/innokafe_website /tmp/sync_innokafe_views_db.py /tmp/safe_asset_warmup.py && "
        f"rm -f /tmp/innokafe_website_sync.tar.gz'"
    )
    p = subprocess.Popen(cmd, shell=True)
    deploy_procs.append((pod, p))

for pod, p in deploy_procs:
    p.wait()
    if p.returncode != 0:
        print(f"[!] Failed deployment on {pod}")
    else:
        print(f"[✓] Synchronized files to {pod}")

print("\n=== 3. EXECUTING INNOKAFE DB SYNC ON LEAD POD ===")
res_sync = subprocess.run([
    "kubectl", "exec", "-n", NAMESPACE, pods[0], "-c", CONTAINER, "--",
    "python3", "/tmp/sync_innokafe_views_db.py", "prod_pod"
], capture_output=True, text=True)
print(res_sync.stdout)
if res_sync.stderr:
    print("Stderr:", res_sync.stderr)

if res_sync.returncode != 0:
    print("[!] DB sync failed! Aborting reload.")
    sys.exit(1)

print("\n=== 4. ZERO-DOWNTIME ASSET PRE-WARMING ON LEAD POD ===")
res_warmup = subprocess.run([
    "kubectl", "exec", "-n", NAMESPACE, pods[0], "-c", CONTAINER, "--",
    "python3", "/tmp/safe_asset_warmup.py", "innokafe_prod"
], capture_output=True, text=True)
print(res_warmup.stdout)
if res_warmup.stderr:
    print("Stderr:", res_warmup.stderr)

print("\n=== 5. RESTARTING CHILD WORKERS ON ALL PODS IN PARALLEL ===")
worker_kill_script = """
import os, signal
current_pid = os.getpid()
for pid in os.listdir('/proc'):
    if pid.isdigit() and int(pid) > 1 and int(pid) != current_pid:
        try:
            with open(f'/proc/{pid}/cmdline', 'rb') as f:
                cmd = f.read()
                if b'insilos-bin' in cmd:
                    print(f'Signaling worker {pid}')
                    os.kill(int(pid), signal.SIGTERM)
        except Exception:
            pass
"""

reload_procs = []
for pod in pods:
    print(f"[*] Reloading workers on {pod}...")
    p = subprocess.Popen([
        "kubectl", "exec", "-n", NAMESPACE, pod, "-c", CONTAINER, "--",
        "python3", "-c", worker_kill_script
    ])
    reload_procs.append((pod, p))

for pod, p in reload_procs:
    p.wait()

print("\n=== 6. WAITING 6 SECONDS FOR WORKERS TO RESPAWN ===")
time.sleep(6)

print("\n=== 7. PROBING ALL PODS DIRECTLY ===")
probe_script = """
import urllib.request, re
try:
    req = urllib.request.Request(
        'http://127.0.0.1:8069/',
        headers={'Host': 'innokafe.insilos.com', 'X-Forwarded-Host': 'innokafe.insilos.com', 'X-Forwarded-Proto': 'https'}
    )
    res = urllib.request.urlopen(req, timeout=30)
    html = res.read().decode('utf-8', 'ignore')
    has_innokafe = 'InnoKafe' in html
    has_hero = 'Cà Phê Việt Nam Nguyên Bản' in html
    has_insilos_hero = 'Chấm Dứt Ốc Đảo Dữ Liệu' in html
    has_insilos_megamenu = 'headingMobileSolutions' in html
    title = re.search(r'<title>(.*?)</title>', html)
    title_text = title.group(1).strip() if title else 'NO_TITLE'
    status_icon = '✓' if (has_innokafe and has_hero and not has_insilos_hero and not has_insilos_megamenu) else '✗'
    print(f'[{status_icon}] HTTP {res.status} | Title: \"{title_text}\" | InnoKafe: {has_innokafe} | Hero: {has_hero} | Rogue Insilos: {has_insilos_hero or has_insilos_megamenu}')
except Exception as e:
    print(f'[!] Probe error: {e}')
"""

for pod in pods:
    print(f"[*] Probing {pod}:")
    subprocess.run([
        "kubectl", "exec", "-n", NAMESPACE, pod, "-c", CONTAINER, "--",
        "python3", "-c", probe_script
    ])

print("\n=== 8. PROBING EXTERNAL HTTPS://INNOKAFE.INSILOS.COM ===")
ext_res = run_cmd("curl -sI https://innokafe.insilos.com/ | head -n 5")
print(f"Headers:\n{ext_res.stdout.strip()}")

ext_body = run_cmd("curl -sL https://innokafe.insilos.com/ | grep -E 'InnoKafe|Cà Phê Việt Nam|Chấm Dứt Ốc Đảo' | head -n 5")
print(f"Sample matches:\n{ext_body.stdout.strip()}")
print("\n[✓] Deployment & verification workflow completed.")
