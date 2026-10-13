# Đặc Tả Kỹ Thuật & Vận Hành Chuẩn: DMS • KMS • SOP-RAG • AI Concierge (Innoria.com)
## Hệ Thống Quản Trị Tài Liệu Số, Tri Thức Thẩm Quyền, Động Cơ RAG Triệt Tiêu Ảo Giác & Trợ Lý Số Doanh Nghiệp

> **Mã quy chuẩn:** SPEC-AI-KMS-2026-V4  
> **Căn cứ nghiệp vụ:** SOP-09 (DMS) • SOP-10 (KMS) • SOP-11 (SOP-RAG) • SOP-12 (AI Services innoria.com)  
> **Phân hệ phần mềm:** `documents` • `knowledge` • `addons/insilos_al2c`  
> **Tuân thủ pháp định:** Nghị định 13/2023/NĐ-CP (PDPD) • Tiêu chuẩn an ninh thông tin ISO/IEC 27001 • OWASP Top 10 LLM Applications

---

## 1. Hệ Thống Quản Trị Tài Liệu Số Doanh Nghiệp (Enterprise DMS Governance)

Hệ thống Quản trị Tài liệu Số (`documents.document`) là kho lưu trữ trung tâm các bằng chứng pháp lý, hợp đồng thương mại, biên bản nghiệm thu mốc và hồ sơ chứng từ của công ty phần mềm doanh nghiệp:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        VÒNG ĐỜI TÀI LIỆU SỐ DOANH NGHIỆP (DMS LIFECYCLE)              │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                        │
│   [1. DRAFT]                [2. UNDER REVIEW]           [3. APPROVED]                  │
│   Tài liệu soạn thảo   ───▶ Thẩm định pháp lý      ───▶ Đã được ký số HSM /           │
│   Chưa có giá trị pháp lý    & Trưởng CoE phê duyệt     Ký điện tử hợp pháp            │
│                                                                │                       │
│                                                                ▼                       │
│                                                         [4. LOCKED / IMMUTABLE]        │
│                                                         Khóa sửa đổi vĩnh viễn,        │
│                                                         Lưu vết SHA-256 trên sổ cái    │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### 1.1. Cấu Trúc Phân Cấp Thư Mục Tài Liệu Tiêu Chuẩn

Mọi tài liệu phát sinh trong quá trình vận hành được tự động phân loại vào 6 không gian thư mục có kiểm soát quyền truy cập chặt chẽ:
1. `01_Products_And_Catalogs`: Đặc tả kỹ thuật SKU, tài liệu kiến trúc, hướng dẫn sử dụng sản phẩm.
2. `02_Proposals_And_Quotations`: Báo giá chính thức đã duyệt Deal-Desk, hồ sơ đề xuất thầu (RFP).
3. `03_Contracts_And_Agreements`: Hợp đồng dịch vụ tư vấn (SOW), cam kết chất lượng SLA, thỏa thuận bảo mật NDA.
4. `04_Project_Deliverables`: Biên bản nghiệm thu 5 mốc SAP Activate, tài liệu thiết kế giải pháp tổng thể (BBP).
5. `05_Timesheet_Statements_And_Invoices`: Bảng kê chi tiết giờ công có chữ ký số PM, hóa đơn điện tử VAT Nghị định 70/2025.
6. `06_Compliance_And_Audits`: Bằng chứng kiểm toán ISO 27001, hồ sơ đồng ý xử lý dữ liệu cá nhân theo Nghị định 13/2023/NĐ-CP.

### 1.2. Hàng Rào Vân Tay Số SHA-256 & Bảo Mật PDPD (CWE-345 & CWE-200)

- **Vân Tay Số Bất Biến (Cryptographic SHA-256 Fingerprint):** Mọi tệp tài liệu khi tải lên hệ thống được tính toán mã băm SHA-256 độc lập. Mã băm này được lưu trữ cố định trên trường `checksum` và đối chiếu trong mọi lần trích dẫn hoặc đối soát tài chính, ngăn ngừa triệt để nguy cơ tráo đổi tài liệu.
- **Ẩn Liên Kết Công Khai Nhạy Cảm (Protected Share Links):** Các thư mục chứa hợp đồng, bảng kê giờ công và thông tin cá nhân bắt buộc phải kích hoạt cờ `is_access_via_link_hidden = True`. Khách hàng chỉ có thể truy cập qua Cổng Khách Hàng (Customer Portal) có xác thực danh tính hoặc mã token HMAC có thời hạn hiệu lực.
- **Tuân Thủ Xóa Dữ Liệu Cá Nhân PDPD:** Khi đối tác hoặc ứng viên yêu cầu thực thi quyền được quên (Right to be Forgotten) theo Nghị định 13/2023/NĐ-CP, module `al2c.pdpd.erasure` tự động bôi đen (redact) các trường PII trên tài liệu mà không làm sai lệch số liệu kế toán tổng hợp.

---

## 2. Hệ Thống Quản Trị Tri Thức Doanh Nghiệp (Corporate KMS Architecture)

Tri thức doanh nghiệp là tài sản vô hình lớn nhất của công ty phần mềm dịch vụ. Hệ sinh thái `knowledge.article` đóng vai trò là **Nguồn Tri Thức Thẩm Quyền Duy Nhất (Single Source of Truth - SSOT)**:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        7 KHÔNG GIAN TRI THỨC CỐT LÕI (KMS SPACES)                      │
├────────────────────────┬────────────────────────┬──────────────────────────────────────┤
│ 1. Products & Features │ 2. Target Industries   │ 3. Sales Playbooks & Battlecards     │
│ 4. Delivery Frameworks │ 5. RFP & Bid Library   │ 6. Post-Mortems & Risk Cases         │
├────────────────────────┴────────────────────────┴──────────────────────────────────────┤
│ 7. Compliance, Legal & Regulatory Directives (VAS/IFRS, PDPD, ISO 27001)               │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### 2.1. Quy Trình Cập Nhật & Kiểm Định Tri Thức Hai Cấp (Dual-Stage Peer Review)

1. **Giai Đoạn Soạn Thảo (Drafting):** Chuyên gia CoE tạo bài viết mới hoặc chỉnh sửa phiên bản hiện tại bằng định dạng Markdown cấu trúc chuẩn.
2. **Giai Đoạn Thẩm Định Chuyên Môn (SME Review Gate):** Trưởng CoE chuyên môn (Practice Lead) kiểm tra tính chuẩn xác của mã SKU, chính sách đơn giá và kiến trúc kỹ thuật.
3. **Giai Đoạn Xuất Bản & Tự Động Đồng Bộ (Publish & Auto-Reindexing):** Sau khi được duyệt, hệ thống tự động gắn nhãn phiên bản, kích hoạt tiến trình lập chỉ mục và phân mảnh RAG vào bảng `al2c.rag.chunk`.
4. **Chu Kỳ Rà Soát Định Kỳ 90 Ngày (90-Day Freshness Review):** Mọi bài viết chưa được cập nhật quá 90 ngày sẽ được gắn cờ cảnh báo (Amber/Red Flag) để tác giả rà soát lại tính tương thích với phiên bản phần mềm mới nhất.

---

## 3. Kiến Trúc SOP-RAG Triệt Tiêu Ảo Giác (Zero-Hallucination SOP-RAG Pipeline)

Để phục vụ các yêu cầu tra cứu tự động của khách hàng, nhân viên và trợ lý ảo trên `innoria.com`, Innoria xây dựng động cơ RAG theo phương pháp **Chứng minh Căn cứ Tuyệt đối (Absolute Grounding Pipeline)**:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                       ĐƯỜNG ỐNG XỬ LÝ DỮ LIỆU CỦA ĐỘNG CƠ SOP-RAG                      │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                        │
│ [1. Kiến Trúc Phân Mảnh Bảo Toàn Bảng Biểu (Semantic Table-Preserving Chunking)]       │
│ • Bóc tách AST Markdown, nhận diện các tiêu đề H1/H2/H3 làm Breadcrumb ngữ cảnh.      │
│ • Bảng biểu Markdown (| ... |) được BẢO TOÀN NGUYÊN VẸN, không bao giờ bị cắt ngang.   │
│ • Mỗi phân mảnh chứa độ dài tối đa 512 tokens và 50 tokens gối đầu (overlap).          │
│                                  │                                                     │
│                                  ▼                                                     │
│ [2. Tìm Kiếm Lai Đa Tầng (Dense Embeddings + BM25 Sparse Lexical Search)]             │
│ • Vector Search: Nắm bắt hàm ý ngữ nghĩa sâu và các câu hỏi diễn giải bằng ngôn ngữ tự nhiên.│
│ • BM25 Lexical: Tìm kiếm chính xác các mã định danh kỹ thuật (SKU-ERP, TCV, Decree 70).│
│ • Thuật toán Hợp nhất Xếp hạng Nghịch đảo (Reciprocal Rank Fusion - RRF, k=60):        │
│   $$\text{RRF Score}(d) = \sum_{m \in \{\text{dense}, \text{sparse}\}} \frac{1}{60 + r_m(d)}$$│
│                                  │                                                     │
│                                  ▼                                                     │
│ [3. Cổng Thẩm Định Suy Diễn Logic Khắt Khe (Strict Entailment Gate $\ge 0.75$)]       │
│ • Mô hình phân loại suy luận tự nhiên (NLI Cross-Encoder) thẩm định câu trả lời:      │
│   $$\text{Entailment Score} = P(\text{Premise Entails Hypothesis} \mid \text{Context}, \text{Answer})$$ │
│ • Nếu điểm Entailment $< 0.75$: Hệ thống CHỦ ĐỘNG TỪ CHỐI TRẢ LỜI (Safe Abstention),   │
│   tuyệt đối không bịa đặt thông tin và chuyển hướng sang chuyên gia tư vấn con người.  │
│                                  │                                                     │
│                                  ▼                                                     │
│ [4. Hợp Đồng Trích Dẫn Thẩm Quyền Bắt Buộc (Universal Citation Contract)]             │
│ • Mọi khẳng định trong câu trả lời bắt buộc phải gắn thẻ trích dẫn chuẩn:              │
│   `[Tên_Văn_Bản | Đề_Mục_Chi_Tiết | Mã_Phân_Mảnh | 8_Ký_Tự_Đầu_Mã_Băm_SHA256]`        │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Trợ Lý Khách Hàng Cấp Cao Trên Innoria.com (Public Executive AI Concierge)

Trợ lý ảo trên website công khai `innoria.com` được thiết kế dưới dạng **Thành phần OWL 2 Reactive (OWL 2 Chat Drawer Widget)** kết nối trực tiếp với backend Insilos AL2C:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        KIẾN TRÚC TƯƠNG TÁC CỦA TRỢ LÝ AI CONCIERGE                     │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                        │
│   KHÁCH THĂM WEBSITE                              HỆ THỐNG BACKEND INSILOS             │
│   (innoria.com)                                   (addons/insilos_al2c)                │
│                                                                                        │
│   ┌────────────────────────┐                      ┌────────────────────────┐           │
│   │ Floating Launcher Icon │                      │ Controller Gateway     │           │
│   │ (Logo Innoria + Badge) │                      │ /innoria/ai_concierge/ │           │
│   └───────────┬────────────┘                      │ query                  │           │
│               │ Bấm mở                                └───────────▲────────────┘           │
│               ▼                                                   │                    │
│   ┌────────────────────────┐      JSON-RPC Query                 │                    │
│   │ OWL 2 Chat Drawer      │─────────────────────────────────────┘                    │
│   │ • Trả lời grounded     │                                                          │
│   │ • Chip trích dẫn nguồn │      JSON-RPC Lead Capture           ┌────────────────────┴───┐
│   │ • Form đặt lịch tư vấn │─────────────────────────────────────▶│ /innoria/ai_concierge/ │
│   └────────────────────────┘                                      │ book_lead              │
│                                                                   └───────────┬────────────┘
│                                                                               │ Tạo hồ sơ &
│                                                                               ▼ chấm điểm
│                                                                   ┌────────────────────────┐
│                                                                   │ Hồ Sơ Cơ Hội Bán Hàng  │
│                                                                   │ crm.lead (Score 0-100) │
│                                                                   └────────────────────────┘
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### 4.1. Thuật Toán Tự Động Chấm Điểm & Phân Loại Khách Hàng Tiềm Năng (B2B Fit Scoring)

Khi khách hàng trò chuyện hoặc gửi biểu mẫu đăng ký tư vấn, hệ thống tự động tính điểm theo ma trận 4 chiều (Thang điểm 0 - 100):
$$\text{B2B Fit Score} = S_{\text{firmographics}} (30\text{đ}) + S_{\text{budget}} (30\text{đ}) + S_{\text{urgency}} (20\text{đ}) + S_{\text{intent}} (20\text{đ})$$

1. **Quy Mô & Ngành Nghề ($S_{\text{firmographics}}$ - Tối đa 30đ):**
   - Thuộc nhóm ngành trọng điểm (Ngân hàng, Bán lẻ lớn, Dược phẩm, Sản xuất): 30 điểm.
   - Doanh nghiệp vừa và nhỏ (SME): 15 điểm.
   - Cá nhân / Khách lẻ: 5 điểm.
2. **Khả Năng Ngân Sách ($S_{\text{budget}}$ - Tối đa 30đ):**
   - Dự kiến ngân sách $\ge 500$ triệu VND (Nhóm Enterprise): 30 điểm.
   - Ngân sách 100 - 500 triệu VND (Nhóm Growth): 20 điểm.
   - Ngân sách $< 100$ triệu VND: 10 điểm.
3. **Thời Gian Triển Khai Mong Muốn ($S_{\text{urgency}}$ - Tối đa 20đ):**
   - Cần triển khai ngay trong vòng 30 ngày: 20 điểm.
   - Kế hoạch trong quý (1 - 3 tháng): 15 điểm.
   - Đang tham khảo thông tin (Chưa có hạn định): 5 điểm.
4. **Mức Độ Rõ Ràng Của Nhu Cầu ($S_{\text{intent}}$ - Tối đa 20đ):**
   - Yêu cầu báo giá chi tiết, phân tích so sánh kỹ thuật, cần bản demo giải pháp: 20 điểm.
   - Hỏi chung về tính năng: 10 điểm.

**Quy Tắc Phân Luồng Tự Động Của AL2C Lead Router:**
- **Điểm $\ge 70$ (Qualified Enterprise Lead):** Khởi tạo `crm.lead` với độ ưu tiên cao (`priority = '3'`), tự động gán cho Giám đốc Khối Tư vấn CoE phụ trách ngành, đồng thời gửi thông báo qua email và tạo lịch hẹn trao đổi trực tuyến (Google Meet).
- **Điểm $< 70$ (Nurturing Lead):** Đưa vào quy trình chăm sóc tự động (Email Nurturing Sequence), định kỳ gửi cẩm nang kiến trúc và lời mời tham gia hội thảo chuyên đề.

---

## 5. Quy Chuẩn Giao Diện Người Dùng & Trải Nghiệm Khách Hàng (UI/UX Standards)

- **Ngôn Ngữ Thiết Kế:** Tuân thủ tiêu chuẩn thiết kế phẳng hiện đại **IBM Carbon Design System** kết hợp các điểm nhấn dải màu gradient **SAP Horizon** (`#0070F2` đến `#0ABBDB`).
- **Khả Năng Tương Thích Chế Độ Tối (Sovereign Dark Mode Architecture):** Tự động thích ứng mượt mà với cài đặt giao diện của hệ điều hành; sử dụng các biến màu ngữ nghĩa (`var(--insilos-bg-surface)`, `var(--insilos-text-primary)`), tuyệt đối không để lộ các bề mặt màu trắng chói mắt.
- **Tiêu Chuẩn Tiếp Cận Web WCAG 2.1 AA:** Đảm bảo độ tương phản màu sắc tối thiểu $4.5:1$ đối với văn bản thông thường và $3.0:1$ đối với các nút bấm điều khiển; hỗ trợ đầy đủ phím tắt bàn phím và thẻ nhãn ARIA cho người khiếm thị.

---
*Văn bản ban hành bởi Ban Kiến Trúc Hệ Thống AI & Quản Trị Tri Thức Doanh Nghiệp Innoria.*
