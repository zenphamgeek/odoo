# SOP-DGM-10: Quy trình Đánh giá KPI Nhân sự, Nghiệm thu Công việc & Cổng Nâng cấp Kỹ năng Kỹ sư Phần mềm Bắt buộc
## (Employee KPI Evaluation, Work Performance Appraisal & Mandatory Software Engineer Skill Upgrade Gate)

- **Mã Quy trình (Document ID):** `SOP-DGM-10`
- **Phiên bản (Version):** `2026.1`
- **Pháp nhân Áp dụng (Legal Entity):** CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ (DIGIMATE JSC — MST: `0317958465` • Mã ĐV BHXH: `TZ0857G`)
- **Nền tảng Thực thi (Platform):** Insilos Enterprise Odoo 20 (`addons/insilos_al2c` & `enterprise/web_enterprise` Employee Self-Service Hub)
- **Tiêu chuẩn Tuân thủ (Compliance):** ISO/IEC 27001:2022, ISO/IEC 27701:2019, Nghị định 13/2023/NĐ-CP, Bộ luật Lao động 2019

---

## 1. Mục đích & Nguyên tắc Quản trị (Executive Summary & Governance Principles)

Quy trình **SOP-DGM-10** thiết lập khung đánh giá hiệu suất công việc định kỳ (**4-Pillar Weighted KPI Appraisal**) kết hợp chặt chẽ với **Cổng Nâng cấp Kỹ năng Kỹ sư Phần mềm Bắt buộc (Mandatory Software Engineer Skill Upgrade Gate)** dành cho toàn bộ đội ngũ Kỹ sư Phần mềm, Chuyên gia AI và Nhân sự vận hành tại **Digimate JSC**.

### Nguyên tắc cốt lõi (Core Invariants)
1. **Không ngừng nâng cấp năng lực kỹ thuật (Continuous Engineering Mastery):** Mọi kỹ sư phần mềm từ cấp độ Junior (`L1`) đến Principal/CTO (`L5`) đều phải hoàn thành và vượt qua bài kiểm định thực chiến của các chuyên đề kỹ năng bắt buộc trong kỳ (`dgm.hr.skill.track` & `dgm.hr.employee.skill.gate`).
2. **Chốt chặn Cổng Kỹ năng Bắt buộc (`Mandatory Skill Upgrade Gate Cap`):** Nhân sự có điểm giao phẩm dự án cao nhưng **chưa hoàn thành 100% học phần nâng cấp kỹ năng bắt buộc** (`all_mandatory_skills_completed == False`) sẽ bị **khóa trần điểm KPI chính thức ở mức `84.9đ` (`skill_gate_capped = True`)**, xếp hạng tối đa **Hạng B (`tier_b`)**, hệ số thưởng chuẩn `100%` và chưa đủ điều kiện xét thăng cấp (`promotion_eligible = False`).
3. **Mở khóa Tức thì theo Thời gian Thực (`Real-Time Reactive Unlock`):** Ngay khi kỹ sư nộp minh chứng thực chiến (`PR / Commit / Lab Verification`) và được CTO / Tech Lead nghiệm thu đạt chuẩn (`action_certify_skill_upgrade`), hệ thống tự động tính toán lại điểm KPI cuối kỳ, gỡ bỏ khóa trần và nâng hạng lên **Hạng A (`120%` thưởng)** hoặc **Hạng S (`150%` thưởng & xét thăng cấp)**.

---

## 2. Khung Cấp bậc Kỹ sư Phần mềm 5 Tầng (5-Level Software Engineer Competency Ladder)

| Mã Cấp bậc (`engineer_level`) | Chức danh Chuẩn (Bilingual Title) | Yêu cầu Năng lực Cốt lõi & Phạm vi Trách nhiệm |
| :--- | :--- | :--- |
| **`l1_junior`** | **L1 — Kỹ sư Phần mềm Sơ cấp** *(Junior Software Engineer)* | Nắm vững chuẩn OWL 2/3 cơ bản, tuân thủ tuyệt đối Anti-Slop SCSS (không dùng mã hex cứng), bảo mật PII theo Nghị định 13/2023/NĐ-CP và viết kịch bản kiểm thử Playwright E2E. |
| **`l2_mid`** | **L2 — Kỹ sư Phần mềm Độc lập** *(Mid-Level Software Engineer)* | Phát triển độc lập các phân hệ Odoo 20 / Insilos, triển khai giao diện Dual-Theme Light/Dark chuẩn xác, tham gia dự án B2B Onsite (MTI, AIfin) đạt định mức 140–180h/tháng. |
| **`l3_senior`** | **L3 — Kỹ sư Phần mềm Cao cấp / Onsite B2B** *(Senior Software Engineer)* | Làm chủ kiến trúc OWL 3 Reactive Signal, tối ưu PostgreSQL Concurrency (`pg_advisory_xact_lock`, Compatibility Views), tích hợp Grounded RAG và dẫn dắt giao phẩm B2B. |
| **`l4_lead`** | **L4 — Kỹ sư Trưởng / Kiến trúc sư** *(Staff / Tech Lead)* | Thiết kế kiến trúc hệ thống đa tầng, tối ưu Mojo AI / SIMD, kiểm duyệt Code Review, chịu trách nhiệm Zero-Regression và hướng dẫn nâng cấp kỹ năng cho đội ngũ L1–L3. |
| **`l5_principal`** | **L5 — Kiến trúc sư Trưởng / CTO** *(Principal / Executive Tech)* | Định hình chiến lược công nghệ Sovereign Enterprise ERP & AI Agentic Fleet, phê duyệt chuẩn kiến trúc toàn công ty và nghiệm thu cổng kỹ năng cấp cao. |

---

## 3. Danh mục 8 Chuyên đề Nâng cấp Kỹ năng Bắt buộc (`dgm.hr.skill.track`)

| STT | Mã Kỹ năng (`code`) | Tên Chuyên đề Nâng cấp Kỹ năng | Nhóm (`category`) | Giờ Chuẩn | Điểm Đạt | Lệnh Kiểm định Thực chiến (`verification_cmd`) |
| :-: | :--- | :--- | :--- | :-: | :-: | :--- |
| 1 | `SKL-ERP-OWL3` | Kiến trúc Component OWL 2/3 Reactive Props, Signal & Sovereign View Hooks | `erp_owl` | 24h | 85/100 | `python3 tools/audit_systemic_refactor_risks.py --strict` |
| 2 | `SKL-ERP-SCSS-DARK` | Kiến trúc Sovereign Dark Mode Token, Dual-Asset Bundle & Anti-Slop SCSS | `erp_owl` | 20h | 85/100 | `python3 tools/unslop_scss_rigorous.py && node tools/test_theme_switch_dark_to_light.js` |
| 3 | `SKL-AI-MOJO` | Kỹ thuật Hệ thống Mojo AI, High-Throughput Inference & Token Budget Optimization | `ai_mojo` | 32h | 88/100 | `python3 tools/test_adversarial_security.py` |
| 4 | `SKL-AI-RAG` | Grounded Sovereign RAG, Citation Contract & Zero-Hallucination Entailment Gate | `ai_mojo` | 24h | 85/100 | `python3 tools/test_adversarial_security.py` |
| 5 | `SKL-K8S-PG` | Kiến trúc PostgreSQL Concurrency, Compatibility Views & Kubernetes Zero-Downtime | `cloud_db` | 28h | 85/100 | `python3 tools/audit_systemic_refactor_risks.py --strict` |
| 6 | `SKL-SEC-ISO27001` | Bảo mật An toàn Thông tin ISO/IEC 27001:2022, ISO/IEC 27701 & Nghị định 13/2023/NĐ-CP | `sec_privacy` | 16h | 90/100 | `python3 tools/test_dgm_hr_payroll_dashboard.py` |
| 7 | `SKL-B2B-ACTIVATE` | Quy trình Triển khai B2B Staff Augmentation (SOP-DGM-06/07/08) & SAP Activate 5 Phases | `b2b_delivery` | 20h | 85/100 | `python3 tools/test_dgm_partner_onboarding.py` |
| 8 | `SKL-QA-PLAYWRIGHT` | Kiểm thử Tự động Đa tầng, Adversarial Security & Headless Playwright E2E Dual-Theme | `qa_e2e` | 24h | 85/100 | `python3 tools/test_adversarial_security.py` |

---

## 4. Công thức Chấm điểm KPI 4 Trụ cột (`dgm.hr.kpi.evaluation`)

Điểm KPI trọng số gốc (`raw_weighted_score`) được tổng hợp tự động từ 4 trụ cột:

1. **Trụ cột 1 — Giao phẩm & Tiến độ Dự án (`score_delivery` — Trọng số `35%`):**
   $$\text{hours\_ratio} = \min\left(105.0,\ \frac{\text{kpi\_billable\_hours\_actual}}{\text{kpi\_billable\_hours\_target}} \times 100.0\right)$$
   $$\text{score\_delivery} = \min\left(100.0,\ 0.6 \times \text{kpi\_sprint\_completion\_pct} + 0.4 \times \text{hours\_ratio}\right)$$

2. **Trụ cột 2 — Chất lượng Code & Kiến trúc (`score_quality` — Trọng số `25%`):**
   $$\text{score\_quality} = \max\left(0.0,\ \min\left(100.0,\ 0.5 \times \text{kpi\_code\_review\_pass\_rate} + 0.5 \times \text{kpi\_zero\_regression\_score} - 8.0 \times \text{kpi\_production\_defect\_count}\right)\right)$$

3. **Trụ cột 3 — Nghiệm thu Công việc B2B & Tuân thủ SOP (`score_work_eval` — Trọng số `20%`):**
   $$\text{score\_work\_eval} = \min\left(100.0,\ 0.6 \times \text{kpi\_client\_csat\_score} + 0.4 \times \text{kpi\_sop\_compliance\_score}\right)$$

4. **Trụ cột 4 — Cổng Nâng cấp Kỹ năng Kỹ sư Bắt buộc (`score_skill_upgrade` — Trọng số `20%`):**
   - Mỗi học phần bắt buộc (`is_mandatory = True`) đóng góp `assessment_score` nếu đã `certified`, hoặc `0.8 * progress_pct` nếu chưa `certified`.

### Tổng hợp Điểm Trọng số & Quy tắc Khóa Trần (`Skill Gate Cap`)
$$\text{raw\_weighted\_score} = 0.35 \times \text{score\_delivery} + 0.25 \times \text{score\_quality} + 0.20 \times \text{score\_work\_eval} + 0.20 \times \text{score\_skill\_upgrade}$$

- **Trường hợp 1 (`all_mandatory_skills_completed == True`):**
  - `skill_gate_capped = False`
  - `final_kpi_score = raw_weighted_score`
  - **Hạng S (`tier_s`):** `final_kpi_score >= 92.0` $\rightarrow$ Thưởng `150%`, `promotion_eligible = True`
  - **Hạng A (`tier_a`):** `85.0 <= final_kpi_score < 92.0` $\rightarrow$ Thưởng `120%`, `promotion_eligible = True`
  - **Hạng B (`tier_b`):** `75.0 <= final_kpi_score < 85.0` $\rightarrow$ Thưởng `100%`, `promotion_eligible = False`
- **Trường hợp 2 (`all_mandatory_skills_completed == False`):**
  - `skill_gate_capped = (raw_weighted_score >= 85.0)`
  - `final_kpi_score = min(raw_weighted_score, 84.9)`
  - Xếp hạng tối đa **Hạng B (`tier_b`)**, hệ số thưởng tối đa `100%`, `promotion_eligible = False`.

---

## 5. Bảng Phân bổ Đánh giá KPI & Cổng Kỹ năng Kỳ `2026-Q4` (`DGM-001`..`DGM-009`)

| Mã NV | Họ và Tên | Cấp bậc | Dự án Trọng tâm `2026-Q4` | Kỹ năng Bắt buộc | Trạng thái Gate | Hạng KPI |
| :---: | :--- | :---: | :--- | :---: | :---: | :---: |
| `DGM-001` | Lê Xuân Hoàng | `l5_principal` | Insilos Sovereign ERP & AL2C Executive Architecture | 3/3 Certified | Passed | **Hạng S (`tier_s`)** |
| `DGM-002` | Nguyễn Hoài Ân | `l5_principal` | Mojo AI Engine, Sovereign RAG & K8s Production Cluster | 4/4 Certified | Passed | **Hạng S (`tier_s`)** |
| `DGM-003` | Mai Thị Hồng Thắm | `l4_lead` | Statutory VN 2026 Payroll (VCB DigiBiz) & Decree 70 E-Invoicing | 3/3 Certified | Passed | **Hạng S (`tier_s`)** |
| `DGM-004` | Bùi Hữu Tài | `l3_senior` | MTI Technology Dedicated ODC (`DIGIMATE2401-001`) | 4/4 Certified | Passed | **Hạng S (`tier_s`)** |
| `DGM-005` | Huỳnh Trần Quang Khánh | `l4_lead` | Insilos Core WebClient, OWL 3 Runtime & Dual-Theme | 4/4 Certified | Passed | **Hạng S (`tier_s`)** |
| `DGM-006` | Ngô Thanh Lộc | `l3_senior` | MTI Technology Dedicated ODC (`DIGIMATE2401-001`) | 3/3 Certified | Passed | **Hạng A (`tier_a`)** |
| `DGM-007` | Lê Cao Bảo Phúc | `l2_mid` | MTI Technology Onsite Delivery & Portal Integration | 2/3 (`SKL-ERP-OWL3` In Progress) | **Capped at 84.9** | **Hạng B (`tier_b`)** |
| `DGM-008` | Thái Nguyễn Đăng Khoa | `l1_junior` | Insilos UI Components & Automated E2E Suite | 2/3 (`SKL-QA-PLAYWRIGHT` In Progress) | **Capped at 84.9** | **Hạng B (`tier_b`)** |
| `DGM-009` | Trần Văn Huỳnh Phố | `l3_senior` | AIfin Company Global Staff Augmentation (`DIGIMATE-AIFIN-VN_2610-001`) | 4/4 Certified | Passed | **Hạng S (`tier_s`)** |

---

## 6. Cổng Kiểm định Tự động (Automated Verification Gates)

```bash
python3 tools/seed_dgm_kpi_skill_framework.py
python3 tools/test_dgm_kpi_skill_framework.py
python3 tools/audit_systemic_refactor_risks.py --strict
```
