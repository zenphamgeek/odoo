#!/usr/bin/env python3
"""
tools/sync_logos_to_assets_library.py
Indexes and registers all canonical brand logos (ZenCode & INSILOS) into Odoo's 
Database Assets & Media Library (ir_attachment) with public=True.
Allows editors to seamlessly pick and drag logos from the Odoo Media Dialog.
Supports local (127.0.0.1:5434) and production pod environments.
"""

import os
import sys
import hashlib
import json
import psycopg2
import mimetypes

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
candidate_dirs = [
    os.path.join(BASE_DIR, 'enterprise', 'insilos_website', 'static', 'src', 'img', 'assets_library'),
    "/app/insilos/enterprise/insilos_website/static/src/img/assets_library",
    "/app/insilos/apps/insilos_website/static/src/img/assets_library",
    "/home/zen/O20/enterprise/insilos_website/static/src/img/assets_library",
]
ASSETS_DIR = candidate_dirs[0]
for cand in candidate_dirs:
    if os.path.exists(cand):
        ASSETS_DIR = cand
        break

def get_mimetype(filename):
    if filename.endswith('.svg'):
        return 'image/svg+xml'
    elif filename.endswith('.png'):
        return 'image/png'
    elif filename.endswith('.webp'):
        return 'image/webp'
    elif filename.endswith('.jpg') or filename.endswith('.jpeg'):
        return 'image/jpeg'
    elif filename.endswith('.ico'):
        return 'image/x-icon'
    mime, _ = mimetypes.guess_type(filename)
    return mime or 'application/octet-stream'

def format_title(category, filename):
    base, ext = os.path.splitext(filename)
    clean = base.replace('-', ' ').replace('_', ' ').title()
    prefix = '[Assets Library]'
    cat_tag = category.upper()
    return f"{prefix} [{cat_tag}] {clean} ({ext.lstrip('.').upper()})"

def collect_assets():
    assets = []
    if not os.path.exists(ASSETS_DIR):
        print(f"[!] Assets dir not found: {ASSETS_DIR}")
        return assets

    for cat in sorted(os.listdir(ASSETS_DIR)):
        cat_path = os.path.join(ASSETS_DIR, cat)
        if not os.path.isdir(cat_path):
            continue
        for root, _, files in os.walk(cat_path):
            for file in sorted(files):
                if file.startswith('.'):
                    continue
                file_path = os.path.join(root, file)
                rel_url = '/insilos_website/static/src/img/assets_library/' + os.path.relpath(file_path, ASSETS_DIR).replace('\\', '/')
                title = format_title(cat, file)
                mimetype = get_mimetype(file)
                size = os.path.getsize(file_path)
                with open(file_path, 'rb') as f:
                    content_bytes = f.read()
                checksum = hashlib.sha1(content_bytes).hexdigest()
                assets.append({
                    'category': cat,
                    'name': title,
                    'filename': file,
                    'url': rel_url,
                    'mimetype': mimetype,
                    'bytes': content_bytes,
                    'checksum': checksum,
                    'size': size,
                    'file_path': file_path
                })
    return assets

def sync_to_db(host, port, user, password, dbname):
    print(f"[*] Connecting to {dbname} on {host}:{port} as {user}...")
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            dbname=dbname
        )
    except Exception as e:
        print(f"[!] Failed to connect to {dbname}: {e}")
        return False

    conn.autocommit = False
    cur = conn.cursor()

    assets = collect_assets()
    print(f"[*] Found {len(assets)} logo assets to register into Assets Library...")

    synced_count = 0
    updated_count = 0

    for item in assets:
        url = item['url']
        name = item['name']
        mimetype = item['mimetype']
        raw_bytes = item['bytes']
        size = item['size']
        checksum = item['checksum']

        # Check existing by url or name
        cur.execute("SELECT id FROM ir_attachment WHERE url = %s OR name = %s", (url, name))
        row = cur.fetchone()

        if row:
            att_id = row[0]
            cur.execute("""
                UPDATE ir_attachment
                SET name = %s,
                    mimetype = %s,
                    url = %s,
                    public = true,
                    type = 'url',
                    db_datas = %s,
                    file_size = %s,
                    checksum = %s,
                    write_date = NOW()
                WHERE id = %s
            """, (name, mimetype, url, psycopg2.Binary(raw_bytes), size, checksum, att_id))
            updated_count += 1
        else:
            cur.execute("""
                INSERT INTO ir_attachment (
                    name, mimetype, url, public, type, res_model, db_datas, file_size, checksum, create_date, write_date
                ) VALUES (
                    %s, %s, %s, true, 'url', 'ir.ui.view', %s, %s, %s, NOW(), NOW()
                ) RETURNING id
            """, (name, mimetype, url, psycopg2.Binary(raw_bytes), size, checksum))
            att_id = cur.fetchone()[0]
            synced_count += 1

    conn.commit()
    conn.close()
    print(f"[✓] Database {dbname}: Registered {synced_count} new logos, updated {updated_count} logos in Assets Library.")
    return True

if __name__ == '__main__':
    target = sys.argv[1] if len(sys.argv) > 1 else 'local'
    if target == 'local':
        sync_to_db('127.0.0.1', 5434, 'odoo', '1NN0R1@2026', 'innoria_prod')
        sync_to_db('127.0.0.1', 5434, 'odoo', '1NN0R1@2026', 'odoo20_dev')
    elif target == 'prod_pod':
        sync_to_db(
            os.environ.get('DB_HOST', 'pgbouncer-service'),
            int(os.environ.get('DB_PORT', 6432)),
            os.environ.get('DB_USER', 'insilos'),
            os.environ.get('PGPASSWORD', ''),
            'innoria_prod'
        )
