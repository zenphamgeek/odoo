#!/usr/bin/env python3
"""
tools/deploy_innoria_website.py
=============================================================================
Deploys elevated Innoria 3D Website and all 7 Deep Enterprise Pages to
https://innoria.insilos.com (Database: innoria_prod on K8s cluster).
=============================================================================
"""

import base64
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from html import escape

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
    ("enterprise/insilos_website/views/innoria_pages.xml",
     "views/innoria_pages.xml"),
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

def extract_templates_from_file(xml_path, module='insilos_website'):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    templates = {}
    for tmpl in root.findall(".//template"):
        tmpl_id = tmpl.attrib.get("id")
        tmpl_name = tmpl.attrib.get("name", tmpl_id)
        attr_name = escape(tmpl_name, quote=True)
        key = f"{module}.{tmpl_id}" if "." not in tmpl_id else tmpl_id
        inner_xml = "".join(ET.tostring(child, encoding='unicode') for child in tmpl)
        inner_xml = re.sub(r'&(?!(?:amp|lt|gt|quot|apos|#\d+|#x[0-9a-fA-F]+);)', '&amp;', inner_xml)
        arch = f'<t name="{attr_name}" t-name="{key}">\n{inner_xml}\n</t>'
        templates[tmpl_id] = {
            "name": tmpl_name,
            "key": key,
            "arch": arch,
            "inner_xml": inner_xml,
        }
    return templates

def upsert_view_arch(key, name, arch, view_ids=None):
    """
    Safely writes view arch to DB by sending JSON payload via stdin to DB_POD
    and updating or inserting ir_ui_view records.
    """
    safe_key = key.replace('.', '_').replace('/', '_')
    tmp_path = f"/tmp/arch_{safe_key}.json"
    json_bytes = json.dumps({"en_US": arch}).encode('utf-8')

    cp_cmd = ['kubectl', '-n', DB_NAMESPACE, 'exec', '-i', DB_POD, '-c', 'postgres', '--', 'tee', tmp_path]
    subprocess.run(cp_cmd, input=json_bytes, check=True, capture_output=True)

    # 1. If explicit view IDs are given, update them
    if view_ids:
        id_list = ",".join(str(i) for i in view_ids)
        sql_update_ids = f"""
        UPDATE ir_ui_view
        SET arch_db = (SELECT pg_read_file('{tmp_path}')::jsonb),
            write_date = NOW()
        WHERE id IN ({id_list});
        """
        run_psql_command(sql_update_ids)
        log(f"    Updated explicit view ID(s) [{id_list}] for key='{key}'", 'SUCCESS')

    # 2. Check if a view exists with this key
    sql_check = f"SELECT id FROM ir_ui_view WHERE key = '{key}' LIMIT 1;"
    check_res = run_psql_command(sql_check).strip().split('\n')
    existing_id = None
    for line in check_res:
        line = line.strip()
        if line.isdigit():
            existing_id = int(line)
            break

    if existing_id:
        sql_update = f"""
        UPDATE ir_ui_view
        SET arch_db = (SELECT pg_read_file('{tmp_path}')::jsonb),
            name = '{name.replace("'", "''")}',
            write_date = NOW()
        WHERE id = {existing_id};
        """
        run_psql_command(sql_update)
        log(f"    Updated view id={existing_id} key='{key}'", 'SUCCESS')
        return existing_id
    else:
        sql_insert = f"""
        INSERT INTO ir_ui_view (name, type, mode, priority, website_id, key, arch_db, write_date, create_date)
        VALUES ('{name.replace("'", "''")}', 'qweb', 'primary', 99, 1, '{key}',
                (SELECT pg_read_file('{tmp_path}')::jsonb), NOW(), NOW())
        RETURNING id;
        """
        ins_res = run_psql_command(sql_insert).strip().split('\n')
        new_id = None
        for line in ins_res:
            line = line.strip()
            if line.isdigit():
                new_id = int(line)
                break
        if new_id:
            xml_name = key.split('.')[-1]
            module_name = key.split('.')[0] if '.' in key else 'insilos_website'
            sql_insert_model_data = f"""
            INSERT INTO ir_model_data (name, module, model, res_id, noupdate, create_date, write_date)
            VALUES ('{xml_name}', '{module_name}', 'ir.ui.view', {new_id}, true, NOW(), NOW())
            ON CONFLICT DO NOTHING;
            """
            run_psql_command(sql_insert_model_data)
            log(f"    Inserted new view id={new_id} key='{key}'", 'SUCCESS')
        return new_id

def upsert_website_page(url_str, name_str, view_id):
    """
    Ensures website_page table has an active record for the given route.
    """
    sql_check = f"SELECT id FROM website_page WHERE url->>'en_US' = '{url_str}' LIMIT 1;"
    res = run_psql_command(sql_check).strip().split('\n')
    page_id = None
    for line in res:
        line = line.strip()
        if line.isdigit():
            page_id = int(line)
            break

    if page_id:
        sql_update = f"""
        UPDATE website_page
        SET view_id = {view_id},
            name = jsonb_build_object('en_US', '{name_str.replace("'", "''")}'),
            is_published = true,
            website_indexed = true,
            write_date = NOW()
        WHERE id = {page_id};
        """
        run_psql_command(sql_update)
        log(f"    Updated website_page id={page_id} url='{url_str}' -> view_id={view_id}", 'SUCCESS')
    else:
        sql_insert = f"""
        INSERT INTO website_page (url, name, view_id, is_published, website_indexed, create_date, write_date)
        VALUES (
            jsonb_build_object('en_US', '{url_str}'),
            jsonb_build_object('en_US', '{name_str.replace("'", "''")}'),
            {view_id},
            true,
            true,
            NOW(),
            NOW()
        );
        """
        run_psql_command(sql_insert)
        log(f"    Created website_page url='{url_str}' -> view_id={view_id}", 'SUCCESS')

def apply_database_updates():
    log("Applying comprehensive database updates to innoria_prod...")

    # 1. Update website table: domain='innoria.insilos.com', name='INNORIA | Tailored Technology'
    sql_website = """
    UPDATE website
    SET name = 'INNORIA | Tailored Technology',
        domain = 'innoria.insilos.com'
    WHERE id = 1;
    """
    run_psql_command(sql_website)
    log("  Updated website record id = 1: domain='innoria.insilos.com', name='INNORIA | Tailored Technology'", 'SUCCESS')

    # 2. Extract templates from both XML files
    home_tmpls = extract_templates_from_file("enterprise/insilos_website/views/innoria_homepage.xml")
    pages_tmpls = extract_templates_from_file("enterprise/insilos_website/views/innoria_pages.xml")

    # 3. Upsert Navbar & Footer
    log("  Upserting reusable Navbar & Footer...")
    if 'innoria_navbar' in home_tmpls:
        upsert_view_arch('insilos_website.innoria_navbar', 'INNORIA Navbar', home_tmpls['innoria_navbar']['arch'])
    if 'innoria_footer' in home_tmpls:
        upsert_view_arch('insilos_website.innoria_footer', 'INNORIA Footer', home_tmpls['innoria_footer']['arch'])

    # 4. Upsert Homepage Templates
    log("  Upserting Homepage templates...")
    if 'innoria_homepage_template' in home_tmpls:
        home_arch = home_tmpls['innoria_homepage_template']['arch']
        # Update view 15304 (insilos_website.insilos_homepage)
        upsert_view_arch('insilos_website.insilos_homepage', 'INNORIA — Tailored Technology', home_arch, view_ids=[15304])
        # Update view 980 and 1688 (website.homepage)
        website_home_arch = f'<t name="Home" t-name="website.homepage">\n{home_tmpls["innoria_homepage_template"]["inner_xml"]}\n</t>'
        upsert_view_arch('website.homepage', 'Home', website_home_arch, view_ids=[980, 1688])
        # Upsert insilos_website.innoria_homepage_template
        upsert_view_arch('insilos_website.innoria_homepage_template', 'Innoria — Tailored Technology', home_arch)

    # 5. Upsert All 7 Deep Enterprise Pages
    log("  Upserting 7 Deep Enterprise Page Templates...")

    # Page 1: About Us / Company
    if 'insilos_about_page' in pages_tmpls:
        about = pages_tmpls['insilos_about_page']
        vid = upsert_view_arch(about['key'], about['name'], about['arch'], view_ids=[15321])
        upsert_website_page('/about', about['name'], vid or 15321)

    # Page 2: Platform / Artificial Intelligence Platform
    if 'insilos_platform_page' in pages_tmpls:
        platform = pages_tmpls['insilos_platform_page']
        vid = upsert_view_arch(platform['key'], platform['name'], platform['arch'], view_ids=[15305])
        upsert_website_page('/platform', platform['name'], vid or 15305)

    # Page 3: No-Code Platform (DIGIFORCE)
    if 'innoria_digiforce_page' in pages_tmpls:
        nocode = pages_tmpls['innoria_digiforce_page']
        vid = upsert_view_arch(nocode['key'], nocode['name'], nocode['arch'])
        if vid:
            upsert_website_page('/no-code-platform', nocode['name'], vid)

    # Page 4: Blockchain Platform (MOJOVERSE)
    if 'innoria_blockchain_page' in pages_tmpls:
        bc = pages_tmpls['innoria_blockchain_page']
        vid = upsert_view_arch(bc['key'], bc['name'], bc['arch'])
        if vid:
            upsert_website_page('/blockchain', bc['name'], vid)

    # Page 5: Solutions (AI-Enhanced ERP)
    if 'insilos_solutions_page' in pages_tmpls:
        sol = pages_tmpls['insilos_solutions_page']
        vid = upsert_view_arch(sol['key'], sol['name'], sol['arch'], view_ids=[15306])
        upsert_website_page('/solutions', sol['name'], vid or 15306)

    # Page 6: Industries (Ultra AI Vision)
    if 'insilos_industries_page' in pages_tmpls:
        ind = pages_tmpls['insilos_industries_page']
        vid = upsert_view_arch(ind['key'], ind['name'], ind['arch'], view_ids=[15312])
        upsert_website_page('/industries', ind['name'], vid or 15312)

    # Page 7: Contact Us (Executive Workshop Blueprint)
    if 'innoria_contactus' in pages_tmpls:
        contact = pages_tmpls['innoria_contactus']
        # Deactivate conflicting website_crm inherited view if present
        sql_deact_crm = "UPDATE ir_ui_view SET active = false WHERE id = 2595;"
        run_psql_command(sql_deact_crm)
        # Upsert insilos_website.innoria_contactus
        vid = upsert_view_arch(contact['key'], contact['name'], contact['arch'])
        upsert_website_page('/contactus', contact['name'], vid or 15750)

    # 6. Synchronize website_page publishing state
    sql_pages_publish = """
    UPDATE website_page
    SET is_published = true
    WHERE id IN (2, 3, 5, 8, 9, 10, 13);
    """
    run_psql_command(sql_pages_publish)
    log("  All core website_page records set to published.", 'SUCCESS')

    # 7. Synchronize official Innoria SVG logo & favicon to ir_attachment
    log("  Synchronizing official Innoria logo & favicon to database ir_attachment...")
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
    cp_logo = ['kubectl', '-n', DB_NAMESPACE, 'exec', '-i', DB_POD, '-c', 'postgres', '--', 'tee', '/tmp/update_logo.sql']
    subprocess.run(cp_logo, input=sql_logo_attachments.encode('utf-8'), check=True, capture_output=True)
    run_psql_command("/tmp/update_logo.sql", as_file=True)
    log("  Updated ir_attachment logo and favicon records.", 'SUCCESS')

    # 8. Purge compiled asset bundles so frontend recompiles immediately
    log("  Purging compiled web assets on innoria_prod...")
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
    log("Warming up frontend assets across key routes on https://innoria.insilos.com...")
    import urllib.request
    import re
    import time
    time.sleep(3)
    
    routes_to_warm = [
        "/",
        "/about",
        "/platform",
        "/no-code-platform",
        "/blockchain",
        "/solutions",
        "/industries",
        "/contactus"
    ]
    
    seen_assets = set()
    for route in routes_to_warm:
        full_route = f"https://innoria.insilos.com{route}"
        log(f"  Warming route {full_route}...")
        try:
            req = urllib.request.Request(full_route, headers={'User-Agent': 'InsilosDeploy/1.0'})
            with urllib.request.urlopen(req, timeout=30) as resp:
                html = resp.read().decode('utf-8', errors='ignore')
                log(f"    Loaded {route} -> HTTP {resp.status}", 'SUCCESS')
            
            asset_urls = re.findall(r'href="(/web/assets/[^"]+\.css)"', html) + re.findall(r'src="(/web/assets/[^"]+\.js)"', html)
            asset_urls += re.findall(r'data-src="(/web/assets/[^"]+\.js)"', html)
            for url in set(asset_urls):
                if url not in seen_assets:
                    seen_assets.add(url)
                    full_url = f"https://innoria.insilos.com{url}"
                    req_asset = urllib.request.Request(full_url, headers={'User-Agent': 'InsilosDeploy/1.0'})
                    try:
                        with urllib.request.urlopen(req_asset, timeout=45) as aresp:
                            pass
                    except Exception as e:
                        log(f"      Warning loading asset {url}: {e}", 'WARN')
        except Exception as e:
            log(f"    Warning warming {route}: {e}", 'WARN')

def main():
    log("==================================================", 'INFO')
    log("Starting Innoria Enterprise Multi-Page Deployment...", 'INFO')
    log("==================================================", 'INFO')
    
    pods = get_running_pods()
    log(f"Detected {len(pods)} running pods: {', '.join(pods)}")
    
    # 1. Sync code and templates to all pods
    sync_files_to_pods(pods)

    # 2. Normalize timestamps
    normalize_file_timestamps(pods)

    # 3. Apply comprehensive DB updates
    apply_database_updates()

    # 4. Reload workers
    reload_workers(pods)

    # 5. Warm up frontend and all pages
    warmup_asset_bundles()

    log("==================================================", 'SUCCESS')
    log("Innoria Enterprise Deployment completed successfully!", 'SUCCESS')
    log("==================================================", 'SUCCESS')

if __name__ == '__main__':
    main()
