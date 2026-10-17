#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
End-to-End Verification Suite for SOP-DGM-13:
Autonomous Marketing Automation, Continuous B2B Market Research,
Competitor Intelligence Battlecards & GEO Content Supply Chain (`Innoria.com` & Digimate JSC — MST: 0317958465).
"""
import os
import site
import sys
import types

PYENV_PYTHON = "/home/zen/.pyenv/versions/3.12.13/bin/python3"
if os.path.exists(PYENV_PYTHON) and os.path.realpath(sys.executable) != os.path.realpath(PYENV_PYTHON):
    os.execv(PYENV_PYTHON, [PYENV_PYTHON] + sys.argv)

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VENV_SITE = os.path.join(ROOT_DIR, ".venv/lib/python3.12/site-packages")
if os.path.isdir(VENV_SITE):
    site.addsitedir(VENV_SITE)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
try:
    import xmlsec  # noqa: F401
except Exception:
    sys.modules["xmlsec"] = types.ModuleType("xmlsec")

try:
    from insilos_adapter.hook import install as install_insilos_hook
    install_insilos_hook()
except Exception:
    pass

import odoo
from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry

_local_conf = os.path.join(ROOT_DIR, "odoo.conf")
if os.path.isdir("/var/lib/insilos/filestore"):
    _extra = [
        p
        for p in (
            "/var/lib/insilos/filestore/custom_addons",
            f"{ROOT_DIR}/odoo/addons",
            f"{ROOT_DIR}/addons",
            f"{ROOT_DIR}/enterprise",
        )
        if os.path.isdir(p)
    ]
    odoo.tools.config.parse_config(
        [
            f"--addons-path={','.join(_extra)}",
            "--data-dir=/var/lib/insilos/filestore",
            f"--db_host={os.environ.get('DB_HOST', 'pgbouncer-service')}",
            f"--db_port={os.environ.get('DB_PORT', '6432')}",
            f"--db_user={os.environ.get('DB_USER', 'insilos')}",
            f"--db_password={os.environ.get('PGPASSWORD', '')}",
        ]
    )
elif os.path.exists(_local_conf):
    odoo.tools.config.parse_config(["-c", _local_conf])
else:
    odoo.tools.config.parse_config([])


def verify_database(dbname):
    print(f"\n=== Verifying SOP-DGM-13 Autonomous Marketing & Market Research Radar in `{dbname}` ===")
    reg = Registry.new(dbname)
    with reg.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        Radar = env["dgm.market.research.radar"].sudo()
        Campaign = env["dgm.marketing.automation.campaign"].sudo()
        Workflow = env["dgm.knowledge.sop.workflow"].sudo()
        RagChunk = env["al2c.rag.chunk"].sudo()
        RagService = env["al2c.rag.service"].sudo()
        Document = env["documents.document"].sudo()

        # Gate 1: Verify 6 Market Research Radars (`MKT-RES-01` .. `MKT-RES-06`)
        radars = Radar.search([("active", "=", True)], order="code asc")
        radar_codes = set(radars.mapped("code"))
        expected_radars = {f"MKT-RES-{i:02d}" for i in range(1, 7)}
        assert expected_radars.issubset(radar_codes), f"[{dbname}] Missing radars: {expected_radars - radar_codes}"
        total_tam = sum(radars.mapped("tam_vnd_billion"))
        total_som = sum(radars.mapped("som_target_vnd_billion"))
        assert total_tam >= 80000.0, f"[{dbname}] Expected total TAM >= 80,000B VND, got {total_tam}"
        assert total_som >= 900.0, f"[{dbname}] Expected total SOM >= 900B VND, got {total_som}"
        for r in radars:
            assert r.grounding_verified is True, f"[{dbname}] Radar {r.code} must have 100% verified Claim Atoms"
            assert r.claim_count >= 1, f"[{dbname}] Radar {r.code} has 0 claim atoms"
            assert r.content_sha256 and len(r.content_sha256) == 64, f"[{dbname}] Radar {r.code} invalid SHA-256"
            assert r.rag_chunk_id and r.rag_chunk_id.active, f"[{dbname}] Radar {r.code} missing active RAG chunk"
            assert r.state in ("verified_grounded", "published_campaign"), f"[{dbname}] Unexpected radar state {r.state}"
        print(f"  [PASS] Gate 1: 6 Market Research Radars (`MKT-RES-01..06`, TAM={total_tam}B, SOM={total_som}B) verified.")

        # Gate 2: Verify 6 Autonomous Marketing Campaigns (`AUT-CMP-01` .. `AUT-CMP-06`)
        campaigns = Campaign.search([("active", "=", True)], order="code asc")
        camp_codes = set(campaigns.mapped("code"))
        expected_camps = {f"AUT-CMP-{i:02d}" for i in range(1, 7)}
        assert expected_camps.issubset(camp_codes), f"[{dbname}] Missing campaigns: {expected_camps - camp_codes}"
        for c in campaigns:
            assert c.state == "running_autonomous", f"[{dbname}] Campaign {c.code} not in running_autonomous: {c.state}"
            assert c.autonomy_mode == "autonomous_on", f"[{dbname}] Campaign {c.code} autonomy_mode != autonomous_on"
            assert c.claim_grounding_rate == 100.0, f"[{dbname}] Campaign {c.code} grounding rate != 100%"
            assert c.actual_mql_count > 0 and c.actual_sql_count > 0, f"[{dbname}] Campaign {c.code} zero MQL/SQL"
            assert c.conversion_rate_pct > 0.0, f"[{dbname}] Campaign {c.code} zero conversion rate"
            assert c.pipeline_revenue_vnd > 0.0 and c.roi_multiple > 1.0, f"[{dbname}] Campaign {c.code} invalid ROI"
            assert c.marketing_kit_id and c.marketing_kit_id.grounding_verified, (
                f"[{dbname}] Campaign {c.code} missing grounded al2c.marketing.kit"
            )
            assert c.native_campaign_id and c.native_campaign_id.state == "running", (
                f"[{dbname}] Campaign {c.code} missing running marketing.campaign"
            )
        print("  [PASS] Gate 2: 6 Autonomous Campaigns (`AUT-CMP-01..06`) linked to `al2c.marketing.kit` & `marketing.campaign`.")

        # Gate 3: Verify Autonomous Cron Execution & Kill-Switch Governance (in savepoint)
        with cr.savepoint():
            res_live = Campaign.cron_dgm_autonomous_marketing_and_research()
            assert res_live.get("status") == "ok", f"[{dbname}] Cron failed: {res_live}"
            assert res_live.get("radars_scanned") >= 6
            assert res_live.get("campaigns_executed") >= 6
            assert res_live.get("total_pipeline_vnd", 0.0) > 0.0

            env["ir.config_parameter"].sudo().set_param("dgm.autonomy_enabled", "False")
            res_paused = Campaign.cron_dgm_autonomous_marketing_and_research()
            assert res_paused.get("status") == "paused_by_kill_switch", (
                f"[{dbname}] Cron must respect dgm.autonomy_enabled kill-switch: {res_paused}"
            )
        print("  [PASS] Gate 3: Autonomous Marketing Cron (`ir_cron_dgm_autonomous_marketing_research`) & Kill-Switch verified.")

        # Gate 4: Verify KMS-SOP-13 & Battlecard Retrieval via SOP-RAG Copilot
        wf_13 = Workflow.search([("code", "=", "KMS-SOP-13"), ("active", "=", True)], limit=1)
        assert wf_13 and wf_13.lifecycle_stage == "indexed_rag", f"[{dbname}] KMS-SOP-13 not indexed_rag"
        chunk_13 = RagChunk.search([("sop_code", "=", "SOP-DGM-13"), ("active", "=", True)], limit=1)
        assert chunk_13, f"[{dbname}] Missing SOP-DGM-13 RAG chunk"

        with cr.savepoint():
            ceo = env["hr.employee"].sudo().search([("registration_number", "=", "DGM-001")], limit=1)
            rag_ans = RagService.query_sop_rag_copilot(
                query_text="Quy trình tự động hóa Marketing 4-Touch ABM, nghiên cứu thị trường TAM/SAM/SOM và Battlecard đối thủ theo SOP-DGM-13?",
                channel_mode="internal_sop_copilot",
                employee_id=ceo.id if ceo else False,
            )
            assert rag_ans["ok"] is True and rag_ans["is_grounded"] is True
            assert rag_ans["entailment_score"] >= 0.85
            assert any(
                code in rag_ans["matched_sop_codes"]
                for code in ("SOP-DGM-13", "MKT-RES-01", "MKT-RES-02", "MKT-RES-03")
            ), f"[{dbname}] Expected SOP-DGM-13 or MKT-RES in matched codes: {rag_ans['matched_sop_codes']}"
        print("  [PASS] Gate 4: `KMS-SOP-13` & `MKT-RES-01..06` Battlecards retrievable via Grounded SOP-RAG Copilot.")

        # Gate 5: Verify Branded HTML Documents (`SOP-DGM-13` & `TPL-MKT-01`), Knowledge Article & 0 Empty Folders
        for doc_fname in (
            "SOP-DGM-13_Quy_Trinh_Tu_Dong_Hoa_Marketing_Nghien_Cuu_Thi_Truong_B2B_Va_GEO_Innoria.html",
            "TPL-MKT-01_Bao_Cao_Nghien_Cuu_Thi_Truong_Battlecard_Doi_Thu_Va_Kich_Ban_4_Touch_ABM.html",
        ):
            docs = Document.search([("type", "!=", "folder"), ("active", "=", True), ("name", "=", doc_fname)])
            assert docs, f"[{dbname}] Missing branded HTML document {doc_fname}"
            for d in docs:
                assert d.file_size and d.file_size > 1500, f"[{dbname}] Document {doc_fname} too small: {d.file_size}"
                assert d.owner_id.id is False, f"[{dbname}] Document {doc_fname} must have owner_id=False"
                assert d.access_internal in ("edit", "view")
                raw_html = (d.attachment_id.raw or b"").decode("utf-8", errors="ignore")
                assert "data:image/png;base64," in raw_html, f"[{dbname}] {doc_fname} missing Drive Logo base64"
                assert "0317958465" in raw_html, f"[{dbname}] {doc_fname} missing MST 0317958465"

        kb_13 = env["knowledge.article"].sudo().search([("name", "ilike", "SOP-DGM-13%"), ("active", "=", True)], limit=1)
        assert kb_13, f"[{dbname}] Missing SOP-DGM-13 knowledge.article"
        assert "data:image/png;base64," in str(kb_13.body or "")

        cr.execute(
            """
            SELECT f.id, f.name
              FROM documents_document f
             WHERE f.type = 'folder'
               AND f.active = TRUE
               AND NOT EXISTS (
                   SELECT 1 FROM documents_document c
                    WHERE c.folder_id = f.id AND c.active = TRUE
               )
            """
        )
        empty_folders = cr.fetchall()
        assert len(empty_folders) == 0, f"[{dbname}] Found empty active folders: {empty_folders}"
        print("  [PASS] Gate 5: Branded HTML Documents (`SOP-DGM-13`, `TPL-MKT-01`), Knowledge Article & 0 Empty Folders verified.")


def verify_employee_dashboard_wiring():
    ctrl_path = os.path.join(ROOT_DIR, "enterprise/web_enterprise/controllers/employee_dashboard.py")
    js_path = os.path.join(ROOT_DIR, "enterprise/web_enterprise/static/src/webclient/home_menu/home_menu.js")
    xml_path = os.path.join(ROOT_DIR, "enterprise/web_enterprise/static/src/webclient/home_menu/home_menu.xml")

    with open(ctrl_path, "r", encoding="utf-8") as f:
        ctrl_src = f.read()
    assert "_get_autonomous_marketing_hub" in ctrl_src
    assert "/insilos/employee_dashboard/run_autonomous_marketing_scan" in ctrl_src
    assert '"autonomous_marketing_hub": autonomous_marketing_hub' in ctrl_src

    with open(js_path, "r", encoding="utf-8") as f:
        js_src = f.read()
    assert "onRunAutonomousMarketingScan" in js_src
    assert "openMarketResearchRadarApp" in js_src
    assert "openAutonomousMarketingCampaignApp" in js_src

    with open(xml_path, "r", encoding="utf-8") as f:
        xml_src = f.read()
    assert "SOP-DGM-13" in xml_src
    assert "onRunAutonomousMarketingScan" in xml_src
    assert "mktHub.radars" in xml_src
    assert "mktHub.campaigns" in xml_src
    print("  [PASS] Gate 6: Employee Dashboard Controller & OWL HomeMenu (`Section 6 — SOP-DGM-13`) wired.")


def main():
    targets = sys.argv[1:] if len(sys.argv) > 1 else ["insilos20_dev", "innoria_prod"]
    for db in targets:
        verify_database(db)
    if os.path.exists(os.path.join(ROOT_DIR, "enterprise/web_enterprise/controllers/employee_dashboard.py")):
        verify_employee_dashboard_wiring()
    print("\n=== ALL 6 SOP-DGM-13 AUTONOMOUS MARKETING & MARKET RESEARCH RADAR GATES PASSED (EXIT 0) ===")


if __name__ == "__main__":
    main()
