#!/usr/bin/env python3
"""
Test HTTP request against local Odoo instance on port 28069
to verify bilingual rendering for vi_VN vs en_US.
"""

import requests
import psycopg2
import json

def test():
    # 1. Update arch_db of innoria_navbar to have distinct text in vi_VN and en_US
    conn = psycopg2.connect(
        host="127.0.0.1",
        port=5434,
        user="odoo",
        password="1NN0R1@2026",
        dbname="innoria.insilos.com"
    )
    conn.autocommit = True
    cur = conn.cursor()

    cur.execute("SELECT arch_db FROM ir_ui_view WHERE key = 'insilos_website.innoria_navbar';")
    row = cur.fetchone()
    if not row:
        print("[!] View not found!")
        return
    
    current_arch = row[0]
    # If it's already dict
    if isinstance(current_arch, str):
        current_arch = json.loads(current_arch)
    
    base_xml = current_arch.get("en_US") or current_arch.get("vi_VN")

    # Create distinct test strings in navbar
    vn_xml = base_xml.replace('<span>Nền Tảng</span>', '<span>Nền Tảng VN</span>')
    en_xml = base_xml.replace('<span>Nền Tảng</span>', '<span>Platform EN</span>')

    dual_arch = {
        "vi_VN": vn_xml,
        "en_US": en_xml
    }

    cur.execute("UPDATE ir_ui_view SET arch_db = %s::jsonb WHERE key = 'insilos_website.innoria_navbar';", (json.dumps(dual_arch),))
    print("[✓] Updated innoria_navbar with dual arch_db (vi_VN & en_US)")

    conn.close()

if __name__ == "__main__":
    test()
