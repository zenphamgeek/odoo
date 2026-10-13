# SOP-RAG-003: Kiến Trúc RAG Doanh Nghiệp (Retrieval-Augmented Generation), Chứng Thực Nguồn Tri Thức (Grounding Governance) & Phòng Chống Ảo Giác AI

> **Mã quy trình:** SOP-RAG-003  
> **Phiên bản:** 2.0 (Tháng 10/2026 - Chuẩn hóa Enterprise Hybrid RAG)  
> **Phạm vi áp dụng:** Toàn bộ hệ thống sinh văn bản tự động, chatbot tư vấn khách hàng trên website `innoria.com`, trợ lý ảo nội bộ Mojo AI, và công cụ tự động phản hồi hồ sơ thầu RFP.  
> **Chủ quản quy trình:** Giám đốc AI (Head of AI), Kiến trúc sư Trưởng RAG & LLM Systems, Ban Đạo đức & An toàn Trí tuệ Nhân tạo.

---

## 1. Mục Đích & Nguyên Lý "Không Có Căn Cứ - Không Sinh Lời" (Grounding Principle)

### 1.1. Mục Đích
Thiết lập tiêu chuẩn kỹ thuật tối thượng cho toàn bộ các mô hình ngôn ngữ lớn (LLMs) hoạt động trong hệ thống của Innoria Enterprise:
1. **Loại Bỏ Triệt Để Ảo Giác (Zero-Hallucination Mandate):** Mô hình không bao giờ được phép tự suy đoán thông tin về giá bán, tính năng kỹ thuật, hoặc cam kết pháp lý nếu không có đoạn trích dẫn (Context Chunk) tương ứng trong tài liệu thẩm quyền.
2. **Truy Xuất Nguồn Gốc Toàn Diện (Full Provenance & Citations):** Mọi câu khẳng định sự thật (factual assertion) trong câu trả lời phải kèm theo mã định danh chứng thực: `[Tên Tài Liệu | Mã Bài Viết | Đoạn Băm SHA-256]`.
3. **Phân Vùng Đa Khách Hàng Tuyệt Đối (Multi-Tenant & RBAC Isolation):** Không bao giờ rò rỉ tri thức nội bộ hoặc tài liệu riêng của Khách hàng A sang câu trả lời cung cấp cho Khách hàng B (CWE-200 / Information Exposure Defense).

---

## 2. Quy Trình Vận Hành 7 Bước Của Đường Ống RAG Chuẩn (7-Stage Pipeline)

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│             ĐƯỜNG ỐNG TRUY XUẤT & SINH VĂN BẢN CÓ CĂN CỨ (ENTERPRISE SOP-RAG)          │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ [1. Thu Nhận Tri Thức] Đọc từ knowledge.article, documents.document, Git Markdown      │
│                                  │                                                     │
│                                  ▼                                                     │
│ [2. Bóc Tách Phân Tầng] Phân đoạn văn bản ngữ nghĩa (512-1024 tokens) giữ nguyên Bảng │
│                                  │                                                     │
│                                  ▼                                                     │
│ [3. Đánh Chỉ Mục Kép]  Dense Vector (Gemini/OpenAI) + Sparse Lexical (Postgres tsvector│
│                                  │                                                     │
│                                  ▼                                                     │
│ [4. Lọc Thẩm Quyền RBAC]Giới hạn theo company_id và nhóm quyền hạn ir.model.access    │
│                                  │                                                     │
│                                  ▼                                                     │
│ [5. Hợp Nhất & Tái Xếp]Thuật toán Reciprocal Rank Fusion (RRF) + Cross-Encoder Reranker│
│                                  │                                                     │
│                                  ▼                                                     │
│ [6. Thẩm Định Căn Cứ]  Chấm điểm suy diễn logic (Entailment Score >= 0.85)             │
│                        (Fail-closed: từ chối trả lời nếu không đủ căn cứ)              │
│                                  │                                                     │
│                                  ▼                                                     │
│ [7. Sinh Lời Kèm Nguồn]Xuất câu trả lời hoàn chỉnh kèm chú thích trích dẫn thẩm quyền  │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Đặc Tả Kỹ Thuật Chi Tiết Từng Phân Đoạn (Technical Specifications)

### 3.1. Chiến Lược Phân Đoạn Văn Bản (Hierarchical Semantic Chunking)
- **Kích thước đoạn (Chunk Window):** Tối ưu từ 512 đến 1024 tokens; độ gối đầu (overlap) là $10\%$ (khoảng 50 tokens) để giữ tính liên tục của ngữ cảnh.
- **Bảo toàn Cấu trúc Tiêu đề:** Mỗi đoạn chunk phải được tiền tố bằng đường dẫn phân cấp tiêu đề (Breadcrumb Headers), ví dụ: `Products > ERP > ERP-STARTER > Phạm Vi Dịch Vụ`.
- **Nguyên Tắc Bất Biến Về Bảng Dữ Liệu (Table Continuity Invariant):**
  - Nghiêm cấm ngắt ngang một bảng Markdown ở giữa hàng. Nếu bảng dài vượt quá 1024 tokens, bảng phải được bóc tách thành các đoạn độc lập nhưng luôn bảo lưu hàng tiêu đề (Header row).

### 3.2. Thuật Toán Truy Xuất Lai Hợp Nhất (Hybrid Retrieval Engine & RRF)
Hệ thống kết hợp cả hai phương pháp tìm kiếm để bù trừ điểm yếu của nhau:
1. **Dense Vector Search:** Đo độ tương đồng ngữ nghĩa bằng khoảng cách Cosine trên không gian vector 1536/3072 chiều.
2. **Sparse Lexical Search:** Tìm kiếm từ khóa chính xác bằng chỉ mục `tsvector` tiếng Việt và tiếng Anh có hỗ trợ stemming và BM25.
3. **Thuật toán Hợp nhất Thứ hạng Nghịch đảo (Reciprocal Rank Fusion - RRF):**
   $$RRF(d) = \sum_{m \in \{Dense, Sparse\}} \frac{1}{k + r_m(d)}$$
   *(Trong đó tham số hằng số $k = 60$; $r_m(d)$ là thứ hạng của tài liệu $d$ trong mô hình $m$).*

### 3.3. Bộ Lọc An Toàn Đa Tầng Quyền Hạn (Multi-Tenant & RBAC Filter)
Trước khi đưa kết quả vào mô hình LLM, tầng trung gian thực thi truy vấn lọc nghiêm ngặt:
```sql
WHERE chunk.company_id = :current_company_id
  AND chunk.access_group_ids && :user_group_ids
  AND chunk.freshness_state != 'deprecated'
```
- Ngăn chặn hoàn toàn việc nhân viên hoặc khách hàng truy cập vào các đoạn tri thức vượt cấp thẩm quyền của mình.

### 3.4. Cổng Kiểm Soát Chứng Thực Căn Cứ (Grounding Verification Gate)
- Mô hình kiểm chứng độc lập (NLI Verifier / Natural Language Inference) đánh giá xác suất suy diễn logic giữa câu trả lời sinh ra ($A$) và ngữ cảnh trích xuất ($C$):
  $$\text{Score}_{Entailment}(A \mid C) \ge 0.85$$
- **Nguyên tắc Đóng Kín An Toàn (Fail-Closed Invariant):**
  - Nếu điểm số $< 0.85$, hệ thống lập tức hủy bỏ câu trả lời sinh tự do và xuất thông điệp chuẩn:  
    *“Yêu cầu của Quý khách hiện chưa có thông tin chính thức trong Cơ sở Tri thức Thẩm quyền của Innoria. Chuyên viên tư vấn của chúng tôi sẽ liên hệ phản hồi trực tiếp.”*

### 3.5. Quy Chuẩn Trích Dẫn Thẩm Quyền (Strict Citation Contract)
Mỗi sự kiện, thông số kỹ thuật, đơn giá hoặc cam kết SLA được xuất ra phải có định dạng trích dẫn chuẩn:
```markdown
[Nguồn: <Tên Tài Liệu / SKU> | Bài Viết: <kb_id> | Đoạn Băm: <sha256_short>]
```
Ví dụ:
> *Dịch vụ triển khai Insilos ERP Starter hoàn thành trong thời gian cố định 6 tuần với mô hình giá trọn gói [Nguồn: ERP-STARTER | ID: kb_sku_erp_starter | Hash: 8f4c2e1a].*

---

## 4. Cơ Chế Làm Mới Chỉ Mục Vector Hướng Sự Kiện (Event-Driven Re-indexing)

1. Khi một bài viết `knowledge.article` hoặc tài liệu `documents.document` được lưu (`write`) hoặc xóa (`unlink`):
   - ORM trigger kích hoạt sự kiện phát tín hiệu qua bus tin nhắn nội bộ `bus.bus` hoặc Redis stream.
   - Trình xử lý nền tự động hủy bộ đệm câu trả lời (Cache Invalidation) trong vòng $\le 1$ giây.
   - Lập lịch phân đoạn và tái nhúng vector (Re-embedding) cho các đoạn thay đổi trong vòng $\le 5$ giây.
2. Đảm bảo tri thức mới được cập nhật tức thời tới các trợ lý ảo AI trên `innoria.com` mà không cần khởi động lại dịch vụ.

---
*Lưu hành nội bộ - Ban Quản trị AI & Dữ liệu Lớn UNG DUNG SANG TAO LLC / INNORIA ENTERPRISE.*
