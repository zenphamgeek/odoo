# TEST_INFRA.md: Insilos Platform Hard Fork — Automated Dual-Track E2E Test Infrastructure & Specification

**Standard**: Hard Fork Experts Council — SAP Enterprise Lexicon & Fiori Horizon Transformation Testing Infrastructure & Quality Assurance Specification  
**Target Platform**: Insilos Enterprise Platform (`insilos-genesis-fork`), Python 3.12, PostgreSQL 18 (`odoo20_dev`)  
**Architecture**: 4-Tier Presentation Architecture (ORM Lexicon Mixin, Web OWL Service, Declarative Navigation XML, Financial FSV)  
**Author**: Test Writer (Specialist & QA) — Hard Fork Experts Council  
**Date**: September 28, 2026  
**Status**: ACTIVE & OPERATIONAL  

---

## 1. Test Architecture & Testing Philosophy

### 1.1 Opaque-Box & Requirement-Driven Foundation
The Insilos Platform Hard Fork test architecture enforces **opaque-box, requirement-driven verification**. Tests treat the entire platform as an integrated industrial enterprise system, interacting strictly through observable contracts and verifiable boundaries:
- **Presentation & ORM Introspection Layer**: Verification of `fields_get()`, `get_views()`, and model `_description` to confirm SAP enterprise terminology (Business Partner, Material Master, Plant, Storage Location, Sales Order, Customer Billing Document, Outbound Delivery, Production Order, Cost/Profit Centers) without mutating SQL schemas or model technical identifiers (`_name`).
- **Web Client OWL Translation Layer**: Verification of `sap_lexicon_service.js` injecting terminology into `translatedTermsGlobal` for real-time frontend terminology rendering in QWeb templates.
- **Declarative Navigation & Action XML Layer**: Verification of idempotent `<record>` updates in `addons/insilos_sap_fiori/data/sap_menu_data.xml` for all target `ir.ui.menu` and `ir.actions.act_window` records.
- **Financial Reporting FSV Layer**: Verification of `account.report` and `account.report.line` enforcing SAP `S_ALR_87012284` terminology for Balance Sheet, P&L, Trial Balance (`S_ALR_87012301`), and General Ledger (`S_ALR_87012277`).
- **Fiori Horizon High-Density Ergonomics Layer**: Verification of compact 32px–34px table rows, sticky `#F8FAFC` headers, streamlined 44px control panel, 4-state semantic status badges (Positive `#107E3E`, Critical `#BB0000`, Warning `#E9730C`, Information `#0070F2`), and KPI Object Cards (`.o_kpi_trend`).
- **Security & Counter Code Scanner Invariance Layer**: Programmatic verification via `scripts/counter_code_scanner.py` ensuring zero legacy genesis signatures (`odoo`, `openerp`, legacy URLs, legacy brand colors `#714B67`/`#017e84`) across scoped target modules (`addons/web`, `addons/base`, `branding`, `enterprise/web_enterprise`).

### 1.2 Progressive Testability & Milestone Isolation
Tests are organized into progressive tiers corresponding to project milestones (M1 through M6). Each test can be independently executed and verified without requiring mock artifacts or unfinished dependencies from downstream milestones:
- **Milestone M1 (Core Master Data & Navigation Launchpad)**: BP Master Data, Material Master, Plant/Storage Location mapping, Launchpad tiles, Top Navbar.
- **Milestone M2 (Supply Chain SD & MM Lexicon & Documents)**: SD Quotations & Sales Orders, Customer Billing Documents (F2), Outbound Delivery/Goods Issue (601), MM Purchase Orders & Vendor RFQs, Inbound Delivery/Goods Receipt (101), Physical Inventory Adjustments & Movement Types (101, 102, 261, 301, 311, 601, 701, 702).
- **Milestone M3 (Financial Accounting FI/CO & Production Planning PP)**: FI Accounting Documents (`BKPF`/`BSEG`), G/L Accounts, Cost Centers (`KOSTL`) & Profit Centers (`PRCTR`), `S_ALR_87012284` Statutory Financial Reports, PP Production Orders (`CO01`/`CO02`), Production BOMs (`CS01`), Work Centers / Routing Resources (`CR01`).
- **Milestone M4 (SAP Fiori Horizon High-Density Ergonomics & Iconography)**: KPI Object Cards, Semantic Status Badges, High-Density Master-Detail & Tabular Views, Phosphor Duotone Icon Binding (`ph-duotone`).
- **Milestone M5 (Counter Code Security Sanitization)**: Remediation of legacy genesis detections in `enterprise/web_enterprise` to achieve 0 detections.
- **Milestone M6 (10-Gate E2E Verification & Forensic Audit)**: Full 10-Gate Release Verification Matrix execution via `tools/run_hard_fork_council_gates.py`.

### 1.3 Expected Output Derivation & Authoritative Oracles
Every test case defines an explicit, authoritative source of truth:
1. **SAP Standard Lexicon Oracle**: Official SAP ECC / S4HANA nomenclature reference (SAP Terminology Database, SD/MM/FI/CO/PP module specifications).
2. **SAP Fiori Horizon Design Oracle**: SAP Fiori 4 / Horizon Design Guidelines (KPI card metrics, 4 semantic status colors, compact table row geometry, Phosphor Duotone mappings).
3. **Database & ORM Schema Oracle**: PostgreSQL `odoo20_dev` relational schema inspection, ensuring technical table names (`res_partner`, `product_template`, `sale_order`, `stock_picking`, `account_move`, `mrp_production`) remain immutable.
4. **Programmatic Security Scanner Oracle**: `scripts/counter_code_scanner.py` with parameter `--max-allowed-detections 0`.
5. **Runtime Boot & Interop Oracle**: `insilos-bin -c insilos.conf -d odoo20_dev --stop-after-init` and `tools/test_insilos_import_hook.py`.

### 1.4 Test Integrity & Anti-Cheat Protocol
In accordance with council integrity directives:
- Facade tests that pass unconditionally without exercising real underlying logic are strictly banned.
- Hardcoded test outputs or dummy bypass scripts are forbidden.
- All test runners must invoke genuine processes, capture actual exit codes, measure authentic wall-clock timings, and produce verifiable diagnostic traces.

---

## 2. 4-Tier Test Taxonomy Overview

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ TIER 4: Real-World Enterprise Journeys & Executive Personas (4 End-to-End Scenarios)   │
│ - Scenario 1: VP Supply Chain Order-to-Cash (SD Quotation -> Order -> Delivery -> Bill)│
│ - Scenario 2: Head of Procurement Procure-to-Pay (RFQ -> PO -> GR -> Vendor Bill)      │
│ - Scenario 3: Financial Controller Statutory Close (FI Docs -> S_ALR_87012284 FSV)     │
│ - Scenario 4: Plant Production Manager Discrete MRP (BOM -> Work Center -> PP Order)   │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ TIER 3: Cross-Feature Subsystem Combinations & Contract Testing (10 Interaction Suites)│
│ - Mixin interception on fields_get() & get_views() without ORM technical mutation       │
│ - OWL Translation Service + translatedTermsGlobal QWeb reactivity                      │
│ - Declarative XML menu overrides vs ir.ui.menu registry                                │
│ - High-Density SCSS responsive collapse (32px table -> mobile list card)              │
│ - Phosphor Duotone icon SVG rendering in place of legacy fa-* classes                  │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ TIER 2: Boundary, Extreme Viewport, Movement Type Stress & Edge Cases (15 Suites)      │
│ - Invalid movement types, circular BOMs, unposted FI entries, multi-currency rounding  │
│ - 320px mobile viewport, 4K ultrawide layout, extreme string length, XSS escaping      │
│ - Bearer token auth vs X-Session-Id header vs unauthenticated API access               │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ TIER 1: Feature Coverage (Features 1 to 22 across Milestones M1 to M6)                │
│ - 22 Features × >= 5 Isolated Verifiable Test Cases = 110+ Discrete Unit/API Tests     │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Tier 1: Detailed Feature-by-Feature Test Specifications

### Feature 1: Business Partner (BP) Master Data (M1)
- **TEST-F01-01 (Model Description)**: Introspect `res.partner` via ORM; verify `_description` equals `"Business Partner (BP)"`.
- **TEST-F01-02 (Partner Roles)**: Verify fields or view tabs distinguish General, Customer, and Vendor roles.
- **TEST-F01-03 (Technical Identifier Invariance)**: Verify `res.partner._name == 'res.partner'` and table name is `res_partner`.
- **TEST-F01-04 (Field Label Overrides)**: Verify `fields_get()['name']['string']` and contact fields display SAP BP strings.
- **TEST-F01-05 (View Action String)**: Verify window action title in XML displays `"Business Partners"`.

### Feature 2: Material Master (MM) Architecture (M1)
- **TEST-F02-01 (Model Description)**: Introspect `product.template` and `product.product`; verify description reflects `"Material Master (MM)"`.
- **TEST-F02-02 (Material Types)**: Verify classification of materials into standard SAP types (ROH: Raw Materials, HALB: Semi-Finished, FERT: Finished Goods, HAWA: Trading Goods, DIEN: Services).
- **TEST-F02-03 (Schema Invariance)**: Verify `product_template` and `product_product` database tables remain unchanged.
- **TEST-F02-04 (UoM & Valuations)**: Verify Base Unit of Measure (UoM) and material valuation fields present SAP terminology.
- **TEST-F02-05 (Product Form View Header)**: Verify `<form>` view header displays Material Master rather than legacy Product.

### Feature 3: Organizational Structure Standard (Bukrs, Werks, SLoc) (M1)
- **TEST-F03-01 (Company Code Mapping)**: Verify `res.company` displays `"Company Code (Bukrs)"` in UI labels.
- **TEST-F03-02 (Plant Mapping)**: Verify `stock.warehouse` displays `"Plant (Werks)"` in UI labels.
- **TEST-F03-03 (Storage Location Mapping)**: Verify `stock.location` displays `"Storage Location (SLoc)"` in UI labels.
- **TEST-F03-04 (Hierarchy Verification)**: Verify multi-level relationship: Company Code -> Plant -> Storage Location resolves correctly.
- **TEST-F03-05 (No Broken Foreign Keys)**: Verify `company_id`, `warehouse_id`, `location_id` technical fields remain intact.

### Feature 4: Launchpad & App Drawer Navigation (M1)
- **TEST-F04-01 (Functional Space Grouping)**: Verify home launcher categorizes apps into SAP functional spaces (SD, MM, FI/CO, PP, BP).
- **TEST-F04-02 (Acronym Pills)**: Verify launcher app tiles feature high-contrast acronym pills (e.g. `[SD]`, `[MM]`, `[FI]`).
- **TEST-F04-03 (160x160px Tile Geometry)**: Verify computed CSS geometry on `.o_app` evaluates to 160×160px tiles.
- **TEST-F04-04 (Top Navbar Lexicon)**: Verify top navigation dropdown menus reflect SAP business module naming.
- **TEST-F04-05 (Zero Console Errors on Launchpad)**: Verify loading `/insilos` produces 0 uncaught JavaScript console errors.

### Feature 5: SD Quotations & Sales Orders (M2)
- **TEST-F05-01 (Model Description)**: Introspect `sale.order`; verify description reflects `"Sales Order (SD)"`.
- **TEST-F05-02 (Status Lifecycle)**: Verify lifecycle states: Draft -> Sales Inquiry -> SD Quotation -> SD Sales Order.
- **TEST-F05-03 (Partner Party Roles)**: Verify Sold-to Party (`partner_id`), Bill-to Party (`partner_invoice_id`), and Ship-to Party (`partner_shipping_id`) labels.
- **TEST-F05-04 (Order Lines Lexicon)**: Verify `order_line` columns display Material, Order Quantity, Net Price, Tax Code, Line Total.
- **TEST-F05-05 (Action Title)**: Verify window action title renders `"SD Sales Orders"`.

### Feature 6: Customer Billing Documents (M2)
- **TEST-F06-01 (Billing Document Naming)**: Introspect customer invoice moves; verify description reflects `"Customer Billing Document (F2)"`.
- **TEST-F06-02 (Credit Memo Naming)**: Verify customer credit notes reflect `"Credit Memo (RE)"`.
- **TEST-F06-03 (Schema Invariance)**: Verify table `account_move` and field `move_type` remain untouched.
- **TEST-F06-04 (Billing Status Field)**: Verify invoice payment state displays SAP billing status labels (Open, Paid, Reversed).
- **TEST-F06-05 (Printout / Report Title)**: Verify billing document QWeb PDF header prints `"Customer Billing Document"`.

### Feature 7: Outbound Delivery & Goods Issue (Movement Type 601) (M2)
- **TEST-F07-01 (Outbound Transfer Description)**: Introspect outgoing `stock.picking`; verify description reflects `"Outbound Delivery (Post Goods Issue)"`.
- **TEST-F07-02 (Movement Type 601 Annotation)**: Verify Outbound Delivery operations annotate SAP Movement Type `601`.
- **TEST-F07-03 (Picking State Mapping)**: Verify states map to Picking, Packing, Goods Issue Posted.
- **TEST-F07-04 (Stock Move Line Labels)**: Verify stock move lines display Material, Storage Location, Delivered Qty.
- **TEST-F07-05 (Zero SQL Breaking Changes)**: Verify table `stock_picking` and relations remain standard.

### Feature 8: MM Purchase Orders & Vendor RFQs (M2)
- **TEST-F08-01 (Purchase Order Description)**: Introspect `purchase.order`; verify description reflects `"MM Purchase Order"`.
- **TEST-F08-02 (Vendor RFQ Description)**: Verify RFQ view header renders `"Vendor Request for Quotation (RFQ)"`.
- **TEST-F08-03 (Purchase Requisition Binding)**: Verify requisition references reflect Purchase Requisition (PR).
- **TEST-F08-04 (Vendor Partner Label)**: Verify `partner_id` in purchase order renders as `"Vendor / Supplier"`.
- **TEST-F08-05 (PO Line Material Columns)**: Verify PO lines render Material Master, PO Quantity, Net Unit Price.

### Feature 9: Inbound Delivery & Goods Receipt (Movement Type 101) (M2)
- **TEST-F09-01 (Inbound Transfer Description)**: Introspect incoming `stock.picking`; verify description reflects `"Inbound Delivery (Goods Receipt)"`.
- **TEST-F09-02 (Movement Type 101 Annotation)**: Verify Inbound Delivery annotates SAP Movement Type `101`.
- **TEST-F09-03 (Receiving Storage Location)**: Verify destination location renders as Receiving Storage Location (SLoc).
- **TEST-F09-04 (Goods Receipt Posting)**: Verify validate button action corresponds to Post Goods Receipt.
- **TEST-F09-05 (Traceability & Lots)**: Verify lot/serial number tracking displays Batch / Lot Master.

### Feature 10: Physical Inventory Adjustments & Movement Types (M2)
- **TEST-F10-01 (Inventory Adjustment Nomenclature)**: Introspect `stock.quant`; verify adjustment views reflect `"Physical Inventory Adjustment"`.
- **TEST-F10-02 (Movement Type 701/702)**: Verify positive adjustment annotates `701` and negative adjustment annotates `702`.
- **TEST-F10-03 (Transfer Movement Types)**: Verify stock transfers document standard movement types (301 Plant-to-Plant, 311 SLoc-to-SLoc).
- **TEST-F10-04 (Consumption Movement Types)**: Verify production consumption annotates Movement Type `261`.
- **TEST-F10-05 (Stock Quant Valuation)**: Verify on-hand inventory list displays Material, Plant, SLoc, Unrestricted Stock, Book Value.

### Feature 11: FI Accounting Documents & G/L (M3)
- **TEST-F11-01 (Journal Entry Description)**: Introspect miscellaneous `account.move`; verify description reflects `"FI Accounting Document (BKPF)"`.
- **TEST-F11-02 (Journal Item Description)**: Introspect `account.move.line`; verify description reflects `"FI Document Line Item (BSEG)"`.
- **TEST-F11-03 (Chart of Accounts Description)**: Introspect `account.account`; verify description reflects `"General Ledger (G/L) Accounts"`.
- **TEST-F11-04 (Debit / Credit Nomenclature)**: Verify Debit (`debit`) and Credit (`credit`) columns display standard FI terminology.
- **TEST-F11-05 (Posting Period & Posting Date)**: Verify date fields reflect Posting Date (`budat`) and Document Date (`bldat`).

### Feature 12: Controlling Cost & Profit Centers (M3)
- **TEST-F12-01 (Cost Center Nomenclature)**: Introspect `account.analytic.account` under Cost category; verify label reflects `"Cost Center (KOSTL)"`.
- **TEST-F12-02 (Profit Center Nomenclature)**: Introspect `account.analytic.account` under Revenue category; verify label reflects `"Profit Center (PRCTR)"`.
- **TEST-F12-03 (Controlling Area Verification)**: Verify multi-company analytic plans correspond to Controlling Area (`KOKRS`).
- **TEST-F12-04 (Analytic Line Posting)**: Introspect `account.analytic.line`; verify postings render as CO Secondary Postings.
- **TEST-F12-05 (Relational Integrity)**: Verify foreign key links to `account_move_line` remain intact.

### Feature 13: Statutory Financial Statements S_ALR_87012284 (M3)
- **TEST-F13-01 (Balance Sheet FSV Report)**: Verify Balance Sheet report in `account.report` is annotated with SAP code `S_ALR_87012284`.
- **TEST-F13-02 (Profit and Loss FSV Report)**: Verify P&L report displays Financial Statement Version (FSV) hierarchy.
- **TEST-F13-03 (Trial Balance S_ALR_87012301)**: Verify Trial Balance report is annotated with `S_ALR_87012301`.
- **TEST-F13-04 (General Ledger S_ALR_87012277)**: Verify General Ledger report is annotated with `S_ALR_87012277`.
- **TEST-F13-05 (Report XML Declarations)**: Verify declarative XML in `addons/insilos_sap_fiori/data/sap_financial_reports.xml` applies cleanly without syntax errors.

### Feature 14: PP Production Orders (M3)
- **TEST-F14-01 (Manufacturing Order Description)**: Introspect `mrp.production`; verify description reflects `"Production Order (PP/CO01)"`.
- **TEST-F14-02 (Order Header Fields)**: Verify fields reflect Material Master, Order Quantity, Basic Dates, Released Status.
- **TEST-F14-03 (Component Allocations)**: Verify raw material allocations reflect Goods Issue for Order (Movement Type 261).
- **TEST-F14-04 (Order Confirmation)**: Verify production recording reflects Order Confirmation (CO11N/CO15).
- **TEST-F14-05 (Finished Goods Receipt)**: Verify goods receipt from production reflects Movement Type `101`.

### Feature 15: Production BOM & Work Centers (M3)
- **TEST-F15-01 (BOM Description)**: Introspect `mrp.bom`; verify description reflects `"Production BOM (CS01)"`.
- **TEST-F15-02 (BOM Components)**: Verify BOM line items display Item Number, Component Material Master, Base Quantity.
- **TEST-F15-03 (Work Center Description)**: Introspect `mrp.workcenter`; verify description reflects `"Work Center / Routing Resource (CR01)"`.
- **TEST-F15-04 (Work Center Capacities)**: Verify standard capacity, efficiency rate, and hourly cost rates.
- **TEST-F15-05 (Routing Operations)**: Verify operations reflect Standard Routing Sequences and Work Steps.

### Feature 16: KPI Object Cards & Micro-Trends (M4)
- **TEST-F16-01 (Card Metric Typography)**: Verify `.oe_stat_button` in Fiori Horizon displays 1.25rem bold value above uppercase micro-label.
- **TEST-F16-02 (Micro-Trend Indicators)**: Verify presence of `.o_kpi_trend` indicator (positive up-arrow, neutral dash, negative down-arrow).
- **TEST-F16-03 (Hover Sheen Lift)**: Verify `.oe_stat_button:hover` applies subtle border illumination and lift.
- **TEST-F16-04 (Zero Inline Styles)**: Verify KPI cards contain 0 inline `style="..."` attributes.
- **TEST-F16-05 (Responsive Grid Behavior)**: Verify KPI button box wraps cleanly on mobile viewports (< 768px).

### Feature 17: Semantic Status Badge Architecture (M4)
- **TEST-F17-01 (4 Canonical States)**: Verify declaration of 4 semantic badge classes: Positive, Critical, Warning, Information in `fiori_status_badges.scss`.
- **TEST-F17-02 (Positive Badge Color Token)**: Verify Positive badge uses `#107E3E` (Dark Green) with soft background tint.
- **TEST-F17-03 (Critical Badge Color Token)**: Verify Critical badge uses `#BB0000` (Burgundy Red) with soft background tint.
- **TEST-F17-04 (Warning Badge Color Token)**: Verify Warning badge uses `#E9730C` (Amber Orange) with soft background tint.
- **TEST-F17-05 (Information Badge Color Token)**: Verify Information badge uses `#0070F2` (Horizon Blue) with soft background tint.

### Feature 18: High-Density Master-Detail & Tabular Views (M4)
- **TEST-F18-01 (Compact Row Height)**: Verify computed row height in `.o_list_table` evaluates between 32px and 34px.
- **TEST-F18-02 (Sticky Table Header)**: Verify `.o_list_table thead th` specifies `position: sticky; top: 0; background-color: #F8FAFC;`.
- **TEST-F18-03 (Streamlined Control Panel)**: Verify control panel search/filter bar height is capped at 44px.
- **TEST-F18-04 (Horizontal Padding)**: Verify high-density table cell horizontal padding is condensed to 8px.
- **TEST-F18-05 (Desktop List Renderer Cleanliness)**: Verify `enterprise/web_enterprise/static/src/views/list/list_renderer_desktop.xml` complies with zero inline styles.

### Feature 19: Phosphor Duotone Icon Binding (M4)
- **TEST-F19-01 (Canonical Icon Mapping Authority)**: Verify `tools/icon_mapping.json` maps >= 60 core apps to Phosphor Duotone glyphs.
- **TEST-F19-02 (Canonical Glyph Specifications)**: Verify all SVGs in `tools/phosphor_duotone/` have `viewBox="0 0 256 256"` and `opacity="0.2"` duotone layer.
- **TEST-F19-03 (Launcher Target Icons Contract)**: Verify all 64 deployed launcher icons meet `#0B2E64` or `currentColor` color standard.
- **TEST-F19-04 (Zero Raster Embeds)**: Verify zero embedded raster images (`<image>` or `data:image/`) in launcher vector icons.
- **TEST-F19-05 (UI Icon Replacement Rate)**: Verify scanner reports >= 3,000 Phosphor icon hits across core scopes.

### Feature 20: Counter Code Security Remediation (M5)
- **TEST-F20-01 (Target Scope Execution)**: Run `python3 scripts/counter_code_scanner.py --scope addons/web addons/base branding enterprise/web_enterprise --max-allowed-detections 0`.
- **TEST-F20-02 (Branding Scope Cleanliness)**: Verify `branding/` reports exactly 0 detections.
- **TEST-F20-03 (Addons/Web Scope Cleanliness)**: Verify `addons/web` reports exactly 0 detections.
- **TEST-F20-04 (Addons/Base Scope Cleanliness)**: Verify `addons/base` reports exactly 0 detections.
- **TEST-F20-05 (Enterprise Web Enterprise Remediation)**: Verify all 116 detections in `enterprise/web_enterprise` are sanitized to 0 hits.

### Feature 21: Prototype Defect Remediation (M1/M2/M3)
- **TEST-F21-01 (Removal of Invalid Function Call)**: Verify absence of `<function model="ir.ui.menu" name="update_sap_menus"/>` in `addons/insilos_sap_fiori`.
- **TEST-F21-02 (Declarative Record Definitions)**: Verify menu changes use idempotent `<record model="ir.ui.menu" id="...">` XML definitions.
- **TEST-F21-03 (Clean Module Upgrade)**: Verify module `insilos_sap_fiori` upgrades with 0 tracebacks or XML parse errors.
- **TEST-F21-04 (Menu Hierarchy Preservation)**: Verify parent-child relationships across all top-level menus remain valid.
- **TEST-F21-05 (Action Binding Intactness)**: Verify menu items bind to existing window actions without broken action IDs.

### Feature 22: 10-Gate E2E Verification & Sign-Off (M6)
- **TEST-F22-01 (Integrated Runner Execution)**: Run `tools/run_hard_fork_council_gates.py` across all 10 gates.
- **TEST-F22-02 (Exit Code Compliance)**: Verify runner exits with code 0 upon release certification.
- **TEST-F22-03 (JSON Report Generation)**: Verify structured JSON audit report generates with complete gate metrics and timestamps.
- **TEST-F22-04 (Individual Gate Selectivity)**: Verify `--gates` flag executes arbitrary subsets (e.g. `--gates 1,2,4,6`).
- **TEST-F22-05 (Forensic Audit Sign-Off)**: Verify zero unhandled exceptions, zero data loss, and zero security regressions.

---

## 4. Tier 2: Boundary & Corner Cases

| Test ID | Boundary Area | Input Condition | Expected Behavior |
|---|---|---|---|
| **TEST-BND-01** | Movement Type Validation | Invalid movement type code `999` | Rejects with clean user-facing error; no database corruption |
| **TEST-BND-02** | Zero/Negative Qty Order | SD Order Line with quantity `0.0` or `-5.0` | Validates line quantity; raises standard business validation warning |
| **TEST-BND-03** | Material Master Code Length | Material SKU containing 128 characters | Truncates or validates cleanly within database column constraints |
| **TEST-BND-04** | Circular BOM Hierarchy | Production BOM referencing itself as component | BOM validation logic detects recursion and raises clean error |
| **TEST-BND-05** | Unbalanced FI Document | FI Document with Debit != Credit | Refuses posting with `"Cannot post unbalanced accounting entry"` |
| **TEST-BND-06** | Currency Rounding Stress | Multi-currency invoice with 6 decimal places | Applies currency precision rounding without float discrepancy |
| **TEST-BND-07** | Mobile Viewport (320px) | Fiori high-density table on 320px screen | Condenses cleanly into stacked responsive cards; no horizontal overflow |
| **TEST-BND-08** | Ultrawide Viewport (3840px) | 4K display resolution on App Drawer | Grid wraps gracefully; tiles maintain 160×160px dimensions |
| **TEST-BND-09** | Extreme Title String Length | Partner name with 255 Unicode characters | Wraps with `text-wrap: balance` without clipping container |
| **TEST-BND-10** | Special Character Escaping | Partner / Material name containing `<script>alert(1)</script>` | QWeb escapes characters cleanly; zero XSS vulnerability |
| **TEST-BND-11** | Unauthenticated API Call | `POST /insilos/api/v1/call` without credentials | Returns HTTP 401 with `server: insilos/20.0` header |
| **TEST-BND-12** | Unknown Model in API | `POST /insilos/api/v1/call` with fake model name | Returns HTTP 404 with error masked; zero internal path leakage |
| **TEST-BND-13** | Bearer Token Auth | API call with `Authorization: Bearer <session_id>` | Authenticates successfully without browser cookies |
| **TEST-BND-14** | X-Session-Id Header Auth | API call with `X-Session-Id: <session_id>` | Authenticates successfully without browser cookies |
| **TEST-BND-15** | Server Exception Masking | Internal Python crash simulated on gateway | Returns HTTP 500 JSON without Traceback or file paths |

---

## 5. Tier 3: Cross-Feature Subsystem Combinations & Contract Testing

| Test ID | Subsystem A | Subsystem B | Interaction Contract & Expected Behavior |
|---|---|---|---|
| **TEST-INT-01** | ORM Lexicon Mixin | Model `fields_get()` | Intercepts field metadata dynamically; returns SAP strings without SQL table alteration |
| **TEST-INT-02** | ORM Lexicon Mixin | Model `get_views()` | Intercepts view definitions; injects SAP labels into XML arch dynamically |
| **TEST-INT-03** | OWL Translation Service | `translatedTermsGlobal` | Injects terms into web client memory; QWeb templates re-render with SAP terminology |
| **TEST-INT-04** | Declarative Menu XML | System Menu Registry | `<record>` updates override `ir.ui.menu` without duplicate entries or broken parent IDs |
| **TEST-INT-05** | Financial Report FSV | General Ledger Postings | `account.report` aggregates balances under `S_ALR_87012284` FSV hierarchy |
| **TEST-INT-06** | SD Sales Order | Stock Outbound Delivery | Confirming Sales Order generates Outbound Delivery with Movement Type `601` |
| **TEST-INT-07** | MM Purchase Order | Stock Inbound Delivery | Confirming Purchase Order generates Inbound Delivery with Movement Type `101` |
| **TEST-INT-08** | PP Production Order | MRP BOM & Routing | Confirming Production Order reserves BOM components (261) and schedules work centers |
| **TEST-INT-09** | Fiori Horizon SCSS | Phosphor Duotone Icons | Table views render compact 32px rows with Phosphor Duotone action icons |
| **TEST-INT-10** | PEP 451 Import Hook | Perimeter API Gateway | Gateway controllers import `from insilos import http, models`; resolves transparently to odoo |

---

## 6. Tier 4: Real-World Enterprise Journeys & Executive Personas

### Scenario 1: VP Supply Chain Order-to-Cash (SD End-to-End Walkthrough)
1. **Entry**: VP logs into Insilos Launchpad (`http://localhost:28069/insilos`), selects `[SD] Sales & Distribution`.
2. **Inquiry / Quotation**: Creates SD Quotation for Business Partner `Tân Cảng Logistics`, adds Material `VLIFT-2500E`.
3. **Sales Order**: Confirms quotation into SD Sales Order `#SO-2026-001`.
4. **Outbound Delivery**: Navigates to Outbound Delivery, validates picking, posts Goods Issue (Movement Type 601).
5. **Customer Billing**: Generates Customer Billing Document (F2) `#BILL-2026-001`; verifies accounting lines post cleanly.

### Scenario 2: Head of Procurement Procure-to-Pay (MM End-to-End Walkthrough)
1. **Entry**: Procurement Lead opens `[MM] Materials Management`.
2. **Vendor RFQ**: Creates Vendor Request for Quotation for Supplier `Hòa Phát Steel`.
3. **Purchase Order**: Converts RFQ into MM Purchase Order `#PO-2026-001` for 20 tons of SS400 raw material.
4. **Goods Receipt**: Receives shipment at Plant `Werks 01` / Storage Location `SLoc 01`, posts Goods Receipt (Movement Type 101).
5. **Vendor Invoice Verification**: Matches PO, GR, and Vendor Bill (3-way match) with zero price tolerance error.

### Scenario 3: Financial Controller Statutory Close (FI/CO S_ALR_87012284 Walkthrough)
1. **Entry**: Controller accesses `[FI] Financial Accounting`.
2. **FI Accounting Documents**: Audits Journal Entries (`BKPF`/`BSEG`), verifies cost center allocations (`KOSTL`).
3. **Statutory Financial Statements**: Generates Balance Sheet and Profit & Loss Statement under `S_ALR_87012284` standard.
4. **Trial Balance Verification**: Generates Trial Balance `S_ALR_87012301`, confirms Debit = Credit balance.
5. **Export & Audit**: Exports audit ledger; verifies zero legacy platform branding in generated PDF/Excel reports.

### Scenario 4: Plant Production Manager Discrete MRP (PP End-to-End Walkthrough)
1. **Entry**: Production Manager accesses `[PP] Production Planning`.
2. **Production Order Creation**: Creates Production Order `CO01` for Finished Good `VLIFT-2500E`.
3. **BOM & Routing Explosion**: Verifies 2-level BOM explosion and routing work centers (`CR01` Laser Fiber, `CR02` Robotic Welding).
4. **Component Issue**: Issues raw material components (Movement Type 261).
5. **Order Confirmation & Goods Receipt**: Records shop floor operation completion, posts finished goods into stock (Movement Type 101).

---

## 7. Non-Negotiable Backward Compatibility Verification Criteria

To ensure database consistency, relational integrity, and zero regressions during the transformation:

### Rule 1: Frozen Relational Identifiers (Technical Invariance)
- **NEVER rename technical model identifiers (`_name`)**: Models like `res.partner`, `product.template`, `sale.order`, `purchase.order`, `stock.picking`, `account.move`, `mrp.production` must retain their exact `_name`.
- **NEVER rename database tables (`_table`) or SQL columns**: Tables like `res_partner`, `sale_order`, `account_move` must remain unchanged to preserve existing database records and foreign key constraints.
- **NEVER rename relational fields**: Fields like `partner_id`, `product_id`, `order_line`, `picking_id` must retain their technical Python attribute names.

### Rule 2: Pure Presentation-Tier Transformation
- All SAP lexicon transformations must be achieved exclusively via:
  - Model `_description`: e.g. `_description = "Business Partner (BP)"`.
  - Field `string` and `help` parameters in Python declarations.
  - XML views: `<field name="partner_id" string="Business Partner"/>`.
  - Action window titles: `<field name="name">SD Sales Orders</field>`.
  - Declarative menu records: `<record model="ir.ui.menu" id="...">`.

### Rule 3: Odoo 20 Constraint Standard
- All new or updated model constraints must use `models.Constraint` rather than deprecated `_sql_constraints`.

---

## 8. 10-Gate Release Verification Matrix

| Gate | Verification Domain | Tool / Command | Pass Criteria |
|:---:|:---|:---|:---|
| **Gate 1** | **Python AST Syntax & Compilation** | `.venv/bin/python tools/verify_gates_1_2.py --gate 1` | 460 Python files across 26 enterprise modules compile with 0 errors (Exit code 0) |
| **Gate 2** | **XML & QWeb Well-formedness** | `.venv/bin/python tools/verify_gates_1_2.py --gate 2` | 203 XML files across 26 enterprise modules parse cleanly with lxml (Exit code 0) |
| **Gate 3** | **Server Boot & Preload Integrity** | `.venv/bin/python insilos-bin -c insilos.conf -d odoo20_dev --stop-after-init` | Preloads 697+ modules; initializes registry; exits cleanly with code 0 |
| **Gate 4** | **PEP 451 Import Hook Interoperability** | `.venv/bin/python tools/test_insilos_import_hook.py` | 8/8 unit tests pass in < 1.0s verifying dynamic namespace proxying (Exit code 0) |
| **Gate 5** | **Perimeter Security Gateway API Contract** | `.venv/bin/python tools/test_insilos_perimeter_gateway.py` | 20/20 test cases pass; `Server: insilos/20.0` enforced; errors masked (Exit code 0) |
| **Gate 6** | **App Icons & Branding Asset Integrity** | `.venv/bin/python tools/check_app_icons_integrity.py` | 62+ launcher icons meet Phosphor Duotone contract; 0 invalid assets (Exit code 0) |
| **Gate 7** | **Counter Code Security Invariance** | `python3 scripts/counter_code_scanner.py --scope addons/web addons/base branding enterprise/web_enterprise --max-allowed-detections 0` | 0 genesis detections across target scopes; exit code 0 |
| **Gate 8** | **Ported Enterprise Modules E2E Lifecycle** | `node tools/test_enterprise_ported_modules_e2e.js` | 26/26 ported modules verified installed; 0 UI brand leaks; 0 errors (Exit code 0) |
| **Gate 9** | **Full 72-App Parallel Playwright Suite** | `node test_all_home_apps_parallel.js` | 72/72 apps pass with 0 uncaught errors and 0 error dialogs (Exit code 0) |
| **Gate 10** | **UI Brand & Lexicon Leak Sweep** | `node tools/sweep_ui_all_apps.js` | 5 public routes + 28 core authenticated apps report 0 genesis leaks (Exit code 0) |

---

## 9. Automated Test Runner Architecture (`tools/run_hard_fork_council_gates.py`)

The integrated test runner at `tools/run_hard_fork_council_gates.py` provides unified command-line execution for the full 10-Gate Matrix:

```bash
# Execute the full 10-Gate Release Verification Matrix
tools/run_hard_fork_council_gates.py

# Execute specific gate subsets (e.g. fast static gates)
tools/run_hard_fork_council_gates.py --gates 1,2,4,6

# Execute with verbose real-time diagnostic output
tools/run_hard_fork_council_gates.py --verbose

# Stop execution immediately upon the first failing gate
tools/run_hard_fork_council_gates.py --stop-on-fail

# Export structured JSON audit report for CI/CD pipelines
tools/run_hard_fork_council_gates.py --json --output audit_reports/council_gates_report.json

# Execute with milestone M5 pending awareness (marks Gate 7 as known pending requirement)
tools/run_hard_fork_council_gates.py --allow-pending-m5
```

### Exit Code Semantics:
- `0`: All selected gates passed (or passed with accepted warnings).
- `1`: One or more selected gates failed.
- `124`: Gate execution timed out.
