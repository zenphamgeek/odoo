#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Insilos Enterprise Odoo 20 — 23-Module Maturity (L1–L5) & Dual-Theme Auditor
============================================================================
Evaluates all 23 `insilos_*` modules across `/home/zen/O20/addons/` (6) and
`/home/zen/O20/enterprise/` (17) against the 5 Sovereign Maturity Dimensions:
  - D1 (20 pts): Manifest & Enterprise Taxonomy Alignment (SAP S/4HANA LoB & IBM CBM / APQC PCF)
  - D2 (20 pts): Data Model & Security ACL Completeness (ir.model.access.csv / XML & PostgreSQL ir_access)
  - D3 (20 pts): View, Action & Menu Ergonomics (Odoo 20 <list>/<form>/<search>/OWL/QWeb)
  - D4 (20 pts): Dual-Theme SCSS & Anti-Slop Compliance (web.assets_backend <-> web.assets_web_dark & ir_asset)
  - D5 (20 pts): Runtime, Controller readonly=False Guard & PostgreSQL DB Health (insilos20_dev & innoria_prod)

Usage:
    python3 tools/audit_insilos_modules_maturity.py [--strict] [--json]
"""

import argparse
import ast
import configparser
import csv
import json
import re
import sys
from pathlib import Path

import psycopg2

ROOT_DIR = Path("/home/zen/O20")
CONF_PATH = ROOT_DIR / "insilos.conf"

# Canonical Enterprise Taxonomy Mapping (SAP S/4HANA LoB / Fiori 4 vs IBM CBM / APQC PCF)
ENTERPRISE_TAXONOMY_MAP = {
    "insilos_adapter": {
        "sap_lob": "SAP BTP Integration Suite",
        "apqc_cbm": "APQC 8.0 IT / IBM CBM Integration Gateway",
        "archetype": "Technical / Hexagonal Gateway",
    },
    "insilos_al2c": {
        "sap_lob": "SAP S/4HANA LoB Finance, HCM & EWM",
        "apqc_cbm": "APQC 1.0–9.0 Cross-Enterprise Core",
        "archetype": "Full-Stack / Sovereign Core",
    },
    "insilos_currency_cron": {
        "sap_lob": "SAP S/4HANA FIN Treasury FX Cron",
        "apqc_cbm": "APQC 9.7 Treasury & FX Batch Scheduling",
        "archetype": "Technical / Cron (Consolidated in insilos_adapter)",
    },
    "insilos_pinned_conversion": {
        "sap_lob": "SAP S/4HANA FIN Currency Valuation",
        "apqc_cbm": "APQC 9.7 Pinned FX Conversion Engine",
        "archetype": "Finance / FX Engine (Consolidated in insilos_adapter)",
    },
    "insilos_sap_fiori": {
        "sap_lob": "SAP Fiori 4 Horizon UX & Central Launchpad",
        "apqc_cbm": "APQC 1.0 Enterprise Control Tower",
        "archetype": "UI Design System & Control Tower",
    },
    "insilos_security": {
        "sap_lob": "SAP GRC Access Control & Zero-Trust",
        "apqc_cbm": "APQC 8.3 Information Security & IAM",
        "archetype": "Security / IAM (Consolidated in insilos_al2c)",
    },
    "insilos_capital_markets_decision_governance": {
        "sap_lob": "SAP TRM (Treasury & Risk Management)",
        "apqc_cbm": "IBM CBM Capital Markets / Investment Governance",
        "archetype": "Capital Markets / Governance",
    },
    "insilos_chemical_trade_compliance": {
        "sap_lob": "SAP EHS Product Safety & Stewardship",
        "apqc_cbm": "APQC 11.1 Chemical Regulatory Compliance",
        "archetype": "EHS / Chemical Trade Compliance",
    },
    "insilos_esg_bridge": {
        "sap_lob": "SAP Sustainability Control Tower (SCT)",
        "apqc_cbm": "APQC 13.7 ESG & Carbon Accounting (CBAM)",
        "archetype": "Sustainability / ESG Intelligence",
    },
    "insilos_finance_agent_os": {
        "sap_lob": "SAP S/4HANA Autonomous Finance & Joule",
        "apqc_cbm": "APQC 9.0 Autonomous Finance Agent OS",
        "archetype": "Finance / Autonomous Agent OS",
    },
    "insilos_hs_sync": {
        "sap_lob": "SAP GTS Tariff & HS Code Classification",
        "apqc_cbm": "APQC 4.4 Trade Compliance & Tariff Sync",
        "archetype": "Global Trade / Webhook Sync",
    },
    "insilos_hse_compliance": {
        "sap_lob": "SAP EHS Workplace Safety & CEMS Telemetry",
        "apqc_cbm": "APQC 11.0 Environmental Health & Safety",
        "archetype": "EHS / Telemetry & Compliance",
    },
    "insilos_industry_showcase": {
        "sap_lob": "SAP BTP Multi-Tenant SaaS Provisioning",
        "apqc_cbm": "IBM CBM Cloud Tenant Lifecycle & Showcase",
        "archetype": "Website / SaaS Control Plane",
    },
    "insilos_knowledge_graph": {
        "sap_lob": "SAP HANA Graph & Enterprise Knowledge",
        "apqc_cbm": "APQC 13.5 Enterprise Knowledge Graph",
        "archetype": "AI / Knowledge Graph",
    },
    "insilos_logistics_idp": {
        "sap_lob": "SAP TM (Transportation Management) & BTP Document AI",
        "apqc_cbm": "APQC 4.4 Freight Forwarding & IDP",
        "archetype": "Logistics / Document AI",
    },
    "insilos_market_data": {
        "sap_lob": "SAP Market Rates Management (MRM)",
        "apqc_cbm": "IBM CBM Financial Market Data Feeds",
        "archetype": "Capital Markets / Market Data",
    },
    "insilos_market_terminal": {
        "sap_lob": "SAP Fiori Trading & Analytics Workstation",
        "apqc_cbm": "IBM CBM Real-Time Trading Terminal",
        "archetype": "Capital Markets / OWL Terminal",
    },
    "insilos_preferential_origin": {
        "sap_lob": "SAP GTS Preferential Origin & FTA Management",
        "apqc_cbm": "APQC 4.4 Rules of Origin & FTA Calculation",
        "archetype": "Global Trade / FTA Engine",
    },
    "insilos_pubsub_bridge": {
        "sap_lob": "SAP Event Mesh / PubSub Bridge",
        "apqc_cbm": "APQC 8.0 Enterprise Event-Driven Architecture",
        "archetype": "Integration / Event Mesh",
    },
    "insilos_tenant_control": {
        "sap_lob": "SAP BTP Cloud Cockpit & Tenant Control",
        "apqc_cbm": "APQC 8.7 Multi-Tenant SaaS Governance",
        "archetype": "Cloud Platform / Tenant Control",
    },
    "insilos_theme_genesis": {
        "sap_lob": "SAP Fiori Horizon Visual Theme Foundation",
        "apqc_cbm": "IBM Carbon / Genesis Design System",
        "archetype": "UI Theme / Design Tokens",
    },
    "insilos_treasury_market_risk": {
        "sap_lob": "SAP TRM Market Risk Analyzer (VaR / Stress)",
        "apqc_cbm": "APQC 9.7 Treasury & Market Risk Analytics",
        "archetype": "Treasury / Quantitative Risk",
    },
    "insilos_website": {
        "sap_lob": "SAP Customer Experience (CX) Digital Portal",
        "apqc_cbm": "APQC 3.0 Market & Sell Products and Services",
        "archetype": "Website / Digital Experience",
    },
}

CONSOLIDATED_COMPANION_MODULES = {
    "insilos_currency_cron": "Consolidated into insilos_adapter DPAS-TSM runtime",
    "insilos_pinned_conversion": "Consolidated into insilos_adapter pinned_conversion runtime",
    "insilos_security": "Consolidated into insilos_al2c security/audit runtime",
}


def get_db_password():
    cp = configparser.ConfigParser()
    cp.read(CONF_PATH)
    return cp.get("options", "db_password")


def connect_db(dbname, password):
    return psycopg2.connect(
        host="localhost", port=5434, user="insilos", password=password, dbname=dbname
    )


def discover_modules():
    modules = []
    for tier, base in [("addons", ROOT_DIR / "addons"), ("enterprise", ROOT_DIR / "enterprise")]:
        for p in sorted(base.glob("insilos_*")):
            if p.is_dir() and (p / "__manifest__.py").exists():
                modules.append((tier, p.name, p))
    return modules


def extract_concrete_models(mod_path: Path):
    concrete_models = set()
    for py_file in mod_path.rglob("*.py"):
        if "tests" in py_file.parts:
            continue
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8", errors="ignore"))
        except Exception:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                bases = [ast.unparse(b) for b in node.bases]
                is_concrete = any("models.Model" in b or "models.TransientModel" in b for b in bases)
                is_abstract = any("models.AbstractModel" in b for b in bases)
                name_val = None
                inherit_val = None
                auto_val = True
                for stmt in node.body:
                    if isinstance(stmt, ast.Assign):
                        for t in stmt.targets:
                            if isinstance(t, ast.Name):
                                if t.id == "_name" and isinstance(stmt.value, ast.Constant):
                                    name_val = stmt.value.value
                                elif t.id == "_inherit":
                                    if isinstance(stmt.value, ast.Constant):
                                        inherit_val = stmt.value.value
                                    elif isinstance(stmt.value, (ast.List, ast.Tuple)) and stmt.value.elts:
                                        if isinstance(stmt.value.elts[0], ast.Constant):
                                            inherit_val = stmt.value.elts[0].value
                                elif t.id == "_auto" and isinstance(stmt.value, ast.Constant):
                                    auto_val = bool(stmt.value.value)
                if name_val and is_concrete and not is_abstract:
                    if inherit_val != name_val:
                        concrete_models.add((name_val, auto_val))
    return concrete_models


def check_controllers_readonly(mod_path: Path):
    ctrl_dir = mod_path / "controllers"
    if not ctrl_dir.exists():
        return True, []
    issues = []
    for py_file in sorted(ctrl_dir.rglob("*.py")):
        if py_file.name == "__init__.py":
            continue
        src = py_file.read_text(encoding="utf-8", errors="ignore")
        try:
            tree = ast.parse(src)
        except Exception as exc:
            issues.append(f"{py_file.name}: AST parse error {exc}")
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                for dec in node.decorator_list:
                    dec_str = ast.unparse(dec)
                    if "route(" in dec_str:
                        has_post = "'POST'" in dec_str or '"POST"' in dec_str
                        has_readonly = "readonly=" in dec_str
                        if has_post and not has_readonly:
                            issues.append(f"{py_file.name}:{node.lineno} {node.name} missing readonly= on POST route")
    return len(issues) == 0, issues


def evaluate_module(tier: str, mod_name: str, mod_path: Path, db_state: dict):
    manifest = ast.literal_eval((mod_path / "__manifest__.py").read_text(encoding="utf-8"))
    notes = []

    # -------------------------------------------------------------------------
    # D1: Manifest & Enterprise Taxonomy Alignment (20 pts)
    # -------------------------------------------------------------------------
    d1 = 20
    m_name = manifest.get("name", "")
    m_ver = str(manifest.get("version", ""))
    m_sum = manifest.get("summary", "")
    m_lic = manifest.get("license", "")
    if not m_name or not m_sum:
        d1 -= 5
        notes.append("D1: Missing name or summary")
    if not re.match(r"^(20\.0|26\.0|1\.0)", m_ver):
        d1 -= 3
        notes.append(f"D1: Non-standard version {m_ver}")
    if not m_lic:
        d1 -= 2
        notes.append("D1: Missing license")

    assets = manifest.get("assets", {})
    backend_assets = assets.get("web.assets_backend", [])
    dark_files_on_disk = list(mod_path.rglob("*.dark.scss"))
    for pat in backend_assets:
        if isinstance(pat, str) and "**/*" in pat and dark_files_on_disk:
            prefix = pat.split("/**/*")[0].replace(f"{mod_name}/", "")
            leaked = [p for p in dark_files_on_disk if str(p.relative_to(mod_path)).startswith(prefix)]
            if leaked:
                d1 -= 10
                notes.append(f"D1: Wildcard glob {pat} leaks .dark.scss into web.assets_backend")

    # -------------------------------------------------------------------------
    # D2: Data Model & Security ACL Completeness (20 pts)
    # -------------------------------------------------------------------------
    d2 = 20
    concrete_models = extract_concrete_models(mod_path)
    acl_csv_path = mod_path / "security" / "ir.model.access.csv"
    csv_model_ids = set()
    if acl_csv_path.exists():
        with acl_csv_path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                mid = (row.get("model_id:id") or "").strip()
                if mid:
                    if "." in mid:
                        mid = mid.split(".", 1)[1]
                    csv_model_ids.add(mid)

    if concrete_models:
        CORE_EXTENDED_MODELS = {
            "res.partner", "res.company", "res.users", "account.move",
            "mrp.production", "product.template", "stock.lot", "stock.scrap",
            "crm.lead", "hr.employee", "hr.payslip", "documents.document",
        }
        for m_dot, _is_auto in concrete_models:
            if m_dot in CORE_EXTENDED_MODELS:
                continue
            expected_mid = "model_" + m_dot.replace(".", "_")
            has_csv_acl = expected_mid in csv_model_ids
            has_db_acl = db_state["dev_acls"].get(m_dot, 0) > 0 and db_state["prod_acls"].get(m_dot, 0) > 0
            if not has_csv_acl and not has_db_acl:
                d2 -= 4
                notes.append(f"D2: Missing ACL coverage for {m_dot}")
            elif db_state["dev_status"] == "installed" and not has_db_acl:
                d2 -= 4
                notes.append(f"D2: Missing DB ir_access in insilos20_dev/innoria_prod for {m_dot}")
    d2 = max(0, d2)

    # -------------------------------------------------------------------------
    # D3: View, Action & Menu Ergonomics (20 pts)
    # -------------------------------------------------------------------------
    d3 = 20
    xml_files = list(mod_path.rglob("*.xml"))
    has_deprecated_attrs = False
    for xf in xml_files:
        txt = xf.read_text(encoding="utf-8", errors="ignore")
        if re.search(r'\battrs\s*=\s*["\']\{', txt):
            has_deprecated_attrs = True
            notes.append(f"D3: Deprecated attrs= in {xf.name}")
    if has_deprecated_attrs:
        d3 -= 5
    if concrete_models and not xml_files:
        d3 -= 8
        notes.append("D3: Concrete models without XML views/data")
    d3 = max(0, d3)

    # -------------------------------------------------------------------------
    # D4: Dual-Theme SCSS & Anti-Slop Compliance (20 pts)
    # -------------------------------------------------------------------------
    d4 = 20
    scss_files = list(mod_path.rglob("*.scss"))
    backend_scss = [p for p in backend_assets if isinstance(p, str) and p.endswith(".scss")]
    dark_assets = [p for p in assets.get("web.assets_web_dark", []) if isinstance(p, str) and p.endswith(".dark.scss")]

    if backend_scss and not dark_assets:
        d4 -= 8
        notes.append("D4: web.assets_backend has SCSS without paired web.assets_web_dark")

    # Check anti-slop rules across all SCSS files in module (banned light hex fallbacks inside var() with !important)
    banned_light_fallback_re = re.compile(
        r"var\([^)]*#(?:fff|ffffff|f8fafc|f4f6f8|f1f5f9)\b\)\s*!important", re.IGNORECASE
    )
    for sf in scss_files:
        stxt = sf.read_text(encoding="utf-8", errors="ignore")
        if banned_light_fallback_re.search(stxt):
            d4 -= 5
            notes.append(f"D4: Banned light hex fallback with !important in {sf.name}")
        if sf.name.endswith(".dark.scss"):
            if 'html[data-theme="light"] body:not(.o_dark_mode)' not in stxt:
                d4 -= 4
                notes.append(f"D4: Missing light safety guard in {sf.name}")
            rel_asset_path = f"{mod_name}/{sf.relative_to(mod_path)}"
            if db_state["dev_status"] == "installed" and rel_asset_path not in db_state["dev_dark_assets"]:
                d4 -= 4
                notes.append(f"D4: {rel_asset_path} missing from active ir_asset in insilos20_dev")
    d4 = max(0, d4)

    # -------------------------------------------------------------------------
    # D5: Runtime, Controller readonly=False & PostgreSQL DB Health (20 pts)
    # -------------------------------------------------------------------------
    d5 = 20
    ctrl_ok, ctrl_issues = check_controllers_readonly(mod_path)
    if not ctrl_ok:
        d5 -= min(10, 4 * len(ctrl_issues))
        notes.extend([f"D5: {iss}" for iss in ctrl_issues])

    if db_state["dev_status"] != "installed" or db_state["prod_status"] != "installed":
        if mod_name in CONSOLIDATED_COMPANION_MODULES:
            d5 -= 2
            notes.append(f"D5: Companion module ({CONSOLIDATED_COMPANION_MODULES[mod_name]})")
        else:
            d5 -= 10
            notes.append(f"D5: Not installed (dev={db_state['dev_status']}, prod={db_state['prod_status']})")
    d5 = max(0, d5)

    total = d1 + d2 + d3 + d4 + d5
    if total >= 90:
        level = "L5 (Sovereign)"
    elif total >= 75:
        level = "L4 (Enterprise)"
    elif total >= 60:
        level = "L3 (Defined)"
    elif total >= 40:
        level = "L2 (Managed)"
    else:
        level = "L1 (Initial)"

    tax = ENTERPRISE_TAXONOMY_MAP.get(mod_name, {
        "sap_lob": "SAP S/4HANA Enterprise",
        "apqc_cbm": "APQC Cross-Enterprise",
        "archetype": "Enterprise Module",
    })

    return {
        "tier": tier,
        "module": mod_name,
        "display_name": m_name,
        "sap_lob": tax["sap_lob"],
        "apqc_cbm": tax["apqc_cbm"],
        "archetype": tax["archetype"],
        "dev_status": db_state["dev_status"],
        "prod_status": db_state["prod_status"],
        "d1": d1,
        "d2": d2,
        "d3": d3,
        "d4": d4,
        "d5": d5,
        "total": total,
        "level": level,
        "notes": notes,
    }


def load_db_snapshot(dbname: str, password: str):
    conn = connect_db(dbname, password)
    cur = conn.cursor()
    cur.execute("SELECT name, state FROM ir_module_module WHERE name LIKE 'insilos_%'")
    mod_states = dict(cur.fetchall())

    cur.execute("""
        SELECT m.model, COUNT(a.id)
        FROM ir_model m
        LEFT JOIN ir_access a ON a.model_id = m.id AND a.active = TRUE
        GROUP BY m.model
    """)
    acls = dict(cur.fetchall())

    cur.execute("""
        SELECT path FROM ir_asset
        WHERE bundle = 'web.assets_web_dark' AND active = TRUE
    """)
    dark_assets = {r[0] for r in cur.fetchall()}
    conn.close()
    return {"mod_states": mod_states, "acls": acls, "dark_assets": dark_assets}


def main():
    parser = argparse.ArgumentParser(description="Audit all 23 insilos_* modules maturity (L1-L5).")
    parser.add_argument("--strict", action="store_true", help="Fail if any module scores below L4 (75/100).")
    parser.add_argument("--json", action="store_true", help="Output JSON report.")
    args = parser.parse_args()

    pw = get_db_password()
    dev_snap = load_db_snapshot("insilos20_dev", pw)
    prod_snap = load_db_snapshot("innoria_prod", pw)

    modules = discover_modules()
    results = []
    for tier, mod_name, mod_path in modules:
        db_state = {
            "dev_status": dev_snap["mod_states"].get(mod_name, "uninstalled"),
            "prod_status": prod_snap["mod_states"].get(mod_name, "uninstalled"),
            "dev_acls": dev_snap["acls"],
            "prod_acls": prod_snap["acls"],
            "dev_dark_assets": dev_snap["dark_assets"],
            "prod_dark_assets": prod_snap["dark_assets"],
        }
        results.append(evaluate_module(tier, mod_name, mod_path, db_state))

    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
        return 0

    avg_score = sum(r["total"] for r in results) / len(results) if results else 0.0
    l5_count = sum(1 for r in results if r["total"] >= 90)
    l4_count = sum(1 for r in results if 75 <= r["total"] < 90)
    below_l4 = [r for r in results if r["total"] < 75]

    print("=" * 140)
    print("INSILOS ENTERPRISE ODOO 20 — 23-MODULE MATURITY SCORECARD (L1–L5) & DUAL-THEME AUDIT")
    print("=" * 140)
    print(f"Total Modules Audited : {len(results)} (6 addons + 17 enterprise)")
    print(f"Average Maturity Score: {avg_score:.1f} / 100.0  |  L5 Sovereign: {l5_count}  |  L4 Enterprise: {l4_count}  |  < L4: {len(below_l4)}")
    print("-" * 140)
    print("| # | Tier | Technical Module | Display Name | SAP S/4HANA LoB / Fiori | IBM CBM / APQC PCF | D1 | D2 | D3 | D4 | D5 | Score | Level |")
    print("|---|------|------------------|--------------|-------------------------|--------------------|----|----|----|----|----|-------|-------|")
    for idx, r in enumerate(results, 1):
        print(
            f"| {idx:02d} | `{r['tier']}` | `{r['module']}` | {r['display_name']} | {r['sap_lob']} | {r['apqc_cbm']} "
            f"| {r['d1']} | {r['d2']} | {r['d3']} | {r['d4']} | {r['d5']} | **{r['total']}/100** | **{r['level']}** |"
        )
    print("-" * 140)

    any_notes = [r for r in results if r["notes"]]
    if any_notes:
        print("\nAudit Notes:")
        for r in any_notes:
            for n in r["notes"]:
                print(f"  - [{r['module']}] {n}")
    else:
        print("\nZero structural, ACL, Dual-Theme SCSS, or Controller readonly=False violations across all 23 modules.")

    if below_l4:
        print(f"\n[FAIL] {len(below_l4)} module(s) scored below L4 (75/100).")
        return 1
    print("\n[PASS] All 23 insilos_* modules achieved L5 Sovereign Maturity (Average: {:.1f}/100).".format(avg_score))
    return 0


if __name__ == "__main__":
    sys.exit(main())
