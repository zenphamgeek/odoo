#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Workspace Setup & Verification Tool for Insilos Enterprise ERP
Configures Outgoing SMTP, Incoming IMAP, and Google OAuth2 for @inno.ai.vn
Target Database: insilos20_dev (PostgreSQL port 5434)
"""

import sys
import os
import argparse
import smtplib
import imaplib
import subprocess
import psycopg2
from email.mime.text import MIMEText

DB_NAME = 'insilos20_dev'
DB_HOST = '127.0.0.1'
DB_PORT = 5434
DB_USER = 'odoo'

def get_db_connection():
    return psycopg2.connect(
        dbname=DB_NAME,
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER
    )

def check_dns(domain="inno.ai.vn"):
    print(f"\n=======================================================")
    print(f"[*] KIỂM TRA BẢN GHI DNS CHO DOMAIN: {domain}")
    print(f"=======================================================")
    
    def run_dig(query_type, qname):
        try:
            res = subprocess.run(['dig', '+short', query_type, qname], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return res.stdout.strip()
        except Exception as e:
            return f"Error: {e}"

    # MX
    mx = run_dig('MX', domain)
    print(f"\n1. [MX Records] Máy chủ nhận email:")
    if 'google' in mx.lower() or 'aspmx' in mx.lower():
        print(f"   [OK] Đã trỏ chính xác về Google Workspace:")
        for line in mx.splitlines():
            print(f"        -> {line}")
    else:
        print(f"   [FAIL] Chưa trỏ về Google Workspace: {mx}")

    # SPF
    spf = run_dig('TXT', domain)
    print(f"\n2. [SPF Record] Bản ghi xác thực IP gửi email:")
    has_spf = False
    for line in spf.splitlines():
        if 'v=spf1' in line:
            has_spf = True
            print(f"   [OK] Tìm thấy SPF: {line}")
            if 'include:_spf.google.com' in line:
                print("        -> Đã include Google Workspace SPF (_spf.google.com).")
            else:
                print("        [CẢNH BÁO] Chưa có include:_spf.google.com")
    if not has_spf:
        print("   [CẢNH BÁO] CHƯA CÓ BẢN GHI SPF!")
        print("   -> Cần thêm bản ghi TXT tại Host '@':")
        print("      v=spf1 include:_spf.google.com ~all")

    # DKIM
    dkim = run_dig('TXT', f"google._domainkey.{domain}")
    print(f"\n3. [DKIM Record] Chữ ký số mã hóa chống giả mạo:")
    if 'v=DKIM1' in dkim or 'k=rsa' in dkim:
        print(f"   [OK] Đã cấu hình DKIM (selector: google):")
        print(f"        -> {dkim[:60]}...")
    else:
        print("   [CẢNH BÁO] CHƯA CÓ BẢN GHI DKIM (selector 'google')!")
        print("   -> Cần vào admin.google.com > Apps > Google Workspace > Gmail > Authenticate email để tạo key.")

    # DMARC
    dmarc = run_dig('TXT', f"_dmarc.{domain}")
    print(f"\n4. [DMARC Record] Chính sách phòng chống lừa đảo giả mạo:")
    if 'v=DMARC1' in dmarc:
        print(f"   [OK] Đã cấu hình DMARC:")
        print(f"        -> {dmarc}")
    else:
        print("   [CẢNH BÁO] CHƯA CÓ BẢN GHI DMARC!")
        print(f"   -> Cần thêm bản ghi TXT tại Host '_dmarc':")
        print(f"      v=DMARC1; p=quarantine; rua=mailto:admin@{domain}; pct=100; adkim=r; aspf=r")
    
    print("\n=======================================================\n")

def test_smtp(user, password, host="smtp.gmail.com", port=465):
    print(f"[*] Đang kiểm tra kết nối SMTP Outgoing ({host}:{port}) với user: {user} ...")
    clean_pass = password.replace(" ", "")
    if len(clean_pass) != 16 or not clean_pass.isalnum():
        print(f"   [CẢNH BÁO ĐỊNH DẠNG] Mật khẩu bạn nhập có ký tự đặc biệt hoặc độ dài {len(clean_pass)} ký tự.")
        print(f"   -> Google Workspace bắt buộc phải sử dụng Mật khẩu ứng dụng (App Password) gồm đúng 16 chữ cái (ví dụ: 'abcd efgh ijkl mnop').")
        print(f"   -> Mật khẩu tài khoản thông thường sẽ bị Google từ chối và tự động đóng kết nối (Connection unexpectedly closed).")
    try:
        if port == 465:
            server = smtplib.SMTP_SSL(host, port, timeout=10)
        else:
            server = smtplib.SMTP(host, port, timeout=10)
            server.starttls()
        server.login(user, clean_pass)
        print(f"   [SUCCESS] Đăng nhập SMTP thành công! App Password hoạt động hoàn hảo.")
        server.quit()
        return True
    except smtplib.SMTPAuthenticationError as e:
        print(f"   [ERROR] Đăng nhập SMTP thất bại (Sai user hoặc App Password): {e}")
        print(f"   -> Vui lòng tạo App Password tại: https://myaccount.google.com/apppasswords")
        return False
    except smtplib.SMTPServerDisconnected as e:
        print(f"   [ERROR] Google SMTP đóng kết nối đột ngột: {e}")
        print(f"   -> NGUYÊN NHÂN CHÍNH: Google từ chối mật khẩu tài khoản thông thường qua giao thức SMTP/IMAP.")
        print(f"   -> BẮT BUỘC: Bạn phải tạo Mật khẩu ứng dụng (16 ký tự) tại https://myaccount.google.com/apppasswords")
        return False
    except Exception as e:
        print(f"   [ERROR] Không thể kết nối tới SMTP {host}:{port}: {e}")
        return False

def test_imap(user, password, host="imap.gmail.com", port=993):
    print(f"[*] Đang kiểm tra kết nối IMAP Incoming ({host}:{port}) với user: {user} ...")
    clean_pass = password.replace(" ", "")
    try:
        mail = imaplib.IMAP4_SSL(host, port)
        mail.login(user, clean_pass)
        status, folders = mail.list()
        print(f"   [SUCCESS] Đăng nhập IMAP thành công! Tìm thấy {len(folders)} thư mục hòm thư.")
        mail.logout()
        return True
    except imaplib.IMAP4.error as e:
        print(f"   [ERROR] Đăng nhập IMAP thất bại: {e}")
        print(f"   -> NGUYÊN NHÂN: Google không chấp nhận mật khẩu tài khoản chính. Cần App Password 16 chữ cái.")
        return False
    except Exception as e:
        print(f"   [ERROR] Không thể kết nối tới IMAP {host}:{port}: {e}")
        return False

def configure_mail_server(user, password, domain="inno.ai.vn", crm_object=True):
    clean_pass = password.replace(" ", "")
    conn = get_db_connection()
    cur = conn.cursor()
    
    print(f"[*] Đang ghi cấu hình Mail Server vào database '{DB_NAME}'...")
    
    # 1. Outgoing Mail Server (ir.mail_server)
    cur.execute("SELECT id FROM ir_mail_server WHERE smtp_user = %s OR name LIKE %s", (user, '%Google Workspace%'))
    existing_mail = cur.fetchone()
    
    if existing_mail:
        server_id = existing_mail[0]
        cur.execute("""
            UPDATE ir_mail_server 
            SET name = %s,
                smtp_host = 'smtp.gmail.com',
                smtp_port = 465,
                smtp_encryption = 'ssl',
                smtp_authentication = 'login',
                smtp_user = %s,
                smtp_pass = %s,
                from_filter = %s,
                active = TRUE,
                smtp_debug = FALSE
            WHERE id = %s
        """, (f"Google Workspace SMTP ({user})", user, clean_pass, domain, server_id))
        print(f"   [OK] Cập nhật ir.mail_server ID {server_id}: smtp.gmail.com:465 (SSL) cho {user}")
    else:
        cur.execute("""
            INSERT INTO ir_mail_server (
                name, smtp_host, smtp_port, smtp_encryption, smtp_authentication, smtp_user, smtp_pass, from_filter, sequence, active, smtp_debug, create_date, write_date
            ) VALUES (
                %s, 'smtp.gmail.com', 465, 'ssl', 'login', %s, %s, %s, 10, TRUE, FALSE, NOW(), NOW()
            ) RETURNING id
        """, (f"Google Workspace SMTP ({user})", user, clean_pass, domain))
        server_id = cur.fetchone()[0]
        print(f"   [OK] Tạo mới ir.mail_server ID {server_id}: smtp.gmail.com:465 (SSL) cho {user}")

    # 2. Incoming Mail Server (fetchmail.server)
    object_id = None
    if crm_object:
        cur.execute("SELECT id FROM ir_model WHERE model = 'crm.lead'")
        res = cur.fetchone()
        if res:
            object_id = res[0]

    cur.execute('SELECT id FROM fetchmail_server WHERE "user" = %s OR name LIKE %s', (user, '%Google Workspace%'))
    existing_fetch = cur.fetchone()
    
    if existing_fetch:
        fetch_id = existing_fetch[0]
        cur.execute("""
            UPDATE fetchmail_server 
            SET name = %s,
                server = 'imap.gmail.com',
                port = 993,
                server_type = 'imap',
                is_ssl = TRUE,
                "user" = %s,
                password = %s,
                object_id = %s,
                active = TRUE,
                state = 'done'
            WHERE id = %s
        """, (f"Google Workspace IMAP ({user})", user, clean_pass, object_id, fetch_id))
        print(f"   [OK] Cập nhật fetchmail.server ID {fetch_id}: imap.gmail.com:993 (SSL) cho {user}")
    else:
        cur.execute("""
            INSERT INTO fetchmail_server (
                name, server, port, server_type, is_ssl, "user", password, object_id, priority, active, state, create_date, write_date
            ) VALUES (
                %s, 'imap.gmail.com', 993, 'imap', TRUE, %s, %s, %s, 5, TRUE, 'done', NOW(), NOW()
            ) RETURNING id
        """, (f"Google Workspace IMAP ({user})", user, clean_pass, object_id))
        fetch_id = cur.fetchone()[0]
        print(f"   [OK] Tạo mới fetchmail.server ID {fetch_id}: imap.gmail.com:993 (SSL) cho {user}")

    conn.commit()
    conn.close()
    print("   [SUCCESS] Hoàn tất ghi cấu hình Mail Server vào hệ thống!")

def configure_oauth(client_id, client_secret=None, domain="inno.ai.vn"):
    conn = get_db_connection()
    cur = conn.cursor()
    
    print(f"[*] Đang cấu hình Google OAuth2 trong database '{DB_NAME}'...")
    
    # ID 3 is the default Google OAuth2 provider record in auth_oauth
    button_label = f"Đăng nhập bằng Google (@{domain})"
    cur.execute("""
        UPDATE auth_oauth_provider
        SET client_id = %s,
            enabled = TRUE,
            body = jsonb_build_object('en_US', %s, 'vi_VN', %s),
            scope = 'openid profile email',
            auth_endpoint = 'https://accounts.google.com/o/oauth2/auth',
            validation_endpoint = 'https://www.googleapis.com/oauth2/v3/userinfo'
        WHERE id = 3
    """, (client_id.strip(), button_label, button_label))
    
    # Ensure auth_signup allows oauth signups if needed
    cur.execute("""
        INSERT INTO ir_config_parameter (key, value, create_date, write_date)
        VALUES ('auth_signup.invitation_scope', 'b2c', NOW(), NOW())
        ON CONFLICT (key) DO UPDATE SET value = 'b2c', write_date = NOW()
    """)

    # Set google_gmail Client ID and Client Secret in ir_config_parameter
    cur.execute("""
        INSERT INTO ir_config_parameter (key, value, create_date, write_date)
        VALUES ('google_gmail_client_id', %s, NOW(), NOW())
        ON CONFLICT (key) DO UPDATE SET value = %s, write_date = NOW()
    """, (client_id.strip(), client_id.strip()))

    if client_secret:
        cur.execute("""
            INSERT INTO ir_config_parameter (key, value, create_date, write_date)
            VALUES ('google_gmail_client_secret', %s, NOW(), NOW())
            ON CONFLICT (key) DO UPDATE SET value = %s, write_date = NOW()
        """, (client_secret.strip(), client_secret.strip()))
    
    conn.commit()
    conn.close()
    print(f"   [SUCCESS] Google OAuth2 & Gmail API đã được kích hoạt thành công!")
    print(f"   - Client ID: {client_id.strip()}")
    if client_secret:
        print(f"   - Client Secret: {'*' * (len(client_secret.strip()) - 4) + client_secret.strip()[-4:]}")
    print(f"   - Nút hiển thị đăng nhập: '{button_label}'")
    print(f"   - Trạng thái: Kích hoạt (enabled = True)")
    print(f"   - Cho phép tự động tạo tài khoản: B2C (auth_signup.invitation_scope = b2c)")
    print(f"\n   [QUAN TRỌNG - GOOGLE CLOUD CONSOLE]")
    print(f"   Hãy chắc chắn bạn đã thêm 'Authorized redirect URIs' trên Google Cloud Console:")
    print(f"   1. Cho đăng nhập SSO:       http://localhost:28069/auth_oauth/signin")
    print(f"   2. Cho kết nối Gmail OAuth: http://localhost:28069/google_gmail/confirm")
    print(f"   (Nếu dùng domain chính thức, thay http://localhost:28069 bằng https://insilos.com)")

def print_status():
    conn = get_db_connection()
    cur = conn.cursor()
    print(f"\n=======================================================")
    print(f"[*] TRẠNG THÁI HIỆN TẠI TRÊN DATABASE '{DB_NAME}':")
    print(f"=======================================================")
    
    print("\n1. Máy chủ gửi mail (ir.mail_server):")
    cur.execute("SELECT id, name, smtp_host, smtp_port, smtp_encryption, smtp_user, from_filter, active FROM ir_mail_server")
    rows = cur.fetchall()
    if not rows:
        print("   [Trống] Chưa có máy chủ gửi mail nào được tạo.")
    else:
        for r in rows:
            print(f"   ID {r[0]}: {r[1]} | Host: {r[2]}:{r[3]} ({r[4]}) | User: {r[5]} | From Filter: {r[6]} | Active: {r[7]}")

    print("\n2. Máy chủ nhận mail (fetchmail.server):")
    cur.execute('SELECT f.id, f.name, f.server, f.port, f.server_type, f."user", f.active, m.model FROM fetchmail_server f LEFT JOIN ir_model m ON f.object_id = m.id')
    rows = cur.fetchall()
    if not rows:
        print("   [Trống] Chưa có máy chủ nhận mail nào được tạo.")
    else:
        for r in rows:
            print(f"   ID {r[0]}: {r[1]} | Server: {r[2]}:{r[3]} ({r[4]}) | User: {r[5]} | Target Model: {r[7]} | Active: {r[6]}")

    print("\n3. Google OAuth Provider (auth.oauth.provider):")
    cur.execute("SELECT id, name, client_id, enabled, body FROM auth_oauth_provider WHERE id = 3")
    row = cur.fetchone()
    if row:
        print(f"   ID {row[0]}: {row[1]} | Client ID: {row[2]} | Enabled: {row[3]} | Body: {row[4]}")
    else:
        print("   [Lỗi] Không tìm thấy provider Google ID 3.")

    conn.close()
    print("\n=======================================================\n")

def main():
    parser = argparse.ArgumentParser(description="Google Workspace & OAuth Setup Tool for Insilos Enterprise")
    parser.add_argument("--dns", action="store_true", help="Kiểm tra trạng thái DNS (MX, SPF, DKIM, DMARC)")
    parser.add_argument("--status", action="store_true", help="Xem trạng thái cấu hình hiện tại trong DB")
    parser.add_argument("--test-smtp", action="store_true", help="Kiểm tra kết nối gửi email qua SMTP")
    parser.add_argument("--test-imap", action="store_true", help="Kiểm tra kết nối nhận email qua IMAP")
    parser.add_argument("--apply-mail", action="store_true", help="Áp dụng cấu hình SMTP và IMAP vào hệ thống")
    parser.add_argument("--apply-oauth", action="store_true", help="Áp dụng Client ID Google OAuth vào hệ thống")
    parser.add_argument("--user", type=str, default="thang@inno.ai.vn", help="Tài khoản email (mặc định: thang@inno.ai.vn)")
    parser.add_argument("--password", type=str, help="Mật khẩu ứng dụng 16 ký tự của Google (App Password)")
    parser.add_argument("--client-id", type=str, help="Google OAuth Client ID (*.apps.googleusercontent.com)")
    parser.add_argument("--client-secret", type=str, help="Google OAuth Client Secret")
    parser.add_argument("--domain", type=str, default="inno.ai.vn", help="Tên miền công ty (mặc định: inno.ai.vn)")
    
    args = parser.parse_args()

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    if args.dns:
        check_dns(args.domain)

    if args.status:
        print_status()

    if args.test_smtp:
        if not args.password:
            print("[LỖI] Cần truyền mật khẩu ứng dụng qua cờ --password '<app_password>'")
            sys.exit(1)
        test_smtp(args.user, args.password)

    if args.test_imap:
        if not args.password:
            print("[LỖI] Cần truyền mật khẩu ứng dụng qua cờ --password '<app_password>'")
            sys.exit(1)
        test_imap(args.user, args.password)

    if args.apply_mail:
        if not args.password:
            print("[LỖI] Cần truyền mật khẩu ứng dụng qua cờ --password '<app_password>'")
            sys.exit(1)
        if test_smtp(args.user, args.password) and test_imap(args.user, args.password):
            configure_mail_server(args.user, args.password, args.domain)
            print_status()
        else:
            print("[HỦY] Xác thực SMTP hoặc IMAP thất bại! Không lưu cấu hình sai vào cơ sở dữ liệu.")

    if args.apply_oauth:
        if not args.client_id:
            print("[LỖI] Cần truyền Google Client ID qua cờ --client-id '<client_id>'")
            sys.exit(1)
        configure_oauth(args.client_id, args.client_secret, args.domain)
        print_status()

if __name__ == "__main__":
    main()
