# Standard Operating Procedure (SOP): SAP Activate Delivery Framework
## Khung Quy Trình Triển Khai Dịch Vụ Phần Mềm Doanh Nghiệp Theo Chuẩn SAP Activate

> **SOP Code:** SOP-PRJ-001 • **Version:** 2.0 (Enterprise Standard)  
> **Methodology:** SAP Activate (Fit-to-Standard & Clean Core) Combined with Agile Sprints  
> **Key Platforms:** Insilos ERP • Vertical Resilience • Mojo AI Solutions  

---

## 1. Triết Lý Triển Khai "Fit-to-Standard" & "Clean Core"

Thay vì tùy biến mã nguồn vô độ dẫn đến sự phân mảnh và tắc nghẽn khi nâng cấp, Innoria áp dụng nghiêm ngặt triết lý **Khớp mẫu Nghiệp vụ Chuẩn (Fit-to-Standard)** và **Giữ Lõi Sạch (Clean Core)**:
- **80% Chuẩn Hóa:** Tận dụng 80% quy trình chuẩn sẵn có của Insilos ERP (kế toán VAS, chuỗi cung ứng, sản xuất) và Vertical Resilience (ma trận rủi ro, kiểm toán).
- **20% May Đo & Giá Trị Khác Biệt:** Tập trung nguồn lực phát triển các tính năng tạo ra lợi thế cạnh tranh độc quyền cho khách hàng bằng các module độc lập, giao diện OWL 2 phản ứng và tác nhân Mojo AI.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        SAP ACTIVATE 5-PHASE LIFECYCLE FOR INSILOS                      │
├─────────────────┬─────────────────┬──────────────────┬────────────────┬────────────────┤
│ 1. PREPARE      │ 2. EXPLORE      │ 3. REALIZE       │ 4. DEPLOY      │ 5. RUN         │
│  (Khởi Động)    │  (Khám Phá)     │  (Hiện Thực Hóa) │  (Chuyển Giao) │  (Vận Hành)    │
├─────────────────┼─────────────────┼──────────────────┼────────────────┼────────────────┤
│ • Project       │ • Fit-to-       │ • Cấu hình phân  │ • Chuyển đổi   │ • Hỗ trợ       │
│   Charter       │   Standard      │   hệ & Sprints   │   dữ liệu chốt │   Hypercare    │
│ • Thiết lập môi │   Workshops     │ • May đo module  │ • Đào tạo người│   30 ngày      │
│   trường dev/uat│ • Bắt bệnh Delta│   độc lập        │   dùng cuối    │ • Chuyển giao  │
│ • RACI &        │ • Tài liệu thiết│ • Kiểm thử chấp  │ • Diễn tập     │   đội ngũ AMS  │
│   Kick-off      │   kế SDD        │   nhận UAT       │   Cutover      │ • Đo lường ROI │
├─────────────────┼─────────────────┼──────────────────┼────────────────┼────────────────┤
│ 🚪 Q-Gate 1     │ 🚪 Q-Gate 2     │ 🚪 Q-Gate 3      │ 🚪 Q-Gate 4    │ 🚪 Q-Gate 5    │
│ (15% Milestone) │ (25% Milestone) │ (35% Milestone)  │ (15% Milestone)│ (10% Milestone)│
└─────────────────┴─────────────────┴──────────────────┴────────────────┴────────────────┘
```

---

## 2. Chi Tiết 5 Pha Triển Khai & Các Cổng Kiểm Định Chất Lượng (Quality Gates)

### Pha 1: Chuẩn Bị & Khởi Động Dự Án (Prepare)
- **Mục tiêu:** Đồng thuận mục tiêu, thành lập Ban chỉ đạo dự án (Steering Committee) và dựng môi trường kỹ thuật.
- **Các Hoạt Động Cốt Lõi:**
  1. Ban hành **Điều lệ Dự án (Project Charter)** quy định rõ phạm vi công việc, ngân sách, nhân sự tham gia và kênh liên lạc chính thức.
  2. Khởi tạo 3 môi trường phân lập trên cụm Kubernetes:
     - `DEV (Development):` Môi trường phát triển kỹ thuật riêng biệt của Innoria.
     - `UAT (Staging/User Acceptance):` Môi trường kiểm thử có dữ liệu mẫu của khách hàng.
     - `PRD (Production):` Môi trường vận hành thực tế được bảo vệ tuyệt đối, mã hóa SSL và sao lưu tự động.
  3. Tổ chức lễ Kick-off chính thức với sự tham gia của Lãnh đạo cấp cao hai bên.
- **🚪 Cổng Kiểm Định Q-Gate 1:**
  - Điều lệ dự án có chữ ký đầy đủ hai bên.
  - 3 môi trường đã sẵn sàng hoạt động.
  - Nghiệm thu Mốc 1 $\rightarrow$ Kích hoạt xuất hóa đơn tạm ứng 15%.

---

### Pha 2: Khám Phá & Khớp Mẫu Nghiệp Vụ (Explore)
- **Mục tiêu:** Xác định sự tương thích giữa quy trình chuẩn của phần mềm và thực tế vận hành của doanh nghiệp; nhận diện các điểm chênh lệch (Delta Backlog).
- **Các Hoạt Động Cốt Lõi:**
  1. Tổ chức chuỗi hội thảo **Fit-to-Standard Workshops** theo từng phân hệ: Tài chính kế toán, Chuỗi cung ứng, Quản trị rủi ro & HSE, Nhân sự & Tiền lương.
  2. Phân loại yêu cầu thành 3 nhóm:
     - *Standard (Chuẩn):* Doanh nghiệp áp dụng quy trình chuẩn của hệ thống mà không cần lập trình thêm.
     - *Configuration (Cấu hình):* Cài đặt quy tắc phê duyệt, biểu mẫu, tham số hệ thống.
     - *Delta (May đo):* Báo cáo đặc thù, tích hợp hệ thống bên thứ 3 hoặc nghiệp vụ độc quyền.
  3. Hoàn thiện **Tài Liệu Thiết Kế Giải Pháp Chi Tiết (Solution Design Document - SDD)**.
  4. Cung cấp biểu mẫu chuẩn bị dữ liệu danh mục (Khách hàng, Nhà cung cấp, Vật tư, Số dư tài khoản, Định mức sản xuất).
- **🚪 Cổng Kiểm Định Q-Gate 2:**
  - Tài liệu SDD được Kế toán trưởng và Giám đốc nghiệp vụ phía khách hàng ký duyệt chính thức.
  - Danh mục Delta Backlog được chốt phạm vi, không phát sinh chi phí ẩn.
  - Nghiệm thu Mốc 2 $\rightarrow$ Kích hoạt xuất hóa đơn 25%.

---

### Pha 3: Hiện Thực Hóa & Kiểm Thử Chấp Nhận (Realize)
- **Mục tiêu:** Cấu hình toàn bộ hệ thống, phát triển các chức năng Delta theo chuẩn Clean-Core và tổ chức kiểm thử nghiệm thu người dùng (UAT).
- **Các Hoạt Động Cốt Lõi:**
  1. Chia nhỏ quá trình phát triển thành các chu kỳ chạy nước rút (Agile Sprints) kéo dài 2 tuần.
  2. Cuối mỗi Sprint tổ chức buổi trình diễn thực tế (Sprint Review / Demo) cho người dùng cốt lõi (Key Users).
  3. Kỹ thuật lập trình tuân thủ tiêu chuẩn: Giao diện thuần OWL 2 Component, biến CSS semantic token (`--o-theme-*`), không can thiệp DDL trực tiếp vào schema database.
  4. Thực hiện kiểm thử tích hợp toàn diện (System Integration Testing - SIT) với Cổng ngân hàng Napas247 và hệ thống Hóa đơn điện tử.
  5. Tổ chức đợt **Kiểm Thử Chấp Nhận Người Dùng (UAT - User Acceptance Testing)** dựa trên các kịch bản thực tế xuyên suốt chu trình kinh doanh (End-to-End Scenarios).
- **🚪 Cổng Kiểm Định Q-Gate 3:**
  - 100% kịch bản kiểm thử UAT trọng yếu (Critical / High) vượt qua thành công với 0 lỗi nghiêm trọng (Blocker).
  - Biên bản xác nhận UAT hoàn tất có chữ ký xác nhận của đại diện khách hàng.
  - Nghiệm thu Mốc 3 $\rightarrow$ Kích hoạt xuất hóa đơn 35%.

---

### Pha 4: Chuyển Giao & Vận Hành Chính Thức (Deploy & Cutover)
- **Mục tiêu:** Chuyển đổi dữ liệu số dư, đào tạo đại trà người dùng cuối và chính thức vận hành hệ thống (Go-Live).
- **Các Hoạt Động Cốt Lõi:**
  1. Ban hành **Kịch bản Chuyển Đổi Từng Giờ (Hour-by-Hour Cutover Runbook)** phân công chi tiết thời điểm chốt sổ hệ thống cũ, trích xuất dữ liệu, kiểm toán số dư đầu kỳ và nạp dữ liệu vào Insilos ERP.
  2. Tổ chức đào tạo người dùng cuối (End-User Training) và cấp chứng nhận người dùng đủ điều kiện thao tác.
  3. Cuộc họp Ban Chỉ đạo chốt quyết định vận hành chính thức (**Go / No-Go Decision Gate**):
     - Dữ liệu số dư kế toán khớp 100% giữa hai hệ thống.
     - Hạ tầng máy chủ kiểm tra tải thành công.
     - Đội ngũ hỗ trợ khẩn cấp túc trực tại hiện trường.
  4. Chính thức bấm nút Go-Live đưa hệ thống vào phục vụ hoạt động sản xuất kinh doanh thường nhật.
- **🚪 Cổng Kiểm Định Q-Gate 4:**
  - Biên bản bàn giao đưa hệ thống vào vận hành chính thức (Go-Live Certificate) được ký kết.
  - Toàn bộ giao dịch nghiệp vụ mới được hạch toán trực tiếp trên hệ thống Insilos ERP.
  - Nghiệm thu Mốc 4 $\rightarrow$ Kích hoạt xuất hóa đơn 15%.

---

### Pha 5: Vận Hành Ổn Định & Chuyển Giao Dài Hạn (Run & Value Realization)
- **Mục tiêu:** Hỗ trợ sát sao trong 30 ngày đầu (Hypercare), đóng dự án và chuyển sang quy trình bảo trì dài hạn (AMS).
- **Các Hoạt Động Cốt Lõi:**
  1. Đội ngũ tư vấn triển khai túc trực tại chỗ trong 2 tuần đầu và hỗ trợ từ xa trong 2 tuần tiếp theo để giải quyết ngay lập tức các thắc mắc nghiệp vụ trong kỳ đóng sổ tháng đầu tiên.
  2. Bàn giao tài liệu hướng dẫn vận hành, nhật ký cấu hình hệ thống cho Quản trị viên CNTT của khách hàng.
  3. Chuyển giao trách nhiệm tiếp nhận sự cố sang Đội ngũ Hỗ trợ Dịch vụ (AMS Support Team) thông qua hệ thống Helpdesk.
  4. Đánh giá mức độ hiện thực hóa giá trị doanh nghiệp (Value Realization Assessment) so với mục tiêu đặt ra ban đầu tại tài liệu `al2c.value.case`.
- **🚪 Cổng Kiểm Định Q-Gate 5:**
  - Kết thúc thời gian Hypercare 30 ngày với nhật ký không còn tồn đọng lỗi mức độ 1 và 2.
  - Biên bản thanh lý hợp đồng và bàn giao bảo hành được ký kết.
  - Nghiệm thu Mốc 5 $\rightarrow$ Kích hoạt xuất hóa đơn quyết toán 10%.

---

## 3. Quy Trình Quản Lý Thay Đổi Phạm Vi (Scope Change Request - CR)

Để tránh hiện tượng dự án bị phình to phạm vi (Scope Creep) làm cháy ngân sách và trễ tiến độ:
1. Mọi yêu cầu phát sinh ngoài tài liệu SDD đã ký phải được lập thành **Phiếu Yêu Cầu Thay Đổi (CR Form)**.
2. Trưởng Ban Dự án (Project Manager) và Kiến trúc sư giải pháp thực hiện đánh giá tác động 3 chiều:
   - Tác động tới tiến độ (Schedule Impact): Kéo dài bao nhiêu ngày?
   - Tác động tới ngân sách (Budget Impact): Cần bao nhiêu ngày công tư vấn (Man-Days) phụ trội?
   - Tác động tới kiến trúc (Architectural Risk): Có vi phạm nguyên tắc Clean-Core hay không?
3. Nếu chi phí phát sinh $\le 5\%$ ngân sách dự án: Giám đốc Dự án hai bên có quyền quyết định bằng văn bản.
4. Nếu chi phí phát sinh $> 5\%$ ngân sách: Phải ký phụ lục hợp đồng bổ sung và kích hoạt quy trình phê duyệt Deal-Desk trước khi lập trình.
