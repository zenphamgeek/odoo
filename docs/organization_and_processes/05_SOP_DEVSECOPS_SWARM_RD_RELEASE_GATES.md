# Standard Operating Procedure (SOP): DevSecOps, Swarm Engineering & Release Gates
## Quy Trình Kỹ Nghệ Phần Mềm, Vibe Coding Song Song & 13 Cổng Kiểm Định Chất Lượng Hội Đồng

> **SOP Code:** SOP-ENG-001 • **Version:** 2.0 (Master Release Standard)  
> **Key Frameworks:** Dual-Track Agile • AGY Fleet Multi-Account Swarm • Hard Fork Council Matrix  
> **Core Tooling:** `run_hard_fork_council_gates.py` • `run_hoot.js` • `sweep_ui_all_apps.js`  

---

## 1. Mô Hình Kỹ Nghệ Hai Tuyến (Dual-Track Agile Engineering)

Để vừa duy trì tốc độ phát triển sản phẩm lõi vừa đáp ứng kịp thời các dự án khách hàng, đội ngũ Kỹ nghệ & R&D áp dụng mô hình Hai Tuyến Độc Lập:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              DUAL-TRACK AGILE ARCHITECTURE                             │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 1. TUYẾN SẢN PHẨM LÕI (UPSTREAM DISCOVERY & CORE PLATFORMS)                            │
│    • Nghiên cứu kiến trúc Odoo 20 LTS Clean-Core, Flutter Mobile & GRC                  │
│    • Phát triển các gói module chuẩn (SKUs): ERP, Risk Registry, Mojo AI               │
│    • Chạy liên tục kiểm định bảo mật đối kháng (34 Adversarial Security Findings)      │
│    • Đóng gói bản phát hành ổn định (Quarterly Sovereign Release)                      │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                      ▲                                                 │
│                        Đóng góp module / Trích xuất Best Practices                     │
│                                      ▼                                                 │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 2. TUYẾN DỰ ÁN KHÁCH HÀNG (DOWNSTREAM CLIENT IMPLEMENTATION)                           │
│    • Khởi tạo dự án từ nhánh sản phẩm lõi mới nhất (Fork & Rebase)                      │
│    • Triển khai theo 5 pha SAP Activate (Prepare ➔ Explore ➔ Realize ➔ Deploy ➔ Run)    │
│    • Tùy biến phân hệ riêng biệt (Delta Modules), không can thiệp lõi                  │
│    • Mọi tính năng tổng quát hóa được kiểm định chuyển ngược lại sản phẩm lõi         │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Kỹ Nghệ Swarm & Vibe Coding Song Song (AGY Fleet Swarm Engine)

Tận dụng cụm **AGY Fleet 23 Nodes** đa tài khoản, đội ngũ áp dụng quy trình **Vibe Coding Song Song (Parallel Vibe Coding)** theo chu trình PDCA tốc độ cao nhưng tuyệt đối không đánh đổi chất lượng:

```
                          ┌───────────────────────────────┐
                          │   Antigravity Main Session    │
                          │   (Thin Coordinator Agent)    │
                          └───────────────┬───────────────┘
                                          │
                  ┌───────────────────────┴───────────────────────┐
                  │ 1. Phân rã bài toán & Dispatch Task           │
                  ▼                                               ▼
      ┌───────────────────────┐                       ┌───────────────────────┐
      │   Claude Opus 5.5     │                       │  Gemini 3.8 Flash High│
      │  (Hoạch Định & Phản Biện)                     │  (Lập Trình Song Song)│
      └───────────┬───────────┘                       └───────────┬───────────┘
                  │                                               │
                  │ 2. Trả về mã nguồn & diff cấu trúc           │
                  └───────────────────────┬───────────────────────┘
                                          │
                                          ▼
                          ┌───────────────────────────────┐
                          │   Áp dụng cục bộ & Kiểm thử   │
                          │   (Local Validation Gates)    │
                          └───────────────┬───────────────┘
                                          │
                                          ▼
                          ┌───────────────────────────────┐
                          │  13 Cổng Kiểm Định Hội Đồng   │
                          │  (Hard Fork Council Gates)    │
                          └───────────────────────────────┘
```

### Các Nguyên Tắc Bắt Buộc Của Điều Phối Viên Tinh Gọn (Thin-Coordinator Mandate):
1. **Không tạo khối mã lớn (>20 dòng) trực tiếp trong cửa sổ chat đơn lẻ** khi cụm Fleet đang sẵn sàng; phải ủy thác cho các worker node.
2. **Kỹ nghệ tái cấu trúc Biện chứng Hegelian (Hegelian Dialectic Refactoring):**
   - *Chính đề (Thesis):* Yêu cầu chức năng ban đầu hoặc đoạn mã kế thừa.
   - *Phản đề (Antithesis):* Đội ngũ Red-Team hoặc node Opus đóng vai trò kẻ tấn công, tìm kiếm lỗ hổng rò rỉ bộ nhớ, race condition, rò rỉ PII, vi phạm bảo mật CWE.
   - *Hợp đề (Synthesis):* Tạo ra phiên bản mã nguồn mới loại bỏ triệt để điểm yếu của cả hai phía.
3. **Nguyên tắc Không Kiểm Thử Giả Mạo (Zero-Fake-Pass Invariant):**
   - Mọi xác nhận hoàn thành công việc đều phải được kiểm chứng bằng lệnh chạy thực tế trên máy trạm với mã thoát (Exit Code) bằng 0. Nghiêm cấm hoàn toàn mock rỗng hoặc kiểm thử hình thức.

---

## 3. Ma Trận 13 Cổng Kiểm Định Bản Phát Hành Của Hội Đồng (13 Hard Fork Council Gates)

Trước khi bất kỳ nhánh mã nguồn nào được hợp nhất vào nhánh phát hành chính thức (`insilos-genesis-fork` hoặc nhánh dự án khách hàng), toàn bộ **13 Cổng Kiểm Định** sau đây phải chạy qua tự động và đạt 100% xanh (Exit 0):

```
================================================================================
               13-GATE RELEASE VERIFICATION SUMMARY MATRIX
================================================================================
Gate   | Verification Domain                          | Target Script / Command
--------------------------------------------------------------------------------
Gate 1 | Python AST Syntax & Compilation Audit        | tools/verify_gates_1_2.py --gate 1
Gate 2 | XML & QWeb Well-formedness Audit             | tools/verify_gates_1_2.py --gate 2
Gate 3 | Server Boot & Preload Integrity              | odoo-bin -c insilos.conf --stop-after-init
Gate 4 | PEP 451 Import Hook Interoperability         | tools/test_insilos_import_hook.py
Gate 5 | Perimeter Security Gateway API Contract      | tools/test_gateway_security.py
Gate 6 | App Icons & Branding Asset Integrity         | tools/check_app_icons_integrity.py
Gate 7 | Counter Code Security Invariance             | scripts/counter_code_scanner.py
Gate 8 | Ported Enterprise Modules E2E Lifecycle      | tools/test_enterprise_ported_modules_e2e.js
Gate 9 | Full 72-App Parallel Playwright Verification | test_all_home_apps_parallel.js
Gate 10| UI Brand & Lexicon Leak Sweep Core Apps      | tools/sweep_ui_all_apps.js
Gate 11| Modern OWL 2 HOOT Test Suite Verification    | node run_hoot.js --concurrency=4
Gate 12| Sovereign Navigation & Header Collision Inva | tools/audit_header_menu_collision.py
Gate 13| QWeb / Owl Template Null-Safety Invariant    | tools/lint_qweb_find_optional_chaining.py
================================================================================
```

### Chi Tiết Kỹ Thuật Các Cổng Trọng Yếu:
- **Gate 1 & 2 (AST & XML Well-Formedness):** Dùng `py_compile` và `lxml.etree` quét toàn bộ kho mã nguồn; bất kỳ lỗi cú pháp, thụt đầu dòng hay thẻ đóng mở XML sai đều bị chặn đứng ngay lập tức.
- **Gate 6 (Icon Duotone Standard):** Đảm bảo 62+ biểu tượng ứng dụng launcher tuân thủ định dạng vector Phosphor Duotone với mã màu tech-cyan chuẩn, không dùng icon mờ hay icon kế thừa.
- **Gate 7 (Counter Code Scanner):** Quét toàn bộ mã nguồn với ngưỡng phát hiện bằng 0 (`max-allowed-detections 0`) đối với các chuỗi ký danh nguồn gốc cũ (`Odoo`, `OpenERP`, URL cộng đồng).
- **Gate 10 (UI Brand & Lexicon Sweep):** Playwright không đầu thu thập toàn bộ văn bản hiển thị trên trình duyệt của 5 route công khai và 28 ứng dụng xác thực, đảm bảo không rò rỉ PII và văn bản kế thừa. Áp dụng cơ chế lọc `safeRedact` và tự kiểm tra `assertRedactionWorks`.
- **Gate 11 (OWL 2 HOOT Test Suite):** Chạy kiểm thử đơn vị frontend OWL 2 phản ứng song song 4 luồng trình duyệt với cơ chế cách ly bí mật (`redactSensitive`) chống rò rỉ mật khẩu vào log CI.
- **Gate 12 (Navigation & Header Collision Guard):** Kiểm định cấu trúc cây menu đa website; nghiêm cấm nhân bản trùng lặp các route điều hướng và ép buộc cờ `noupdate="1"`.
- **Gate 13 (QWeb/Owl Null-Safety Guard):** Quét cú pháp các biểu thức `Array.find()` trong template QWeb, ép buộc sử dụng toán tử an toàn optional chaining `?.` để ngăn chặn lỗi màn hình trắng (White Screen of Death).

---

## 4. Chính Sách Cách Ly Dữ Liệu Chủ Quyền & Bảo Vệ Database Sản Xuất

> [!CAUTION]
> **QUY TẮC BẤT BIẾN: CẤM TUYỆT ĐỐI CAN THIỆP CƠ SỞ DỮ LIỆU SẢN XUẤT TRONG KIỂM THỬ**

1. **Phân Vùng Môi Trường Rõ Ràng:**
   - Mọi hoạt động lập trình, chạy kiểm thử tự động, thử nghiệm kịch bản rủi ro **CHỈ ĐƯỢC PHÉP TRUY CẬP CƠ SỞ DỮ LIỆU PHÁT TRIỂN CỤC BỘ**:
     $$\text{Host: } 127.0.0.1:5434 \quad | \quad \text{Database: } insilos20\_dev \quad | \quad \text{User: } odoo$$
   - **Tuyệt đối cấm kết nối, viết truy vấn INSERT/UPDATE/DELETE hoặc thực hiện lệnh DDL** lên các cơ sở dữ liệu sản xuất (`innoria_prod`, `innokafe_prod`).
2. **Kỷ Luật Commit Git Trọng Tâm (Zero Untargeted Staging):**
   - Nghiêm cấm sử dụng lệnh `git add -A` hoặc `git add .` bừa bãi.
   - Chỉ stage những tập tin đã được kiểm định đích danh (`git add path/to/file`).
   - Mọi commit phải vượt qua hook `.git/hooks/pre-commit` (44 bài kiểm tra unslop + xác thực khóa HMAC bí mật).
