# Standard Operating Procedure (SOP): Lead-to-Cash (AL2C) & Deal-Desk Governance
## Quy Trình Vận Hành Chuẩn Từ Tiếp Cận Cơ Hội Đến Thu Hồi Công Nợ & Quản Trị Hợp Đồng

> **SOP Code:** SOP-AL2C-001 • **Version:** 3.0 (Master Council Compliant)  
> **Applicable Regulations:** Nghị định 13/2023/NĐ-CP (PDPD) • Nghị định 70/2025/NĐ-CP (E-Invoice) • Luật Thuế GTGT 48/2024 • Luật Kế toán 88/2015  
> **Key Models:** `crm.lead` • `sale.order` • `al2c.value.case` • `al2c.timesheet.staging` • `account.analytic.line` • `al2c.dispute` • `account.move`  

---

## 1. Sơ Đồ Quy Trình Tổng Thể 13 Giai Đoạn (13-Stage AL2C Architecture)

Quy trình Lead-to-Cash của công ty kết hợp phương pháp luận tiếp cận khách hàng **MCEM (Microsoft Customer Engagement Methodology)** ở pha Bán hàng và phương pháp luận **SAP Activate** ở pha Triển khai & Tính tiền dịch vụ:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                   GIAI ĐOẠN TIỀN DỰ ÁN & BÁN HÀNG (PRE-SALES & MCEM)                   │
├──────────────┬──────────────┬──────────────┬──────────────┬─────────────┬──────────────┤
│ 1. GEO &     │ 2. Thu Thập  │ 3. Đánh Giá  │ 4. Khảo Sát  │ 5. Lập Báo  │ 6. Phê Duyệt │
│    Thị Trường│    & Làm Giàu│    Cơ Hội    │    & Kiến Trúc│    Giá, SOW │    Hợp Đồng  │
│    (Inbound) │    Dữ Liệu   │ (BANT/MEDDIC)│    Giá Trị   │ & Deal Desk │    & Ký Số   │
└──────┬───────┴──────┬───────┴──────┬───────┴──────┬───────┴─────┬───────┴──────┬───────┘
       │              │              │              │             │              │
       ▼              ▼              ▼              ▼             ▼              ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│               GIAI ĐOẠN TRIỂN KHAI & THU HỒI DÒNG TIỀN (DELIVERY & CASH)               │
├──────────────┬──────────────┬──────────────┬──────────────┬─────────────┬──────────────┤
│ 7. Khởi Động │ 8. Thu Nhận  │ 9. Lập Bảng  │ 10. Khách    │ 11. Xuất    │ 12. Tái Ký & │
│    & Cung Cấp│    Timesheet │    Kê & Đối  │     Hàng Xác │     HĐ VAT  │     Gia Hạn  │
│    Tài Nguyên│    info@inno │    Soát Dịch │     Nhận 1-  │     NĐ 70 & │   Thuê Bao   │
│    (Activate)│    .ai.vn    │    Vụ Tư Vấn │     Click    │     Napas247│   & AMS      │
└──────────────┴──────────────┴──────────────┴──────────────┴─────────────┴──────────────┘
```

---

## 2. Chi Tiết Các Giai Đoạn Vận Hành & Hàng Rào Kiểm Soát (Governance Gates)

### Giai đoạn 1 & 2: Tiếp Cận Khách Hàng & Làm Giàu Dữ Liệu (Capture & Enrich)
- **Kênh Tiếp Nhận:** Website công ty, cổng thông tin `/llms.txt` (Generative Engine Optimization), sự kiện ngành hoặc email gửi tới `info@inno.ai.vn`.
- **Hàng Rào Kiểm Soát Nghị Định 13/2023/NĐ-CP (PDPD Guard):**
  - Mọi biểu mẫu đăng ký trực tuyến phải có checkbox xác nhận đồng thuận xử lý dữ liệu cá nhân (`consent_pdpd = True`).
  - Hệ thống tự động ghi nhật ký (Audit Log) thời điểm, địa chỉ IP và nội dung đồng thuận.
  - Tự động tra cứu mã số thuế (MST) qua Cổng thông tin Tổng cục Thuế để làm giàu thông tin: Tên pháp nhân chuẩn, người đại diện pháp luật, địa chỉ trụ sở chính và tình trạng đóng/mở mã số thuế.

### Giai đoạn 3: Đánh Giá Chất Lượng Cơ Hội (Lead Qualification)
- Áp dụng thang điểm **MEDDIC / BANT**:
  - **Budget (Ngân sách):** Dự kiến $\ge 150.000.000$ VND cho dự án triển khai hoặc $\ge 15.000.000$ VND/tháng cho dịch vụ thuê bao SaaS.
  - **Authority (Thẩm quyền):** Người tiếp cận có quyền ra quyết định (C-Level, Giám đốc CNTT, Kế toán trưởng) hoặc có quyền giới thiệu trực tiếp.
  - **Need (Nhu cầu thực tế):** Hệ thống cũ quá tải, chuẩn bị thanh kiểm tra thuế, yêu cầu chứng nhận an toàn hóa chất/ESG, hoặc hiện đại hóa quản trị.
  - **Timeline (Kế hoạch):** Kế hoạch golive cụ thể trong vòng 3 đến 6 tháng tới.

### Giai đoạn 4: Khảo Sát Nghiệp Vụ & Hồ Sơ Giá Trị (Value Architecture)
- Thiết lập tài liệu **Value Case (`al2c.value.case`)**:
  - Ghi nhận hiện trạng thất thoát, thời gian đối soát thủ công và rủi ro tuân thủ của khách hàng.
  - Định lượng chỉ số ROI dự kiến (ví dụ: giảm 80% thời gian đóng sổ kế toán tháng, tiết kiệm 1,2 tỷ VND chi phí nhân sự đối soát).
  - Bản thảo Kiến trúc Giải pháp Tổng thể (Solution Blueprint) tích hợp giữa Insilos ERP, Vertical Resilience và Mojo AI.

### Giai đoạn 5 & 6: Lập Báo Giá, SOW, Phê Duyệt Deal-Desk & Ký Hợp Đồng
- Lựa chọn bộ sản phẩm chuẩn từ Danh mục SKUs (ERP, SaaS, GRC, AI/Mojo).
- Áp dụng Hàng rào Deal-Desk (The Triple Guardrails chi tiết tại Mục 3).
- Ký kết hợp đồng điện tử qua `sign.request` có chứng thư số hợp lệ.

### Giai đoạn 7: Khởi Động Dự Án Chuẩn SAP Activate (Prepare Phase)
- Hệ thống tự động tạo dự án (`project.project`) từ mẫu chuẩn, thiết lập 5 giai đoạn Activate (Prepare ➔ Explore ➔ Realize ➔ Deploy ➔ Run).
- Cung cấp tài nguyên hệ thống, môi trường Dev/Staging/Production cô lập theo nguyên tắc Sovereign DB Isolation.

### Giai đoạn 8: Thu Nhận Giờ Công Chuyên Gia Hướng Sự Kiện (Event-Driven Timesheet Ingestion)
- Chuyên gia tư vấn gửi email báo cáo công việc về `info@inno.ai.vn`.
- Đường ống tự động đẩy dữ liệu vào vùng đệm `al2c.timesheet.staging`.
- Mojo AI bóc tách thông minh đa định dạng (.xlsx, .xls, .csv, body), kiểm định định danh 3 tầng và chống trùng lặp qua dấu vân tay SHA-256.
- Trưởng Dự Án (PM) kiểm tra và bấm nút duyệt 1-click **"Xác Nhận & Ghi Nhận Timesheet"** để ghi vào sổ cái phân tích `account.analytic.line`.

### Giai đoạn 9: Lập Bảng Kê Giờ Công & Gửi Email Đối Soát Cho Khách Hàng (Timesheet Statement & Customer Review)
- Hệ thống tự động cập nhật số lượng bàn giao `qty_delivered` trên các dòng hợp đồng dịch vụ liên kết (`sale.order.line`).
- Khởi tạo **Bảng Kê Chi Tiết Giờ Công & Hóa Đơn Tạm Tính (Timesheet Statement & Pro-forma Invoice)**:
  - Chi tiết từng chuyên gia: họ tên, vai trò, ngày làm, công việc, số giờ bàn giao, đơn giá giờ công theo hợp đồng (Rate Card).
- Gửi email chuẩn doanh nghiệp **IBM Carbon & SAP Horizon** (`email_template_al2c_timesheet_statement_confirm`) tới Người đại diện khách hàng.
- Thư đính kèm bảng kê có chữ ký số PM và liên kết truy cập Cổng Khách hàng (Customer Portal) bảo mật bằng mã xác nhận một lần (Token).

### Giai đoạn 10: Khách Hàng Xác Nhận 1-Click Trực Tuyến (Customer Confirmation Protocol)
- Khách hàng kiểm tra bảng kê giờ công trên Portal:
  - Trường hợp đồng ý: Bấm nút **"Xác Nhận Giờ Công & Đồng Ý Xuất Hóa Đơn"**. Hệ thống lập tức cập nhật trạng thái `al2c_timesheet_statement_state = 'confirmed'` và ghi vết kiểm toán (IP, timestamp, định danh người duyệt).
  - Trường hợp có thắc mắc: Bấm **"Khiếu nại / Đối soát AL2C-INV-103"**, tiến trình nhắc nợ được đóng băng ngay lập tức để hai bên giải trình minh bạch.

### Giai đoạn 11: Phát Hành Hóa Đơn Điện Tử VAT Nghị Định 70/2025/NĐ-CP & Thu Hồi Tiền (Billing & Collections)
- Hóa đơn dịch vụ tư vấn billable chuyển sang trạng thái đã ghi sổ (`posted`).
- Hệ thống kích hoạt `action_issue_einvoice()`:
  - Ký số bằng chứng thư số HSM doanh nghiệp.
  - Gửi dữ liệu đồng bộ với Cơ quan Thuế (CQT) để nhận Mã tra cứu và Ký hiệu mẫu số (ví dụ: `1C26TAA-00000001`).
  - Tích hợp mã QR **Napas247 / VietQR** thanh toán tự động vào tài khoản Vietcombank của Innoria.
- Gửi hóa đơn điện tử chính thức (PDF + XML gốc) tới Ban Giám đốc và Kế toán của khách hàng.
- Tự động khớp dòng tiền đối soát ngân hàng khi tiền về tài khoản.

### Giai đoạn 12 & 13: Đôn Đốc Công Nợ (Dunning), Tái Ký & Gia Hạn Thuê Bao (Renewal & AMS)
- Vận hành thang nhắc nợ tự động ($D-3, D+1, D+7, D+15, D+30$).
- Theo dõi định kỳ SLA hỗ trợ vận hành AMS và đề xuất gia hạn thuê bao SaaS 60 ngày trước khi hết hạn hợp đồng.

---

## 3. Cổng Phê Duyệt Deal-Desk & Phân Quyền Nhiệm Vụ (Deal-Desk SoD Guardrails)

Tại **Giai đoạn 5 (Lập Báo Giá, SOW & Deal-Desk)**, hệ thống áp dụng cơ chế phân quyền kiểm soát tự động tại tầng ORM nhằm bảo vệ biên lợi nhuận của doanh nghiệp:

### 3.1. Bộ Ba Hàng Rào Kiểm Soát Bắt Buộc (The Triple Guardrails):
Hệ thống **TỰ ĐỘNG KHÓA (BLOCK)** hành động gửi báo giá (`action_quotation_send`) hoặc xác nhận đơn hàng (`action_confirm`) nếu phát hiện bất kỳ vi phạm nào sau đây:

1. **Hàng Rào Chiết Khấu (Discount Cap):**
   $$\text{Chiết Khấu Thực Tế} = 1 - \frac{\text{Tổng Tiền Dòng}}{\text{Giá Niêm Yết} \times \text{Số Lượng}} > 10\%$$
2. **Hàng Rào Quy Mô Hợp Đồng (TCV Threshold):**
   $$\text{Giá Trị Hợp Đồng Trước Thuế (Untaxed TCV)} > 500.000.000 \text{ VND}$$
3. **Hàng Rào Biên Lợi Nhuận Gộp Tối Thiểu (Gross Margin Floor):**
   $$\text{Biên Lợi Nhuận Gộp} = \frac{\text{Untaxed TCV} - \text{Chi Phí Nhân Lực & Hạ Tầng Dự Kiến}}{\text{Untaxed TCV}} < 35\%$$
4. **Hàng Rào Lịch Sử Công Nợ Khách Hàng:**
   Khách hàng hiện có bất kỳ hóa đơn nào quá hạn quá 30 ngày ($D+30$) chưa thanh toán.

### 3.2. Quy Trình Mở Khóa Phê Duyệt (Approval Workflow):
- Nhân viên kinh doanh thuộc nhóm `insilos_al2c.group_al2c_agent` **KHÔNG THỂ TỰ PHÊ DUYỆT**.
- Đơn hàng vi phạm sẽ chuyển sang trạng thái chờ duyệt `al2c_state = 'pending_approval'`.
- Chỉ người dùng thuộc nhóm **Giám Đốc Bán Hàng (`sales_team.group_sale_manager`)** hoặc **Ban Giám Đốc (Board of Directors)** mới có quyền tích chọn trường `al2c_approved = True` kèm theo lý do giải trình kinh doanh hợp lệ được ghi nhận vào Chatter.

---

## 4. Quản Trị Nghiệm Thu, Xuất Hóa Đơn & Đôn Đốc Công Nợ (Billing & Collections)

### 4.1. Quy Chuẩn Xuất Hóa Đơn Điện Tử Theo Nghị Định 70/2025/NĐ-CP:
- **Nguyên tắc cốt lõi:** Tuyệt đối không xuất hóa đơn khống hoặc xuất hóa đơn sai thời điểm. Hóa đơn điện tử chỉ được phát hành khi thỏa mãn một trong ba điều kiện:
  1. *Tiền tạm ứng dịch vụ (Advance Payment):* Xuất hóa đơn trong vòng 24 giờ kể từ thời điểm nhận được tiền vào tài khoản ngân hàng.
  2. *Nghiệm thu theo mốc (Milestone Acceptance):* Phải có **Biên bản nghiệm thu bàn giao có chữ ký số hai bên** được đính kèm vào hồ sơ `documents.document` liên kết với mốc dự án.
  3. *Dịch vụ tư vấn theo giờ (Billable Timesheet / T&M):* Phải có **Bảng kê chi tiết giờ công (Timesheet Statement)** được Trưởng Dự Án phê duyệt từ dữ liệu bóc tách của `al2c.timesheet.staging` và **ĐÃ ĐƯỢC ĐẠI DIỆN KHÁCH HÀNG BẤM XÁC NHẬN TRỰC TUYẾN** trên Cổng Khách Hàng (`al2c_timesheet_statement_state == 'confirmed'`).

- **Tỷ Trọng Thanh Toán Mẫu Cho Dự Án Triển Khai (`ERP-STARTER` / `ERP-GROWTH`):**
  - Mốc 1 (Prepare - Tạm ứng khởi động): **15%** giá trị hợp đồng.
  - Mốc 2 (Explore - Ký duyệt thiết kế chi tiết SDD): **25%** giá trị hợp đồng.
  - Mốc 3 (Realize - Hoàn thành kiểm thử chấp nhận UAT): **35%** giá trị hợp đồng.
  - Mốc 4 (Deploy - Golive chính thức đưa vào sử dụng): **15%** giá trị hợp đồng.
  - Mốc 5 (Run - Hết thời gian bảo hành/Hypercare 30 ngày): **10%** giá trị hợp đồng.

### 4.2. Thang Đôn Đốc Công Nợ & Cơ Chế Đóng Băng Tranh Chấp (`al2c.dispute`):
Hệ thống tự động kích hoạt tiến trình đôn đốc thanh toán (Dunning Ladder):
- **Ngày $D-3$ (Trước hạn 3 ngày):** Email tự động gửi bảng kê hóa đơn và mã QR VietQR / Napas247 chuyển khoản chính xác nội dung.
- **Ngày $D+1$ (Quá hạn 1 ngày):** Thông báo nhắc nhở lịch sự qua Email và Zalo ZNS cho Kế toán thanh toán của khách hàng.
- **Ngày $D+7$ (Quá hạn 7 ngày):** Thông báo đôn đốc chính thức lần 1; hệ thống tự động giao nhiệm vụ nhắc nợ cho Quản lý khách hàng (Account Executive).
- **Ngày $D+15$ (Quá hạn 15 ngày):** Thư cảnh báo ngừng cung cấp dịch vụ kỹ thuật và hỗ trợ AMS nếu không hoàn tất thanh toán.
- **Ngày $D+30$ (Quá hạn 30 ngày):** Tự động chuyển tài khoản sang trạng thái đóng băng tín dụng, khóa quyền nâng cấp hoặc mở rộng user; chuyển hồ sơ sang bộ phận Pháp chế xử lý.

> **CƠ CHẾ ĐÓNG BĂNG KHIẾU NẠI (`AL2C-INV-103`):**  
> Khi khách hàng mở phiếu khiếu nại thương mại hoặc kỹ thuật (`al2c.dispute`), toàn bộ tiến trình đôn đốc nhắc nợ và tính lãi phạt chậm trả **TỰ ĐỘNG TẠM DỪNG (FREEZE)** cho đến khi Giám đốc Tài chính hoặc Trưởng Ban Dự án xác nhận giải quyết xong khiếu nại.
