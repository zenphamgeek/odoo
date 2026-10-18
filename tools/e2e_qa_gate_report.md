# Insilos O20 & Innoria Master E2E QA Gate Report

- **Generated At (UTC)**: `2026-10-18T12:01:53.397041+00:00`
- **Mode**: `full`
- **Total Gates Executed**: `10`
- **Passed Gates**: `10`
- **Failed Gates**: `0`
- **Total Assertions (`[✓]`)**: `72`
- **Wall-Clock Duration**: `307.584s`
- **Overall Verdict**: **PASS**

## Gate Summary Matrix

| Gate ID | Category | Fast | Title | Commands | Assertions | Duration (s) | Status |
| :--- | :--- | :---: | :--- | :---: | :---: | :---: | :---: |
| `E2E-QA-01` | `website` | Yes | Public Website Brand, IBM Carbon v11, Poppins Typography & Header Menu Uniqueness | 2 | 4 | 11.26s | **PASS** |
| `E2E-QA-02` | `website` | No | Public AI Concierge, Service Configurator & Grounded RAG Lead-to-CRM Flow | 1 | 9 | 35.50s | **PASS** |
| `E2E-QA-03` | `domain` | Yes | Sales-First Partner Onboarding, Tiering, Companion Docs (TPL-ONB-01..04) & Payment Gate | 1 | 5 | 3.99s | **PASS** |
| `E2E-QA-04` | `domain` | Yes | Project Delivery, SAP Activate Stage Gates & Timesheet-to-1C26TAA E-Invoice Pipeline | 1 | 6 | 41.45s | **PASS** |
| `E2E-QA-05` | `domain` | No | Knowledge Management & Grounded SOP-RAG Chatbot (SOP-DGM-12) | 1 | 1 | 25.67s | **PASS** |
| `E2E-QA-06` | `domain` | No | Employee Self-Service Hub (HomeMenu), Statutory VN 2026 Payroll, VCB DigiBiz 11-Col Export & ISO 27701 Masking | 1 | 12 | 4.89s | **PASS** |
| `E2E-QA-07` | `domain` | No | KPI & SWE Skill Framework + OKR, 360° Appraisal & Project PDCA (SOP-DGM-10/11) | 2 | 2 | 58.57s | **PASS** |
| `E2E-QA-08` | `domain` | No | Documents Multi-Level Tree & Google Drive Shared-With-Me RBAC Matrix | 1 | 10 | 35.68s | **PASS** |
| `E2E-QA-09` | `ui` | Yes | Playwright Dual-Theme (Light <-> Dark) & CRM/Documents Luminance E2E | 2 | 1 | 49.35s | **PASS** |
| `E2E-QA-10` | `ui` | Yes | Playwright Master User Journeys E2E (Public Nav, AI Concierge, HomeMenu Hub, Documents Tree Switcher, CRM Form) | 1 | 22 | 41.24s | **PASS** |

## Detailed Gate Evidence

### E2E-QA-01: Public Website Brand, IBM Carbon v11, Poppins Typography & Header Menu Uniqueness [PASS]
- **Category**: `website` | **Fast Gate**: `True` | **Duration**: `11.26s`
- **Command**: `python3 tools/audit_header_menu_collision.py --check` — **PASS** (`0.80s`, `2` assertions)
  ```text
  [✓] insilos20_dev             Menus: 33   Collisions: 0
  [✓] innoria_prod              Menus: 33   Collisions: 0
  ```
- **Command**: `python3 tools/test_innoria_website_brand_and_content_audit.py` — **PASS** (`10.46s`, `2` assertions)
  ```text
  [✓] Source audit passed: 100% INNORIA primary website brand, IBM Carbon v11 design system, Poppins sans-serif typography & zero explicit client/vendor/competitor names.
  [🎉] PATCH 39 & PATCH 41 INNORIA WEBSITE BRAND, IBM CARBON V11 & POPPINS TYPOGRAPHY AUDIT PASSED (EXIT 0)
  ```

### E2E-QA-02: Public AI Concierge, Service Configurator & Grounded RAG Lead-to-CRM Flow [PASS]
- **Category**: `website` | **Fast Gate**: `False` | **Duration**: `35.50s`
- **Command**: `python3 tools/test_website_concierge_and_marketing.py` — **PASS** (`35.50s`, `9` assertions)
  ```text
  [✓] insilos20_dev [1/4]: /innoria/ai_concierge/services_catalog verified (6 services, 13 live SKUs)
  [✓] insilos20_dev [2/4]: /innoria/ai_concierge/estimate_service verified (sw_squad=1.140.000.000 VNĐ, sw_turnkey=480.000.000 VNĐ, erp=150.000.000 VNĐ)
  [✓] insilos20_dev [3/4]: /innoria/ai_concierge/query verified across all 6 service pillars with grounded citations, service_cards & suggested_actions
  [✓] insilos20_dev [4/4]: /innoria/ai_concierge/book_lead + /health + AB-PCT + ESIH + DDK-CDLQ + Savepoint Isolation verified (lead_id=358, expected_revenue=1,140,000,000 VND, tags=['AI Concierge Interactive', 'Co-Engineering Squad (TT 13/2020)', 'Innoria Software Services'], marketing_campaign_enrolled=True, quarantine_ledger_size=5)
  [✓] innoria_prod [1/4]: /innoria/ai_concierge/services_catalog verified (6 services, 13 live SKUs)
  [✓] innoria_prod [2/4]: /innoria/ai_concierge/estimate_service verified (sw_squad=1.140.000.000 VNĐ, sw_turnkey=480.000.000 VNĐ, erp=150.000.000 VNĐ)
  [✓] innoria_prod [3/4]: /innoria/ai_concierge/query verified across all 6 service pillars with grounded citations, service_cards & suggested_actions
  [✓] innoria_prod [4/4]: /innoria/ai_concierge/book_lead + /health + AB-PCT + ESIH + DDK-CDLQ + Savepoint Isolation verified (lead_id=64, expected_revenue=1,140,000,000 VND, tags=['AI Concierge Interactive', 'Co-Engineering Squad (TT 13/2020)', 'Innoria Software Services'], marketing_campaign_enrolled=True, quarantine_ledger_size=10)
  [🎉] ALL INNORIA AI CONCIERGE SERVICE CATALOG, PRICING CONFIGURATOR, GROUNDED QUERY & MARKETING CAMPAIGN CHECKS PASSED (EXIT 0)
  ```

### E2E-QA-03: Sales-First Partner Onboarding, Tiering, Companion Docs (TPL-ONB-01..04) & Payment Gate [PASS]
- **Category**: `domain` | **Fast Gate**: `True` | **Duration**: `3.99s`
- **Command**: `python3 tools/test_dgm_partner_onboarding.py` — **PASS** (`3.99s`, `5` assertions)
  ```text
  [✓] insilos20_dev: 8 canonical DGM partners (PTN-DGM-2026-0001..0008 incl. AIfin & KTT Khang Trường Thịnh), 32 companion documents (TPL-ONB-01..04), SOP-DGM-09 Software Contracts (TPL-SW-MTI-01..04 & TPL-SW-KTT-01..04), 5 Drive Logo PNGs, 22 Master Standardized Templates, 3 SOP-DGM-07 SKUs, 2 SOP-DGM-08 Official E-Invoiced Timesheet Sheets, 0 empty folders, and SOP-DGM-06/07/08/09 Knowledge Articles verified
  [✓] innoria_prod: 8 canonical DGM partners (PTN-DGM-2026-0001..0008 incl. AIfin & KTT Khang Trường Thịnh), 32 companion documents (TPL-ONB-01..04), SOP-DGM-09 Software Contracts (TPL-SW-MTI-01..04 & TPL-SW-KTT-01..04), 5 Drive Logo PNGs, 22 Master Standardized Templates, 3 SOP-DGM-07 SKUs, 2 SOP-DGM-08 Official E-Invoiced Timesheet Sheets, 0 empty folders, and SOP-DGM-06/07/08/09 Knowledge Articles verified
  [✓] SOP-DGM-06 & SOP-DGM-07 Partner Tiering, Sales-First Confirm, Companion Docs (TPL-ONB-01..05), Staff Augmentation 140-180h SLA, OT 100%/150%, 5-Day Trial & Net 40 Gate verified
  [✓] K8s live production (`innoria_prod` SOP-DGM-06 & SOP-DGM-07): K8S_SOP_DGM_06_07_OK partners=8 companion_docs=32 empty_folders=0 kb06=1 kb07=1 kb09=1 skus=3
  [🎉] ALL SOP-DGM-06 & SOP-DGM-07 PARTNER ONBOARDING, STAFF AUGMENTATION & PAYMENT GATE CHECKS PASSED (EXIT 0)
  ```

### E2E-QA-04: Project Delivery, SAP Activate Stage Gates & Timesheet-to-1C26TAA E-Invoice Pipeline [PASS]
- **Category**: `domain` | **Fast Gate**: `True` | **Duration**: `41.45s`
- **Command**: `python3 tools/test_dgm_timesheet_to_invoice_pipeline.py` — **PASS** (`41.45s`, `6` assertions)
  ```text
  [✓] insilos20_dev: SOP-DGM-08 Knowledge Article, PRJ-NTF-202610-0001..0002, TS-DGM-202610-0001 (MTI 250M/270M VND) & TS-DGM-202610-0002 (AIfin 35M/37.8M VND), 8 companion billing HTML documents, 1C26TAA official E-Invoices, and 0 empty folders verified!
  [✓] innoria_prod: SOP-DGM-08 Knowledge Article, PRJ-NTF-202610-0001..0002, TS-DGM-202610-0001 (MTI 250M/270M VND) & TS-DGM-202610-0002 (AIfin 35M/37.8M VND), 8 companion billing HTML documents, 1C26TAA official E-Invoices, and 0 empty folders verified!
  [✓] Portal Controller Security: 2 @http.route endpoints verified with hmac.compare_digest & readonly=False
  [✓] Behavioral & Security Guardrails: UserError before customer_approved, revision_requested loop, 64-char SHA-256 signature hash, and MTI draft->official 1C26TAA E-Invoice state machine verified (savepoint rolled back cleanly)!
  [✓] K8s live production (`innoria_prod` SOP-DGM-08): K8S_SOP_DGM_08_OK kb08=1 ntfs=2 sheets=2 empty_folders=0
  === ALL SOP-DGM-08 TIMESHEET-TO-INVOICE PIPELINE VERIFICATION GATES PASSED (EXIT 0) ===
  ```

### E2E-QA-05: Knowledge Management & Grounded SOP-RAG Chatbot (SOP-DGM-12) [PASS]
- **Category**: `domain` | **Fast Gate**: `False` | **Duration**: `25.67s`
- **Command**: `python3 tools/test_dgm_knowledge_rag_chatbot.py` — **PASS** (`25.66s`, `1` assertions)
  ```text
  === ALL 8 SOP-DGM-12 KNOWLEDGE MANAGEMENT, AI CHAT BOX & SOP-RAG GATES PASSED (EXIT 0) ===
  ```

### E2E-QA-06: Employee Self-Service Hub (HomeMenu), Statutory VN 2026 Payroll, VCB DigiBiz 11-Col Export & ISO 27701 Masking [PASS]
- **Category**: `domain` | **Fast Gate**: `False` | **Duration**: `4.89s`
- **Command**: `python3 tools/test_dgm_hr_payroll_dashboard.py` — **PASS** (`4.89s`, `12` assertions)
  ```text
  [✓] insilos20_dev: 9 DGM employees (including DGM-009 Trần Văn Huỳnh Phố), 4 departments, 9 contracts, 18 payslips, and VCB bank accounts verified
  [✓] innoria_prod: 9 DGM employees (including DGM-009 Trần Văn Huỳnh Phố), 4 departments, 9 contracts, 18 payslips, and VCB bank accounts verified
  [✓] VCB DigiBiz 11-Column Excel (.xlsx) generator verified (0111000287863 leading zero preserved)
  [✓] ISO/IEC 27701 & Decree 13/2023/ND-CP Partial Masking, Need-to-Know RBAC, 30s Audited Reveal, TOCTOU FOR UPDATE NOWAIT Lock, Dual-Control SoD, OKR PDCA Loop, 360° HR Appraisal 9-Box & Mandatory SWE Skill Gate verified
  [✓] OWL 2 HomeMenu Employee Dashboard JS/XML/SCSS, Sovereign Dark Mode Tokens & dgm_hr_master_data.xml verified
  [✓] K8s live production (`innoria_prod`): K8S_BUNDLE_AND_DB_OK emps=9 depts=4 slips=18 okrs=12 aprs=9 pdca_tpls=4 asset_js_bytes=13802993
  [✓] insilos20_dev: 8 canonical DGM partners (PTN-DGM-2026-0001..0008 incl. AIfin & KTT Khang Trường Thịnh), 32 companion documents (TPL-ONB-01..04), SOP-DGM-09 Software Contracts (TPL-SW-MTI-01..04 & TPL-SW-KTT-01..04), 5 Drive Logo PNGs, 22 Master Standardized Templates, 3 SOP-DGM-07 SKUs, 2 SOP-DGM-08 Official E-Invoiced Timesheet Sheets, 0 empty folders, and SOP-DGM-06/07/08/09 Knowledge Articles verified
  [✓] innoria_prod: 8 canonical DGM partners (PTN-DGM-2026-0001..0008 incl. AIfin & KTT Khang Trường Thịnh), 32 companion documents (TPL-ONB-01..04), SOP-DGM-09 Software Contracts (TPL-SW-MTI-01..04 & TPL-SW-KTT-01..04), 5 Drive Logo PNGs, 22 Master Standardized Templates, 3 SOP-DGM-07 SKUs, 2 SOP-DGM-08 Official E-Invoiced Timesheet Sheets, 0 empty folders, and SOP-DGM-06/07/08/09 Knowledge Articles verified
  [✓] SOP-DGM-06 & SOP-DGM-07 Partner Tiering, Sales-First Confirm, Companion Docs (TPL-ONB-01..05), Staff Augmentation 140-180h SLA, OT 100%/150%, 5-Day Trial & Net 40 Gate verified
  [✓] K8s live production (`innoria_prod` SOP-DGM-06 & SOP-DGM-07): K8S_SOP_DGM_06_07_OK partners=8 companion_docs=32 empty_folders=0 kb06=1 kb07=1 kb09=1 skus=3
  [🎉] ALL SOP-DGM-06 & SOP-DGM-07 PARTNER ONBOARDING, STAFF AUGMENTATION & PAYMENT GATE CHECKS PASSED (EXIT 0)
  [🎉] ALL DGM HR, PAYROLL, ONBOARDING, LEAVING & VCB DIGIBIZ DASHBOARD CHECKS PASSED (EXIT 0)
  ```

### E2E-QA-07: KPI & SWE Skill Framework + OKR, 360° Appraisal & Project PDCA (SOP-DGM-10/11) [PASS]
- **Category**: `domain` | **Fast Gate**: `False` | **Duration**: `58.57s`
- **Command**: `python3 tools/test_dgm_kpi_skill_framework.py` — **PASS** (`30.84s`, `1` assertions)
  ```text
  ✅ ALL SOP-DGM-10 KPI & SOFTWARE ENGINEER SKILL UPGRADE GATE CHECKS PASSED ACROSS ALL DATABASES!
  ```
- **Command**: `python3 tools/test_dgm_okr_appraisal_project_pdca.py` — **PASS** (`27.73s`, `1` assertions)
  ```text
  === ALL SOP-DGM-11 PDCA PROJECT, 360° APPRAISAL & OKR TESTS PASSED (EXIT 0) ===
  ```

### E2E-QA-08: Documents Multi-Level Tree & Google Drive Shared-With-Me RBAC Matrix [PASS]
- **Category**: `domain` | **Fast Gate**: `False` | **Duration**: `35.68s`
- **Command**: `/usr/bin/python3 tools/test_documents_rbac_matrix.py` — **PASS** (`35.67s`, `10` assertions)
  ```text
  [✓] insilos20_dev: 978 folders & 7920 files verified across all 11 RBAC profiles (0 unmapped, 0 empty folders)
  [✓] innoria_prod: 978 folders & 7917 files verified across all 11 RBAC profiles (0 unmapped, 0 empty folders)
  [✓] ORM _compute_user_folder_id verified across all 978 active folders ('COMPANY' root & str(folder_id.id) children)
  [✓] Adversarial Test 1 (test_cross_tenant_isolation_boundary): CWE-284 cross-company boundary verified
  [✓] Adversarial Test 2 (test_dag_acyclicity_and_chunked_generation): DAG cycle interception & deterministic generation hash verified
  [✓] Autonomous Triage Cron RBAC Reconciliation ('rbac_reconciled') & INNO Customer Folder -> Project Linkage verified
  [✓] Runtime ORM RBAC enforcement (check_dgm_folder_rbac_access) verified across 5 role personas
  [✓] Adversarial Test 3 (test_working_tree_clean_gate): Dirty working tree fail-closed gate verified
  [✓] K8s live production (`innoria_prod`): K8S_RBAC_OK folders=981 files=7908 unmapped=0
  [🎉] ALL DGM & INNORIA DOCUMENTS RBAC MATRIX CHECKS PASSED (EXIT 0)
  ```

### E2E-QA-09: Playwright Dual-Theme (Light <-> Dark) & CRM/Documents Luminance E2E [PASS]
- **Category**: `ui` | **Fast Gate**: `True` | **Duration**: `49.35s`
- **Command**: `node tools/audit_crm_dual_theme.js` — **PASS** (`19.44s`, `0` assertions)
- **Command**: `node tools/test_theme_switch_dark_to_light.js` — **PASS** (`29.91s`, `1` assertions)
  ```text
  [🎉] ALL DARK -> LIGHT THEME SWITCH E2E LUMINANCE & SCREENSHOT CHECKS PASSED!
  ```

### E2E-QA-10: Playwright Master User Journeys E2E (Public Nav, AI Concierge, HomeMenu Hub, Documents Tree Switcher, CRM Form) [PASS]
- **Category**: `ui` | **Fast Gate**: `True` | **Duration**: `41.24s`
- **Command**: `node tools/test_e2e_qa_master_flows.js` — **PASS** (`41.23s`, `22` assertions)
  ```text
  ✓ /            -> HTTP 200 | Logo: logo_innoria_header.svg | Nav links: 8 (0 dupes) | Font: Poppins | CTA radius: 0px
  ✓ /platform    -> HTTP 200 | Logo: logo_innoria_header.svg | Nav links: 8 (0 dupes) | Font: Poppins | CTA radius: 0px
  ✓ /solutions   -> HTTP 200 | Logo: logo_innoria_header.svg | Nav links: 8 (0 dupes) | Font: Poppins | CTA radius: 0px
  ✓ /industries  -> HTTP 200 | Logo: logo_innoria_header.svg | Nav links: 8 (0 dupes) | Font: Poppins | CTA radius: 0px
  ✓ /about       -> HTTP 200 | Logo: logo_innoria_header.svg | Nav links: 8 (0 dupes) | Font: Poppins | CTA radius: 0px
  ✓ /pricing     -> HTTP 200 | Logo: logo_innoria_header.svg | Nav links: 8 (0 dupes) | Font: Poppins | CTA radius: 0px
  ✓ /contactus   -> HTTP 200 | Logo: logo_innoria_header.svg | Nav links: 8 (0 dupes) | Font: Poppins | CTA radius: 0px
  ✅ [Journey 1/5] PASSED!
  ✓ Step 2a (services_catalog): 6 service pillars, 13 SKUs, PCT token issued
  ✓ Step 2b (estimate_service): sw_squad (4 eng × 6 mos) -> 1.140.000.000 VNĐ (1140000000 VND) | ESIH token verified
  ✓ Step 2c (query): Grounded answer (1539 chars) with 5 citations
  ✓ Step 2d (health): status=ok, rag_chunks_active=158, esih=active
  ✅ [Journey 2/5] PASSED!
  ✓ HomeMenu (.o_insilos_emp_dashboard) visible | Single Light Logo (dark=none) | Masked PII: CCCD=089******917, Phone=090*****01, Bank=13****8161
  ✅ [Journey 3/5] PASSED!
  ✓ Documents .o_search_panel rendered (46 nodes, sample: All, Company, DGM · Công ty Cổ phần Người Bạn Số (Digimate JSC), 01. Pháp lý & Hành chính (Legal & Corporate), 378. Người Bạn Số - Thay đổi)
  ✓ Switched Documents view List (.o_switch_view.o_list) <-> Kanban (.o_switch_view.o_kanban) cleanly
  ✅ [Journey 4/5] PASSED!
  ✓ CRM Form Sheet (.o_form_sheet) width=1046px (> 900px) | bgColor=rgb(255, 255, 255)
  ✓ innoria_prod (http://localhost:28070) -> HTTP 200 | Logo: logo_innoria_header.svg | Font: Poppins | AI Concierge: ok
  ✅ [Journey 5/5] PASSED!
  🎉 ALL 5 LIVE BROWSER E2E QA MASTER JOURNEYS PASSED 100% (EXIT CODE 0)!
  ```
