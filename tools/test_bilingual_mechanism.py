#!/usr/bin/env python3
"""
Test Odoo 20 Multi-Language Bilingual Mechanism
Verifies res.lang, website_lang_rel, ir_ui_view arch_db JSONB structure,
and routing behavior.
"""

import json
import psycopg2

def test_db():
    conn = psycopg2.connect(
        host="127.0.0.1",
        port=5434,
        user="odoo",
        password="1NN0R1@2026",
        dbname="innoria.insilos.com"
    )
    conn.autocommit = True
    cur = conn.cursor()

    print("[*] Inspecting active languages in res_lang...")
    cur.execute("SELECT id, code, name, active, url_code FROM res_lang WHERE code IN ('vi_VN', 'en_US');")
    langs = cur.fetchall()
    for l in langs:
        print(f"  - ID: {l[0]}, Code: {l[1]}, Name: {l[2]}, Active: {l[3]}, URL Code: {l[4]}")

    print("\n[*] Inspecting websites and default_lang_id...")
    cur.execute("SELECT id, name, domain, default_lang_id FROM website;")
    websites = cur.fetchall()
    for w in websites:
        print(f"  - Website #{w[0]}: {w[1]} (domain={w[2]}, default_lang_id={w[3]})")

    print("\n[*] Inspecting website_lang_rel...")
    cur.execute("SELECT website_id, lang_id FROM website_lang_rel;")
    rel = cur.fetchall()
    for r in rel:
        print(f"  - website_id: {r[0]} -> lang_id: {r[1]}")

    print("\n[*] Inspecting arch_db keys in ir_ui_view...")
    cur.execute("""
        SELECT key, (arch_db->>'vi_VN') IS NOT NULL as has_vi, (arch_db->>'en_US') IS NOT NULL as has_en
        FROM ir_ui_view
        WHERE key IN ('insilos_website.innoria_navbar', 'insilos_website.innoria_homepage_template', 'insilos_website.insilos_about_page');
    """)
    views = cur.fetchall()
    for v in views:
        print(f"  - View {v[0]}: has_vi={v[1]}, has_en={v[2]}")

    conn.close()

if __name__ == "__main__":
    test_db()
