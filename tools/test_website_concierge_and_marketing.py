#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
End-to-End Verification Suite for Innoria AI Concierge Interactive Software Services,
Instant Pricing Configurator, Grounded RAG Service Cards, and AL2C Marketing Campaign Enrollment
across `insilos20_dev` and `innoria_prod`.
"""
import os
import sys

ROOT_DIR = "/home/zen/O20"
VENV_DIR = os.path.join(ROOT_DIR, ".venv")
VENV_PYTHON = os.path.join(VENV_DIR, "bin", "python3")
if os.path.exists(VENV_PYTHON) and os.path.abspath(sys.prefix) != os.path.abspath(VENV_DIR):
    os.execv(VENV_PYTHON, [VENV_PYTHON] + sys.argv)

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import odoo
from odoo.api import Environment
from odoo.modules.registry import Registry


def verify_database(dbname):
    print(f"[*] Initializing Odoo Registry & Environment for `{dbname}`...")
    registry = Registry(dbname)
    with registry.cursor() as cr:
        env = Environment(cr, odoo.SUPERUSER_ID, {})
        try:
            from odoo.addons.insilos_al2c.controllers.ai_concierge import InnoriaAiConciergeController

            controller = InnoriaAiConciergeController()
            controller.env = env

            # Ensure at least one active RAG chunk exists in the test transaction for grounding verification
            RagChunk = env["al2c.rag.chunk"].sudo()
            if RagChunk.search_count([("active", "=", True)]) == 0:
                RagChunk.create({
                    "name": "Innoria Software Engineering & Enterprise Suite Architecture",
                    "source_model": "knowledge.article",
                    "source_id": 1,
                    "source_ref": "knowledge.article,1",
                    "section_header": "Software Services & Four Pillars",
                    "chunk_seq": 0,
                    "content": (
                        "Innoria cung cấp Kỹ Nghệ Phần Mềm Đồng Phát Triển (Co-Engineering Squads) theo 7 công đoạn "
                        "Thông tư 13/2020/TT-BTTTT, Giải Pháp Phần Mềm Trọn Gói (Turnkey Custom Software) theo SAP Activate "
                        "5-Gate, Insilos ERP chuẩn kế toán VAS & HĐĐT Nghị định 70/2025/NĐ-CP, Vertical Resilience GRC "
                        "ISO 27001 & Nghị định 13/2023/NĐ-CP, Mojo AI Grounded RAG Swarm, và Zencode Ent Clean-Room."
                    ),
                    "chunk_hash": "a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90",
                    "token_count": 72,
                    "company_id": env.company.id,
                })

            # =========================================================================
            # 1. Verify /innoria/ai_concierge/services_catalog
            # =========================================================================
            cat_res = controller.ai_concierge_services_catalog(env=env)
            assert cat_res.get("status") == "ok" and cat_res.get("success") is True, (
                f"{dbname}: services_catalog failed: {cat_res}"
            )
            services = cat_res.get("services", [])
            expected_codes = ["sw_squad", "sw_turnkey", "erp", "grc", "ai", "zencode"]
            actual_codes = [s.get("code") for s in services]
            assert actual_codes == expected_codes, (
                f"{dbname}: Expected 6 service codes {expected_codes}, got {actual_codes}"
            )
            for s in services:
                assert s.get("short_title") and s.get("title") and s.get("badge"), (
                    f"{dbname}: Service {s.get('code')} missing title/badge metadata"
                )
                assert isinstance(s.get("lifecycle_steps"), list) and len(s["lifecycle_steps"]) >= 4, (
                    f"{dbname}: Service {s.get('code')} invalid lifecycle_steps: {s.get('lifecycle_steps')}"
                )
                assert isinstance(s.get("skus"), list) and len(s["skus"]) >= 1, (
                    f"{dbname}: Service {s.get('code')} missing SKUs"
                )
                assert isinstance(s.get("tiers"), dict) and set(s["tiers"].keys()) == {"starter", "growth", "enterprise"}, (
                    f"{dbname}: Service {s.get('code')} missing tier pricing"
                )

            squad_svc = services[0]
            assert len(squad_svc["lifecycle_steps"]) == 7, (
                f"{dbname}: sw_squad must have 7 Circular 13/2020 steps, got {len(squad_svc['lifecycle_steps'])}"
            )
            turnkey_svc = services[1]
            assert len(turnkey_svc["lifecycle_steps"]) == 5, (
                f"{dbname}: sw_turnkey must have 5 SAP Activate gates, got {len(turnkey_svc['lifecycle_steps'])}"
            )
            catalog_skus = cat_res.get("catalog_skus", [])
            assert len(catalog_skus) >= 10, (
                f"{dbname}: Expected >= 10 cross-referenced product.template SKUs, got {len(catalog_skus)}"
            )
            print(f"[✓] {dbname} [1/4]: /innoria/ai_concierge/services_catalog verified (6 services, {len(catalog_skus)} live SKUs)")

            # =========================================================================
            # 2. Verify /innoria/ai_concierge/estimate_service
            # =========================================================================
            # 2a. Co-Engineering Squad (sw_squad): 4 engineers, growth (50M/month), 6 months (5% discount) -> 1,140,000,000 VND
            est_squad = controller.ai_concierge_estimate_service(
                service_code="sw_squad",
                scale_tier="growth",
                units=4,
                duration_months=6,
                env=env,
            )
            assert est_squad.get("status") == "ok" and est_squad.get("success") is True
            assert est_squad["service_code"] == "sw_squad"
            assert est_squad["estimated_total_vnd"] == 1_140_000_000.0, (
                f"{dbname}: Expected 1,140,000,000 VND for 4 eng x 6m growth, got {est_squad['estimated_total_vnd']}"
            )
            assert est_squad["monthly_breakdown_vnd"] == 190_000_000.0
            assert "1.140.000.000 VNĐ" == est_squad["formatted_total_vnd"]
            assert any("13/2020/TT-BTTTT" in g for g in est_squad.get("compliance_guarantees", []))
            assert "SOP-DGM-08" in est_squad.get("payment_schedule", "")

            # 2b. Turnkey Custom Software (sw_turnkey): growth (480M base), 1 module, 4 months
            est_turnkey = controller.ai_concierge_estimate_service(
                service_code="sw_turnkey",
                scale_tier="growth",
                units=1,
                duration_months=4,
                env=env,
            )
            assert est_turnkey["service_code"] == "sw_turnkey"
            assert est_turnkey["estimated_total_vnd"] == 480_000_000.0
            assert est_turnkey["milestone_30_40_30"]["m1_amount"] == 144_000_000.0
            assert est_turnkey["milestone_30_40_30"]["m2_amount"] == 192_000_000.0
            assert est_turnkey["milestone_30_40_30"]["m3_amount"] == 144_000_000.0

            # 2c. Insilos Clean-Core ERP (erp): starter (150M base), 25 users, 12 months
            est_erp = controller.ai_concierge_estimate_service(
                service_code="erp",
                scale_tier="starter",
                units=25,
                duration_months=12,
                env=env,
            )
            assert est_erp["service_code"] == "erp"
            assert est_erp["estimated_total_vnd"] == 150_000_000.0
            assert "ERP-STARTER" in est_erp["recommended_skus"]
            print(f"[✓] {dbname} [2/4]: /innoria/ai_concierge/estimate_service verified (sw_squad={est_squad['formatted_total_vnd']}, sw_turnkey={est_turnkey['formatted_total_vnd']}, erp={est_erp['formatted_total_vnd']})")

            # =========================================================================
            # 3. Verify /innoria/ai_concierge/query across all 6 service lines
            # =========================================================================
            query_matrix = [
                (
                    "sw_squad",
                    "Tư vấn thuê đội kỹ sư phần mềm đồng phát triển Squad theo Thông tư 13/2020 và đối soát timesheet?",
                    "Thông tư 13/2020/TT-BTTTT",
                ),
                (
                    "sw_turnkey",
                    "Báo giá phát triển phần mềm trọn gói Turnkey chìa khóa trao tay bàn giao mã nguồn?",
                    "Turnkey",
                ),
                (
                    "erp",
                    "Doanh nghiệp chúng tôi muốn tìm hiểu về hệ thống ERP, chuẩn kế toán VAS và phương pháp triển khai SAP Activate.",
                    "Insilos ERP",
                ),
                (
                    "grc",
                    "Giải pháp của công ty có đáp ứng kiểm toán ISO 27001 và Nghị định 13/2023 về bảo vệ dữ liệu cá nhân không?",
                    "Vertical Resilience",
                ),
                (
                    "ai",
                    "Tư vấn giải pháp Mojo AI Agent Swarm, Grounded RAG và bóc tách chứng từ tự động?",
                    "Mojo AI",
                ),
                (
                    "zencode",
                    "Quy trình hiện đại hóa mã nguồn kế thừa bằng Zencode Ent và AGY Fleet?",
                    "Zencode Ent",
                ),
            ]
            for expected_pillar, q_text, expected_phrase in query_matrix:
                q_res = controller.ai_concierge_query(query=q_text, env=env)
                assert q_res.get("success") is True, f"{dbname}: Query failed for {expected_pillar}: {q_res}"
                assert q_res.get("grounded") is True, f"{dbname}: Query not grounded for {expected_pillar}"
                assert q_res.get("entailment_score", 0.0) >= 0.75, (
                    f"{dbname}: Entailment score < 0.75 for {expected_pillar}: {q_res.get('entailment_score')}"
                )
                assert q_res.get("matched_pillar") == expected_pillar, (
                    f"{dbname}: Expected matched_pillar={expected_pillar}, got {q_res.get('matched_pillar')}"
                )
                assert expected_phrase in q_res.get("answer", ""), (
                    f"{dbname}: Expected `{expected_phrase}` in answer for {expected_pillar}"
                )
                cards = q_res.get("service_cards", [])
                assert 1 <= len(cards) <= 3, (
                    f"{dbname}: Expected 1..3 service_cards for {expected_pillar}, got {len(cards)}"
                )
                assert cards[0]["code"] == expected_pillar, (
                    f"{dbname}: Primary service card mismatch: {cards[0]['code']} != {expected_pillar}"
                )
                actions = q_res.get("suggested_actions", [])
                action_types = {a.get("action") for a in actions}
                assert {"open_configurator", "open_lead", "prompt"}.issubset(action_types), (
                    f"{dbname}: Missing expected suggested_actions for {expected_pillar}: {actions}"
                )
            print(f"[✓] {dbname} [3/4]: /innoria/ai_concierge/query verified across all 6 service pillars with grounded citations, service_cards & suggested_actions")

            # =========================================================================
            # 4. Verify /innoria/ai_concierge/book_lead CRM Lead, Tags & Marketing Campaign
            # =========================================================================
            lead_res = controller.ai_concierge_book_lead(
                name="Lê Hoàng Nam",
                email="nam.le@fintech-vietnam.vn",
                phone="0909888777",
                company_name="Công ty Cổ phần Công nghệ Tài chính Việt Nam",
                product_interest="Kỹ Nghệ Phần Mềm Đồng Phát Triển (Co-Engineering Squads)",
                employee_count="200 - 500 nhân sự",
                notes="Cần thuê biệt đội 4 Senior Engineers phát triển Core Banking Microservices trong 6 tháng.",
                service_code="sw_squad",
                scale_tier="growth",
                units=4,
                duration_months=6,
                estimated_total_vnd=1_140_000_000.0,
                campaign_source="concierge_configurator_test",
                env=env,
            )
            assert lead_res.get("success") is True, f"{dbname}: book_lead failed: {lead_res}"
            assert lead_res.get("qualification_state") == "qualified"
            assert lead_res.get("fit_score", 0.0) >= 80.0
            assert lead_res.get("marketing_campaign_enrolled") is True, (
                f"{dbname}: Expected marketing_campaign_enrolled=True, got {lead_res}"
            )
            assert lead_res.get("campaign_name") == "Innoria Software Services — AL2C Concierge Automation"
            assert lead_res.get("service_code") == "sw_squad"
            assert lead_res.get("estimated_total_vnd") == 1_140_000_000.0

            lead_rec = env["crm.lead"].sudo().browse(lead_res["lead_id"])
            assert lead_rec.exists(), f"{dbname}: Created crm.lead does not exist"
            assert float(lead_rec.expected_revenue) == 1_140_000_000.0, (
                f"{dbname}: Expected expected_revenue=1,140,000,000.0, got {lead_rec.expected_revenue}"
            )
            tag_names = set(lead_rec.tag_ids.mapped("name"))
            expected_tags = {
                "Innoria Software Services",
                "AI Concierge Interactive",
                "Co-Engineering Squad (TT 13/2020)",
            }
            assert expected_tags.issubset(tag_names), (
                f"{dbname}: Missing expected CRM tags {expected_tags}, got {tag_names}"
            )
            assert "1.140.000.000 VNĐ" in (lead_rec.description or ""), (
                f"{dbname}: Missing formatted estimate in lead.description"
            )

            # Verify AB-PCT (Autonomous AI-Agent Capability Budget & Proof-Carrying Token)
            pct_tok = controller.mint_capability_token(env=env, budget=2, ttl=3600)
            assert pct_tok.startswith("pct."), f"{dbname}: Expected pct. prefix on minted token, got {pct_tok}"
            pct_lead_1 = controller.ai_concierge_book_lead(
                name="Trần Minh Quân",
                email="quan.tran@fintech-vietnam.vn",
                company_name="Công ty Cổ phần Công nghệ Tài chính Việt Nam",
                service_code="sw_turnkey",
                scale_tier="growth",
                pct_token=pct_tok,
                env=env,
            )
            assert pct_lead_1.get("success") is True and pct_lead_1.get("capability_budget_remaining") == 1, (
                f"{dbname}: Expected capability_budget_remaining=1 on 1st PCT use, got {pct_lead_1}"
            )
            pct_lead_2 = controller.ai_concierge_book_lead(
                name="Trần Minh Quân",
                email="quan.tran@fintech-vietnam.vn",
                company_name="Công ty Cổ phần Công nghệ Tài chính Việt Nam",
                service_code="sw_turnkey",
                scale_tier="growth",
                pct_token=pct_tok,
                env=env,
            )
            assert pct_lead_2.get("success") is True and pct_lead_2.get("capability_budget_remaining") == 0, (
                f"{dbname}: Expected capability_budget_remaining=0 on 2nd PCT use, got {pct_lead_2}"
            )
            pct_lead_exhausted = controller.ai_concierge_book_lead(
                name="Trần Minh Quân",
                email="quan.tran@fintech-vietnam.vn",
                company_name="Công ty Cổ phần Công nghệ Tài chính Việt Nam",
                service_code="sw_turnkey",
                scale_tier="growth",
                pct_token=pct_tok,
                env=env,
            )
            assert pct_lead_exhausted.get("success") is False and pct_lead_exhausted.get("status") == "pct_capability_budget_exhausted", (
                f"{dbname}: Expected pct_capability_budget_exhausted on 3rd use, got {pct_lead_exhausted}"
            )
            tampered_tok = pct_tok[:-4] + ("0000" if not pct_tok.endswith("0000") else "ffff")
            pct_lead_tampered = controller.ai_concierge_book_lead(
                name="Trần Minh Quân",
                email="quan.tran@fintech-vietnam.vn",
                company_name="Công ty Cổ phần Công nghệ Tài chính Việt Nam",
                pct_token=tampered_tok,
                env=env,
            )
            assert pct_lead_tampered.get("success") is False and pct_lead_tampered.get("status") == "invalid_pct_signature", (
                f"{dbname}: Expected invalid_pct_signature on tampered token, got {pct_lead_tampered}"
            )

            print(f"[✓] {dbname} [4/4]: /innoria/ai_concierge/book_lead + AB-PCT capability guard verified (lead_id={lead_rec.id}, expected_revenue={lead_rec.expected_revenue:,.0f} VND, tags={sorted(tag_names)}, marketing_campaign_enrolled=True)")
        finally:
            # Rollback cursor so test records do not pollute dev or prod databases
            cr.rollback()


def main():
    odoo.tools.config.parse_config(["-c", "/home/zen/O20/odoo.conf"])
    for dbname in ("insilos20_dev", "innoria_prod"):
        verify_database(dbname)
    print("[🎉] ALL INNORIA AI CONCIERGE SERVICE CATALOG, PRICING CONFIGURATOR, GROUNDED QUERY & MARKETING CAMPAIGN CHECKS PASSED (EXIT 0)")


if __name__ == "__main__":
    main()
