#!/usr/bin/env python3
import psycopg2
import json
import re

def main():
    conn = psycopg2.connect(host='127.0.0.1', port=5434, dbname='odoo20_dev', user='odoo', password='1NN0R1@2026')
    cur = conn.cursor()

    cur.execute('''
        SELECT id, name, key, arch_fs, arch_db 
        FROM ir_ui_view 
        WHERE arch_db::text ILIKE '%odoo%'
    ''')
    views = cur.fetchall()

    print(f"Total views matching '%odoo%' in arch_db: {len(views)}")

    user_facing = []

    # Patterns indicating user-facing text vs technical identifiers
    patterns = [
        re.compile(r'>[^<]*\b[oO]doo\b[^<]*<'),
        re.compile(r'string=["\'][^"\']*\b[oO]doo\b[^"\']*["\']', re.IGNORECASE),
        re.compile(r'placeholder=["\'][^"\']*\b[oO]doo\b[^"\']*["\']', re.IGNORECASE),
        re.compile(r'title=["\'][^"\']*\b[oO]doo\b[^"\']*["\']', re.IGNORECASE),
        re.compile(r'alt=["\'][^"\']*\b[oO]doo\b[^"\']*["\']', re.IGNORECASE),
        re.compile(r'https?://[a-zA-Z0-9.-]*odoo\.com', re.IGNORECASE),
        re.compile(r'\bOdoo\b'),
    ]

    for v_id, v_name, key, arch_fs, arch_db in views:
        text_content = json.dumps(arch_db)
        matches = []
        for p in patterns[:6]:
            m = p.findall(text_content)
            if m:
                matches.extend(m)
        if matches:
            user_facing.append((v_id, v_name, key, arch_fs, matches))

    print(f"User facing visual matches found in {len(user_facing)} views:\n")
    for item in user_facing:
        print(f"ID {item[0]} | Name: {item[1]} | Key: {item[2]} | File: {item[3]}")
        for m in item[4][:4]:
            print(f"    Match: {m[:120]}")
        print()

if __name__ == '__main__':
    main()
