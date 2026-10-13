# Đặc Tả Kiến Trúc & Quy Trình Chi Tiết: Đường Ống Thu Nhận Timesheet Tự Động & Hóa Đơn Điện Tử NĐ 70/2025
## Thu Nhận Email Hướng Sự Kiện Qua info@inno.ai.vn • Bóc Tách Đa Phương Thức • Chống Trùng Lặp SHA-256 • Đối Soát Cổng Khách Hàng 1-Click • Phát Hành Hóa Đơn VAT Hợp Pháp

> **Mã đặc tả:** SPEC-OPS-TIMESHEET-BILLING-2026-V4  
> **Áp dụng cho:** Toàn bộ nhân sự tư vấn dự án khách hàng, Khối Tài chính Kế toán & Hệ thống Cổng Khách Hàng (Customer Portal)  
> **Căn cứ pháp lý:** Nghị định 70/2025/NĐ-CP (Hóa đơn điện tử) • Nghị định 123/2020/NĐ-CP • Thông tư 78/2021/TT-BTC • Bộ luật Lao động 45/2019/QH14  
> **Cấu trúc dữ liệu:** `al2c.timesheet.staging` • `account.analytic.line` • `sale.order.line` • `account.move` • `al2c.dispute`

---

## 1. Tổng Quan Kiến Trúc Động Cơ Doanh Thu Dịch Vụ Tư Vấn (End-to-End Pipeline Topology)

Đường ống thu nhận timesheet tự động chuyển hóa công sức chuyên môn của các chuyên gia tư vấn thành dòng tiền thực tế cho doanh nghiệp thông qua một chu trình 6 bước khép kín và an toàn tuyệt đối:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│               KIẾN TRÚC TỔNG THỂ ĐƯỜNG ỐNG TÍNH TIỀN DỊCH VỤ TƯ VẤN (E2E TOPOLOGY)     │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                        │
│  [1. Inbound Email Event]                                                              │
│  Chuyên gia gửi email báo cáo công việc (kèm .xlsx / .csv / body) tới info@inno.ai.vn  │
│                                  │                                                     │
│                                  ▼ (Webhook có chữ ký số HMAC-SHA256 & DMARC Check)   │
│  [2. Event Daemon & Isolation Buffer]                                                  │
│  mail_pubsub_daemon.py tiếp nhận, kiểm định nguồn gửi, lưu vào al2c.timesheet.staging   │
│                                  │                                                     │
│                                  ▼ (Mojo AI Intelligent Parser & Dedup)                │
│  [3. Multi-Modal Parsing & Deduplication Engine]                                       │
│  Bóc tách bảng tính, khớp định danh 3 tầng, kiểm tra khóa vân tay SHA-256 duy nhất     │
│                                  │                                                     │
│                                  ▼ (PM Review & SoD Approval)                          │
│  [4. 1-Click Project Manager Approval]                                                 │
│  Trưởng dự án duyệt hợp lệ ➔ Ghi sổ phân tích bất biến account.analytic.line           │
│                                  │                                                     │
│                                  ▼ (Timesheet Statement & Billing Trigger)             │
│  [5. Timesheet Statement & Customer Portal Notification]                               │
│  Tự động cập nhật qty_delivered trên Đơn hàng dịch vụ (SO Line) ➔ Khởi tạo Bảng Kê     │
│  Gửi email kèm Bảng kê có chữ ký số & Đường link xác nhận thời hạn (Time-boxed Token)  │
│                                  │                                                     │
│                                  ▼ (1-Click Client Confirmation)                       │
│  [6. Customer 1-Click Confirmation & Decree 70/2025 E-Invoice Issuance]                │
│  Đại diện khách hàng xác nhận trực tuyến trên Portal ➔ Hệ thống tự động phát hành      │
│  Hóa đơn VAT điện tử Nghị định 70/2025/NĐ-CP, ký số HSM, truyền dữ liệu CQT và VietQR │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Giai Đoạn 1: Tiếp Nhận Email Hướng Sự Kiện & Cách Ly An Toàn (Ingestion & Quarantine Boundary)

### 2.1. Cổng Tiếp Nhận Hướng Sự Kiện (Event-Driven Webhook Gateway)
- **Hộp Thư Tiếp Nhận Trung Tâm:** `info@inno.ai.vn`.
- **Giao Thức Đồng Bộ:** Google Workspace Gmail Push Notification (Cloud Pub/Sub) hoặc Mailgun Webhook.
- **Tiến Trình Daemon Nền (`tools/mail_pubsub_daemon.py`):** Lắng nghe các thông báo sự kiện theo thời gian thực (Real-time Message Ingestion), giải mã gói tin email MIME đa phần (Multipart MIME Messages), và chuyển tiếp tới API controller `/innoria/timesheet/webhook`.

### 2.2. Hàng Rào Xác Thực Xuất Xứ Thư (Email Authentication Boundary - CWE-346 / CWE-20)
Để ngăn ngừa rủi ro bị tấn công chèn ép dữ liệu ảo hoặc mạo danh tư vấn viên (Email Spoofing):
1. **Kiểm Tra DMARC / SPF / DKIM Bắt Buộc:**
   - Hệ thống kiểm tra tiêu đề `Authentication-Results` của email.
   - Nếu `dmarc=fail` hoặc `spf=fail`, bản ghi được đánh dấu `dmarc_status = 'fail'` và tự động chuyển sang chế độ **CÁCH LY NGHIÊM NGẶT (`is_quarantined = True`)**.
2. **Khóa Vân Tay Khắc Chống Tấn Công Lặp Lại (Anti-Replay Nonce Invariant):**
   - Mỗi payload gửi đến được bảo vệ bởi một mã `external_nonce` kết hợp thời gian phát sinh:
     $$\text{Nonce Hash} = \text{SHA256}(\text{sender\_email} \parallel \text{message\_id} \parallel \text{timestamp})$$
   - Ràng buộc cấp cơ sở dữ liệu `al2c_timesheet_staging_external_nonce_uniq` lập tức từ chối mọi yêu cầu trùng lặp mã nonce.
3. **Giới Hạn Tải Trọng Phòng Vệ Từ Chối Dịch Vụ (Anti-DoS Capping):**
   - Giới hạn payload email tối đa: **256 KB** cho văn bản; tệp bảng tính đính kèm tối đa **10 MB** hoặc $100.000$ dòng $\times$ $512$ cột.

---

## 3. Giai Đoạn 2: Bóc Tách Thông Minh Đa Phương Thức & Chống Trùng Lặp (Mojo AI Parsing & Dedup)

### 3.1. Động Cơ Bóc Tách Tệp Bảng Tính Đính Kèm (Multi-Format Attachment Parsers)
Mojo AI hỗ trợ tự động nhận diện và bóc tách các định dạng tài liệu phổ biến nhất mà chuyên gia gửi về:
- **Tệp Microsoft Excel Mới (`.xlsx`):** Bóc tách qua thư viện `openpyxl` với cờ chỉ đọc (`read_only=True`) để tối ưu hóa bộ nhớ RAM.
- **Tệp Microsoft Excel Cũ (`.xls`):** Bóc tách qua thư viện `xlrd` với bộ giải mã múi giờ chuẩn hóa UTC.
- **Tệp Văn Bản Phân Tách (`.csv`):** Tự động nhận diện dấu phân cách (Dấu phẩy `,`, Dấu chấm phẩy `;`, hoặc Tab `\t`) và bảng mã ký tự (UTF-8, UTF-8 BOM, CP1258).
- **Nội Dung Thân Email (HTML / Markdown Table):** Tự động phát hiện cấu trúc bảng biểu trong thân thư bằng biểu thức chính quy (Regex Table Parser) khi tư vấn viên không đính kèm tệp rời.

### 3.2. Thuật Toán Khớp Định Danh 3 Tầng (3-Tier Entity Resolution)

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        CƠ CHẾ PHÂN GIẢI ĐỊNH DANH CHUYÊN GIA 3 TẦNG                    │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                        │
│   [TẦNG 1: Email Trực Tiếp]    Khớp work_email / private_email trên hr.employee        │
│                                            │ (Nếu không tìm thấy)                      │
│                                            ▼                                           │
│   [TẦNG 2: User Account]       Khớp login / email trên res.users ➔ hr.employee         │
│                                            │ (Nếu không tìm thấy)                      │
│                                            ▼                                           │
│   [TẦNG 3: Danh Bạ Đối Tác]    Khớp work_contact_id.email trên hr.employee             │
│                                            │                                           │
│                                            ▼                                           │
│   [NGUYÊN TẮC AN TOÀN]         Nếu tìm thấy > 1 bản ghi khớp trong cùng một tầng:      │
│                                ➔ TỪ CHỐI GÁN TỰ ĐỘNG, chuyển sang trạng thái CẢNH BÁO   │
│                                để con người xác nhận (Ambiguity Fail-Closed Guard).     │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### 3.3. Hàng Rào Chống Trùng Lặp SHA-256 (Row-Level Cryptographic Deduplication)

Mỗi dòng chi tiết công việc trong bảng kê trước khi được lưu vào cơ sở dữ liệu được tính toán một Khóa Nhận Dạng Duy Nhất (Dedup Fingerprint):
$$\text{Line Fingerprint} = \text{SHA256}(\text{employee\_id} \parallel \text{task\_id} \parallel \text{work\_date} \parallel \text{unit\_amount})$$

- Hệ thống truy vấn đối chiếu đồng thời trong hai nguồn:
  1. Các dòng đang chờ duyệt khác trong bảng `al2c.timesheet.staging.line`.
  2. Toàn bộ các dòng đã ghi sổ chính thức trong bảng `account.analytic.line`.
- Nếu phát hiện trùng lặp vân tay, dòng đó lập tức được gắn cờ `is_duplicate = True` và chuyển trạng thái sang `skipped`, hoàn toàn loại bỏ nguy cơ tính tiền hai lần cho cùng một giờ làm việc của nhân sự.

---

## 4. Giai Đoạn 3: Phê Duyệt 1-Click Của Quản Lý Dự Án & Ghi Sổ Phân Tích (PM Review & SoD Commit)

### 4.1. Giao Diện Bảng Điều Khiển Hàng Đợi (Staging Dashboard)
Trưởng Dự Án (Project Manager) theo dõi danh sách timesheet gửi về thông qua giao diện chuyên dụng (`al2c.timesheet.staging`):
- 🟢 **Xanh lá (Ready to Commit):** Định danh chuyên gia chuẩn xác, khớp đúng mã dự án/nhiệm vụ, không trùng lặp và nằm trong ngân sách giờ công dự án.
- 🟡 **Vàng (Duplicate / Skipped):** Giờ công đã tồn tại hoặc đã được ghi nhận ở lần gửi trước; hệ thống tự động loại trừ khỏi bút toán tài chính.
- 🔴 **Đỏ (Quarantined / Error):** Email không vượt qua kiểm định DMARC, địa chỉ lạ hoặc số giờ làm việc bất thường ($> 12$h/ngày).

### 4.2. Nguyên Tắc Phân Quyền Bắt Buộc (SoD Guardrail)
- **Quy Tắc Bất Biến:** Nhân viên tư vấn thông thường tuyệt đối không được tự phê duyệt dòng timesheet của chính mình.
- Hành động bấm nút **"Xác Nhận & Ghi Nhận Giờ Công" (`action_approve_and_commit`)** chỉ khả dụng cho người dùng thuộc nhóm **Quản Lý Dự Án (`project.group_project_manager`)** hoặc **Giám Đốc Bán Hàng (`sales_team.group_sale_manager`)**.
- Quá trình thăng hạng dữ liệu sang `account.analytic.line` được bao bọc trong một Database Savepoint nguyên tử (`with self.env.cr.savepoint()`), đảm bảo nguyên tắc tất cả hoặc không có gì (All-or-Nothing ACID Guarantee).

---

## 5. Giai Đoạn 4: Lập Bảng Kê Giờ Công & Gửi Email Đối Soát (Statement Generation & Client Outreach)

### 5.1. Khởi Tạo Bảng Kê Chi Tiết Giờ Công (Timesheet Statement Generation)
Ngay khi các dòng giờ công được ghi vào sổ cái phân tích:
1. Trường `qty_delivered` trên các dòng đơn hàng dịch vụ liên kết (`sale.order.line` với chính sách xuất hóa đơn theo giờ đã bàn giao) tự động tăng lên tương ứng.
2. Hệ thống kế toán tự động khởi tạo **Bảng Kê Chi Tiết Giờ Công & Hóa Đơn Tạm Tính (Timesheet Statement & Pro-forma Invoice - `account.move`)**:
   - Nhóm chi tiết theo Chuyên gia tư vấn, Cấp bậc chuyên môn, Ngày làm việc, Tên công việc và Kết quả bàn giao (Deliverables).
   - Áp dụng Bảng đơn giá chuẩn (Rate Card) theo hợp đồng kinh tế đã ký.
   - Thể hiện rõ số tiền trước thuế, thuế suất GTGT và tổng giá trị thanh toán tạm tính.
   - Trạng thái bảng kê: `al2c_timesheet_statement_state = 'draft_statement'`.

### 5.2. Mẫu Thư Điện Tử Đối Soát Chuẩn Doanh Nghiệp (Email Statement Template)
Hệ thống gửi email tự động tới Đại diện Khách hàng và Kế toán trưởng đối tác:
- **Tệp Đính Kèm:** Bảng Kê Chi Tiết Giờ Công (Định dạng PDF và Excel có chữ ký số PM).
- **Mã Xác Nhận Token An Toàn (Time-Boxed HMAC Token):**
  $$\text{Confirm Token} = \text{HMAC-SHA256}(\text{invoice\_id} \parallel \text{partner\_id} \parallel \text{secret\_key} \parallel \text{expiry\_date})$$
  Token có hiệu lực trong vòng 14 ngày làm việc.
- **Nút Bấm Trực Tuyến:**
  - 🟢 **"Xác Nhận Giờ Công & Đồng Ý Xuất Hóa Đơn"** (Dẫn tới Cổng Khách Hàng).
  - 🟡 **"Khiếu Nại / Yêu Cầu Đối Soát AL2C-INV-103"** (Mở hồ sơ tranh chấp thương mại, tự động đóng băng quy trình nhắc nợ).

---

## 6. Giai Đoạn 5: Khách Hàng Xác Nhận & Phát Hành Hóa Đơn Điện Tử NĐ 70/2025 (Portal Confirmation & Decree 70 E-Invoicing)

### 6.1. Xác Nhận 1-Click Trên Cổng Khách Hàng (Customer Portal Verification)
1. Đại diện khách hàng truy cập đường link bảo mật: `/innoria/portal/timesheet_statement/<id>?confirm_token=<token>`.
2. Giao diện Cổng Khách Hàng thể hiện trực quan bảng phân rã giờ công:
   - Tên từng chuyên gia tham gia dự án.
   - Chi tiết công việc đã thực hiện theo từng mốc SAP Activate.
   - Có thể hỏi đáp trực tiếp với trợ lý ảo **AI Statement Explainer** (`/my/invoices/<id>/ai_explain`) để hiểu rõ từng khoản mục trước khi bấm duyệt.
3. Đại diện khách hàng bấm nút **"Xác Nhận Đối Soát Bảng Kê Giờ Công"**:
   - Hệ thống cập nhật `al2c_timesheet_statement_state = 'confirmed'`.
   - Ghi nhận thời gian xác nhận (`al2c_timesheet_confirmed_date`), tên người xác nhận (`al2c_timesheet_confirmed_by`) và địa chỉ IP vào nhật ký kiểm toán bất biến.

### 6.2. Phát Hành Hóa Đơn VAT Điện Tử Hợp Pháp (Decree 70/2025/NĐ-CP Compliance)

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│               QUY TRÌNH PHÁT HÀNH HÓA ĐƠN ĐIỆN TỬ THEO NGHỊ ĐỊNH 70/2025                │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                        │
│   1. KHÁCH HÀNG XÁC NHẬN        2. KẾ TOÁN GHI SỔ        3. KÝ SỐ HSM & TRUYỀN CQT    │
│   Đã bấm xác nhận trên ───▶     Hóa đơn chuyển sang ───▶ Gửi dữ liệu XML tới Cục Thuế, │
│   Portal (State=confirmed)      trạng thái 'posted'      nhận Mã tra cứu CQT chính thức│
│                                                                      │                 │
│                                                                      ▼                 │
│                                 4. GỬI HÓA ĐƠN VAT CHÍNH THỨC                          │
│                                 Tự động gửi email kèm PDF bản thể hiện, XML gốc và    │
│                                 Mã QR thanh toán động Napas247 VietQR chính xác số tiền│
└────────────────────────────────────────────────────────────────────────────────────────┘
```

1. **Điều Kiện Tiên Quyết Bắt Buộc (Decree 70 Issuance Precondition):**
   - Trạng thái bảng kê bắt buộc phải là `confirmed` (Đã được khách hàng xác nhận) hoặc có biên bản nghiệm thu mốc được ký duyệt bởi cấp có thẩm quyền.
   - Nghiêm cấm xuất hóa đơn VAT khi bảng kê còn đang ở trạng thái nháp (`draft_statement`) hoặc đang có khiếu nại mở (`al2c.dispute`).
2. **Ký Số Chuyên Dùng (HSM Cloud Signing):**
   - Hóa đơn được ký số tự động bằng Chứng thư số doanh nghiệp lưu trữ trên thiết bị bảo mật phần cứng HSM (Hardware Security Module).
   - Tạo tệp XML hóa đơn gốc theo đúng định dạng chuẩn của Tổng cục Thuế Việt Nam.
3. **Thanh Toán Nhanh Qua Napas247 / VietQR:**
   - Trên bản thể hiện hóa đơn PDF tự động tích hợp mã QR Napas247 chuẩn EMVCo chứa sẵn số tài khoản ngân hàng của Innoria, số tiền thanh toán chính xác và nội dung chuyển khoản định danh mã hóa đơn, giúp dòng tiền thanh toán được đối soát tự động 100%.

---

## 7. Xử Lý Khủng Hoảng, Tranh Chấp & Khôi Phục Lỗi (Dispute Handling & Failure Recovery)

| Tình Huống Phát Sinh | Hậu Quả Tiềm Ẩn | Cơ Chế Phản Ứng Tự Động Của Hệ Thống | Trách Nhiệm Xử Lý |
| :--- | :--- | :--- | :--- |
| **Email gửi bị DMARC Fail** | Nguy cơ mạo danh tư vấn viên | Đưa vào vùng cách ly `is_quarantined = True`, gửi cảnh báo an ninh cho PM | Trưởng Dự Án liên hệ xác minh trực tiếp với tư vấn viên |
| **Gửi trùng email timesheet** | Nhân đôi giờ công và doanh thu | Khóa Dedup SHA-256 tự động nhận diện và chuyển trạng thái dòng thành `skipped` | Hệ thống xử lý tự động, ghi nhận log kiểm toán |
| **Khách hàng khiếu nại giờ công** | Trì hoãn thanh toán toàn bộ | Khởi tạo hồ sơ `al2c.dispute`, tự động ĐÓNG BĂNG quy trình nhắc nợ Dunning | Trưởng CoE và PM tổ chức họp đối soát kỹ thuật trong 48h |
| **Mất kết nối mạng tới CQT** | Gián đoạn phát hành hóa đơn | Hóa đơn lưu ở trạng thái chờ truyền; tự động kích hoạt cơ chế retry lũy thừa | Bộ phận IT Vận hành và Kế toán thuế theo dõi bảng điều khiển |

---
*Văn bản ban hành bởi Giám Đốc Tài Chính & Giám Đốc Khối Vận Hành Doanh Nghiệp Innoria.*
