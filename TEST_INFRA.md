# E2E Test Infra: Dashboard KPI Analytics & Executive Control Tower

## Test Philosophy
- **Requirement-Driven & Opaque-Box**: Exercises the Executive Control Tower Dashboard as an end user and executive would across desktop (1440x900) and tablet viewports.
- **Methodology**: Category-Partition + Boundary Value Analysis + Mathematical WCAG Contrast Measurement + Security Invariance Auditing.

## Verification Harnesses
1. **Playwright Dashboard Verification Suite**: `tools/verify_dashboard_analytics.js`
   - Invocation: `node tools/verify_dashboard_analytics.js`
   - Viewport: 1440x900
   - Authentication: Session-based via `/web/session/authenticate` on `http://localhost:28069`
   - Assertions:
     - 16-Column Carbon Grid layout integrity (`scrollWidth <= clientWidth`, 0 horizontal scroll)
     - Timeframe selector reactivity (Today, 7d, Month, Quarter, FY2026)
     - Real-time KPI Tiles (tabular-nums font, pure SVG sparklines, semantic delta badges)
     - Smart Factory MES OEE 3-pillar radial gauge & live station status
     - Logistics Drayage Hub fleet tracking & DET/DEM expiration countdown alert
     - High-Contrast Dark Mode aesthetic tokens (`#070B14`, `#141E33`, `#00F2FE`, `#10B981`)
     - Mathematical WCAG 2.1 AAA contrast ratio measurement (>= 7:1)
     - 0 uncaught console errors, 0 legacy genesis brand leaks
2. **Server Boot & Module Preload**:
   - Invocation: `.venv/bin/python insilos-bin -c insilos.conf -d odoo20_dev --stop-after-init`
   - Expected: Exit code 0, 700 modules preloaded cleanly, graceful shutdown.
3. **Counter Code Security Scanner**:
   - Invocation: `python3 scripts/counter_code_scanner.py --path . --scope enterprise/insilos_theme_genesis addons/web enterprise/web_studio addons/insilos_sap_fiori tools --max-allowed-detections 0`
   - Expected: 0 legacy genesis detections, `genesis_cleared: true`, exit code 0.
4. **Hard Fork Council Gates**:
   - Invocation: `python3 tools/run_hard_fork_council_gates.py --gates 8,10`
   - Expected: 100% PASS on Gate 8 (Enterprise Ported Modules) and Gate 10 (UI Brand Leak Sweep).
5. **Database Schema Invariance**:
   - Invocation: `git diff addons/ enterprise/`
   - Expected: 0 DDL statements, 0 table mutations, 0 column alterations on PostgreSQL `odoo20_dev`.

## Feature Coverage Matrix
| Feature | Tier 1 (Functional) | Tier 2 (Boundary/Edge) | Tier 3 (Cross-Feature) | Tier 4 (Executive Workload) |
|---|:---:|:---:|:---:|:---:|
| F1: Carbon 16-Col Grid | ✓ (16 cols rendered) | ✓ (no horizontal overflow) | ✓ (resizes with sidebar) | ✓ (desktop & tablet viewports) |
| F2: Timeframe Bar | ✓ (switches presets) | ✓ (custom date range) | ✓ (refreshes all cards) | ✓ (sub-second reactive update) |
| F3: Fiori Card Layout | ✓ (all 4 card types) | ✓ (empty data states) | ✓ (independent card loads) | ✓ (executive cockpits) |
| F4: Process Pipelines | ✓ (chevrons rendered) | ✓ (zero count handling) | ✓ (cross-module L2C/P2P) | ✓ (click-through drilldown) |
| F5: Backend ORM Service | ✓ (returns JSON envelope) | ✓ (null/missing parameters) | ✓ (dynamic date filtering) | ✓ (strict schema invariance) |
| F6: KPI Summary Tiles | ✓ (6 tiles rendered) | ✓ (large number formatting) | ✓ (links to recordsets) | ✓ (tabular-nums display) |
| F7: Pure SVG Sparklines | ✓ (SVG paths rendered) | ✓ (flatline / 1 point) | ✓ (area gradient fill) | ✓ (60 FPS rendering) |
| F8: Semantic Delta Badges | ✓ (percentage badges) | ✓ (zero change delta) | ✓ (cost vs revenue logic) | ✓ (color-inverted semantics) |
| F9: MES OEE 3-Pillars | ✓ (gauge rendered) | ✓ (0% - 100% limits) | ✓ (composite calculation) | ✓ (world-class benchmark) |
| F10: CNC Telemetry | ✓ (stations listed) | ✓ (offline station state) | ✓ (work order links) | ✓ (live state dots) |
| F11: Logistics Fleet | ✓ (vehicles listed) | ✓ (unassigned trucks) | ✓ (coupling status) | ✓ (route tracking) |
| F12: DET/DEM Warnings | ✓ (countdown tag) | ✓ (SLA < 24h urgency) | ✓ (SO / container links) | ✓ (penalty averted alert) |
| F13: High-Contrast Dark | ✓ (dark mode class) | ✓ (contrast transitions) | ✓ (all cards themed) | ✓ (#070B14 / #141E33 / #00F2FE) |
| F14: WCAG AAA Contrast | ✓ (contrast >= 7:1) | ✓ (small & large text) | ✓ (badges & sparklines) | ✓ (full DOM audit) |
| F15: Focus & Accessibility | ✓ (2px outline) | ✓ (keyboard navigation) | ✓ (interactive tiles) | ✓ (:focus-visible state) |
