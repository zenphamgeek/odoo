# SOP-DGM-12: Quy trình Quản trị Tri thức (`knowledge.article`), Kiến trúc Chat Box & Chatbot AI Đa Kênh, và Hệ thống Grounded SOP-RAG (`Innoria.com` & Digimate JSC — MST: `0317958465`)

> **Mã hiệu Tài liệu:** `SOP-DGM-12` • **Phiên bản:** `2026.10-v1.0`  
> **Đơn vị ban hành:** CÔNG TY CỔ PHẦN DIGIMATE (`INNORIA` — MST: `0317958465` / `0318201249`, BHXH Quận 7: `TZ0857G`)  
> **Phạm vi áp dụng:** Toàn bộ hệ thống Quản trị Tri thức (`knowledge.article`), Kho Lưu trữ Tài liệu Số (`documents.document`), Kênh Chat Box AI Công khai (`Innoria.com`), và Trợ lý AI Nội bộ (`Internal SOP-RAG Copilot` trên `HomeMenu` Employee Dashboard).

---

## 1. Kiến trúc Đa Kênh: Sự khác biệt giữa Chat Box AI Công khai & Chatbot AI Nội bộ

| Tiêu chí | 1. Public Website AI Chat Box (`public_website_concierge`) | 2. Internal Employee SOP-RAG Copilot (`internal_sop_copilot`) | 3. B2B Customer Portal Assistant (`portal_customer_assistant`) |
| :--- | :--- | :--- | :--- |
| **Giao diện & Điểm chạm** | Floating Chat Box góc phải dưới trên `innoria.com` (`ai_concierge_widget.js`) | Thẻ tương tác trực tiếp tại Tab 6 (`KPI, OKRs, 360° Appraisal & Kỹ năng SWE`) trên `HomeMenu` | Cổng Nghiệm thu Timesheet & Đối soát Hóa đơn Nháp MTI/AIFin (`/insilos/timesheet_approval/...`) |
| **Chế độ Xác thực (`auth`)** | `auth='public'` (Khách truy cập ẩn danh / B2B Prospect) | `auth='user'` (Nhân sự nội bộ Digimate `DGM-001..DGM-009`) | `auth='public'` kèm Token `hmac.compare_digest` |
| **Phạm vi RBAC (`authorized_rbac_profiles`)** | Chỉ duy nhất `['public_brand']` (`is_public = True`, `dgm_confidentiality_level = 'public'`) | Động theo vai trò nhân sự: CEO/CTO (`DGM-001`, `DGM-002`) toàn bộ 11 profiles; HR (`DGM-003`) 5 profiles; Kỹ sư (`DGM-004..DGM-009`) 5 profiles kỹ thuật & SOP chung | `['public_brand', 'project_delivery']` |
| **Mục tiêu Nghiệp vụ** | Tư vấn dịch vụ Kỹ sư Phần mềm Onsite B2B, Giải pháp Insilos ERP, thu thập nhu cầu và tự động khởi tạo `crm.lead` | Giải đáp tức thì quy trình `SOP-DGM-01..12`, OKRs, 360° Appraisal 9-Box, Cổng Kỹ năng Bắt buộc Hạng B, BHXH `TZ0857G`, VCB DigiBiz 11 cột | Hỗ trợ đối tác kiểm tra bảng chấm công, biên bản nghiệm thu và hóa đơn nháp trước khi xuất HĐĐT `1C26TAA` |

---

## 2. Vòng đời Quản trị Tri thức 5 Bước (`dgm.knowledge.sop.workflow`)

Mọi quy trình vận hành chuẩn (`SOP-DGM-01..12`) và danh mục thương mại (`CAT-B2B-01..06`) trước khi được phép đưa vào bộ nhớ truy xuất của AI phải đi qua 5 cổng kiểm soát:

1. **`draft` (Bản thảo — Authoring)**: Biên soạn trên `knowledge.article` và `documents.document` với chuẩn định dạng biểu mẫu thương hiệu Google Drive Logo Digimate.
2. **`tech_review` (Thẩm định Kỹ thuật — CTO Review)**: Rà soát tính chính xác nghiệp vụ, công thức tính toán và cấu trúc dữ liệu bởi CTO (`Phạm Bảo Chinh` — `DGM-002`).
3. **`compliance_approved` (Phê duyệt Pháp chế & Bảo mật — CEO Sign-off)**: Gán nhãn phân quyền `rbac_profile`, cấp độ bảo mật `confidentiality_level` (`public`, `internal`, `confidential`, `strictly_restricted`), và kênh hiển thị `visibility_channel` bởi CEO (`Mai Ngọc Thắm` — `DGM-001`).
4. **`indexed_rag` (Vector hóa & Lập chỉ mục SOP-RAG)**: Tự động chia đoạn ngữ nghĩa (`semantic_chunk_document`), tạo vector nhúng 64 chiều, tính mã băm toàn vẹn `SHA-256` (`content_sha256`), và lưu vào `al2c.rag.chunk`.
5. **`superseded` (Thay thế / Lưu trữ)**: Thu hồi tự động các phân đoạn RAG cũ khi ban hành phiên bản SOP mới.

---

## 3. Cơ chế Truy xuất Lai (Hybrid RRF `k=60`) & 4 Lớp Phòng vệ Chống Ảo giác (`al2c.rag.service`)

```
[Truy vấn Người dùng]
       │
       ▼
[Lớp 1: Adversarial & Prompt Injection Guard] ──(Vi phạm)──► Chặn & Khóa phiên (`quarantined_security`)
       │
       ▼
[Lớp 2: RBAC Pre-Filter + Hybrid RRF (k=60)]  ──► Kết hợp Dense Vector Cosine + Sparse BM25 trên tập Chunk hợp lệ
       │
       ▼
[Lớp 3: Grounded Synthesis & Entailment Gate] ──► Kiểm chứng `entailment_score >= 0.85` + Trích dẫn `[Doc | Section | ID | SHA256_8]`
       │
       ▼
[Lớp 4: ISO/IEC 27701 & NĐ 13/2023 PII Scrubber] ──► Che dấu SĐT (`090*****01`), CCCD (`089******917`), API Keys (`[REDACTED_SECRET]`)
```
