#!/usr/bin/env python3
"""
tools/deploy_innoria_website.py
=============================================================================
Deploys elevated Innoria 3D Website and branding to https://innoria.insilos.com
(Database: innoria_prod on K8s cluster).
=============================================================================
"""

import base64
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET

POD_LABEL = 'app=insilos-saas'
NAMESPACE = 'production'
DB_NAMESPACE = 'database'
DB_POD = 'postgres-0'
DB_NAME = 'innoria_prod'

# Base code and views
BASE_FILES = [
    ("enterprise/insilos_website/controllers/main.py",
     "controllers/main.py"),
    ("enterprise/insilos_website/static/src/js/innoria_topology_3d.js",
     "static/src/js/innoria_topology_3d.js"),
    ("enterprise/insilos_website/static/src/scss/innoria_theme.scss",
     "static/src/scss/innoria_theme.scss"),
    ("enterprise/insilos_website/static/src/img/snippets_thumbs/s_innoria_3d_topology.svg",
     "static/src/img/snippets_thumbs/s_innoria_3d_topology.svg"),
    ("enterprise/insilos_website/views/snippets_3d.xml",
     "views/snippets_3d.xml"),
    ("enterprise/insilos_website/views/innoria_homepage.xml",
     "views/innoria_homepage.xml"),
    ("enterprise/insilos_website/__manifest__.py",
     "__manifest__.py"),
]

# Authentic Innoria image assets extracted from innoria.com
INNORIA_IMG_DIR = "enterprise/insilos_website/static/src/img/innoria"
INNORIA_IMAGES = [
    "architecture_innoria_platform_grey.svg",
    "banner_digital_transformation.jpg",
    "client_a_gray.png",
    "client_b_gray.png",
    "client_d_gray.png",
    "coding_ai_nlp_data.jpg",
    "favicon.ico",
    "group_52424.webp",
    "header_innoria_banner.svg",
    "importance_of_ai_services.webp",
    "innoria_logo_grayscale.svg",
    "logo_innoria_eco_1.webp",
    "logo_innoria_eco_2.webp",
    "logo_innoria_export.webp",
    "logo_innoria_header.svg",
    "team_advisory_photo.jpeg",
]

LOCAL_FILES = BASE_FILES + [
    (f"{INNORIA_IMG_DIR}/{img}", f"static/src/img/innoria/{img}")
    for img in INNORIA_IMAGES
]

def log(msg, level='INFO'):
    colors = {
        'INFO': '\033[94m[*]\033[0m',
        'SUCCESS': '\033[92m[✓]\033[0m',
        'WARN': '\033[93m[!]\033[0m',
        'ERROR': '\033[91m[✗]\033[0m',
    }
    print(f"{colors.get(level, '[*]')} {msg}")

def get_running_pods():
    cmd = [
        'kubectl', '-n', NAMESPACE, 'get', 'pods',
        '-l', POD_LABEL,
        '--field-selector=status.phase=Running',
        '-o', 'jsonpath={.items[*].metadata.name}'
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    pods = res.stdout.strip().split()
    if not pods:
        raise RuntimeError("No running pods found with label " + POD_LABEL)
    return pods

def sync_files_to_pods(pods):
    log(f"Syncing {len(LOCAL_FILES)} files ({len(INNORIA_IMAGES)} images + {len(BASE_FILES)} code/views) to {len(pods)} pod(s)...")
    for pod in pods:
        # Pre-create directory for images on both targets
        mkdir_cmd = [
            'kubectl', '-n', NAMESPACE, 'exec', pod, '-c', 'insilos', '--',
            'mkdir', '-p',
            '/app/insilos/apps/insilos_website/static/src/img/innoria',
            '/app/insilos/enterprise/insilos_website/static/src/img/innoria'
        ]
        subprocess.run(mkdir_cmd, check=True, capture_output=True)

        for local_file, rel_path in LOCAL_FILES:
            if not os.path.exists(local_file):
                raise FileNotFoundError(f"Local file not found: {local_file}")
            
            # Copy to both /app/insilos/apps/insilos_website and /app/insilos/enterprise/insilos_website
            for target_base in ['/app/insilos/apps/insilos_website', '/app/insilos/enterprise/insilos_website']:
                dest = f"{target_base}/{rel_path}"
                cmd = [
                    'kubectl', '-n', NAMESPACE, 'cp',
                    local_file, f"{pod}:{dest}",
                    '-c', 'insilos'
                ]
                subprocess.run(cmd, check=True, capture_output=True)
        log(f"  Synchronized files to {pod}", 'SUCCESS')
    log("All files successfully synchronized to all application pods (apps & enterprise).", 'SUCCESS')

def extract_full_template_xml():
    xml_path = "enterprise/insilos_website/views/innoria_homepage.xml"
    tree = ET.parse(xml_path)
    root = tree.getroot()
    tmpl = root.find(".//template[@id='innoria_homepage_template']")
    if tmpl is None:
        raise ValueError("Could not find template innoria_homepage_template in " + xml_path)

    # Extract all children inside <template id="innoria_homepage_template">
    inner_xml = "".join(ET.tostring(child, encoding='unicode') for child in tmpl)
    return inner_xml

def build_view_arch_insilos_homepage(inner_xml):
    arch = f'''<t name="INNORIA — Tailored Technology" t-name="insilos_website.insilos_homepage">
{inner_xml}
</t>'''
    return arch

def build_view_arch_website_homepage(inner_xml):
    arch = f'''<t name="Home" t-name="website.homepage">
{inner_xml}
</t>'''
    return arch

def build_view_arch_innoria_template(inner_xml):
    arch = f'''<t name="Innoria — Tailored Technology" t-name="insilos_website.innoria_homepage_template">
{inner_xml}
</t>'''
    return arch

def run_psql_command(sql, as_file=False):
    if as_file:
        cmd = [
            'kubectl', '-n', DB_NAMESPACE, 'exec', DB_POD, '-c', 'postgres',
            '--', 'psql', '-U', 'postgres', '-d', DB_NAME, '-f', sql
        ]
    else:
        cmd = [
            'kubectl', '-n', DB_NAMESPACE, 'exec', DB_POD, '-c', 'postgres',
            '--', 'psql', '-U', 'postgres', '-d', DB_NAME, '-c', sql
        ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"psql failed: {res.stderr}\nQuery was: {sql[:200]}")
    return res.stdout

def apply_database_updates():
    inner_xml = extract_full_template_xml()
    arch_insilos = build_view_arch_insilos_homepage(inner_xml)
    arch_website = build_view_arch_website_homepage(inner_xml)
    arch_innoria = build_view_arch_innoria_template(inner_xml)

    log("Updating website metadata on innoria_prod...")
    # 1. Update website table: domain='innoria.insilos.com', name='INNORIA | Tailored Technology'
    sql_website = """
    UPDATE website
    SET name = 'INNORIA | Tailored Technology',
        domain = 'innoria.insilos.com'
    WHERE id = 1;
    """
    run_psql_command(sql_website)
    log("  Updated website record id = 1: domain='innoria.insilos.com', name='INNORIA | Tailored Technology'", 'SUCCESS')

    # 2. Update view 15304 (insilos_website.insilos_homepage)
    log("Updating view 15304 (insilos_website.insilos_homepage) with full template...")
    json_bytes_15304 = json.dumps({"en_US": arch_insilos}).encode('utf-8')
    cp_cmd1 = ['kubectl', '-n', DB_NAMESPACE, 'exec', '-i', DB_POD, '-c', 'postgres', '--', 'tee', '/tmp/arch_15304.json']
    subprocess.run(cp_cmd1, input=json_bytes_15304, check=True, capture_output=True)

    sql_view_15304 = """
    UPDATE ir_ui_view
    SET arch_db = (SELECT pg_read_file('/tmp/arch_15304.json')::jsonb),
        name = 'INNORIA — Tailored Technology',
        write_date = NOW()
    WHERE id = 15304;
    """
    run_psql_command(sql_view_15304)
    log("  Updated view 15304 (insilos_website.insilos_homepage) arch_db successfully.", 'SUCCESS')

    # 3. Update views 980 and 1688 (website.homepage)
    log("Updating views 980 and 1688 (website.homepage) on innoria_prod...")
    json_bytes_website = json.dumps({"en_US": arch_website}).encode('utf-8')
    cp_cmd2 = ['kubectl', '-n', DB_NAMESPACE, 'exec', '-i', DB_POD, '-c', 'postgres', '--', 'tee', '/tmp/arch_website.json']
    subprocess.run(cp_cmd2, input=json_bytes_website, check=True, capture_output=True)

    sql_views_website = """
    UPDATE ir_ui_view
    SET arch_db = (SELECT pg_read_file('/tmp/arch_website.json')::jsonb),
        write_date = NOW()
    WHERE id IN (980, 1688);
    """
    run_psql_command(sql_views_website)
    log("  Updated ir_ui_view IDs 980 and 1688 arch_db successfully.", 'SUCCESS')

    # 4. Upsert insilos_website.innoria_homepage_template in ir_ui_view
    log("Upserting insilos_website.innoria_homepage_template into ir_ui_view...")
    json_bytes_innoria = json.dumps({"en_US": arch_innoria}).encode('utf-8')
    cp_cmd3 = ['kubectl', '-n', DB_NAMESPACE, 'exec', '-i', DB_POD, '-c', 'postgres', '--', 'tee', '/tmp/arch_innoria.json']
    subprocess.run(cp_cmd3, input=json_bytes_innoria, check=True, capture_output=True)

    sql_check_view = "SELECT id FROM ir_ui_view WHERE key = 'insilos_website.innoria_homepage_template' LIMIT 1;"
    check_res = run_psql_command(sql_check_view).strip().split('\n')
    existing_id = None
    for line in check_res:
        line = line.strip()
        if line.isdigit():
            existing_id = int(line)
            break

    if existing_id:
        sql_update_template = f"""
        UPDATE ir_ui_view
        SET arch_db = (SELECT pg_read_file('/tmp/arch_innoria.json')::jsonb),
            name = 'Innoria — Tailored Technology',
            write_date = NOW()
        WHERE id = {existing_id};
        """
        run_psql_command(sql_update_template)
        log(f"  Updated existing view id={existing_id} (insilos_website.innoria_homepage_template)", 'SUCCESS')
    else:
        sql_insert_template = """
        INSERT INTO ir_ui_view (name, type, mode, priority, website_id, key, arch_db, write_date, create_date)
        VALUES ('Innoria — Tailored Technology', 'qweb', 'primary', 99, 1, 'insilos_website.innoria_homepage_template',
                (SELECT pg_read_file('/tmp/arch_innoria.json')::jsonb), NOW(), NOW())
        RETURNING id;
        """
        ins_res = run_psql_command(sql_insert_template).strip().split('\n')
        new_id = None
        for line in ins_res:
            line = line.strip()
            if line.isdigit():
                new_id = int(line)
                break
        if new_id:
            sql_insert_model_data = f"""
            INSERT INTO ir_model_data (name, module, model, res_id, noupdate, create_date, write_date)
            VALUES ('innoria_homepage_template', 'insilos_website', 'ir.ui.view', {new_id}, true, NOW(), NOW())
            ON CONFLICT DO NOTHING;
            """
            run_psql_command(sql_insert_model_data)
            log(f"  Inserted new view id={new_id} (insilos_website.innoria_homepage_template)", 'SUCCESS')

    # 5. Synchronize website_page table
    sql_page = """
    UPDATE website_page
    SET is_published = true,
        website_id = 1
    WHERE id IN (2, 5);
    """
    run_psql_command(sql_page)
    log("  Updated website_page records 2 and 5 to active.", 'SUCCESS')

    # 6. Synchronize official Innoria SVG logo & favicon to ir_attachment
    log("Synchronizing official Innoria logo & favicon to database ir_attachment...")
    logo_path = "enterprise/insilos_website/static/src/img/innoria/logo_innoria_header.svg"
    favicon_path = "enterprise/insilos_website/static/src/img/innoria/favicon.ico"

    with open(logo_path, 'rb') as f:
        logo_b64 = base64.b64encode(f.read()).decode('utf-8')
    with open(favicon_path, 'rb') as f:
        favicon_b64 = base64.b64encode(f.read()).decode('utf-8')

    sql_logo_attachments = f"""
    UPDATE ir_attachment
    SET db_datas = decode('{logo_b64}', 'base64'),
        store_fname = NULL,
        file_size = octet_length(decode('{logo_b64}', 'base64')),
        mimetype = 'image/svg+xml',
        write_date = NOW()
    WHERE id IN (41, 383, 3124, 3125, 3126);

    UPDATE ir_attachment
    SET db_datas = decode('{logo_b64}', 'base64'),
        store_fname = NULL,
        file_size = octet_length(decode('{logo_b64}', 'base64')),
        mimetype = 'image/svg+xml',
        write_date = NOW()
    WHERE id = 9;

    UPDATE ir_attachment
    SET db_datas = decode('{favicon_b64}', 'base64'),
        store_fname = NULL,
        file_size = octet_length(decode('{favicon_b64}', 'base64')),
        mimetype = 'image/x-icon',
        write_date = NOW()
    WHERE id = 42;
    """
    # Write SQL to /tmp/update_logo.sql via stdin to avoid ARG_MAX
    cp_logo = ['kubectl', '-n', DB_NAMESPACE, 'exec', '-i', DB_POD, '-c', 'postgres', '--', 'tee', '/tmp/update_logo.sql']
    subprocess.run(cp_logo, input=sql_logo_attachments.encode('utf-8'), check=True, capture_output=True)
    run_psql_command("/tmp/update_logo.sql", as_file=True)
    log("  Updated ir_attachment logo and favicon records with authentic Innoria data.", 'SUCCESS')

    # 7. Purge compiled asset bundles so frontend recompiles immediately
    log("Purging compiled web assets on innoria_prod...")
    sql_purge = """
    DELETE FROM ir_attachment
    WHERE name LIKE '%web.assets%' AND (res_model = 'ir.ui.view' OR res_model IS NULL);
    """
    out = run_psql_command(sql_purge)
    log(f"  {out.strip()}", 'SUCCESS')

def normalize_file_timestamps(pods):
    log("Normalizing file timestamps across pods to ensure identical bundle hashes...")
    fixed_time = "2026-10-05 12:00:00"
    for pod in pods:
        cmd = [
            'kubectl', '-n', NAMESPACE, 'exec', pod, '-c', 'insilos',
            '--', 'find', '/app/insilos/apps/insilos_website', '/app/insilos/enterprise/insilos_website',
            '-exec', 'touch', '-d', fixed_time, '{}', '+'
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        log(f"  Normalized timestamps on {pod}", 'SUCCESS')

def reload_workers(pods):
    log("Reloading Odoo worker processes across pods...")
    for pod in pods:
        cmd = [
            'kubectl', '-n', NAMESPACE, 'exec', pod, '-c', 'insilos',
            '--', 'python3', '-c',
            'import os, signal; os.kill(1, signal.SIGHUP); print("Sent SIGHUP to PID 1")'
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        log(f"  {pod}: {res.stdout.strip() or res.stderr.strip()}", 'SUCCESS')

def warmup_asset_bundles():
    log("Warming up frontend assets on https://innoria.insilos.com...")
    import urllib.request
    import re
    import time
    time.sleep(3)
    try:
        req = urllib.request.Request("https://innoria.insilos.com/", headers={'User-Agent': 'InsilosDeploy/1.0'})
        with urllib.request.urlopen(req, timeout=30) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
        
        asset_urls = re.findall(r'href="(/web/assets/[^"]+\.css)"', html) + re.findall(r'src="(/web/assets/[^"]+\.js)"', html)
        asset_urls += re.findall(r'data-src="(/web/assets/[^"]+\.js)"', html)
        for url in set(asset_urls):
            full_url = f"https://innoria.insilos.com{url}"
            log(f"  Warming up {url}...")
            req_asset = urllib.request.Request(full_url, headers={'User-Agent': 'InsilosDeploy/1.0'})
            try:
                with urllib.request.urlopen(req_asset, timeout=45) as aresp:
                    log(f"    Loaded {url} -> HTTP {aresp.status}", 'SUCCESS')
            except Exception as e:
                log(f"    Warning loading {url}: {e}", 'WARN')
    except Exception as e:
        log(f"  Warning during warmup: {e}", 'WARN')

def main():
    log("Starting Innoria Website Deployment...", 'INFO')
    pods = get_running_pods()
    log(f"Detected {len(pods)} running pods: {', '.join(pods)}")
    
    # 1. Sync code to pods
    sync_files_to_pods(pods)

    # 2. Normalize timestamps
    normalize_file_timestamps(pods)

    # 3. Apply DB updates
    apply_database_updates()

    # 4. Reload workers
    reload_workers(pods)

    # 5. Warm up asset bundles
    warmup_asset_bundles()

    log("Deployment completed successfully!", 'SUCCESS')

if __name__ == '__main__':
    main()
