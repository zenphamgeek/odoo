# SOP-CS-005: Tiêu Chuẩn Vận Hành Quản Lý Thành Công Khách Hàng (Customer Success), Dịch Vụ Cam Kết (SLA) & Giải Quyết Tranh Chấp Công Nợ (Commercial Disputes)

> **Mã quy trình:** SOP-CS-005  
> **Phiên bản:** 2.0 (Tháng 10/2026 - Chuẩn hóa Enterprise Multi-Product)  
> **Phạm vi áp dụng:** Toàn bộ 4 dòng sản phẩm chiến lược (**Insilos ERP**, **Vertical Resilience**, **Mojo AI**, **Zencode Ent**) thuộc Hệ sinh thái Doanh nghiệp Software Services.  
> **Chủ quản quy trình:** Giám đốc Vận hành Dịch vụ (Chief Services Officer - CSO) & Trưởng Ban Quản trị Thành công Khách hàng (Head of Customer Success).

---

## 1. Mục Đích & Phạm Vi Nguyên Tắc

### 1.1. Mục Đích
Thiết lập chuẩn mực vận hành cấp doanh nghiệp (Enterprise Grade) để tối ưu hóa chỉ số Tỷ lệ Giữ chân Khách hàng (Gross Revenue Retention - GRR > 95%), Tỷ lệ Tăng trưởng Doanh thu Ròng (Net Revenue Retention - NRR > 120%), đảm bảo tuân thủ nghiêm ngặt các cam kết dịch vụ kỹ thuật (SLA), đồng thời vận hành cơ chế giải quyết tranh chấp thương mại minh bạch (AL2C-INV-103) nhằm tránh gián đoạn dịch vụ đối với các khách hàng chiến lược.

### 1.2. 4 Trụ Cột Vận Hành Dịch Vụ
```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                   HỆ THỐNG VẬN HÀNH THÀNH CÔNG KHÁCH HÀNG (CS & SLA)              │
├────────────────────┬────────────────────┬───────────────────┬────────────────────┤
│   INSILOS ERP      │VERTICAL RESILIENCE │     MOJO AI       │    ZENCODE ENT     │
│ Cloud Core & L2C   │ GRC & Compliance   │ Autonomous Agents │ Developer Velocity │
├────────────────────┼────────────────────┼───────────────────┼────────────────────┤
│ • SLA 99.9% Uptime │ • Audit Readiness  │ • P99 Latency     │ • CI/CD Throughput │
│ • Hạch toán VAT    │ • ISO 27001 / D13  │   < 800ms         │ • Fleet Allocation │
│ • Đối soát Timesheet│ • RCM Live Sync   │ • Zero Data Leak  │ • Zero-Regression  │
└────────────────────┴────────────────────┴───────────────────┴────────────────────┘
```

---

## 2. Khung Cam Kết Mức Dịch Vụ Kỹ Thuật (Service Level Agreement - SLA Matrix)

Doanh nghiệp áp dụng 4 cấp độ dịch vụ (Tiered Support) được định cấu hình trực tiếp trong hệ thống quản lý hợp đồng (`sale.subscription` và `project.project`):

| Cấp Độ SLA | Thời Gian Phản Hồi Sự Cố P1 (Khẩn cấp) | Thời Gian Khắc Phục Sự Cố P1 (MTTR) | Khả Năng Sẵn Sàng Hệ Thống (Uptime SLA) | Kênh Tiếp Nhận Ưu Tiên | Bồi Thường Vi Phạm SLA (Service Credit) |
|---|---|---|---|---|---|
| **Platinum (Mission-Critical)** | $\le$ 15 phút (24/7/365) | $\le$ 2 giờ | **99.95%** | Dedicated Slack/Teams, Hotline VIP, Webhook PagerDuty | 10% phí dịch vụ tháng / mỗi 0.1% downtime |
| **Gold (Enterprise Standard)** | $\le$ 30 phút (24/7) | $\le$ 4 giờ | **99.90%** | Portal Doanh nghiệp, Email `support@inno.ai.vn`, Teams | 5% phí dịch vụ tháng / mỗi 0.1% downtime |
| **Silver (Professional)** | $\le$ 2 giờ (Giờ hành chính) | $\le$ 8 giờ | **99.50%** | Portal Doanh nghiệp, Email Ticket | 3% phí dịch vụ tháng |
| **Bronze (Standard SaaS)** | $\le$ 4 giờ (Giờ hành chính) | $\le$ 24 giờ | **99.00%** | Web Portal Ticket | Theo điều khoản hợp đồng chung |

### Phân Loại Sự Cố Kỹ Thuật (Severity Classification):
1. **Severity 1 (P1 - Critical Blocker):** Toàn bộ hệ thống ngừng hoạt động; dữ liệu cốt lõi không thể truy cập; đường ống tiếp nhận email hóa đơn/timesheet bị tắc nghẽn hoàn toàn; ảnh hưởng trực tiếp đến thanh toán hoặc báo cáo tài chính pháp định.
2. **Severity 2 (P2 - High Degradation):** Một phân hệ chính (như GRC Risk Register hoặc Mojo AI OCR Extraction) gặp lỗi nhưng quy trình công việc có giải pháp thay thế tạm thời; hiệu năng suy giảm nghiêm trọng.
3. **Severity 3 (P3 - Moderate Defect):** Tính năng đơn lẻ hoạt động không đúng đặc tả; lỗi giao diện không chặn nghiệp vụ cốt lõi; người dùng vẫn hoàn thành được giao dịch.
4. **Severity 4 (P4 - Minor Inquiry / Enhancement):** Yêu cầu hỗ trợ hướng dẫn sử dụng, thay đổi mẫu báo cáo, hoặc đề xuất tính năng mới.

---

## 3. Quy Trình Vận Hành Dunning & Kiểm Soát Công Nợ Tự Động (AL2C Dunning Engine)

Quy trình nhắc nợ đa tầng tuân thủ chuẩn SAP Horizon và IBM Carbon Design Tokens, loại bỏ hoàn toàn các thông báo thô sơ, bảo đảm quan hệ đối tác tin cậy:

```
[Ngày Hạn Thanh Toán - Due Date]
               │
               ▼
[D+3 Ngày]: Giai Đoạn 1 - Nhắc Nhở Lịch Sự (Gentle Reminder)
- Trạng thái: al2c_dunning_stage = 'd3_reminder'
- Tự động gửi Email đính kèm Bảng kê giờ công & QR Napas247 động
- CC: Quản lý Quan hệ Khách hàng (Customer Success Manager - CSM)
               │
               ▼
[D+15 Ngày]: Giai Đoạn 2 - Cảnh Báo Phí Chậm Trả & Leo Thang (Escalation Warning)
- Trạng thái: al2c_dunning_stage = 'd15_warning'
- Thông báo nguy cơ tạm dừng tính năng cao cấp (ví dụ: Mojo AI GPU Bursting, Zencode High-Tier Fleet)
- Cuộc họp rà soát công nợ giữa Giám đốc Tài chính hai bên
               │
               ▼
[D+30 Ngày]: Giai Đoạn 3 - Tạm Dừng Dịch Vụ Có Kiểm Soát (Service Suspension)
- Trạng thái: al2c_dunning_stage = 'd30_suspension'
- Tự động phong tỏa tài khoản triển khai và API tokens ngoại trừ quyền truy cập Backup dữ liệu (tuân thủ Nghị định 13/2023/NĐ-CP)
```

---

## 4. Cơ Chế Giải Quyết Tranh Chấp Thương Mại & Đối Soát Bảng Kê (AL2C-INV-103 Dispute Protocol)

Khi khách hàng có thắc mắc hoặc không đồng ý với một số dòng ghi nhận giờ công trong bảng kê chi tiết dịch vụ:

### 4.1. Kích Hoạt Tranh Chấp Trực Tuyến 1-Click
- Tại Cổng Khách Hàng (Customer Portal) hoặc thông qua phản hồi email bảng kê, khách hàng nhấn nút **"Khiếu nại / Đối soát (Dispute)"**.
- Hệ thống tự động khởi tạo bản ghi `al2c.dispute` liên kết trực tiếp với hóa đơn `account.move`:
  - `state = 'open'`
  - `reason`: Bóc tách theo danh mục (Lệch giờ công, Sai chức danh nhân sự, Thiếu biên bản nghiệm thu mốc Activate, Lệch đơn giá ngoại tệ).
- **Cơ chế Đóng Băng Nhắc Nợ Tự Động (Dunning Freeze Guard):**
  - Ngay khi `al2c_has_open_dispute = True`, toàn bộ cron job nhắc nợ (`d3_reminder`, `d15_warning`, `d30_suspension`) lập tức bị đóng băng (`freeze`).
  - Hệ thống nghiêm cấm mọi hành vi tạm ngắt dịch vụ của khách hàng trong khi tranh chấp đang được thụ lý (Zero False Suspension Invariant).

### 4.2. Quy Trình Thụ Lý & Segregation of Duties (SoD)
1. **Rà soát dữ liệu gốc (T+24h):** Quản lý Dự án (PM) đối chiếu giữa dòng `account.analytic.line`, email gốc lưu trữ tại `al2c.timesheet.staging`, và nhật ký commit mã nguồn (Git commit logs / PRs).
2. **Họp đối soát biên bản:** CSM chủ trì phiên làm việc ngắn trực tuyến cùng đại diện kỹ thuật khách hàng.
3. **Thẩm quyền phê duyệt giải quyết tranh chấp:**
   - Chỉ người dùng thuộc nhóm **Kế toán trưởng / Giám đốc Tài chính (`account.group_account_manager`)** hoặc **Giám đốc Kinh doanh (`sales_team.group_sale_manager`)** mới có thẩm quyền thực hiện thao tác `action_resolve_dispute()`.
   - Nhân viên kinh doanh hoặc kỹ sư dịch vụ thông thường không được phép tự ý hủy bỏ tranh chấp hoặc giải tỏa nhắc nợ (SoD Invariant - CWE-269).
4. **Điều chỉnh và Xuất Hóa Đơn Thay Thế:**
   - Nếu chấp thuận khiếu nại: Kế toán phát hành Hóa đơn điều chỉnh / Bù trừ (Credit Note) đúng theo quy chuẩn Nghị định 70/2025/NĐ-CP và Thông tư 78/2021/TT-BTC.
   - Tranh chấp chuyển trạng thái `resolved`, dunning engine tái kích hoạt theo số dư công nợ thực tế mới.

---

## 5. Bảng Đo Lường Hiệu Suất CS & SLA (Key Performance Indicators)

| Chỉ Số | Mục Tiêu | Chu Kỳ Đo Lường | Trách Nhiệm |
|---|---|---|---|
| **CSAT (Customer Satisfaction Score)** | $\ge 4.8 / 5.0$ | Sau mỗi mốc triển khai (SAP Activate Gate) | CSM & PM |
| **Gross Revenue Retention (GRR)** | $\ge 96\%$ | Hàng quý (Quarterly) | Head of CS |
| **Net Revenue Retention (NRR)** | $\ge 125\%$ | Hàng năm (Annual) | CSO & Head of CS |
| **Tỷ lệ Tuân Thủ SLA Uptime** | $\ge 99.9\%$ | Hàng tháng | CoE Cloud Infrastructure |
| **Thời gian Xử lý Tranh chấp Bảng kê (MTTR-Dispute)** | $\le 48$ giờ làm việc | Hàng tháng | PM & Lead Accountant |
| **Tỷ lệ Trùng Lặp Timesheet Được Chặn (Dedup Rate)** | $100\%$ | Liên tục (Real-time telemetry) | CoE Applied AI / Mojo AI |

---
*Tài liệu được ban hành chính thức và lưu trữ tại kho lưu trữ số của UNG DUNG SANG TAO LLC / INNORIA ENTERPRISE.*
