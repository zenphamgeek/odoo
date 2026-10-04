# NGHIÊN CỨU KIẾN TRÚC ĐẶT TÊN THEO CHUẨN IBM
## (IBM Enterprise Data Architecture, IBM Industry Models & Carbon Design System)

**Tài liệu**: Nghiên cứu Chiến lược Tái định danh Toàn diện Hệ thống Insilos Enterprise  
**Phiên bản**: 1.0.0-ENTERPRISE  
**Cơ sở đối chiếu**: 
1. **IBM Industry Models (BDW / IIW / MDM)** — Chuẩn mô hình dữ liệu doanh nghiệp hàng đầu thế giới.
2. **IBM Maximo Asset Management & IBM Sterling SCM/OMS** — Chuẩn danh pháp chuỗi cung ứng & quản trị tài sản.
3. **IBM Carbon Design System 11** — Chuẩn UI/UX, Component & Design Tokens doanh nghiệp.

---

## 1. Bối Cảnh & Sự Cần Thiết Của Việc Đổi Tên Theo Chuẩn IBM

### 1.1 Khuyết tật kiến trúc của danh pháp cũ (Legacy Genesis Footprints)
Hệ thống hiện tại mang nhiều tàn dư lịch sử từ 20 năm trước (TinyERP $\rightarrow$ OpenERP $\rightarrow$ Odoo):
- **Tiền tố `res_*` ("Resource")**: Đặt tên mù mờ (`res_partner`, `res_users`, `res_company`, `res_currency`). Trong một ERP hiện đại, "partner" bị nhồi nhét hỗn tạp giữa cá nhân, doanh nghiệp, nhà cung cấp, khách hàng, địa chỉ giao hàng và liên hệ.
- **Tiền tố `ir_*` ("Information Repository")**: Gây nhầm lẫn giữa dữ liệu nghiệp vụ và siêu dữ liệu hệ thống (`ir_attachment`, `ir_model`, `ir_ui_view`, `ir_act_window`).
- **Từ viết tắt chắp vá**: `mrp_*` (Manufacturing), `pos_*` (Point of Sale), `hr_*` (Human Resources), `fleet_*` thiếu tính nhất quán của một chuẩn kiến trúc doanh nghiệp lớn.

### 1.2 Triết lý đặt tên của IBM (The IBM Enterprise Lexicon)
Trong các bộ chuẩn công nghiệp của IBM (**IBM InfoSphere Master Data Management**, **IBM Industry Models for Banking & Insurance - BDW/IIW**, **IBM Maximo**, **IBM Sterling**):
1. **Tính định danh thực thể thực tế (Noun-First Entity Specificity)**: Tên thực thể phản ánh chính xác bản chất kinh doanh trong thế giới thực, không dùng tên kỹ thuật chung chung.
2. **Mô hình Party Pattern**: Mọi đối tượng tham gia tương tác kinh doanh đều thuộc thực thể trừu tượng **`Party`**, được phân loại và định danh vai trò qua **`Party Role`** (`Customer`, `Supplier`, `Carrier`, `Employee`) và **`Party Classification`**.
3. **Phân tách ranh giới rõ ràng (Bounded Context Separation)**: Siêu dữ liệu hệ thống mang tiền tố `system_*` hoặc `metadata_*`, hoàn toàn tách bạch với dữ liệu nghiệp vụ `party_*`, `catalog_*`, `procurement_*`, `order_*`, `finance_*`.

---

## 2. Quy Chuẩn Đặt Tên 4 Tầng Theo Chuẩn IBM

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        IBM ENTERPRISE NAMING TAXONOMY MATRIX                           │
└────────────────────────────────────────────────────────────────────────────────────────┘
  [Tầng 1: Database DDL]        ──▶  snake_case, danh từ số ít, tiền tố phân hệ rõ ràng.
                                     (e.g., party_master, party_classification, sales_order)

  [Tầng 2: Python ORM (_name)]   ──▶  dot.notation, phân cấp Domain.Subdomain.Entity.
                                     (e.g., party.master, party.classification, order.header)

  [Tầng 3: QWeb / Views]         ──▶  XML IDs & Action IDs mang namespace doanh nghiệp.
                                     (e.g., view_party_master_form, action_party_classification)

  [Tầng 4: Frontend OWL 3 / UI]  ──▶  PascalCase cho Components theo chuẩn IBM Carbon 11.
                                     (e.g., PartyClassificationTable, PartyHeaderView, FilterChip)
```

---

## 3. Bảng Đối Chiếu Danh Pháp Rosetta Stone: Genesis $\rightarrow$ IBM Standard

### 3.1 Phân Hệ Master Data (Đối tác, Tổ chức, Danh tính)

| Legacy Genesis Model | Legacy DB Table | **IBM Enterprise Model** | **IBM Physical Table** | **IBM UI / Business Term** |
| :--- | :--- | :--- | :--- | :--- |
| `res.partner` | `res_partner` | **`party.master`** *(hoặc `party.entity`)* | **`party_master`** | **Business Partner / Involved Party** |
| `res.partner.category` | `res_partner_category` | **`party.classification`** | **`party_classification`** | **Party Classification / Tags** |
| `res.company` | `res_company` | **`organization.unit`** | **`organization_unit`** | **Legal Entity / Operating Unit** |
| `res.users` | `res_users` | **`identity.user`** | **`identity_user`** | **System User / Operator Identity** |
| `res.currency` | `res_currency` | **`finance.currency`** | **`finance_currency`** | **Currency Master** |
| `res.country` | `res_country` | **`geography.country`** | **`geography_country`** | **Country Master** |

### 3.2 Phân Hệ Vật Tư, Sản Phẩm & Danh Mục (IBM Maximo / Sterling Pattern)

| Legacy Genesis Model | Legacy DB Table | **IBM Enterprise Model** | **IBM Physical Table** | **IBM UI / Business Term** |
| :--- | :--- | :--- | :--- | :--- |
| `product.template` | `product_template` | **`catalog.item`** | **`catalog_item`** | **Item Master / Product Catalog** |
| `product.product` | `product_product` | **`catalog.sku`** *(Item Instance)* | **`catalog_sku`** | **Stock Keeping Unit (SKU)** |
| `product.category` | `product_category` | **`catalog.classification`** | **`catalog_classification`** | **Merchandise Hierarchy / Class** |
| `product.pricelist` | `product_pricelist` | **`pricing.schedule`** | **`pricing_schedule`** | **Pricing Agreement / Schedule** |

### 3.3 Phân Hệ Mua Hàng & Cung Ứng (IBM Sterling / Maximo Procurement)

| Legacy Genesis Model | Legacy DB Table | **IBM Enterprise Model** | **IBM Physical Table** | **IBM UI / Business Term** |
| :--- | :--- | :--- | :--- | :--- |
| `purchase.order` | `purchase_order` | **`procurement.order`** | **`procurement_order`** | **Purchase Order / Agreement** |
| `purchase.order.line` | `purchase_order_line` | **`procurement.order.line`** | **`procurement_order_line`** | **Purchase Order Item** |
| `purchase.requisition`| `purchase_requisition`| **`procurement.requisition`**| **`procurement_requisition`**| **Purchase Requisition (PR)** |

### 3.4 Phân Hệ Bán Hàng & Đơn Đặt Hàng (IBM Sterling Order Management)

| Legacy Genesis Model | Legacy DB Table | **IBM Enterprise Model** | **IBM Physical Table** | **IBM UI / Business Term** |
| :--- | :--- | :--- | :--- | :--- |
| `sale.order` | `sale_order` | **`order.header`** *(hoặc `sales.order`)*| **`order_header`** | **Sales Order / Commitment** |
| `sale.order.line` | `sale_order_line` | **`order.line`** | **`order_line`** | **Sales Order Line Item** |
| `crm.lead` | `crm_lead` | **`opportunity.lead`** | **`opportunity_lead`** | **Sales Opportunity / Lead** |

### 3.5 Phân Hệ Kho Vận & Chuỗi Cung Ứng (IBM Sterling Logistics)

| Legacy Genesis Model | Legacy DB Table | **IBM Enterprise Model** | **IBM Physical Table** | **IBM UI / Business Term** |
| :--- | :--- | :--- | :--- | :--- |
| `stock.picking` | `stock_picking` | **`logistics.transfer`** | **`logistics_transfer`** | **Shipment / Goods Movement** |
| `stock.move` | `stock_move` | **`logistics.movement`** | **`logistics_movement`** | **Inventory Transaction** |
| `stock.warehouse` | `stock_warehouse` | **`facility.warehouse`** | **`facility_warehouse`** | **Distribution Center / Facility** |
| `stock.location` | `stock_location` | **`facility.location`** | **`facility_location`** | **Storage Bin / Storage Location** |

### 3.6 Phân Hệ Sản Xuất & Điều Độ Máy Móc (IBM Maximo Manufacturing)

| Legacy Genesis Model | Legacy DB Table | **IBM Enterprise Model** | **IBM Physical Table** | **IBM UI / Business Term** |
| :--- | :--- | :--- | :--- | :--- |
| `mrp.production` | `mrp_production` | **`manufacturing.workorder`** | **`manufacturing_workorder`**| **Work Order (WO) / Job** |
| `mrp.bom` | `mrp_bom` | **`manufacturing.bom`** | **`manufacturing_bom`** | **Bill of Materials (Engineering BOM)**|
| `mrp.workcenter` | `mrp_workcenter` | **`facility.workcenter`** | **`facility_workcenter`** | **Work Center / Machine Routing** |

### 3.7 Phân Hệ Tài Chính & Kế Toán Doanh Nghiệp (IBM General Ledger)

| Legacy Genesis Model | Legacy DB Table | **IBM Enterprise Model** | **IBM Physical Table** | **IBM UI / Business Term** |
| :--- | :--- | :--- | :--- | :--- |
| `account.move` | `account_move` | **`finance.transaction`** | **`finance_transaction`** | **Financial Document / Journal Entry**|
| `account.move.line` | `account_move_line` | **`finance.entry.line`** | **`finance_entry_line`** | **General Ledger Line** |
| `account.account` | `account_account` | **`finance.gl_account`** | **`finance_gl_account`** | **Chart of Accounts (G/L Account)** |
| `account.journal` | `account_journal` | **`finance.journal`** | **`finance_journal`** | **Accounting Register / Journal** |

### 3.8 Phân Hệ Siêu Dữ Liệu Hệ Thống (System Metadata & Architecture)

| Legacy Genesis Model | Legacy DB Table | **IBM Enterprise Model** | **IBM Physical Table** | **IBM UI / Business Term** |
| :--- | :--- | :--- | :--- | :--- |
| `ir.attachment` | `ir_attachment` | **`system.attachment`** | **`system_attachment`** | **Managed Content Asset / Document**|
| `ir.model` | `ir_model` | **`metadata.entity`** | **`metadata_entity`** | **Entity Definition Catalog** |
| `ir.model.fields` | `ir_model_fields` | **`metadata.attribute`** | **`metadata_attribute`** | **Attribute Schema Specification** |
| `ir.ui.view` | `ir_ui_view` | **`metadata.view`** | **`metadata_view`** | **UI View Specification** |
| `ir.ui.menu` | `ir_ui_menu` | **`metadata.navigation`** | **`metadata_navigation`** | **Enterprise Navigation Menu** |

---

## 4. Ứng Dụng Thực Tế Cho Cohort 1: `res.partner.category`

Theo chuẩn IBM Industry Models & Maximo:
- **Tên cũ (Genesis)**: `res.partner.category` (Bảng `res_partner_category`)
- **Tên theo chuẩn IBM**:
  * **Option 1 (IBM Master Data Management - MDM Standard)**:
    - Model: **`party.classification`**
    - Bảng vật lý: **`party_classification`**
    - Bảng M2M: **`party_classification_rel`**
    - Field name: `classification_ids` (hoặc giữ `category_id` qua aliasing)
    - UI String: `"Party Classification"` (Nhãn tiếng Việt: *"Phân loại Đối tác Doanh nghiệp"*)
  * **Option 2 (IBM Maximo / Carbon Pragmatic)**:
    - Model: **`party.category`**
    - Bảng vật lý: **`party_category`**
    - Bảng M2M: **`party_category_rel`**
    - UI String: `"Business Partner Category"`

### Chiến lược tích hợp với bộ công cụ AST-Grep & PostgreSQL View Facade:
1. **Tại PostgreSQL**:
   ```sql
   ALTER TABLE insilos_partner_category RENAME TO party_classification;
   CREATE OR REPLACE VIEW res_partner_category AS SELECT * FROM party_classification;
   CREATE OR REPLACE VIEW insilos_partner_category AS SELECT * FROM party_classification;
   ```
   *(Cả 2 view cũ đều truyền thẳng xuống `party_classification`, tương thích 100% 3 thế hệ: Genesis $\rightarrow$ Insilos v1 $\rightarrow$ IBM Standard).*
2. **Tại Python ORM**:
   Định nghĩa class:
   ```python
   class PartyClassification(models.Model):
       _name = 'party.classification'
       _description = 'Party Classification Scheme'
       _table = 'party_classification'
   ```
   Đồng thời qua `odoo/orm_sovereign.py`, hệ thống tự động mapping:
   `'res.partner.category': 'party.classification'`
   `'insilos.partner.category': 'party.classification'`

---

## 5. Lộ Trình Triển Khai Danh Pháp IBM Theo Bounded Cohorts

| Giai Đoạn | Cohort | Đối Tượng Genesis $\rightarrow$ IBM | Công Nghệ Áp Dụng |
| :--- | :--- | :--- | :--- |
| **P1** | **Cohort 1 (Tags & Classes)** | `res.partner.category` $\rightarrow$ **`party.classification`** | AST-Grep + Updatable Views (Đã chạy thử nghiệm) |
| **P2** | **Cohort 2 (System Content)** | `ir.attachment` $\rightarrow$ **`system.attachment`** | AST-Grep + Binary Storage Verification |
| **P3** | **Cohort 3 (Business Partner)** | `res.partner` $\rightarrow$ **`party.master`** | Pre-boot Metadata Injection + M2M View Bridges |
| **P4** | **Cohort 4 (Catalog & Items)** | `product.template` $\rightarrow$ **`catalog.item`** | Inventory Movement AST-Grep Rewriter |
| **P5** | **Cohort 5 (Procure-to-Pay)** | `purchase.order` $\rightarrow$ **`procurement.order`** | Vendor Bill / PR Dual View Architecture |
| **P6** | **Cohort 6 (Order-to-Cash)** | `sale.order` $\rightarrow$ **`order.header`** | Sales Pipeline & Quotation Refactoring |
| **P7** | **Cohort 7 (Financial Ledger)** | `account.move` $\rightarrow$ **`finance.transaction`** | Circular 78 / TT200 Compliance Invariance |

---

## 6. Kết Luận & Khuyến Nghị

1. **Đồng bộ hóa triệt để**: Sử dụng danh pháp IBM giúp Insilos Platform thoát hẳn khỏi định kiến "một bản mod Odoo", vươn lên thành một giải pháp ERP đẳng cấp quốc tế sánh ngang với SAP và IBM Enterprise Solutions.
2. **Không gây đứt gãy**: Nhờ phát kiến **PostgreSQL Updatable View Facade** kết hợp **AST-Grep Sequential PDCA**, chúng ta có thể áp dụng toàn bộ bảng danh pháp IBM này vào database thực tế mà không làm gián đoạn bất kỳ dòng code legacy nào.
