# Insilos Platform Iconography & SVG Architecture Roadmap
**Unified Phosphor Duotone Standard & Insilos Signature Media Assets**

*Author: Worker R2 (Council Role: Iconography & SVG Designer)*  
*Platform: Insilos Enterprise Platform (Genesis Fork)*  
*Status: Approved Standard & Reference Architecture*  
*Target Branch: `insilos-genesis-fork`*  

---

## 1. Executive Summary & Design Vision

The Insilos Platform requires an uncompromising, sovereign, and cohesive visual language. Prior framework versions suffered from an accumulation of disparate icon sets, including legacy FontAwesome 4/5 (`fa-*`), Google Material Symbols (`oi-*`), and disparate bespoke SVGs rendered in decommissioned genesis palettes (`#714B67`, `#017e84`, `#875A7B`, `#6B4862`).

This Roadmap establishes the **Phosphor Duotone Architecture** as the single source of truth for all graphical and iconographic primitives throughout the Insilos ecosystem (Base framework, Community Addons, Enterprise Apps, and the Insilos Web Showcase).

### Core Aesthetic Pillars
1. **Geometric Precision**: Standardized 16px and 256px coordinate spaces with consistent stroke weight (`stroke-width="16"` on 256px canvas, proportional `1.5px` - `2px` on web fonts).
2. **Duotone Depth**: Dual-layer vector rendering combining a secondary 20% opacity ambient tone (`fill="currentColor" opacity="0.2"`) with a primary high-contrast outline.
3. **Insilos Signature Palette**:
   - **Electric Amber (Brand Accent)**: `#FF8000`
   - **Industrial Obsidian (Dark Base)**: `#070B14`
   - **Deep Tech Slate (Structure)**: `#1E293B`
   - **Mid Slate (Borders & Muted Elements)**: `#334155` / `#64748B`
   - **High-Contrast Surface (Light Mode / Paper)**: `#FFFFFF` / `#F8FAFC`
4. **Zero Legacy Color Invariance**: Hard gate enforcement guaranteeing 0 hits for `#714B67`, `#017e84`, `#875a7b`, or `#6b4862` across all platform vector assets.

---

## 2. Iconography Architecture: Dual Delivery System

The Insilos Platform employs a dual-delivery model balancing high-performance webclient typography with crisp scalable vector sprites:

```
Insilos Iconography Subsystem
 ├── Webclient Font Tier (CSS Classes: .ph, .ph-duotone, .ph-*)
 │    ├── addons/web/static/lib/phosphor/phosphor.woff2 (Regular)
 │    ├── addons/web/static/lib/phosphor/phosphor-bold.woff2 (Bold)
 │    ├── addons/web/static/lib/phosphor/phosphor-duotone.woff2 (Duotone)
 │    ├── addons/web/static/lib/phosphor/phosphor.css (Glyph mapping & web fonts)
 │    └── addons/web/static/lib/phosphor/phosphor_shim.css (Backward shim)
 │    └── Declared natively via 'web.phosphor_icons' asset bundle in addons/web/__manifest__.py
 │
 ├── SVG Vector Sprite Tier (Symbol Groups: <use href="...#ph-*"/>)
 │    └── enterprise/insilos_website/static/src/icons/phosphor-duotone.svg (1,515 symbols)
 │
 └── Standalone Signature SVGs (Empty States & Notifications)
      ├── addons/web/static/img/smiling_face.svg (Happy empty state)
      ├── addons/web/static/img/neutral_face.svg (Neutral empty state)
      ├── addons/web/static/img/empty_folder.svg (No documents state)
      ├── addons/mail/static/src/img/insilos_empty_inbox.svg (Empty notification tray)
      └── enterprise/web_enterprise/static/img/background-light.svg (App drawer mesh)
```

---

## 3. Tier 1: Phosphor Font & CSS Class Standards

### 3.1 Class Naming Hierarchy
- Base Font Class: `.ph` (Regular variant)
- Duotone Font Class: `.ph-duotone` (Duotone ligature / unicode font)
- Specific Icon Glyph: `.ph-<icon-name>` (e.g. `.ph-squares-four`, `.ph-envelope-simple`)

### 3.2 Standard Sizing Scale
Consistent sizing tokens integrated directly into SCSS:

| Class | Font Size | Line Height | Typical Usage Context |
| :--- | :--- | :--- | :--- |
| `.ph-xs` | `10px` | `1` | Micro-indicators, badge pills, inline tags |
| `.ph-sm` | `12px` | `1` | Dropdown items, auxiliary metadata, breadcrumbs |
| `.ph-md` | `14px` | `1` | Standard table actions, form inputs, button labels |
| `.ph-lg` | `16px` | `1` | Navbar utilities, top-level actions, tab icons |
| `.ph-xl` | `18px` | `1` | Card headers, modal titles, drawer navigation |
| `.ph-2x` | `24px` | `1` | Feature callouts, stat counters, empty state anchors |

### 3.3 Utility Modifiers
- `.ph-fw`: Fixed-width ratio alignment ensuring tabular consistency.
- `.ph-spin`: Smooth 2s continuous linear rotation for loading states.
- `.ph-pulse`: 8-step stepped animation for discrete progress indicators.

### 3.4 Asset Bundle Integration
```python
# addons/web/__manifest__.py
'web.phosphor_icons': [
    '/web/static/lib/phosphor/phosphor.woff2',
    '/web/static/lib/phosphor/phosphor-bold.woff2',
    '/web/static/lib/phosphor/phosphor-duotone.woff2',
    '/web/static/lib/phosphor/phosphor.css',
    '/web/static/lib/phosphor/phosphor_shim.css',
],
'web.icons_fonts': [
    ...
    ('include', 'web.phosphor_icons'),
    'web/static/src/webclient/icons.scss',
],
```
In `icons.scss`:
```scss
// addons/web/static/src/webclient/icons.scss
.ph {
    font-family: 'Phosphor' !important;
    speak: never;
    font-style: normal;
    font-weight: normal;
    font-variant: normal;
    text-transform: none;
    line-height: 1;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    display: inline-block;
}

.ph-duotone {
    font-family: 'Phosphor-Duotone', 'Phosphor' !important;
    speak: never;
    font-style: normal;
    font-weight: normal;
    display: inline-block;
}
```

---

## 4. Tier 2: SVG Sprite Symbol Architecture

For high-resolution marketing routes, 3D dashboards, and rich snippets, icons are served from the precompiled vector symbol catalog at `enterprise/insilos_website/static/src/icons/phosphor-duotone.svg`.

### 4.1 Symbol Internal Anatomy
Each symbol adheres to a 256x256 viewBox and separates ambient fill from outline stroke:
```xml
<symbol id="ph-chart-line-up" viewBox="0 0 256 256">
    <!-- Ambient 20% Tint Layer -->
    <path d="M224,208H32V48H224Z" opacity="0.2" fill="currentColor"/>
    <!-- Structural Line Drawing -->
    <polyline points="224 208 32 208 32 48" fill="none" stroke="currentColor" 
              stroke-linecap="round" stroke-linejoin="round" stroke-width="16"/>
    <polyline points="224 96 144 152 96 112 32 168" fill="none" stroke="currentColor" 
              stroke-linecap="round" stroke-linejoin="round" stroke-width="16"/>
    <polyline points="224 144 224 96 176 96" fill="none" stroke="currentColor" 
              stroke-linecap="round" stroke-linejoin="round" stroke-width="16"/>
</symbol>
```

### 4.2 QWeb Template Invocation Pattern
```xml
<!-- Inline usage in QWeb Templates -->
<svg class="ph-duotone ph-chart-line-up ph-lg text-primary" aria-hidden="true">
    <use href="/insilos_website/static/src/icons/phosphor-duotone.svg#ph-chart-line-up"/>
</svg>
```

---

## 5. Tier 3: Signature Empty-State & Notification SVGs

Empty states communicate clarity, industrial discipline, and responsiveness. All target assets have been refactored to eliminate legacy palettes:

### 5.1 Asset Catalog

#### 1. Happy State (`addons/web/static/img/smiling_face.svg`)
- **Dimensions**: `120x140`, viewBox `0 0 120 140`
- **Palette**: Circle gradient in `#FF8000` -> `#EA580C`, drop shadow `#070B14`, document surface `#FFFFFF`, borders `#1E293B`, feature expression `#070B14`, sparkle accents `#FF8000`.
- **Purpose**: Positive empty state (Kanban empty column, zero pending tasks).

#### 2. Neutral State (`addons/web/static/img/neutral_face.svg`)
- **Dimensions**: `120x140`, viewBox `0 0 120 140`
- **Palette**: Circle gradient in `#334155` -> `#1E293B`, document surface `#FFFFFF`, borders `#1E293B`, feature expression `#1E293B`, top-left star accents `#FF8000`.
- **Purpose**: Informational empty state (Search returned no results, filtered view empty).

#### 3. Empty Folder (`addons/web/static/img/empty_folder.svg`)
- **Dimensions**: `120x80`, viewBox `0 0 120 80`
- **Palette**: Rear folder tab `#1E293B`, front folder card `#FFFFFF`, stroke `#334155`, mouth accent `#FF8000`.
- **Purpose**: Document repository empty state, attachment dropzones.

#### 4. Empty Notification Inbox (`addons/mail/static/src/img/insilos_empty_inbox.svg`)
- **Dimensions**: `100x100`, viewBox `0 0 100 100`
- **Palette**: Floating checkmark badge `#FF8000` (18% duotone fill + solid stroke), ambient glow `#FF8000` gradient, front tray cutout `#070B14` (stroke-width 3), tray interior `#1E293B` gradient.
- **Integration**: Rendered natively within `addons/mail/static/src/core/public_web/messaging_menu/messaging_menu_empty.xml` via:
  ```xml
  <img src="/mail/static/src/img/insilos_empty_inbox.svg" class="mb-3" style="width: 100px; height: 100px;" alt="Empty Inbox"/>
  ```

#### 5. Enterprise App Drawer Mesh (`enterprise/web_enterprise/static/img/background-light.svg`)
- **Dimensions**: `1920x1080`
- **Palette**: Clean slate/neutral gradients (`#F8FAFC`, `#F1F5F9`, `#E2E8F0`, `#CBD5E1`) completely replacing legacy mauve/purple pastel stops (`#EAE7F9`, `#E5E2F6`, `#ECE5F8`, `#9996A9`, `#7A768F`).

---

## 6. Comprehensive Legacy Icon Mapping Table

The following master table provides the definitive mapping from legacy FontAwesome (`fa-*`) and Material Symbols (`oi-*`) to their native Phosphor equivalents.

### 6.1 Core Navigation & User Actions
| Legacy Class / Token | Material Symbol ID | Phosphor Icon Name | Unicode Glyph | Recommended Context |
| :--- | :--- | :--- | :--- | :--- |
| `fa-star`, `oi-star` | `star` | `ph-star` | `\e46a` | Favorites, rating, priority |
| `fa-times`, `fa-close` | `close` | `ph-x` | `\e4f6` | Dismiss, clear, close modal |
| `fa-ellipsis-v` | `more_vert` | `ph-dots-three-vertical` | `\e208` | Action dropdown menu |
| `fa-ellipsis-h` | `more_horiz` | `ph-dots-three` | `\e1fe` | Overflow menu |
| `fa-trash`, `fa-trash-o` | `delete` | `ph-trash` | `\e4a6` | Delete record |
| `fa-download` | `download` | `ph-download-simple` | `\e20c` | Export, download file |
| `fa-upload` | `upload` | `ph-upload-simple` | `\e4c0` | Import, upload file |
| `fa-cloud-upload` | `cloud_upload` | `ph-cloud-arrow-up` | `\e1ae` | Cloud backup / sync |
| `fa-search` | `search` | `ph-magnifying-glass` | `\e30c` | Global search, filter |
| `fa-plus` | `add` | `ph-plus` | `\e3d4` | Create, add line |
| `fa-minus` | `remove` | `ph-minus` | `\e32a` | Remove line, collapse |
| `fa-pencil`, `fa-edit` | `edit` | `ph-pencil-simple` | `\e3b4` | Inline edit, rename |
| `fa-check` | `check` | `ph-check` | `\e182` | Confirm, validate |
| `fa-check-circle` | `check_circle` | `ph-check-circle` | `\e184` | Completed, verified |
| `fa-ban` | `block` | `ph-prohibit` | `\e3de` | Forbidden, blocked |
| `fa-refresh`, `fa-sync`| `refresh` | `ph-arrows-clockwise` | `\e094` | Reload data |
| `fa-filter` | `filter_alt` | `ph-funnel` | `\e266` | Search filters |
| `fa-sort` | `sort` | `ph-arrows-down-up` | `\e444` | Column sorting |
| `fa-arrows-v` | `swap_vert` | `ph-arrows-down-up` | `\e098` | Reorder vertical |

### 6.2 Directions, Chevrons & Arrows
| Legacy Class / Token | Material Symbol ID | Phosphor Icon Name | Unicode Glyph | Recommended Context |
| :--- | :--- | :--- | :--- | :--- |
| `fa-chevron-right` | `chevron_right` | `ph-caret-right` | `\e13a` | Accordion expand, pagination |
| `fa-chevron-left` | `chevron_left` | `ph-caret-left` | `\e138` | Accordion collapse, back |
| `fa-chevron-down` | `arrow_drop_down` | `ph-caret-down` | `\e136` | Dropdown trigger |
| `fa-arrow-right` | `arrow_forward` | `ph-arrow-right` | `\e06c` | Next step, submit flow |
| `fa-arrow-left` | `arrow_back` | `ph-arrow-left` | `\e058` | Previous step, return |
| `fa-arrow-up` | `arrow_upward` | `ph-arrow-up` | `\e08e` | Scroll top, sort ascending |
| `fa-arrow-down` | `arrow_downward` | `ph-arrow-down` | `\e03e` | Scroll bottom, sort descending |
| `fa-angle-double-right`| `keyboard_double_arrow_right` | `ph-caret-double-right`| `\e12a` | Fast-forward, jump to end |

### 6.3 Business Objects & System Architecture
| Legacy Class / Token | Material Symbol ID | Phosphor Icon Name | Unicode Glyph | Recommended Context |
| :--- | :--- | :--- | :--- | :--- |
| `fa-database` | `database` | `ph-database` | `\e1de` | Database manager, backups |
| `fa-envelope`, `fa-envelope-o` | `mail` | `ph-envelope` | `\e218` | Email, message notification |
| `fa-phone` | `phone` | `ph-phone` | `\e3b8` | Telephone contact |
| `fa-mobile` | `smartphone` | `ph-device-mobile` | `\e1e0` | Mobile view, SMS |
| `fa-laptop` | `laptop` | `ph-laptop` | `\e586` | Desktop view |
| `fa-calendar` | `calendar_today` | `ph-calendar` | `\e108` | Scheduling, deadlines |
| `fa-clock-o` | `schedule` | `ph-clock` | `\e19a` | Timestamps, durations |
| `fa-building`, `fa-building-o` | `business` | `ph-buildings` | `\e102` | Company selector, branches |
| `fa-user`, `fa-user-circle` | `account_circle` | `ph-user-circle` | `\e4c4` | Profile, user menu |
| `fa-user-plus` | `person_add` | `ph-user-plus` | `\e4d0` | Invite user, assign partner |
| `fa-users` | `group` | `ph-users` | `\e4ce` | Teams, customer groups |
| `fa-eye` | `visibility` | `ph-eye` | `\e220` | Reveal password, inspect |
| `fa-eye-slash` | `visibility_off` | `ph-eye-slash` | `\e224` | Hide password, mask |
| `fa-key` | `key` | `ph-key` | `\e2d6` | API keys, passkeys, tokens |
| `fa-cog`, `fa-cogs` | `settings` | `ph-gear` | `\e272` | Preferences, configuration |
| `fa-th`, `fa-bars` | `apps` | `ph-squares-four` | `\e464` | App Drawer, home menu |
| `fa-sign-out` | `logout` | `ph-sign-out` | `\e42a` | Session logout |

### 6.4 Analytics, Views & Documents
| Legacy Class / Token | Material Symbol ID | Phosphor Icon Name | Unicode Glyph | Recommended Context |
| :--- | :--- | :--- | :--- | :--- |
| `fa-th-large` | `oi_view-kanban` | `ph-kanban` | `\eb54` | Kanban card view |
| `fa-list` | `view_list` | `ph-list-bullets` | `\e2f4` | Tree / list view |
| `fa-table` | `oi_view-grid` | `ph-table` | `\e296` | Spreadsheet / grid view |
| `fa-bar-chart` | `bar_chart` | `ph-chart-bar` | `\e150` | Bar visualization |
| `fa-pie-chart` | `pie_chart` | `ph-chart-pie` | `\e158` | Distribution chart |
| `fa-line-chart` | `show_chart` | `ph-chart-line` | `\e154` | Telemetry & trend line |
| `fa-sitemap` | `account_tree` | `ph-tree-structure` | `\e67c` | Hierarchy, BOM levels |
| `fa-file-text-o` | `article` | `ph-file-text` | `\e0a8` | Invoice, SO, document record |
| `fa-copy` | `content_copy` | `ph-copy` | `\e1ca` | Duplicate record |
| `fa-paperclip` | `attach_file` | `ph-paperclip` | `\e39a` | File attachments |
| `fa-print` | `print` | `ph-printer` | `\e3dc` | Document printing |
| `fa-shopping-cart` | `shopping_cart` | `ph-shopping-cart` | `\e41e` | Cart, POS ordering |

---

## 7. Migration & Quality Enforcement Rules

1. **Strict Legacy Color Prohibition**:
   - Never introduce `#714B67`, `#017E84`, `#875A7B`, or `#6B4862` into any `.svg`, `.scss`, or `.xml` file.
   - Run the automated verification harness prior to handoff:
     ```bash
     python3 scripts/asset_inventory_scanner.py --path . --output .agents/teamwork/ASSET_INVENTORY.json --max-legacy-palette-hits 0
     ```
2. **Zero FontAwesome Regression**:
   - In modern QWeb views, replace all `<i class="fa fa-*">` with `<i class="ph ph-*">` or `<i class="ph-duotone ph-*">`.
   - Never import external CDN FontAwesome stylesheets.
3. **OWL Component Standard**:
   - Inside OWL components, dynamic icon references must pass the phosphor class string (e.g. `icon: "ph ph-bell"`).
4. **Accessibility Conformance**:
   - Decorative icons must include `aria-hidden="true"`.
   - Interactive icon buttons must declare a descriptive `aria-label` and `title`.

---

## 8. Verification & Continuous Audit

The Phosphor Duotone architecture is enforced continuously via two primary harnesses:
1. **Asset Inventory Scanner** (`scripts/asset_inventory_scanner.py`):
   - Validates all 22,700 media and vector assets.
   - Enforces `--max-legacy-palette-hits 0`.
2. **Counter Code Security Scanner** (`scripts/counter_code_scanner.py`):
   - Scans core modules for genesis fingerprints.
   - Audits Phosphor icon adoption (`phosphor_icon_hits >= 3,100`).

Both tests MUST return exit code 0 on all deployment branches.
