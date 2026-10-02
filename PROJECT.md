# Project: Dashboard KPI Analytics & Executive Control Tower

## Executive Summary
Trung tâm điều hành doanh nghiệp Dashboard KPI Analytics & Executive Control Tower theo chuẩn SAP Fiori Horizon Overview Page (OVP) và IBM Carbon Design System 11 trên nền tảng Insilos Enterprise (Odoo 20 LTS).

## Architecture
- **Framework**: OWL 3 (`@insilos/owl`) + SAP Fiori Horizon Cards Hierarchy + IBM Carbon 16-Column Responsive Grid.
- **Backend Service**: `models.AbstractModel` (`_auto = False`) with `@api.model` read-only aggregation queries ensuring **Strict Database Schema Invariance** (0 DDL/schema changes on PostgreSQL `odoo20_dev`).
- **Gateway Endpoint**: `/insilos/api/v1/control_tower/kpis` (JSON envelope, `Server: insilos/20.0`).
- **Action Client Registration**: Action `insilos_executive_control_tower` registered in `addons/insilos_sap_fiori`.
- **Accessibility & Contrast**: WCAG 2.1 AAA (>= 7:1 contrast ratio) and High-Contrast Dark Mode (`#070B14` canvas, `#141E33` card, `#00F2FE` Tech Cyan neon, `#10B981` Emerald).
- **Micro-Visualizations**: Native mathematical SVG sparklines (viewBox `0 0 120 36`), radial OEE gauge, and semantic delta badges (+/- %) with zero external heavy charting dependencies.

## Code Layout & Write Ownership
| File Path | Component / Module | Write Ownership |
|---|---|---|
| `tools/verify_dashboard_analytics.js` | Playwright E2E Verification Suite | E2E Testing Track |
| `addons/insilos_sap_fiori/models/insilos_control_tower.py` | Read-only ORM Aggregation Service (`AbstractModel`) | Milestone 2 Worker |
| `addons/insilos_sap_fiori/controllers/control_tower_controller.py` | Perimeter Gateway Controller Endpoint | Milestone 2 Worker |
| `addons/insilos_sap_fiori/data/sap_menu_data.xml` | Menu Item & Action Client Declaration | Milestone 1 Worker |
| `addons/insilos_sap_fiori/views/sap_control_tower_views.xml` | Action Client View Declaration | Milestone 1 Worker |
| `addons/insilos_sap_fiori/static/src/executive_control_tower/executive_control_tower.js` | Root OWL 3 Action Component | Milestone 1 Worker |
| `addons/insilos_sap_fiori/static/src/executive_control_tower/executive_control_tower.xml` | Carbon 16-Col Grid Root QWeb Template | Milestone 1 Worker |
| `addons/insilos_sap_fiori/static/src/executive_control_tower/components/timeframe_filter_bar.js` | Global Timeframe Bar Component | Milestone 1 Worker |
| `addons/insilos_sap_fiori/static/src/executive_control_tower/components/timeframe_filter_bar.xml` | Timeframe Bar Template | Milestone 1 Worker |
| `addons/insilos_sap_fiori/static/src/executive_control_tower/components/kpi_summary_tile.js` | KPI Summary Tile Component | Milestone 2 Worker |
| `addons/insilos_sap_fiori/static/src/executive_control_tower/components/kpi_summary_tile.xml` | KPI Summary Tile Template (SVG Sparkline) | Milestone 2 Worker |
| `addons/insilos_sap_fiori/static/src/executive_control_tower/components/mes_oee_card.js` | Smart Factory MES OEE Hub Component | Milestone 3 Worker |
| `addons/insilos_sap_fiori/static/src/executive_control_tower/components/mes_oee_card.xml` | MES OEE Gauge & Telemetry Template | Milestone 3 Worker |
| `addons/insilos_sap_fiori/static/src/executive_control_tower/components/logistics_hub_card.js` | Logistics Drayage & DET/DEM Hub Component | Milestone 3 Worker |
| `addons/insilos_sap_fiori/static/src/executive_control_tower/components/logistics_hub_card.xml` | Logistics Drayage & DET/DEM Hub Template | Milestone 3 Worker |
| `addons/insilos_sap_fiori/static/src/executive_control_tower/components/process_monitoring_card.js` | E2E Chevron Process Pipelines (L2C, P2P, O2D) | Milestone 1 Worker |
| `addons/insilos_sap_fiori/static/src/executive_control_tower/components/process_monitoring_card.xml` | Process Pipelines Template | Milestone 1 Worker |
| `addons/insilos_sap_fiori/static/src/executive_control_tower/executive_control_tower.scss` | Carbon Grid & Fiori Card SCSS Styling | Milestone 4 Worker |
| `enterprise/insilos_theme_genesis/static/src/scss/insilos_modern_tokens.scss` | Theme SCSS & Dark Mode Contrast Tokens | Milestone 4 Worker |

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---|---|---|---|
| F1 | IBM Carbon 16-Col Responsive Grid | Layout breakpoint hierarchy (Desktop 16-col, Tablet 8-col, Mobile 4-col) | M1 | Survey R1 |
| F2 | Global Timeframe Bar | Presets (Today, 7d, Month, Quarter, FY2026) with reactive filter state | M1 | Survey R1 |
| F3 | Fiori Cards Hierarchy Layout | Container for Analytical, Summary, Process, and Priority Cards | M1 | Survey R1 |
| F4 | Process Monitoring Pipelines | Multi-stage chevron flows for L2C, P2P, and O2D with click-throughs | M1 | Survey R1 |
| F5 | Read-Only Aggregation Backend | `AbstractModel` and JSON controller providing real-time data under strict schema invariance | M2 | Survey R2 |
| F6 | Executive KPI Tiles | 6 core KPI summary tiles (Revenue, Spend/TCO, OCF, OTIF, DOH, HSE) | M2 | Survey R2 |
| F7 | Pure SVG Micro-Sparklines | Mathematical coordinate mapping for 7d/30d trends without 3rd party libraries | M2 | Survey R2 |
| F8 | Semantic Delta Badges | YoY/MoM percentage delta indicators with color inversion for costs/hazards | M2 | Survey R2 |
| F9 | Smart Factory MES OEE Hub | 3-Pillar radial/bar gauge (Availability >= 92%, Performance >= 95%, Quality >= 99%) | M3 | Survey R3 |
| F10 | Live CNC & Robot Telemetry | Real-time status for Fiber Laser 12kW, Yaskawa welding robot, and press brake | M3 | Survey R3 |
| F11 | Logistics Drayage Fleet Hub | Fleet tracking (Hyundai Xcient, CIMC chassis) between Cat Lai & Cai Mep | M3 | Survey R3 |
| F12 | DET/DEM Penalty Warning | Real-time SLA countdown and penalty avoidance alert | M3 | Survey R3 |
| F13 | High-Contrast Dark Mode | Deep slate `#070B14` canvas, `#141E33` card, `#00F2FE` Tech Cyan neon accents | M4 | Survey R4 |
| F14 | WCAG AAA Contrast (>= 7:1) | Strict contrast compliance on typography, labels, numbers, and badges | M4 | Survey R4 |
| F15 | Tabular Nums & Focus Outlines | Precision font styling (`tabular-nums`) and `:focus-visible` 2px outlines | M4 | Survey R4 |
| F16 | Playwright E2E Test Suite | Headless test harness verifying 100% of dashboard cards, grid, and contrast | E2E | Survey R1-R4 |
| F17 | Platform & Council Gates Invariance | Boot 700 modules, 0 genesis detections, Council Gates 8 & 10, git diff = 0 | Final | Survey R4 |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|---|---|---|---|
| E2E | E2E Testing Track | Build `tools/verify_dashboard_analytics.js` | none | IN_PROGRESS |
| M1 | Executive Control Tower Architecture | Carbon 16-Col Grid, Action Client, Timeframe Bar, Process Pipelines | none | IN_PROGRESS |
| M2 | Real-Time KPI Tiles & SVG Sparklines | Backend AbstractModel aggregation & KPI Tiles with SVG Sparklines | M1 | PLANNED |
| M3 | MES OEE Hub & Logistics Drayage Hub | OEE 3-pillar gauge, station telemetry, fleet tracking, DET/DEM countdown | M1, M2 | PLANNED |
| M4 | SCSS Component & Dark Mode Polish | Carbon SCSS, High-Contrast Dark Mode tokens, WCAG AAA contrast | M1, M2, M3 | PLANNED |
| Final | Council Gates & Adversarial Audit | Gates 8 & 10, Server Boot, Counter Code Scanner, Git DDL Invariance | E2E, M1-M4 | PLANNED |

## Interface Contracts

### Backend ↔ Frontend Contract
Endpoint: `/insilos/api/v1/control_tower/kpis` or RPC `insilos.control.tower.get_executive_kpi_metrics(timeframe, filters)`
Request Payload:
```json
{
  "timeframe": "7d", // "today" | "7d" | "month" | "quarter" | "fy2026"
  "filters": {
    "company_id": 1,
    "domain": "all" // "all" | "sd" | "mm" | "pp" | "le" | "hse"
  }
}
```
Response Payload Schema:
```json
{
  "success": true,
  "timeframe": "7d",
  "kpis": {
    "net_revenue": { "value": 1860500000.0, "value_formatted": "1.860 Tỷ ₫", "delta_percent": 14.2, "delta_semantic": "positive", "sparkline": { "points": [...], "line_d": "...", "area_d": "..." } },
    "procurement_tco": { "value": 615300000.0, "value_formatted": "615.3 Tr ₫", "tco_savings_annual_formatted": "₫2,029,050,000 / Năm", "delta_percent": -8.6, "delta_semantic": "positive", "sparkline": { ... } },
    "operating_cash_flow": { "value": 1245250000.0, "value_formatted": "+1.245 Tỷ ₫", "delta_percent": 18.5, "delta_semantic": "positive", "sparkline": { ... } },
    "otif_delivery": { "value": 99.2, "value_formatted": "99.2%", "threshold_formatted": ">= 98.5%", "delta_percent": 0.7, "delta_semantic": "positive", "sparkline": { ... } },
    "days_on_hand": { "value": 18.5, "value_formatted": "18.5 Ngày", "delta_percent": -10.2, "delta_semantic": "positive", "sparkline": { ... } },
    "safety_index": { "value": 100.0, "value_formatted": "100%", "ppe_compliance_formatted": "99.8%", "lost_time_injuries": 0, "sparkline": { ... } }
  },
  "industrial_mes": {
    "oee_composite": 92.5,
    "pillars": {
      "availability": { "threshold": 92.0, "actual": 94.2, "status": "passed" },
      "performance": { "threshold": 95.0, "actual": 98.1, "status": "passed" },
      "quality": { "threshold": 99.0, "actual": 99.8, "status": "passed" }
    },
    "workcenters": [
      { "code": "WC-CUT-01", "name": "Fiber Laser 12kW", "actual_oee": 91.2, "status": "running" },
      { "code": "WC-WELD-01", "name": "Yaskawa Motoman", "actual_oee": 94.8, "status": "running" }
    ]
  },
  "logistics_hub": {
    "drayage_fleet": [
      { "plate": "51C-982.45", "model": "Hyundai Xcient GT", "status": "in_transit" },
      { "plate": "51R-089.34", "model": "CIMC Chassis 40ft", "status": "coupled" }
    ],
    "container_moves": {
      "det_dem_countdown_hours": 28.0,
      "buffer_time_hours": 8.5,
      "potential_penalty_averted": 48000000.0,
      "potential_penalty_formatted": "48,000,000 ₫"
    }
  },
  "process_pipelines": {
    "lead_to_cash": [ { "stage": "Inquiries", "count": 24 }, { "stage": "Quotations", "count": 18 }, { "stage": "Orders", "count": 42 }, { "stage": "Billing", "count": 36 } ],
    "procure_to_pay": [ { "stage": "Requisitions", "count": 12 }, { "stage": "RFQs", "count": 8 }, { "stage": "POs", "count": 26 }, { "stage": "Inbound", "count": 24 } ],
    "order_to_delivery": [ { "stage": "Confirmed", "count": 10 }, { "stage": "Production", "count": 8 }, { "stage": "QA Inspection", "count": 6 }, { "stage": "Dispatched", "count": 14 } ]
  }
}
```
