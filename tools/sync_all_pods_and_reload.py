#!/usr/bin/env python3
import subprocess
import time
import os

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
    exit(1)

# Package targeted files (controllers, views, scss, js, icons, images)
print("\n=== 1. PACKAGING targeted insilos_website ARCHIVE ===")
tar_path = "/tmp/insilos_website_sync.tar.gz"
run_cmd(
    f"tar -czf {tar_path} -C enterprise/insilos_website "
    f"__manifest__.py controllers views static/src/scss static/src/js static/src/icons static/src/img/innoria",
    check=True
)
tar_size = os.path.getsize(tar_path)
print(f"[✓] Created {tar_path} ({tar_size} bytes)")

print("\n=== 2. DEPLOYING ARCHIVE TO ALL PODS IN PARALLEL ===")
deploy_procs = []
for pod in pods:
    cmd = (
        f"kubectl cp -n {NAMESPACE} -c {CONTAINER} {tar_path} {pod}:/tmp/insilos_website_sync.tar.gz && "
        f"kubectl cp -n {NAMESPACE} -c {CONTAINER} tools/sync_innoria_views_db.py {pod}:/app/insilos/tools/sync_innoria_views_db.py && "
        f"kubectl exec -n {NAMESPACE} {pod} -c {CONTAINER} -- sh -c '"
        f"mkdir -p /app/insilos/apps/insilos_website /app/insilos/enterprise/insilos_website && "
        f"tar -xzf /tmp/insilos_website_sync.tar.gz -C /app/insilos/apps/insilos_website/ && "
        f"tar -xzf /tmp/insilos_website_sync.tar.gz -C /app/insilos/enterprise/insilos_website/ && "
        f"chown -R insilos:insilos /app/insilos/apps/insilos_website /app/insilos/enterprise/insilos_website /app/insilos/tools/sync_innoria_views_db.py && "
        f"rm -f /tmp/insilos_website_sync.tar.gz'"
    )
    p = subprocess.Popen(cmd, shell=True)
    deploy_procs.append((pod, p))

for pod, p in deploy_procs:
    p.wait()
    if p.returncode != 0:
        print(f"[!] Failed deployment on {pod}")
    else:
        print(f"[✓] Synchronized files to {pod}")

print("\n=== 3. RUNNING DB SYNC ON LEAD POD ===")
res = subprocess.run([
    "kubectl", "exec", "-n", "production", pods[0], "-c", "insilos", "--",
    "python3", "/app/insilos/tools/sync_innoria_views_db.py", "prod_pod"
], capture_output=True, text=True)
print(res.stdout)
if res.stderr:
    print("Stderr:", res.stderr)

print("\n=== 4. RESTARTING CHILD WORKERS ON ALL PODS IN PARALLEL ===")
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
        "kubectl", "exec", "-n", "production", pod, "-c", "insilos", "--",
        "python3", "-c", worker_kill_script
    ])
    reload_procs.append((pod, p))

for pod, p in reload_procs:
    p.wait()

print("\n=== 5. WAITING 5 SECONDS FOR SPAWN ===")
time.sleep(5)

print("\n=== 6. PROBING ALL PODS DIRECTLY ===")
probe_script = """
import urllib.request
try:
    req = urllib.request.Request('http://127.0.0.1:8069/', headers={'Host': 'innoria.insilos.com', 'X-Forwarded-Host': 'innoria.insilos.com', 'X-Forwarded-Proto': 'https'})
    html = urllib.request.urlopen(req, timeout=30).read().decode('utf-8', 'ignore')
    has_deck = 'architecture_deck' in html or 's_innoria_3d_architecture_deck' in html or 'deckContainer' in html
    has_innoria = 'INNORIA' in html
    has_insilos_hero = 'Insilos 3D Hero Cinematic' in html
    has_hero_slider = 'hero-slider' in html or 'innoria-hero' in html or 'hero_slider' in html
    print(f'[✓] Status 200 OK | INNORIA: {has_innoria} | 3D Deck: {has_deck} | Hero Slider: {has_hero_slider} | Insilos Hero: {has_insilos_hero}')
except Exception as e:
    print(f'[!] Probe error: {e}')
"""

for pod in pods:
    print(f"[*] Probing {pod}:")
    subprocess.run([
        "kubectl", "exec", "-n", "production", pod, "-c", "insilos", "--",
        "python3", "-c", probe_script
    ])

print("\n=== 7. PROBING EXTERNAL INNORIA.INSILOS.COM ===")
ext_res = run_cmd("curl -sL https://innoria.insilos.com/ | grep -oE 'architecture_deck|hero-slider|Insilos 3D Hero' | head -n 5")
print(f"External check result: {ext_res.stdout.strip()}")
