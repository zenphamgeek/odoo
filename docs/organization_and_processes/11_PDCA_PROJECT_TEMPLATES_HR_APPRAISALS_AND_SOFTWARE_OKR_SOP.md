# SOP-DGM-11: Quy Trình Vòng Lặp PDCA Quản Trị Dự Án Phần Mềm, Đánh Giá Nhân Sự 360° (HR Appraisals 9-Box) & Triển Khai OKRs Doanh Nghiệp Phần Mềm (2026)

- **Mã Quy trình:** `SOP-DGM-11`
- **Phiên bản:** `2026.1`
- **Pháp nhân Áp dụng:** **CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ (DIGIMATE JSC)** — MST: `0317958465` • Mã đơn vị BHXH: `TZ0857G` & Khối Công nghệ **INNORIA / INSILOS**
- **Hệ thống Thực thi:** Insilos Enterprise Odoo 20 (`dgm.okr.objective`, `dgm.okr.key.result`, `dgm.hr.appraisal.sheet`, `dgm.project.pdca.template`)
- **Liên kết Quy trình:** `SOP-DGM-06` (Onboarding Đối tác), `SOP-DGM-07` (Phái cử Kỹ sư B2B), `SOP-DGM-08` (Timesheet & Hóa đơn MTI/AIfin), `SOP-DGM-10` (Đánh giá KPI 4 Trụ cột & Cổng Kỹ năng Kỹ sư Phần mềm Bắt buộc).

---

## 1. Mục Đích & Triết Lý Quản Trị Khép Kín (Closed-Loop PDCA Software Governance)

Trong doanh nghiệp phần mềm hiện đại (kết hợp giữa **Phát triển Sản phẩm Lõi AI/ERP — Product R&D**, **Triển khai Dự án Trọn gói — Turnkey SAP Activate**, và **Phái cử Kỹ sư Phần mềm B2B Onsite — Dedicated ODC/Staff Augmentation**), sự tách rời giữa mục tiêu chiến lược công ty, tiến độ dự án và đánh giá nhân sự thường dẫn đến lệch pha nguồn lực.

Quy trình **`SOP-DGM-11`** thiết lập **Vòng lặp PDCA (Plan – Do – Check – Act)** liên kết chặt chẽ 4 trụ cột:
1. **Khung OKRs Doanh nghiệp Phần mềm 3 Cấp (`dgm.okr.objective` & `dgm.okr.key.result`):** Liên kết mục tiêu từ Cấp Công ty (Company) $\rightarrow$ Khối/Squad Kỹ thuật (Department/Squad) $\rightarrow$ Từng Kỹ sư (Individual) theo chuẩn chấm điểm `0.00 – 1.00` của Google/Intel.
2. **4 Khung Mẫu Dự án Phần mềm Chuẩn PDCA (`dgm.project.pdca.template`):** Chuẩn hóa 4 loại hình dự án phần mềm chủ lực với cổng kiểm soát chất lượng từng giai đoạn `Plan – Do – Check – Act`.
3. **Đánh giá Nhân sự Đa chiều 360° & Ma trận Nhân tài 9-Box (`dgm.hr.appraisal.sheet`):** Kết hợp điểm hoàn thành OKR (`35%`), Đánh giá chuyên môn của Tech Lead (`25%`), Phản hồi 360° từ đồng nghiệp & khách hàng B2B (`25%`), và Tự đánh giá của nhân sự (`15%`).
4. **Chốt chặn Cổng Kỹ năng Kỹ sư Phần mềm Bắt buộc (`skill_gate_passed` Cap Invariant):** Đồng bộ tuyệt đối với `SOP-DGM-10` — kỹ sư chưa hoàn thành 100% chuyên đề kỹ năng bắt buộc bị giới hạn ở ô **`9-Box [6] Emerging Potential`** và điểm Appraisal tối đa **`84.90 / 100`** cho đến khi nghiệm thu đạt chuẩn.

---

## 2. Bộ 4 Khung Mẫu Dự Án Phần Mềm Chuẩn PDCA (`dgm.project.pdca.template`)

| Mã Mẫu Dự Án | Tên Khung Mẫu Dự Án | Phương Pháp Luận (`delivery_methodology`) | Biên Lợi Nhuận Mục Tiêu | SLA Cam Kết | Bộ Biểu Mẫu Bắt Buộc |
| :--- | :--- | :--- | :---: | :---: | :--- |
| **`PRJ-TPL-PDCA-01`** | Khung Dự án Trọn gói Turnkey ERP & AI (KTT / Swarovski) | `sap_activate_pdca` (SAP Activate 5-Phase + PDCA) | `48.0%` | `99.95%` | `TPL-PRJ-01..06` |
| **`PRJ-TPL-PDCA-02`** | Khung Dự án Phái cử Kỹ sư B2B Onsite (MTI / AIfin) | `b2b_onsite_agile` (Agile Scrum + SLA 140–180h) | `42.0%` | `99.90%` | `TPL-ONB-05, TPL-PRJ-01, TPL-PRJ-05, TPL-PRJ-06` |
| **`PRJ-TPL-PDCA-03`** | Khung Dự án R&D Sản phẩm Lõi AI Agentic & Mojo Kernel | `ai_mojo_rd` (AI Benchmark & SIMD Optimization Loop) | `55.0%` | `99.99%` | `TPL-PRJ-02, TPL-PRJ-05, TPL-PRJ-06, TPL-OKR-01` |
| **`PRJ-TPL-PDCA-04`** | Khung Dự án Kiểm toán Bảo mật ISO 27001/27701 & NĐ 13 | `iso_grc_audit` (Security & Privacy Compliance PDCA) | `50.0%` | `99.99%` | `TPL-ONB-03, TPL-PRJ-05, TPL-PRJ-06, TPL-HR-07` |

Mỗi dự án khởi tạo từ khung mẫu đều tự động gắn 5 cột giai đoạn Kanban chuẩn:
1. `1. Plan & Prepare` (Khởi tạo Charter, Định nghĩa OKR dự án & Ma trận RACI)
2. `2. Explore & Architecture` (Thiết kế Kiến trúc Fit-to-Standard & Bảo mật ISO 27001)
3. `3. Do / Realize Sprint` (Thực thi Sprint 2 tuần, Code Review & Chấm công Billable)
4. `4. Check / UAT & Security Gate` (Kiểm thử Playwright Dual-Theme, Adversarial Security & Nghiệm thu UAT)
5. `5. Act / Deploy & Run SLA` (Go-Live, Đối soát Hóa đơn 1C26TAA & Họp Retrospective Cải tiến)

---

## 3. Khung OKRs Doanh Nghiệp Phần Mềm (`dgm.okr.objective` & `dgm.okr.key.result`)

### 3.1. Cấu Trúc Phân Cấp 3 Tầng (3-Tier OKR Cascade)
- **Tầng 1 — Company Strategic OKRs (`okr_tier = 'company'`):**
  - `OKR-2026-Q4-C01`: Tăng trưởng Doanh thu Dịch vụ Phần mềm B2B, Turnkey ERP & Xuất khẩu 0% VAT.
  - `OKR-2026-Q4-C02`: Xuất sắc Kỹ thuật Nền tảng Insilos Odoo 20, AI Agentic Mojo & 100% Cổng Kỹ năng SWE.
  - `OKR-2026-Q4-C03`: Tuân thủ Tuyệt đối Pháp chế Thuế, BHXH TZ0857G, ISO/IEC 27001 & Bảo vệ Dữ liệu Cá nhân ISO 27701.
- **Tầng 2 — Department / Engineering Squad OKRs (`okr_tier = 'department'`):** Phân rã mục tiêu xuống Khối Điều hành, Khối R&D AI/Mojo, Khối Core Platform OWL 3, và Khối Tài chính – Pháp chế – Nhân sự.
- **Tầng 3 — Individual Engineer OKRs (`okr_tier = 'individual'`):** Gắn trực tiếp với từng kỹ sư (`DGM-001`..`DGM-009`), liên kết trực tiếp với dự án đang phụ trách (MTI Technology, AIfin Global, KTT, Core Insilos) và chuyên đề nâng cấp kỹ năng bắt buộc (`linked_skill_track_id`).

### 3.2. Quy Tắc Chấm Điểm KR & Độ Tự Tin (`action_update_kr_checkin`)
- Tiến độ từng Key Result:
  $$\text{progress\_pct} = \text{clamp}\left(\frac{\text{current\_value} - \text{start\_value}}{\text{target\_value} - \text{start\_value}} \times 100, 0, 100\right)$$
- Điểm chuẩn Google/Intel OKR:
  $$\text{kr\_score} = \frac{\text{progress\_pct}}{100.0} \in [0.00, 1.00]$$
- Phân loại mức độ tự tin (`confidence_level`):
  - `🟢 on_track`: `okr_score >= 0.70`
  - `🟡 at_risk`: `0.40 <= okr_score < 0.70`
  - `🔴 off_track`: `okr_score < 0.40`

---

## 4. Đánh Giá Nhân Sự 360° & Ma Trận Hiệu Chuẩn Nhân Tài 9-Box (`dgm.hr.appraisal.sheet`)

### 4.1. Công Thức Tính Điểm Hiệu Chuẩn Đa Chiều (`calibrated_total_score`)
Điểm đánh giá tổng hợp 360° trước cổng kỹ năng (`raw_cal`) được tính từ 4 nguồn độc lập:
$$\text{raw\_cal} = 0.35 \times \text{okr\_achievement\_pct} + 0.25 \times \text{manager\_technical\_score} + 0.25 \times \text{peer\_client\_360\_score} + 0.15 \times \text{self\_assessment\_score}$$

### 4.2. Quy Tắc Khóa Cổng Kỹ Năng Bắt Buộc Trên Ma Trận 9-Box
- **Trường hợp 1 (`skill_gate_passed == False`):** Nhân sự còn bất kỳ chuyên đề kỹ năng bắt buộc nào chưa đạt trạng thái `'certified'`:
  - `calibrated_total_score = min(raw_cal, 84.90)`
  - `calibration_box = 'box_6_emerging'` (nếu `raw_cal >= 75.0`) hoặc `'box_2_pip'` (nếu `< 75.0`). Tuyệt đối không được xếp vào nhóm `'box_9_star'` hoặc `'box_8_high_perf'`.
- **Trường hợp 2 (`skill_gate_passed == True`):** Nhân sự đã hoàn thành 100% chuyên đề kỹ năng bắt buộc:
  - `calibrated_total_score = raw_cal`
  - `raw_cal >= 92.0` $\rightarrow$ **`box_9_star`** (*Top Talent / Future Leader — Mở khóa Thăng cấp & Thưởng 150%*).
  - `85.0 <= raw_cal < 92.0` $\rightarrow$ **`box_8_high_perf`** (*High Impact Engineer — Nòng cốt Kỹ thuật & Thưởng 120%*).
  - `75.0 <= raw_cal < 85.0` $\rightarrow$ **`box_5_core`** (*Solid Core Contributor — Đạt chuẩn Ổn định*).
  - `raw_cal < 75.0` $\rightarrow$ **`box_2_pip`** (*Action Required / PIP 30 Ngày*).

---

## 5. Danh Mục 6 Biểu Mẫu Chuẩn Ban Hành Kèm Theo (`SOP-DGM-11`)

1. **`TPL-PRJ-05_Mau_Ke_Hoach_Du_An_Phan_Mem_PDCA_SAP_Activate.html`**: Mẫu Kế hoạch Quản trị Dự án Phần mềm theo Vòng lặp PDCA & SAP Activate 5 Giai đoạn.
2. **`TPL-PRJ-06_Bien_Ban_Nghiem_Thu_Sprint_UAT_Va_Go_Live_PDCA.html`**: Mẫu Biên bản Nghiệm thu Sprint, Kiểm thử UAT, Cổng Bảo mật & Bàn giao Go-Live.
3. **`TPL-HR-07_Phieu_Danh_Gia_Nhan_Su_360_HR_Appraisal_9Box_PDCA.html`**: Mẫu Phiếu Đánh giá Nhân sự Đa chiều 360° & Hiệu chuẩn Ma trận Nhân tài 9-Box.
4. **`TPL-HR-08_Bien_Ban_Hieu_Chuan_Nang_Luc_Career_Calibration_SWE.html`**: Mẫu Biên bản Họp Hội đồng Hiệu chuẩn Năng lực & Xét Thăng cấp Kỹ sư Phần mềm (Career Calibration Committee).
5. **`TPL-OKR-01_Khung_OKRs_Doanh_Nghiep_Phan_Mem_Digimate_Innoria_2026.html`**: Khung Mục tiêu Chiến lược OKRs Doanh nghiệp Phần mềm Digimate & Innoria (Cascade 3 Cấp).
6. **`SOP-DGM-11_Quy_Trinh_PDCA_Quan_Tri_Du_An_HR_Appraisals_Va_OKRs_Phan_Mem.html`**: Văn bản Quy trình Chuẩn SOP-DGM-11 lưu trữ tại `02 · Quy Trình & Quy Định Nội Bộ` và `Knowledge Article`.
