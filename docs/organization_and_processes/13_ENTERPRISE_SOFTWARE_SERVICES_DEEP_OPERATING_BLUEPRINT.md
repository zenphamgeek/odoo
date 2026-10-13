# Blueprint Vận Hành Toàn Diện Doanh Nghiệp Dịch Vụ Phần Mềm Đa Sản Phẩm (Enterprise Software Services Operating Blueprint)
## Khung Quản Trị Tổ Chức, Cơ Cấu CoE & Chuỗi Giá Trị Hợp Nhất Tứ Trụ: Insilos ERP • Vertical Resilience • Mojo AI • Zencode Ent

> **Mã văn bản:** BP-ENT-OPS-2026-V4  
> **Áp dụng cho:** Toàn bộ các Trung tâm Xuất sắc (CoEs), Khối Dự án Triển khai & Hệ thống 4 Repositories  
> **Cơ sở hạ tầng & Mã nguồn:**  
> • Insilos ERP: [`/home/zen/O20`](file:///home/zen/O20) & [`/home/zen/insilos_mobile`](file:///home/zen/insilos_mobile)  
> • Vertical Resilience: [`/home/zen/VerticalRisk`](file:///home/zen/VerticalRisk)  
> • Mojo AI: [`addons/insilos_al2c`](file:///home/zen/O20/addons/insilos_al2c)  
> • Zencode Ent: [`/home/zen/zencode-ent`](file:///home/zen/zencode-ent)  
> **Cơ chế pháp lý & Tuân thủ:** Nghị định 13/2023/NĐ-CP (PDPD) • Nghị định 70/2025/NĐ-CP (Hóa đơn điện tử) • ISO/IEC 27001 • SOC 2 Type II

---

## 1. Cơ Cấu Tổ Chức Ma Trận (Matrix CoE × Client Delivery Pods)

Doanh nghiệp hoạt động theo mô hình tổ chức **Ma trận Chuyên môn hóa (Dual-Axis Matrix Model)** kết hợp giữa các **Trung tâm Xuất sắc Chuyên môn (Centers of Excellence - CoEs)** và các **Tổ hợp Triển khai Khách hàng Đa chức năng (Client Delivery Pods)**.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        BAN ĐIỀU HÀNH & HỘI ĐỒNG CHIẾN LƯỢC (EXECUTIVE BOARD)          │
│                    Chief Executive Officer • Chief Technology Officer                  │
│                     Head of Consulting Practices • General Counsel                     │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
        ┌───────────────────────────────────┴───────────────────────────────────┐
        ▼                                                                       ▼
┌───────────────────────────────────────────┐   ┌───────────────────────────────────────────┐
│     KHỐI TRUNG TÂM XUẤT SẮC (CoE AXIS)    │   │      KHỐI TRIỂN KHAI DỰ ÁN (DELIVERY AXIS)│
│       Quản trị Năng lực & Tài sản         │   │         Cam kết P&L và SLA Khách hàng     │
├───────────────────────────────────────────┤   ├───────────────────────────────────────────┤
│ 1. Enterprise ERP CoE (Insilos O20 Core)  │──▶│ Pod Alpha: Triển khai Khối Ngân hàng & TCKT│
│ 2. Security, Risk & GRC CoE (VerticalRisk)│──▶│ Pod Beta: Doanh nghiệp Sản xuất & Bán lẻ   │
│ 3. Cognitive Agentic AI CoE (Mojo Swarm)  │──▶│ Pod Gamma: Chuỗi Cung ứng & Logistics WMS │
│ 4. Modernization & Swarm CoE (Zencode Ent)│──▶│ Pod Delta: Chuyển đổi số Di sản Core Legacy│
└───────────────────────────────────────────┘   └───────────────────────────────────────────┘
```

### 1.1. Chi Tiết Vai Trò & Ma Trận Phân Bổ Nhân Sự (Role Profiles & Staffing Framework)

| Cấp Bậc (Level) | Chức Danh Chuyên Môn | Trọng Tâm Trách Nhiệm CoE | Trọng Tâm Trách Nhiệm Dự Án | Định Mức Giờ Tính Tiền (Target Billability) |
| :--- | :--- | :--- | :--- | :---: |
| **L6 - Partner / Principal** | Giám đốc Khối Tư vấn / Practice Principal | • Chiến lược năng lực CoE<br>• Phê duyệt kiến trúc chuẩn<br>• Đào tạo hạt giống & R&D | • Bảo trợ cấp cao (Executive Sponsor)<br>• Xử lý khủng hoảng & leo thang SLA<br>• Phê duyệt Deal-Desk hợp đồng lớn | **$\ge 45\%$** (Tập trung chiến lược & deal lớn) |
| **L5 - Lead Architect** | Kiến trúc sư Giải pháp Trưởng / Solution Architect | • Định hình mẫu thiết kế (Blueprints)<br>• Đồng bộ hợp đồng dữ liệu liên repo<br>• Kiểm định các Council Gates | • Thiết kế kiến trúc tổng thể toàn dự án<br>• Thẩm định Fit-to-Standard SAP Activate<br>• Giám sát ranh giới Clean Core | **$\ge 75\%$** |
| **L4 - Delivery Lead / PM** | Giám đốc Dự án / Senior Project Manager | • Đóng góp bài học kinh nghiệm (Post-Mortem)<br>• Chuẩn hóa mẫu tài liệu nghiệm thu | • Quản lý P&L dự án, tiến độ 5 pha Activate<br>• Phê duyệt 1-click Bảng kê Timesheet<br>• Kiểm soát ngân sách giờ công ($\le 85\%$) | **$\ge 85\%$** |
| **L3 - Senior Consultant** | Chuyên viên Tư vấn Cao cấp (ERP/GRC/AI) | • Viết bài viết tri thức KMS chuẩn hóa<br>• Xây dựng bộ thư viện quy trình mẫu | • Cấu hình nghiệp vụ chuyên sâu, thiết kế quy trình<br>• Hướng dẫn người dùng chính (Key Users)<br>• Báo cáo timesheet chuẩn qua email | **$\ge 88\%$** |
| **L2 - Technical Engineer** | Kỹ sư Công nghệ (Python, OWL2, Mojo, Node) | • Viết mã nguồn module, API adapters<br>• Thực thi kiểm thử tự động, linting | • Tùy biến mã sạch Clean Core, viết báo cáo<br>• Tích hợp hệ thống thứ ba qua Webhooks/mTLS<br>• Báo cáo timesheet chi tiết theo Task ID | **$\ge 90\%$** |
| **L1 - Associate / Junior** | Kỹ sư Tập sự / Associate Consultant | • Tích lũy chứng chỉ CoE theo lộ trình<br>• Tham gia thực hành Swarm Pairing | • Hỗ trợ kiểm thử UAT, làm sạch dữ liệu di trú<br>• Shadowing có định mức dưới sự kèm cặp của L3/L4 | **$\ge 75\%$** (Phần còn lại là đào tạo CoE) |

---

## 2. Các Chỉ Số Kinh Tế & Hàng Rào Tài Chính Bất Biến (Financial & Delivery Invariants)

### 2.1. Định Mức Tận Dụng Tư Vấn Toàn Công Ty (Target Billable Utilization $\ge 78\%$)

Công thức tính tỷ lệ tận dụng nguồn lực tư vấn:
$$\text{Billable Utilization Rate} = \frac{\sum \text{Billable Consulting Hours Recorded}}{\sum \text{Standard Capacity Working Hours (160h/tháng)}} \times 100\%$$

- **Ngưỡng An Toàn Toàn Doanh Nghiệp:** $\ge 78\%$.
- **Cơ Chế Cảnh Báo Sớm (Early-Warning Mechanism):** Nếu tỷ lệ tận dụng của một CoE giảm xuống dưới $70\%$ trong 2 tuần liên tiếp, hệ thống AL2C tự động kích hoạt tác vụ kiểm định rà soát Bench Time, tái phân bổ chuyên gia sang các dự án đang thiếu hụt nguồn lực hoặc chuyển hướng làm giàu tài sản mã nguồn tái sử dụng (Reusable Accelerators).
- **Hàng Rào Trần Giờ Làm Việc (Burnout & Safety Ceiling Invariant):** Nghiêm cấm ghi nhận vượt quá **12 giờ/ngày** cho một nhân sự. Mọi bản ghi vượt ngưỡng bị hệ thống tự động từ chối để bảo vệ sức khỏe nhân sự và tuân thủ Bộ luật Lao động.

### 2.2. Khung Đơn Giá Giờ Công Chuẩn (Enterprise Blended Rate Card)

| Mã Cấp Bậc | Chức Danh Chuyên Môn | Đơn Giá Tiêu Chuẩn (VND/Giờ) | Đơn Giá Theo Ngày (8h/Ngày) | Đơn Giá Khẩn Cấp / Ngoài Giờ (+50%) |
| :---: | :--- | :---: | :---: | :---: |
| **RC-PRIN** | Practice Principal / Lead Solution Architect | **3.500.000** | 28.000.000 | 5.250.000 |
| **RC-SARC** | Enterprise Solution Architect (ERP/GRC/AI) | **2.500.000** | 20.000.000 | 3.750.000 |
| **RC-PMGR** | Senior Project Delivery Lead / Scrum Master | **2.000.000** | 16.000.000 | 3.000.000 |
| **RC-SCON** | Senior Consultant (VAS Accounting / GRC / Lead AI) | **1.800.000** | 14.400.000 | 2.700.000 |
| **RC-MCON** | Mid-level Consultant / Fullstack Engineer | **1.200.000** | 9.600.000 | 1.800.000 |
| **RC-ACON** | Associate Consultant / Implementation Support | **800.000** | 6.400.000 | 1.200.000 |

### 2.3. Hàng Rào Bảo Vệ Biên Lợi Nhuận Gộp & Kiểm Soát Deal-Desk (Margin Protection Invariants)

1. **Biên Lợi Nhuận Gộp Tối Thiểu (Gross Margin Floor):** Mọi hợp đồng dịch vụ tư vấn triển khai và bảo trì phải đạt biên lợi nhuận gộp danh định $\ge 42\%$:
   $$\text{Gross Margin} = \frac{\text{Contract Value} - (\text{Direct Consultant Salaries} + \text{Cloud/Infra Costs})}{\text{Contract Value}} \ge 42\%$$
2. **Quy Tắc SoD Deal-Desk Bất Biến (Separation of Duties Guardrail):**
   - Đơn vị kinh doanh (Sales Rep) không được phép tự phê duyệt đơn hàng hoặc báo giá có mức chiết khấu vượt quá **$10\%$** hoặc tổng giá trị hợp đồng (TCV) vượt quá **500.000.000 VND**.
   - Mọi báo giá vượt ngưỡng bắt buộc phải được chuyển tiếp qua Deal-Desk và có chữ ký số phê duyệt của Giám đốc Bán hàng (`sales_team.group_sale_manager`) và Giám đốc Tài chính trước khi gửi cho khách hàng.

---

## 3. Chiến Lược Gói Giải Pháp Hợp Nhất Tứ Trụ (Cross-Product Synergy Playbooks)

Doanh nghiệp không bán các sản phẩm rời rạc mà cung cấp **Gói Giải Pháp Chuyển Đổi Số Toàn Diện (Sovereign Transformation Suites)**, tạo sức mạnh cộng hưởng và doanh thu định kỳ bền vững:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                   CHUỖI GIÁ TRỊ GIAO THOA CỦA HỆ SINH THÁI TỨ TRỤ                       │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                        │
│     ┌─────────────────────┐                          ┌─────────────────────┐           │
│     │     INSILOS ERP     │                          │ VERTICAL RESILIENCE │           │
│     │  • Sổ cái VAS/IFRS  │◄──── Hợp đồng rủi ro ───►│  • Quản trị rủi ro  │           │
│     │  • Đơn hàng TCV/SO  │      đơn hàng & kiểm soát│  • Tuân thủ PDPD    │           │
│     │  • Quản lý WMS/MRP  │      mốc Activate Q-Gates│  • Cổng thuế quan   │           │
│     └──────────┬──────────┘                          └──────────┬──────────┘           │
│                │                                                │                      │
│                │ Bóc tách Timesheet & Hóa đơn                   │ Quét lỗ hổng CI/CD   │
│                │ RAG giải trình công nợ                         │ & Kiểm toán mã nguồn │
│                ▼                                                ▼                      │
│     ┌─────────────────────┐                          ┌─────────────────────┐           │
│     │       MOJO AI       │                          │     ZENCODE ENT     │           │
│     │  • Tác nhân tự chủ  │◄──── Tối ưu hóa suy luận ───►│  • Cụm AGY Fleet    │           │
│     │  • RAG triệt ảo giác│      kỹ nghệ đảo ngược mã│  • Tái cấu trúc     │           │
│     │  • Bóc tách thông   │      và kiểm thử tự động │  • 13 Council Gates │           │
│     │    minh OCR/Email   │                          │                     │           │
│     └─────────────────────┘                          └─────────────────────┘           │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### 3.1. Bốn Gói Giải Pháp Tích Hợp Chiến Lược (Packaged Synergy Solutions)

#### 1. Gói "Sovereign Enterprise Core" (ERP + GRC)
- **Đối Tượng:** Các tập đoàn tài chính, ngân hàng, bất động sản, chuỗi bán lẻ quy mô lớn.
- **Sức Mạnh Tích Hợp:** Insilos ERP đảm nhiệm toàn bộ quy trình kế toán VAS (Thông tư 200/133), lead-to-cash, mua hàng, kho bãi. Vertical Resilience kết nối trực tiếp vào ERP, kiểm soát rủi ro giao dịch theo thời gian thực (Real-time GRC Sentinel), tự động khóa các giao dịch vượt hạn mức rủi ro tín dụng và xuất báo cáo tuân thủ ISO/IEC 27001 và SOC 2.

#### 2. Gói "Autonomous Cognitive Operations" (ERP + Mojo AI)
- **Đối Tượng:** Các doanh nghiệp dịch vụ chuyên nghiệp, logistics, thương mại điện tử đa kênh.
- **Sức Mạnh Tích Hợp:** Toàn bộ dữ liệu chứng từ (Hóa đơn đầu vào, bảng kê timesheet gửi về `info@inno.ai.vn`, hợp đồng scan) được Mojo AI bóc tách thông minh, đối chiếu 3 chiều và tự động ghi sổ kế toán. Trợ lý Web Concierge trên `innoria.com` hỗ trợ khách hàng giải trình chi tiết từng dòng giờ công trên cổng portal.

#### 3. Gói "Legacy Clean-Core Modernization" (Zencode Ent + Insilos ERP)
- **Đối Tượng:** Doanh nghiệp có hệ thống phần mềm kế thừa cồng kềnh (SAP ECC, Oracle cũ, AS400, COBOL).
- **Sức Mạnh Tích Hợp:** Zencode Ent sử dụng phương pháp Biện chứng Hegelian và cụm AGY Fleet Swarm để phân tích AST, đảo ngược mã nguồn kế thừa (Clean Reverse-Engineering), trích xuất quy tắc nghiệp vụ và tái cấu trúc sang kiến trúc Odoo 20 LTS Clean Core hiện đại mà không làm gián đoạn vận hành liên tục.

#### 4. Gói "Resilient Intelligent Supply Chain" (ERP + GRC + Mojo AI + Mobile)
- **Đối Tượng:** Nhà máy sản xuất dược phẩm, hóa chất, chuỗi phân phối F&B.
- **Sức Mạnh Tích Hợp:** Ứng dụng di động `insilos_mobile` hỗ trợ công nhân quét mã vạch và chấm công định vị vệ tinh GPS; Vertical Resilience giám sát an toàn hóa chất GHS và tiêu chuẩn ESG CSRD; Insilos ERP điều độ sản xuất MRP II và tính giá thành đích thực.

---

## 4. Quản Trị Tích Hợp Đa Repository (Multi-Repository Governance Framework)

Doanh nghiệp duy trì cam kết **Độc lập Chủ quyền (Sovereign Isolation)** nhưng **Đồng bộ Hợp đồng Dữ liệu (Schema-Invariant Interoperability)** giữa 4 repositories:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        HỢP ĐỒNG GIAO TIẾP GIỮA CÁC REPOSITORIES                        │
├───────────────────────┬───────────────────────┬────────────────────────────────────────┤
│ Repository Gốc        │ Repository Đích       │ Giao Thức & Hợp Đồng Dữ Liệu           │
├───────────────────────┼───────────────────────┼────────────────────────────────────────┤
│ `/home/zen/O20`       │ `/home/zen/VerticalRisk`│ REST/JSON-RPC có chữ ký số HMAC-SHA256,│
│ (Insilos ERP Core)    │ (GRC Sentinel)        │ webhook thông báo sự kiện mốc nghiệm thu│
├───────────────────────┼───────────────────────┼────────────────────────────────────────┤
│ `/home/zen/O20`       │ `/home/zen/insilos_mobile`│ GraphQL / REST API qua JWT Token xác   │
│ (Insilos ERP Core)    │ (Mobile Operations)   │ thực kép, đồng bộ danh mục & timesheet │
├───────────────────────┼───────────────────────┼────────────────────────────────────────┤
│ `/home/zen/zencode-ent`│ `/home/zen/O20`       │ Council Gates CI/CD, phân tích AST tĩnh,│
│ (Developer Platform)  │ & `/VerticalRisk`     │ kiểm định an ninh và phòng vệ injection│
├───────────────────────┼───────────────────────┼────────────────────────────────────────┤
│ `/home/zen/O20`       │ `innoria.com` Public  │ JSON-RPC công khai, RAG Grounding API  │
│ (AL2C AI Concierge)   │ Website Visitors      │ kèm chứng chỉ trích dẫn không ảo giác  │
└───────────────────────┴───────────────────────┴────────────────────────────────────────┘
```

### Bốn Giới Hạn Kiến Trúc Bất Biến (Non-Negotiable Architecture Invariants):
1. **Phân Lập Tuyệt Đối Cơ Sở Dữ Liệu (Zero Cross-Database Coupling):** Mỗi dịch vụ sở hữu cơ sở dữ liệu riêng biệt. Nghiêm cấm mọi truy vấn SQL trực tiếp liên cơ sở dữ liệu (Cross-DB Raw SQL Queries). Mọi tương tác bắt buộc phải thông qua API hoặc Event Bus.
2. **Không Vượt Cổng Kiểm Định Giả (Zero-Fake-Pass Invariant):** Không bao giờ chấp nhận các bài kiểm thử giả định (mock rỗng, `assert True`). Mọi mã nguồn đưa vào sản xuất phải vượt qua bài kiểm tra thực tế trên môi trường giả lập chuẩn.
3. **Tuyệt Đối Không Để Lộ Dấu Vết Nền Tảng (Zero-Signature Branding):** Mọi giao diện, email, bảng kê, tài liệu xuất bản cho khách hàng tuyệt đối không chứa các chuỗi từ khóa của bên thứ ba ("Odoo", "OpenERP"), bảo toàn 100% nhận diện thương hiệu Innoria Enterprise.
4. **Bảo Mật Giao Dịch Đa Tiền Tệ (Multi-Currency Transaction Safety):** Toàn bộ giao dịch ghi nhận doanh thu và hóa đơn phải lưu vết tỷ giá quy đổi tại thời điểm phát sinh (`exchange_rate_snapshot`), bảo vệ toàn vẹn số liệu kiểm toán VAS.

---

## 5. Ma Trận Trách Nhiệm RACI Trong Chu Trình Dự Án (Enterprise RACI Matrix)

| Giai Đoạn & Nhiệm Vụ Trọng Yếu | Practice Principal | Solution Architect | Delivery Lead / PM | Senior Consultant | Technical Engineer | Client PM / Sponsor |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Pha 1: Prepare & Báo Giá Deal-Desk** | **A** | **R** | **C** | **I** | **I** | **C** |
| **Pha 2: Explore & Fit-to-Standard** | **I** | **A** | **C** | **R** | **C** | **R** |
| **Pha 3: Realize & Cấu Hình/Phát Triển** | **I** | **C** | **A** | **R** | **R** | **C** |
| **Thu Nhận Timesheet Email Tuần** | **I** | **I** | **A** (Duyệt) | **R** (Gửi) | **R** (Gửi) | **I** |
| **Lập Bảng Kê Giờ Công & Đối Soát** | **I** | **I** | **R** | **C** | **I** | **A** (Xác nhận) |
| **Pha 4: Deploy & Q-Gate Nghiệm Thu** | **A** | **C** | **R** | **R** | **R** | **A** |
| **Xuất Hóa Đơn VAT NĐ 70/2025** | **I** | **I** | **C** | **I** | **I** | **R** (Thanh toán) |
| **Pha 5: Run & Vận Hành Hỗ Trợ AMS** | **I** | **I** | **A** | **R** | **R** | **C** |

*(Chú thích: **R** = Responsible / Người thực hiện; **A** = Accountable / Người chịu trách nhiệm phê duyệt; **C** = Consulted / Người được tham vấn; **I** = Informed / Người được thông báo).*

---
*Văn bản ban hành bởi Ban Giám Đốc Khối Dịch Vụ Phần Mềm Doanh Nghiệp Innoria Enterprise.*
