# Standard Operating Procedure (SOP): Consulting Resources & Timesheet Pipeline
## Quy Trình Quản Trị Nguồn Lực Tư Vấn, Thu Nhận Báo Cáo Thời Gian Hướng Sự Kiện & Tính Tiền Dịch Vụ Khách Hàng (Billable Timesheet-to-Invoice Engine)

> **SOP Code:** SOP-OPS-002 • **Version:** 3.0 (Master Council Compliant)  
> **Key Architecture:** Event-Driven Timesheet Email Ingestion Pipeline (`info@inno.ai.vn`)  
> **Applicable Regulations:** Nghị định 70/2025/NĐ-CP (Hóa đơn điện tử) • Nghị định 13/2023/NĐ-CP (Bảo vệ dữ liệu cá nhân) • Luật Kế toán 88/2015/QH13  
> **Core Models:** `al2c.timesheet.staging` • `al2c.timesheet.staging.line` • `account.analytic.line` • `sale.order.line` • `account.move` • `al2c.dispute`  

---

## 1. Bản Chất Nghiệp Vụ: Động Cơ Doanh Thu Dịch Vụ Tư Vấn (Billable Consulting Services Engine)

Trong mô hình công ty phần mềm và dịch vụ công nghệ doanh nghiệp (Software Services Company) triển khai hệ sinh thái **Insilos ERP**, **Vertical Resilience**, **Mojo AI** và **Zencode Enterprise**, đường ống timesheet không đơn thuần là công cụ chấm công nội bộ hay tính chi phí nhân sự (Cost COGS).

**Đây là Động Cơ Sinh Ra Doanh Thu Cốt Lõi (Primary Revenue Engine):**
1. **Dịch vụ Theo Giờ & Vật Liệu (Time & Materials - T&M):** Mọi giờ công chuyên gia (Consulting Hours) tham gia dự án khách hàng trực tiếp chuyển hóa thành doanh thu có thể tính tiền (`qty_delivered` billable).
2. **Hợp Đồng Trọn Gói Theo Mốc (Fixed-Price Milestone Delivery):** Giờ công là căn cứ xác thực tiến độ thực hiện (Effort Progress), đo lường biên lợi nhuận gộp theo thời gian thực (Real-time Margin Tracking), và là bằng chứng phụ lục bàn giao không thể thiếu khi xuất hóa đơn nghiệm thu theo từng mốc SAP Activate.
3. **Dịch vụ Vận Hành & Bảo Trì Ứng Dụng (AMS - Application Management Services):** Giờ công chuyên gia được khấu trừ theo hạn mức SLA tháng, tự động phát sinh hóa đơn phụ trội (Overage Billing) khi vượt định mức cam kết.

---

## 2. Kiến Trúc Thu Nhận Timesheet Tự Động Hướng Sự Kiện (Event-Driven Ingestion Pipeline)

Để giải phóng các chuyên gia tư vấn (Consultants) khỏi việc nhập liệu timesheet thủ công tốn thời gian, Innoria thiết lập đường ống xử lý tự động tiếp nhận email gửi về hộp thư trung tâm `info@inno.ai.vn`:

```
               ┌────────────────────────────────────────────────────────┐
               │    Chuyên gia tư vấn gửi Email (Excel / CSV / Body)    │
               │                   info@inno.ai.vn                      │
               └───────────────────────────┬────────────────────────────┘
                                           │
                                           ▼ (1. Webhook / Pub-Sub Event)
               ┌────────────────────────────────────────────────────────┐
               │           GOOGLE WORKSPACE / MAIL PUBSUB DAEMON        │
               │              (tools/mail_pubsub_daemon.py)             │
               └───────────────────────────┬────────────────────────────┘
                                           │
                                           ▼ (2. Raw Payload Ingestion)
               ┌────────────────────────────────────────────────────────┐
               │         VÙNG ĐỆM TRUNG GIAN (STAGING BUFFER)           │
               │               al2c.timesheet.staging                   │
               │  • Trạng thái: received ➔ parsed ➔ approved / rejected │
               │  • Lưu trữ raw_payload, tệp đính kèm và siêu dữ liệu   │
               └───────────────────────────┬────────────────────────────┘
                                           │
                                           ▼ (3. Mojo AI Intelligent Parser)
               ┌────────────────────────────────────────────────────────┐
               │              MOJO AI PARSER & DEDUP ENGINE             │
               │  • Bóc tách bảng biểu Excel (.xlsx), CSV, hoặc Markdown│
               │  • Khớp định danh chuyên gia 3 tầng: email ➔ employee  │
               │  • Khớp dự án & công việc: tên/mã ➔ project.task       │
               │  • Chống trùng lặp (Dedup): (Chuyên gia, Ngày, Task)   │
               └───────────────────────────┬────────────────────────────┘
                                           │
                                           ▼ (4. 1-Click PM Review)
               ┌────────────────────────────────────────────────────────┐
               │          TRƯỞNG DỰ ÁN DUYỆT 1-CLICK TRÊN ERP           │
               │       Nút bấm "Xác Nhận & Ghi Sổ" (Action Approve)     │
               └───────────────────────────┬────────────────────────────┘
                                           │
                                           ▼ (5. Final Commit & Downstream Billing)
               ┌────────────────────────────────────────────────────────┐
               │          SỔ CÁI PHÂN TÍCH (IMMUTABLE ANALYTIC LINE)    │
               │                 account.analytic.line                  │
               │  • Cập nhật giờ bàn giao: qty_delivered trên SO Line   │
               │  • Phát hành Bảng kê giờ công & Hóa đơn tạm tính       │
               │  • Gửi mail đối soát khách hàng ➔ Nhận xác nhận 1-Click│
               │  • Phát hành Hóa đơn VAT điện tử Nghị định 70/2025     │
               └────────────────────────────────────────────────────────┘
```

---

## 3. Cơ Chế Bóc Tách Thông Minh & Hàng Rào Chống Trùng Lặp (Mojo AI & Dedup Guard)

Mojo AI Parser thực hiện tuần tự các bước kiểm định dữ liệu tự động với độ chịu lỗi cao (Fault-Tolerant Engine):

### 3.1. Đối Khớp Định Danh Chuyên Gia 3 Tầng (3-Tier Consultant Resolution)
Hệ thống không phụ thuộc vào một thuộc tính đơn lẻ mà phân giải danh tính theo cơ chế phân tầng nghiêm ngặt:
1. **Tier 1 (Trực tiếp từ Nhân sự):** Khớp địa chỉ email người gửi với trường `work_email` hoặc `private_email` trên bảng nhân sự `hr.employee`.
2. **Tier 2 (Qua Tài khoản Người dùng):** Khớp email với `login` hoặc `email` trên bảng người dùng `res.users`, từ đó truy vết ra nhân viên liên kết `hr.employee`.
3. **Tier 3 (Qua Danh bạ Liên hệ Công tác):** Khớp email với `work_contact_id.email` trên `hr.employee`.
4. **Nguyên Tắc An Toàn (Ambiguity Rejection):** Nếu một địa chỉ email hoặc tên nhân sự khớp với từ 2 bản ghi trở lên trong cùng một tầng, hệ thống **từ chối tự động gán** (`refusing silent attribution`) và gắn nhãn cảnh báo để người phụ trách xác nhận thủ công, ngăn ngừa rủi ro tính sai chi phí và doanh thu.

### 3.2. Bóc Tách Đa Định Dạng (Multi-Format Attachment Parsing)
- **Tệp Excel Hiện Đại (`.xlsx`, `.xlsm`):** Bóc tách qua thư viện `openpyxl` với cơ chế kiểm tra dung lượng chống tấn công từ chối dịch vụ (giới hạn an toàn tối đa 100.000 dòng $\times$ 512 cột).
- **Tệp Excel Di Sản (`.xls`):** Bóc tách qua thư viện `xlrd` với bộ giải mã kiểu dữ liệu ngày tháng tự động (`xldate_as_datetime`).
- **Tệp Văn Bản Phân Tách (`.csv`):** Tự động phát hiện ký tự phân cách (dấu phẩy `,` hoặc dấu chấm phẩy `;`) và bảng mã ký tự (UTF-8, UTF-8 with BOM, CP1258 cho tiếng Việt).
- **Bảng Biểu Trong Thân Thư (Markdown / HTML Table):** Phân tích cú pháp biểu thức chính quy (Regex Table Extractor) để bóc tách cột Ngày, Dự án, Công việc, Số giờ, Diễn giải.

### 3.3. Hàng Rào Chống Trùng Lặp Kép (Dual-Layer Deduplication Guard)
Để loại bỏ hoàn toàn rủi ro một chuyên gia gửi lại báo cáo tuần nhiều lần dẫn tới tính tiền trùng lặp cho khách hàng:
1. **Lớp 1: Mã Băm Dấu Vân Tay Toàn Cục (Global SHA-256 Fingerprint):**
   $$\text{Fingerprint} = \text{SHA256}(\text{sender\_email} \parallel \text{subject} \parallel \text{body\_content})$$
   Khóa duy nhất cấp cơ sở dữ liệu (`UNIQUE INDEX ... WHERE state = 'approved'`) đảm bảo tuyệt đối không một payload nào bị ghi sổ hai lần ngay cả trong tình huống có nhiều tiến trình chạy song song (Race-Condition Proof).
2. **Lớp 2: Kiểm Tra Bộ Khóa Duy Nhất Từng Dòng (Row-Level Dedup Key):**
   $$\text{Dedup Key} = (\text{employee\_id}, \text{task\_id}, \text{date})$$
   Mỗi dòng timesheet trước khi ghi nhận vào `account.analytic.line` đều được quét đối chiếu với các bản ghi đã tồn tại trong hệ thống. Nếu phát hiện trùng lặp, dòng đó lập tức bị chuyển trạng thái `duplicate` kèm thông báo mã dòng phân tích đối soát và không được tính tiền lại.

---

## 4. Chu Trình 6 Bước: Từ Timesheet Đến Hóa Đơn VAT Điện Tử (The 6-Stage Billable Lifecycle)

Đây là quy trình khép kín chi tiết từ khi chuyên gia tư vấn gửi báo cáo công việc đến khi nhận được xác nhận của khách hàng và xuất hóa đơn điện tử hợp pháp:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                   CHU TRÌNH 6 BƯỚC TÍNH TIỀN DỊCH VỤ TƯ VẤN & XUẤT HÓA ĐƠN             │
├──────────────┬──────────────┬──────────────┬──────────────┬─────────────┬──────────────┤
│ Bước 1:      │ Bước 2:      │ Bước 3:      │ Bước 4:      │ Bước 5:     │ Bước 6:      │
│ Thu Nhận     │ Bóc Tách &   │ PM Duyệt     │ Lập Bảng Kê  │ Gửi Email   │ Khách Hàng   │
│ Email        │ Chống Trùng  │ 1-Click      │ Giờ Công &   │ Đối Soát &  │ Xác Nhận ➔   │
│ info@inno    │ Lặp Thông    │ Ghi Sổ Phân  │ Hóa Đơn Tạm  │ Link Portal │ Xuất HĐ VAT  │
│ .ai.vn       │ Minh (Mojo)  │ Tích         │ Tính         │ Xác Nhận    │ NĐ 70/2025   │
└──────────────┴──────────────┴──────────────┴──────────────┴─────────────┴──────────────┘
```

### Bước 1: Thu Nhận Email Tự Động Hướng Sự Kiện (Automated Inbound Ingestion)
1. Chuyên gia tư vấn định kỳ (thứ 6 hàng tuần hoặc ngày cuối tháng) gửi email báo cáo công việc tới `info@inno.ai.vn`.
2. Tiến trình lắng nghe Pub/Sub (`tools/mail_pubsub_daemon.py`) hoặc cổng email gateway Odoo tự động nhận diện thư gửi đến, khởi tạo bản ghi vùng đệm `al2c.timesheet.staging` ở trạng thái `received`.
3. Toàn bộ tệp đính kèm và nội dung gốc được lưu trữ nguyên trạng trong kho tài liệu chứng từ `documents.document` phục vụ lưu trữ kiểm toán ISO/IEC 27001.

### Bước 2: Bóc Tách & Chống Trùng Lặp Thông Minh (AI Parsing & Validation)
1. Mojo AI kích hoạt phương thức `action_parse_content()`.
2. Hệ thống bóc tách các dòng công việc, thực hiện đối khớp 3 tầng chuyên gia, nhận diện mã dự án và nhiệm vụ (`project.task`).
3. Thực hiện kiểm tra tính hợp lệ:
   - Số giờ làm việc hàng ngày phải $> 0$ và $\le 24$ giờ/ngày.
   - Ngày làm việc phải hợp lệ, không nằm trong tương lai quá 7 ngày.
   - Dự án và nhiệm vụ phải đang ở trạng thái hoạt động (`active = True`).
   - Kiểm tra trùng lặp trên sổ cái phân tích `account.analytic.line`.
4. Bản ghi chuyển sang trạng thái `parsed` sẵn sàng cho Trưởng Dự Án (PM) phê duyệt.

### Bước 3: Phê Duyệt 1-Click Của Trưởng Dự Án (1-Click PM Review & SoD Commit)
1. Trưởng Dự Án truy cập màn hình **Hàng Đợi Timesheet Email** (`al2c.timesheet.staging`).
2. Giao diện thể hiện trực quan trạng thái từng dòng:
   - 🟢 **Valid (Hợp lệ):** Đầy đủ thông tin, không trùng lặp, nằm trong ngân sách.
   - 🟡 **Warning / Duplicate (Cảnh báo/Trùng lặp):** Đã tồn tại dòng giờ công cùng ngày, hệ thống tự động đánh dấu bỏ qua.
   - 🔴 **Error (Lỗi):** Không khớp được dự án/nhiệm vụ hoặc số giờ không hợp lệ.
3. PM bấm nút **"Xác Nhận & Ghi Nhận Timesheet" (`action_approve_and_commit`)**:
   - **Hàng Rào Phân Quyền Bắt Buộc (SoD Guard):** Chỉ người dùng thuộc nhóm Quản Lý Dự Án (`project.group_project_manager`) hoặc Giám Đốc Bán Hàng (`sales_team.group_sale_manager`) mới có quyền phê duyệt. Chuyên gia tư vấn thông thường tuyệt đối không thể tự duyệt giờ công của chính mình.
   - Hệ thống ghi các dòng hợp lệ vào sổ cái phân tích bất biến `account.analytic.line`.

### Bước 4: Cập Nhật Giờ Bàn Giao & Lập Bảng Kê Hóa Đơn Tạm Tính (Timesheet Statement Generation)
1. Ngay khi các dòng `account.analytic.line` được tạo, trường `qty_delivered` trên các dòng đơn hàng dịch vụ liên kết (`sale.order.line` với SKU ví dụ `CONSULT-HOUR`, `AI-PILOT-HR`, `ERP-ACTIVATE-TM`) tự động tăng tương ứng với số giờ công thực tế đã thực hiện.
2. Hệ thống tự động khởi tạo **Bảng Kê Chi Tiết Giờ Công & Hóa Đơn Tạm Tính (Timesheet Statement & Pro-forma Invoice)**:
   - Tổng hợp danh sách chuyên gia tư vấn tham gia trong kỳ (Họ tên, Cấp bậc chuyên môn, Ngày làm việc, Tên công việc, Mô tả bàn giao, Số giờ).
   - Áp dụng Bảng đơn giá chuẩn (Rate Card) theo hợp đồng đã ký kết giữa hai bên.
   - Tính toán tổng tiền trước thuế, thuế suất GTGT (thông thường 8% hoặc 10% theo luật thuế hiện hành), và tổng tiền thanh toán tạm tính.
   - Trạng thái đối soát bảng kê được thiết lập: `al2c_timesheet_statement_state = 'draft_statement'`.

### Bước 5: Gửi Email Đối Soát & Yêu Cầu Khách Hàng Xác Nhận (Email Statement with 1-Click Confirmation Link)
1. Hệ thống tự động kích hoạt hành động gửi email `action_send_timesheet_statement()` sử dụng mẫu thư chuẩn doanh nghiệp **IBM Carbon & SAP Horizon**: `email_template_al2c_timesheet_statement_confirm`.
2. Nội dung email gửi tới Người đại diện dự án / Kế toán trưởng của Khách hàng bao gồm:
   - Thư mời đối soát trân trọng, ghi rõ mã kỳ thanh toán, tên dự án, tổng số giờ công và tổng số tiền dịch vụ tạm tính.
   - Tệp Bảng Kê Chi Tiết Giờ Công (PDF & Excel) có chữ ký số của PM Innoria.
   - Nút hành động trực tuyến: **"Xác Nhận Giờ Công & Đồng Ý Xuất Hóa Đơn (Confirm Timesheet & Approve Invoice)"** dẫn trực tiếp đến Cổng Khách Hàng (Customer Portal) bảo mật qua mã xác thực một lần (Secure Confirmation Token).
   - Nút hành động đối soát: **"Khiếu nại / Đối soát AL2C-INV-103"** cho phép khách hàng nêu các điểm chưa rõ ràng về khối lượng công việc để hai bên giải trình minh bạch.
3. Trạng thái bảng kê chuyển sang `al2c_timesheet_statement_state = 'sent_to_client'`.

### Bước 6: Khách Hàng Xác Nhận & Phát Hành Hóa Đơn VAT Điện Tử Nghị Định 70/2025/NĐ-CP
1. **Khách Hàng Xác Nhận Trực Tuyến:**
   - Đại diện khách hàng truy cập đường link Portal, xem bảng kê giờ công và bấm nút xác nhận.
   - Hệ thống lập tức cập nhật trạng thái `al2c_timesheet_statement_state = 'confirmed'`, ghi nhận thời gian xác nhận (`al2c_timesheet_confirmed_date`), định danh đối tác xác nhận (`al2c_timesheet_confirmed_by`), và địa chỉ IP vào nhật ký kiểm toán.
2. **Phát Hành Hóa Đơn VAT Điện Tử Hợp Pháp (Decree 70/2025 Compliance):**
   - Kế toán hoặc hệ thống tự động thực hiện ghi sổ hóa đơn (`action_post`).
   - Gọi bộ điều hợp hóa đơn điện tử `action_issue_einvoice()`:
     - Ký số hóa đơn bằng chứng thư số HSM của doanh nghiệp.
     - Truyền dữ liệu tới Cơ quan Thuế (CQT) để cấp Mã tra cứu và Ký hiệu mẫu số (ví dụ: `1C26TAA-00000001`).
     - Tạo mã thanh toán động **Napas247 / VietQR** chính xác số tiền và số hóa đơn.
   - Tự động gửi email Hóa Đơn Điện Tử chính thức kèm tệp PDF bản thể hiện và tệp XML gốc có chữ ký số hợp lệ tới phòng Tài chính Kế toán của khách hàng.
3. **Đối Soát Dòng Tiền & Tính Thưởng Doanh Số (Cash Reconciliation & Sales Commission):**
   - Khi khách hàng quét mã VietQR Napas247 thanh toán vào tài khoản Vietcombank của Innoria, hệ thống đối soát tự động khớp tiền và kích hoạt tính hoa hồng bán hàng cash-matched theo `AL2C-PAY-001`.

---

## 5. Bảng Đơn Giá Giờ Công Chuẩn Cho Nhân Sự Dự Án (Consulting Rate Card Framework)

Để đảm bảo tính nhất quán và bảo vệ biên lợi nhuận dịch vụ, Innoria ban hành Bảng đơn giá giờ công chuẩn áp dụng cho các dòng dịch vụ tư vấn billable:

| Mã Cấp Bậc (Role Code) | Chức Danh Chuyên Gia Tư Vấn (Consulting Role) | Trách Nhiệm Chính Trên Dự Án | Đơn Giá Chuẩn (VND/Giờ) | Đơn Giá Ngoài Giờ / Khẩn Cấp (+50%) |
| :--- | :--- | :--- | :--- | :--- |
| **ROLE-ARCH-01** | Principal Enterprise Architect | Kiến trúc tổng thể hệ thống, bảo mật ISO 27001, tích hợp đa nền tảng | **3.000.000 - 3.500.000** | **4.500.000 - 5.250.000** |
| **ROLE-TECH-02** | Senior Technical Lead / DevSecOps | Phát triển lõi Odoo 20 OWL, xây dựng Pipeline CI/CD, tối ưu hiệu năng | **2.000.000 - 2.500.000** | **3.000.000 - 3.750.000** |
| **ROLE-FUNC-03** | Senior Functional Consultant (SAP/ERP) | Khảo sát Fit-to-Standard, thiết kế quy trình Kế toán/Kho/Sản xuất | **1.800.000 - 2.200.000** | **2.700.000 - 3.300.000** |
| **ROLE-AI-04** | Mojo AI & LLM Systems Engineer | Tích hợp Agentic LLM, tối ưu hóa RAG, huấn luyện mô hình bóc tách | **2.200.000 - 2.800.000** | **3.300.000 - 4.200.000** |
| **ROLE-SPEC-05** | Implementation Specialist / Developer | Lập trình tính năng, cấu hình báo cáo, chuyển đổi dữ liệu kế thừa | **1.200.000 - 1.500.000** | **1.800.000 - 2.250.000** |
| **ROLE-QA-06** | Quality Assurance / UAT Coordinator | Kiểm thử chức năng, điều phối kiểm thử chấp nhận người dùng UAT | **800.000 - 1.000.000** | **1.200.000 - 1.500.000** |

> **Nguyên Tắc Hợp Đồng (Contract Guardrail):** Mọi điều khoản báo giá thấp hơn mức sàn tối thiểu của cấp bậc chuyên gia phải được phê duyệt trước bởi Giám Đốc Dịch Vụ (VP of Services) và Giám Đốc Tài Chính (CFO).

---

## 6. Hệ Thống Cảnh Báo Tiêu Hao Ngân Sách Giờ (Burn-Rate Alerting Protocol)

Để ngăn ngừa tình trạng chi phí nhân lực vượt quá ngân sách đã ký kết với khách hàng:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        TASK BUDGET CONSUMPTION PROGRESSION                             │
├────────────────────────────┬─────────────────────────────┬─────────────────────────────┤
│ 🟢 VÙNG AN TOÀN (0 - 84%)  │ 🟡 VÙNG CẢNH BÁO (85 - 99%) │ 🔴 VÙNG NGUY HIỂM (≥ 100%)  │
│ Tiến độ tiêu hao bình thường│ Tự động kích hoạt Cảnh Báo  │ Khóa ghi nhận tự động       │
│                            │ Cần đánh giá nguy cơ chậm trễ│ Bắt buộc phải có CR         │
└────────────────────────────┴─────────────────────────────┴─────────────────────────────┘
```

1. **Ngưỡng Cảnh Báo Sớm 85% (`Burn Warning Gate`):**
   - Khi tổng số giờ ghi nhận trên một nhiệm vụ vượt quá **85%** số giờ kế hoạch (`allocated_hours`), hệ thống tự động:
     - Gửi email cảnh báo khẩn cấp đến Trưởng Ban Dự Án và Giám đốc Dịch vụ.
     - Hiển thị huy hiệu cảnh báo màu vàng trên Kanban điều phối của dự án.
     - Yêu cầu chuyên gia tư vấn giải trình tỷ lệ hoàn thành công việc thực tế (Actual Work Progress %).
2. **Ngưỡng Vượt Định Mức 100% (`Budget Overrun Gate`):**
   - Khi số giờ chạm ngưỡng 100%, hệ thống chuyển sang chế độ **CẦN PHÊ DUYỆT ĐẶC BIỆT**.
   - Mọi giờ công phát sinh tiếp theo không được tự động tính vào doanh thu thanh toán (Unbillable Hours) trừ khi khách hàng đã ký kết **Phiếu Yêu Cầu Thay Đổi Phạm Vi (Change Request - CR)** theo đúng quy trình `SOP-PRJ-001`.

---

## 7. Cơ Chế Đóng Băng Khiếu Nại & Đối Soát Thương Mại (`AL2C-INV-103`)

Trường hợp khách hàng có bất kỳ điểm chưa hài lòng hoặc cần làm rõ về bảng kê giờ công của các chuyên gia:
1. Khách hàng bấm nút **"Khiếu nại / Đối soát AL2C-INV-103"** trực tiếp trên Cổng Khách hàng trực tuyến hoặc phản hồi email.
2. Ngay khi tiếp nhận yêu cầu đối soát:
   - Hệ thống **LẬP TỨC ĐÓNG BĂNG (FREEZE)** tiến trình đôn đốc thu nợ tự động (Dunning Ladder) đối với hóa đơn này.
   - Tự động tạo hồ sơ khiếu nại thương mại `al2c.dispute` liên kết với hóa đơn và phân công xử lý cho PM dự án.
   - PM dự án phối hợp cùng chuyên gia tư vấn rà soát lại nhật ký công việc (Work Logs) và phát hành biên bản đối soát giải trình trong vòng 24 - 48 giờ làm việc.
3. Sau khi hai bên thống nhất:
   - Nếu khách hàng đồng ý: Khách hàng xác nhận và hóa đơn tiếp tục quy trình thanh toán.
   - Nếu có điều chỉnh số giờ: PM thực hiện điều chỉnh giảm số giờ không hợp lệ trên hệ thống, phát hành lại bảng kê điều chỉnh để khách hàng xác nhận.

---

## 8. Ma Trận Phân Quyền Nhiệm Vụ (RACI Matrix)

| Giai Đoạn / Bước Thực Hiện | Chuyên Gia Tư Vấn (Consultant) | Trưởng Dự Án (PM) | Kế Toán Doanh Nghiệp (Accountant) | Giám Đốc Dịch Vụ (COO/VP) | Đại Diện Khách Hàng (Client Rep) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| 1. Gửi email timesheet về `info@inno.ai.vn` | **R** | I | I | I | I |
| 2. Bóc tách thông minh & Chống trùng lặp (Mojo AI) | I | **A** | I | I | I |
| 3. Duyệt 1-Click & Ghi sổ Phân tích (`account.analytic.line`) | I | **R / A** | C | I | I |
| 4. Lập Bảng kê Giờ công & Hóa đơn Tạm tính | I | **R** | **A** | C | I |
| 5. Gửi Mail Bảng kê Đối soát Kèm Link Portal | I | I | **R** | I | **A** |
| 6. Kiểm tra & Bấm nút Xác nhận trên Portal | I | C | I | I | **R / A** |
| 7. Phát hành Hóa đơn VAT Điện tử Nghị định 70/2025 | I | I | **R / A** | I | I |
| 8. Đối soát thanh toán Napas247 & Khóa sổ | I | I | **R / A** | C | I |

*Chú thích: R = Responsible (Người thực hiện chính); A = Accountable (Người chịu trách nhiệm cuối cùng); C = Consulted (Người được tham vấn); I = Informed (Người được thông báo).*

---

## 9. Chỉ Số Đo Lường Hiệu Suất Vận Hành (Operational KPIs)

Hệ thống theo dõi các chỉ số vận hành sau để bảo đảm tính kỷ luật và tối ưu hóa dòng tiền doanh nghiệp:
1. **Tỷ Lệ Giờ Công Sinh Ra Doanh Thu (Billable Utilization Rate):**
   $$\text{Billable Utilization} = \frac{\sum \text{Giờ Công Được Khách Hàng Xác Nhận}}{\sum \text{Tổng Giờ Làm Việc Chuyên Gia}} \ge 78\%$$
2. **Thời Gian Xử Lý Timesheet Đến Hóa Đơn (Timesheet-to-Invoice Cycle Time):**
   Thời gian từ khi chuyên gia gửi email đến khi phát hành hóa đơn điện tử chính thức $\le 72$ giờ làm việc.
3. **Tỷ Lệ Chấp Thuận Bảng Kê Ngay Lần Đầu (First-Pass Statement Acceptance Rate):**
   Tỷ lệ bảng kê giờ công được khách hàng bấm xác nhận ngay mà không phát sinh khiếu nại đối soát $\ge 95\%$.
4. **Tỷ Lệ Tự Động Hóa Không Chạm (Zero-Touch Ingestion Rate):**
   Tỷ lệ email timesheet được Mojo AI bóc tách chính xác 100% không cần can thiệp sửa đổi thủ công $\ge 92\%$.
