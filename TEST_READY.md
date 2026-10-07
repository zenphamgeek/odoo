# TEST_READY: Innoria Platform E2E Verification & Quality Harnesses

**Campaign:** Innoria Breakthrough UI/UX & 3D Architecture Campaign  
**Track:** E2E Testing Track — Multi-Route Quality & Hero Flow Test Suites  
**Author:** teamwork_preview_test_writer_e2e  
**Date:** 2026-10-06T16:06:00Z  
**Status:** READY FOR VERIFICATION & CONTINUOUS AUDITING  

---

## 1. Executive Summary

This document announces the completion and availability of the Automated E2E Verification Harnesses for the Innoria Sovereign Web Platform (`https://innoria.insilos.com/`). Two dedicated, non-trivial, adversarial Playwright test runners have been built and verified in the repository:

1. `tools/verify_routes_layout_quality.js`: Multi-route responsive layout, DOM purity, zero-overflow, and WCAG AA/AAA contrast scanner across 6 main routes and 3 standard viewports (Mobile 375x812, Tablet 768x1024, Desktop 1440x900).
2. `tools/verify_hero_interactive_flow.js`: Homepage interactive stage harness verifying B2B cinema narrative, 4-mode scene switching, VIP CTA button with halo pulse, kinetic 60 FPS animation loop, and console error cleanliness.

Both test runners adhere strictly to progressive testability and test integrity guidelines:
- **Zero facades**: Real DOM queries, computed style extractions, relative luminance mathematics, and in-page requestAnimationFrame performance benchmarks.
- **Fail-safe exit codes**: Return exit code `0` on 100% PASS, non-zero (`1`) on any defect detected.
- **Configurable targets**: Accept `--url <base_url>` to run seamlessly against production (`https://innoria.insilos.com`), local development instances (`http://localhost:28069` or `http://localhost:28070`), or preview pods.

---

## 2. Test Suites Inventory & Specifications

### 2.1 Multi-Route Layout & DOM Quality Scanner (`tools/verify_routes_layout_quality.js`)

- **File Path:** `/home/zen/O20/tools/verify_routes_layout_quality.js`
- **Scope:** 6 Main Routes across 3 Responsive Viewports (18 Route x Viewport combinations):
  * **Routes:**
    1. `/` — Homepage (Lõi Đa Nền Tảng)
    2. `/solutions` — Solutions Directory (AI-Enhanced ERP)
    3. `/platform` — Platform (Digiforce Studio & Mojo AI)
    4. `/industries` — Industries (Ultra AI Vision & HSE)
    5. `/about` — About Us (Doanh Nghiệp & Đội Ngũ)
    6. `/contactus` — Contact Us (Tư Vấn Doanh Nghiệp & FAQ)
  * **Viewports:**
    - Mobile: `375 x 812` (iPhone X/13/14 profile)
    - Tablet: `768 x 1024` (iPad portrait profile)
    - Desktop: `1440 x 900` (MacBook / Standard HD widescreen)
- **Target Host:** `https://innoria.insilos.com` (configurable via `--url <url>`)
- **Gates Evaluated per Route / Viewport:**
  1. **3D Component Transparency:**
     - 100% of 3D component stage containers (`.innoria-solutions-3d-stage`, `[data-snippet="s_innoria_3d_solutions_erp"]`, `.deck-container-3d`, `#innoriaTopologyViewport`, `.innoria-deck-viewport`, `.hero-3d-canvas-wrap`) must compute `background: transparent` (alpha = 0), `border: none` (0px), and `box-shadow: none`.
  2. **DOM Instructional Text Purity:**
     - Exactly 0 instructional phrases in DOM (searches `document.body.innerText`, all text nodes via `TreeWalker`, and accessibility attributes).
     - Prohibited phrases: `"Kéo chuột"`, `"Hover khối"`, `"Rê chuột"`, `"360° interactive"`, `"360°"`, `"Hardware 3D // 60 FPS"`, `"HARDWARE 3D // 60 FPS"`.
  3. **Zero Horizontal Overflow:**
     - 100% `scrollWidth === clientWidth` on all viewports (`overflowDiff <= 1px` subpixel margin).
     - Automated offender detection logs exact elements exceeding viewport bounds.
  4. **WCAG AA/AAA Contrast Compliance:**
     - Computed via relative luminance formula $L = 0.2126 R + 0.7152 G + 0.0722 B$ with multi-layer alpha blending against parent containers.
     - Body text & UI labels: $\ge 4.5:1$ (WCAG AA).
     - Headings on dark canvas ($L < 0.2$): $\ge 7.0:1$ (WCAG AAA).
     - Large text ($\ge 24\text{px}$, or $\ge 18.5\text{px}$ bold): $\ge 3.0:1$ (WCAG AA).
     - Specifically catches FAQ accordion white-on-white (`.inn-faq-button`), comparison table cyan-on-white, and badge/job title contrast flaws.
  5. **Console Cleanliness:**
     - 0 unhandled JavaScript exceptions or console errors recorded.

### 2.2 Hero Interactive Flow & 60 FPS Harness (`tools/verify_hero_interactive_flow.js`)

- **File Path:** `/home/zen/O20/tools/verify_hero_interactive_flow.js`
- **Scope:** Interactive flow, state machine, and animation performance of the Homepage Hero Stage (`#innoria_hero_cover`).
- **Gates Evaluated:**
  1. **Hero Stage Mount & Visibility:** Container `#innoria_hero_cover` present and visible.
  2. **Hero Stage Controller:** Evaluates `window.innoriaHeroInteractiveStage` or `window.innoriaHeroSlider`.
  3. **B2B Cinema Headline:** Asserts presence of high-impact narrative: `"Tailored Technology for Sovereign Enterprise"`.
  4. **4-Mode Scene Switcher Transitions:**
     - Mode 0: `[Cloud & Data Fabric]` (`cloud-fabric`)
     - Mode 1: `[Autonomous AI Swarm]` (`ai-swarm`)
     - Mode 2: `[Intelligent ERP]` (`smart-erp`)
     - Mode 3: `[Enterprise Trust & Security]` (`trust-security`)
     - Clicks each mode tab, waits for LERP camera/scene transition, asserts `.active` class on nav item, visible content pane (`opacity > 0.1`), and controller index synchronization.
  5. **VIP CTA Button & Halo Pulse:**
     - Locates button `.btn-hero-vip-poc` with exact text `"Trải Nghiệm Live Proof-of-Concept 3 Giờ"`.
     - Asserts kinetic halo pulse effect (`@keyframes haloPulse` in stylesheet or `animation` computed style).
     - Asserts target link points to `#innoria_contact_section` (or `#contactus`).
  6. **60 FPS Kinetic Performance Benchmark:**
     - In-page `requestAnimationFrame` loop capturing 120 consecutive frames (~2 seconds).
     - Measures Average FPS, Min FPS, Max Delta (ms), and frame freeze count (deltas $> 100\text{ms}$).
     - Asserts zero frame freezes ($> 100\text{ms}$) and compliant average frame rate.
  7. **Zero Instructional Text in Hero DOM:** Asserts 0 banned instruction strings in `#innoria_hero_cover`.
  8. **Console Cleanliness:** 0 unhandled console errors during the interactive session.

---

## 3. How to Run the Test Suites

### 3.1 Running Multi-Route Quality Scanner

```bash
# Run full suite across all 6 routes and 3 viewports against production
node tools/verify_routes_layout_quality.js

# Run against local development instance
node tools/verify_routes_layout_quality.js --url http://localhost:28069

# Run verbose mode with diagnostic details
node tools/verify_routes_layout_quality.js --verbose

# Run single route on a specific viewport
node tools/verify_routes_layout_quality.js --route /solutions --viewport mobile
node tools/verify_routes_layout_quality.js --route /contactus --viewport desktop

# Export results to JSON
node tools/verify_routes_layout_quality.js --json /tmp/innoria_routes_audit.json
```

### 3.2 Running Hero Interactive Flow Test

```bash
# Run against production
node tools/verify_hero_interactive_flow.js

# Run against local development instance
node tools/verify_hero_interactive_flow.js --url http://localhost:28069

# Run verbose mode
node tools/verify_hero_interactive_flow.js --verbose

# Run with custom minimum FPS threshold (e.g., in virtualized CI)
node tools/verify_hero_interactive_flow.js --min-fps 20

# Export results to JSON
node tools/verify_hero_interactive_flow.js --json /tmp/hero_flow_report.json
```

---

## 4. Acceptance Criteria Matrix & Pre-Flight Baseline

When executed against the current live production cluster (`https://innoria.insilos.com/`) prior to Milestone 1–4 deployment, the test runners produced genuine, non-zero diagnostic failures that corroborate the survey findings:

| Gate | Acceptance Criteria | Baseline Result (Pre-Deployment) | Expected Status Post-Deployment (M1-M4) |
|---|---|---|---|
| **3D Transparency** | 100% of 3D components render `background: transparent`, `border: none`, `box-shadow: none` | **PASS (1/1)** on 3D deck container; M1 solutions component pending deployment | **PASS (100%)** |
| **Zero Instruction Text** | Exactly 0 banned phrases in DOM (`"Hover khối"`, `"Kéo chuột"`, `"360°"`, `"Hardware 3D // 60 FPS"`) | **FAIL (3 detections on `/`)**: `"Rê chuột"`, `"HARDWARE 3D // 60 FPS"`, `"Hover khối..."` | **PASS (0 detections)** |
| **Zero Overflow** | `scrollWidth === clientWidth` on 375px, 768px, 1440px | **PASS (0px overflow)** across tested routes | **PASS (0px overflow)** |
| **WCAG Contrast** | Body text $\ge 4.5:1$, headings on dark $\ge 7:1$, large text $\ge 3:1$ | **FAIL (Violations on `/contactus`, `/about`, `/platform`)**: FAQ accordion white-on-white (1.05:1), job titles (2.4:1), blueprint bullets | **PASS (100% compliant)** |
| **B2B Cinema Headline** | Hero contains `"Tailored Technology for Sovereign Enterprise"` | **FAIL**: Live site serves legacy DigiForce Low-Code banner | **PASS** |
| **Hero 4-Mode Switcher** | Clicks switch modes, activate classes, crossfade content panes | **PASS (4/4 modes)** | **PASS (4/4 modes)** |
| **VIP CTA Halo Pulse** | Button `"Trải Nghiệm Live Proof-of-Concept 3 Giờ"` with `@keyframes haloPulse` | **FAIL**: Live site has `"Đặt Lịch Tư Vấn 3 Giờ"` without halo pulse | **PASS** |
| **Kinetic 60 FPS** | Zero frame freezes $> 100\text{ms}$ | **PASS**: 0 freeze episodes | **PASS** |
| **Console Cleanliness** | 0 unhandled console errors | **FAIL (1 error)**: 404 asset resource failure | **PASS (0 errors)** |

---

## 5. Next Steps & Handoff to Implementing Agents and QA Auditor

1. **Implementation Workers (M1, M2, M3):**
   - Utilize `tools/verify_routes_layout_quality.js` and `tools/verify_hero_interactive_flow.js` as continuous feedback loops.
   - Run `node tools/verify_routes_layout_quality.js --route <route> --verbose` to verify fixes for contrast, 3D transparency, and instruction text elimination.
   - Run `node tools/verify_hero_interactive_flow.js --verbose` to verify hero headline, 4-mode switcher, and halo pulse button.
2. **Deployment Worker (M4):**
   - Run `tools/sync_all_pods_and_reload.py` to synchronize updated QWeb templates and asset bundles to all Kubernetes pods.
   - Execute both test runners against `https://innoria.insilos.com/` to verify clean exit code `0`.
3. **QA Auditor:**
   - Run both runners with default options; assert exit code `0` and 100% PASS across all diagnostic gates.
