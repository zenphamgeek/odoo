# SOP-DOC-001: Quản Trị Hệ Thống Tài Liệu Doanh Nghiệp (Enterprise Document Management System - DMS) & An Toàn Thông Tin Số

> **Mã quy trình:** SOP-DOC-001  
> **Phiên bản:** 2.0 (Tháng 10/2026 - Chuẩn hóa Enterprise Multi-Tenant)  
> **Phạm vi áp dụng:** Toàn bộ hồ sơ số, hợp đồng thương mại, tài liệu kỹ thuật, biên bản bàn giao mốc dự án, và bằng chứng kiểm toán thuộc Hệ sinh thái Innoria Enterprise (`innoria.com` / `insilos.com`).  
> **Chủ quản quy trình:** Giám đốc An toàn Thông tin (CISO), Trưởng Ban Pháp chế & Tuân thủ (Head of Legal & Compliance), Giám đốc Vận hành Dịch vụ (CSO).

---

## 1. Mục Đích & Nguyên Tắc Cốt Lõi

### 1.1. Mục Đích
Thiết lập quy trình chuẩn hóa toàn bộ vòng đời tài liệu doanh nghiệp (DMS Lifecycle) dựa trên phân hệ `documents.document` của Insilos ERP, đảm bảo:
1. **Tuân thủ Pháp định Khắt khe:** Đáp ứng tuyệt đối Luật Giao dịch điện tử 2023, Nghị định 13/2023/NĐ-CP (Bảo vệ dữ liệu cá nhân - PDPD), Nghị định 70/2025/NĐ-CP (Chứng từ điện tử kế toán), và chuẩn an ninh ISO/IEC 27001:2022.
2. **Liêm Chính & Bất Biến (Integrity & Immutability):** Mọi hợp đồng, biên bản nghiệm thu (Deliverables) đã ký số phải được khóa sửa đổi, lưu vết kiểm toán (Audit Trail) chi tiết và có mã băm SHA-256 định danh.
3. **Phân Quyền Ngăn Ngừa Rò Rỉ (Segregation of Duties & Access Isolation):** Ngăn chặn triệt để nguy cơ lộ lọt dữ liệu nội bộ qua cơ chế kiểm soát liên kết công khai (`is_access_via_link_hidden`) và cách ly thư mục nhạy cảm.

### 1.2. 4 Trụ Cột Quản Trị Tài Liệu
```
┌──────────────────────────────────────────────────────────────────────────────────┐
│              HỆ THỐNG QUẢN TRỊ TÀI LIỆU SỐ DOANH NGHIỆP (ENTERPRISE DMS)          │
├────────────────────┬────────────────────┬───────────────────┬────────────────────┤
│   PRODUCT DOCS     │    PROPOSALS &     │   DELIVERABLES    │    COMPLIANCE      │
│     & SPECS        │     CONTRACTS      │  (SAP ACTIVATE)   │     EVIDENCE       │
├────────────────────┼────────────────────┼───────────────────┼────────────────────┤
│ • Whitepapers      │ • Commercial SOW   │ • Business Blue-  │ • ISO 27001 Audits │
│ • Architecture Doc │ • Service Contract │   print (Explore) │ • PDPD Consents    │
│ • API Catalogs     │ • Chữ ký số điện tử│ • UAT Sign-off    │ • Decree 70 Tax    │
│ • Release Notes    │ • SoD Strict Lock  │ • Cutover Runbook │ • SOC 2 Evidence   │
└────────────────────┴────────────────────┴───────────────────┴────────────────────┘
```

---

## 2. Cấu Trúc Cây Thư Mục Không Gian Làm Việc (Workspace Taxonomy)

Hệ thống tài liệu được tổ chức phân cấp trên mô hình `documents.document` với thuộc tính `type='folder'`:

```
/ (Root DMS Workspace)
├── [60] Product Docs (access_internal: view)
│   ├── ERP (ERP-STARTER, ERP-GROWTH, ERP-ENT, SAAS-HOSTING-PRO, SAAS-SLA-PLUS)
│   ├── GRC (GRC-ESSENTIALS, GRC-RISK-REGISTER, GRC-AUDIT-PACK)
│   ├── AI Solutions (AI-DISCOVERY, AI-POC, AI-PILOT, AI-PROD)
│   ├── Mojo AI Apps (MOJO-APP-SUB, MOJO-TOKENS, MOJO-ONPREM)
│   └── Services (AMS-BRONZE, AMS-SILVER, AMS-GOLD, TRAINING-DAY, CONSULT-HOUR)
├── [61] Proposals (access_internal: edit)
│   ├── Commercial Quotations (Báo giá thương mại theo chuẩn IBM Carbon)
│   └── Statements of Work (SOW - Phạm vi công việc dự án theo mốc)
├── [62] Contracts (access_internal: none, access_via_link: none, is_access_via_link_hidden: true)
│   ├── Master Service Agreements (Hợp đồng nguyên tắc MSA)
│   ├── Non-Disclosure Agreements (Thỏa thuận bảo mật thông tin NDA)
│   └── Data Processing Agreements (DPA tuân thủ Nghị định 13/2023/NĐ-CP)
├── [63] Deliverables (access_internal: edit)
│   ├── Prepare (Project Charter, Governance Structure)
│   ├── Explore (Fit-to-Standard Matrix, Business Blueprint)
│   ├── Realize (Configuration Specs, Integration Tests, Data Migration Sign-off)
│   ├── Deploy (Cutover Checklist, User Training Records, Go-Live Protocol)
│   └── Run (Hypercare Handover, Operational SLA Certificate)
├── [64] Marketing Assets (access_internal: edit)
│   ├── Brand Guidelines, Logos, Typography Sheets
│   └── Case Studies, Solution Briefs, Deck Presentations
└── [65] Compliance Evidence (access_internal: view)
    ├── Security Incident Reports & Post-mortems
    ├── Periodic Penetration Testing Reports
    └── Statutory Tax E-Invoice XML Bundles & Digital Signatures
```

---

## 3. Hệ Thống Thẻ & Nhãn Phân Loại (Metadata Facets & Tags)

Mỗi tài liệu đưa vào hệ thống bắt buộc phải được gắn ít nhất một Thẻ Nhận Diện (`documents.tag`):

| Thẻ Phân Loại (Tag Name) | Mã Nhận Diện XML | Mô Tả Nghiệp Vụ | Thẩm Quyền Truy Cập |
|---|---|---|---|
| `L2C > Proposal` | `insilos_al2c.tag_proposal` | Hồ sơ đề xuất thương mại, bản ước tính chi phí giải pháp | Nhân viên Kinh doanh, Quản lý Kinh doanh |
| `L2C > Contract` | `insilos_al2c.tag_contract` | Hợp đồng dịch vụ có tính ràng buộc pháp lý | Kế toán trưởng, Giám đốc Pháp chế, Ban Tổng Giám đốc |
| `L2C > Deliverable` | `insilos_al2c.tag_deliverable` | Biên bản nghiệm thu bàn giao mốc dự án (Milestone Deliverable) | Quản lý Dự án (PM), Kiến trúc sư Giải pháp |
| `L2C > Marketing Asset` | `insilos_al2c.tag_marketing_asset` | Tài liệu quảng bá, brochure, slide trình chiếu đối tác | Toàn bộ nhân viên nội bộ |
| `L2C > Compliance Evidence`| `insilos_al2c.tag_compliance_evidence`| Chứng từ kiểm toán bảo mật, giấy chứng nhận tuân thủ | CISO, Trưởng Ban Kiểm soát Nội bộ |

---

## 4. Vòng Đời Tài Liệu Số (Document Lifecycle State Machine)

```
[1. Tiếp Nhận / Khởi Tạo (Draft)]
               │
               ▼
[2. Thẩm Định Đồng Cấp (Peer Review)]
- Rà soát kỹ thuật (CoE Lead)
- Rà soát thương mại (Deal-Desk Manager)
               │
               ▼
[3. Thẩm Định Pháp Lý & Tuân Thủ (Legal & Compliance Sign-off)]
- Đối soát điều khoản bảo vệ dữ liệu PDPD (Nghị định 13/2023)
- Kiểm tra tính tuân thủ thuế & VAT (Nghị định 70/2025)
               │
               ▼
[4. Ký Số Điện Tử (Digital Signature - sign.request)]
- Ký số bằng USB Token PKI / HSM Server (Chuẩn chữ ký số Việt Nam)
- Lưu mã băm SHA-256 của file PDF đã ký vào cơ sở dữ liệu
               │
               ▼
[5. Hiệu Lực Vận Hành (Active & Locked)]
- Tài liệu chuyển chế độ Chỉ Đọc (Read-Only)
- Khóa toàn bộ quyền chỉnh sửa hoặc ghi đè (Immutable Storage)
               │
               ▼
[6. Lưu Trữ & Hủy Hạn Định (Retention & Secure Purge)]
- Thời gian lưu trữ hợp đồng & chứng từ kế toán: Tối thiểu 10 năm theo Luật Kế toán
- Hủy tài liệu bảo mật hết hạn bằng phương pháp ghi đè băm mật mã
```

---

## 5. Hàng Rào Bảo Mật Bất Biến Cho Tài Liệu (Security & Privacy Invariants)

1. **Khóa Liên Kết Ngoại Tuyến Thư Mục Hợp Đồng (CWE-639 / IDOR Defense):**
   - Thư mục `Contracts` (`folder_contracts`) bắt buộc cấu hình `access_internal = 'none'` và `is_access_via_link_hidden = True`.
   - Nghiêm cấm tạo URL chia sẻ công khai không qua xác thực đối với bất kỳ tài liệu nào mang tag `L2C > Contract`.
2. **Ký Sốdeliverable Trước Khi Kích Hoạt Hóa Đơn (Milestone Invariant):**
   - Không một hóa đơn mốc triển khai (Milestone Invoice) nào được phép tạo nếu Biên bản nghiệm thu bàn giao mốc tương ứng chưa có chữ ký số điện tử hợp lệ lưu trong thư mục `Deliverables`.
3. **Mã Hóa Dữ Liệu Lưu Trữ (Encryption at Rest & in Transit):**
   - File nhị phân lưu trữ tại Filestore được bảo vệ bằng quyền hạn tệp `chmod 0600`, đường truyền HTTPS TLS 1.3 bắt buộc mã hóa toàn trình.

---
*Lưu hành nội bộ - Ban Pháp chế, An toàn Thông tin & Vận hành Doanh nghiệp.*
