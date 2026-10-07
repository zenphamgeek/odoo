# E2E Test Infra: UI/UX Modernization & Design System Compliance

## Test Philosophy
- Requirement-driven, opaque-box and system-level verification.
- Enforce Strict Schema Invariance (0 DDL) and zero compilation/pre-load regressions.
- Validate visual compliance against IBM Carbon Design System 11 and SAP Fiori Horizon standards.

## Feature Inventory & Test Coverage
| # | Feature | Verification Mechanism | Status |
|---|---------|------------------------|--------|
| 1 | Server Pre-Load Integrity | `.venv/bin/python insilos-bin -c insilos.conf --stop-after-init` exits with code 0 | READY |
| 2 | Strict 0 DDL Invariance | `git diff HEAD -- addons/ enterprise/ -- '*.py'` yields 0 lines of diff | READY |
| 3 | SCSS Asset Compilation | `ir.qweb._get_asset_bundle('web.assets_backend', css=True).css()` & `web.assets_web_dark` compile via libsass with exit code 0 | READY |
| 4 | Carbon 11 Spacing & Radii | Verify CSS tokens `--insilos-radius-sm: 4px`, 0 Telegram 20px pill buttons on `.btn-primary` | READY |
| 5 | Fiori Horizon KPI Stat-Buttons | Verify `.oe_stat_button` layout (value bold top, label uppercase bottom, 3-state micro-trend) | READY |
| 6 | 34px Compact Table Rows | Verify `tr.o_data_row` height is 32px–34px with tabular numbers and sticky first column | READY |
| 7 | Form Sheet & Chatter Width | Verify form sheet width >= 840px on viewports down to 1280px without horizontal overflow | READY |

## Execution Commands
1. Pre-Load Check:
   `.venv/bin/python insilos-bin -c insilos.conf --stop-after-init`
2. Schema Diff Check:
   `git diff HEAD -- addons/ enterprise/ -- '*.py'`
3. SCSS Compilation Check:
   `.venv/bin/python -c "import insilos; from insilos.tools import config; from insilos.modules.registry import Registry; config.parse_config(['-c', 'insilos.conf', '-d', 'odoo20_dev']); registry = Registry('odoo20_dev'); with registry.cursor() as cr: env = insilos.api.Environment(cr, insilos.SUPERUSER_ID, {}); b = env['ir.qweb']._get_asset_bundle('web.assets_backend', css=True, js=False); assert len(b.css()) > 0; b_dark = env['ir.qweb']._get_asset_bundle('web.assets_web_dark', css=True, js=False); assert len(b_dark.css()) > 0; print('ASSETS COMPILED CLEANLY (EXIT CODE 0)')"`
