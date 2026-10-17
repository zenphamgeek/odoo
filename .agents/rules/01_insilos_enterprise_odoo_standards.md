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
