# MASTER ZERO SIGNATURE REMEDIATION PLAN (v4.0)
**Insilos Enterprise Hard Fork Architecture Council**
**Standard: IBM Carbon 11 + SAP Fiori Horizon + Telegram Capsule Pill**
**Database Integrity: 100% Strict Schema Invariance (0 DDL / 0 Migration)**

---

## 1. Executive Summary & Design Axioms

### 1.1 Tri-Pillar Design System
1. **IBM Carbon 11 Precision Geometry**:
   - 34px compact high-density data tables, 11px uppercase tracked headers, `tabular-nums` monetary alignment.
   - 0px floating elevation blur, crisp 1px borders (`#E2E8F0` light / `#334155` dark).
   - Checkbox width 44px with zero clipping on select-all checkbox.
2. **SAP Fiori Horizon Smart Navigation**:
   - 48px ShellBar and Action Toolbar alignment between Statusbar (left) and Chatter (right).
   - Single-line search container with zero nested inner borders.
   - Connected timeline status pipeline with subtle node separators replacing heavy Odoo chevron cutouts.
3. **Telegram Capsule Interaction Pattern**:
   - Statusbar buttons & Action controls: `border-radius: 20px`, `height: 32px`, Telegram gradient (`#2AABEE` → `#229ED9`) for primary, soft reply pill (`rgba(36, 129, 204, 0.08)`) for secondary.
   - Top-right cluster (Pager & Knowledge button): unified capsule pill container (`border-radius: 20px`, `height: 32px`).
   - Chatter Message Layout: 2-user staggered layout (Messenger/Telegram style) with rounded transparent bubbles (`border-radius: 18px`, `border: 1.5px solid`, asymmetrical tail radius 4px for incoming vs outgoing).

---

## 2. 74-Screen Classification Matrix

### 2.1 Tier A — Critical Zero Signature Remediation (47 Screens)
- **19 List Views (Search Bar Double-Border + Table Single-Border + Checkbox Overflow)**:
  - MM Purchase Orders, Quotations, Invoices, Delivery Orders, Manufacturing Orders, BOMs, Inventory Adjustments, Journal Entries, Customers/Vendors, Employees, Products/Materials, Maintenance Requests, Project Tasks, Recruitment Applications, Time Off, Payroll, Expenses, Fleet Vehicles, Quality Checks.
- **28 Form Views (Statusbar Pills + Connected Flow + Inline Title + Telegram Chatter + Phosphor Icons)**:
  - Form Purchase Order, Form RFQ, Form Sales Order, Form Customer Invoice, Form Vendor Bill, Form Stock Picking, Form Manufacturing Order, Form Employee Profile, Form Partner, Form Journal Entry, Form Product Template, Form Project Task, Form Fleet Vehicle, Form Maintenance Equipment, etc.

### 2.2 Tier B — Zero Signature Verified / Enhancement (27 Screens)
- 12 Kanban Boards, 6 Pivot / Graph Analytics Views, 4 Calendar / Activity Schedules, 5 Settings & Configuration Consoles.

---

## 3. Surgical Root Causes & Exact Remedies

### R1. Search Bar Double Border ("bị 2 border")
- **Root Cause**: `.o_searchview` container has `border: 1px solid var(--insilos-border-subtle)` / cyan outline in dark mode, while inner `.o_searchview_input` / `input` also receives a default browser or framework border/outline (`border: 1.5px solid #2481cc` or `:focus-visible`).
- **Remedy**:
  ```scss
  .o_searchview {
    border: 1px solid var(--insilos-border-subtle, #e2e8f0) !important;
    border-radius: 20px !important; // Telegram pill search bar
    input.o_searchview_input,
    .o_searchview_input_container input {
      border: none !important;
      outline: none !important;
      box-shadow: none !important;
      background: transparent !important;
    }
  }
  ```

### R2. List View Header Double Border & Checkbox Clipping
- **Root Cause**: Stacking of `.o_control_panel` bottom border directly above `.o_list_renderer` top border + `border-bottom: 2px solid` on `th` colliding with `border-top` on rows.
- **Checkbox Clipping**: `th.o_list_record_selector` had `width: 38px` and `padding-left: 14px`, clipping the right border of the checkbox input so it rendered as `[`.
- **Remedy**:
  - Set `th.o_list_record_selector { width: 44px !important; min-width: 44px !important; padding-left: 14px !important; padding-right: 6px !important; overflow: visible !important; }`.
  - Collapse table borders cleanly to a single border: `border-collapse: collapse !important;` or `border-spacing: 0;` with strictly single-edge bottom borders.

### R3. Statusbar Button Layout & Connected Timeline Flow
- **Root Cause**: Legacy Odoo statusbar uses heavy angled arrow cutouts (`.o_arrow_button`) and boxy buttons.
- **Remedy**:
  - Buttons: Capsule pills `border-radius: 20px !important; height: 32px !important;`.
  - Status pipeline: Connected timeline flow (`.o_statusbar_status`) with pill badges connected by a sleek timeline path line or subtle `›` dividers, highlighting active state with Telegram Blue / Cyan gradient.

### R4. Form Title & Badge Row Alignment
- **Root Cause**: `.oe_title` flex wrap allowed "MM Purchase Order" badge to sit on a separate line or overlap the document title.
- **Remedy**:
  - Flex-row with `align-items: center; gap: 8px;` keeping the badge and document type cleanly aligned without collision.

### R5. Chatter 2-User Staggered Telegram / Messenger Layout
- **Root Cause**: Monolithic centered message stream with boxy card styling.
- **Remedy**:
  - Staggered layout: Left for system/bot/incoming, right for user/outgoing.
  - Transparent rounded bubbles: `background: transparent !important; border: 1.5px solid var(--insilos-border-subtle) !important; border-radius: 18px !important;`.

### R6. Knowledge & Documents Phosphor Duotone Icon Integration
- **Root Cause**: Rendered as monochrome `currentColor` generic font icons or low-contrast icons.
- **Remedy**:
  - Style button into Telegram capsule pill.
  - SVG uses canonical Phosphor Duotone colors (`#0B2E64` / `#00F0FF`).
