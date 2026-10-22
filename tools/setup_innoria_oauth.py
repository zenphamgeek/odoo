#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Setup Google OAuth2 for innoria_prod on https://innoria.com/web/login
"""
import psycopg2
import json

DB_NAME = 'innoria_prod'
DB_HOST = '127.0.0.1'
DB_PORT = 5434
DB_USER = 'odoo'
DB_PASS = '1NN0R1@2026'

import os

CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
DOMAIN = 'inno.ai.vn'
BASE_URL = 'https://innoria.com'

def configure():
    conn = psycopg2.connect(
        dbname=DB_NAME,
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASS
    )
    cur = conn.cursor()
    print(f"[*] Đang cấu hình Google OAuth2 trên database '{DB_NAME}'...")

    # 1. Update auth_oauth_provider
    button_label = f"Đăng nhập bằng Google (@{DOMAIN})"
    body_json = json.dumps({"en_US": button_label, "vi_VN": button_label})
    cur.execute("""
        UPDATE auth_oauth_provider
        SET client_id = %s,
            enabled = TRUE,
            body = %s::jsonb,
            scope = 'openid profile email',
            auth_endpoint = 'https://accounts.google.com/o/oauth2/auth',
            validation_endpoint = 'https://www.googleapis.com/oauth2/v3/userinfo',
            css_class = 'fa fa-fw fa-google',
            write_date = NOW()
        WHERE name = 'Google OAuth2' OR id = 3
    """, (CLIENT_ID, body_json))
    print(f"   [OK] auth_oauth_provider cập nhật: {cur.rowcount} hàng.")

    # 2. Update ir_config_parameter
    params = [
        ('web.base.url', BASE_URL),
        ('web.base.url.freeze', 'True'),
        ('auth_signup.invitation_scope', 'b2c'),
        ('google_gmail_client_id', CLIENT_ID),
        ('google_gmail_client_secret', CLIENT_SECRET),
    ]

    for key, val in params:
        cur.execute("""
            INSERT INTO ir_config_parameter (key, value, create_date, write_date)
            VALUES (%s, %s, NOW(), NOW())
            ON CONFLICT (key) DO UPDATE SET value = %s, write_date = NOW()
        """, (key, val, val))
        print(f"   [OK] ir_config_parameter: {key} = {val}")

    # 3. Update website domain
    cur.execute("""
        UPDATE website
        SET domain = %s
        WHERE id = 1
    """, (BASE_URL,))
    print(f"   [OK] website domain cập nhật về: {BASE_URL}")

    conn.commit()

    # Verify
    print("\n--- XÁC MINH CẤU HÌNH ---")
    cur.execute("SELECT id, name, client_id, enabled, body FROM auth_oauth_provider WHERE enabled = TRUE")
    for r in cur.fetchall():
        print(f"Provider Active: ID={r[0]}, Name={r[1]}, ClientID={r[2]}, Enabled={r[3]}, Body={r[4]}")

    cur.execute("SELECT key, value FROM ir_config_parameter WHERE key IN ('web.base.url', 'web.base.url.freeze', 'auth_signup.invitation_scope', 'google_gmail_client_id')")
    for r in cur.fetchall():
        print(f"Config: {r[0]} = {r[1]}")

    conn.close()
    print("\n[SUCCESS] Hoàn tất cấu hình Google OAuth2 cho innoria_prod!")

if __name__ == '__main__':
    configure()
