# Project: Innokafe Autonomous Campaign

## Architecture
- **Branding & Assets**: Official vector logo assets derived from `/home/zen/Downloads/logo Innokafe brown(1).svg` residing in `enterprise/innokafe_website/static/src/img/branding/` (`innokafe_logo_master.svg`, `innokafe_logo_dark.svg`, `innokafe_logo_white.svg`, `innokafe_mark_symbol.svg`).
- **Database Layer**: PostgreSQL database `innokafe_prod` on port 5434 (and production PgBouncer). Views `website.option_header_brand_logo` (ID: 1046) and `website.footer_custom` (IDs: 1059, 1696) maintained with zero-DDL compliance (100% parameter-bound DML updates).
- **Frontend SCSS & Templates**: `enterprise/innokafe_website/static/src/scss/innokafe_theme.scss`, `innokafe_style.scss`, `enterprise/innokafe_website/views/website_templates.xml`, `home.xml`.
- **Automated Audit Engines**:
  - `pixel_layout_scanner.js` (Desktop 1440x900, Tablet 768x1024, Mobile 375x812)
  - `website_audit_runner.js` / `innokafe_website_audit.js` (6 routes: `/`, `/story`, `/products`, `/taste-profiler`, `/solutions-b2b`, `/contactus`)
- **Swarm Infrastructure**: AGY Fleet MCP server (Claude Opus 4.6 Thinking & Gemini 3.8 Flash High) across 37 nodes.
- **Production Kubernetes Cluster**: 3 active pods (`insilos-saas-app-575f447b-bfhnb`, `csm5r`, `mgxdt`) synchronized via `tools/deploy_innokafe_production.py`.

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Official Vector Logo Asset Harmonization | Refine Master, Dark Bazan, White, and Mark Symbol SVGs in `static/src/img/branding/` | M1 | Survey |
| 2 | Database arch_db Clean-up (Zero-DDL) | Purge fake text logos from views 1046, 1059, 1696 in `innokafe_prod` | M1 | Survey |
| 3 | Tooling Sync Script Permanent Fix | Update `tools/sync_innokafe_views_db.py` to write vector `<img ...>` tag | M1 | Survey |
| 4 | DOM Vector Logo Verification Suite | Playwright test asserting 100% SVG logos on Navbar, Sticky, Footer, Drawer Cart | M1 | Survey |
| 5 | WCAG AAA Contrast Recalibration | Fix 5 badge contrast issues in `home.xml` and `website_templates.xml` | M2 | Survey |
| 6 | Touch Target Ergonomics & Button Sizing | Enforce min-height 44px on buttons and 36px on footer links | M2 | Survey |
| 7 | Mobile Grid Gutter Overflow Remediation | Resolve `.row.g-5` negative margin overflow on 375px mobile screens | M2 | Survey |
| 8 | Pixel Layout Scanner Enhancement | Add visible section filtering and streaming media handling to scanner | M2 | Survey |
| 9 | Grade A+ Pixel Layout Verification | Achieve 100/100 (Grade A+) on Desktop, Tablet, and Mobile viewports | M2 | Survey |
| 10 | Multi-Route Visual & Semantic Audit | Audit 6 routes against Specialty Coffee 4-Không, Terroir, SCA 84+, Hot-Air | M3 | Survey |
| 11 | Pod Ephemeral Video Stream Restoration | Re-distribute missing video assets (`innokafe_coffee_pour_16x9_opt.mp4`) to pods | M4 | Survey |
| 12 | AGY Fleet Parallel Vibe Coding Swarm | Mobilize Claude Opus (review) and Gemini 3.8 Flash High (parallel code) | M4 | Survey |
| 13 | Multi-Pod Zero-Downtime Deployment | Synchronize code and assets to all 3 pods, pre-warm assets, rolling reload | M4 | Survey |
| 14 | Strict Schema Invariance Enforcement | Verify 0 DDL mutations across `odoo20_dev`, `insilos20_dev`, `innoria_prod`, `innokafe_prod` | M4 | Survey |
| 15 | Multi-Gate Comprehensive Acceptance Gate | Execute Quality Gate, E2E Suite, Playwright live tests, and Forensic Audit | M5 | Survey |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Official Vector Logo & DB Purge | SVG assets, DB arch_db clean-up, sync script update, DOM verification | none | DONE |
| M2 | Pixel Layout & Responsive Hardening | WCAG AAA contrast, touch targets, mobile gutter, 100/100 Grade A+ | none | DONE |
| M3 | Multi-Route Visual & Content Audit | 6 routes audit, content alignment, video streams verification | M1, M2 | DONE |
| M4 | AGY Fleet Swarm & Multi-Pod Deployment | Fleet parallelization, pod code/video sync, warmup, schema invariance | M1, M2 | PLANNED |
| M5 | Final E2E Acceptance & Forensic Audit | 7-Gate Quality Gate, E2E suite, live verification, forensic audit | M1, M2, M3, M4 | PLANNED |

## Interface Contracts
### Vector Branding Assets ↔ QWeb Templates
- `innokafe_logo_master.svg`: Dimensions 805.6 x 232.6, rendered at height 38px in `.navbar-brand img`.
- `innokafe_logo_white.svg`: Rendered at height 38px in `#footer img`.
- `innokafe_mark_symbol.svg`: Rendered at 28x28px in Cart Drawer header and 512x512 favicon.

### Database arch_db ↔ Odoo QWeb View Engine
- Zero-DDL guarantee: Updates executed via `UPDATE ir_ui_view SET arch_db = ...::jsonb, write_date = NOW()`.
- No table schema, column definitions, or constraints altered.

## Code Layout
- `enterprise/innokafe_website/static/src/img/branding/`: Master vector assets.
- `enterprise/innokafe_website/static/src/scss/`: `innokafe_theme.scss`, `innokafe_style.scss`.
- `enterprise/innokafe_website/views/`: `website_templates.xml`, `home.xml`, `story.xml`, `products.xml`.
- `tools/`: `cleanup_innokafe_fake_logos_db.py`, `sync_innokafe_views_db.py`, `test_innokafe_logo_dom.js`, `deploy_innokafe_production.py`, `verify_schema_invariance.py`.
- `.agents/skills/screenshot-pixels-scan/scripts/`: `pixel_layout_scanner.js`.
