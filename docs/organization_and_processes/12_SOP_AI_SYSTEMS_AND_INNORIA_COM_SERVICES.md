# SOP-AI-004: Quản Trị Hệ Thống Trí Tuệ Nhân Tạo (Enterprise AI Systems), Dịch Vụ Web Innoria.com & Động Cơ Tự Động Hóa Doanh Nghiệp

> **Mã quy trình:** SOP-AI-004  
> **Phiên bản:** 2.0 (Tháng 10/2026 - Chuẩn hóa Enterprise AI & Autonomous Operations)  
> **Phạm vi áp dụng:** Toàn bộ dịch vụ AI hướng ngoại trên cổng thông tin doanh nghiệp `innoria.com`, trợ lý ảo khách hàng, động cơ tự động bóc tách Mojo AI (`info@inno.ai.vn`), hệ thống làm giàu dữ liệu B2B Leads, và cụm kỹ nghệ tự động hóa Zencode Developer Swarm.  
> **Chủ quản quy trình:** Giám đốc AI (Head of AI), Giám đốc Công nghệ (CTO), Giám đốc Doanh thu (CRO), và Ban Đạo đức & An toàn Trí tuệ Nhân tạo (AI Governance Board).

---

## 1. Mục Đích & Nguyên Lý Quản Trị AI Doanh Nghiệp

### 1.1. Mục Đích
Thiết lập khuôn khổ vận hành, hàng rào an toàn và tiêu chuẩn chất lượng dịch vụ (SLA) cho toàn bộ các hệ sinh thái AI của Innoria Enterprise, nhằm:
1. **Chuyển Đổi Trải Nghiệm Khách Hàng Đỉnh Cao (Hyper-Personalized B2B Experience):** Cung cấp trợ lý số thông minh trên `innoria.com` hỗ trợ tìm hiểu giải pháp, phân tích nhu cầu và kết nối tư vấn chuyên sâu 24/7.
2. **Tự Động Hóa Vòng Đời Bán Hàng & Vận Hành (Lead-to-Cash Automation):** Làm giàu hồ sơ khách hàng tiềm năng (`crm.lead`), đối soát giờ công tự động qua email, và minh bạch hóa giải trình hóa đơn cho khách hàng.
3. **Tuân Thủ Pháp Định & Đạo Đức AI (Regulatory & Ethical AI Compliance):** Tuân thủ tuyệt đối Luật An ninh mạng, Nghị định 13/2023/NĐ-CP (PDPD), tiêu chuẩn ISO/IEC 42001:2023 (Artificial Intelligence Management System), và tiêu chuẩn bảo vệ dữ liệu xuyên biên giới.

### 1.2. 5 Trụ Cột Năng Lực AI Của Innoria Enterprise
```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                   HỆ SINH THÁI AI DOANH NGHIỆP INNORIA ENTERPRISE                        │
├────────────────────┬────────────────────┬────────────────────┬───────────────────────────┤
│ 1. WEB CONCIERGE   │ 2. LEAD ENRICHMENT │ 3. PORTAL EXPLAINER│ 4. MOJO INGESTION WORKER  │
│  (innoria.com AI)  │    (B2B CRM AI)    │  (Customer Portal) │   (info@inno.ai.vn)       │
├────────────────────┼────────────────────┼────────────────────┼───────────────────────────┤
│ • Portfolio Advisor│ • MST / Doanh thu  │ • Giải trình công nợ│ • Bóc tách bảng kê (.xlsx)│
│ • Sơ bộ FIT-Score  │ • Công nghệ Tech   │ • Diễn giải giờ tư │ • Khớp 3 tầng chuyên gia  │
│ • Đặt lịch tư vấn  │ • Điểm mua (Intent)│   vấn chi tiết     │ • Chống trùng lặp SHA-256 │
│ • Grounded 100%    │ • Tự động gắn nhãn │ • Đối soát AL2C-103│ • Tự động hóa đề xuất VAT │
├────────────────────┴────────────────────┴────────────────────┴───────────────────────────┤
│ 5. ZENCODE DEVELOPER SWARM (AGY Fleet • Autonomous DevSecOps • 13 Council Verification)  │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Đặc Tả Chi Tiết 5 Năng Lực AI Trọng Yếu

### 2.1. Trợ Lý Khảo Sát & Tư Vấn Cấp Cao (Executive AI Concierge trên `innoria.com`)
- **Mục tiêu:** Tiếp đón khách hàng truy cập website `innoria.com`, trả lời các câu hỏi về danh mục sản phẩm (Insilos ERP, Vertical Resilience GRC, Mojo AI, Zencode Ent), định hướng giải pháp phù hợp với quy mô doanh nghiệp.
- **Hàng rào Grounding (Zero Hallucination Invariant):**
  - Chỉ được sử dụng các đoạn tri thức (Context Chunks) đã được chỉ mục từ không gian `/Products`, `/Industries`, và `/Battlecards` của KMS (SOP-KNW-002).
  - Điểm suy diễn logic (Entailment Score) bắt buộc $\ge 0.85$. Nếu điểm $< 0.85$, hệ thống xuất câu phản hồi an toàn: *"Innoria hiện đang hoàn thiện tài liệu chi tiết cho cấu phần này. Quý khách vui lòng để lại email hoặc kết nối chuyên gia tư vấn để nhận thông tin thẩm quyền."*
- **Tương tác chuyển đổi:** Tích hợp tính năng gợi ý đặt lịch hẹn tư vấn chuyên sâu (Discovery Briefing) trực tiếp vào bảng lịch `calendar.event` và sinh cơ hội bán hàng `crm.lead`.

### 2.2. Động Cơ Làm Giàu & Chấm Điểm Cơ Hội Bán Hàng (B2B Lead Enrichment & Scoring Engine)
- **Kích hoạt:** Khi khách hàng gửi yêu cầu tư vấn trên website hoặc qua email `contact@innoria.com`.
- **Luồng xử lý tự động (Processing Flow):**
  1. *Làm sạch & Chuẩn hóa:* Chuẩn hóa tên doanh nghiệp, số điện thoại, định dạng email doanh nghiệp (loại trừ email cá nhân @gmail, @yahoo trừ trường hợp đặc biệt).
  2. *Truy vấn Dữ liệu Doanh nghiệp (Enterprise Registry Enrichment):* Tra cứu Mã số thuế (MST), vốn điều lệ, địa chỉ đăng ký kinh doanh, người đại diện pháp luật từ cổng dữ liệu quốc gia.
  3. *Phân tích Khẩu vị Công nghệ (Tech-Stack & Digital Maturity):* Quét hạ tầng tên miền, công nghệ web đang sử dụng (ERP hiện tại, nền tảng thương mại điện tử, máy chủ đám mây).
  4. *Chấm điểm Tiềm năng (B2B Fit Score):*
     - Điểm quy mô (Vốn, số lượng nhân sự): Trọng số $30\%$.
     - Điểm ngành nghề mũi nhọn (Tài chính, Bán lẻ chuỗi, Sản xuất): Trọng số $30\%$.
     - Điểm hành vi tương tác trên website (Xem báo giá, đọc whitepaper, thời gian trên trang): Trọng số $40\%$.
  5. *Phân bổ Cơ hội (Lead Routing):* Tự động gán cơ hội cho Trưởng bộ phận phụ trách ngành tương ứng kèm bản tóm tắt phân tích (Lead Dossier) trong `crm.lead`.

### 2.3. Trợ Lý Diễn Giải Bảng Kê Giờ Công & Hóa Đơn Khách Hàng (Customer Portal Explainer)
- **Vị trí tích hợp:** Hiển thị trực tiếp trên giao diện Cổng Khách Hàng (`portal.portal_my_home`, view hóa đơn `account.portal_invoice_page`).
- **Nghiệp vụ cốt lõi:**
  - Diễn giải minh bạch từng dòng chi phí trên hóa đơn dịch vụ tư vấn: Số giờ làm việc thực tế, đầu việc cụ thể tương ứng với từng mốc giai đoạn SAP Activate (Prepare, Explore, Realize, Deploy, Run).
  - Đối soát tỷ giá quy đổi ngoại tệ (USD/EUR sang VND) theo hợp đồng đã ký và quy định của Ngân hàng Nhà nước.
  - Hỗ trợ giải đáp các câu hỏi thường gặp về điều khoản thanh toán, tài khoản thụ hưởng Napas247, và biên bản nghiệm thu mốc.
  - Tích hợp nút kích hoạt quy trình khiếu nại tranh chấp (AL2C-INV-103) khi khách hàng cần làm rõ số liệu, tự động đóng băng tiến trình nhắc nợ (Dunning Freeze).

### 2.4. Công Nhân Xử Lý Timesheet Tự Động Mojo AI (`info@inno.ai.vn`)
- **Vai trò:** Trung tâm thu nhận và tiền xử lý dữ liệu timesheet email hướng sự kiện (Event-Driven Timesheet Ingestion Pipeline).
- **Quy trình xử lý tự động:**
  1. *Tiếp nhận:* Daemon `mail_pubsub_daemon.py` lắng nghe Webhook khi có email gửi đến `info@inno.ai.vn`.
  2. *Kiểm tra An toàn Email:* Thẩm định SPF, DKIM, DMARC. Cách ly các thư mạo danh vào vùng Quarantine.
  3. *Bóc tách Định Dạng Đa Dạng (Multi-Modal Document Parsing):*
     - Đọc file Excel đính kèm (`.xlsx`, `.xls`): Tự động nhận diện sheet chứa bảng chấm công, cột chuyên gia, ngày thực hiện, số giờ, và mã công việc.
     - Đọc file CSV hoặc văn bản có cấu trúc trong nội dung email (Email Body).
  4. *Khớp Chuyên Gia 3 Tầng (3-Tier Matcher):*
     - Tầng 1: Khớp chính xác theo địa chỉ email chuyên gia (`hr.employee.work_email`).
     - Tầng 2: Khớp theo Mã định danh nhân viên (`identification_id` / Mã tư vấn).
     - Tầng 3: Khớp theo họ tên không dấu và phòng ban CoE chuyên trách.
  5. *Chống Trùng Lặp Tuyệt Đối (SHA-256 Deduplication):*
     - Tính toán mã băm SHA-256 trên nội dung payload và kiểm tra trùng lặp trên bộ đệm `al2c.timesheet.staging`.
     - Kiểm tra trùng lặp với sổ cái phân tích đã ghi nhận `account.analytic.line` theo cặp `(employee_id, task_id, date)`.
  6. *Đẩy Trình Duyệt 1-Click:* Chuyển dữ liệu hợp lệ sang trạng thái `staged` để Quản lý Dự án (`project.group_project_manager`) kiểm tra và bấm "Xác Nhận & Ghi Sổ" chỉ với 1 click.

### 2.5. Cụm Kỹ Nghệ Tự Động Hóa Zencode Developer Swarm
- **Kiến trúc:** Cụm 8 node tự động hóa phân tán (AGY Fleet Multi-Account Swarm), kết nối qua API router nội bộ.
- **Nhiệm vụ chuyên trách:**
  - Vibe Coding song song (Parallel Synthesis): Phát triển tính năng mới đồng thời trên nhiều luồng.
  - Tái cấu trúc Biện chứng (Hegelian Dialectic Refactoring): Nâng cấp mã nguồn thừa kế thành mã sạch theo tiêu chuẩn Clean Core.
  - Kiểm thử Hồi quy Tự động: Tự động sinh test cases, kiểm tra tính toàn vẹn của mô hình ORM và giao diện OWL 2.
  - Vận hành 13 Cổng Hội Đồng Kỹ Thuật (13 Council Gates): Đảm bảo mã nguồn đáp ứng 100% tiêu chí trước khi hợp nhất vào nhánh chính.

---

## 3. Các Hàng Rào Quản Trị Bắt Buộc (Critical Governance Invariants)

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                      4 HÀNG RÀO AN TOÀN TUYỆT ĐỐI CHO HỆ THỐNG AI                        │
├──────────────────────────┬──────────────────────────┬────────────────────────────────────┤
│ 1. ZERO HALLUCINATION    │ 2. DATA PROTECTION (PDPD)│ 3. MULTI-TENANT ISOLATION          │
├──────────────────────────┼──────────────────────────┼────────────────────────────────────┤
│ • Entailment Score >=0.85│ • Che giấu PII tự động   │ • Cách ly tri thức theo company_id │
│ • Trích dẫn đầy đủ nguồn │ • Không huấn luyện mô hình│ • Kiểm soát quyền ir.model.access │
│   [Doc|Sec|ID|SHA256]    │   bằng dữ liệu khách hàng│ • Zero cross-tenant leakage        │
├──────────────────────────┴──────────────────────────┴────────────────────────────────────┤
│ 4. HUMAN-IN-THE-LOOP FOR CRITICAL ACTIONS (Duyệt tài chính, Phê duyệt hóa đơn, Ký hợp đồng│
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

### 3.1. Hàng Rào Chống Ảo Giác & Hợp Đồng Trích Dẫn (Citation Contract)
- Mọi câu trả lời của AI trên website và cổng khách hàng phải tuân thủ hợp đồng trích dẫn chuẩn:
  `[Tên Tài Liệu | Tiêu Đề Mục | ID Bản Ghi | Mã Băm SHA-256]`
- Không bao giờ sinh nội dung khẳng định nếu không tìm thấy ít nhất 1 chunk chứng minh có độ tương đồng cosine $\ge 0.75$ và điểm suy diễn logic $\ge 0.85$.

### 3.2. Bảo Vệ Dữ Liệu Cá Nhân (Decree 13/2023/NĐ-CP & PII Redaction)
- **Quy tắc Redaction bắt buộc:** Trước khi truyền bất kỳ văn bản nào từ email hoặc phản hồi của người dùng tới các dịch vụ mô hình ngôn ngữ lớn (LLM APIs), hệ thống phải quét và che giấu các trường dữ liệu nhạy cảm:
  - Số Căn cước công dân (CCCD / CMND).
  - Số tài khoản ngân hàng cá nhân, số thẻ thanh toán.
  - Mật khẩu, mã OTP, và các token xác thực bí mật.
- Dữ liệu khách hàng tuyệt đối không được sử dụng để huấn luyện lại (re-training/fine-tuning) các mô hình công cộng.

### 3.3. Phân Lập Dữ Liệu Đa Khách Hàng (Multi-Tenant RBAC Isolation)
- Quá trình truy xuất dữ liệu (Retrieval Stage) bắt buộc phải lọc theo `company_id` của phiên làm việc hiện tại và quyền hạn `ir.model.access` của người dùng.
- Khách hàng vãng lai trên `innoria.com` chỉ có quyền truy xuất các tri thức được công khai gắn nhãn `public`.

### 3.4. Con Người Giữ Quyền Quyết Định Cuối Cùng (Human-in-the-Loop - HITL)
- AI chỉ đóng vai trò phân tích, bóc tách và đề xuất (Co-Pilot).
- Mọi thao tác tài chính trọng yếu:
  - Phê duyệt chiết khấu bán hàng $> 10\%$.
  - Ghi nhận giờ công vào sổ sách kế toán `account.analytic.line`.
  - Phát hành hóa đơn điện tử VAT có ký số.
  - Giải quyết khiếu nại tranh chấp thương mại.
  Bắt buộc phải do người dùng có thẩm quyền thực hiện bằng thao tác bấm duyệt minh thị trên giao diện người dùng.

---

## 4. Cơ Chế Giám Sát, Đo Lường & Báo Cáo Hiệu Năng (SLA & Telemetry)

Hệ thống AI được giám sát 24/7 thông qua bộ chỉ số đo lường hiệu năng:

| Chỉ Số Đo Lường | Mục Tiêu Cam Kết (Target SLA) | Hành Động Khắc Phục Khi Vi Phạm (Mitigation) |
| :--- | :---: | :--- |
| **Độ trễ phản hồi Web Concierge** | $\le 1.5$ giây (P95) | Kích hoạt bộ nhớ đệm ngữ nghĩa (Semantic Cache), chuyển hướng sang mô hình Flash nhẹ hơn. |
| **Độ chính xác bóc tách Timesheet** | $\ge 99.5\%$ | Cách ly các mẫu timesheet dị biệt vào hàng đợi duyệt thủ công, cập nhật parser mẫu mới. |
| **Tỷ lệ Ảo giác (Hallucination Rate)** | $0.0\%$ (Tuyệt đối không) | Nâng ngưỡng Entailment Gate lên 0.90, tạm ngừng trả lời tự động cho chủ đề bị lỗi. |
| **Thời gian làm giàu B2B Lead** | $\le 10$ giây kể từ khi submit | Bổ sung hàng đợi nền Celery/Cron xử lý bất đồng bộ, sử dụng dữ liệu lưu đệm từ registry. |
| **Tính khả dụng của hệ thống AI** | $\ge 99.9\%$ uptime | Thiết lập cơ chế tự động chuyển mạch (Failover) giữa các cụm model dự phòng (Google Gemini / Anthropic Claude). |

---

## 5. Quy Trình Ứng Phó Sự Cố AI (Incident Response Protocol)

Khi phát hiện sự cố AI (ảo giác nghiêm trọng, rò rỉ dữ liệu, lỗi phân tích timesheet hàng loạt):
1. **Pha 1 - Khẩn cấp (Immediate Freeze $\le 5$ phút):**
   - Kích hoạt chốt ngắt khẩn cấp (Kill-Switch) thông qua tham số `ir.config_parameter`: `al2c.autonomy_enabled = False`.
   - Toàn bộ các tương tác AI chuyển sang chế độ dự phòng tĩnh (Static Fallback Message & Human Handover).
2. **Pha 2 - Điều tra & Cô lập (Isolate & Investigate $\le 30$ phút):**
   - Trích xuất nhật ký truy vấn RAG, mã băm văn bản chunk, và prompt tương ứng trong bảng nhật ký `al2c.runtime.incident`.
   - Xác định nguyên nhân gốc rễ (Lỗi chỉ mục, sai lệch tài liệu nguồn, hay tấn công tiêm nhiễm câu lệnh - Prompt Injection).
3. **Pha 3 - Khắc phục & Cập nhật Tri Thức (Remediation & Cache Purge $\le 2$ giờ):**
   - Chỉnh sửa tài liệu thẩm quyền nguồn trong KMS hoặc cập nhật bộ lọc parser.
   - Xóa bỏ toàn bộ vector nhúng và bộ nhớ đệm bị lỗi liên quan.
   - Chạy bộ kiểm thử tự động `test_al2c_rag_grounding.py` và kiểm định tính toàn vẹn 100% xanh.
4. **Pha 4 - Tái kích hoạt & Hậu kiểm (Resume & Post-Mortem):**
   - Mở lại tham số `al2c.autonomy_enabled = True`.
   - Xuất biên bản sự cố vào không gian `/Post_mortems` trong KMS theo đúng quy định SOP-KNW-002.
