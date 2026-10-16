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

## 4. Canonical Google Drive `Shared with me` (`info@inno.ai.vn` $\leftarrow$ `tham.mai@inno.ai.vn`) Synchronization & Role-Based Folder Hierarchy
- All Google Drive document ingestion and synchronization into `documents.document` MUST operate exclusively via the **`Shared with me` (`sharedWithMe = true`)** workspace of **`info@inno.ai.vn`** (shared in full by **`tham.mai@inno.ai.vn`**, covering both the **`DGM`** corporate tree and the **`INNO` / `INNORIA` (`INNO - HỢP ĐỒNG`, `DỰ ÁN`, `KH`, `MTI - TIMESHEET`)** commercial/project tree).
- Synchronization MUST recursively traverse and preserve 100% of the original multi-level folder hierarchy (`parent_id` $\rightarrow$ `folder_id` / `user_folder_id`) without flattening, enabling accurate role-based access control (`access_internal`, group permissions) per department, project, and customer folder.

