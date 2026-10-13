# SOP-EA-006: Kiến Trúc Doanh Nghiệp Hợp Nhất (Enterprise Architecture) & Cơ Chế Hiệp Đồng Tứ Trụ Sản Phẩm (Cross-Product Synergy)

> **Mã quy trình:** SOP-EA-006  
> **Phiên bản:** 2.0 (Tháng 10/2026 - Tích hợp Tứ Trụ Công Nghệ Insilos)  
> **Phạm vi áp dụng:** 4 Nền tảng cốt lõi: **Insilos ERP**, **Vertical Resilience**, **Mojo AI**, **Zencode Ent**.  
> **Chủ quản quy trình:** Giám đốc Công nghệ (CTO), Hội đồng Kiến trúc Doanh nghiệp (Enterprise Architecture Board - EAB).

---

## 1. Tầm Nhìn Kiến Trúc Tứ Trụ (The Quad-Core Operating Topology)

Mô hình hoạt động của công ty Software Services được thiết kế theo cấu trúc phân tầng vi dịch vụ và module có chủ quyền (Sovereign Modules), trong đó mỗi sản phẩm đóng vai trò một động cơ chuyên biệt nhưng vận hành trên một mặt bằng dữ liệu và bảo mật đồng nhất:

```
                                  ┌─────────────────────────────────────────────────────────┐
                                  │           ENTERPRISE CUSTOMER EXPERIENCES (CX)          │
                                  │      (Web Portal • Mobile App • Executive Dashboards)   │
                                  └────────────────────────────┬────────────────────────────┘
                                                               │
                                  ┌────────────────────────────▼────────────────────────────┐
                                  │       UNIFIED IDENTITY & API GATEWAY (OIDC / OAuth2)    │
                                  │    • SSO Federation  • Decree 13 Privacy Guard • RBAC   │
                                  └────────────────────────────┬────────────────────────────┘
                                                               │
                     ┌─────────────────────────────────────────┼─────────────────────────────────────────┐
                     │                                         │                                         │
                     ▼                                         ▼                                         ▼
      ┌──────────────────────────────┐          ┌──────────────────────────────┐          ┌──────────────────────────────┐
      │         INSILOS ERP          │          │     VERTICAL RESILIENCE      │          │           MOJO AI            │
      │  (The Commercial & Financial │          │   (The GRC, Security & Trust │          │    (The Cognitive Engine &   │
      │       Operating Engine)      │          │       Operating Engine)      │          │      Autonomous Agents)      │
      ├──────────────────────────────┤          ├──────────────────────────────┤          ├──────────────────────────────┤
      │ • Lead-to-Cash (AL2C)        │◄────────►│ • Risk Registers & Matrices  │◄────────►│ • Email Timesheet Ingestion  │
      │ • SAP Activate Stages        │          │ • ISO 27001 / Decree 13/2023 │          │ • Smart Tabular Parser & OCR │
      │ • Timesheet Analytic Ledger  │          │ • Audit Packs & Evidence     │          │ • Multi-Agent Workflow Co-op │
      │ • Decree 70/2025 VAT Invoice │          │ • Commercial Dispute Guard   │          │ • High-Speed Token Inference │
      └──────────────┬───────────────┘          └──────────────┬───────────────┘          └──────────────┬───────────────┘
                     │                                         │                                         │
                     └─────────────────────────────────────────┼─────────────────────────────────────────┘
                                                               │
                                  ┌────────────────────────────▼────────────────────────────┐
                                  │                       ZENCODE ENT                       │
                                  │         (The Developer Velocity & Swarm Engine)         │
                                  ├─────────────────────────────────────────────────────────┤
                                  │ • Multi-Node AGY Fleet Manager (8-Node Cluster)         │
                                  │ • Automated CI/CD Regression & Council Security Gates   │
                                  │ • Repository Scanning & Architecture Drift Telemetry    │
                                  │ • Low-Code Accelerators & Code Synthesis Pipelines      │
                                  └─────────────────────────────────────────────────────────┘
```

---

## 2. Ma Trận Hợp Đồng Tương Tác Dữ Liệu (Inter-Product Data Contracts)

### 2.1. Insilos ERP $\longleftrightarrow$ Mojo AI (Cognitive Automation Contract)
- **Kênh giao tiếp:** Event-Driven Webhooks & RabbitMQ Asynchronous Messages.
- **Quy trình Thu nhận Bảng kê Giờ công:**
  1. Hộp thư `info@inno.ai.vn` nhận email báo cáo công tác hoặc file đính kèm (Excel/CSV/PDF) từ tư vấn viên dự án.
  2. Ingestion Gateway kích hoạt Mojo AI Smart Parser:
     - Bóc tách cấu trúc: `Consultant Email`, `Client/Partner`, `Project Code`, `Task Name`, `Work Date`, `Hours`, `Description`, `Currency`.
     - Tính toán `content_fingerprint` (SHA-256) và `external_nonce` nhằm đảm bảo khả năng chống trùng lặp tuyệt đối.
  3. Mojo AI đẩy payload đã chuẩn hóa vào bộ đệm `al2c.timesheet.staging` của Insilos ERP.
  4. Quản lý Dự án (PM) thẩm định và thực hiện 1-click commit vào sổ cái `account.analytic.line`.

### 2.2. Insilos ERP $\longleftrightarrow$ Vertical Resilience (GRC & Risk Ledger Contract)
- **Kênh giao tiếp:** RESTful Service APIs / gRPC với xác thực mTLS và API Tokens phân tầng.
- **Quy trình Kiểm soát Rủi ro & Tuân thủ Dự án:**
  1. Khi một Hợp đồng hoặc Đơn hàng (Sale Order) được xác nhận với giá trị TCV $> 500,000,000$ VND hoặc tỷ lệ chiết khấu $> 10\%$:
     - Insilos ERP tự động gửi tín hiệu kiểm soát đến Vertical Resilience để lập bản ghi **Đánh giá Rủi ro Thương mại (Commercial Risk Assessment)**.
  2. Trong quá trình giao hàng theo phương pháp SAP Activate:
     - Các mốc nghiệm thu (Stage Gates: Explore, Realize, Deploy) chỉ được phép chuyển trạng thái Billable khi Vertical Resilience xác nhận tình trạng hồ sơ chứng từ tuân thủ (Compliance Evidence Pack).
  3. Xử lý Tranh chấp Công nợ (AL2C-INV-103):
     - Mọi bản ghi `al2c.dispute` mở đều lập tức đồng bộ sang Risk Register của Vertical Resilience để theo dõi rủi ro nợ xấu và dự phòng tài chính.

### 2.3. Zencode Ent $\longleftrightarrow$ Toàn Bộ 3 Khối Ứng Dụng (Developer Platform & Swarm Router Contract)
- **Kênh giao tiếp:** Antigravity Fleet MCP (`http://localhost:7777`), Git Automated Workflows, Pinned Monitor Daemons.
- **Chức năng:**
  1. Phân bổ năng lực tính toán AI (Claude Opus 5.5 / Gemini 3.8 Flash) theo thời gian thực tới các kỹ sư phát triển sản phẩm.
  2. Thực thi kiểm định đa tầng tự động (Pre-commit hooks, Negative-selection unslop tests, AST iteration safety, Database isolation assertions).
  3. Quét kiểm tra độ lệch tài liệu (Documentation Drift Scanner) trên cả 4 repository: cảnh báo tự động khi mã nguồn thay đổi nhưng tài liệu kiến trúc quá hạn 30 ngày chưa cập nhật.

---

## 3. Các Gói Giải Pháp Thương Mại Đóng Gói Sẵn (Pre-Packaged Commercial Bundles)

Nhằm tối ưu hóa chu kỳ bán hàng (Lead-to-Cash Velocity) và gia tăng giá trị trọn đời của khách hàng (LTV), doanh nghiệp cung cấp 3 gói giải pháp tích hợp sẵn:

### Gói 1: Enterprise Digital Core (Insilos ERP + Mojo AI)
- **Đối tượng:** Doanh nghiệp sản xuất, bán buôn, dịch vụ chuyên nghiệp cần số hóa toàn diện từ Bán hàng, Mua hàng, Kho vận đến Kế toán tài chính tuân thủ Nghị định 70/2025/NĐ-CP.
- **Giá trị cốt lõi:** Tự động hóa 80% công việc nhập liệu thông qua trợ lý ảo Mojo AI; thanh toán quét mã VietQR/Napas247 tức thời; phát hành hóa đơn điện tử tự động sau khi đối soát giờ công.

### Gói 2: Fintech & Banking Resilience Suite (Vertical Resilience + Insilos ERP Core)
- **Đối tượng:** Ngân hàng số, Công ty Chứng khoán, Quỹ Đầu tư, Tổ chức Trung gian Thanh toán phải đáp ứng quy định khắt khe của Ngân hàng Nhà nước và Nghị định 13/2023/NĐ-CP về bảo vệ dữ liệu cá nhân.
- **Giá trị cốt lõi:** Báo cáo tuân thủ tự động theo khung ISO/IEC 27001, PCI-DSS; sổ theo dõi rủi ro vận hành (RCM) thời gian thực kết hợp kế toán quản trị minh bạch.

### Gói 3: Autonomous Software Engineering Transformation (Zencode Ent + Mojo AI)
- **Đối tượng:** Các tập đoàn công nghệ, ngân hàng có trung tâm phát triển phần mềm nội bộ (In-house Software Center) muốn nâng cao năng suất kỹ thuật gấp 3-5 lần.
- **Giá trị cốt lõi:** Hệ thống định tuyến Swarm đa tài khoản; bộ kiểm tra an ninh tự động loại bỏ lỗ hổng mã nguồn từ vòng phát triển; bộ công cụ tạo mã thông minh theo ngữ cảnh dự án.

---

## 4. Các Giới Hạn Kiến Trúc Bất Biến (Non-Negotiable Architectural Invariants)

1. **Cô Lập Cơ Sở Dữ Liệu & Môi Trường Thử Nghiệm (Strict DB Isolation):**
   - Mọi hoạt động phát triển, kiểm thử unit test, di trú schema phải tuyệt đối thực hiện trên cơ sở dữ liệu `insilos20_dev` (cổng `5434`).
   - Nghiêm cấm mọi kết nối ghi, xóa, hoặc thay đổi DDL trực tiếp vào các cơ sở dữ liệu sản xuất (`innoria_prod`, `innokafe_prod`).
2. **Nguyên Tắc Zero-Fake-Pass:**
   - Mọi kết quả kiểm thử, chứng thực an ninh, nghiệm thu tính năng phải có bằng chứng thực thi thực tế (Command output, Exit code 0, log kiểm thử) trong phiên làm việc.
3. **Thương Hiệu Thuần Khiết (Zero-AI-Tells & Zero-Framework-Leaks):**
   - Mọi giao diện, email mẫu, hóa đơn gửi tới khách hàng phải mang chuẩn nhận diện thương hiệu Insilos / Innoria Enterprise; loại bỏ hoàn toàn các từ ngữ mặc định của nền tảng mã nguồn mở hoặc dấu vết máy học sinh ra tự động.
4. **Bảo Mật Tiền Tệ & Tỷ Giá Bất Biến (Multi-Currency Invariant):**
   - Tất cả các dòng tiền tệ chéo (VND, USD, EUR) trên bảng kê và hóa đơn phải sử dụng độ chính xác số học 8 chữ số thập phân (`digits=(16, 8)`), có snapshot tỷ giá tại thời điểm chốt và xử lý đóng kín (fail-closed) khi tỷ giá chưa được định nghĩa.

---
*Phê duyệt bởi Hội đồng Kiến trúc Doanh nghiệp UNG DUNG SANG TAO LLC / INNORIA ENTERPRISE.*
