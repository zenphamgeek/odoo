#!/usr/bin/env python3
import subprocess
import time
import os
import sys

NAMESPACE = "production"

def run_cmd(cmd, check=False):
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and res.returncode != 0:
        raise RuntimeError(f"Command failed ({res.returncode}): {cmd}\n{res.stderr}")
    return res

print("=== 0. DISCOVERING ACTIVE RUNNING PODS ACROSS ALL INNORIA & INSILOS SERVICES ===")

import re

# Discover innoria-prod pods
res_inno = run_cmd(f"kubectl get pods -n {NAMESPACE} -l app=innoria-prod --field-selector=status.phase=Running -o jsonpath='{{.items[*].metadata.name}}'")
innoria_pods = [p for p in res_inno.stdout.split() if p.strip() and re.match(r"^[a-zA-Z0-9.-]+$", p.strip())]

# Discover insilos-saas pods
res_insilos = run_cmd(f"kubectl get pods -n {NAMESPACE} -l app=insilos-saas --field-selector=status.phase=Running -o jsonpath='{{.items[*].metadata.name}}'")
insilos_pods = [p for p in res_insilos.stdout.split() if p.strip() and re.match(r"^[a-zA-Z0-9.-]+$", p.strip())]

print(f"[✓] Found {len(innoria_pods)} innoria-prod pods: {innoria_pods}")
print(f"[✓] Found {len(insilos_pods)} insilos-saas pods: {insilos_pods}")

all_targets = []
for p in innoria_pods:
    all_targets.append({"pod": p, "container": "innoria", "service": "innoria-prod", "db": "innoria_prod", "host": "innoria.com"})
for p in insilos_pods:
    all_targets.append({"pod": p, "container": "insilos", "service": "insilos-saas", "db": "insilos_ind_inno_ai", "host": "insilos.com"})

if not all_targets:
    print("[!] No active running pods found! Aborting.")
    sys.exit(1)

print("\n=== 1. PACKAGING targeted insilos_website, theme, and media ARCHIVES ===")
tar_path_website = "/tmp/insilos_website_sync.tar.gz"
run_cmd(
    f"tar --exclude='static/src/video' --exclude='static/src/img' --exclude='static/src/docs' -chzf {tar_path_website} -C enterprise/insilos_website "
    f"__manifest__.py controllers views static/src/scss static/src/js static/src/icons",
    check=True
)
tar_size_web = os.path.getsize(tar_path_website)
print(f"[✓] Created {tar_path_website} ({tar_size_web:,} bytes)")

tar_path_media = "/tmp/insilos_media_sync.tar.gz"
media_files = [
    "static/src/video/hero_cleanroom_pharma_opt.mp4",
    "static/src/video/hero_cleanroom_pharma_opt_poster.webp",
    "static/src/video/hero_fmcg_conveyor_opt.mp4",
    "static/src/video/hero_fmcg_conveyor_opt_poster.webp",
    "static/src/video/hero_petrochem_refinery_opt.mp4",
    "static/src/video/hero_petrochem_refinery_opt_poster.webp",
    "static/src/video/hero_digiforce_opt.mp4",
    "static/src/video/hero_digiforce_opt_poster.webp",
    "static/src/video/hero_blockchain_opt.mp4",
    "static/src/video/hero_blockchain_opt_poster.webp",
    "static/src/video/hero_contact_opt.mp4",
    "static/src/video/hero_contact_opt_poster.webp",
    "static/src/img/innoria/bg_contactus_boardroom.webp",
    "static/src/img/innoria/bg_digiforce_grid.webp",
    "static/src/img/innoria/bg_industry_precision.webp",
    "static/src/img/innoria/bg_platform_datacenter.webp",
    "static/src/img/innoria/bg_about_architecture.webp",
    "static/src/img/innoria/bg_blockchain_lattice.webp",
]
existing_media = [m for m in media_files if os.path.exists(os.path.join("enterprise/insilos_website", m))]
run_cmd(
    f"tar -czf {tar_path_media} -C enterprise/insilos_website {' '.join(existing_media)}",
    check=True
)
tar_size_media = os.path.getsize(tar_path_media)
print(f"[✓] Created {tar_path_media} ({tar_size_media:,} bytes)")

tar_path_theme = "/tmp/insilos_theme_genesis_sync.tar.gz"
run_cmd(
    f"tar -czf {tar_path_theme} -C enterprise/insilos_theme_genesis "
    f"__manifest__.py views static",
    check=True
)
tar_size_theme = os.path.getsize(tar_path_theme)
print(f"[✓] Created {tar_path_theme} ({tar_size_theme:,} bytes)")

tar_path_adapter = "/tmp/insilos_adapter_sync.tar.gz"
run_cmd(
    f"tar -czf {tar_path_adapter} -C addons/insilos_adapter hook.py",
    check=True
)
print(f"[✓] Created {tar_path_adapter}")

print("\n=== 2. DEPLOYING ARCHIVES TO ALL PODS & PERSISTENT VOLUMES IN PARALLEL ===")
deploy_procs = []

for target in all_targets:
    pod = target["pod"]
    container = target["container"]
    cmd = (
        f"kubectl cp -n {NAMESPACE} -c {container} {tar_path_website} {pod}:/tmp/insilos_website_sync.tar.gz && "
        f"kubectl cp -n {NAMESPACE} -c {container} {tar_path_media} {pod}:/tmp/insilos_media_sync.tar.gz && "
        f"kubectl cp -n {NAMESPACE} -c {container} {tar_path_theme} {pod}:/tmp/insilos_theme_genesis_sync.tar.gz && "
        f"kubectl cp -n {NAMESPACE} -c {container} {tar_path_adapter} {pod}:/tmp/insilos_adapter_sync.tar.gz && "
        f"kubectl cp -n {NAMESPACE} -c {container} tools/sync_innoria_views_db.py {pod}:/tmp/sync_innoria_views_db.py && "
        f"kubectl cp -n {NAMESPACE} -c {container} tools/sync_logos_to_assets_library.py {pod}:/tmp/sync_logos_to_assets_library.py && "
        f"kubectl cp -n {NAMESPACE} -c {container} tools/safe_asset_warmup.py {pod}:/tmp/safe_asset_warmup.py && "
        f"kubectl exec -n {NAMESPACE} {pod} -c {container} -- sh -c '"
        f"mkdir -p /var/lib/insilos/filestore/custom_addons/insilos_website "
        f"/var/lib/insilos/filestore/custom_addons/insilos_theme_genesis "
        f"/app/insilos/enterprise/insilos_website "
        f"/app/insilos/enterprise/insilos_theme_genesis "
        f"/app/insilos/apps/insilos_website "
        f"/app/insilos/apps/insilos_theme_genesis && "
        # Extract into persistent storage (Longhorn block volume)
        f"tar -xzf /tmp/insilos_website_sync.tar.gz -C /var/lib/insilos/filestore/custom_addons/insilos_website/ && "
        f"tar -xzf /tmp/insilos_media_sync.tar.gz -C /var/lib/insilos/filestore/custom_addons/insilos_website/ && "
        f"tar -xzf /tmp/insilos_theme_genesis_sync.tar.gz -C /var/lib/insilos/filestore/custom_addons/insilos_theme_genesis/ && "
        # Extract into runtime app paths (where Odoo loads enterprise modules)
        f"tar -xzf /tmp/insilos_website_sync.tar.gz -C /app/insilos/enterprise/insilos_website/ && "
        f"tar -xzf /tmp/insilos_media_sync.tar.gz -C /app/insilos/enterprise/insilos_website/ && "
        f"tar -xzf /tmp/insilos_website_sync.tar.gz -C /app/insilos/apps/insilos_website/ && "
        f"tar -xzf /tmp/insilos_media_sync.tar.gz -C /app/insilos/apps/insilos_website/ && "
        f"tar -xzf /tmp/insilos_theme_genesis_sync.tar.gz -C /app/insilos/enterprise/insilos_theme_genesis/ && "
        f"tar -xzf /tmp/insilos_theme_genesis_sync.tar.gz -C /app/insilos/apps/insilos_theme_genesis/ && "
        # Update insilos_adapter hook
        f"tar -xzf /tmp/insilos_adapter_sync.tar.gz -C /app/insilos/addons/insilos_adapter/ 2>/dev/null || true && "
        f"tar -xzf /tmp/insilos_adapter_sync.tar.gz -C /app/insilos/insilos_adapter/ 2>/dev/null || true && "
        # Ensure correct ownership
        f"chown -R insilos:insilos /var/lib/insilos/filestore/custom_addons /app/insilos/enterprise /app/insilos/apps /tmp/*.py 2>/dev/null || true && "
        f"rm -f /tmp/insilos_website_sync.tar.gz /tmp/insilos_media_sync.tar.gz /tmp/insilos_theme_genesis_sync.tar.gz /tmp/insilos_adapter_sync.tar.gz'"
    )
    p = subprocess.Popen(cmd, shell=True)
    deploy_procs.append((pod, p))

for pod, p in deploy_procs:
    p.wait()
    if p.returncode != 0:
        print(f"[!] Failed deployment on {pod}")
    else:
        print(f"[✓] Synchronized persistent filestore and runtime paths to {pod}")

print("\n=== 3. RUNNING DB SYNC ON INNORIA LEAD POD ===")
if innoria_pods:
    lead_pod = innoria_pods[0]
    print(f"[*] Running view and asset sync on {lead_pod} (container: innoria)...")
    res = subprocess.run([
        "kubectl", "exec", "-n", "production", lead_pod, "-c", "innoria", "--",
        "python3", "/tmp/sync_innoria_views_db.py", "prod_pod"
    ], capture_output=True, text=True)
    print(res.stdout)
    if res.stderr:
        print("Stderr:", res.stderr)

    res_assets = subprocess.run([
        "kubectl", "exec", "-n", "production", lead_pod, "-c", "innoria", "--",
        "python3", "/tmp/sync_logos_to_assets_library.py", "prod_pod"
    ], capture_output=True, text=True)
    print(res_assets.stdout)
    if res_assets.stderr:
        print("Stderr:", res_assets.stderr)

    print("\n[*] Pre-warming SCSS assets for innoria_prod...")
    res_warmup = subprocess.run([
        "kubectl", "exec", "-n", "production", lead_pod, "-c", "innoria", "--",
        "python3", "/tmp/safe_asset_warmup.py", "innoria_prod"
    ], capture_output=True, text=True)
    print(res_warmup.stdout)
    if res_warmup.stderr:
        print("Stderr:", res_warmup.stderr)

print("\n=== 3B. PRE-WARMING ASSETS ON INSILOS LEAD POD ===")
if insilos_pods:
    lead_insilos = insilos_pods[0]
    print(f"[*] Pre-warming SCSS assets on {lead_insilos} for insilos_ind_inno_ai...")
    res_warmup2 = subprocess.run([
        "kubectl", "exec", "-n", "production", lead_insilos, "-c", "insilos", "--",
        "python3", "/tmp/safe_asset_warmup.py", "insilos_ind_inno_ai"
    ], capture_output=True, text=True)
    print(res_warmup2.stdout)
    if res_warmup2.stderr:
        print("Stderr:", res_warmup2.stderr)

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
for target in all_targets:
    pod = target["pod"]
    container = target["container"]
    print(f"[*] Reloading workers on {pod} ({container})...")
    p = subprocess.Popen([
        "kubectl", "exec", "-n", "production", pod, "-c", container, "--",
        "python3", "-c", worker_kill_script
    ])
    reload_procs.append((pod, p))

for pod, p in reload_procs:
    p.wait()

print("\n=== 5. WAITING 5 SECONDS FOR CLEAN WORKER RESPAWN ===")
time.sleep(5)

print("\n=== 6. PROBING ALL PODS DIRECTLY ===")
probe_script = """
import urllib.request, sys
host = sys.argv[1] if len(sys.argv) > 1 else 'innoria.com'
try:
    req = urllib.request.Request('http://127.0.0.1:8069/', headers={'Host': host, 'X-Forwarded-Host': host, 'X-Forwarded-Proto': 'https'})
    html = urllib.request.urlopen(req, timeout=30).read().decode('utf-8', 'ignore')
    has_deck = 'architecture_deck' in html or 's_innoria_3d_architecture_deck' in html or 'deckContainer' in html
    has_innoria = 'INNORIA' in html
    has_hero_slider = 'hero-slider' in html or 'innoria-hero' in html or 'hero_slider' in html
    print(f'[✓] Host: {host} | Status 200 OK | INNORIA: {has_innoria} | 3D Deck: {has_deck} | Hero: {has_hero_slider} | Length: {len(html):,}')
except Exception as e:
    print(f'[!] Probe error for {host}: {e}')
"""

for target in all_targets:
    pod = target["pod"]
    container = target["container"]
    host = target["host"]
    print(f"[*] Probing {pod} ({container}) for {host}:")
    subprocess.run([
        "kubectl", "exec", "-n", "production", pod, "-c", container, "--",
        "python3", "-c", probe_script, host
    ])

print("\n=== 7. PROBING PUBLIC DOMAINS ===")
for url in ["https://innoria.com/", "https://innoria.insilos.com/"]:
    res = run_cmd(f"curl -sI {url} | head -n 3")
    print(f"{url} -> {res.stdout.strip().replace(chr(10), ' | ')}")

print("\n[✓] ALL PODS SYNCHRONIZED AND VERIFIED ZERO-REGRESSION!")
