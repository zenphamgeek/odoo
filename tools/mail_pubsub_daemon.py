#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Innoria AL2C Mail Pub/Sub & Timesheet Ingestion Daemon
Part of Insilos Enterprise O20 Autonomous Lead-to-Cash (AL2C) Engine.

Listens for incoming emails or Pub/Sub push notifications for info@inno.ai.vn,
extracts consultant timesheet records and attachments (.xlsx, .csv),
computes constant-time HMAC-SHA256 signatures, and posts to /api/v1/timesheet/ingest.

Usage:
  python3 tools/mail_pubsub_daemon.py --simulate
  python3 tools/mail_pubsub_daemon.py --once
  python3 tools/mail_pubsub_daemon.py --daemon
"""

import sys
import os
import time
import json
import uuid
import hmac
import hashlib
import base64
import argparse
import logging
import email
from email import policy
import imaplib
import urllib.request
import urllib.error
import psycopg2

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
_logger = logging.getLogger("al2c_mail_pubsub")

DEFAULT_ODD_URL = "http://127.0.0.1:28069"
DEFAULT_WEBHOOK_PATH = "/api/v1/timesheet/ingest"
DEFAULT_SECRET = "inno_al2c_timesheet_pubsub_secret_2026_prod_grade"
DB_HOST = "127.0.0.1"
DB_PORT = 5434
DB_NAME = "insilos20_dev"
DB_USER = "odoo"
DB_PASS = "1NN0R1@2026"


def get_webhook_secret():
    """Retrieve secret from environment or dev DB ir_config_parameter."""
    env_secret = os.environ.get("AL2C_TIMESHEET_WEBHOOK_SECRET")
    if env_secret:
        return env_secret
    try:
        conn = psycopg2.connect(
            host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS, dbname=DB_NAME, connect_timeout=3
        )
        cur = conn.cursor()
        cur.execute("SELECT value FROM ir_config_parameter WHERE key = 'insilos_al2c.timesheet_webhook_secret' LIMIT 1;")
        row = cur.fetchone()
        conn.close()
        if row and row[0]:
            return row[0].strip()
    except Exception as e:
        _logger.debug("Database config lookup skipped: %s", e)
    return DEFAULT_SECRET


def get_imap_credentials():
    """Retrieve IMAP credentials for info@inno.ai.vn from fetchmail_server in dev DB."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS, dbname=DB_NAME, connect_timeout=3
        )
        cur = conn.cursor()
        cur.execute("""
            SELECT server, port, "user", password, is_ssl
            FROM fetchmail_server
            WHERE "user" = 'info@inno.ai.vn' OR name ILIKE '%Google Workspace%'
            LIMIT 1;
        """)
        row = cur.fetchone()
        conn.close()
        if row:
            return {
                'server': row[0] or 'imap.gmail.com',
                'port': int(row[1] or 993),
                'user': row[2],
                'password': (row[3] or '').replace(' ', ''),
                'ssl': bool(row[4]),
            }
    except Exception as e:
        _logger.debug("Could not read fetchmail credentials: %s", e)
    return None


def sign_payload(secret: str, raw_bytes: bytes, timestamp: float) -> str:
    """Generate HMAC-SHA256 signature matching Al2cTimesheetWebhookController."""
    ts_bytes = str(timestamp).encode('utf-8')
    to_sign = ts_bytes + b'.' + raw_bytes
    return hmac.new(secret.encode('utf-8'), to_sign, hashlib.sha256).hexdigest()


def send_to_webhook(payload: dict, base_url: str = DEFAULT_ODD_URL, secret: str = None) -> dict:
    """Post JSON payload to AL2C timesheet webhook with signature headers."""
    if not secret:
        secret = get_webhook_secret()
    
    raw_bytes = json.dumps(payload).encode('utf-8')
    now_ts = time.time()
    sig = sign_payload(secret, raw_bytes, now_ts)
    
    url = f"{base_url.rstrip('/')}{DEFAULT_WEBHOOK_PATH}"
    headers = {
        'Content-Type': 'application/json',
        'X-Timestamp': str(now_ts),
        'X-Signature': sig,
        'User-Agent': 'Innoria-MailPubSub-Daemon/2.0',
    }
    
    req = urllib.request.Request(url, data=raw_bytes, headers=headers, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            status = resp.status
            body = resp.read().decode('utf-8')
            res_json = json.loads(body) if body else {}
            res_json['http_status'] = status
            return res_json
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8') if e.fp else ''
        _logger.error("Webhook HTTP %d: %s", e.code, err_body)
        return {'http_status': e.code, 'error': err_body}
    except Exception as e:
        _logger.error("Connection error to webhook: %s", e)
        return {'http_status': 0, 'error': str(e)}


def simulate_timesheet_intake(base_url: str, count: int = 1):
    """Synthesizes realistic Innoria timesheet submissions to exercise the pipeline."""
    _logger.info("=== BẮT ĐẦU MÔ PHỎNG TIẾP NHẬN TIMESHEET QUA PUBSUB / EMAIL ===")
    
    scenarios = [
        {
            'sender': 'consultant.a@inno.ai.vn',
            'subject': '[Timesheet] Bảng chấm công tuần 42 - Nguyễn Văn A (SAP Activate)',
            'body': (
                "2026-10-12 | Triển khai ERP & AI Port Automation — Saigon Newport (SAP Activate) | Explore Phase Architecture Workshop | 8.0 | Khảo sát quy trình tích hợp Cảng biển\n"
                "2026-10-13 | Triển khai ERP & AI Port Automation — Saigon Newport (SAP Activate) | Explore Phase Architecture Workshop | 7.5 | Thiết kế sơ đồ Fit-to-Standard\n"
            ),
            'filename': 'timesheet_w42_activate.csv',
            'csv': (
                "Date,Project,Task,Hours,Description\n"
                "2026-10-14,Triển khai ERP & AI Port Automation — Saigon Newport (SAP Activate),Explore Phase Architecture Workshop,8.0,Thiết kế kiến trúc tích hợp hệ thống TOS\n"
                "2026-10-15,Triển khai ERP & AI Port Automation — Saigon Newport (SAP Activate),Explore Phase Architecture Workshop,6.0,Hội thảo rà soát Gap Analysis & SoD\n"
            )
        },
        {
            'sender': 'tran.thi.b@inno.ai.vn',
            'subject': '[Timesheet] Log công tuần 42 - Trần Thị B (Mojo AI Copilot)',
            'body': (
                "2026-10-12 | Consulting Pool (T&M) | Khảo sát nhu cầu AI | 4.0 | Cài đặt môi trường Private AI\n"
                "2026-10-13 | Consulting Pool (T&M) | Khảo sát nhu cầu AI | 4.5 | Đào tạo mô hình phân loại chứng từ\n"
            ),
            'filename': 'timesheet_mojo_pilot.csv',
            'csv': (
                "Date,Project,Task,Hours,Description\n"
                "2026-10-14,Consulting Pool (T&M),Khảo sát nhu cầu AI,5.0,Tích hợp API OCR hóa đơn điện tử Nghị định 70\n"
            )
        }
    ]
    
    results = []
    for i in range(min(count, len(scenarios))):
        sc = scenarios[i]
        nonce = f"sim-{uuid.uuid4().hex[:12]}"
        
        att_b64 = base64.b64encode(sc['csv'].encode('utf-8')).decode('utf-8')
        payload = {
            'sender': sc['sender'],
            'subject': sc['subject'],
            'body': sc['body'],
            'channel': 'email_pubsub',
            'nonce': nonce,
            'attachments': [
                {
                    'filename': sc['filename'],
                    'content': att_b64,
                }
            ]
        }
        
        _logger.info("Đang gửi timesheet mô phỏng từ: %s | Tiêu đề: '%s'", sc['sender'], sc['subject'])
        res = send_to_webhook(payload, base_url=base_url)
        _logger.info("Kết quả webhook: HTTP %s -> %s", res.get('http_status'), res)
        results.append(res)
        
        # Test duplicate deduplication immediately
        _logger.info("Kiểm tra cơ chế chống trùng lặp (Idempotency Dedup) với cùng Nonce: %s...", nonce)
        res_dup = send_to_webhook(payload, base_url=base_url)
        _logger.info("Kết quả gửi lặp lại: %s (Status: %s)", res_dup.get('status'), res_dup.get('http_status'))
        
    return results


def poll_imap_inbox(creds: dict, base_url: str):
    """Connects to IMAP server (info@inno.ai.vn) and processes unread timesheet emails."""
    _logger.info("Kết nối IMAP tới %s:%d với user %s...", creds['server'], creds['port'], creds['user'])
    try:
        if creds['ssl']:
            mail = imaplib.IMAP4_SSL(creds['server'], creds['port'])
        else:
            mail = imaplib.IMAP4(creds['server'], creds['port'])
            mail.starttls()
            
        mail.login(creds['user'], creds['password'])
        mail.select('INBOX')
        
        # Search unread emails with timesheet keywords
        status, messages = mail.search(None, '(UNSEEN)')
        if status != 'OK':
            _logger.warning("Không thể tìm kiếm hộp thư: %s", status)
            mail.logout()
            return
            
        msg_ids = messages[0].split()
        _logger.info("Tìm thấy %d thư chưa đọc trong INBOX.", len(msg_ids))
        
        timesheet_count = 0
        for mid in msg_ids:
            res, data = mail.fetch(mid, '(RFC822)')
            if res != 'OK':
                continue
            raw_email = data[0][1]
            msg = email.message_from_bytes(raw_email, policy=policy.default)
            
            subject = str(msg.get('subject', ''))
            sender = str(msg.get('from', ''))
            
            # Check timesheet relevance
            is_timesheet = any(kw in subject.lower() for kw in ['timesheet', 'chấm công', 'bảng công', 'log time'])
            
            body = ""
            attachments = []
            if msg.is_multipart():
                for part in msg.walk():
                    ctype = part.get_content_type()
                    cdisp = str(part.get('Content-Disposition', ''))
                    if ctype == 'text/plain' and 'attachment' not in cdisp:
                        body += part.get_payload(decode=True).decode(part.get_content_charset() or 'utf-8', errors='replace')
                    elif 'attachment' in cdisp or part.get_filename():
                        fname = part.get_filename() or 'unnamed_file'
                        if fname.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.svg')):
                            continue
                        raw_payload = part.get_payload(decode=True)
                        if fname.lower().endswith(('.xlsx', '.xls', '.csv')):
                            is_timesheet = True
                        attachments.append({
                            'filename': fname,
                            'content': base64.b64encode(raw_payload).decode('utf-8') if raw_payload else ''
                        })
            else:
                body = msg.get_payload(decode=True).decode(msg.get_content_charset() or 'utf-8', errors='replace')
                
            if is_timesheet:
                timesheet_count += 1
                _logger.info("Phát hiện email Timesheet: [%s] từ %s. Đang đẩy vào AL2C Webhook...", subject, sender)
                payload = {
                    'sender': sender,
                    'subject': subject,
                    'body': body,
                    'channel': 'email_pubsub',
                    'nonce': f"imap-{msg.get('message-id', uuid.uuid4().hex)}",
                    'attachments': attachments,
                }
                res = send_to_webhook(payload, base_url=base_url)
                _logger.info("Đã xử lý email ID %s: Webhook response: %s", mid.decode('ascii'), res)
                
        mail.logout()
        _logger.info("Hoàn thành kiểm tra IMAP. Tổng số email timesheet đã xử lý: %d", timesheet_count)
    except Exception as e:
        _logger.error("Lỗi khi kết nối IMAP hoặc xử lý hòm thư: %s", e)


def main():
    parser = argparse.ArgumentParser(description="Innoria AL2C Mail Pub/Sub & Timesheet Webhook Daemon")
    parser.add_argument('--simulate', action='store_true', help='Run simulation of incoming timesheets')
    parser.add_argument('--once', action='store_true', help='Poll IMAP or PubSub once and exit')
    parser.add_argument('--daemon', action='store_true', help='Run continuous listener daemon')
    parser.add_argument('--url', default=DEFAULT_ODD_URL, help=f'Base ERP URL (default: {DEFAULT_ODD_URL})')
    parser.add_argument('--interval', type=int, default=60, help='Polling interval in seconds (default: 60)')
    args = parser.parse_args()

    _logger.info("Khởi chạy Innoria AL2C Mail Pub/Sub Ingestion Engine...")
    _logger.info("ERP Target URL: %s%s", args.url, DEFAULT_WEBHOOK_PATH)
    
    if args.simulate:
        simulate_timesheet_intake(args.url, count=2)
        return

    creds = get_imap_credentials()
    if not creds:
        _logger.warning("Không tìm thấy cấu hình IMAP cho info@inno.ai.vn trong DB. Chuyển sang chế độ mô phỏng...")
        simulate_timesheet_intake(args.url, count=1)
        return

    if args.once:
        poll_imap_inbox(creds, args.url)
        return

    if args.daemon:
        _logger.info("Chạy ở chế độ Daemon với chu kỳ %d giây. Nhấn Ctrl+C để dừng.", args.interval)
        try:
            while True:
                poll_imap_inbox(creds, args.url)
                time.sleep(args.interval)
        except KeyboardInterrupt:
            _logger.info("Đã nhận tín hiệu dừng daemon.")


if __name__ == '__main__':
    main()
