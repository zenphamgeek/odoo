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
- **Zero Bare White Surfaces**: Never hardcode bare `#ffffff`, `#fff`, `#f8fafc`, `#f4f6f8` as background on buttons, cards, dropdown menus, modals, or controls. Always utilize semantic tokens (`var(--insilos-bg-canvas)`, `var(--insilos-bg-surface)`, `var(--insilos-bg-card)`, `var(--insilos-bg-hover)`, `var(--insilos-bg-selected)`).
- **Dual-Scheme Verification Gate**: Verify all UI changes with automated headless Playwright checks across both `color_scheme=light` and `color_scheme=dark` with real session state.

## 5. Sovereign Multi-Tenant Navigation & Header Architecture
- **ORM-Level Idempotency Guard**: All creations of `website.menu` via ORM (`WebsiteMenu.create`) or module loading MUST match on canonical resolution `(website_id, parent_id, page_id/url)`. If an entry exists under the same parent tree, update in-place; NEVER duplicate child items.
- **Explicit `noupdate="1"` on Navigation Data Records**: All default or starter website menu definitions declared in XML views (`website_menu.xml`) MUST be wrapped in `<odoo noupdate="1">` so subsequent module upgrades (`-u <module>`) do not overwrite or duplicate existing menu trees.
- **Zero Raw SQL Unmanaged Menu Inserts**: Synchronization scripts, migrations, or database loaders MUST NEVER execute naive `INSERT INTO website_menu` without prior canonical deduplication and cleanup. Any sync script must resolve canonical URLs and prune redundant duplicates.
- **Fail-Closed Verification Gates**: Every tenant deployment, upgrade, or pipeline check MUST run `tools/audit_header_menu_collision.py --check` and verify rendered HTML nav uniqueness in Playwright/E2E test suites with zero duplicate route assertions.

