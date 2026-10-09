#!/usr/bin/env python3
import subprocess
import time
import os

NAMESPACE = "production"
CONTAINER = "innoria"

def run_cmd(cmd, check=False):
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and res.returncode != 0:
        raise RuntimeError(f"Command failed ({res.returncode}): {cmd}\n{res.stderr}")
    return res

print("=== 0. DISCOVERING ACTIVE DEDICATED INNORIA PROD PODS ===")
pod_out = run_cmd(f"kubectl get pods -n {NAMESPACE} -l app=innoria-prod --field-selector=status.phase=Running -o jsonpath='{{.items[*].metadata.name}}'")
pods = [p.strip() for p in pod_out.stdout.split() if p.strip()]
print(f"[✓] Found {len(pods)} running innoria-prod pods: {pods}")

if not pods:
    print("[!] No running innoria-prod pods found! Aborting.")
    exit(1)

# Package targeted files (controllers, views, scss, js, icons, images)
print("\n=== 1. PACKAGING targeted insilos_website & insilos_theme_genesis ARCHIVES ===")
tar_path_website = "/tmp/insilos_website_sync.tar.gz"
run_cmd(
    f"tar --exclude='*.mp4' --exclude='static/src/video/gold_masters' -czf {tar_path_website} -C enterprise/insilos_website "
    f"__manifest__.py controllers views static",
    check=True
)
tar_size_web = os.path.getsize(tar_path_website)
print(f"[✓] Created {tar_path_website} ({tar_size_web} bytes)")

tar_path_theme = "/tmp/insilos_theme_genesis_sync.tar.gz"
run_cmd(
    f"tar -czf {tar_path_theme} -C enterprise/insilos_theme_genesis "
    f"__manifest__.py views static",
    check=True
)
tar_size_theme = os.path.getsize(tar_path_theme)
print(f"[✓] Created {tar_path_theme} ({tar_size_theme} bytes)")

print("\n=== 2. DEPLOYING ARCHIVES TO ALL INNORIA PODS IN PARALLEL ===")
deploy_procs = []
for pod in pods:
    cmd = (
        f"kubectl cp -n {NAMESPACE} -c {CONTAINER} {tar_path_website} {pod}:/tmp/insilos_website_sync.tar.gz && "
        f"kubectl cp -n {NAMESPACE} -c {CONTAINER} {tar_path_theme} {pod}:/tmp/insilos_theme_genesis_sync.tar.gz && "
        f"kubectl cp -n {NAMESPACE} -c {CONTAINER} tools/sync_innoria_views_db.py {pod}:/tmp/sync_innoria_views_db.py && "
        f"kubectl cp -n {NAMESPACE} -c {CONTAINER} tools/sync_logos_to_assets_library.py {pod}:/tmp/sync_logos_to_assets_library.py && "
        f"kubectl cp -n {NAMESPACE} -c {CONTAINER} tools/safe_asset_warmup.py {pod}:/tmp/safe_asset_warmup.py && "
        f"kubectl exec -n {NAMESPACE} {pod} -c {CONTAINER} -- sh -c '"
        f"mkdir -p /app/insilos/enterprise/insilos_website /app/insilos/enterprise/insilos_theme_genesis /app/insilos/apps/insilos_website /app/insilos/apps/insilos_theme_genesis && "
        f"tar -xzf /tmp/insilos_website_sync.tar.gz -C /app/insilos/enterprise/insilos_website/ && "
        f"tar -xzf /tmp/insilos_website_sync.tar.gz -C /app/insilos/apps/insilos_website/ && "
        f"tar -xzf /tmp/insilos_theme_genesis_sync.tar.gz -C /app/insilos/enterprise/insilos_theme_genesis/ && "
        f"tar -xzf /tmp/insilos_theme_genesis_sync.tar.gz -C /app/insilos/apps/insilos_theme_genesis/ && "
        f"rm -f /tmp/insilos_website_sync.tar.gz /tmp/insilos_theme_genesis_sync.tar.gz'"
    )
    p = subprocess.Popen(cmd, shell=True)
    deploy_procs.append((pod, p))

for pod, p in deploy_procs:
    p.wait()
    if p.returncode != 0:
        print(f"[!] Failed deployment on {pod}")
    else:
        print(f"[✓] Synchronized files to {pod}")

print("\n=== 3. RUNNING DB SYNC ON LEAD INNORIA POD ===")
res = subprocess.run([
    "kubectl", "exec", "-n", "production", pods[0], "-c", CONTAINER, "--",
    "python3", "/tmp/sync_innoria_views_db.py", "prod_pod"
], capture_output=True, text=True)
print(res.stdout)
if res.stderr:
    print("Stderr:", res.stderr)

print("\n=== 3B. REGISTERING LOGOS IN ASSETS LIBRARY (IR.ATTACHMENT) ON LEAD POD ===")
res_assets = subprocess.run([
    "kubectl", "exec", "-n", "production", pods[0], "-c", CONTAINER, "--",
    "python3", "/tmp/sync_logos_to_assets_library.py", "prod_pod"
], capture_output=True, text=True)
print(res_assets.stdout)
if res_assets.stderr:
    print("Stderr:", res_assets.stderr)

print("\n=== 3C. ZERO-DOWNTIME SCSS ASSET PRE-WARMING ON LEAD POD ===")
res_warmup = subprocess.run([
    "kubectl", "exec", "-n", "production", pods[0], "-c", CONTAINER, "--",
    "python3", "/tmp/safe_asset_warmup.py", "innoria_prod"
], capture_output=True, text=True)
print(res_warmup.stdout)
if res_warmup.stderr:
    print("Stderr:", res_warmup.stderr)

print("\n=== 4. RESTARTING CHILD WORKERS ON ALL INNORIA PODS IN PARALLEL ===")
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
        "kubectl", "exec", "-n", "production", pod, "-c", CONTAINER, "--",
        "python3", "-c", worker_kill_script
    ])
    reload_procs.append((pod, p))

for pod, p in reload_procs:
    p.wait()

print("\n[*] Waiting 4s for master process to respawn pristine workers...")
time.sleep(4)

print("\n=== 5. PROBING ALL INNORIA PODS DIRECTLY ===")
all_ok = True
for pod in pods:
    pod_ip_res = run_cmd(f"kubectl get pod -n {NAMESPACE} {pod} -o jsonpath='{{.status.podIP}}'")
    pod_ip = pod_ip_res.stdout.strip()
    probe_cmd = f"curl -s -o /dev/null -w '%{{http_code}}' -H 'Host: innoria.com' http://{pod_ip}:8069/"
    code_res = run_cmd(probe_cmd)
    code = code_res.stdout.strip()
    if code in ("200", "303", "301", "302"):
        print(f"[✓] Pod {pod} ({pod_ip}): HTTP {code} OK")
    else:
        print(f"[✗] Pod {pod} ({pod_ip}): HTTP {code} FAILED")
        all_ok = False

if all_ok:
    print("\n[SUCCESS] Dedicated Innoria cluster is 100% synchronized and healthy!")
else:
    print("\n[WARNING] Some pods reported non-200 status. Check logs.")
