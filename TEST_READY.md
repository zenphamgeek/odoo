# AL2C Operational Optimization — E2E Acceptance Test Suite Readiness (`TEST_READY.md`)

## 1. Overview & Verification Scope
This document specifies the operational verification protocol and acceptance test matrix for the **Lead-to-Cash (AL2C) Operational Optimization** track (`insilos_al2c`) across Tiers 1 through 4.

The acceptance suite is codified in:
`addons/insilos_al2c/tests/test_al2c_operational_e2e.py`

Target Test Class:
`TestAl2cOperationalE2E`

---

## 2. Environment & Database Isolation Notice
- **Database Target**: `insilos20_dev` (PostgreSQL local instance at `127.0.0.1:5434`).
- **Production Guardrail**: All tests are strictly isolated to the development database `insilos20_dev`. Under NO circumstances are tests executed against production databases (`innoria_prod`, `innokafe_prod`).
- **Test User Isolation**: Dedicated test partners, users (`pm_user`, `consultant_user`), sale orders, and analytical staging records are created within standard Odoo `TransactionCase` rollback boundaries.

---

## 3. Official Test Execution Command
Run the test runner using the dedicated test port (`28176`):

```bash
/home/zen/O20/.venv/bin/python3 odoo-bin -c insilos.conf -d insilos20_dev -u insilos_al2c --test-tags /insilos_al2c:TestAl2cOperationalE2E --stop-after-init --http-port 28176
```

---

## 4. Tier Coverage & Acceptance Matrix

| Tier | Test Identifier | Covered Specifications | Acceptance Criteria |
| :--- | :--- | :--- | :--- |
| **Tier 1** | `test_01_tier1_r1_catalog_skus_and_commercial_alignment` | Catalog SKUs, VAT Classification (Decree 70/2025), Invoicing Policy, VND Pricing | 21 SKUs verified: 12 Implementation (`kct`), 6 Recurring (`kct`/`gtgt_10`), 3 Add-on (`kct`/`gtgt_10`); Invoicing policies match service milestone vs prepaid/postpaid standards; Default VND pricelist populated. |
| **Tier 1** | `test_02_tier1_r2_multirepo_scanner_execution` | Multi-Repo Scanner execution across 4 repos (`odoo-ce`, `odoo-ee`, `innoria-custom`, `innokafe`) | Scanner executes without unhandled exceptions; Outputs valid Backlog JSON v2 schema; Identifies standard vs custom vs enterprise module categorizations. |
| **Tier 1** | `test_03_tier1_r3_sales_document_templates_compilation_and_branding` | Sales Document Templates compilation (`report_statement_of_work`, `report_sla_contract`) | Both QWeb XML templates compile and render cleanly with zero AI tells; Vietnamese commercial terminology verified; Legal Decree 70/2025 compliance confirmed. |
| **Tier 1** | `test_04_tier1_r4_stage_gates_and_budget_burn` | Stage Gates & Budget Burn Alert Trigger | Phase sequence locking strictly blocks skipping gates; Customer acceptance signoff unlocks billing eligibility; 85% timesheet burn alert triggers automated notification. |
| **Tier 1** | `test_05_tier1_r5_timesheet_staging_ingestion_and_approval` | Timesheet Staging, Structured Body Parsing & PM 1-Click Commit | Unstructured and pipe-delimited email bodies parsed; Employee auto-matched by email; SoD guardrail blocks self-approval; PM 1-click commit pushes to `account.analytic.line`. |
| **Tier 2** | `test_06_tier2_unapproved_milestone_invoice_blocked` | Unapproved Milestone Invoice Blocking & SoD Enforcement | Milestones lacking customer signoff deliver 0 quantity; Attempting to invoice delivers `UserError` or zero-value invoice lines; Consultant cannot approve own timesheets. |
| **Tier 2** | `test_07_tier2_timesheet_burn_boundary_84_vs_85_vs_86` | Boundary Testing: 84% vs 85% vs 86% Burn Alert | 84.0% effective hours = NO alert; Exactly 85.0% = Alert triggers; 86.0% = Warning flag preserved without duplicate spamming; Resetting hours clears alert. |
| **Tier 2** | `test_08_tier2_duplicate_email_submissions_and_deduplication` | Duplicate Submissions & Idempotent Deduplication | Identical email Message-ID or identical staging payloads detected; Duplicate records flagged with `state='duplicate'`; Intra-batch and row-level deduplication verified. |
| **Tier 2** | `test_09_tier2_corrupted_and_empty_excel_csv_handling` | Robustness Against Corrupted & Empty Excel / CSV Payloads | Empty CSV payload handled cleanly with `parse_status='error'`; Corrupted rows (>24 hours, negative hours) quarantined to `state='error'`; Valid `.xlsx` ingested via `openpyxl`. |
| **Tier 3** | `test_10_tier3_cross_feature_sales_to_timesheet_to_burn_to_milestone_to_invoice` | End-to-End Cross-Feature Pipeline Integration | SO confirmed -> Project generated -> Consultant logs timesheet -> 86% Burn alert fired -> PM commits timesheet -> Milestone signed off -> 15% invoice created & posted under Decree 70/2025. |
| **Tier 4** | `test_11_tier4_full_innoria_erp_activate_implementation_engagement_lifecycle` | Full Enterprise Activate Engagement Lifecycle | Master engagement contract (450M VND) traversed across all 5 sequential Q-Gates (Prepare 15%, Explore 25%, Realize 35%, Deploy 15%, Run 10%); Invariance gate locks verified; 100% delivered and invoiced across 5 sequential posted invoices. |

---

## 5. Pass/Fail Semantics & Gate Criteria
- **PASS Criteria**:
  - All 11 tests in `TestAl2cOperationalE2E` execute to completion with 0 errors, 0 failures, and 0 skipped.
  - Odoo process exits with exit code `0`.
  - Zero unhandled exceptions in the test runner log.
- **FAIL Criteria**:
  - Any `AssertionError`, `UserError`, or unhandled Python exception during test execution.
  - Inability to acquire registry lock or database connectivity failure.
  - Discrepancy in VAT classification (`kct` vs `gtgt_10`) or pricing calculation.

---

## 6. Escalated Implementation Issues (Resolved & Verified)
1. **`addons/insilos_al2c/views/report_sales_documents.xml:208, 329`**:
   - `line.product_uom.name` referenced instead of `line.product_uom_id.name` for Odoo 20 compatibility.
   - Status: **RESOLVED & VERIFIED**. Updated to `line.product_uom_id.name`.
2. **`addons/insilos_al2c/models/al2c_timesheet_staging.py:217-233`**:
   - Attachment `raw_bytes` when returning `LocalBinaryFile` caused subscript error (`[:4]`).
   - Status: **RESOLVED & VERIFIED**. Model updated with lazy stream `.content` unwrapping.
3. **`addons/insilos_al2c/tests/test_sales_reports.py:199, 258`**:
   - Ampersand entities `&amp;` in assertions updated to match raw unescaped HTML serialization `&`.
   - Status: **RESOLVED & VERIFIED**. All 5 tests in `TestSalesReports` pass 100% green.

---

## 7. Multi-Suite Verification Summary (Local Development Database `insilos20_dev`)

| Test Suite / Scope | Test Class / Tool | Tests | Result | Verification Evidence |
| :--- | :--- | :---: | :---: | :--- |
| **R1. Catalog & Pricing** | `TestAl2cPricing` | 9 | **PASS (100%)** | 9 post-tests passed in 1.48s, 0 failed, 0 errors |
| **R2. Multi-Repo Scanner** | `tools/multi_repo_scanner.py` | 8 | **PASS (100%)** | 8 test gates passed (71s runtime), 121 modules scanned across 4 repos |
| **R3. Sales Documents** | `TestSalesReports` | 5 | **PASS (100%)** | 5 post-tests passed in 2.71s, 0 failed, 0 errors, zero-tell audit confirmed |
| **R4. Activate Stage Gates** | `TestAl2cStageGates` | 4 | **PASS (100%)** | 4 post-tests passed in 2.21s, 0 failed, 0 errors, SoD and 85% burn verified |
| **R5. Timesheet Staging** | `TestAl2cTimesheetStaging` | 10 | **PASS (100%)** | 10 post-tests passed in 12.0s, 0 failed, 0 errors, Excel/CSV/gateway verified |
| **Cross-Stream E2E Suite** | `TestAl2cOperationalE2E` | 11 | **PASS (100%)** | 11 post-tests passed in 20.01s, 0 failed, 0 errors across Tiers 1-4 |
| **Total Automated Tests** | — | **47** | **ALL GREEN** | **Zero failures, zero regressions, 100% compliant** |

