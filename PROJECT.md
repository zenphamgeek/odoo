# Project: "Bring Arts into Technology" Visual Revolution Campaign across innoria.insilos.com

## Architecture
Layered frontend styling, 3D WebGL Web visual arts, and computer vision presentation on Odoo 20:
- **Design Tokens & Spatial Theme**: `enterprise/insilos_website/static/src/scss/insilos_liquid_spatial.scss` (Elegance Palette: Deep Obsidian, Titanium Slate, Liquid Aurora, Royal Electric Indigo, Warm Rose Glow; mesh gradient depth; soft ethereal glows; cardless floating primitives).
- **3D WebGL Storytelling Arts**: Three.js r180 air-gapped bundle (`static/src/lib/three/three.min.js`), `innoria_hero_controllers.js`, `innoria_hero_interactive_stage.js`, `innoria_hero_3d_manager.js` (3,600-point responsive mathematical wave mesh, 4-state morphing digital sphere, 4 narrative chapters, 360° inertia orbit, blueprint wireframe to PBR mesh morphing, camera focal length zoom).
- **Cinematic YOLO Industrial AI HUD**: `innoria_yolo_inspection.js`, `insilos_cctv_player.js`, `views/innoria_pages.xml`, `views/snippets_cctv.xml` (Dual-mode viewport: real 1080p industrial video feeds + micro-metrology inspection, dynamic 60 FPS laser scanline, real-time RAF telemetry readout).
- **Multi-Route Cardless Sub-routes**: Cardless UI floating layers on `/`, `/solutions`, `/industries`, `/resources`, `/showcase-3d` eliminating all `#E2E8F0` solid borders and boxed cards.
- **Verification & Deployment Infrastructure**: Playwright console/performance auditor, edge viewport invariants scanner, 3D stress harnesses, empirical WCAG contrast suite, quality gate, and multi-pod K8s deployment tool (`tools/sync_all_pods_and_reload.py`).

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Elegance Palette Token Architecture | Full CSS custom properties for Deep Obsidian (#050811, #0A101D), Titanium Slate (#1E293B), Liquid Aurora (#42E6C3 to #00F2FE), Royal Electric Indigo (#6366F1, #818CF8), Warm Rose Glow (#F43F5E, #FB7185) | M1 | Survey |
| 2 | Multi-Tier Mesh Gradient Depth | Declarative radial & mesh gradient depth formulas (`--ins-mesh-gradient-obsidian`, `--ins-mesh-gradient-aurora`) creating organic spatial depth without flat black | M1 | Survey |
| 3 | Diffused Ethereal Glow Borders | Ambient optical glow tokens (`--ins-glow-aurora`, `--ins-glow-indigo`, `--ins-glow-rose`) replacing harsh drop-shadows and solid box borders | M1 | Survey |
| 4 | Cardless Spatial UI Primitives | Reusable floating layer classes (`.ins-spatial-layer`, `.ins-floating-pod`, `.ins-mesh-canvas`, `.ins-cardless`) with 24px backdrop-blur and 160% saturation | M1 | Survey |
| 5 | WCAG AAA Contrast Normalization | Mathematical verification of 14.6:1 to 20.0:1 contrast for headings/text on obsidian, and dark text #05101E on mint/cyan (12.1:1 to 13.8:1) | M1 | Survey |
| 6 | Design Tokens & SCSS Test Suite Extension | Update `tools/test_design_tokens_wcag_empirical.py` to assert Elegance Palette tokens, WCAG contrast ratios, and `web.assets_frontend` compilation | M1 | Survey |
| 7 | Mathematical Particle Wave Engine | 3,600-point ($60 \times 60$) dynamic wave field ($y = A\sin(kx+\omega t)\cos(kz+\omega t)$) styled in Liquid Aurora palette with cursor repulsion displacement | M2 | Survey |
| 8 | Morphing Digital Sphere | 4-state geometric particle morphing (Wave Surface $\leftrightarrow$ Fibonacci Sphere $\leftrightarrow$ Toroidal Core $\leftrightarrow$ Quantum Hex Matrix) with smooth cubic hermite interpolation | M2 | Survey |
| 9 | 4-Chapter Storytelling State Machine | Synchronize 4 Hero modes (Cloud Fabric, AI Swarm, Smart ERP, Trust Security) with lighting, camera position, geometry morphing, and HUD titles | M2 | Survey |
| 10 | Animated Exploded View & Leader Lines | Central 3D core separates into elevated volumetric layers with glowing data buses during Chapter 2 (Intelligent ERP) | M2 | Survey |
| 11 | Blueprint Wireframe to PBR Mesh Morph | Dynamic shader/material transition animating from cyan holographic blueprint wireframe to photorealistic reflective PBR metallic mesh | M2 | Survey |
| 12 | 360° Kinetic Orbit with Inertia Damping | Custom pointer drag rotation with exponential velocity decay ($\lambda = 3.2$) and vertical pitch clamping [$15^\circ, 85^\circ$] | M2 | Survey |
| 13 | Cinematic Focal Length Camera Zoom | Animate camera FOV ($55^\circ \rightarrow 35^\circ$) with projection matrix updates for dramatic depth compression during chapter transitions | M2 | Survey |
| 14 | WebGL Context Loss & Mobile Optimization | Clamp DPR to 2.0, dynamic particle scaling (1,600 on mobile, 3,600 on desktop) guaranteeing $\ge 55$ FPS on iPhone viewports; zero memory leak | M2 | Survey |
| 15 | Dual-Mode Cinematic AI Viewport | Architectural fusion of real industrial video feeds and micro-metrology synthetic inspection in high-tech viewport frame | M3 | Survey |
| 16 | Authentic Industrial Video Streaming | Seamless integration of high-resolution CCTV video feeds (`cctv_cam02_welding_ss400.mp4`, etc.) with continuous 60 FPS playback | M3 | Survey |
| 17 | Real-time AI HUD Visual Overlay | Dynamic 60 FPS sweeping laser scanline, animated bounding boxes with confidence tags, corner reticles, and optical calibration grid | M3 | Survey |
| 18 | Live Telemetry Real-time Stream | High-frequency RAF ticker displaying live latency (11.2ms), stream FPS (60.0), precision (99.42%), and defect classifications | M3 | Survey |
| 19 | Featured YOLO HUD Placement on Homepage | Mount featured YOLO/CCTV inspection block on `innoria_homepage.xml` (`/`) and elevate on `/industries` | M3 | Survey |
| 20 | Homepage (`/`) Cardless Conversion | Convert 6 vertical solution cards, 4 cadence steps, and closing CTA into `.ins-spatial-layer` with soft diffused glow, eliminating `#E2E8F0` solid borders | M4 | Survey |
| 21 | `/solutions` Cardless Polish | Remove outer box from `s_innoria_3d_solutions_erp`, convert 4 ERP pillars from 4px solid left stripes to organic floating layers, convert comparison matrix to open liquid table | M4 | Survey |
| 22 | `/industries` Cardless Polish | Eliminate `#FFFFFF` section clash on dark canvas, convert 4 case studies and 101 Industries directory into exhibition case study layout | M4 | Survey |
| 23 | `/resources` Cardless Polish | Transform whitepaper cards and webinar cards into cardless floating liquid spatial tiles with glowing filter pills | M4 | Survey |
| 24 | `/showcase-3d` Elegance Polish | Harmonize 5-snippet vertical stack under Elegance Palette, convert `.ins-3d-viewport` and 3 BOM ledger cards to spatial frames | M4 | Survey |
| 25 | DOM Invariant & Banned Phrase Elimination | Verify zero occurrences of banned phrases ("Kéo chuột", "Hover khối", "Rê chuột", "360° interactive", "Hardware 3D // 60 FPS") across all views | M4 | Survey |
| 26 | Design Tokens & WCAG Verification | Execute `tools/test_design_tokens_wcag_empirical.py` asserting all tokens, contrast ratios $\ge 4.5:1$, and SCSS compilation | M5 | Survey |
| 27 | 3D Stress & Performance Verification | Execute `tools/stress_hero_3d_performance.js` (40 clicks at 50ms, 180 frames $\ge 55$ FPS, zero leak) and `tools/empirical_stress_3d_deck.js` | M5 | Survey |
| 28 | Playwright Multi-Route Console & LCP Audit | Execute `tools/audit_website_console_performance.js` across 7 routes asserting 0 console errors, 0 network errors, LCP $\le 2.2$s, CLS $\le 0.05$ | M5 | Survey |
| 29 | Edge Viewport & DOM Invariants Audit | Execute `tools/verify_edge_viewports_and_dom_invariants.js` asserting 0 overflow at 320/414/820/1920px and 0 banned phrases | M5 | Survey |
| 30 | Quality Gate Compliance Audit | Execute `python3 enterprise/insilos_website/tools/quality_gate.py` asserting 7/7 gates PASS | M5 | Survey |
| 31 | Visual Evidence High-Res Audit Deck | Capture full-page screenshots at 1920x1080 (Desktop) and 390x844 (Mobile) for `/`, `/solutions`, `/industries`, `/resources`, `/showcase-3d` | M5 | Survey |
| 32 | Multi-Pod Production Sync & Probe | Execute `tools/sync_all_pods_and_reload.py` syncing all 3 K8s pods and validating HTTP/2 200 OK | M5 | Survey |

## Milestones
| # | Name | Scope | Dependencies | Status | Key Outputs |
|---|------|-------|-------------|--------|-------------|
| M1 | Elegance Palette & Liquid Spatial Theme | Tokens #1–6: SCSS tokens engine, mesh gradients, ethereal diffused glows, cardless primitives, WCAG test suite | none | DONE | `insilos_liquid_spatial.scss`, updated `__manifest__.py`, expanded `test_design_tokens_wcag_empirical.py` (97 tests pass) |
| M2 | Hero 3D Interactive Storytelling Arts | Features #7–14: 3,600-point particle wave field, 4-state morphing sphere, 4-chapter narrative transitions, exploded view, wireframe to mesh, 360° inertia orbit | M1 | DONE | `innoria_hero_controllers.js`, `innoria_hero_interactive_stage.js`, `innoria_hero_3d_manager.js` (stress & flow PASS) |
| M3 | Cinematic YOLO Industrial AI HUD | Features #15–19: Dual-mode industrial video viewport, 60 FPS sweeping laser scanline, pulsing bounding boxes, real-time RAF telemetry ticker | M1 | DONE | `innoria_yolo_inspection.js`, `snippets_cctv.xml`, `insilos_cctv_player.js` (Gate 4 diversity PASS) |
| M4 | Multi-Route Cardless Conversion & Polish | Features #20–25: Cardless conversion on `/`, `/solutions`, `/industries`, `/resources`, `/showcase-3d`, elimination of rigid borders & banned phrases | M1 | DONE | Refactored QWeb views, 24/24 edge viewports PASS, 0 banned phrases |
| M5 | Comprehensive E2E Verification & Pod Sync | Features #26–32: 6 automated test suites, high-res visual audit deck (1920x1080 & 390x844), multi-pod K8s deployment & live probe | M2, M3, M4 | DONE | 100% test pass, 3 K8s pods synced HTTP/2 200 OK, git commit af4f9fe69 on main |

## Interface Contracts
### Tokens ↔ Liquid Spatial Styles
- All colors and gradients MUST consume the Elegance Palette CSS variables (`--ins-obsidian-deep`, `--ins-obsidian-surface`, `--ins-titanium-slate`, `--ins-aurora-mint`, `--ins-aurora-cyan`, `--ins-electric-indigo`, `--ins-rose-glow`).
- Hardcoded `#E2E8F0` solid borders and boxed machine shadows are strictly prohibited on cardless elements.
- All floating spatial layers MUST utilize `backdrop-filter: blur(var(--ins-spatial-layer-blur))` and `--ins-spatial-border-glow`.

### Three.js Hero Manager ↔ Interactive Stage Controllers
- Particle waves and morphing spheres MUST register with `InnoriaHero3DManager` disposables for clean GPU garbage collection.
- Pointer tracking MUST calculate normalized device coordinates (NDC) and pass them to active controllers.
- Camera FOV and position changes MUST execute via smooth LERP in requestAnimationFrame.

### Industrial AI HUD ↔ Telemetry Controllers
- YOLO HUD scanline and bounding boxes MUST synchronize with video playback clock without blocking main thread.
- Telemetry tickers (Latency, FPS, Precision) MUST update via requestAnimationFrame with micro-fluctuations matching industrial sensor physics.

## Code Layout
- Tokens & Liquid Spatial SCSS: `enterprise/insilos_website/static/src/scss/insilos_liquid_spatial.scss`
- Base Website Styling: `enterprise/insilos_website/static/src/scss/insilos.scss`
- Theme Styling & Scoped Overrides: `enterprise/insilos_website/static/src/scss/innoria_theme.scss`
- 3D Hero Controllers: `enterprise/insilos_website/static/src/js/innoria_hero_controllers.js`
- 3D Stage & Storytelling Manager: `enterprise/insilos_website/static/src/js/innoria_hero_interactive_stage.js`
- 3D WebGL Engine & Lifecycle: `enterprise/insilos_website/static/src/js/innoria_hero_3d_manager.js`
- YOLO Inspection Engine: `enterprise/insilos_website/static/src/js/innoria_yolo_inspection.js`
- CCTV Player Engine: `enterprise/insilos_website/static/src/js/insilos_cctv_player.js`
- Homepage View: `enterprise/insilos_website/views/innoria_homepage.xml`
- Pages View (`/solutions`, `/industries`): `enterprise/insilos_website/views/innoria_pages.xml`
- Resources View: `enterprise/insilos_website/views/resources_about_demo.xml`
- 3D & CCTV Snippets: `enterprise/insilos_website/views/snippets_3d.xml`, `enterprise/insilos_website/views/snippets_cctv.xml`
- Test Harnesses:
  - `tools/test_design_tokens_wcag_empirical.py`
  - `tools/stress_hero_3d_performance.js`
  - `tools/empirical_stress_3d_deck.js`
  - `tools/audit_website_console_performance.js`
  - `tools/verify_edge_viewports_and_dom_invariants.js`
  - `enterprise/insilos_website/tools/quality_gate.py`
  - `tools/sync_all_pods_and_reload.py`
