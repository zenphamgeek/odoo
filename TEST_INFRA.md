# TEST INFRA: Insilos App-Launcher Icon Redesign Campaign

## 1. Executive Summary & Test Infrastructure Overview
This document defines the comprehensive end-to-end (E2E) testing infrastructure, architecture, and multi-tier verification methodology for the **Insilos App-Launcher Icon Redesign Campaign**.

The icon redesign transitions the entire Insilos Platform (77 root launcher apps, 230+ modules, webclient home screen, and settings tabs) from legacy Phosphor Duotone raw line icons to the **Insilos Horizon-Carbon Tile (HCT)** standard—a flat light squircle tile (`x="12" y="12" width="232" height="232" rx="48" ry="48"` on a 256x256 master grid) with two-tone domain-colored geometric glyphs compliant with IBM Carbon 11 density and SAP Fiori Horizon domain taxonomy.

The test suite enforces zero regressions across all operational lifecycles (database initialization, module installs, upgrades, attachment deletions, and server restarts) with **Strict Database Schema Invariance** (0 DDL / 0 table/column mutations).

---

## 2. Testing Philosophy & 4-Tier Opaque-Box Methodology

### Core Testing Tenets
1. **Opaque-Box Empirical Grounding**: Tests inspect observable outputs—HTTP endpoints, database records (`ir.ui.menu`, `ir.attachment`), PostgreSQL filestore checksums, file system binary headers, and live browser DOM properties. No artificial mocks or bypass facades.
2. **Progressive Testability & Defect Escalation**: The test suite accurately discriminates between passing features and un-remediated defects. If an implementation defect is discovered (e.g., missing XML `web_icon` declaration, unregenerated disk asset, or contrast violation), the test harness faithfully reports the defect for implementation remediation.
3. **Adversarial Boundary Hardening**: Tests actively exercise edge conditions: attachment deletion, payload corruption, missing filestore files, uninstalled/phantom modules, and multi-mode theme toggling.
4. **WCAG AA/AAA Mathematical Compliance**: Visual auditing calculates exact mathematical relative luminance and contrast ratios ($Ratio \ge 4.5:1$) for all icons and labels across Light and Dark modes.

---

## 3. Test Suite Architecture & Deliverables

The E2E test infrastructure consists of two synchronized, complementary testing engines:

```
Insilos E2E Icon Verification Infrastructure
├── tools/test_launcher_icons_e2e.py        # Python 3.12 Backend & System E2E Runner (Tiers 1, 2, 3)
│    ├── Tier 1: Feature Coverage Suite (77 Root Menus, Dual Assets, Payloads)
│    ├── Tier 2: Boundary & Corner Case Suite (Self-Healing, Corrupt Data, Fallbacks)
│    └── Tier 3: Combinatorial Suite (Registry Hooks, Checksums, Server Bootability)
│
├── tools/audit_launcher_icons_visual.js     # Playwright Headless Browser Visual Auditor (Tier 4)
│    ├── Light Mode Audit (1920x1080 Viewport, WCAG Contrast, 0 Broken Images)
│    ├── Dark Mode Audit (body.o_dark_mode, High-Contrast Verification)
│    ├── Geometry & Signature Inspection (HCT Squircle vs Raw Line Icons)
│    └── High-Resolution Artifact Generation (PNG Screenshots & JSON Telemetry)
│
└── Configuration & Environment
     ├── Configuration: insilos.conf
     ├── Database: odoo20_dev (PostgreSQL)
     └── Python Runtime: .venv/bin/python (3.12.13)
```

---

## 4. 4-Tier Detailed Test Specifications

### Tier 1: Feature Coverage (>=5 Tests per Feature Area)
Exercises primary functional requirements across all root menus, backend payloads, disk assets, and web client serializers:

- **Area 1.1: Root Menu Discovery & Resolution (All 77 Root Menus)**
  - `test_tier1_root_menu_count`: Discovers all 77 root menus in `odoo20_dev` (`parent_id = False`).
  - `test_tier1_root_menu_valid_base64_data`: Asserts every root menu resolves to non-empty image data via `web_icon_data` or `_compute_web_icon_data(web_icon)`.
  - `test_tier1_root_menu_payload_size`: Asserts resolved payload byte size is non-trivial (size > 100 bytes).
  - `test_tier1_root_menu_valid_mimetypes`: Asserts MIME type is strictly `image/png` or `image/svg+xml`.
  - `test_tier1_root_menu_zero_default_cube`: Asserts zero root menus resolve to or point to `/web/static/img/default_icon_app.png`.

- **Area 1.2: Dual Companion Assets on Disk**
  - `test_tier1_disk_asset_presence`: Resolves `web_icon="<module>,<path>"` and asserts the declared file exists on disk.
  - `test_tier1_disk_companion_svg_and_png`: Asserts both SVG and PNG companion assets exist for every module icon.
  - `test_tier1_disk_png_binary_magic_header`: Inspects all PNG icons for magic header `\x89PNG\r\n\x1a\n`.
  - `test_tier1_disk_svg_valid_viewbox`: Inspects SVG icons for `<svg` and standard `viewBox="0 0 256 256"`.

- **Area 1.3: Special Targets & Dual Companion Verification**
  - `test_tier1_special_target_base_modules`: Checks `odoo/addons/base/static/description/modules.png` and `modules.svg`.
  - `test_tier1_special_target_base_settings`: Checks `odoo/addons/base/static/description/settings.png` and `settings.svg`.
  - `test_tier1_special_target_mail_discuss`: Checks `addons/mail/static/description/icon.png` and `icon.svg`.
  - `test_tier1_special_target_timesheet`: Checks `addons/hr_timesheet/static/description/icon_timesheet.png` and `icon.svg`.
  - `test_tier1_special_target_mrp_workorder`: Checks `enterprise/mrp_workorder/static/description/mrp_display_icon.png` and `icon.svg`.

- **Area 1.4: Web Client Menu Payload Serializer Contract**
  - `test_tier1_load_menus_contract`: Invokes `ir.ui.menu.load_menus(debug=False)` and verifies all visible apps return valid base64 data URIs.
  - `test_tier1_load_web_menus_contract`: Invokes `ir.ui.menu.load_web_menus(debug=False)` and verifies webclient JSON dictionary structure.
  - `test_tier1_web_icon_data_format`: Asserts `webIconData` strings strictly match `^data:image/(png|svg\+xml);base64,[A-Za-z0-9+/=]+$`.

- **Area 1.5: Physical Fallback Asset Modernization**
  - `test_tier1_fallback_asset_exists`: Verifies `addons/web/static/img/default_icon_app.png` exists.
  - `test_tier1_fallback_asset_format`: Verifies fallback asset is a valid, uncorrupted PNG binary.
  - `test_tier1_fallback_asset_not_legacy_purple`: Verifies fallback asset does not contain legacy purple cube signatures (`#714B67`).

---

### Tier 2: Boundary & Corner Cases (System Robustness & Self-Healing)
Exercises failure modes, missing data, and error recovery:

- **Area 2.1: Attachment Deletion & Self-Healing Recovery**
  - `test_tier2_attachment_deletion_load_menus_fallback`: In an isolated transaction, unlinks the `ir.attachment` for a sample root menu (`mail.menu_root_discuss`). Calls `load_menus()` and asserts the menu icon is dynamically served from disk without defaulting to purple cube.
  - `test_tier2_attachment_deletion_reconciliation`: Deletes attachment and runs `ir.ui.menu._insilos_sync_icons()`. Asserts the attachment is automatically recreated in the database.

- **Area 2.2: Corrupted & Empty Attachment Recovery**
  - `test_tier2_corrupt_attachment_empty_raw`: Injects an empty attachment (`raw = b""`) and asserts `load_menus()` detects the zero-byte payload and recovers the icon from disk.
  - `test_tier2_corrupt_attachment_invalid_binary`: Injects corrupted garbage bytes (`raw = b"CORRUPTED_GARBAGE"`) and asserts system handles gracefully.

- **Area 2.3: Physically Missing Filestore File Handling**
  - `test_tier2_missing_filestore_file_handling`: Simulates an attachment pointing to a missing file on disk (`os.path.exists == False`). Asserts `_insilos_sync_icons()` and `load_menus()` catch the discrepancy and heal from module disk sources without crashing.

- **Area 2.4: Unknown & Uninstalled Module Fallback Tile**
  - `test_tier2_unknown_module_fallback`: Evaluates a synthetic menu item pointing to `nonexistent_module,static/description/icon.png`. Asserts it falls back to the clean neutral fallback tile without raising unhandled exceptions.
  - `test_tier2_missing_web_icon_fallback`: Evaluates a menu item with `web_icon = False`. Asserts fallback behavior.

- **Area 2.5: Module Upgrade (`-u`) & Install (`-i`) Simulation**
  - `test_tier2_module_upgrade_menu_write_resilience`: Simulates a module upgrade by calling `write({'web_icon': m.web_icon})`. Asserts `web_icon_data` is properly refreshed and retains new icon checksums.

---

### Tier 3: Combinatorial & Cross-Feature Integration
Exercises interactions between database transactions, server bootability, and registry hooks:

- **Area 3.1: Registry Reload & Self-Healing Hook Idempotence**
  - `test_tier3_register_hook_idempotence`: Runs `_register_hook()` sequentially 3 times. Asserts subsequent runs report 0 modifications, no duplicate attachments, and clean exit.
- **Area 3.2: Database vs Disk Checksum Alignment**
  - `test_tier3_checksum_alignment`: Computes SHA1 of disk companion icons and compares with `ir.attachment.checksum` for all root menus. Reports alignment percentage.
- **Area 3.3: Server Bootability & Graceful Shutdown**
  - `test_tier3_server_boot_clean_exit`: Executes `.venv/bin/python insilos-bin -c insilos.conf -d odoo20_dev --stop-after-init` via subprocess. Asserts returncode 0 with 700+ modules loaded.
- **Area 3.4: Strict Database Schema Invariance Guard**
  - `test_tier3_schema_invariance_guard`: Queries PostgreSQL `information_schema.columns` for table `ir_ui_menu`. Asserts zero ad-hoc columns or schema alterations exist.

---

### Tier 4: Real-World Visual & WCAG Contrast Audit (Playwright)
Headless Chromium automation auditing the rendered home screen (`/insilos`) in both Light and Dark modes:

- **Area 4.1: Authentication & Navigation**
  - Acquires admin session cookie via `/web/login`.
  - Sets viewport to 1920x1080.
  - Navigates to `/insilos` with `waitUntil: 'load'`, waiting for `.o_app` selector.
- **Area 4.2: Light Mode Visual Audit**
  - Captures full-viewport screenshot: `tools/artifacts/launcher_visual/launcher_light_mode.png`.
  - Extracts all rendered `.o_app` elements.
  - Verifies 0 broken images (`img.naturalWidth > 0` and `img.complete === true`).
  - Verifies 0 default purple cube icons.
  - Measures text contrast ratio of `.o_caption` against `.o_app` card background ($Ratio \ge 4.5:1$).
  - Measures icon contrast against `.o_app` card background.
- **Area 4.3: Dark Mode Visual Audit**
  - Toggles `body.o_dark_mode` and `[data-bs-theme="dark"]`.
  - Captures full-viewport screenshot: `tools/artifacts/launcher_visual/launcher_dark_mode.png`.
  - Verifies dark surface tokens (`#070B14`, `#141E33`).
  - Measures text contrast ratio of `.o_caption` against dark card background ($Ratio \ge 4.5:1$).
  - Verifies 0 broken images and 0 default purple cube icons in dark mode.
- **Area 4.4: HCT Squircle vs Raw Line Icon Discrimination**
  - Verifies launcher icons incorporate Horizon-Carbon Tile squircle geometry (`rx="48"` or squircle background container) rather than raw uncontained line icons.

---

## 5. Feature Coverage & Traceability Matrix

| Feature ID | Feature Name | Tier 1 (Functional) | Tier 2 (Boundary) | Tier 3 (Cross-Feature) | Tier 4 (Visual/WCAG) |
|---|---|:---:|:---:|:---:|:---:|
| **F1** | 77 Root Menu Icons | ✓ (Discovery & Size) | ✓ (Missing Icon Fallback) | ✓ (DB vs Disk Alignment) | ✓ (DOM Verification) |
| **F2** | Base64 Image Payload | ✓ (MIME & Base64 Valid) | ✓ (Corrupt Payload Guard) | ✓ (Attachment Integrity) | ✓ (Image Decoding) |
| **F3** | Dual Companion Assets | ✓ (SVG + PNG on Disk) | ✓ (Disk Fallback Read) | ✓ (File Checksum SHA1) | ✓ (Multi-DPI Rendering) |
| **F4** | Special Targets | ✓ (Base, Mail, Timesheet) | ✓ (Custom Path Routing) | ✓ (Registry Hook Scan) | ✓ (Card Rendering) |
| **F5** | Zero Purple Cube | ✓ (0 Default Cube) | ✓ (Never Reverts on Unlink)| ✓ (Server Boot Guard) | ✓ (0 Cube in DOM) |
| **F6** | Attachment Self-Healing| ✓ (Data Attachment Read) | ✓ (Unlink Auto-Recovery) | ✓ (_register_hook Idempotence) | ✓ (Live DOM Rendering) |
| **F7** | Module -u / -i Resilience | ✓ (Write Web Icon Recompute)| ✓ (Upgrade Simulation) | ✓ (Checksum Stability) | ✓ (Post-Upgrade DOM) |
| **F8** | Unknown App Tile | ✓ (Neutral Fallback Check) | ✓ (Phantom Module Fallback)| ✓ (Safe Exception Handling)| ✓ (Fallback Tile Render)|
| **F9** | Light Mode Contrast | ✓ (CSS Tokens) | ✓ (Alpha Blending Check) | ✓ (Theme Asset Loading) | ✓ (WCAG Ratio >= 4.5:1)|
| **F10** | Dark Mode Contrast | ✓ (Dark Tokens) | ✓ (Mode Switching) | ✓ (Dark Bundle Preload) | ✓ (WCAG Ratio >= 4.5:1)|
| **F11** | Zero Broken Images | ✓ (Valid Binary Headers) | ✓ (Zero-Byte File Catch) | ✓ (Clean HTTP Responses) | ✓ (naturalWidth > 0) |
| **F12** | Schema Invariance | ✓ (Standard Model Fields)| ✓ (0 DDL Migrations) | ✓ (PostgreSQL DDL Guard) | ✓ (Zero UI Errors) |

---

## 6. Execution Guide & Command Reference

### 6.1 Running the Python Multi-Tier Test Suite
```bash
# Run all Python tiers (Tier 1, Tier 2, Tier 3)
.venv/bin/python tools/test_launcher_icons_e2e.py

# Run specific tier
.venv/bin/python tools/test_launcher_icons_e2e.py --tier 1
.venv/bin/python tools/test_launcher_icons_e2e.py --tier 2
.venv/bin/python tools/test_launcher_icons_e2e.py --tier 3

# Run with verbose output and JSON telemetry persistence
.venv/bin/python tools/test_launcher_icons_e2e.py --verbose --json
```

### 6.2 Running the Playwright Visual & Contrast Audit
```bash
# Run headless browser visual and contrast audit
node tools/audit_launcher_icons_visual.js

# Custom output directory
node tools/audit_launcher_icons_visual.js --output-dir tools/artifacts/launcher_visual
```

### 6.3 Running the Full End-to-End Pipeline
```bash
# Execute Python multi-tier test harness and Playwright visual audit
.venv/bin/python tools/test_launcher_icons_e2e.py --tier all
```

---

## 7. Environmental & Runtime Pre-requisites
- **Python**: 3.12.13 in `/home/zen/O20/.venv`
- **Node.js**: v24.15.0 with `@playwright/test` / `playwright`
- **PostgreSQL Database**: `odoo20_dev` running on `localhost:5432`
- **Odoo Instance**: Running on `http://localhost:28069`
- **Configuration**: `/home/zen/O20/insilos.conf`
