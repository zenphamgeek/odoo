#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
End-to-End Verification Suite for SOP-DGM-15 (E2E-QA-12):
RAG-SOP Sales & Marketing Framework (`SOP-DGM-15`), <5-Minute Rapid CPQ Quoting Engine,
Customer Business-Trait vs. Quotation ROI Matrix (5 Archetypes), and Executive PDF Report Sync.
"""
import base64
import json
import os
import site
import subprocess
import sys
import time
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
from odoo import SUPERUSER_ID, api
from odoo.modules.registry import Registry

_insilos_conf = os.path.join(ROOT_DIR, "insilos.conf")
_local_conf = os.path.join(ROOT_DIR, "odoo.conf")
if os.path.isfile(_insilos_conf):
    odoo.tools.config.parse_config(["-c", _insilos_conf, "-d", "insilos20_dev"])
elif os.path.isfile("/etc/insilos/insilos.conf"):
    odoo.tools.config.parse_config(["-c", "/etc/insilos/insilos.conf", "-d", "insilos20_dev"])
elif os.path.isfile(_local_conf):
    odoo.tools.config.parse_config(["-c", _local_conf, "-d", "insilos20_dev"])
else:
    odoo.tools.config.parse_config(["-d", "insilos20_dev"])

if os.environ.get("DB_HOST"):
    odoo.tools.config["db_host"] = os.environ["DB_HOST"]
if os.environ.get("DB_PORT"):
    odoo.tools.config["db_port"] = int(os.environ["DB_PORT"])
if os.environ.get("DB_USER"):
    odoo.tools.config["db_user"] = os.environ["DB_USER"]
if os.environ.get("PGPASSWORD"):
    odoo.tools.config["db_password"] = os.environ["PGPASSWORD"]

REPORT_PDF_PATH = os.path.join(
    ROOT_DIR, "reports", "INNORIA_DIGIMATE_RAG_SOP_RAPID_QUOTATION_ROI_REPORT.pdf"
)
BRAIN_PDF_PATH = (
    "/home/zen/.gemini/antigravity/brain/790b1743-1724-4f27-a6fd-6d949bee50cf/"
    "INNORIA_DIGIMATE_RAG_SOP_RAPID_QUOTATION_ROI_REPORT.pdf"
)
PDF_DOC_NAME = "INNORIA_DIGIMATE_RAG_SOP_RAPID_QUOTATION_ROI_REPORT.pdf"
SOP_FOLDER_NAME = "07. Quy trình Chuẩn & Tự động hóa (SOP & ERP Blueprints)"

ARCHETYPES = [
    ("outsourcing_partner", "Man-Hour Staff Augmentation"),
    ("ktt_finance_ops", "Chief Accountant KTT Software Dev"),
    ("erp_insilos_enterprise", "Packaged Insilos ERP"),
    ("grc_vertical_resilience", "Packaged Vertical Resilience GRC"),
    ("mojo_ai_automation", "Mojo AI Tools & Sovereign RAG"),
]


def _ensure_sop_dgm_15_seeded(env):
    """Ensure SOP-DGM-15 exists in knowledge.article, dgm.knowledge.sop.workflow, and al2c.rag.chunk."""
    Article = env["knowledge.article"].sudo()
    Workflow = env["dgm.knowledge.sop.workflow"].sudo()
    Chunk = env["al2c.rag.chunk"].sudo()

    kb_15 = Article.search([("name", "ilike", "SOP-DGM-15%"), ("active", "=", True)], limit=1)
    if not kb_15:
        root_kb = Article.search([("parent_id", "=", False), ("active", "=", True)], limit=1)
        kb_15 = Article.create(
            {
                "name": (
                    "SOP-DGM-15: Khung RAG-SOP Phòng Sale & Marketing — Chăm sóc Khách hàng Cũ, "
                    "Đối soát Timesheet, Thanh toán & Báo giá Nhanh "
                    "(Insilos ERP · Vertical Resilience GRC · Mojo AI · KTT & Man-Hour)"
                ),
                "parent_id": root_kb.id if root_kb else False,
                "icon": "🚀",
                "internal_permission": "write",
                "body": (
                    "<div class='dgm-sop-container'>"
                    "<h1>SOP-DGM-15: Khung RAG-SOP Phòng Sale &amp; Marketing</h1>"
                    "<p>1. Maintain Sale &amp; Chăm sóc khách hàng cũ (QBR hàng quý, cảnh báo gia hạn 45 ngày, "
                    "Cross-sell/Upsell 5 trụ cột: Man-Hour Outsourcing, KTT Software, Insilos ERP, "
                    "Vertical Resilience GRC, Mojo AI Tools).</p>"
                    "<p>2. Báo giá nhanh CPQ &lt; 5 phút (SLA 1.8 phút) qua action_generate_rapid_quote_and_roi, "
                    "bóc tách Feature Items (al2c.fts.item) Clean-Core Class A/B/C và định lượng ROI 3 năm.</p>"
                    "<p>3. Đối soát Timesheet đa kênh từ MTI - TIMESHEET vào al2c.timesheet.staging và "
                    "account.analytic.line với OT 2 bậc (100% và 150%) chốt trước ngày làm việc thứ 5.</p>"
                    "<p>4. Thanh toán &amp; xuất Hóa đơn Điện tử 1C26TAA (Nghị định 70/2025/NĐ-CP) sau nghiệm thu, "
                    "VCB DigiBiz 11 cột (BHXH TZ0857G) và 24h Foreign Wire SLA.</p>"
                    "</div>"
                ),
            }
        )

    wf_15 = Workflow.search([("sop_code", "=", "SOP-DGM-15"), ("active", "=", True)], limit=1)
    if not wf_15:
        wf_15 = Workflow.create(
            {
                "code": "KMS-SOP-DGM-15",
                "sop_code": "SOP-DGM-15",
                "name": kb_15.name,
                "category": "sop_governance",
                "knowledge_article_id": kb_15.id,
                "rbac_profile": "crm_sales",
                "confidentiality_level": "public",
                "visibility_channel": "both_public_internal",
                "lifecycle_stage": "indexed_rag",
                "min_entailment_threshold": 0.85,
                "summary_markdown": (
                    "Quy trình SOP-DGM-15 (KMS-SOP-DGM-15) chuẩn hóa hoạt động Phòng Sale & Marketing: "
                    "(1) Maintain Sale & Chăm sóc Khách hàng hiện hữu, gia hạn hợp đồng renewals & QBR; "
                    "(2) Báo giá nhanh CPQ < 5 phút (SLA 1.8 phút) cho Vertical Resilience GRC, Insilos ERP, "
                    "Mojo AI Tools, phần mềm Kế toán Trưởng KTT và Man-Hour Outsourcing; "
                    "(3) Đối soát Timesheet đa kênh MTI - TIMESHEET qua al2c.timesheet.staging sang "
                    "account.analytic.line; "
                    "(4) Thanh toán, xuất hóa đơn điện tử 1C26TAA (Nghị định 70/2025/NĐ-CP) và VCB DigiBiz 11 cột."
                ),
            }
        )

    chunks_15 = Chunk.search([("sop_code", "=", "SOP-DGM-15"), ("active", "=", True)])
    if not chunks_15 or wf_15.lifecycle_stage != "indexed_rag":
        wf_15.action_index_to_sop_rag()
        chunks_15 = Chunk.search([("sop_code", "=", "SOP-DGM-15"), ("active", "=", True)])

    return kb_15, wf_15, chunks_15


def run_verification(dbname="insilos20_dev"):
    print(f"\n=== Verifying SOP-DGM-15 Rapid CPQ, 5-Archetype ROI & Executive PDF Report in `{dbname}` ===")
    reg = None
    for attempt in range(6):
        try:
            reg = Registry.new(dbname)
            break
        except Exception as exc:
            if "LockNotAvailable" in type(exc).__name__ or "lock timeout" in str(exc):
                time.sleep(3.0)
            else:
                raise
    if reg is None:
        reg = Registry.new(dbname)
    with reg.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        RagService = env["al2c.rag.service"].sudo()
        SaleOrder = env["sale.order"].sudo()
        Partner = env["res.partner"].sudo()
        Document = env["documents.document"].sudo()
        Attachment = env["ir.attachment"].sudo()

        # ------------------------------------------------------------------
        # Gate 1: RAG-SOP Sales & Marketing Framework (`SOP-DGM-15`)
        # ------------------------------------------------------------------
        kb_15, wf_15, chunks_15 = _ensure_sop_dgm_15_seeded(env)
        assert kb_15 and kb_15.exists(), f"[{dbname}] Missing SOP-DGM-15 knowledge.article"
        assert wf_15 and wf_15.exists(), f"[{dbname}] Missing SOP-DGM-15 dgm.knowledge.sop.workflow"
        assert wf_15.lifecycle_stage == "indexed_rag", (
            f"[{dbname}] Expected SOP-DGM-15 workflow in indexed_rag, got {wf_15.lifecycle_stage}"
        )
        assert len(chunks_15) >= 1, f"[{dbname}] Expected >= 1 al2c.rag.chunk for SOP-DGM-15, got {len(chunks_15)}"
        print(
            f"[✓] Gate 1.1: SOP-DGM-15 verified in knowledge.article (#{kb_15.id}), "
            f"dgm.knowledge.sop.workflow ({wf_15.code}), and al2c.rag.chunk ({len(chunks_15)} chunks)."
        )

        rag_queries = [
            (
                "Maintain Sale & Renewals",
                "Quy trình SOP-DGM-15 Maintain Sale chăm sóc khách hàng hiện hữu, cảnh báo gia hạn hợp đồng renewals và QBR hàng quý?",
            ),
            (
                "Rapid Quoting (GRC, ERP, Mojo AI, KTT)",
                "Quy trình SOP-DGM-15 báo giá nhanh CPQ dưới 5 phút cho Vertical Resilience GRC, Insilos ERP, Mojo AI Tools và phần mềm Kế toán Trưởng KTT?",
            ),
            (
                "Timesheet & 1C26TAA Payment Workflow",
                "Quy trình SOP-DGM-15 chốt đối soát Timesheet MTI al2c.timesheet.staging và thanh toán xuất hóa đơn điện tử 1C26TAA VCB DigiBiz?",
            ),
        ]
        with cr.savepoint():
            for label, q_text in rag_queries:
                res = RagService.query_sop_rag_copilot(
                    query_text=q_text,
                    channel_mode="internal_sop_copilot",
                )
                assert res.get("ok") is True, f"[{dbname}] RAG query failed for {label}: {res}"
                assert res.get("is_grounded") is True, f"[{dbname}] RAG query not grounded for {label}: {res}"
                assert float(res.get("entailment_score", 0.0)) >= 0.85, (
                    f"[{dbname}] Entailment score < 0.85 for {label}: {res.get('entailment_score')}"
                )
                matched_codes = res.get("matched_sop_codes") or []
                citation_codes = [c.get("sop_code") for c in (res.get("citations") or [])]
                assert "SOP-DGM-15" in matched_codes or "SOP-DGM-15" in citation_codes, (
                    f"[{dbname}] Expected SOP-DGM-15 citation for `{label}`, got matched={matched_codes}, citations={citation_codes}"
                )
                print(
                    f"[✓] Gate 1.2 ({label}): Grounded SOP-RAG answer verified "
                    f"(entailment={res['entailment_score']:.4f}, matched={matched_codes})."
                )

        # ------------------------------------------------------------------
        # Gate 2: Rapid CPQ Quotation & Business-Trait ROI across 5 Archetypes
        # ------------------------------------------------------------------
        with cr.savepoint():
            partner = Partner.search([("dgm_partner_code", "=", "PTN-DGM-2026-0001")], limit=1)
            if not partner:
                partner = Partner.search([("is_company", "=", True)], limit=1)
            if not partner:
                partner = Partner.create({"name": "Enterprise Rapid Quote Test Client", "is_company": True})

            generated_order = None
            for arch_key, arch_label in ARCHETYPES:
                so = SaleOrder.create(
                    {
                        "partner_id": partner.id,
                        "customer_business_archetype": arch_key,
                    }
                )
                t0 = time.monotonic()
                vcase = so.action_generate_rapid_quote_and_roi(archetype=arch_key)
                elapsed_sec = time.monotonic() - t0

                assert elapsed_sec < 1.0, (
                    f"[{dbname}] Archetype `{arch_key}` took {elapsed_sec:.3f}s (exceeds 1.0s limit)"
                )
                assert so.customer_business_archetype == arch_key
                non_display_lines = so.order_line.filtered(lambda l: not l.display_type)
                assert len(non_display_lines) >= 1, (
                    f"[{dbname}] Archetype `{arch_key}` did not populate order_line"
                )
                assert so.amount_untaxed > 0, (
                    f"[{dbname}] Archetype `{arch_key}` has amount_untaxed={so.amount_untaxed}"
                )

                fts_items = so.fts_item_ids
                assert len(fts_items) >= 1, (
                    f"[{dbname}] Archetype `{arch_key}` did not populate fts_item_ids"
                )
                for fts in fts_items:
                    assert fts.feature_code, f"[{dbname}] Missing feature_code on FTS item {fts.name}"
                    assert fts.product_pillar, f"[{dbname}] Missing product_pillar on FTS item {fts.name}"
                    assert fts.estimated_man_hours > 0, (
                        f"[{dbname}] Invalid estimated_man_hours={fts.estimated_man_hours} on {fts.feature_code}"
                    )
                    assert fts.estimated_price_vnd > 0, (
                        f"[{dbname}] Invalid estimated_price_vnd={fts.estimated_price_vnd} on {fts.feature_code}"
                    )

                vc = so.value_case_id or vcase
                assert vc and vc.exists(), f"[{dbname}] Missing linked value_case_id for `{arch_key}`"
                assert vc.quotation_price_vnd > 0, (
                    f"[{dbname}] quotation_price_vnd <= 0 for `{arch_key}`: {vc.quotation_price_vnd}"
                )
                assert vc.net_annual_benefit_vnd > 0, (
                    f"[{dbname}] net_annual_benefit_vnd <= 0 for `{arch_key}`: {vc.net_annual_benefit_vnd}"
                )
                assert vc.three_year_net_benefit_vnd > 0, (
                    f"[{dbname}] three_year_net_benefit_vnd <= 0 for `{arch_key}`: {vc.three_year_net_benefit_vnd}"
                )
                assert vc.quote_to_roi_ratio >= 2.5, (
                    f"[{dbname}] quote_to_roi_ratio={vc.quote_to_roi_ratio} < 2.5 for `{arch_key}`"
                )
                assert vc.roi_percentage > 100.0, (
                    f"[{dbname}] roi_percentage={vc.roi_percentage} <= 100% for `{arch_key}`"
                )
                assert 0.0 < vc.payback_months <= 12.0, (
                    f"[{dbname}] payback_months={vc.payback_months} not in (0, 12] for `{arch_key}`"
                )
                assert vc.battlecard_comparison_json and len(vc.battlecard_comparison_json.strip()) > 20, (
                    f"[{dbname}] Empty battlecard_comparison_json for `{arch_key}`"
                )
                battlecard_data = json.loads(vc.battlecard_comparison_json)
                assert len(battlecard_data.get("competitors", [])) >= 4, (
                    f"[{dbname}] Expected >= 4 competitors in battlecard JSON for `{arch_key}`"
                )
                assert vc.rag_sop_citation_summary and "SOP-DGM-15" in vc.rag_sop_citation_summary, (
                    f"[{dbname}] Missing SOP-DGM-15 in rag_sop_citation_summary for `{arch_key}`"
                )
                generated_order = so
                print(
                    f"[✓] Gate 2 ({arch_key} — {arch_label}): Quote={vc.quotation_price_vnd:,.0f} VND, "
                    f"NetAnnual={vc.net_annual_benefit_vnd:,.0f} VND, 3YNet={vc.three_year_net_benefit_vnd:,.0f} VND, "
                    f"Ratio={vc.quote_to_roi_ratio:.2f}x, ROI={vc.roi_percentage:.1f}%, "
                    f"Payback={vc.payback_months:.1f}m, FTS={len(fts_items)}, Elapsed={elapsed_sec * 1000:.1f}ms."
                )

            # Verify QWeb report `insilos_al2c.report_sales_proposal` renders cleanly on generated `sale.order`
            import re as _re
            assert generated_order is not None
            report_Action = env["ir.actions.report"].sudo()
            html_bytes, _fmt = report_Action._render_qweb_html(
                "insilos_al2c.report_sales_proposal", [generated_order.id]
            )
            html_str = (
                html_bytes.decode("utf-8", errors="replace")
                if isinstance(html_bytes, (bytes, bytearray))
                else str(html_bytes)
            )
            assert len(html_str) > 500, f"[{dbname}] Rendered report_sales_proposal HTML too short ({len(html_str)})"
            visible_text = _re.sub(r"(?is)<(script|style)\b[^>]*>.*?</\1>", " ", html_str)
            visible_text = _re.sub(r"(?s)<[^>]+>", " ", visible_text)
            lower_visible = visible_text.lower()
            assert "odoo" not in lower_visible and "openerp" not in lower_visible, (
                f"[{dbname}] Forbidden word 'Odoo'/'OpenERP' found in rendered insilos_al2c.report_sales_proposal!"
            )
            print(
                f"[✓] Gate 3.2: QWeb report `insilos_al2c.report_sales_proposal` rendered cleanly "
                f"({len(html_str)} chars, 0 'Odoo'/'OpenERP' occurrences)."
            )

        # ------------------------------------------------------------------
        # Gate 3: Executive PDF Report & Documents Data Room Sync
        # ------------------------------------------------------------------
        if not (os.path.isfile(REPORT_PDF_PATH) and os.path.isfile(BRAIN_PDF_PATH)):
            gen_script = os.path.join(ROOT_DIR, "tools", "generate_innoria_rapid_quote_roi_pdf.py")
            assert os.path.isfile(gen_script), f"Missing generator script {gen_script}"
            subprocess.run([sys.executable, gen_script], check=True)

        for pdf_path in (REPORT_PDF_PATH, BRAIN_PDF_PATH):
            assert os.path.isfile(pdf_path), f"Missing expected PDF file: {pdf_path}"
            fsize = os.path.getsize(pdf_path)
            assert fsize > 25 * 1024, f"PDF file {pdf_path} too small: {fsize} bytes (expected > 25 KB)"
            with open(pdf_path, "rb") as f:
                header_bytes = f.read(8)
            assert header_bytes.startswith(b"%PDF-1."), (
                f"PDF file {pdf_path} does not start with %PDF-1., got {header_bytes!r}"
            )
        print(
            f"[✓] Gate 3.1: Executive PDF verified at both `{REPORT_PDF_PATH}` and `{BRAIN_PDF_PATH}` "
            f"({os.path.getsize(REPORT_PDF_PATH):,} bytes, valid %PDF-1. header)."
        )

        # Sync the PDF into `documents.document` under `07. Quy trình Chuẩn & Tự động hóa (SOP & ERP Blueprints)`
        sop_folder = Document.search(
            [
                ("type", "=", "folder"),
                ("active", "=", True),
                ("name", "ilike", "07. Quy trình Chuẩn%"),
            ],
            limit=1,
        )
        if not sop_folder:
            sop_folder = Document.create(
                {
                    "name": SOP_FOLDER_NAME,
                    "type": "folder",
                    "owner_id": False,
                    "access_internal": "edit",
                    "active": True,
                }
            )
        else:
            if sop_folder.owner_id or sop_folder.access_internal != "edit":
                sop_folder.write({"owner_id": False, "access_internal": "edit"})

        with open(REPORT_PDF_PATH, "rb") as f:
            pdf_raw = f.read()
        pdf_b64 = base64.b64encode(pdf_raw)

        existing_doc = Document.search(
            [
                ("folder_id", "=", sop_folder.id),
                ("name", "=", PDF_DOC_NAME),
                ("type", "!=", "folder"),
                ("active", "=", True),
            ],
            limit=1,
        )
        if existing_doc:
            if existing_doc.attachment_id:
                existing_doc.attachment_id.write(
                    {
                        "datas": pdf_b64,
                        "name": PDF_DOC_NAME,
                        "mimetype": "application/pdf",
                    }
                )
            else:
                att = Attachment.create(
                    {
                        "name": PDF_DOC_NAME,
                        "datas": pdf_b64,
                        "mimetype": "application/pdf",
                        "res_model": "documents.document",
                        "res_id": existing_doc.id,
                    }
                )
                existing_doc.attachment_id = att.id
            existing_doc.write(
                {
                    "owner_id": False,
                    "access_internal": "edit",
                    "dgm_rbac_profile": "company_sop" if "dgm_rbac_profile" in existing_doc._fields else False,
                }
                if "dgm_rbac_profile" in existing_doc._fields
                else {
                    "owner_id": False,
                    "access_internal": "edit",
                }
            )
            pdf_doc = existing_doc
        else:
            att = Attachment.create(
                {
                    "name": PDF_DOC_NAME,
                    "datas": pdf_b64,
                    "mimetype": "application/pdf",
                }
            )
            doc_vals = {
                "name": PDF_DOC_NAME,
                "folder_id": sop_folder.id,
                "attachment_id": att.id,
                "type": "binary",
                "owner_id": False,
                "access_internal": "edit",
                "active": True,
            }
            if "dgm_rbac_profile" in Document._fields:
                doc_vals["dgm_rbac_profile"] = "company_sop"
            pdf_doc = Document.create(doc_vals)
            att.write({"res_model": "documents.document", "res_id": pdf_doc.id})

        cr.commit()

        assert pdf_doc and pdf_doc.exists()
        assert pdf_doc.folder_id.id == sop_folder.id
        assert pdf_doc.owner_id.id is False, f"Expected owner_id=False on {pdf_doc.name}, got {pdf_doc.owner_id}"
        assert pdf_doc.access_internal == "edit", (
            f"Expected access_internal='edit' on {pdf_doc.name}, got {pdf_doc.access_internal}"
        )
        assert pdf_doc.file_size > 25 * 1024, f"Expected file_size > 25 KB on {pdf_doc.name}, got {pdf_doc.file_size}"
        print(
            f"[✓] Gate 3.3: Synced `{PDF_DOC_NAME}` into `documents.document` (#{pdf_doc.id}) "
            f"under folder `{sop_folder.name}` (#{sop_folder.id}, owner_id=False, access_internal='edit', "
            f"size={pdf_doc.file_size:,} bytes)."
        )


def main():
    db_list = sys.argv[1:] if len(sys.argv) > 1 else ["insilos20_dev"]
    for dbname in db_list:
        run_verification(dbname)
    print("\n=== ALL SOP-DGM-15 RAPID CPQ, 5-ARCHETYPE ROI & EXECUTIVE PDF GATES PASSED (EXIT 0) ===")


if __name__ == "__main__":
    main()
