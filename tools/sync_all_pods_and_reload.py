#!/usr/bin/env python3
import subprocess
import time
import os

pods = [
    "insilos-saas-app-66c8dfbd69-82d5p",
    "insilos-saas-app-66c8dfbd69-c9jcl",
    "insilos-saas-app-66c8dfbd69-dz7dj"
]

files = [
    ("enterprise/insilos_website/views/innoria_homepage.xml", "/app/insilos/enterprise/insilos_website/views/innoria_homepage.xml"),
    ("enterprise/insilos_website/views/innoria_pages.xml", "/app/insilos/enterprise/insilos_website/views/innoria_pages.xml"),
    ("enterprise/insilos_website/views/snippets_3d.xml", "/app/insilos/enterprise/insilos_website/views/snippets_3d.xml"),
    ("enterprise/insilos_website/static/src/scss/innoria_theme.scss", "/app/insilos/enterprise/insilos_website/static/src/scss/innoria_theme.scss"),
    ("enterprise/insilos_website/static/src/js/innoria_deck_3d.js", "/app/insilos/enterprise/insilos_website/static/src/js/innoria_deck_3d.js"),
    ("tools/sync_innoria_views_db.py", "/app/insilos/tools/sync_innoria_views_db.py")
]

print("=== 1. COPYING FILES TO ALL PODS IN PARALLEL ===")
copy_procs = []
for pod in pods:
    for src, dst in files:
        cmd = ["kubectl", "cp", "-n", "production", "-c", "insilos", src, f"{pod}:{dst}"]
        p = subprocess.Popen(cmd)
        copy_procs.append((pod, src, p))

for pod, src, p in copy_procs:
    p.wait()
    if p.returncode != 0:
        print(f"[!] Failed to copy {src} to {pod}")
    else:
        print(f"[✓] Copied {src} -> {pod}")

print("\n=== 2. RUNNING DB SYNC ON POD 1 ===")
res = subprocess.run([
    "kubectl", "exec", "-n", "production", pods[0], "-c", "insilos", "--",
    "python3", "tools/sync_innoria_views_db.py", "prod_pod"
], capture_output=True, text=True)
print(res.stdout)
if res.stderr:
    print("Stderr:", res.stderr)

print("\n=== 3. RESTARTING CHILD WORKERS ON ALL 3 PODS IN PARALLEL ===")
worker_kill_script = """
import os, signal
current_pid = os.getpid()
for pid in os.listdir('/proc'):
    if pid.isdigit() and int(pid) > 1 and int(pid) != current_pid:
        try:
            with open(f'/proc/{pid}/cmdline', 'rb') as f:
                cmd = f.read()
                if b'insilos-bin' in cmd:
                    print(f'Killing worker {pid}')
                    os.kill(int(pid), signal.SIGTERM)
        except Exception:
            pass
"""

for pod in pods:
    print(f"[*] Reloading workers on {pod}...")
    subprocess.run([
        "kubectl", "exec", "-n", "production", pod, "-c", "insilos", "--",
        "python3", "-c", worker_kill_script
    ])

print("\n=== 4. WAITING 3 SECONDS FOR SPAWN ===")
time.sleep(3)

print("\n=== 5. PROBING ALL 3 PODS DIRECTLY ===")
probe_script = """
import urllib.request
try:
    req = urllib.request.Request('http://127.0.0.1:8069/', headers={'Host': 'innoria.insilos.com'})
    html = urllib.request.urlopen(req, timeout=30).read().decode()
    has_nav_gradient = 'linear-gradient(135deg, #0369A1' in html or 'linear-gradient(135deg,#0369A1' in html
    print(f'[✓] Probe HTTP 200 OK - Gradient in Navbar: {has_nav_gradient}')
except Exception as e:
    print(f'[!] Probe error: {e}')
"""

for pod in pods:
    print(f"[*] Probing {pod}:")
    subprocess.run([
        "kubectl", "exec", "-n", "production", pod, "-c", "insilos", "--",
        "python3", "-c", probe_script
    ])
