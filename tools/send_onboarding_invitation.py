#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/send_onboarding_invitation.py
Send Onboarding & Google OAuth Invitation Emails to @inno.ai.vn employees.
Adheres strictly to IBM Carbon Design Language & SAP Fiori Horizon standards.
Embeds the official small web Innoria logo (transparent PNG base64).
Uses verified Google Workspace SMTP server (info@inno.ai.vn).
"""
import os
import sys
import base64
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465
SMTP_USER = "info@inno.ai.vn"
SMTP_PASS = "hmqiukoacdxyhhuv"
SENDER_NAME = "Innoria Enterprise Systems"
PORTAL_URL = "https://innoria.com"

EMAIL_SUBJECT = "[Innoria Enterprise] Thư mời Kích hoạt Tài khoản & Đăng nhập Hệ thống Điều hành (Google SSO @inno.ai.vn)"

# Load small web Innoria logo as base64 for universal email client compatibility
LOGO_PATH = os.path.join(os.path.dirname(__file__), "..", "addons", "insilos_al2c", "static", "src", "img", "logo_innoria_header.png")
LOGO_BASE64 = ""
if os.path.exists(LOGO_PATH):
    with open(LOGO_PATH, "rb") as f:
        LOGO_BASE64 = base64.b64encode(f.read()).decode("utf-8")

def get_html_content(recipient_name="Anh/Chị", recipient_email=""):
    logo_img_tag = f'<img src="data:image/png;base64,{LOGO_BASE64}" style="max-height: 28px; width: auto; display: block; border: 0;" alt="Innoria Enterprise"/>' if LOGO_BASE64 else '<span style="font-size: 20px; font-weight: 800; color: #161616;">INNORIA <span style="color: #0070F2;">ENTERPRISE</span></span>'

    return f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Thư mời kích hoạt tài khoản Innoria Enterprise</title>
</head>
<body style="margin: 0; padding: 0; background-color: #F4F4F4; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; color: #161616; -webkit-font-smoothing: antialiased;">
    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #F4F4F4; padding: 32px 12px;">
        <tr>
            <td align="center">
                <!-- Master IBM Carbon Card Container -->
                <table border="0" cellpadding="0" cellspacing="0" width="640" style="background-color: #FFFFFF; border: 1px solid #E0E0E0; border-radius: 4px; overflow: hidden; box-shadow: 0 4px 16px rgba(0,0,0,0.06);">
                    
                    <!-- SAP Fiori Horizon Top Accent Stripe -->
                    <tr>
                        <td style="height: 4px; background: linear-gradient(90deg, #0070F2 0%, #0ABBDB 100%); font-size: 0px; line-height: 4px;">&nbsp;</td>
                    </tr>

                    <!-- Corporate Masthead with Small Web Innoria Logo -->
                    <tr>
                        <td style="padding: 20px 32px 16px 32px; border-bottom: 1px solid #EAEAEA;">
                            <table border="0" cellpadding="0" cellspacing="0" width="100%">
                                <tr>
                                    <td align="left" valign="middle">
                                        <a href="{PORTAL_URL}" target="_blank" style="text-decoration: none; display: inline-block;">
                                            {logo_img_tag}
                                        </a>
                                    </td>
                                    <td align="right" valign="middle">
                                        <span style="font-family: ui-monospace, Menlo, Monaco, Consolas, monospace; font-size: 10px; font-weight: 700; color: #525252; background-color: #F4F4F4; border: 1px solid #E0E0E0; padding: 4px 8px; border-radius: 2px; letter-spacing: 0.05em;">
                                            SSO · GOOGLE WORKSPACE
                                        </span>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Section Header Strip -->
                    <tr>
                        <td style="padding: 16px 32px 12px 32px; background-color: #F8F9FA; border-bottom: 1px solid #EAEAEA;">
                            <div style="font-size: 11px; font-weight: 700; text-transform: uppercase; color: #0070F2; letter-spacing: 0.05em; margin-bottom: 4px;">
                                KHÔNG GIAN LÀM VIỆC DOANH NGHIỆP / ENTERPRISE WORKSPACE
                            </div>
                            <div style="font-size: 18px; font-weight: 800; color: #161616; letter-spacing: -0.02em;">
                                Thư mời Kích hoạt Tài khoản &amp; Truy cập Hệ thống Điều hành
                            </div>
                        </td>
                    </tr>

                    <!-- Body Content -->
                    <tr>
                        <td style="padding: 32px 32px 24px 32px;">
                            <p style="margin: 0 0 16px 0; font-size: 15px; font-weight: 700; color: #161616;">
                                Kính gửi {recipient_name},
                            </p>
                            <p style="margin: 0 0 20px 0; font-size: 14px; line-height: 1.6; color: #333333;">
                                Nhằm chuẩn hóa quy trình điều hành và tối ưu hóa năng suất vận hành theo kiến trúc số hóa hiện đại, <strong>Innoria</strong> chính thức triển khai nền tảng quản trị tổng thể doanh nghiệp <strong>Insilos Enterprise Platform v20.0</strong> dành cho toàn bộ nhân sự tại:
                            </p>

                            <!-- SAP Fiori Horizon Facets: System Specs -->
                            <div style="background-color: #F8F9FA; border: 1px solid #E0E0E0; border-left: 4px solid #0070F2; border-radius: 4px; padding: 16px; margin-bottom: 24px;">
                                <table border="0" cellpadding="0" cellspacing="0" width="100%" style="font-size: 13px; line-height: 1.6;">
                                    <tr>
                                        <td style="color: #525252; width: 35%; padding-bottom: 6px;">Cổng truy cập:</td>
                                        <td style="font-weight: 700; color: #0070F2; width: 65%; padding-bottom: 6px;">
                                            <a href="{PORTAL_URL}" target="_blank" style="color: #0070F2; text-decoration: none;">{PORTAL_URL}</a>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style="color: #525252; padding-bottom: 6px;">Cơ chế đăng nhập:</td>
                                        <td style="font-weight: 600; color: #161616; padding-bottom: 6px;">
                                            Google OAuth 2.0 Single Sign-On (Một chạm)
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style="color: #525252; padding-bottom: 6px;">Hòm thư ủy quyền:</td>
                                        <td style="font-family: ui-monospace, Menlo, Monaco, Consolas, monospace; font-weight: 700; color: #161616; padding-bottom: 6px;">
                                            {recipient_email if recipient_email else '@inno.ai.vn'}
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style="color: #525252;">Phân hệ hoạt động:</td>
                                        <td style="color: #333333;">
                                            AL2C (Lead-to-Cash), CRM, Dự án SAP Activate, E-Invoice, Tri thức Doanh nghiệp
                                        </td>
                                    </tr>
                                </table>
                            </div>

                            <p style="margin: 0 0 20px 0; font-size: 14px; line-height: 1.6; color: #333333;">
                                Toàn bộ cán bộ nhân viên sử dụng email có đuôi <strong>@inno.ai.vn</strong> đã được cấu hình đăng nhập tự động qua tài khoản Google Workspace. <strong>Anh/Chị không cần tạo hay ghi nhớ mật khẩu mới!</strong>
                            </p>

                            <!-- SAP Fiori Horizon Primary Action Button -->
                            <table border="0" cellpadding="0" cellspacing="0" width="100%" style="margin: 28px 0;">
                                <tr>
                                    <td align="center">
                                        <a href="{PORTAL_URL}" target="_blank" style="display: inline-block; background-color: #0070F2; color: #FFFFFF; font-size: 14px; font-weight: 600; text-decoration: none; padding: 14px 36px; border-radius: 4px; box-shadow: 0 4px 12px rgba(0, 112, 242, 0.35);">
                                            Đăng Nhập Ngay Bằng Google (@inno.ai.vn)
                                        </a>
                                    </td>
                                </tr>
                            </table>

                            <!-- IBM Carbon Step Guide -->
                            <div style="margin-top: 24px; margin-bottom: 24px;">
                                <div style="font-size: 12px; font-weight: 700; text-transform: uppercase; color: #161616; letter-spacing: 0.05em; margin-bottom: 12px;">
                                    3 BƯỚC ĐĂNG NHẬP NHANH:
                                </div>
                                <table border="0" cellpadding="0" cellspacing="0" width="100%" style="font-size: 13px; line-height: 1.6;">
                                    <tr>
                                        <td valign="top" style="width: 28px; padding-bottom: 10px;">
                                            <div style="background-color: #0070F2; color: #FFFFFF; width: 20px; height: 20px; border-radius: 50%; text-align: center; line-height: 20px; font-size: 11px; font-weight: 700;">1</div>
                                        </td>
                                        <td valign="top" style="color: #333333; padding-bottom: 10px;">
                                            Truy cập liên kết hệ thống: <a href="{PORTAL_URL}" target="_blank" style="color: #0070F2; text-decoration: none; font-weight: 600;">{PORTAL_URL}</a>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td valign="top" style="width: 28px; padding-bottom: 10px;">
                                            <div style="background-color: #0070F2; color: #FFFFFF; width: 20px; height: 20px; border-radius: 50%; text-align: center; line-height: 20px; font-size: 11px; font-weight: 700;">2</div>
                                        </td>
                                        <td valign="top" style="color: #333333; padding-bottom: 10px;">
                                            Tại giao diện đăng nhập, nhấp chọn nút <strong>"Đăng nhập bằng Google (@inno.ai.vn)"</strong>.
                                        </td>
                                    </tr>
                                    <tr>
                                        <td valign="top" style="width: 28px; padding-bottom: 10px;">
                                            <div style="background-color: #0070F2; color: #FFFFFF; width: 20px; height: 20px; border-radius: 50%; text-align: center; line-height: 20px; font-size: 11px; font-weight: 700;">3</div>
                                        </td>
                                        <td valign="top" style="color: #333333; padding-bottom: 10px;">
                                            Chọn hòm thư Google công việc của Anh/Chị. Hệ thống sẽ tự động đối soát định danh và chuyển hướng trực tiếp vào không gian làm việc.
                                        </td>
                                    </tr>
                                </table>
                            </div>

                            <!-- ISO 27001 Security Notice -->
                            <div style="background-color: #FFFBEB; border: 1px solid #FDE68A; border-radius: 4px; padding: 12px 16px; font-size: 12px; color: #92400E; line-height: 1.5;">
                                <strong>Lưu ý bảo mật &amp; Tuân thủ ISO/IEC 27001:</strong> Vui lòng đảm bảo tài khoản Google Workspace của Anh/Chị đã kích hoạt <strong>Xác thực 2 bước (2-Step Verification)</strong>. Không chia sẻ tài khoản hoặc truy cập hệ thống từ các thiết bị công cộng chưa được kiểm duyệt.
                            </div>
                        </td>
                    </tr>

                    <!-- Enterprise Legal & Compliance Footer -->
                    <tr>
                        <td style="background-color: #F8F9FA; border-top: 1px solid #E0E0E0; padding: 20px 32px; font-size: 11px; line-height: 1.6; color: #6F6F6F;">
                            <table border="0" cellpadding="0" cellspacing="0" width="100%">
                                <tr>
                                    <td valign="top" style="width: 70%;">
                                        <strong style="color: #161616;">CÔNG TY CỔ PHẦN GIẢI PHÁP INNORIA (INNORIA SOLUTIONS JSC)</strong><br/>
                                        Ban Công nghệ Thông tin &amp; Quản trị Vận hành Hệ thống<br/>
                                        Hỗ trợ kỹ thuật: <a href="mailto:info@inno.ai.vn" style="color: #0070F2; text-decoration: none;">info@inno.ai.vn</a> | Quản trị viên: <a href="mailto:thang@inno.ai.vn" style="color: #0070F2; text-decoration: none;">thang@inno.ai.vn</a><br/>
                                        <span style="font-size: 10px; color: #8D8D8D; margin-top: 4px; display: block;">
                                            Hệ thống quản lý tuân thủ Tiêu chuẩn An ninh Thông tin ISO/IEC 27001:2022 và Nghị định 13/2023/NĐ-CP về Bảo vệ Dữ liệu Cá nhân.
                                        </span>
                                    </td>
                                    <td valign="top" align="right" style="width: 30%;">
                                        <span style="color: #161616; font-weight: 700;">INNORIA ENTERPRISE</span><br/>
                                        <a href="{PORTAL_URL}" target="_blank" style="color: #0070F2; text-decoration: none; font-size: 10px; font-weight: 600;">innoria.com</a>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""

def get_text_content(recipient_name="Anh/Chị", recipient_email=""):
    return f"""Kính gửi {recipient_name},

Nhằm chuẩn hóa quy trình điều hành và tối ưu hóa năng suất vận hành theo kiến trúc số hóa hiện đại, Innoria chính thức triển khai nền tảng quản trị tổng thể doanh nghiệp Insilos Enterprise Platform v20.0 tại địa chỉ: {PORTAL_URL}

Toàn bộ cán bộ nhân viên sử dụng email @inno.ai.vn đã được kích hoạt tính năng Đăng nhập một chạm (Single Sign-On - SSO) qua Google Workspace. Anh/Chị KHÔNG CẦN KHỞI TẠO HAY GHI NHỚ MẬT KHẨU MỚI!

HƯỚNG DẪN 3 BƯỚC ĐĂNG NHẬP:
1. Truy cập vào cổng làm việc: {PORTAL_URL}
2. Tại màn hình đăng nhập, nhấp chọn nút "Đăng nhập bằng Google (@inno.ai.vn)".
3. Chọn tài khoản Google công việc ({recipient_email if recipient_email else 'tenban@inno.ai.vn'}). Hệ thống sẽ tự động xác thực và kích hoạt không gian làm việc.

CÁC PHÂN HỆ VẬN HÀNH CHÍNH TRÊN HỆ THỐNG:
• Quản trị Khách hàng & Thẩm định Cơ hội Kinh doanh (CRM BANT/MEDDICC)
• Quản lý Dự án Triển khai Chuẩn SAP Activate 5 Pha
• Xuất & Đối soát Hóa đơn Điện tử Nghị định 70/2025/NĐ-CP & Nghị định 123/2020/NĐ-CP
• Cơ sở Tri thức & Tài liệu Sản phẩm Doanh nghiệp (Knowledge Base)

LƯU Ý BẢO MẬT & TUÂN THỦ ISO 27001:
Để đảm bảo an toàn dữ liệu khách hàng và chủ quyền thông tin, vui lòng đảm bảo tài khoản Google Workspace của Anh/Chị đã kích hoạt Xác thực 2 bước (2-Step Verification).

Mọi thắc mắc và yêu cầu hỗ trợ kỹ thuật, xin vui lòng liên hệ:
- Email hỗ trợ: info@inno.ai.vn
- Quản trị viên hệ thống: thang@inno.ai.vn

Trân trọng,
Ban Công nghệ & Vận hành Innoria
"""

def send_invitation_email(to_email, recipient_name="Cán bộ Nhân viên"):
    print(f"[*] Đang gửi email mời kích hoạt (Chuẩn IBM/SAP Fiori) tới: {to_email} ...")
    msg = MIMEMultipart("alternative")
    msg["Subject"] = EMAIL_SUBJECT
    msg["From"] = f"{SENDER_NAME} <{SMTP_USER}>"
    msg["To"] = to_email

    part_text = MIMEText(get_text_content(recipient_name, to_email), "plain", "utf-8")
    part_html = MIMEText(get_html_content(recipient_name, to_email), "html", "utf-8")

    msg.attach(part_text)
    msg.attach(part_html)

    try:
        server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=15)
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(SMTP_USER, [to_email], msg.as_string())
        server.quit()
        print(f"   [SUCCESS] Đã gửi thư mời chuẩn IBM/SAP thành công tới {to_email}!")
        return True
    except Exception as e:
        print(f"   [ERROR] Gửi email thất bại tới {to_email}: {e}")
        return False

def get_inno_employees_from_db(db_name="insilos20_dev"):
    import psycopg2
    try:
        conn = psycopg2.connect(host="127.0.0.1", port=5434, dbname=db_name, user="odoo")
        cur = conn.cursor()
        cur.execute("""
            SELECT e.name, COALESCE(e.work_email, u.login) as email
            FROM hr_employee e
            LEFT JOIN res_users u ON e.user_id = u.id
            WHERE e.work_email LIKE '%@inno.ai.vn' OR u.login LIKE '%@inno.ai.vn'
            UNION
            SELECT p.name, u.login as email
            FROM res_users u
            JOIN res_partner p ON u.partner_id = p.id
            WHERE u.login LIKE '%@inno.ai.vn'
        """)
        return cur.fetchall()
    except Exception as e:
        print(f"[ERROR] Không thể truy vấn database {db_name}: {e}")
        return []

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--all-employees":
            print("[*] Đang quét danh sách nhân sự có hòm thư @inno.ai.vn từ cơ sở dữ liệu...")
            employees = get_inno_employees_from_db()
            if not employees:
                print("   [INFO] Chưa tìm thấy nhân sự nào có email @inno.ai.vn trong database 'insilos20_dev'.")
                print("   [HƯỚNG DẪN] Bạn có thể gửi trực tiếp bằng lệnh:")
                print("   python3 tools/send_onboarding_invitation.py <email@inno.ai.vn> '<Tên Nhân Viên>'")
            else:
                print(f"   [FOUND] Tìm thấy {len(employees)} nhân sự:")
                for name, email in employees:
                    print(f"   - {name} <{email}>")
                confirm = input("Xác nhận gửi email mời onboarding cho tất cả nhân sự trên? (y/n): ")
                if confirm.lower() == 'y':
                    for name, email in employees:
                        send_invitation_email(email, name)
        else:
            target = sys.argv[1]
            name = sys.argv[2] if len(sys.argv) > 2 else "Cán bộ Nhân viên"
            send_invitation_email(target, name)
    else:
        print("Usage: python3 tools/send_onboarding_invitation.py <recipient_email> [recipient_name]")
        print("   hoặc: python3 tools/send_onboarding_invitation.py --all-employees")
        print("Ví dụ: python3 tools/send_onboarding_invitation.py thang@inno.ai.vn 'Anh Thắng'")
