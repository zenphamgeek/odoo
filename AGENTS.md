# Insilos Enterprise Odoo 20 Architectural Guidelines

> **Classification: Workspace Sovereign Rule • Priority: CRITICAL**  
> **Applies to: All coding agents operating within /home/zen/O20.**

---

## 1. Native QWeb & Bootstrap 5 SCSS Standards
- Never use synthetic inline CSS or generic external frameworks where native Odoo 20 / Bootstrap 5 components exist.
- Use native Odoo text effects, snippet options, and brand tokens.
- All styles must be encapsulated in SCSS using appropriate CSS variables (`--o-theme-*`).

## 2. OWL 2 Component Architecture
- Adhere strictly to Odoo Web Library (OWL 2) reactive component standards (`xml` templates, hooks `useState`, `useSubEnv`).
- Never introduce legacy Widget classes or manual DOM mutation outside the OWL reactive lifecycle.

## 3. Zero-Signature & Clean Enterprise Branding
- Strictly maintain Insilos enterprise branding without leaving raw, unstyled AI templates or placeholder text.
- Verify all changes with local test suites and live headless audits (`test_innokafe_playwright_e2e.js`, `unslop_scss_rigorous.py`).

## 4. Sovereign Dark Mode Token Architecture & Anti-Slop SCSS Standards
- **Banned Hex Fallbacks with `!important`**: Never write hardcoded light fallbacks inside `var()` coupled with `!important` (e.g. `var(--insilos-bg-subtle, #f8fafc) !important`). Semantic variables must always be guaranteed at root level.
- **Dual-Asset Bundle Segregation**: Never rely on `body.o_dark_mode` inside `web.assets_backend` as the primary dark mode strategy. Any module providing customized UI views, hubs, forms, or controls MUST register dedicated `.dark.scss` bundles under `web.assets_web_dark` in `__manifest__.py`, directly binding dark variables and overrides to `:root, html, body, .o_web_client`.
- **Zero Wildcard Globs with `.dark.scss` Coexistence**: Never use wildcard globs (`static/src/**/*`) in `web.assets_backend` if `.dark.scss` files exist in that directory tree, as this leaks dark styles into `web.assets_web.min.css`. List light files explicitly in `web.assets_backend` and `.dark.scss` files exclusively in `web.assets_web_dark`. Never use `('remove', ...)` on a file not previously added to that bundle.
- **Dual-Theme Icon Inline Guard**: Any QWeb template rendering paired light/dark `<img>` or `<svg>` icons (e.g. `.o_insilos_launcher_icon_light` and `.o_insilos_launcher_icon_dark`) MUST set inline `display: none;` on the dark variant in XML, backed by explicit `display` toggles in `web.assets_backend` and `web.assets_web_dark` so two logos never appear simultaneously.
- **Zero Bare White Surfaces**: Never hardcode bare `#ffffff`, `#fff`, `#f8fafc`, `#f4f6f8` as background on buttons, cards, dropdown menus, modals, or controls. Always utilize semantic tokens (`var(--insilos-bg-canvas)`, `var(--insilos-bg-surface)`, `var(--insilos-bg-card)`, `var(--insilos-bg-hover)`, `var(--insilos-bg-selected)`). Always reset `.o_notebook { .nav, .nav-tabs, .o_notebook_headers { background-color: transparent !important; } }` to override core `notebook.scss`.
- **Odoo 20 Form Sheet Full-Width Selector Hierarchy**: In Odoo 20, `.o_form_view` is the parent of `.o_content` (`.o_form_view > .o_form_view_container > .o_content > .o_form_sheet_bg > .o_form_sheet`). Never write inverted `.o_content > .o_form_view` selectors when overriding form sheet `max-width`.
- **Dual-Scheme Verification Gate**: Verify all UI changes with automated headless Playwright checks (`node tools/audit_crm_dual_theme.js`) across both `color_scheme=light` and `color_scheme=dark` with real session state against `insilos20_dev` (port `28069`, PG port `5434`).

## 5. Sovereign Multi-Tenant Navigation & Header Architecture
- **ORM-Level Idempotency Guard**: All creations of `website.menu` via ORM (`WebsiteMenu.create`) or module loading MUST match on canonical resolution `(website_id, parent_id, page_id/url)`. If an entry exists under the same parent tree, update in-place; NEVER duplicate child items.
- **Explicit `noupdate="1"` on Navigation Data Records**: All default or starter website menu definitions declared in XML views (`website_menu.xml`) MUST be wrapped in `<odoo noupdate="1">` so subsequent module upgrades (`-u <module>`) do not overwrite or duplicate existing menu trees.
- **Zero Raw SQL Unmanaged Menu Inserts**: Synchronization scripts, migrations, or database loaders MUST NEVER execute naive `INSERT INTO website_menu` without prior canonical deduplication and cleanup. Any sync script must resolve canonical URLs and prune redundant duplicates.
- **Fail-Closed Verification Gates**: Every tenant deployment, upgrade, or pipeline check MUST run `tools/audit_header_menu_collision.py --check` and verify rendered HTML nav uniqueness in Playwright/E2E test suites with zero duplicate route assertions.

