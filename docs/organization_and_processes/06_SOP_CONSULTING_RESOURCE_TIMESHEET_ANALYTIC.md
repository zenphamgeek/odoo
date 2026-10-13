# Standard Operating Procedure (SOP): Consulting Resources & Timesheet Pipeline
## Quy Trình Quản Trị Nguồn Lực Tư Vấn, Thu Nhận Báo Cáo Thời Gian Hướng Sự Kiện & Đối Soát Doanh Thu

> **SOP Code:** SOP-OPS-002 • **Version:** 2.0 (Enterprise Standard)  
> **Key Architecture:** Event-Driven Timesheet Email Ingestion Pipeline (`info@inno.ai.vn`)  
> **Core Models:** `al2c.timesheet.staging` • `account.analytic.line` • `project.task` • `hr.employee`  

---

## 1. Kiến Trúc Thu Nhận Timesheet Tự Động Hướng Sự Kiện (Event-Driven Ingestion Pipeline)

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
               │  • Trạng thái: draft ➔ parsed ➔ validated ➔ posted     │
               │  • Lưu trữ raw_payload, tệp đính kèm và siêu dữ liệu   │
               └───────────────────────────┬────────────────────────────┘
                                           │
                                           ▼ (3. Mojo AI Intelligent Parser)
               ┌────────────────────────────────────────────────────────┐
               │              MOJO AI PARSER & DEDUP ENGINE             │
               │  • Bóc tách bảng biểu Excel (.xlsx), CSV, hoặc Markdown│
               │  • Khớp định danh chuyên gia: email ➔ hr.employee      │
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
                                           ▼ (5. Final Commit)
               ┌────────────────────────────────────────────────────────┐
               │          SỔ CÁI PHÂN TÍCH (IMMUTABLE ANALYTIC LINE)    │
               │                 account.analytic.line                  │
               │  • Ghi nhận chi phí giờ công thực tế vào dự án         │
               │  • Cập nhật tỷ lệ giải ngân ngân sách giờ (Burn Rate)  │
               └────────────────────────────────────────────────────────┘
```

---

## 2. Các Bước Vận Hành Đường Ống Timesheet Bằng Mô Hình Staging

### Bước 1: Tiếp Nhận & Lưu Trữ Vùng Đệm (Staging Buffer)
1. Kỹ sư tư vấn hoàn tất công việc trong tuần, gửi email báo cáo về `info@inno.ai.vn` kèm bảng tính Excel hoặc gõ trực tiếp bảng Markdown vào nội dung thư.
2. Tiến trình `mail_pubsub_daemon.py` lắng nghe sự kiện push từ Google Cloud Pub/Sub, lập tức tạo mới bản ghi `al2c.timesheet.staging` ở trạng thái `draft`.
3. Tệp tin đính kèm được lưu an toàn trong kho lưu trữ chứng từ `documents.document` phục vụ đối soát kiểm toán.

### Bước 2: Bóc Tách & Đối Khớp Dữ Liệu Thông Minh (Parsing & Matching)
Mojo AI Parser thực hiện tuần tự các bước kiểm định tự động:
1. **Khớp Chuyên Gia:** Lấy địa chỉ email người gửi đối chiếu với trường `work_email` trên bảng nhân sự `hr.employee`. Nếu không tìm thấy, bản ghi bị đánh dấu `error = "Unknown Consultant Email"`.
2. **Khớp Dự Án & Đầu Việc:** Phân tích cú pháp tên dự án (ví dụ: `[ERP-STARTER] Cty Nông Sản X`) và tên công việc (ví dụ: `Fit-to-Standard Phân Hệ Kế Toán`) để tìm ID tương ứng trên `project.task`.
3. **Phát Hiện Trùng Lặp (Deduplication Guard):**
   - Hệ thống quét bộ khóa duy nhất `(employee_id, date, task_id)`.
   - Nếu đã tồn tại bản ghi đã duyệt trên `account.analytic.line` hoặc bản ghi trùng lặp trong đợt gửi trước, hệ thống tự động gắn nhãn cảnh báo `is_duplicate = True` và chuyển trạng thái sang `needs_review`.

### Bước 3: Phê Duyệt 1-Click Dành Cho Trưởng Dự Án (1-Click PM Approval)
1. Trưởng Dự Án (Project Manager) mở màn hình **Hàng Đợi Duyệt Giờ Công (Staging Review Queue)** trên Insilos ERP.
2. Giao diện hiển thị trực quan các dòng dữ liệu đã được đối khớp thành công với các mã màu:
   - Xanh lá cây: Khớp chính xác 100%, không trùng lặp, nằm trong hạn mức ngân sách.
   - Vàng: Bản ghi có dấu hiệu trùng lặp hoặc nội dung mô tả công việc chưa rõ ràng.
   - Đỏ: Không khớp được dự án hoặc vượt định mức cho phép.
3. Trưởng Dự Án kiểm tra nhanh và bấm nút **"Xác Nhận & Ghi Sổ" (Post Timesheets)**. Hệ thống tạo các bản ghi bất biến `account.analytic.line` và đóng bản ghi staging với trạng thái `posted`.

---

## 3. Hệ Thống Cảnh Báo Cháy Ngân Sách Giờ Tư Vấn (Burn-Rate Alerting Protocol)

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

## 4. Đối Soát Giờ Công Sang Doanh Thu Hóa Đơn (Timesheet to Billing Reconciliation)

1. **Đối Với Hợp Đồng Theo Thời Gian & Vật Liệu (Time & Materials - T&M):**
   - Vào ngày 25 hàng tháng, hệ thống tổng hợp toàn bộ các dòng `account.analytic.line` đã được PM phê duyệt.
   - Nhân số giờ với đơn giá trong Bảng đơn giá chuẩn (Rate Card) đã ký trong hợp đồng để tạo hóa đơn nháp (Draft Customer Invoice).
   - Đính kèm bảng kê chi tiết giờ công có xác nhận của PM vào hồ sơ hóa đơn.
2. **Đối Với Hợp Đồng Trọn Gói Theo Mốc (Fixed-Price Milestone):**
   - Giờ công phân tích được dùng để tính toán **Chi Phí Thực Tế (Actual Cost of Goods Sold - COGS)** và đo lường Biên Lợi Nhuận Gộp Thời Gian Thực (Real-time Margin) của dự án:
     $$\text{Biên Lợi Nhuận Dự Án} = \frac{\text{Doanh Thu Mốc Đã Ký} - \sum (\text{Giờ Công Thực Tế} \times \text{Chi Phí Lương Giờ})}{\text{Doanh Thu Mốc Đã Ký}}$$
   - Nếu biên lợi nhuận gộp thực tế tụt xuống dưới ngưỡng 35%, hệ thống sẽ tự động đưa dự án vào danh sách giám sát đặc biệt của Giám đốc Vận hành (COO) và Giám đốc Tài chính (CFO).
