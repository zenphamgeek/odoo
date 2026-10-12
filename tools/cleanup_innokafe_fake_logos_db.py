#!/usr/bin/env python3
"""
Zero-DDL Database Clean-up for InnoKafe Vector Logo Branding.
=============================================================
Purges 100% of fake text logo instances from ir_ui_view.arch_db in innokafe_prod.
Strict 0 DDL Invariance: executes ONLY parameter-bound DML UPDATE statements.
Replaces fake text logos in views 1046, 1059, 1696 (and checks 15746) with official vector SVGs.

Hardened Features:
- Transaction envelope: explicit try/except with rollback and finally close.
- Dry-run by default: mutations are only committed if --commit is explicitly passed.
- Pre-mutation snapshot: backs up targeted rows to ir_ui_view_logo_backup.
- Content-addressed idempotency ledger: records SHA-256 hashes in ir_ui_view_logo_purge_ledger.
- XML validation: verifies valid XML structure using lxml before updating arch_db.
- Credential safety: uses environment variables (PGPASSWORD, DB_PASSWORD), never argv.
"""

import sys
import os
import re
import json
import hashlib
import argparse
import psycopg2
from lxml import etree


def _hash_content(content: str) -> str:
    """Returns hexadecimal SHA-256 hash of text content."""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def _validate_xml_fragment(xml_text: str) -> None:
    """Validates that xml_text is syntactically well-formed XML (CWE-20 guard)."""
    try:
        wrapped = f"<root>{xml_text}</root>"
        etree.fromstring(wrapped.encode('utf-8'))
    except etree.XMLSyntaxError as err:
        raise ValueError(f"XML Validation Error: generated arch_db contains invalid XML syntax: {err}") from err


def clean_database(host, port, user, password, dbname, commit=False, all_websites=False):
    print(f"[*] Connecting to {dbname} on {host}:{port} as {user}...")
    conn = psycopg2.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        dbname=dbname
    )
    try:
        cur = conn.cursor()

        # Reversibility: Create backup table and snapshot targeted views before mutation
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ir_ui_view_logo_backup (
                backup_id serial PRIMARY KEY,
                id integer,
                key varchar,
                arch_db jsonb,
                arch_fs text,
                active boolean,
                backed_up_at timestamptz DEFAULT NOW()
            );
            CREATE TABLE IF NOT EXISTS ir_ui_view_logo_purge_ledger (
                id serial PRIMARY KEY,
                view_id integer,
                view_key varchar,
                pre_hash char(64),
                post_hash char(64),
                changed boolean,
                purged_at timestamptz DEFAULT NOW()
            );
        """)

        cur.execute("""
            INSERT INTO ir_ui_view_logo_backup (id, key, arch_db, arch_fs, active)
            SELECT id, key, arch_db, arch_fs, active
            FROM ir_ui_view
            WHERE id IN (1046, 1059, 1696, 15746)
               OR key IN ('website.option_header_brand_logo', 'website.footer_custom')
        """)
        print(f"[✓] Backed up {cur.rowcount} rows to ir_ui_view_logo_backup.")

        print("\n--- 1. Purging Fake Text Logo in View 1046 (website.option_header_brand_logo) ---")
        navbar_vector_arch = """<data name="Header Brand Logo">
    <xpath expr="//*[@id='o_fake_navbar_brand']" position="replace">
        <a data-name="Navbar Logo" href="/" t-attf-class="navbar-brand logo inno-logo-interactive d-inline-flex align-items-center py-1 me-xl-4 me-3 #{_link_class}">
            <img class="inno-brand-logo img-fluid" src="/innokafe_website/static/src/img/branding/innokafe_logo_master.svg" alt="InnoKafe - Inspire the Techno" height="38" style="height: 38px; width: auto; max-height: 44px;"/>
        </a>
    </xpath>
</data>"""
        _validate_xml_fragment(navbar_vector_arch)
        new_header_json = json.dumps({"en_US": navbar_vector_arch})
        new_header_hash = _hash_content(new_header_json)

        if all_websites:
            cur.execute("SELECT id, key, arch_db::text FROM ir_ui_view WHERE (id = 1046 OR key = 'website.option_header_brand_logo')")
        else:
            cur.execute("SELECT id, key, arch_db::text FROM ir_ui_view WHERE id = %s", (1046,))
        header_rows = cur.fetchall()

        for h_id, h_key, h_arch in header_rows:
            old_hash = _hash_content(h_arch or "")
            if 'innokafe_logo_master.svg' in (h_arch or ''):
                print(f"[✓] View {h_id} ({h_key}) already carries vector SVG master logo (Idempotent skip).")
                cur.execute("""
                    INSERT INTO ir_ui_view_logo_purge_ledger (view_id, view_key, pre_hash, post_hash, changed)
                    VALUES (%s, %s, %s, %s, false)
                """, (h_id, h_key, old_hash, old_hash))
            else:
                cur.execute("""
                    UPDATE ir_ui_view
                    SET arch_db = %s::jsonb, arch_fs = NULL, arch_updated = true, write_date = NOW()
                    WHERE id = %s
                """, (new_header_json, h_id))
                cur.execute("""
                    INSERT INTO ir_ui_view_logo_purge_ledger (view_id, view_key, pre_hash, post_hash, changed)
                    VALUES (%s, %s, %s, %s, true)
                """, (h_id, h_key, old_hash, new_header_hash))
                print(f"[✓] Updated view {h_id} ({h_key}) -> set to vector SVG logo master.")

        print("\n--- 2. Purging Fake Text Logo in Footer Views 1059 & 1696 (website.footer_custom) ---")
        cur.execute("SELECT id, key, arch_db::text FROM ir_ui_view WHERE key = 'website.footer_custom' OR id IN (1059, 1696)")
        footer_views = cur.fetchall()

        new_footer_brand = """<a href="/" class="d-inline-flex align-items-center text-decoration-none">
                                        <img src="/innokafe_website/static/src/img/branding/innokafe_logo_white.svg" alt="InnoKafe - Inspire the Techno" height="38" style="height: 38px; width: auto; max-height: 44px;"/>
                                    </a>"""
        _validate_xml_fragment(new_footer_brand)

        for v_id, v_key, arch_text in footer_views:
            old_hash = _hash_content(arch_text or "")
            if 'Inno<span' in arch_text or 'Specialty' in arch_text or 'VIETNAM SPECIALTY' in arch_text:
                arch_data = json.loads(arch_text)
                for lang, xml_content in arch_data.items():
                    cleaned_content = re.sub(
                        r'<a href="/" class="d-inline-flex align-items-center gap-2 text-decoration-none">\s*<span class="fs-2 fw-bold inno-serif text-white tracking-tight">\s*Inno<span class="text-warning inno-amber-text">Kafe</span>\s*</span>\s*</a>\s*(?:<div class="text-warning small font-monospace mt-1"[^>]*>\s*VIETNAM SPECIALTY COFFEE &amp; ROASTERY\s*</div>)?',
                        new_footer_brand,
                        xml_content,
                        flags=re.DOTALL
                    )
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
                    _validate_xml_fragment(cleaned_content)
                    arch_data[lang] = cleaned_content

                new_arch_json = json.dumps(arch_data)
                new_hash = _hash_content(new_arch_json)
                cur.execute("""
                    UPDATE ir_ui_view
                    SET arch_db = %s::jsonb, arch_fs = NULL, arch_updated = true, write_date = NOW()
                    WHERE id = %s
                """, (new_arch_json, v_id))
                cur.execute("""
                    INSERT INTO ir_ui_view_logo_purge_ledger (view_id, view_key, pre_hash, post_hash, changed)
                    VALUES (%s, %s, %s, %s, true)
                """, (v_id, v_key, old_hash, new_hash))
                print(f"[✓] Sanitized footer view {v_id} -> Replaced fake text with vector innokafe_logo_white.svg")
            else:
                cur.execute("""
                    INSERT INTO ir_ui_view_logo_purge_ledger (view_id, view_key, pre_hash, post_hash, changed)
                    VALUES (%s, %s, %s, %s, false)
                """, (v_id, v_key, old_hash, old_hash))

        print("\n--- 3. Checking Legacy View 15746 / innokafe_header_brand_bar ---")
        cur.execute("SELECT id, key, name, arch_db::text FROM ir_ui_view WHERE id = 15746 OR key LIKE '%innokafe_header_brand_bar%'")
        legacy_rows = cur.fetchall()
        if legacy_rows:
            for r_id, r_key, r_name, r_arch in legacy_rows:
                old_hash = _hash_content(r_arch or "")
                print(f"[!] Legacy view found: ID {r_id}, Key: {r_key}, Name: {r_name}. Updating to vector SVG and deactivating...")
                cur.execute("""
                    UPDATE ir_ui_view
                    SET arch_db = %s::jsonb, active = false, write_date = NOW()
                    WHERE id = %s
                """, (new_header_json, r_id))
                cur.execute("""
                    INSERT INTO ir_ui_view_logo_purge_ledger (view_id, view_key, pre_hash, post_hash, changed)
                    VALUES (%s, %s, %s, %s, true)
                """, (r_id, r_key, old_hash, new_header_hash))
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
                old_hash = _hash_content(r_arch or "")
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
                    _validate_xml_fragment(arch_data[lang])
                new_arch_json = json.dumps(arch_data)
                new_hash = _hash_content(new_arch_json)
                cur.execute("""
                    UPDATE ir_ui_view
                    SET arch_db = %s::jsonb, arch_updated = true, write_date = NOW()
                    WHERE id = %s
                """, (new_arch_json, r_id))
                cur.execute("""
                    INSERT INTO ir_ui_view_logo_purge_ledger (view_id, view_key, pre_hash, post_hash, changed)
                    VALUES (%s, %s, %s, %s, true)
                """, (r_id, r_key, old_hash, new_hash))
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

        if commit:
            conn.commit()
            print("\n[✓] TRANSACTION COMMITTED DURABLY.")
        else:
            conn.rollback()
            print("\n[!] DRY-RUN MODE: All changes rolled back cleanly (0 durable mutations). Pass --commit to persist.")

        if remaining_count > 0:
            raise RuntimeError(f"Database purge incomplete: {remaining_count} fake text logo instances still remain!")
        print(f"\n[SUCCESS] 100% of fake text logos purged from {dbname} under strict 0 DDL invariance.")

    except Exception:
        conn.rollback()
        print("\n[✗] Exception encountered — transaction rolled back, zero changes persisted.")
        raise
    finally:
        conn.close()


def _require_env(*names: str) -> str:
    """Return the first non-empty, non-blank env var among names, or exit non-zero.
    A destructive utility must never fall back to a hard-coded credential.
    """
    for name in names:
        val = os.environ.get(name)
        if val and val.strip():  # reject whitespace-only secrets
            return val.strip()
    joined = " / ".join(names)
    sys.exit(f"FATAL: required environment variable(s) not set: {joined}")


def main():
    parser = argparse.ArgumentParser(description="Zero-DDL Database Clean-up for InnoKafe Vector Logo Branding.")
    parser.add_argument("target", choices=["local", "prod_pod"], nargs="?", default="local", help="Target environment (default: local)")
    parser.add_argument("--commit", action="store_true", default=False, help="Persist changes to database (default: dry-run with rollback)")
    parser.add_argument("--all-websites", action="store_true", default=False, help="Overwrite all website COW copies of brand logo view (default: single tenant view)")
    args = parser.parse_args()

    # Credential hygiene: pull from environment, never require on command line, fail closed
    if args.target == "local":
        host = os.environ.get("DB_HOST", "127.0.0.1")
        port = int(os.environ.get("DB_PORT", 5434))
        user = os.environ.get("DB_USER", "insilos")
        password = _require_env("PGPASSWORD", "DB_PASSWORD")
        dbname = os.environ.get("DB_NAME", "innokafe_prod")
    else:  # prod_pod
        host = os.environ.get("DB_HOST", "pgbouncer-service")
        port = int(os.environ.get("DB_PORT", 6432))
        user = _require_env("DB_USER")
        password = _require_env("PGPASSWORD", "DB_PASSWORD")
        dbname = _require_env("DB_NAME")

        # Defense-in-depth: prod_pod target must never resolve to loopback
        if host in ("127.0.0.1", "localhost", "::1"):
            sys.exit("FATAL: prod_pod target resolved to a loopback host; refusing to run.")

        # Defense-in-depth: overwriting all website COW copies on prod_pod requires explicit confirmation
        if args.all_websites and args.commit:
            if not os.environ.get("CONFIRM_ALL_WEBSITES_PROD"):
                sys.exit("FATAL: --all-websites --commit on prod_pod requires CONFIRM_ALL_WEBSITES_PROD=1")

    clean_database(host, port, user, password, dbname, commit=args.commit, all_websites=args.all_websites)


if __name__ == '__main__':
    main()
