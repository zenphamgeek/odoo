#!/usr/bin/env python3
import subprocess
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

print("\n=== 1. PACKAGING innokafe_website ARCHIVE ===")
tar_path_kafe = "/tmp/innokafe_website_sync.tar.gz"
run_cmd(
    f"tar -czf {tar_path_kafe} -C enterprise/innokafe_website .",
    check=True
)
print(f"[✓] Created {tar_path_kafe} ({os.path.getsize(tar_path_kafe)} bytes)")

print("\n=== 2. DEPLOYING ARCHIVES TO ALL PODS IN PARALLEL ===")
deploy_procs = []
for pod in pods:
    cmd = (
        f"kubectl cp -n {NAMESPACE} -c {CONTAINER} {tar_path_kafe} {pod}:/tmp/innokafe_website_sync.tar.gz && "
        f"kubectl exec -n {NAMESPACE} {pod} -c {CONTAINER} -- sh -c '"
        f"mkdir -p /app/insilos/enterprise/innokafe_website /app/insilos/apps/innokafe_website && "
        f"tar -xzf /tmp/innokafe_website_sync.tar.gz -C /app/insilos/enterprise/innokafe_website/ && "
        f"tar -xzf /tmp/innokafe_website_sync.tar.gz -C /app/insilos/apps/innokafe_website/ && "
        f"chown -R insilos:insilos /app/insilos/enterprise/innokafe_website /app/insilos/apps/innokafe_website && "
        f"rm -f /tmp/innokafe_website_sync.tar.gz'"
    )
    p = subprocess.Popen(cmd, shell=True)
    deploy_procs.append((pod, p))

for pod, p in deploy_procs:
    p.wait()
    if p.returncode != 0:
        print(f"[!] Failed deployment on {pod}")
    else:
        print(f"[✓] Synchronized innokafe_website to {pod}")

print("\n=== 3. INSTALLING/UPGRADING innokafe_website ON LEAD POD ===")
res = subprocess.run([
    "kubectl", "exec", "-n", "production", pods[0], "-c", "insilos", "--",
    "python3", "/app/insilos/insilos-bin",
    "-c", "/etc/insilos/insilos.conf",
    "--stop-after-init",
    "-d", "innokafe_prod",
    "-i", "innokafe_website",
    "--no-http"
], capture_output=True, text=True)
print(res.stdout[-1500:] if len(res.stdout) > 1500 else res.stdout)
if res.stderr:
    print("Stderr:", res.stderr[-1000:] if len(res.stderr) > 1000 else res.stderr)

print("\n=== 4. RESTARTING WORKERS ON ALL PODS ===")
worker_kill_script = """
import os, signal
current_pid = os.getpid()
for pid in os.listdir('/proc'):
    if pid.isdigit() and int(pid) > 1 and int(pid) != current_pid:
        try:
            with open(f'/proc/{pid}/cmdline', 'rb') as f:
                cmd = f.read()
                if b'insilos-bin' in cmd:
                    os.kill(int(pid), signal.SIGTERM)
        except Exception:
            pass
"""

for pod in pods:
    subprocess.run([
        "kubectl", "exec", "-n", "production", pod, "-c", "insilos", "--",
        "python3", "-c", worker_kill_script
    ], capture_output=True)
    print(f"[✓] Sent reload signal to workers on {pod}")

print("\n🎉 Deployment completed successfully!")
