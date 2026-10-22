#!/usr/bin/env python3
import subprocess
import os
import sys

NAMESPACE = "production"
CONTAINER = "innoria"
TAR_PATH = "/tmp/patch_js_bundle.tar.gz"

def run_cmd(cmd, check=True):
    print(f"[*] Running: {cmd}")
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and res.returncode != 0:
        raise RuntimeError(f"Command failed ({res.returncode}): {cmd}\n{res.stderr}")
    return res

# 1. Discover pods
pod_out = run_cmd(f"kubectl get pods -n {NAMESPACE} -l app=innoria-prod --field-selector=status.phase=Running -o jsonpath='{{.items[*].metadata.name}}'")
pods = [p.strip() for p in pod_out.stdout.split() if p.strip()]
print(f"[✓] Found {len(pods)} running innoria-prod pods: {pods}")

# 2. Deploy to all pods
for pod in pods:
    print(f"\n--- Deploying to {pod} ---")
    run_cmd(f"kubectl cp -n {NAMESPACE} -c {CONTAINER} {TAR_PATH} {pod}:/tmp/patch_js_bundle.tar.gz")
    
    # Extract to /app/insilos and to /var/lib/insilos/filestore/custom_addons
    extract_script = f"""
    tar -xzf /tmp/patch_js_bundle.tar.gz -C /app/insilos/ &&
    mkdir -p /var/lib/insilos/filestore/custom_addons/insilos_theme_genesis &&
    mkdir -p /var/lib/insilos/filestore/custom_addons/insilos_sap_fiori &&
    mkdir -p /var/lib/insilos/filestore/custom_addons/insilos_al2c &&
    mkdir -p /var/lib/insilos/filestore/custom_addons/insilos_logistics_idp &&
    mkdir -p /var/lib/insilos/filestore/custom_addons/insilos_market_terminal &&
    mkdir -p /var/lib/insilos/filestore/custom_addons/insilos_website &&
    cp -r /app/insilos/enterprise/insilos_theme_genesis/* /var/lib/insilos/filestore/custom_addons/insilos_theme_genesis/ 2>/dev/null || true &&
    cp -r /app/insilos/addons/insilos_sap_fiori/* /var/lib/insilos/filestore/custom_addons/insilos_sap_fiori/ 2>/dev/null || true &&
    cp -r /app/insilos/addons/insilos_al2c/* /var/lib/insilos/filestore/custom_addons/insilos_al2c/ 2>/dev/null || true &&
    cp -r /app/insilos/enterprise/insilos_logistics_idp/* /var/lib/insilos/filestore/custom_addons/insilos_logistics_idp/ 2>/dev/null || true &&
    cp -r /app/insilos/enterprise/insilos_market_terminal/* /var/lib/insilos/filestore/custom_addons/insilos_market_terminal/ 2>/dev/null || true &&
    cp -r /app/insilos/enterprise/insilos_website/* /var/lib/insilos/filestore/custom_addons/insilos_website/ 2>/dev/null || true &&
    rm -f /tmp/patch_js_bundle.tar.gz
    """
    run_cmd(f"kubectl exec -n {NAMESPACE} {pod} -c {CONTAINER} -- sh -c '{extract_script}'")
    print(f"[✓] Extracted & synchronized files on {pod}")

# 3. Purge cached asset bundles in innoria_prod DB
print("\n--- Purging cached asset attachments in innoria_prod ---")
lead_pod = pods[0]
purge_sql_script = """
import os, psycopg2
conn = psycopg2.connect(
    host=os.environ.get('DB_HOST', 'pgbouncer-service'),
    port=int(os.environ.get('DB_PORT', 6432)),
    user=os.environ.get('DB_USER', 'insilos'),
    password=os.environ.get('PGPASSWORD'),
    dbname='innoria_prod'
)
cur = conn.cursor()
cur.execute("DELETE FROM ir_attachment WHERE url LIKE '/web/assets/%web.assets_web%';")
print(f"Purged {cur.rowcount} cached web.assets_web attachments.")
conn.commit()
conn.close()
"""
res = subprocess.run([
    "kubectl", "exec", "-n", NAMESPACE, lead_pod, "-c", CONTAINER, "--",
    "python3", "-c", purge_sql_script
], capture_output=True, text=True)
print(res.stdout)
if res.stderr:
    print("Stderr:", res.stderr)

# 4. SIGHUP reload all pods
print("\n--- Sending SIGHUP reload to master process on all pods ---")
reload_script = "python3 -c 'import os, signal; os.kill(1, signal.SIGHUP)'"
for pod in pods:
    run_cmd(f"kubectl exec -n {NAMESPACE} {pod} -c {CONTAINER} -- sh -c \"{reload_script}\"")
    print(f"[✓] SIGHUP signal delivered to {pod}")

print("\n[✓] Deployment & cache purge completed successfully!")
