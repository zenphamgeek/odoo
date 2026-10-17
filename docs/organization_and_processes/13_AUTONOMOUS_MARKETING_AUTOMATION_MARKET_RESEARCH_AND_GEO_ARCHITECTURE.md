# SOP-DGM-13: Quy Trình Tự Động Hóa Marketing (`Autonomous Marketing Automation`), Nghiên Cứu Thị Trường B2B Liên Tục (`Market Research Radar`), Tình Báo Đối Thủ (`Battlecards`) & Tối Ưu Công Cụ AI (`GEO Content Supply Chain`)

> **Pháp nhân áp dụng**: Công ty Cổ phần Digimate (`Digimate JSC` / Thương hiệu Công nghệ Quốc tế: **Innoria** — `https://innoria.com`)  
> **Mã số thuế**: `0317958465` (`0318201249` đối ứng nội bộ) • **Đơn vị BHXH**: `TZ0857G` (BHXH Quận 7)  
> **Mã quy trình**: `SOP-DGM-13` • **Biểu mẫu đính kèm**: `TPL-MKT-01` • **Chuẩn quản trị**: `AL2C-MKT-402/403`, `ISO/IEC 27701`, `Nghị định 13/2023/NĐ-CP`, `Nghị định 70/2025/NĐ-CP`

---

## 1. Mục Đích & Triết Lý Quản Trị (`100% Claim Atom Grounding & Zero Hallucination Marketing`)

Trong lĩnh vực phát triển phần mềm B2B, cho thuê đội ngũ kỹ sư chuyên trách (`Dedicated Agile Squad / Staff Augmentation` như hợp đồng **MTI Technology**, **AIfin**, **Canva**) và triển khai hệ thống quản trị doanh nghiệp **Insilos Enterprise ERP / GRC / AI**, hoạt động Marketing và Nghiên cứu thị trường phải tuân thủ **3 nguyên tắc cốt lõi**:

1. **Nghiên cứu Thị trường Định lượng Liên tục (`dgm.market.research.radar` — `MKT-RES-01..06`)**:
   - Mọi chiến dịch tiếp thị đều xuất phát từ dữ liệu quy mô thị trường thực tế (**TAM / SAM / SOM** tính theo tỷ VNĐ/năm và tốc độ tăng trưởng kép **CAGR %** giai đoạn 2026–2030 tại Việt Nam & APAC).
   - Phân tích ma trận điểm yếu của đối thủ cạnh tranh truyền thống (`Legacy ERPs: SAP ECC/S4, Oracle NetSuite`, `Big-Box Outsourcers`, `Local Point-Solution Vendors`) đối chiếu với **Lợi thế Độc tôn (`Unfair Moat`) của Innoria / Digimate**: Kiến trúc Clean-Core Odoo 20, tích hợp gốc Hóa đơn Điện tử Nghị định 70 (`1C26TAA`), ưu đãi thuế TNDN Doanh nghiệp Phần mềm & thuế suất **0% GTGT xuất khẩu phần mềm**.
2. **Chuỗi Cung ứng Nội dung Kiểm chứng 100% bằng `Claim Atom` (`al2c.claim.atom` $\to$ `al2c.marketing.kit`)**:
   - Nghiêm cấm AI tự suy diễn thông số kỹ thuật, giá bán hoặc cam kết SLA chưa được kiểm chứng.
   - Mọi học liệu Marketing (`One-Pager`, `Competitive Battlecard`, `Social Thought-Leadership`, `4-Touch ABM Email`) bắt buộc liên kết với các `al2c.claim.atom` ở trạng thái `verified` kèm mã băm `SHA-256`.
   - Các Battlecard chiến lược được tự động đồng bộ vào kho chỉ mục **`al2c.rag.chunk`** (`dgm_rbac_profile='crm_sales'`, `dgm_confidentiality_level='C1_INTERNAL'`) để đội ngũ Sales & Ban Giám đốc tra cứu tức thì qua **SOP-RAG Copilot (`SOP-DGM-12`)**.
3. **Vận hành Phễu 4-Touch ABM & GEO Tự hành 24/7 (`dgm.marketing.automation.campaign` — `AUT-CMP-01..06`)**:
   - Hệ thống tự động chạy ngầm định kỳ mỗi **6 giờ** qua daemon `ir_cron_dgm_autonomous_marketing_research` (`cron_dgm_autonomous_marketing_and_research()`), tôn trọng công tắc an toàn kép `al2c.autonomy_enabled` và `dgm.autonomy_enabled`.
   - Tự động phân luồng cơ hội B2B (`crm.lead`), nuôi dưỡng theo kịch bản **4 điểm chạm (`Day 1` $\to$ `Day 4` $\to$ `Day 8` $\to$ `Day 14`)**, đo lường tỷ lệ chuyển đổi `MQL` $\to$ `SQL`, giá trị Pipeline (`VNĐ`) và hệ số hoàn vốn **`ROI Multiple (x)`**.

---

## 2. Ma Trận 6 Hồ Sơ Nghiên Cứu Thị Trường & Battlecard (`MKT-RES-01` .. `MKT-RES-06`)

| Mã Radar | Trụ cột Dịch vụ | Phân khúc ICP Mục tiêu | TAM / SAM / SOM (Tỷ VNĐ) | CAGR | Đối thủ Chính | Tỷ lệ Thắng (`Win-Rate`) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`MKT-RES-01`** | `sw_squad` — Dedicated Agile Squad & Staff Augmentation | Khối Ngân hàng, Fintech & Trung tâm R&D FDI (Nhật/Úc/Singapore) | `18,500` / `4,200` / `185` | `21.5%` | FPT Software, NashTech, KMS, Savvycom | `46.0%` |
| **`MKT-RES-02`** | `sw_turnkey` — Turnkey Custom Software & AI Product | Doanh nghiệp Tăng trưởng & Chuyển đổi số Việt Nam & APAC | `14,200` / `3,100` / `140` | `24.0%` | CMC Global, VMO, Rikkeisoft, Boutique Studios | `44.0%` |
| **`MKT-RES-03`** | `erp` — Clean-Core Enterprise ERP, NĐ 70 & Payroll | Khối Sản xuất, Khu Công nghiệp & Chuỗi cung ứng FDI/VN | `22,000` / `5,400` / `240` | `19.8%` | SAP B1/S4, Oracle NetSuite, Base.vn, MISA AMIS | `48.0%` |
| **`MKT-RES-04`** | `grc` — GRC, ISO 27001/27701, PDPD NĐ 13 & HSE | Khối Tuân thủ ISO 27001/27701, Dữ liệu Cá nhân & Hóa chất | `6,800` / `1,850` / `95` | `28.5%` | Big4 Consulting, OneTrust, Vanta, Local ISO Consultants | `52.0%` |
| **`MKT-RES-05`** | `ai` — Sovereign AI Concierge, SOP-RAG & IDP | Khối Tự động hóa Tri thức AI & Logistics IDP | `9,600` / `2,600` / `135` | `34.0%` | Microsoft Copilot Studio, FPT.AI, Kore.ai, Wrapper Chatbots | `49.0%` |
| **`MKT-RES-06`** | `zencode` — ZenCode Autonomous Engineering & DevSecOps | Thị trường Xuất khẩu Phần mềm Quốc tế 0% GTGT | `16,400` / `3,900` / `165` | `29.2%` | Devin/Cursor Enterprise, Offshore DevOps Agencies | `45.0%` |

---

## 3. Ma Trận 6 Chiến Dịch Marketing Tự Hành 24/7 (`AUT-CMP-01` .. `AUT-CMP-06`)

1. **`AUT-CMP-01` — Chiến dịch ABM 4-Touch: Mở rộng Đội ngũ Kỹ sư Chuyên trách (`Dedicated Agile Squad — MTI & Global R&D Model`)**:
   - **Touch 1 (Ngày 1)**: Phân tích bài toán thiếu hụt Senior Engineers và chi phí ẩn khi tuyển dụng nội bộ tại Nhật/Úc/Singapore & TP.HCM.
   - **Touch 2 (Ngày 4)**: Giới thiệu mô hình **Dedicated Squad Chuẩn MTI Technology** (SLA 140–180 giờ/tháng, cổng kỹ năng bắt buộc `SOP-DGM-10/11`, đối soát hóa đơn nháp 2 bước `SOP-DGM-08`).
   - **Touch 3 (Ngày 8)**: Case Study thực chiến vận hành đội ngũ Senior Engineers cho **MTI Technology (`PTN-DGM-2026-0001`)** và **Canva (`PTN-DGM-2026-0003`)**.
   - **Touch 4 (Ngày 14)**: Mời trải nghiệm dự toán **ESIH Instant Estimator** trên `innoria.com` và đặt lịch phỏng vấn kỹ sư trong 48 giờ.
2. **`AUT-CMP-02` — Chiến dịch Turnkey Software & AI Product (`360-Sales & Custom Platform — AIfin Model`)**.
3. **`AUT-CMP-03` — Chiến dịch Clean-Core Enterprise ERP, Hóa đơn Điện tử NĐ 70 (`1C26TAA`) & Bảng lương VCB DigiBiz**.
4. **`AUT-CMP-04` — Chiến dịch Tuân thủ GRC, Bảo vệ Dữ liệu Cá nhân NĐ 13/2023 (`ISO 27701`) & An toàn Hóa chất**.
5. **`AUT-CMP-05` — Chiến dịch Sovereign AI Concierge, Grounded SOP-RAG (`Entailment >= 0.85`) & Intelligent Document Processing**.
6. **`AUT-CMP-06` — Chiến dịch Xuất khẩu Phần mềm 0% GTGT & ZenCode Autonomous DevSecOps (`APAC / US / EU`)**.

---

## 4. Tích Hợp Trên Employee Self-Service Hub (`HomeMenu` — Tab 6 `kpi_skills` Section 6)

Trên giao diện **Employee Self-Service Hub** (`enterprise/web_enterprise/static/src/webclient/home_menu/`), mục **Section 6: Tự Động Hóa Marketing & Nghiên Cứu Thị Trường B2B (`SOP-DGM-13`)** hiển thị trực quan:
- **4 Thẻ Chỉ số Điều hành (`Executive Marketing KPIs`)**:
  1. Tổng quy mô thị trường mục tiêu (**TAM / SAM / SOM** của 6 trụ cột).
  2. Số chiến dịch tự hành đang chạy **24/7 (`Autonomous ON`)** & tỷ lệ kiểm chứng **100% Claim Atom**.
  3. Tổng số **MQL $\to$ SQL** thu hút và tỷ lệ chuyển đổi trung bình.
  4. Tổng giá trị **Pipeline B2B (`VNĐ`)** và hệ số hoàn vốn **`ROI Multiple (x)`**.
- **Nút Hành động 1-Click**: `"⚡ Chạy Quét Thị Trường & Nuôi Dưỡng Lead Tự Hành (Autonomous Scan)"` gọi trực tiếp endpoint `/insilos/employee_dashboard/run_autonomous_marketing_scan` (`readonly=False`), kích hoạt `cron_dgm_autonomous_marketing_and_research()` và cập nhật tức thì bảng Radar & Chiến dịch.
