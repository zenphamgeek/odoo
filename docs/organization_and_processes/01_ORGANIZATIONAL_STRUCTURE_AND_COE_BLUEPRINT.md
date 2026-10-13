# Insilos & Innoria — Enterprise Software Services Organizational Blueprint
## Kiến Trúc Tổ Chức Ma Trận & Trung Tâm Xuất Sắc (CoE) Cho Doanh Nghiệp Dịch Vụ & Sản Phẩm Phần Mềm

> **Classification:** Sovereign Enterprise Standard • **Version:** 2.0 (Master Blueprint)  
> **Applicable Entity:** Innoria / Insilos Software Services Corporation  
> **Core Product Lines:** Insilos ERP • Vertical Resilience • Mojo AI • Zencode Ent  

---

## 1. Tầm Nhìn Chiến Lược & Mô Hình Kinh Doanh Kép (Dual-Engine Business Model)

Công ty vận hành theo mô hình **Sản phẩm kết hợp Dịch vụ Chuyên gia Cao cấp (Product-Led & High-Value Professional Services)**:
- **Sản phẩm (Products):** 4 nền tảng phần mềm có tính chủ quyền cao (Sovereign Software Stack), đóng gói chuẩn hóa, có thể triển khai SaaS đa người thuê (Multi-tenant Cloud) hoặc On-Premise/Private Cloud cho các tập đoàn lớn.
- **Dịch vụ (Services):** Tư vấn chiến lược số hóa, triển khai giải pháp theo chuẩn SAP Activate, phát triển giải pháp tích hợp may đo (Custom Extensions), hiện đại hóa hệ thống kế thừa (Legacy Modernization), đào tạo và dịch vụ quản trị vận hành 24/7 (AMS).

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        INNORIA / INSILOS ENTERPRISE ECOSYSTEM                          │
├────────────────────────┬────────────────────────┬─────────────────────┬────────────────┤
│      INSILOS ERP       │  VERTICAL RESILIENCE   │       MOJO AI       │  ZENCODE ENT   │
│  (System of Record)    │  (System of Assurance) │(System of Cognition)│  (System of    │
│                        │                        │                     │  Engineering)  │
├────────────────────────┴────────────────────────┴─────────────────────┴────────────────┤
│                           PRACTICE CENTERS OF EXCELLENCE (CoEs)                        │
│   • Enterprise ERP CoE   • Risk & Compliance CoE   • Agentic AI CoE   • Modernization  │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                      CROSS-FUNCTIONAL DELIVERY & PROJECT MANAGEMENT                    │
│   • PMO Core • Solution Architecture • Delivery Streams (SAP Activate) • QA & Security │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                       SHARED ENTERPRISE GOVERNANCE & OPERATIONS                        │
│   • Deal-Desk & Legal (PDPD) • Finance & VAS Invoicing • DevOps & SRE Fleet Infrastructure│
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Mô Hình Tổ Chức Ma Trận (Matrix Organizational Structure)

Mô hình kết hợp giữa **Quản lý theo Chuyên môn (Vertical Practice Centers of Excellence)** và **Quản lý theo Dự án Khách hàng (Horizontal Project Delivery)**:

```
                           ┌───────────────────────────┐
                           │   CHIEF EXECUTIVE OFFICER │
                           │           (CEO)           │
                           └─────────────┬─────────────┘
                                         │
       ┌──────────────────┬──────────────┴──────────────┬──────────────────┐
       │                  │                             │                  │
┌──────┴──────┐    ┌──────┴──────┐               ┌──────┴──────┐    ┌──────┴──────┐
│  CHIEF      │    │  CHIEF      │               │  CHIEF      │    │  CHIEF RISK │
│  TECHNOLOGY │    │  OPERATING  │               │  FINANCIAL  │    │  & DATA OFF.│
│  OFFICER    │    │  OFFICER    │               │  OFFICER    │    │  (CRO/DPO)  │
│  (CTO)      │    │  (COO)      │               │  (CFO)      │    │(Decree 13)  │
└──────┬──────┘    └──────┬──────┘               └──────┬──────┘    └─────────────┘
       │                  │                             │
       │                  ├──────────────────────┐      └──────────────┐
       │                  │                      │                     │
┌──────▼──────┐    ┌──────▼──────┐        ┌──────▼──────┐       ┌──────▼──────┐
│  R&D & CORE │    │  DELIVERY   │        │ COMMERCIAL  │       │ FINANCE &   │
│  PLATFORMS  │    │  PMO OFFICE │        │ & PRE-SALES │       │ COMPLIANCE  │
│  (SWARM)    │    │             │        │ (DEAL-DESK) │       │ (VAS / TAX) │
└──────┬──────┘    └──────┬──────┘        └─────────────┘       └─────────────┘
       │                  │
       ├──────────────────┼────────────────────────────────────────────────────┐
       ▼                  ▼                                                    ▼
┌─────────────┐    ┌─────────────┐                                      ┌─────────────┐
│ ERP CoE     │    │ GRC CoE     │                                      │ AI & SWARM  │
│ (Insilos)   │    │ (Vertical)  │                                      │ (Mojo/Zen)  │
└──────┬──────┘    └──────┬──────┘                                      └──────┬──────┘
       │                  │                                                    │
       └──────────────────┴──────────────────┬─────────────────────────────────┘
                                             │ (Phân bổ nhân lực vào dự án)
                                             ▼
                             ┌───────────────────────────────┐
                             │    PROJECT DELIVERY TEAMS     │
                             │  • Dự án Khách hàng A (ERP)  │
                             │  • Dự án Khách hàng B (GRC)  │
                             │  • Dự án Khách hàng C (AI)   │
                             │  • Dự án Enterprise All-in-1 │
                             └───────────────────────────────┘
```

---

## 3. Chi Tiết 4 Trung Tâm Xuất Sắc (Practice Centers of Excellence - CoEs)

### 3.1. Enterprise ERP CoE (Insilos ERP Practice)
- **Trọng tâm Sản phẩm:** Nền tảng Insilos ERP (Odoo 20 LTS Sovereign Fork), Insilos Mobile Client.
- **Vai trò Chính:**
  - **Practice Director / Principal Architect:** Định hướng kiến trúc phân hệ, kiểm soát clean-core, không làm biến dạng mã nguồn lõi.
  - **Lead Functional Consultants:**
    - *Financials & Costing Lead:* Chuyên gia chuẩn mực kế toán Việt Nam (VAS Circular 200/133, IFRS), thuế VAT, khấu hao TSCĐ, tính giá thành phân bổ tự động.
    - *Supply Chain & Logistics Lead:* Mua hàng, Quản trị kho đa địa điểm, WMS vạch mã, Landed Cost (chi phí đích danh), Hải quan xuất nhập khẩu.
    - *Manufacturing (MRP II) Lead:* Định mức nguyên vật liệu (BOM), Công đoạn sản xuất (Work Centers), Lệnh sản xuất (MO), Kiểm soát chất lượng (QC).
    - *HCM & Payroll Lead:* Nhân sự, Chấm công vân tay/GPS, Thuế TNCN (PIT), Bảo hiểm xã hội theo mức trần 2026.
  - **Technical Engineers / OWL 2 Frontend Developers:** Xây dựng component giao diện phản ứng (OWL 2), SCSS dark-mode semantic token, báo cáo QWeb động.

### 3.2. Governance, Risk & Compliance CoE (Vertical Resilience Practice)
- **Trọng tâm Sản phẩm:** Nền tảng `VerticalRisk`, Risk Engine, Audit Packs, Trade/Chemicals/HSE/ESG Bridges.
- **Vai trò Chính:**
  - **GRC Solution Director:** Am hiểu khung quản trị rủi ro quốc tế (COSO, ISO 31000) và các quy định pháp luật ngành đặc thù.
  - **Compliance & Regulatory Auditor:**
    - *Trade Compliance Specialist:* Hệ thống mã HS Tariff, phân loại hàng hóa, kiểm tra C/O (chứng nhận xuất xứ), kiểm soát xuất nhập khẩu tự động.
    - *Chemical & Safety Consultant:* Quản lý an toàn hóa chất (GHS, REACH), bảng chỉ dẫn an toàn SDS, kiểm soát lưu trữ hóa chất nguy hại.
    - *HSE & ESG Carbon Specialist:* Đo lường kiểm kê khí nhà kính (Scope 1, 2, 3), tính toán dấu chân carbon chuỗi cung ứng, lập báo cáo phát triển bền vững theo chuẩn CSRD/GRI.
  - **IDP (Intelligent Document Processing) Specialist:** Tích hợp mô hình thị giác máy học và OCR để bóc tách chứng từ hải quan, vận đơn, phiếu kiểm nghiệm.

### 3.3. Agentic AI & Automation CoE (Mojo AI Practice)
- **Trọng tâm Sản phẩm:** Mojo AI Engine, Multi-Agent Swarms, Enterprise RAG Pipeline, Vector Embeddings.
- **Vai trò Chính:**
  - **AI Research & Agent Architect:** Thiết kế kiến trúc Multi-Agent phối hợp, phân rã mục tiêu (Goal Decomposition), định tuyến công cụ (Tool Routing).
  - **RAG & Knowledge Engineer:** Xây dựng Knowledge Graph, xử lý dữ liệu phi cấu trúc, kỹ thuật sinh văn bản có căn cứ (Grounding & Claim Atom Verification) để triệt tiêu ảo giác (Zero AI Slop).
  - **Mojo Systems Engineer:** Biên dịch các thuật toán suy luận cục bộ bằng ngôn ngữ Modular Mojo, tối ưu hóa độ trễ tính toán xuống mức micro-giây trên CPU/GPU on-premise.

### 3.4. Platform Modernization & DevSecOps CoE (Zencode Ent Practice)
- **Trọng tâm Sản phẩm:** Zencode Ent Autonomous Fleet Router, Clean-Room Reverse Engineering Framework, Council Gates Runner.
- **Vai trò Chính:**
  - **Fleet Infrastructure Architect:** Quản trị cụm phân tán đa tài khoản (Multi-Account Swarm), điều phối tự động giữa các mô hình (Claude Opus, Gemini Pro/Flash), kiểm soát hạn ngạch và tự phục hồi (Circuit Breaker).
  - **Code Modernization Specialist:** Chuyên gia dịch chuyển mã kế thừa (COBOL/ABAP/Legacy monoliths $\rightarrow$ Modern Python/TypeScript/Microservices) áp dụng biện chứng Hegelian (Thesis $\rightarrow$ Antithesis $\rightarrow$ Synthesis).
  - **DevSecOps & Reliability Engineer (SRE):** Đảm bảo an toàn bảo mật AST, kiểm tra rò rỉ danh tính mã nguồn (0-Signature), kiểm soát tính bất biến lược đồ cơ sở dữ liệu (PostgreSQL Schema Invariance).

---

## 4. Ma Trận Trách Nhiệm RACI Trong Vận Hành Doanh Nghiệp

| Giai đoạn / Quy trình Vận hành | Executive / Board | Deal-Desk / Sales | CoE Leads | Project PMO | R&D / DevSecOps | DPO / Pháp chế |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **1. Lead Ingestion & Qualification** | I | **A / R** | C | I | I | I |
| **2. Solution Discovery & Value Architecture** | I | A | **R** | C | C | I |
| **3. CPQ, Báo giá, SOW & Deal-Desk Approval** | C (nếu >500M) | **A / R** | C | C | I | C (Nghị định 13) |
| **4. Ký kết Hợp đồng & Pháp lý (DPA/SLA)** | **A** | R | I | I | I | **R** |
| **5. Kick-off & Khởi tạo Dự án (Prepare)** | I | C | C | **A / R** | C | I |
| **6. Khảo sát & Khớp mẫu (Explore - Fit to Standard)**| I | I | **A / R** | R | C | C |
| **7. Phát triển & Kiểm thử (Realize - CI/CD Gates)** | I | I | C | R | **A / R** | C |
| **8. Nghiệm thu & Chuyển giao (Deploy & Cutover)** | I | C | C | **A / R** | R | I |
| **9. Xuất hóa đơn NĐ 70 & Đối soát Thanh toán** | I | C | I | C | I | **A / R (Kế toán)** |
| **10. Vận hành AMS 24/7 & Nâng cấp (Run)** | I | C | C | C | **A / R** | I |

*Chú thích:*
- **R (Responsible):** Người trực tiếp thực hiện công việc.
- **A (Accountable):** Người chịu trách nhiệm phê duyệt cuối cùng và giải trình kết quả.
- **C (Consulted):** Người được tham vấn chuyên môn hai chiều.
- **I (Informed):** Người được thông báo kết quả cập nhật một chiều.

---

## 5. Chính Sách Quản Trị Nhân Lực & Tỷ Lệ Sử Dụng Tư Vấn (Consulting Utilization Policy)

1. **Phân Cấp Chức Danh (Consultant Career Ladder & Rate Card):**
   - **Principal Consultant / Practice Lead:** Rate card 2,500,000 – 4,000,000 VND/giờ. Đảm nhận định trúc giải pháp, cố vấn cấp C-level, giải quyết khủng hoảng kỹ thuật.
   - **Senior Functional / Technical Consultant:** Rate card 1,500,000 – 2,500,000 VND/giờ. Chủ trì các phân hệ chuyên sâu, bảo vệ giải pháp tại phân đoạn Fit-to-Standard.
   - **Consultant / Implementer:** Rate card 800,000 – 1,500,000 VND/giờ. Cấu hình hệ thống, đào tạo người dùng cuối, lập trình chức năng nghiệp vụ chuẩn.
   - **Associate Consultant / Junior Engineer:** Rate card 500,000 – 800,000 VND/giờ. Chuẩn bị dữ liệu mẫu, viết kịch bản kiểm thử, hỗ trợ tài liệu bàn giao.

2. **Chỉ Tiêu Hiệu Suất Tận Dụng (Billable Utilization Targets):**
   - Junior/Associate: **$\ge 85\%$** thời gian tính phí cho khách hàng (Billable Hours).
   - Mid/Senior Consultant: **$\ge 75\%$** Billable Hours (25% dành cho R&D module và hỗ trợ Pre-sales).
   - Principal / Practice Lead: **$\ge 50\%$** Billable Hours (50% cho kiến trúc sản phẩm lõi, cố vấn deal lớn và đào tạo nội bộ).
