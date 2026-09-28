# TEST_INFRA.md: Insilos Enterprise Platform E2E Test Infrastructure & Specification

**Standard**: Enterprise Industrial AI Testing Architecture & Quality Assurance Protocol  
**Target Platform**: Insilos 20 Enterprise Platform (`enterprise/insilos_website`)  
**Integrity Mode**: Continuous PDCA Benchmark & Zero-Defect Enforcement  
**Author**: E2E Test Writer (Specialist & QA)  
**Date**: September 27, 2026  

---

## 1. Test Architecture & Testing Philosophy

### 1.1 Opaque-Box & Requirement-Driven Foundation
The Insilos Enterprise testing architecture is built upon **opaque-box, requirement-driven verification**. Tests treat the application as an integrated industrial software suite, interacting exclusively through observable interfaces:
- **HTTP / Network Layer**: Live HTTP status codes, response headers, content negotiation, caching directives, and redirect flows (`urllib`, `requests`, Playwright).
- **DOM & Rendered QWeb Layer**: Structural element presence, dropzone activation (`oe_structure`, `s_*`), metadata attributes (`data-snippet`, `data-name`), and semantic HTML5 tags.
- **Visual Design System & CSS Token Layer**: CSS custom properties (`--ins-orange: #FF8000`), typography wrapping rules (`text-wrap: balance/pretty`), layout rhythm constraints (`.ins-card-row-balanced`), and baseline alignment geometry.
- **Static Asset & Template Hygiene**: Pure Phosphor SVG iconography, zero FontAwesome legacy tags, zero inline `style="..."` attributes, and clean Insilos 20 QWeb directives (`t-out`, zero `t-esc`, zero server `t-key`).
- **Interactive State & Event Contracts**: Mega-Menu custom events (`insilos-menu-preview-change`), Video Transition Stage buffer switching, RAF throttling listeners, and IntersectionObserver memory management.

### 1.2 Progressive Testability & Milestone Isolation
Tests are decoupled into progressive tiers corresponding to project milestones (M1 through M5). Each test can be independently executed and verified without requiring mock artifacts or unfinished dependencies from downstream milestones:
- **M1 Tests**: Target typography, brand tokens, and template hygiene.
- **M2 Tests**: Target mega-menu navigation, preview hover states, and responsive drawers.
- **M3 Tests**: Target 3D cockpit telemetry, video transitions, and memory safeguards.
- **M4 Tests**: Target continuous PDCA route presentations, industrial copywriting, and lead generation funnels.
- **M5 Tests**: Target holistic quality gate verification, module upgrade execution, and adversarial stress hardening.

### 1.3 Expected Output Derivation & Authoritative Oracles
Every test case defines an explicit, authoritative source of truth:
1. **Design System Token Oracle**: `enterprise/insilos_website/static/src/scss/insilos.scss` and `insilos-web-design-premium` standard.
2. **Structural & QWeb Directive Oracle**: Insilos 20 Website Builder core specifications and `quality_gate.py`.
3. **Route & Content Oracle**: `controllers/main.py`, `controllers/industry_registry.py`, and `ORIGINAL_REQUEST.md`.
4. **Behavioral Interaction Oracle**: `PROJECT.md § Interface Contracts` and `static/src/js/c3ai_interactive.js`.

---

## 2. 4-Tier Test Taxonomy Overview

```
┌────────────────────────────────────────────────────────────────────────┐
│ TIER 4: Real-World Application & Executive Journey Scenarios (4 suites)│
├────────────────────────────────────────────────────────────────────────┤
│ TIER 3: Cross-Feature Interactions & Event Contracts (10 suites)       │
├────────────────────────────────────────────────────────────────────────┤
│ TIER 2: Boundary, Extreme Viewport & Corner Cases (15 suites)          │
├────────────────────────────────────────────────────────────────────────┤
│ TIER 1: Feature Coverage (30 Features × >= 5 Tests = 150+ Test Cases)  │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Tier 1: Feature Coverage (150+ Discrete Tests)

Each of the 30 features from `PROJECT.md` is mapped to at least 5 isolated, verifiable test cases.

### Feature 1: SCSS Brand Orange Token System (M1)
- **TEST-F01-01 (Primary Orange Token)**: Verify `--ins-orange: #FF8000` and `--ins-primary: #FF8000` exist in `:root` of `insilos.scss`.
- **TEST-F01-02 (Orange Gradient Token)**: Verify `--ins-orange-gradient` is defined with valid multi-stop linear gradient (`#FFA033`, `#FF8000`, `#E66A00`).
- **TEST-F01-03 (Primary Button Class)**: Verify `.btn-primary` in `insilos.scss` references `var(--ins-orange-gradient)` or `var(--ins-orange)`.
- **TEST-F01-04 (Glow Shadow & Hover Lift)**: Verify `.btn-primary:hover` applies luminous lift `translateY(-2px)` and box-shadow glow with brand orange RGBA.
- **TEST-F01-05 (Zero Rogue Button Classes)**: Verify 0 occurrences of `btn-cyan`, `btn-outline-cyan`, `btn-dark-glow`, `btn-custom` across all QWeb templates.

### Feature 2: Smart Title Wrapping (`text-wrap: balance`) (M1)
- **TEST-F02-01 (Heading Rule Declaration)**: Verify `h1, h2, h3, h4, h5, h6` in `insilos.scss` declare `text-wrap: balance;`.
- **TEST-F02-02 (Display Classes Declaration)**: Verify `.display-1` through `.display-6` declare `text-wrap: balance;`.
- **TEST-F02-03 (Bento & Card Titles Declaration)**: Verify `.ins-card-title`, `.ins-bento-title`, `.ins-title-balance` declare `text-wrap: balance;`.
- **TEST-F02-04 (Security Banner Title Rule)**: Verify the security banner in `home.xml` includes `ins-title-balance` or semantic break preventing title stump.
- **TEST-F02-05 (Rendered DOM Verification)**: Verify computed style `text-wrap` on `h1` at `/` evaluates to `balance` on modern rendering engines.

### Feature 3: Body Copy Pretty Wrapping (`text-wrap: pretty`) (M1)
- **TEST-F03-01 (Paragraph Rule Declaration)**: Verify `p` in `insilos.scss` declares `text-wrap: pretty;`.
- **TEST-F03-02 (Lead Copy Rule Declaration)**: Verify `.lead` declares `text-wrap: pretty;`.
- **TEST-F03-03 (Card Text Rule Declaration)**: Verify `.card-text` and `.ins-card-desc` declare `text-wrap: pretty;`.
- **TEST-F03-04 (Proof Description Declaration)**: Verify `.ins-proof-desc` declares `text-wrap: pretty;`.
- **TEST-F03-05 (Orphan Elimination on Paragraphs)**: Verify multi-line paragraphs in `platform_solutions.xml` do not render a single stranded word on the terminal line.

### Feature 4: Semantic Break Tags (M1)
- **TEST-F04-01 (Responsive Break Tag Class)**: Verify high-impact headings utilize `<br class="d-none d-md-inline"/>` or `<br class="d-none d-sm-inline"/>`.
- **TEST-F04-02 (Cognitive Boundary Placement)**: Verify break tags occur after conjunctions (`&amp;`, `và`), dashes, or colons.
- **TEST-F04-03 (Homepage Hero Headline Break)**: Verify hero H1 on `/` contains semantic break balancing headline halves.
- **TEST-F04-04 (Platform Solutions Headline Break)**: Verify solutions overview H1 contains semantic break.
- **TEST-F04-05 (Industries Overview Headline Break)**: Verify 101 Industries H1 contains semantic break.

### Feature 5: HBox Symmetrical Rhythm Locks (M1)
- **TEST-F05-01 (HBox Balanced Class Declaration)**: Verify `.ins-card-row-balanced` is declared in `insilos.scss`.
- **TEST-F05-02 (Title Height Locking)**: Verify `.ins-card-row-balanced .card-title` locks `min-height: 2.85rem` with `-webkit-line-clamp: 2`.
- **TEST-F05-03 (Body Text Height Locking)**: Verify `.ins-card-row-balanced .card-text` locks `min-height: 4.25rem` with `-webkit-line-clamp: 3`.
- **TEST-F05-04 (Col-Card Height Alignment Rate)**: Verify >= 95% of sibling cards in `col-lg-[2346]` containers include `h-100`.
- **TEST-F05-05 (Card Footer Baseline Button Lock)**: Verify action buttons in card footers have `mt-auto` to lock horizontal baseline alignment.

### Feature 6: Inline Style Sanitation (M1)
- **TEST-F06-01 (Zero Inline Style Attributes in Views)**: Audit `views/*.xml` for total occurrences of `style="..."` (Target: 0).
- **TEST-F06-02 (Zero Inline Style on SVG Elements)**: Verify `<svg>` elements replace inline `style="width:...; pointer-events:...;"` with utility classes.
- **TEST-F06-03 (Zero Inline Style on Containers)**: Verify `<div>` and `<section>` containers replace inline background/z-index with SCSS classes.
- **TEST-F06-04 (Zero Inline Style on Buttons)**: Verify `<a class="...btn...">` has 0 inline style color or background overrides.
- **TEST-F06-05 (SCSS Utility Class Migration)**: Verify replacement utility classes (`.ins-svg-bus`, `.ins-z-above`, `.ins-hero-poster-fallback`) exist in `insilos.scss`.

### Feature 7: FontAwesome Icon Elimination (M1)
- **TEST-F07-01 (Zero FontAwesome in views/*.xml)**: Audit all XML templates for `<i class="fa fa-..."/>` (Target: 0).
- **TEST-F07-02 (Showcase Landing Cleanliness)**: Verify `showcase_landing.xml` contains 0 FontAwesome tags.
- **TEST-F07-03 (Cinematic Snippets Cleanliness)**: Verify `snippets_cinematic.xml` contains 0 FontAwesome tags.
- **TEST-F07-04 (Phosphor SVG Duotone Migration)**: Verify all visual icons utilize Phosphor Duotone SVG or Phosphor icon classes (`ph-*`).
- **TEST-F07-05 (SVG ViewBox & Namespace Validation)**: Verify injected Phosphor SVG elements contain valid `viewBox` and `xmlns` attributes.

### Feature 8: Mega-Menu Glassmorphism Container (M2)
- **TEST-F08-01 (Backdrop Filter SCSS Rule)**: Verify `.ins-mega-menu` declares `backdrop-filter: blur(16px)` and `-webkit-backdrop-filter: blur(16px)`.
- **TEST-F08-02 (Background Translucency)**: Verify container background uses deep translucent navy `rgba(7, 11, 20, 0.92)`.
- **TEST-F08-03 (Border & Shadow Elegance)**: Verify 1px glass border `rgba(255, 255, 255, 0.08)` and box shadow.
- **TEST-F08-04 (QWeb Menu Integration)**: Verify mega-menu template inherits or overrides `website.header_standard` without breaking Insilos navbar.
- **TEST-F08-05 (Z-Index Hierarchy)**: Verify mega-menu dropdown has `z-index: 1050` ensuring it floats over 3D hero canvas.

### Feature 9: Mega-Menu Dynamic Indicator Sheen (M2)
- **TEST-F09-01 (Sheen Indicator Element)**: Verify presence of animated indicator element `.ins-nav-indicator` or sheen highlight track.
- **TEST-F09-02 (Transition Timing)**: Verify CSS transition on indicator transform is `all 0.25s cubic-bezier(0.4, 0, 0.2, 1)`.
- **TEST-F09-03 (Active Route Tracking)**: Verify indicator aligns with the active route on page load.
- **TEST-F09-04 (Mouse Hover Tracking)**: Verify mousemove / mouseenter listener shifts indicator position smoothly.
- **TEST-F09-05 (Memory Leak Absence)**: Verify unbind or cleanup on DOM teardown.

### Feature 10: Solution Preview Hover Cards (M2)
- **TEST-F10-01 (Event Binding)**: Verify solution links emit `insilos-menu-preview-change` custom event on hover.
- **TEST-F10-02 (Event Payload Schema)**: Verify payload contains `{ title, metric, description, href, badge }`.
- **TEST-F10-03 (Vertical IDP Card Preview)**: Verify hovering Vertical IDP item displays `99.8% STP` metric.
- **TEST-F10-04 (Knowledge Graph Card Preview)**: Verify hovering Knowledge Graph displays `Sub-Second Reasoning` metric.
- **TEST-F10-05 (Trade Compliance & FSM Card Previews)**: Verify Trade Compliance displays `WCO SAFE` and FSM displays `First-Time Fix 94.8%`.

### Feature 11: Industry Preview Hover Cards (M2)
- **TEST-F11-01 (Industry Menu Hover Triggers)**: Verify hovering Logistics, Pharma, Energy triggers industry preview card updates.
- **TEST-F11-02 (Logistics Metric Preview)**: Verify Logistics preview highlights `OTIF 99.4%` and Cát Lái Port case study.
- **TEST-F11-03 (Pharma Metric Preview)**: Verify Pharma preview highlights `FDA 21 CFR Part 11` & Golden Batch consistency.
- **TEST-F11-04 (Energy Metric Preview)**: Verify Energy preview highlights `IEC 61850` and EVN Genco 3 substation telemetry.
- **TEST-F11-05 (Fallback Preview Card)**: Verify preview card defaults to featured highlight when no menu item is hovered.

### Feature 12: Header Responsive Mobile Fallback (M2)
- **TEST-F12-01 (Mobile Toggler Button)**: Verify presence of `.navbar-toggler` with accessible `aria-expanded` and `aria-label`.
- **TEST-F12-02 (Offcanvas / Accordion Drawer)**: Verify mobile navigation collapses into smooth drawer on viewport width < 992px.
- **TEST-F12-03 (Brand Orange Accents on Mobile)**: Verify active items in mobile drawer maintain `#FF8000` accents.
- **TEST-F12-04 (Touch Target Sizing)**: Verify mobile menu item touch targets have minimum height >= 44px.
- **TEST-F12-05 (Drawer Close on Navigate)**: Verify clicking a navigation link closes the offcanvas drawer.

### Feature 13: Video Transition Engine 6 Modes Full Rotation (M3)
- **TEST-F13-01 (Stage Container & Dual Buffers)**: Verify `#ins_scene_transition_stage` contains `#ins-hero-video-a` and `#ins-hero-video-b`.
- **TEST-F13-02 (Blade Wipe Class)**: Verify `.ins-fx-blade-in` applies directional polygon clip-path transition.
- **TEST-F13-03 (Cyber Glitch Class)**: Verify `.ins-fx-glitch-in` applies chromatic aberration and slice keyframe.
- **TEST-F13-04 (Iris Bloom & Quantum Warp)**: Verify `.ins-fx-iris-in` (radial aperture) and `.ins-fx-warp-in` (perspective scale).
- **TEST-F13-05 (Luma Flare & Vault Shutter)**: Verify `.ins-fx-luma-in` (exposure bloom) and `.ins-fx-shutter-in` (dual door close).

### Feature 14: 60 FPS RAF Throttling (M3)
- **TEST-F14-01 (RAF Hook Presence)**: Verify mousemove listeners in `c3ai_interactive.js` utilize `requestAnimationFrame`.
- **TEST-F14-02 (Throttle Flag State)**: Verify `isThrottled` or `ticking` boolean flag prevents concurrent frame stacking.
- **TEST-F14-03 (Gyroscope Tilt Calculation)**: Verify tilt angles are clamped within $[-15^\circ, 15^\circ]$ range.
- **TEST-F14-04 (Frame Budget Maintenance)**: Verify per-frame execution time does not exceed 16.6ms.
- **TEST-F14-05 (Smooth Dampening)**: Verify easing interpolation (lerp factor $\le 0.15$) for fluid inertia.

### Feature 15: Video Memory-Leak Safeguard (M3)
- **TEST-F15-01 (IntersectionObserver Registration)**: Verify video stage registers an `IntersectionObserver`.
- **TEST-F15-02 (Off-screen Pause Trigger)**: Verify video playback pauses when `intersectionRatio == 0`.
- **TEST-F15-03 (On-screen Resume Trigger)**: Verify video playback resumes when `isIntersecting` becomes true.
- **TEST-F15-04 (Observer Disconnect Cleanup)**: Verify observer is disconnected upon component destroy/page unload.
- **TEST-F15-05 (Zero Memory Growth Over 10 Rotations)**: Verify JS heap memory remains stable across continuous scene transitions.

### Feature 16: 4-Layer 3D Cockpit Deck Refinement (M3)
- **TEST-F16-01 (Layer 1 Foundation Plate)**: Verify `.ins-deck-foundation` renders with data-grid matrix and glowing edge.
- **TEST-F16-02 (Layer 2 Telemetry Signal Bus)**: Verify `.ins-cockpit-bus-svg` renders signal pulses with pure CSS animations.
- **TEST-F16-03 (Layer 3 Neural Reasoning Core)**: Verify `.ins-deck-core` renders isometric model nodes.
- **TEST-F16-04 (Layer 4 Executive HUD Glass)**: Verify `.ins-deck-hud` renders telemetry gauges with glass reflection.
- **TEST-F16-05 (Perspective Viewport & Preserve-3d)**: Verify parent container sets `transform-style: preserve-3d` and `perspective: 1200px`.

### Feature 17: Platform Topology Interactive Diagram (M4)
- **TEST-F17-01 (5-Tier Topology Structure)**: Verify presence of 5 distinct tiers (Ingestion, Normalization, Knowledge Graph, Reasoning, Application).
- **TEST-F17-02 (Node Click Drill-Down)**: Verify clicking any topology node activates details drawer or modal.
- **TEST-F17-03 (Active Telemetry Ticker)**: Verify animated packet flow along SVG connector paths.
- **TEST-F17-04 (Connector Path Geometry)**: Verify SVG spline connectors connect node anchor coordinates accurately.
- **TEST-F17-05 (Responsive Collapse)**: Verify topology switches to vertical stacked timeline on mobile viewports.

### Feature 18: Continuous PDCA Homepage Enhancement (M4)
- **TEST-F18-01 (Route HTTP 200)**: Verify `GET /` returns HTTP 200 with non-empty HTML.
- **TEST-F18-02 (C3.ai Industrial Presentation)**: Verify homepage features Model-Driven Architecture and Sovereign Industrial AI banner.
- **TEST-F18-03 (Hero Dropzones)**: Verify top and bottom `oe_structure` dropzones are present.
- **TEST-F18-04 (4-Column Executive Numbers)**: Verify `s_numbers` snippet displays audited operational metrics.
- **TEST-F18-05 (Bottom CTA Funnel)**: Verify bottom CTA directs to `/request-demo` with brand orange button.

### Feature 19: Platform Route Enhancement (M4)
- **TEST-F19-01 (Route HTTP 200)**: Verify `GET /platform` returns HTTP 200 with valid dropzones.
- **TEST-F19-02 (Architecture Code Studio)**: Verify presence of `s_c3ai_code_studio` snippet demonstrating declarative model syntax.
- **TEST-F19-03 (Air-Gapped Sovereign Security Section)**: Verify dedicated section highlighting on-premise air-gapped deployment.
- **TEST-F19-04 (Sub-Second Benchmark Ledger)**: Verify table or card displaying < 15ms inference latency.
- **TEST-F19-05 (Platform Navigation Links)**: Verify links to `/solutions` and `/request-demo` resolve correctly.

### Feature 20: Solutions Catalog & Detail Overhauls (M4)
- **TEST-F20-01 (Directory HTTP 200)**: Verify `GET /solutions` returns HTTP 200.
- **TEST-F20-02 (Vertical IDP Route HTTP 200)**: Verify `GET /solutions/vertical-idp` renders dedicated solution template.
- **TEST-F20-03 (Knowledge Graph Route HTTP 200)**: Verify `GET /solutions/enterprise-knowledge-graph` renders dedicated solution template.
- **TEST-F20-04 (Trade Compliance & FSM Routes HTTP 200)**: Verify `/solutions/trade-compliance` and `/solutions/field-service-intelligence` return HTTP 200.
- **TEST-F20-05 (Fallback Template Resilience)**: Verify unmapped solution slug renders `insilos_solution_page` fallback without 500 error.

### Feature 21: Industries Catalog & Detail Overhauls (M4)
- **TEST-F21-01 (Directory HTTP 200)**: Verify `GET /industries` returns HTTP 200.
- **TEST-F21-02 (101 Industry Registry Ingestion)**: Verify `INDUSTRY_101_REGISTRY` contains 101 industry definitions.
- **TEST-F21-03 (Logistics Route HTTP 200)**: Verify `GET /industries/logistics` renders dedicated industry view.
- **TEST-F21-04 (Pharma & Energy Routes HTTP 200)**: Verify `GET /industries/pharma` and `GET /industries/energy` render dedicated views.
- **TEST-F21-05 (101 Industries Slugs)**: Verify arbitrary slug (e.g. `/industries/freight`, `/industries/electrical`) resolves via fallback template.

### Feature 22: Pricing Route Enhancement (M4)
- **TEST-F22-01 (Route HTTP 200)**: Verify `GET /pricing` returns HTTP 200 with valid dropzones.
- **TEST-F22-02 (3-Tier Enterprise Matrix)**: Verify Standard, Enterprise, and Sovereign Air-Gapped tier cards.
- **TEST-F22-03 (Micro-Ledger / SLA Commitments)**: Verify clear SLA guarantees (99.9% uptime, <15ms latency).
- **TEST-F22-04 (Interactive ROI Calculator Snippet)**: Verify `s_c3ai_roi_calculator` is embedded with interactive slider inputs.
- **TEST-F22-05 (Card Row Height Locking)**: Verify pricing tier cards have `.ins-card-row-balanced` and `h-100`.

### Feature 23: About & Resources Route Overhauls (M4)
- **TEST-F23-01 (About Route HTTP 200)**: Verify `GET /about` returns HTTP 200.
- **TEST-F23-02 (Resources Route HTTP 200)**: Verify `GET /resources` returns HTTP 200.
- **TEST-F23-03 (Technical Whitepapers Sub-routes)**: Verify `/resources/operational-ai` and `/resources/trade-compliance-handbook` return HTTP 200.
- **TEST-F23-04 (Case Studies EVN & Mobifone)**: Verify case study highlights are embedded with verified metrics.
- **TEST-F23-05 (Media Credits Route HTTP 200)**: Verify `GET /media-credits` returns HTTP 200.

### Feature 24: Request Demo Executive Funnel (M4)
- **TEST-F24-01 (Route HTTP 200)**: Verify `GET /request-demo` returns HTTP 200 with rendered form.
- **TEST-F24-02 (CSRF Protection)**: Verify presence of CSRF token `<input type="hidden" name="csrf_token"/>`.
- **TEST-F24-03 (Mandatory Form Fields)**: Verify name, email, company, industry, use case, consent fields exist.
- **TEST-F24-04 (Industry & Use Case Select Options)**: Verify dropdowns populate from `INDUSTRY_SELECTIONS` and `USE_CASE_SELECTIONS`.
- **TEST-F24-05 (Thank You Page Route HTTP 200)**: Verify `GET /thank-you` returns HTTP 200.

### Feature 25: B2B Marketing Hooks & Quantified Friction (M4)
- **TEST-F25-01 (Data Silo Quantification)**: Verify presence of concrete friction metrics ($45k/hr downtime, 70% manual keystroke elimination).
- **TEST-F25-02 (Active Verb Headlines)**: Verify headlines start with active verbs ("Xóa bỏ", "Khóa cứng", "Tự động hóa", "Đối soát").
- **TEST-F25-03 (3-Second Executive Hook Format)**: Verify cards follow Hook (<10 words) + Metric (<15 words) + Action structure.
- **TEST-F25-04 (No Generic AI Claims)**: Verify absence of vague buzzwords ("AI ma thuật", "Giải pháp toàn diện nhất").
- **TEST-F25-05 (Executive Audience Calibration)**: Verify content targets C-level roles (CEO, COO, CFO, CIO).

### Feature 26: Regulatory & Tech Standard Badges (M4)
- **TEST-F26-01 (WCO SAFE Badge)**: Verify World Customs Organization SAFE framework badge on logistics/trade pages.
- **TEST-F26-02 (VAS 200 Accounting Badge)**: Verify Circular 200/2014/TT-BTC compliance token on financial/IDP pages.
- **TEST-F26-03 (IEC 61850 Substation Badge)**: Verify IEC 61850 standard badge on energy pages.
- **TEST-F26-04 (FDA 21 CFR Part 11 Badge)**: Verify pharmaceutical electronic record compliance badge on pharma pages.
- **TEST-F26-05 (SOC 2 & ISO 27001 Badges)**: Verify security accreditations on `/about` and `/platform`.

### Feature 27: Fix Dead Links in JS Components (M4)
- **TEST-F27-01 (Industry Explorer Links Audit)**: Verify `industry_explorer.js` does not link to dead `/insilos/industries/fsm`.
- **TEST-F27-02 (Canonical Slug Routing)**: Verify all JS links target `/industries/<slug>` canonical routes.
- **TEST-F27-03 (Showcase 3D Link Target)**: Verify 3D landing links target `/showcase-3d`.
- **TEST-F27-04 (PDF Brochure Links Audit)**: Verify brochure links target `/industry/<slug>/brochure`.
- **TEST-F27-05 (Zero 404 in Static Links)**: Audit all static anchor `href` values for broken internal URLs.

### Feature 28: Quality Gate Suite 100% Pass Verification (M5)
- **TEST-F28-01 (Gate 1 Static Snippets Pass)**: Verify 100% of sections have valid `data-snippet` and `data-name`.
- **TEST-F28-02 (Gate 2 Live Routes Pass)**: Verify all public routes return HTTP 200 with dropzones.
- **TEST-F28-03 (Gate 3 Website Editor Pass)**: Verify custom snippets inherit `website.snippets`.
- **TEST-F28-04 (Gate 4 Snippet Diversity Pass)**: Verify distinct snippet count >= 20 (Target achieved: 26).
- **TEST-F28-05 (Gate 5-7 Pass)**: Verify Gate 5 (QWeb), Gate 6 (Button Theme), Gate 7 (Typographic/HBox) all pass.

### Feature 29: Insilos Module Upgrade Execution (M5)
- **TEST-F29-01 (Upgrade Command Syntax)**: Verify upgrade command matches `.venv/bin/python insilos-bin -c insilos.conf -d odoo20_dev -u insilos_website --stop-after-init`.
- **TEST-F29-02 (Clean Upgrade Log)**: Verify 0 critical errors or tracebacks in upgrade output.
- **TEST-F29-03 (Manifest Asset Bundle Ingestion)**: Verify `__manifest__.py` assets bundle compiles cleanly.
- **TEST-F29-04 (View Record Parsing)**: Verify all XML views parse without QWeb syntax errors.
- **TEST-F29-05 (Post-Upgrade Server Health)**: Verify server responds HTTP 200 immediately after upgrade.

### Feature 30: Adversarial Coverage Hardening (M5)
- **TEST-F30-01 (High-DPI / Retina Display Scaling)**: Verify SVG and WebP images maintain crisp rendering at 2x/3x DPR.
- **TEST-F30-02 (Viewport Breakpoint Stress 320px)**: Verify zero horizontal overflow scroll on 320px screen width.
- **TEST-F30-03 (Editor Mode Compatibility)**: Verify pages load with `?enable_editor=1` without JS exceptions.
- **TEST-F30-04 (Rapid Form Submission Rate Limit)**: Verify demo request form enforces 20s cooldown between submissions.
- **TEST-F30-05 (Malformed Query String Handling)**: Verify arbitrary query strings (`/?debug=1&foo=bar`) do not disrupt page rendering.

---

## 4. Tier 2: Boundary & Corner Cases

Tier 2 tests explore edge conditions, extreme parameters, and failure modes:

| Test ID | Boundary Area | Input Condition | Expected Behavior |
|---|---|---|---|
| **TEST-BND-01** | Extreme Heading Length | Title containing 150+ characters | Wraps gracefully without overlapping sibling elements or clipping container |
| **TEST-BND-02** | Minimal Heading Length | Short 2-word title (e.g. "Tổng Quan") | Balanced line-wrap maintains optical alignment; zero orphan stump |
| **TEST-BND-03** | Mobile Viewport (320px) | iPhone SE / small screen viewport | `text-wrap: balance` collapses cleanly; 0 horizontal page overflow |
| **TEST-BND-04** | Ultrawide Viewport (3840px) | 4K display resolution | Maximum content container capped (`container-xl` / 1320px); no stretched typography |
| **TEST-BND-05** | Card Copy Variance | Sibling cards with varying copy | Title lines clamped to 2, description to 3; height variance <= 25% |
| **TEST-BND-06** | Invalid Solution Slug | `GET /solutions/non-existent-solution-123` | Clean HTTP 404 (Not Found); no 500 server traceback |
| **TEST-BND-07** | Invalid Industry Slug | `GET /industries/unregistered-industry-xyz` | Clean HTTP 404 (Not Found); no 500 server traceback |
| **TEST-BND-08** | Demo Form Empty Submit | `POST /request-demo` with empty payload | Returns HTTP 200 with field validation errors highlighted |
| **TEST-BND-09** | Demo Form Malformed Email | Email = `executive@notanemail` | Field error "Vui lòng nhập email hợp lệ" displayed |
| **TEST-BND-10** | Demo Form Honeypot Trigger | `website_url` field populated by bot | Silent redirect to `/thank-you` without creating CRM lead |
| **TEST-BND-11** | Demo Rate Limit Trigger | 2 submissions within 5 seconds | Error "Yêu cầu vừa được gửi. Vui lòng đợi một chút..." |
| **TEST-BND-12** | Max Length Input Stress | 5000 character message in demo form | Truncates or validates cleanly without database buffer overflow |
| **TEST-BND-13** | Missing Brochure PDF | `GET /industry/unknown/brochure` | Returns HTTP 404 cleanly |
| **TEST-BND-14** | Network Latency Simulation | 3000ms delay on static video poster | Poster fallback background displays immediately; zero white flash |
| **TEST-BND-15** | Special Character Escaping | Query string with `<script>` tags | Properly sanitized in rendered QWeb output; zero XSS vulnerability |

---

## 5. Tier 3: Cross-Feature Combinations & Interaction Testing

Tier 3 validates contracts and event flows across coupled subsystems:

| Test ID | Subsystem A | Subsystem B | Interaction Contract & Expected Behavior |
|---|---|---|---|
| **TEST-INT-01** | Mega-Menu Dropdown | Live Website Routing | Every href in mega-menu corresponds to an active HTTP 200 route |
| **TEST-INT-02** | Menu Hover Card | Custom DOM Event | Hovering solution link fires `insilos-menu-preview-change` with verified payload |
| **TEST-INT-03** | Video Scene Engine | Dual Video Stage Buffers | Video transitions alternate seamlessly between `#ins-hero-video-a` and `#b` |
| **TEST-INT-04** | 3D Cockpit Mousemove | RAF Throttling | Mousemove tilt calculations fire at most once per 16.6ms frame via RAF |
| **TEST-INT-05** | Video Scene Engine | IntersectionObserver | Scrolling stage out of viewport pauses video; scrolling back in resumes |
| **TEST-INT-06** | HBox Rhythm Locks | Responsive Grid Breakpoint | On `col-12` mobile collapse, height locks unlock cleanly to natural height |
| **TEST-INT-07** | Brand Orange Tokens | Button Pseudo-classes | Hover, active, focus states on `.btn-primary` maintain brand orange luminance |
| **TEST-INT-08** | Dynamic Sheen Bar | Active Route URL | Sheen bar initializes over current route's navbar link on initial page load |
| **TEST-INT-09** | Demo Request POST | CRM Lead Pipeline | Valid submission creates `insilos.demo.request` record and queues email |
| **TEST-INT-10** | Website Editor (`?enable_editor=1`) | Custom Insilos Snippets | All 13 custom snippets appear in Insilos snippet sidebar for drag-and-drop |

---

## 6. Tier 4: Real-World Application & Executive Journey Scenarios

Tier 4 tests model end-to-end user journeys representing key enterprise buyer personas.

### Scenario 1: Enterprise CEO Sovereign AI Evaluation Journey
1. **Entry**: CEO navigates to `https://insilos.com/`.
2. **Engagement**: Observes C3.ai benchmark telemetry and 4-layer 3D cockpit showing sovereign air-gapped architecture.
3. **Exploration**: Opens Mega-Menu, inspects hover cards for Vertical IDP and Knowledge Graph.
4. **Deep Dive**: Clicks `/solutions/vertical-idp`, reviews 3-way reconciliation diagram, 99.8% STP metric, and WCO SAFE compliance badge.
5. **Conversion**: Clicks "Yêu Cầu Demo Trực Tiếp", fills enterprise inquiry for 1,000+ employee logistics group.
6. **Confirmation**: Reaches `/thank-you` confirmation page; lead verified in CRM backend.

### Scenario 2: Supply Chain Director Logistics Modernization Audit
1. **Entry**: Director visits `/industries/logistics`.
2. **Investigation**: Reviews Freight Forwarding, Cold Chain, and Smart Warehousing bento cards.
3. **Symmetry Audit**: Verifies all 3 bento cards on row 1 maintain identical baseline button heights (`mt-auto`).
4. **Proof Inspection**: Reads Cát Lái Port case study (99.4% on-time dispatch, 34L/100km fuel optimization).
5. **Documentation**: Downloads official solution brochure at `/industry/logistics/brochure`.

### Scenario 3: Plant Operations Director Energy Reliability Walkthrough
1. **Entry**: Director accesses `/industries/energy`.
2. **Telemetry Validation**: Inspects IEC 61850 substation SCADA integration and DGA transformer telemetry card.
3. **ROI Verification**: Navigates to `/pricing`, interacts with `s_c3ai_roi_calculator` slider to calculate annual downtime savings.
4. **SLA Assurance**: Verifies < 15ms sub-second latency and 99.9% uptime micro-ledger commitment.

### Scenario 4: Chief Compliance Officer Sovereign Security Audit
1. **Entry**: CCO navigates to `/about`.
2. **Security Verification**: Reviews Zero-Trust architecture, SOC 2 Type II, ISO 27001, and Vietnamese Sovereign Data Law compliance.
3. **Technical Whitepaper**: Navigates to `/resources/trade-compliance-handbook`, reviews 6 GIR classification rules and Legal-Policy Dossier framework.
4. **Direct Contact**: Submits compliance inquiry via bottom funnel CTA.

---

## 7. Automated Test Runner Architecture (`test_e2e_suite.py`)

The automated E2E test runner is located at `enterprise/insilos_website/tools/test_e2e_suite.py`. It integrates 7 core verification suites executable via CLI:

```bash
# Standard test execution
.venv/bin/python enterprise/insilos_website/tools/test_e2e_suite.py

# Verbose execution with detailed diagnostic logs
.venv/bin/python enterprise/insilos_website/tools/test_e2e_suite.py --verbose

# JSON output mode for CI/CD integration
.venv/bin/python enterprise/insilos_website/tools/test_e2e_suite.py --json
```

### Verification Matrix Enforced by Runner:
1. **Quality Gate Suite**: Full pass across all 7 gates in `quality_gate.py`.
2. **Live HTTP Route Health**: HTTP 200 on all 25+ core and sub-routes.
3. **Inline Style Sanitation**: Zero `style="..."` attributes across all XML view templates.
4. **Iconography Standard**: Zero `<i class="fa fa-...">` tags; 100% Phosphor SVG.
5. **Brand Orange Button Conformance**: 100% buttons use `#FF8000` tokens; zero rogue classes.
6. **Typographic Balance & Orphan Prevention**: Semantic line-breaks, `text-wrap: balance`, 0 orphans.
7. **HBox Symmetrical Baseline Alignment**: Locked height alignment rate $\ge 95\%$ with `mt-auto`.
