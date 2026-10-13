# SOP-KNW-002: Quản Trị Hệ Thống Tri Thức Doanh Nghiệp (Corporate Knowledge Management System - KMS) & Bộ Nhớ Tổ Chức (Organizational Memory)

> **Mã quy trình:** SOP-KNW-002  
> **Phiên bản:** 2.0 (Tháng 10/2026 - Tích hợp Nguồn Tri Thức Thẩm Quyền Single Source of Truth)  
> **Phạm vi áp dụng:** Toàn bộ cơ sở tri thức nghiệp vụ, danh mục sản phẩm, cẩm nang triển khai, thư viện hồ sơ thầu (RFP), và tài liệu định vị cạnh tranh (Battlecards) trên phân hệ `knowledge.article` của Innoria Enterprise.  
> **Chủ quản quy trình:** Giám đốc Công nghệ (CTO), Giám đốc Doanh thu (CRO), Trưởng các Trung tâm Xuất sắc (CoE Leads).

---

## 1. Mục Đích & Nguyên Lý Tri Thức Nguồn Thẩm Quyền

### 1.1. Mục Đích
Xây dựng một "Bộ Nhớ Tổ Chức" (Organizational Memory) duy nhất, có cấu trúc chặt chẽ và luôn được cập nhật theo thời gian thực, nhằm:
1. **Nguồn Dữ Liệu Thẩm Quyền Duy Nhất (Single Source of Truth - SSOT):** Chấm dứt tình trạng tài liệu phân tán, thông tin sai lệch về tính năng sản phẩm, đơn giá dịch vụ và chính sách chiết khấu.
2. **Cơ Sở Nền Tảng Cho RAG & Trợ Lý Ảo AI (Grounding Bedrock for AI):** Cung cấp dữ liệu đã được chứng thực (Verified Grounded Knowledge) để các mô hình trí tuệ nhân tạo (Mojo AI, Website Copilot, RFP Generator) trích dẫn chính xác 100%, không bị ảo giác (Zero Hallucination).
3. **Bảo Tồn & Chuyển Giao Tri Thức Dự Án:** Tự động hóa quá trình đúc rút kinh nghiệm sau mỗi dự án triển khai (Post-mortems), biến kinh nghiệm cá nhân thành tài sản trí tuệ chung của doanh nghiệp.

### 1.2. 7 Không Gian Tri Thức Cốt Lõi (Core Knowledge Spaces)
```
┌──────────────────────────────────────────────────────────────────────────────────┐
│              CƠ CẤU KHÔNG GIAN TRI THỨC DOANH NGHIỆP (KNOWLEDGE SPACES)          │
├───────────────┬───────────────┬───────────────┬────────────────┬─────────────────┤
│ 1. PRODUCTS   │ 2. INDUSTRIES │ 3. PLAYBOOKS  │ 4. BATTLECARDS │ 5. RFP LIBRARY  │
│ (SSOT SKUs)   │ (Verticals)   │ (How We Work) │ (Competitors)  │ (Tender QA)     │
├───────────────┼───────────────┼───────────────┼────────────────┼─────────────────┤
│ • ERP Lines   │ • Banking/Fin │ • Sales & Deal│ • vs SAP S/4   │ • Security QA   │
│ • GRC Specs   │ • Manufacture │ • Presales Fit│ • vs NetSuite  │ • Architecture  │
│ • Mojo AI App │ • Retail/Omni │ • Activate SOP│ • vs Vanilla   │ • Compliance    │
│ • Zencode Ent │ • Logistics   │ • Hypercare   │ • Win/Loss Pitch • Legal Terms   │
├───────────────┴───────────────┴───────────────┴────────────────┴─────────────────┤
│ 6. POST-MORTEMS (Project Delivery Retro • Incident RCA • Customer Win/Loss)     │
│ 7. COMPLIANCE (Decree 70/2025 Tax • Decree 13/2023 PDPD • ISO 27001 Controls)   │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Đặc Tả Chi Tiết Từng Không Gian Tri Thức

### 2.1. Không Gian `/Products` (Sản Phẩm & Danh Mục Dịch Vụ)
- **Mã nhận diện gốc:** `insilos_al2c.kb_products`
- **Nguyên tắc SSOT:** Mỗi mã SKU thương mại (trong số 21 SKUs chuẩn) sở hữu duy nhất 1 bài viết tri thức mô tả đầy đủ:
  - Tên thương mại & Mã SKU (`default_code`).
  - Chính sách dịch vụ (`service_policy`): trả trước (`ordered_prepaid`), theo mốc (`delivered_milestones`), hay theo giờ công (`delivered_timesheet`).
  - Phạm vi bao gồm (Scope & Included Deliverables).
  - Giả định kỹ thuật (Assumptions) & Điểm loại trừ (Exclusions).
  - Đơn giá cơ sở và chính sách gia hạn thuê bao (SaaS Recurring).

### 2.2. Không Gian `/Industries` (Giải Pháp Theo Ngành)
- **Mã nhận diện gốc:** `insilos_al2c.kb_industries`
- Chứa các kịch bản chuẩn Fit-to-Standard theo từng ngành mũi nhọn:
  - *Tài chính - Ngân hàng (Fintech/Banking):* Tuân thủ bảo mật dữ liệu khách hàng, quản trị rủi ro thanh khoản, đối soát giao dịch liên ngân hàng.
  - *Sản xuất (Manufacturing):* Hoạch định nhu cầu nguyên vật liệu (MRP), quản lý định mức BOM, kiểm soát chất lượng QA/QC.
  - *Bán lẻ & Chuỗi F&B (Retail/Omnichannel):* Tích hợp POS bán hàng đa kênh, quản trị kho tập trung, chương trình khách hàng thân thiết.
  - *Giao vận & Kho bãi (Logistics/3PL):* Quản lý hạm đội vận tải (TMS), tối ưu vị trí lưu kho (WMS), định tuyến thông minh.

### 2.3. Không Gian `/Playbooks` (Cẩm Nang Vận Hành)
- **Mã nhận diện gốc:** `insilos_al2c.kb_playbooks`
- Hướng dẫn thực hành chi tiết theo chuẩn mực thế giới:
  - *Cẩm nang Bán hàng (Sales Playbook):* Phương pháp tiếp cận khách hàng doanh nghiệp lớn, nghệ thuật trình diễn giải pháp (Demo Script), hàng rào chiết khấu Deal-Desk.
  - *Cẩm nang Triển khai (Delivery Playbook):* Khung phương pháp luận SAP Activate 5 pha (Prepare, Explore, Realize, Deploy, Run) và hướng dẫn tổ chức hội thảo Fit-to-Standard.

### 2.4. Không Gian `/Battlecards` (Vũ Khí Cạnh Tranh Thương Mại)
- **Mã nhận diện gốc:** `insilos_al2c.kb_battlecards`
- Phân tích so sánh tính năng, chi phí TCO và lợi thế cạnh tranh cốt lõi:
  - *Vs. SAP S/4HANA Cloud:* Thời gian triển khai nhanh gấp 3 lần (6-12 tuần vs 9-18 tháng), chi phí TCO thấp hơn 65%, giao diện Fiori Horizon hiện đại, kế toán Việt Nam bản địa hóa chuyên sâu.
  - *Vs. Oracle NetSuite:* Linh hoạt tùy biến quy trình theo phương pháp Clean Core, không bị khóa cứng nhà cung cấp (Zero Vendor Lock-in), hỗ trợ triển khai lai (Hybrid On-premise/Private Cloud).
  - *Vs. Odoo Vanilla / ERPNext:* Loại bỏ triệt để giao diện nghiệp dư, chuẩn hóa kiểm soát an ninh cấp doanh nghiệp (SoD, Token-bucket rate limiter, Decree 70/2025 e-invoice native).

### 2.5. Không Gian `/RFP_Library` (Thư Viện Câu Hỏi Thầu & Thẩm Định An Ninh)
- **Mã nhận diện gốc:** `insilos_al2c.kb_rfp`
- Tập hợp hơn 200+ câu trả lời chuẩn đã được phê duyệt bởi Ban Pháp chế và CISO:
  - Tiêu chuẩn an ninh hạ tầng trung tâm dữ liệu (Tier III, ISO 27001).
  - Chính sách sao lưu dự phòng (RPO $\le 15$ phút, RTO $\le 2$ giờ).
  - Cơ chế phân quyền và ghi vết truy cập quản trị hệ thống.

---

## 3. Quy Trình Duy Trì Độ Tươi Mới Của Tri Thức (Knowledge Freshness Governance)

```
[Khởi Tạo Bài Viết Tri Thức]
               │
               ▼
[Gắn Thẻ Sở Hữu CoE Lead (Owner Attribution)]
- Phân công rõ ràng chuyên gia phụ trách nội dung
               │
               ▼
[Chu Kỳ Rà Soát Bắt Buộc (SLA Review Cycle)]
- Battlecards: Định kỳ tối đa 30 ngày / lần
- Product SKUs & RFP Library: Định kỳ tối đa 90 ngày / lần
               │
               ▼
[Kiểm Định Độ Lệch Tri Thức (Knowledge Drift Alert)]
- Hệ thống tự động quét ngày cập nhật gần nhất (write_date)
- Cảnh báo vàng (Amber) khi quá 60 ngày chưa cập nhật
- Khóa tự động và cảnh báo đỏ (Red) khi quá 90 ngày: Cấm AI dùng làm Grounding Source
               │
               ▼
[Phê Duyệt Tái Xác Thực (Re-certification Sign-off)]
- CoE Lead ký xác nhận tính chính xác -> Gia hạn chu kỳ tươi mới
```

---

## 4. Cơ Chế Đồng Bộ Hai Chiều Giữa Git Markdown Và Odoo KMS

Để kết hợp hoàn hảo giữa quy trình làm việc của kỹ sư phần mềm (Git-centric) và người dùng khối kinh doanh/vận hành (Web-centric):
1. **Từ Git sang Odoo KMS (`/docs` $\longrightarrow$ `knowledge.article`):**
   - Bộ quét tự động `tools/sync_knowledge_docs.py` đọc các file markdown chuẩn trong thư mục `docs/organization_and_processes/`.
   - Chuyển đổi định dạng Markdown sang QWeb HTML chuẩn (IBM Carbon typography).
   - Cập nhật hoặc tạo mới bản ghi `knowledge.article` tương ứng trên môi trường với khóa định danh duy nhất (Slug).
2. **Từ Odoo KMS sang Git (`knowledge.article` $\longrightarrow$ `/docs`):**
   - Khi chuyên gia nội dung chỉnh sửa bài viết trên giao diện Cổng Tri Thức, một sự kiện Webhook kích hoạt commit tự động vào nhánh tài liệu của kho lưu trữ.
   - Toàn bộ lịch sử thay đổi (Git Diff) được lưu giữ vĩnh viễn, ngăn ngừa rủi ro mất mát dữ liệu tri thức.

---
*Lưu hành nội bộ - Ban Quản trị Tri thức Doanh nghiệp UNG DUNG SANG TAO LLC / INNORIA ENTERPRISE.*
