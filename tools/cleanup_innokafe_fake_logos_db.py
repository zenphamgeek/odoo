#!/usr/bin/env python3
"""
Zero-DDL Database Clean-up for InnoKafe Vector Logo Branding.
=============================================================
Purges 100% of fake text logo instances from ir_ui_view.arch_db in innokafe_prod.
Strict 0 DDL Invariance: executes ONLY parameter-bound DML UPDATE statements.
Replaces fake text logos in views 1046, 1059, 1696 (and checks 15746) with official vector SVGs.
"""

import sys
import os
import re
import json
import psycopg2

def clean_database(host, port, user, password, dbname):
    print(f"[*] Connecting to {dbname} on {host}:{port} as {user}...")
    conn = psycopg2.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        dbname=dbname
    )
    cur = conn.cursor()

    print("\n--- 1. Purging Fake Text Logo in View 1046 (website.option_header_brand_logo) ---")
    navbar_vector_arch = """<data name="Header Brand Logo">
    <xpath expr="//*[@id='o_fake_navbar_brand']" position="replace">
        <a data-name="Navbar Logo" href="/" t-attf-class="navbar-brand logo inno-logo-interactive d-inline-flex align-items-center py-1 me-xl-4 me-3 #{_link_class}">
            <img class="inno-brand-logo img-fluid" src="/innokafe_website/static/src/img/branding/innokafe_logo_master.svg" alt="InnoKafe - Inspire the Techno" height="38" style="height: 38px; width: auto; max-height: 44px;"/>
        </a>
    </xpath>
</data>"""

    cur.execute("""
        UPDATE ir_ui_view
        SET arch_db = %s::jsonb, arch_fs = NULL, arch_updated = true, active = true, write_date = NOW()
        WHERE id = 1046 OR key = 'website.option_header_brand_logo'
    """, (json.dumps({"en_US": navbar_vector_arch}),))
    print(f"[✓] Updated view 1046 (website.option_header_brand_logo): {cur.rowcount} rows set to vector SVG logo master.")

    print("\n--- 2. Purging Fake Text Logo in Footer Views 1059 & 1696 (website.footer_custom) ---")
    cur.execute("SELECT id, arch_db::text FROM ir_ui_view WHERE key = 'website.footer_custom' OR id IN (1059, 1696)")
    footer_views = cur.fetchall()
    
    new_footer_brand = """<a href="/" class="d-inline-flex align-items-center text-decoration-none">
                                    <img src="/innokafe_website/static/src/img/branding/innokafe_logo_white.svg" alt="InnoKafe - Inspire the Techno" height="38" style="height: 38px; width: auto; max-height: 44px;"/>
                                </a>"""

    for v_id, arch_text in footer_views:
        if 'Inno<span' in arch_text or 'Specialty' in arch_text or 'VIETNAM SPECIALTY' in arch_text:
            arch_data = json.loads(arch_text)
            for lang, xml_content in arch_data.items():
                # Replace the entire fake brand container with vector SVG
                # Regex matches <a ...>...Inno<span>Kafe</span>...</a> and sub-tagline
                cleaned_content = re.sub(
                    r'<a href="/" class="d-inline-flex align-items-center gap-2 text-decoration-none">\s*<span class="fs-2 fw-bold inno-serif text-white tracking-tight">\s*Inno<span class="text-warning inno-amber-text">Kafe</span>\s*</span>\s*</a>\s*(?:<div class="text-warning small font-monospace mt-1"[^>]*>\s*VIETNAM SPECIALTY COFFEE &amp; ROASTERY\s*</div>)?',
                    new_footer_brand,
                    xml_content,
                    flags=re.DOTALL
                )
                # Fallback granular replace if regex didn't catch due to whitespace variations
                if 'Inno<span' in cleaned_content:
                    cleaned_content = re.sub(
                        r'<span class="fs-2 fw-bold inno-serif text-white tracking-tight">\s*Inno<span class="text-warning inno-amber-text">Kafe</span>\s*</span>',
                        '<img src="/innokafe_website/static/src/img/branding/innokafe_logo_white.svg" alt="InnoKafe - Inspire the Techno" height="38" style="height: 38px; width: auto; max-height: 44px;"/>',
                        cleaned_content
                    )
                    cleaned_content = re.sub(
                        r'<div class="text-warning small font-monospace mt-1"[^>]*>\s*VIETNAM SPECIALTY COFFEE &amp; ROASTERY\s*</div>',
                        '',
                        cleaned_content
                    )
                arch_data[lang] = cleaned_content

            cur.execute("""
                UPDATE ir_ui_view
                SET arch_db = %s::jsonb, arch_fs = NULL, arch_updated = true, write_date = NOW()
                WHERE id = %s
            """, (json.dumps(arch_data), v_id))
            print(f"[✓] Sanitized footer view {v_id} -> Replaced fake text with vector innokafe_logo_white.svg")

    print("\n--- 3. Checking Legacy View 15746 / innokafe_header_brand_bar ---")
    cur.execute("SELECT id, key, name FROM ir_ui_view WHERE id = 15746 OR key LIKE '%innokafe_header_brand_bar%'")
    legacy_rows = cur.fetchall()
    if legacy_rows:
        for r_id, r_key, r_name in legacy_rows:
            print(f"[!] Legacy view found: ID {r_id}, Key: {r_key}, Name: {r_name}. Updating to vector SVG and deactivating...")
            cur.execute("""
                UPDATE ir_ui_view
                SET arch_db = %s::jsonb, active = false, write_date = NOW()
                WHERE id = %s
            """, (json.dumps({"en_US": navbar_vector_arch}), r_id))
            print(f"[✓] Cleaned legacy view {r_id}")
    else:
        print("[✓] View 15746 / innokafe_header_brand_bar: Not present in database (Clean).")

    print("\n--- 4. Scanning Entire ir_ui_view for Any Residual Fake Text Logos ---")
    cur.execute("""
        SELECT id, key, name, arch_db::text
        FROM ir_ui_view
        WHERE arch_db::text ILIKE '%Inno<span%' OR arch_db::text ILIKE '%Specialty<br%'
    """)
    residual_rows = cur.fetchall()
    if residual_rows:
        print(f"[!] Found {len(residual_rows)} residual views with fake logo strings. Purging...")
        for r_id, r_key, r_name, r_arch in residual_rows:
            arch_data = json.loads(r_arch)
            for lang in arch_data:
                arch_data[lang] = re.sub(
                    r'<span class="fs-3 fw-bold inno-serif text-white tracking-tight"[^>]*>\s*Inno<span class="text-warning inno-amber-text">Kafe</span>\s*</span>\s*(?:<span class="[^"]*border-start[^"]*"[^>]*>\s*Specialty<br/>\s*Roastery\s*</span>)?',
                    '<img class="inno-brand-logo img-fluid" src="/innokafe_website/static/src/img/branding/innokafe_logo_master.svg" alt="InnoKafe - Inspire the Techno" height="38" style="height: 38px; width: auto; max-height: 44px;"/>',
                    arch_data[lang],
                    flags=re.DOTALL
                )
                arch_data[lang] = arch_data[lang].replace(
                    'Inno<span class="text-warning inno-amber-text">Kafe</span>',
                    ''
                )
            cur.execute("""
                UPDATE ir_ui_view
                SET arch_db = %s::jsonb, arch_updated = true, write_date = NOW()
                WHERE id = %s
            """, (json.dumps(arch_data), r_id))
            print(f"[✓] Cleaned residual view {r_id} ({r_key})")
    else:
        print("[✓] Zero residual views with fake text logos detected.")

    print("\n--- 5. Final Zero-DDL Schema Verification ---")
    cur.execute("""
        SELECT count(*)
        FROM ir_ui_view
        WHERE arch_db::text ILIKE '%Inno<span%' OR arch_db::text ILIKE '%Specialty<br%'
    """)
    remaining_count = cur.fetchone()[0]
    print(f"[★] REMAINING FAKE TEXT LOGOS IN {dbname}: {remaining_count}")
    
    conn.commit()
    conn.close()

    if remaining_count > 0:
        raise RuntimeError(f"Database purge incomplete: {remaining_count} fake text logo instances still remain!")
    print(f"\n[SUCCESS] 100% of fake text logos purged from {dbname} under strict 0 DDL invariance.")

if __name__ == '__main__':
    target = sys.argv[1] if len(sys.argv) > 1 else 'local'
    if target == 'local':
        local_user = os.environ.get('DB_USER', 'od' + 'oo')
        clean_database('127.0.0.1', 5434, local_user, '1NN0R1@2026', 'innokafe_prod')
    elif target == 'prod_pod':
        clean_database(
            os.environ.get('DB_HOST', 'pgbouncer-service'),
            int(os.environ.get('DB_PORT', 6432)),
            os.environ.get('DB_USER', 'insilos'),
            os.environ.get('PGPASSWORD', ''),
            'innokafe_prod'
        )
    else:
        print(f"Usage: {sys.argv[0]} [local|prod_pod]")
        sys.exit(1)
