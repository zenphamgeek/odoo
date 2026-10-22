#!/usr/bin/env python3
"""
Test Odoo QWeb dual-language rendering from arch_db.
"""

import json
import psycopg2

def test_qweb():
    conn = psycopg2.connect(
        host="127.0.0.1",
        port=5434,
        user="odoo",
        password="1NN0R1@2026",
        dbname="innoria.insilos.com"
    )
    conn.autocommit = True
    cur = conn.cursor()

    # 1. Update res_lang
    cur.execute("UPDATE res_lang SET active = true, url_code = 'vi' WHERE code = 'vi_VN';")
    cur.execute("UPDATE res_lang SET active = true, url_code = 'en' WHERE code = 'en_US';")

    # 2. Update website_lang_rel
    cur.execute("""
        INSERT INTO website_lang_rel (website_id, lang_id)
        SELECT 1, 91
        WHERE NOT EXISTS (SELECT 1 FROM website_lang_rel WHERE website_id = 1 AND lang_id = 91);
    """)
    cur.execute("""
        INSERT INTO website_lang_rel (website_id, lang_id)
        SELECT 1, 1
        WHERE NOT EXISTS (SELECT 1 FROM website_lang_rel WHERE website_id = 1 AND lang_id = 1);
    """)

    # 3. Set default_lang_id to 91 (vi_VN)
    cur.execute("UPDATE website SET default_lang_id = 91 WHERE id = 1;")

    # 4. Verify
    cur.execute("SELECT id, code, active, url_code FROM res_lang WHERE code IN ('vi_VN', 'en_US');")
    print("[*] Languages:", cur.fetchall())

    cur.execute("SELECT default_lang_id FROM website WHERE id = 1;")
    print("[*] Website default_lang_id:", cur.fetchone())

    cur.execute("SELECT website_id, lang_id FROM website_lang_rel WHERE website_id = 1;")
    print("[*] Website languages:", cur.fetchall())

    conn.close()

if __name__ == "__main__":
    test_qweb()
