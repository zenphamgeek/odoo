# BẢN ĐỀ XUẤT THAY THẾ CODE TEXT TOÀN DIỆN (CODE TEXT REPLACEMENT CATALOG)
## Chuẩn Hóa Kiến Trúc Dữ Liệu Doanh Nghiệp Theo Chuẩn IBM (IBM Enterprise Data Architecture)
### Chiến Lược Refactor Độc Lập Sovereign Hard Fork Không Vùng Cấm (No Forbidden Zones)

**Mã tài liệu**: `INSILOS-PROPOSAL-CODE-TEXT-01`  
**Dự án**: Insilos Enterprise Platform 20.0 (Genesis Fork)  
**Phạm vi áp dụng**: 4 Tầng Toàn Diện (PostgreSQL DDL $\rightarrow$ Python ORM $\rightarrow$ QWeb/XML Views $\rightarrow$ OWL 3 / WebClient JS)  
**Mục tiêu**: Loại bỏ triệt để 100% tàn dư danh pháp cũ (Legacy Genesis Footprints: `res_*`, `ir_*`, `product_*`, `purchase_*`, `sale_*`, `stock_*`, `mrp_*`, `account_*`) và thiết lập hệ thống định danh chuẩn công nghiệp theo IBM Industry Models (BDW/IIW), IBM Maximo Asset Management, IBM Sterling Supply Chain, và Carbon Design System 11.

---

## 1. NGUYÊN TẮC THIẾT KẾ & BẢO VỆ HỆ THỐNG (ARCHITECTURAL GUARDRAILS)

Để thực thi việc thay thế code text mà **không gây đứt gãy hệ thống (Zero Breakage)** và **không mất mát dữ liệu (Zero Data Loss)**, toàn bộ quá trình tuân thủ 4 nguyên tắc bất biến:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        4-LAYER ZERO-BREAKAGE MIGRATION PARADIGM                        │
└────────────────────────────────────────────────────────────────────────────────────────┘

  [1. Database Layer]     Physical Table Rename (ALTER TABLE)
                          + Sequence Rebind (ALTER SEQUENCE)
                          + PostgreSQL Updatable Compatibility View (CREATE OR REPLACE VIEW)
                          ──▶ Bảo đảm mọi câu lệnh SQL legacy vẫn ghi đọc thông suốt 100%.

  [2. Metadata Layer]     Pre-Boot Metadata Injection qua SQL:
                          Cập nhật ir_model, ir_model_fields, ir_ui_view, ir_act_window, ir_model_data
                          ──▶ Registry của ORM nạp ngay Model mới, không tạo bảng rỗng mới.

  [3. Codebase Layer]     AST-Grep Structural Pattern Replacement:
                          Cập nhật đồng thời _name, _table, comodel_name, relation, field references.
                          ──▶ Chuẩn hóa code theo IBM Enterprise Syntax.

  [4. Compatibility Layer] Python Alias & Proxy Shim:
                          Tạo dynamically generated alias class trỏ về Model mới
                          ──▶ Module con của bên thứ ba gọi self.env['legacy.model'] vẫn hoạt động bình thường.
```

---

## 2. MA TRẬN 10 BOUNDED COHORTS THAY THẾ CODE TEXT

Hệ thống được phân rã thành 10 Bounded Cohorts thực thi tuần tự theo chu trình PDCA khép kín:

| Cohort | Domain Phân Hệ | Legacy Genesis Model | New IBM Enterprise Model | Physical Table Name | Rủi ro | Thứ tự |
| :--- | :--- | :--- | :--- | :--- | :---: | :---: |
| **01** | Master Data: Tags & Class | `res.partner.category` | **`party.classification`** | `party_classification` | Thấp | **1** (Đã thử nghiệm SQL) |
| **02** | System Metadata: Files | `ir.attachment` | **`system.attachment`** | `system_attachment` | Trung bình | **2** |
| **03** | Master Data: Company | `res.company` | **`organization.unit`** | `organization_unit` | Cao | **3** |
| **04** | Master Data: Business Partner | `res.partner` | **`party.master`** | `party_master` | Rất cao | **4** |
| **05** | Catalog & Materials | `product.template` / `.product` | **`catalog.item`** / **`catalog.sku`** | `catalog_item` / `catalog_sku` | Rất cao | **5** |
| **06** | Procurement & SCM | `purchase.order` / `.line` | **`procurement.order`** / **`.line`** | `procurement_order` | Cao | **6** |
| **07** | Order Management | `sale.order` / `.line` | **`order.header`** / **`order.line`** | `order_header` / `order_line` | Cao | **7** |
| **08** | Logistics & Warehouse | `stock.picking` / `stock.move` | **`logistics.transfer`** / **`.movement`** | `logistics_transfer` | Rất cao | **8** |
| **09** | Manufacturing Execution | `mrp.production` / `mrp.bom` | **`manufacturing.order`** / **`.bom`** | `manufacturing_order` | Cao | **9** |
| **10** | Financial General Ledger | `account.move` / `.line` | **`finance.journal.entry`** / **`.line`** | `finance_journal_entry` | Rất cao | **10** |

---

## 3. BẢNG CHI TIẾT ĐỀ XUẤT THAY THẾ CODE TEXT TỪNG COHORT

### COHORT 01: MASTER DATA — PARTNER CLASSIFICATION & TAGS
*Trạng thái: Đã hoàn tất kiểm thử vật lý DDL và Updatable View trên PostgreSQL `odoo20_dev`.*

#### 3.1.1 Tầng 1: Database DDL & SQL
```sql
-- 1. Đổi tên bảng vật lý và sequence
ALTER TABLE res_partner_category RENAME TO party_classification;
ALTER TABLE res_partner_res_partner_category_rel RENAME TO party_classification_rel;
ALTER SEQUENCE res_partner_category_id_seq RENAME TO party_classification_id_seq;
ALTER TABLE party_classification ALTER COLUMN id SET DEFAULT nextval('party_classification_id_seq'::regclass);

-- 2. Tạo Updatable Compatibility View cho phép write-through
CREATE OR REPLACE VIEW res_partner_category AS SELECT * FROM party_classification;
CREATE OR REPLACE VIEW res_partner_res_partner_category_rel AS SELECT * FROM party_classification_rel;
```

#### 3.1.2 Tầng 2: Python ORM Models (`odoo/addons/base/models/res_partner.py`)
| Vị trí Code / File | Legacy Genesis Code Text | Proposed IBM Replacement Code Text | Mục đích |
| :--- | :--- | :--- | :--- |
| `models/res_partner.py:227` | `_name = 'res.partner.category'` | `_name = 'party.classification'` | Định danh Model theo IBM Party Pattern |
| `models/res_partner.py:228` | *(không khai báo `_table`)* | `_table = 'party_classification'` | Khóa chặt bảng vật lý mới |
| `models/res_partner.py:237` | `parent_id = fields.Many2one('res.partner.category', ...)` | `parent_id = fields.Many2one('party.classification', ...)` | Quan hệ phân cấp cây thư mục |
| `models/res_partner.py:238` | `child_ids = fields.One2many('res.partner.category', 'parent_id', ...)` | `child_ids = fields.One2many('party.classification', 'parent_id', ...)` | Danh sách thẻ con |
| `models/res_partner.py:242` | `partner_ids = fields.Many2many('res.partner', column1='category_id', column2='partner_id', relation='res_partner_res_partner_category_rel')` | `party_ids = fields.Many2many('party.master', column1='classification_id', column2='party_id', relation='party_classification_rel')` | Quan hệ M2M chuẩn IBM |
| `models/res_partner.py:339` | `category_id = fields.Many2many('res.partner.category', ...)` | `classification_ids = fields.Many2many('party.classification', relation='party_classification_rel', column1='party_id', column2='classification_id', string='Classifications')` | Đổi tên field trên đối tác |
| `models/res_partner.py` | *(bổ sung alias property)* | `category_id = classification_ids` | Giữ alias tương thích ngược mềm |

#### 3.1.3 Tầng 3: QWeb & XML Views (`odoo/addons/base/views/res_partner_views.xml`)
| File & Dòng | Legacy Genesis Code Text | Proposed IBM Replacement Code Text | Ghi chú |
| :--- | :--- | :--- | :--- |
| `res_partner_views.xml:510` | `<field name="model">res.partner.category</field>` | `<field name="model">party.classification</field>` | Tree View model binding |
| `res_partner_views.xml:527` | `<field name="model">res.partner.category</field>` | `<field name="model">party.classification</field>` | Form View model binding |
| `res_partner_views.xml:540` | `<field name="model">res.partner.category</field>` | `<field name="model">party.classification</field>` | Search View model binding |
| `res_partner_views.xml:557` | `<field name="res_model">res.partner.category</field>` | `<field name="res_model">party.classification</field>` | Window Action binding |
| `res_partner_views.xml:554` | `id="action_partner_category"` | `id="action_party_classification"` | Action Record ID |
| `res_partner_views.xml:566` | `id="menu_partner_category"` | `id="menu_party_classification"` | Menu Record ID |
| `res_partner_views.xml:210` | `<field name="category_id" widget="many2many_tags".../>` | `<field name="classification_ids" widget="many2many_tags".../>` | Giao diện form đối tác |

#### 3.1.4 Tầng 4: OWL 3 & WebClient JS
| Thành phần Web | Legacy Code Text | Proposed IBM Replacement | Ghi chú |
| :--- | :--- | :--- | :--- |
| Tag Input Field Component | `many2many_tags` | `CarbonTagCluster` / `many2many_tags` | Tích hợp styling IBM Carbon 2px |
| RPC Context Key | `context.get('category_id')` | `context.get('classification_id')` | Context passing |

---

### COHORT 02: SYSTEM METADATA — ATTACHMENTS & DIGITAL ASSETS
*Quy mô: ~2,400 điểm tham chiếu trong toàn bộ mã nguồn.*

#### 3.2.1 Tầng 1: Database DDL & SQL
```sql
ALTER TABLE ir_attachment RENAME TO system_attachment;
ALTER SEQUENCE ir_attachment_id_seq RENAME TO system_attachment_id_seq;
ALTER TABLE system_attachment ALTER COLUMN id SET DEFAULT nextval('system_attachment_id_seq'::regclass);

-- Updatable view cho phép ORM và các module ngoài ghi/đọc dữ liệu không gián đoạn
CREATE OR REPLACE VIEW ir_attachment AS SELECT * FROM system_attachment;
```

#### 3.2.2 Tầng 2: Python ORM Models (`odoo/addons/base/models/ir_attachment.py`)
| Legacy Code Text | Proposed IBM Replacement Code Text | Ghi chú |
| :--- | :--- | :--- |
| `_name = 'ir.attachment'` | `_name = 'system.attachment'` | Tách bạch metadata hệ thống |
| *(chưa có `_table`)* | `_table = 'system_attachment'` | Khóa cứng bảng vật lý mới |
| `res_model = fields.Char(...)` | `target_model = fields.Char(...)` | Danh từ chuẩn IBM MDM |
| `res_id = fields.Many2oneReference(...)` | `target_id = fields.Many2oneReference(...)` | Tham chiếu bản ghi mục tiêu |
| `self.env['ir.attachment']` | `self.env['system.attachment']` | Gọi ORM Model mới |

---

### COHORT 03: MASTER DATA — LEGAL ENTITY / ORGANIZATION UNIT
*Mô hình: `res.company` $\rightarrow$ `organization.unit` (IBM Operating Unit / Plant).*

#### 3.3.1 Ánh Xạ Danh Pháp
| Thành phần | Legacy Genesis | Proposed IBM Standard | Diễn giải nghiệp vụ |
| :--- | :--- | :--- | :--- |
| **Model Name** | `res.company` | **`organization.unit`** | Đơn vị tổ chức pháp nhân / công ty |
| **Physical Table** | `res_company` | **`organization_unit`** | Bảng vật lý lưu thông tin tổ chức |
| **Core Field** | `company_id` | **`org_unit_id`** *(hoặc giữ alias `company_id`)* | Khóa ngoại phân quyền đa công ty |
| **XML Action ID** | `action_res_company_form` | `action_organization_unit_form` | Cửa sổ quản lý công ty |
| **View Template** | `view_company_form` | `view_organization_unit_form` | Giao diện thông tin pháp nhân |

---

### COHORT 04: MASTER DATA — INVOLVED PARTY MASTER
*Mô hình: `res.partner` $\rightarrow$ `party.master` (IBM MDM Party Pattern).*

#### 3.4.1 Ánh Xạ Danh Pháp Cốt Lõi
| Thành phần | Legacy Genesis | Proposed IBM Standard | Diễn giải nghiệp vụ |
| :--- | :--- | :--- | :--- |
| **Model Name** | `res.partner` | **`party.master`** | Thực thể đối tác kinh doanh duy nhất |
| **Physical Table** | `res_partner` | **`party_master`** | Bảng dữ liệu đối tác gốc |
| **Foreign Keys** | `partner_id` | **`party_id`** | Khóa ngoại trỏ đến đối tác |
| **Parent Field** | `parent_id` | **`parent_party_id`** | Công ty mẹ / tổ chức cấp trên |
| **Commercial Field** | `commercial_partner_id` | **`commercial_party_id`** | Pháp nhân thương mại phục vụ tài chính |
| **Bank Field** | `bank_ids` | **`party_bank_account_ids`** | Tài khoản ngân hàng của đối tác |
| **Title Field** | `res.partner.title` | **`party.salutation`** | Danh xưng / chức vụ đại diện |

---

### COHORT 05: CATALOG & MATERIALS — ITEM MASTER & SKU
*Mô hình: IBM Maximo Item Master & IBM Sterling Product Information Management (PIM).*

#### 3.5.1 Ánh Xạ Danh Pháp
| Thành phần | Legacy Genesis | Proposed IBM Standard | Diễn giải nghiệp vụ |
| :--- | :--- | :--- | :--- |
| **Template Model** | `product.template` | **`catalog.item`** | Mục danh mục hàng hóa / sản phẩm chung |
| **Product Model** | `product.product` | **`catalog.sku`** | Đơn vị lưu kho cụ thể (Stock Keeping Unit) |
| **Category Model** | `product.category` | **`catalog.classification`** | Phân cấp ngành hàng / nhóm vật tư |
| **Pricelist Model** | `product.pricelist` | **`pricing.schedule`** | Bảng giá / Biểu phí thỏa thuận |
| **Tables** | `product_template`, `product_product` | `catalog_item`, `catalog_sku` | Bảng vật lý cơ sở dữ liệu |
| **Key Fields** | `product_id`, `product_tmpl_id` | `sku_id`, `item_id` | Khóa ngoại trong các dòng chứng từ |

---

### COHORT 06: PROCUREMENT & SCM — PURCHASE ORDERS
*Mô hình: IBM Sterling SCM & IBM Maximo Purchasing Module.*

#### 3.6.1 Ánh Xạ Danh Pháp
| Thành phần | Legacy Genesis | Proposed IBM Standard | Diễn giải nghiệp vụ |
| :--- | :--- | :--- | :--- |
| **Header Model** | `purchase.order` | **`procurement.order`** | Đơn đặt hàng mua sắm / Hợp đồng mua |
| **Line Model** | `purchase.order.line` | **`procurement.order.line`** | Chi tiết dòng vật tư mua sắm |
| **Requisition** | `purchase.requisition` | **`procurement.requisition`** | Yêu cầu mua hàng nội bộ (PR) |
| **Tables** | `purchase_order`, `purchase_order_line` | `procurement_order`, `procurement_order_line` | Bảng vật lý lưu chứng từ mua |
| **Vendor FK** | `partner_id` | `supplier_party_id` | Nhà cung cấp đối tác |

---

### COHORT 07: SALES & ORDERS — ORDER MANAGEMENT
*Mô hình: IBM Sterling Order Management System (OMS).*

#### 3.7.1 Ánh Xạ Danh Pháp
| Thành phần | Legacy Genesis | Proposed IBM Standard | Diễn giải nghiệp vụ |
| :--- | :--- | :--- | :--- |
| **Order Header** | `sale.order` | **`order.header`** *(hoặc `sales.order`)* | Đơn đặt hàng bán / Hợp đồng kinh doanh |
| **Order Line** | `sale.order.line` | **`order.line`** | Dòng sản phẩm trong đơn hàng bán |
| **Opportunity** | `crm.lead` | **`opportunity.lead`** | Cơ hội kinh doanh / Đầu mối thầu |
| **Tables** | `sale_order`, `sale_order_line` | `order_header`, `order_line` | Bảng vật lý đơn hàng bán |
| **Customer FK** | `partner_id` | `customer_party_id` | Khách hàng đối tác |

---

### COHORT 08: LOGISTICS & INVENTORY — TRANSFERS & MOVEMENTS
*Mô hình: IBM Sterling Inventory Visibility & Logistics Integration Platform.*

#### 3.8.1 Ánh Xạ Danh Pháp
| Thành phần | Legacy Genesis | Proposed IBM Standard | Diễn giải nghiệp vụ |
| :--- | :--- | :--- | :--- |
| **Picking Header**| `stock.picking` | **`logistics.transfer`** | Phiếu điều chuyển / Lệnh xuất-nhập kho |
| **Stock Move** | `stock.move` | **`logistics.movement`** | Giao dịch biến động tồn kho |
| **Move Line** | `stock.move.line` | **`logistics.movement.item`** | Chi tiết số sê-ri / số lô kiện hàng |
| **Warehouse** | `stock.warehouse` | **`facility.warehouse`** | Tổng kho / Trung tâm phân phối |
| **Location** | `stock.location` | **`facility.location`** | Tọa độ kệ hàng / Vị trí lưu kho (Bin) |
| **Tables** | `stock_picking`, `stock_move` | `logistics_transfer`, `logistics_movement` | Bảng vật lý vận tải & kho vận |

---

### COHORT 09: MANUFACTURING & MES — WORK ORDERS & PRODUCTION
*Mô hình: IBM Maximo Manufacturing Assets & Shop Floor Control.*

#### 3.9.1 Ánh Xạ Danh Pháp
| Thành phần | Legacy Genesis | Proposed IBM Standard | Diễn giải nghiệp vụ |
| :--- | :--- | :--- | :--- |
| **Production Order**| `mrp.production` | **`manufacturing.order`** | Lệnh sản xuất cơ khí / chế tạo máy |
| **BOM Header** | `mrp.bom` | **`manufacturing.bom`** | Định mức nguyên vật liệu đa tầng |
| **BOM Line** | `mrp.bom.line` | **`manufacturing.bom.item`** | Dòng thành phần cấu thành BOM |
| **Work Order** | `mrp.workorder` | **`shopfloor.operation`** | Công đoạn gia công trên chuyền / máy |
| **Work Center** | `mrp.workcenter` | **`routing.workcenter`** | Trạm làm việc / Máy CNC / Robot hàn |
| **Tables** | `mrp_production`, `mrp_bom` | `manufacturing_order`, `manufacturing_bom` | Bảng vật lý phân hệ MES |

---

### COHORT 10: FINANCIAL ACCOUNTING — GENERAL LEDGER & DOCUMENTS
*Mô hình: IBM Banking & Financial Markets Data Warehouse (BDW).*

#### 3.10.1 Ánh Xạ Danh Pháp
| Thành phần | Legacy Genesis | Proposed IBM Standard | Diễn giải nghiệp vụ |
| :--- | :--- | :--- | :--- |
| **Journal Entry** | `account.move` | **`finance.journal.entry`** | Chứng từ kế toán / Bút toán nhật ký |
| **Journal Item** | `account.move.line` | **`finance.journal.line`** | Dòng định khoản nợ / có (G/L Entry) |
| **Account** | `account.account` | **`finance.gl.account`** | Tài khoản sổ cái (Chart of Accounts) |
| **Journal** | `account.journal` | **`finance.journal`** | Sổ nhật ký thu/chi/bán/mua |
| **Tables** | `account_move`, `account_move_line` | `finance_journal_entry`, `finance_journal_line`| Bảng vật lý kế toán tài chính |

---

## 4. BỘ QUY TẮC AST-GREP KHÔNG VÙNG CẤM (DECLARATIVE RULE ENGINE)

Để tự động hóa việc thay thế mã nguồn chính xác đến từng AST Token (Abstract Syntax Tree), bộ quy tắc YAML được cấu hình trong `tools/ast_grep/rules/`:

### 4.1 Quy tắc ORM Model Name (`rules/orm/rewrite_model_name.yml`)
```yaml
id: insilos-orm-model-name-rewrite
language: python
rule:
  pattern: _name = '$OLD_MODEL'
transform:
  NEW_MODEL:
    replace:
      source: $OLD_MODEL
      replace:
        'res.partner.category': 'party.classification'
        'ir.attachment': 'system.attachment'
        'res.company': 'organization.unit'
        'res.partner': 'party.master'
        'product.template': 'catalog.item'
        'product.product': 'catalog.sku'
fix: _name = '$NEW_MODEL'
```

### 4.2 Quy tắc ORM Comodel Foreign Key (`rules/orm/rewrite_comodel.yml`)
```yaml
id: insilos-orm-comodel-rewrite
language: python
rule:
  any:
    - pattern: fields.Many2one(comodel_name='$OLD_MODEL', $$$ARGS)
    - pattern: fields.Many2one('$OLD_MODEL', $$$ARGS)
    - pattern: fields.Many2many(comodel_name='$OLD_MODEL', $$$ARGS)
    - pattern: fields.Many2many('$OLD_MODEL', $$$ARGS)
    - pattern: fields.One2many(comodel_name='$OLD_MODEL', $$$ARGS)
    - pattern: fields.One2many('$OLD_MODEL', $$$ARGS)
fix: fields.$METHOD('$NEW_MODEL', $$$ARGS)
```

### 4.3 Quy tắc QWeb & XML Views Model Binding (`rules/qweb/rewrite_xml_model.yml`)
```yaml
id: insilos-xml-model-binding-rewrite
language: html
rule:
  any:
    - pattern: <field name="model">$OLD_MODEL</field>
    - pattern: <field name="res_model">$OLD_MODEL</field>
fix: <field name="$FIELD_NAME">$NEW_MODEL</field>
```

---

## 5. MA TRẬN RỦI RO & CƠ CHẾ PHÒNG VỆ CHỦ ĐỘNG

| Tình huống Rủi ro | Mức độ | Hậu quả tiềm ẩn | Cơ Chế Phòng Vệ Tự Động (Active Defense) |
| :--- | :---: | :--- | :--- |
| **1. Metadata Fracture** | 🔴 Nghiêm trọng | ORM tạo bảng mới rỗng, bỏ rơi bảng cũ chứa dữ liệu sản xuất. | **Pre-boot SQL Injection**: Cập nhật `ir_model` và `ir_model_fields` trước khi khởi động server. |
| **2. XPath Breakage** | 🟡 Trung bình | Các view XML kế thừa bị lỗi do không tìm thấy field hoặc vị trí thẻ. | Giữ nguyên thuộc tính `name` của field trên model thông qua ORM `related` hoặc Python property alias. |
| **3. 3rd-Party Addon Calls** | 🟡 Trung bình | Addon bên ngoài gọi `self.env['res.partner']` sinh lỗi `KeyError`. | **Dynamic Model Shim**: Tiêm alias mapping vào `odoo.modules.registry.Registry.models`. |
| **4. Raw SQL Query Fails** | 🔴 Nghiêm trọng | Code sử dụng `self.env.cr.execute("SELECT * FROM res_partner")` bị vỡ. | **PostgreSQL Updatable Views**: Tạo View cùng tên trỏ về bảng vật lý mới, hỗ trợ ghi/đọc trong suốt. |
| **5. Sequence Out of Sync** | 🟡 Trung bình | Lỗi duplicate key violation khi tạo bản ghi mới sau khi đổi tên bảng. | Tự động đổi tên `SERIAL` sequence và rebind `ALTER TABLE ... ALTER COLUMN id SET DEFAULT nextval(...)`. |

---

## 6. LỘ TRÌNH THỰC THI TUẦN TỰ (SEQUENTIAL PDCA ROADMAP)

```
[COHORT 1: party.classification]
  ├── P (Plan): Lập danh mục 70 files (đã xong)
  ├── D (Do): Chạy AST-Grep + SQL Migration (đã kiểm thử DB)
  ├── C (Check): HOOT Tests + CEW Gates 8-10
  └── A (Act): Merge & Commit Git
        │
        ▼
[COHORT 2: system.attachment]
  ├── P: Quét 2,400 occurrences AST-Grep
  ├── D: Tạo Updatable View system_attachment + Code rewrite
  ├── C: Kiểm thử upload/download tài liệu, avatar, SVG
  └── A: Merge & Commit Git
        │
        ▼
[COHORT 3 -> 10: Master Data, Supply Chain, Manufacturing, Finance]
```

---
*Tài liệu được phê chuẩn bởi Hội đồng Kiến trúc Insilos Sovereign Hard Fork.*
