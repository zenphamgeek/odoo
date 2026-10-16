#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Idempotent Seeder for SOP-DGM-10:
Employee KPI Evaluation, Work Performance Appraisal & Mandatory Software Engineer
Skill Upgrade Gate (`dgm.hr.skill.track`, `dgm.hr.employee.skill.gate`,
`dgm.hr.kpi.evaluation`, `dgm.hr.work.review`) across `insilos20_dev` and `innoria_prod`.

Performs:
1. `reg.init_models(cr, ['dgm.hr.skill.track', 'dgm.hr.employee.skill.gate', 'dgm.hr.kpi.evaluation', 'dgm.hr.work.review', 'hr.employee'], {'module': 'insilos_al2c'}, install=True)`.
2. Loads `security/ir.access.csv` and `views/dgm_hr_kpi_skill_views.xml` via `convert_file`.
3. Calls `env['dgm.hr.kpi.evaluation'].sudo().seed_dgm_kpi_and_skill_framework()`.
4. Seeds `TPL-HR-06_Phieu_Danh_Gia_KPI_Va_Lo_Trinh_Nang_Cap_Ky_Nang_SOP_DGM_10.html` in
   `Bộ Mẫu Biểu Chuẩn Digimate - HR, Partner, Project, Finance` and ensures
   `SOP-DGM-10_KPI_Danh_Gia_Nhan_Su_Va_Khung_Nang_Luc_Ky_Su_Phan_Mem_2026.html` is present in
   both HR and SOP folders with `owner_id=False`, `access_internal='edit'`, `active=True`,
   and the Google Drive Logo Brand Header & Footer (`data-dgm-footer="drive-logo-v1"`,
   `data-logo-source="google-drive-logo-folder"`).
5. Enforces Zero Empty Folders (`0` empty active folders in `documents_document`).
"""
import base64
import os
import site
import sys
import types

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

import odoo
from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry
from odoo.tools import convert_file

_local_conf = os.path.join(ROOT_DIR, "odoo.conf")
if os.path.isfile("/etc/insilos/insilos.conf"):
    odoo.tools.config.parse_config(["-c", "/etc/insilos/insilos.conf"])
elif os.path.isfile(_local_conf):
    odoo.tools.config.parse_config(["-c", _local_conf])
else:
    odoo.tools.config.parse_config([])
if os.path.isdir("/var/lib/insilos/filestore"):
    odoo.tools.config["data_dir"] = "/var/lib/insilos/filestore"
    odoo.tools.config["addons_path"] = f"{ROOT_DIR}/odoo/addons,{ROOT_DIR}/addons,{ROOT_DIR}/enterprise"
if os.environ.get("DB_HOST"):
    odoo.tools.config["db_host"] = os.environ["DB_HOST"]
if os.environ.get("DB_PORT"):
    odoo.tools.config["db_port"] = int(os.environ["DB_PORT"])
if os.environ.get("DB_USER"):
    odoo.tools.config["db_user"] = os.environ["DB_USER"]
if os.environ.get("PGPASSWORD"):
    odoo.tools.config["db_password"] = os.environ["PGPASSWORD"]

from odoo.addons.insilos_al2c.models.dgm_brand_footer import (  # noqa: E402
    wrap_dgm_branded_html_document,
)

MASTER_LIBRARY_FOLDER_NAME = "Bộ Mẫu Biểu Chuẩn Digimate - HR, Partner, Project, Finance"
TPL_HR_06_FILENAME = "TPL-HR-06_Phieu_Danh_Gia_KPI_Va_Lo_Trinh_Nang_Cap_Ky_Nang_SOP_DGM_10.html"
SOP_10_DOC_FILENAME = "SOP-DGM-10_KPI_Danh_Gia_Nhan_Su_Va_Khung_Nang_Luc_Ky_Su_Phan_Mem_2026.html"


def _ensure_doc_active(env, rec):
    if rec and not rec.active:
        env.cr.execute("UPDATE documents_document SET active = TRUE WHERE id IN %s", [tuple(rec.ids)])
        rec.invalidate_recordset(["active"])


def _resolve_folder(env, preferred_id, name_patterns, parent_id=False):
    Document = env["documents.document"].sudo()
    if preferred_id:
        folder = Document.with_context(active_test=False).browse(preferred_id).exists()
        if folder and folder.type == "folder":
            _ensure_doc_active(env, folder)
            folder.write({
                "owner_id": False,
                "access_internal": "edit",
            })
            return folder
    for pat in name_patterns:
        domain = [("type", "=", "folder"), ("name", "ilike", pat)]
        if parent_id:
            domain.append(("folder_id", "=", parent_id))
        folder = Document.with_context(active_test=False).search(domain, order="id asc", limit=1)
        if folder:
            _ensure_doc_active(env, folder)
            folder.write({
                "owner_id": False,
                "access_internal": "edit",
            })
            return folder
    return Document.browse()


def _upsert_html_doc(env, folder_id, doc_name, filename, html_str, code_marker=None):
    Document = env["documents.document"].sudo()
    Attachment = env["ir.attachment"].sudo().with_context(no_document=True)
    b64_datas = base64.b64encode(html_str.encode("utf-8"))

    existing = Document.browse()
    if code_marker:
        existing = Document.with_context(active_test=False).search([
            ("folder_id", "=", folder_id),
            ("type", "!=", "folder"),
            ("name", "ilike", code_marker),
        ], order="id asc", limit=1)
    if not existing:
        existing = Document.with_context(active_test=False).search([
            ("folder_id", "=", folder_id),
            ("type", "!=", "folder"),
            ("name", "=", doc_name),
        ], order="id asc", limit=1)

    if existing:
        _ensure_doc_active(env, existing)
        if existing.attachment_id:
            existing.attachment_id.with_context(no_document=True).write({
                "name": filename,
                "datas": b64_datas,
                "mimetype": "text/html",
            })
        else:
            att = Attachment.create({
                "name": filename,
                "type": "binary",
                "datas": b64_datas,
                "mimetype": "text/html",
                "res_model": "documents.document",
                "res_id": existing.id,
            })
            existing.write({"attachment_id": att.id})
        existing.write({
            "name": doc_name,
            "folder_id": folder_id,
            "owner_id": False,
            "access_internal": "edit",
            "access_via_link": "view",
        })
        return existing

    att = Attachment.create({
        "name": filename,
        "type": "binary",
        "datas": b64_datas,
        "mimetype": "text/html",
        "res_model": "documents.document",
        "res_id": 0,
    })
    doc = Document.create({
        "name": doc_name,
        "folder_id": folder_id,
        "owner_id": False,
        "type": "binary",
        "attachment_id": att.id,
        "access_internal": "edit",
        "access_via_link": "view",
        "active": True,
    })
    att.write({"res_id": doc.id})
    return doc


def _build_tpl_hr_06_html():
    body = """
    <section>
      <h2>PHIẾU ĐÁNH GIÁ KPI NHÂN SỰ, NGHIỆM THU CÔNG VIỆC &amp; CỔNG NÂNG CẤP KỸ NĂNG KỸ SƯ PHẦN MỀM BẮT BUỘC (SOP-DGM-10)</h2>
      <p>
        Mẫu biểu chuẩn <strong>TPL-HR-06</strong> áp dụng thống nhất cho toàn bộ Kỹ sư Phần mềm (L1 Junior → L5 Principal)
        và Nhân sự tại <strong>CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ (DIGIMATE JSC)</strong> theo quy trình <strong>SOP-DGM-10</strong>.
      </p>
      <h3>1. Ma trận 4 Trụ cột Đánh giá KPI Định kỳ (4-Pillar Weighted Appraisal Matrix)</h3>
      <table>
        <thead>
          <tr>
            <th>Trụ cột (Pillar)</th>
            <th>Trọng số</th>
            <th>Chỉ số Đo lường Trọng tâm (Key Metrics)</th>
            <th>Ngưỡng Chuẩn (Target)</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><strong>Trụ cột 1: Tiến độ Giao phẩm &amp; Giờ công Billable (Delivery &amp; Billable SLA)</strong></td>
            <td><strong>35%</strong></td>
            <td>Tỷ lệ hoàn thành Sprint (`kpi_sprint_completion_pct`) &amp; Giờ công thực tế (`kpi_billable_hours_actual` / `160h`)</td>
            <td>&ge; 95% Sprint • 140–180h/tháng</td>
          </tr>
          <tr>
            <td><strong>Trụ cột 2: Chất lượng Kỹ thuật &amp; Kiến trúc (Engineering &amp; Code Quality)</strong></td>
            <td><strong>25%</strong></td>
            <td>Tỷ lệ qua cổng Code Review (`kpi_code_review_pass_rate`), Zero Regression (`kpi_zero_regression_score`), Lỗi Production (`-8đ/lỗi`)</td>
            <td>&ge; 95% • 0 lỗi Production</td>
          </tr>
          <tr>
            <td><strong>Trụ cột 3: Đánh giá Công việc &amp; Tuân thủ SOP (Work Appraisal &amp; CSAT)</strong></td>
            <td><strong>20%</strong></td>
            <td>Điểm hài lòng Khách hàng B2B/PM (`kpi_client_csat_score`) &amp; Tuân thủ SOP/ISO 27001 (`kpi_sop_compliance_score`)</td>
            <td>CSAT &ge; 92% • SOP 100%</td>
          </tr>
          <tr>
            <td><strong>Trụ cột 4: Cổng Nâng cấp Kỹ năng Kỹ sư Bắt buộc (Mandatory Skill Upgrade Gate)</strong></td>
            <td><strong>20%</strong></td>
            <td>Hoàn thành 100% các học phần bắt buộc (`SKL-ERP-OWL3`, `SKL-ERP-SCSS-DARK`, `SKL-AI-MOJO`, `SKL-AI-RAG`, `SKL-K8S-PG`, `SKL-SEC-ISO27001`, `SKL-B2B-ACTIVATE`, `SKL-QA-PLAYWRIGHT`)</td>
            <td>100% Certified (&ge; 85đ/môn)</td>
          </tr>
        </tbody>
      </table>

      <h3>2. Quy tắc Khóa Cổng Kỹ năng Bắt buộc (Mandatory Skill Upgrade Gate Cap Invariant)</h3>
      <ul>
        <li>
          <strong>Chốt chặn Hạng S / Hạng A (`skill_gate_capped`):</strong> Nếu kỹ sư có điểm thực thi công việc rất cao (Tổng điểm thô <code>raw_weighted_score &ge; 85.0</code> hoặc <code>&ge; 92.0</code>)
          nhưng <strong>chưa hoàn thành 100% học phần nâng cấp kỹ năng bắt buộc</strong> (<code>all_mandatory_skills_completed == False</code>), hệ thống tự động khóa trần điểm KPI chính thức ở mức <code>84.9</code>,
          xếp hạng tối đa <strong>Hạng B (`tier_b`)</strong>, hệ số thưởng <code>100%</code> và <code>promotion_eligible = False</code>.
        </li>
        <li>
          <strong>Mở khóa Tự động Tức thì (`action_certify_skill_upgrade`):</strong> Ngay khi Tech Lead / CTO nghiệm thu học phần kỹ năng còn thiếu đạt chuẩn (<code>state = 'certified'</code>, <code>score &ge; passing_score</code>),
          hệ thống tự động tính toán lại KPI, gỡ bỏ <code>skill_gate_capped</code>, nâng hạng lên <strong>Hạng A (`120%`)</strong> hoặc <strong>Hạng S (`150%` &amp; Đủ điều kiện Xét Thăng cấp)</strong>.
        </li>
      </ul>
    </section>
    """
    return wrap_dgm_branded_html_document(
        body_html=body,
        title="[TPL-HR-06] Phiếu Đánh giá KPI Nhân sự, Nghiệm thu Công việc & Lộ trình Nâng cấp Kỹ năng Kỹ sư Phần mềm (SOP-DGM-10)",
        doc_code="TPL-HR-06",
        sop_ref="SOP-DGM-10",
        classification="HR & ENGINEERING GOVERNANCE • KPI & SKILL GATE",
        include_header=True,
    )


def _build_sop_dgm_10_html():
    body = """
    <section>
      <h2>SOP-DGM-10: QUY TRÌNH ĐÁNH GIÁ KPI NHÂN SỰ, NGHIỆM THU CÔNG VIỆC &amp; CỔNG NÂNG CẤP KỸ NĂNG KỸ SƯ PHẦN MỀM BẮT BUỘC</h2>
      <p>
        <strong>Mã Quy trình:</strong> <code>SOP-DGM-10</code> •
        <strong>Pháp nhân:</strong> CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ (DIGIMATE JSC — MST: 0317958465 • Mã ĐV BHXH: TZ0857G)
      </p>
      <h3>I. Danh mục 8 Chuyên đề Nâng cấp Kỹ năng Bắt buộc cho Kỹ sư Phần mềm (`dgm.hr.skill.track`)</h3>
      <table>
        <thead>
          <tr>
            <th>Mã Kỹ năng</th>
            <th>Tên Chuyên đề Đào tạo &amp; Kiểm định Thực chiến</th>
            <th>Nhóm Năng lực</th>
            <th>Giờ Chuẩn</th>
            <th>Điểm Đạt</th>
          </tr>
        </thead>
        <tbody>
          <tr><td><code>SKL-ERP-OWL3</code></td><td>Kiến trúc OWL 2/3 Hybrid Reactivity, Props Guard &amp; Insilos WebClient</td><td><code>erp_owl</code></td><td>24h</td><td>85.0</td></tr>
          <tr><td><code>SKL-ERP-SCSS-DARK</code></td><td>Sovereign Dual-Bundle Dark Mode SCSS &amp; Zero-Bare-Hex Token Architecture</td><td><code>erp_owl</code></td><td>16h</td><td>90.0</td></tr>
          <tr><td><code>SKL-AI-MOJO</code></td><td>Lập trình Hệ thống Hiệu năng cao với Mojo &amp; Tối ưu Kernel AI/SIMD</td><td><code>ai_mojo</code></td><td>32h</td><td>85.0</td></tr>
          <tr><td><code>SKL-AI-RAG</code></td><td>Kiến trúc Sovereign Grounded RAG, Zero-Hallucination Citation &amp; Agentic MCP</td><td><code>ai_mojo</code></td><td>24h</td><td>85.0</td></tr>
          <tr><td><code>SKL-K8S-PG</code></td><td>Cloud-Native Kubernetes Production, PostgreSQL Bipartite Advisory Locks &amp; Zero-Downtime</td><td><code>cloud_db</code></td><td>24h</td><td>85.0</td></tr>
          <tr><td><code>SKL-SEC-ISO27001</code></td><td>Bảo mật ISO/IEC 27001:2022, ISO/IEC 27701 &amp; Nghị định 13/2023/NĐ-CP Zero-Leak PII</td><td><code>sec_privacy</code></td><td>16h</td><td>90.0</td></tr>
          <tr><td><code>SKL-B2B-ACTIVATE</code></td><td>Quy trình Triển khai Dự án B2B Onsite (MTI / AIfin / KTT) &amp; Đối soát Hóa đơn 1C26TAA</td><td><code>b2b_delivery</code></td><td>20h</td><td>85.0</td></tr>
          <tr><td><code>SKL-QA-PLAYWRIGHT</code></td><td>Kiểm thử Tự động Playwright Dual-Theme E2E &amp; Adversarial Security Gate</td><td><code>qa_e2e</code></td><td>20h</td><td>85.0</td></tr>
        </tbody>
      </table>
      <h3>II. Cơ chế Xếp hạng KPI (`rank_grade`) &amp; Thưởng Hiệu suất (`bonus_multiplier_pct`)</h3>
      <ul>
        <li><strong>Hạng S (`tier_s` — &ge; 92.0đ &amp; Đạt 100% Kỹ năng Bắt buộc):</strong> Thưởng 150% KPI, Mở khóa Xét Thăng cấp Cấp bậc Kỹ sư (`promotion_eligible = True`).</li>
        <li><strong>Hạng A (`tier_a` — 85.0–91.9đ &amp; Đạt 100% Kỹ năng Bắt buộc):</strong> Thưởng 120% KPI, Đủ điều kiện Xét Thăng cấp (`promotion_eligible = True`).</li>
        <li><strong>Hạng B (`tier_b` — 75.0–84.9đ hoặc Bị khóa trần do Chưa hoàn thành Kỹ năng Bắt buộc):</strong> Thưởng 100% Chuẩn, yêu cầu hoàn tất học phần bắt buộc trước khi mở khóa Hạng A/S.</li>
        <li><strong>Hạng C (`tier_c` — 60.0–74.9đ):</strong> Hệ số 50%, kích hoạt Lộ trình Cải thiện Hiệu suất &amp; Đào tạo 30 ngày (PIP).</li>
        <li><strong>Hạng D (`tier_d` — &lt; 60.0đ):</strong> Hệ số 0%, cảnh báo hiệu suất và tái đào tạo bắt buộc.</li>
      </ul>
    </section>
    """
    return wrap_dgm_branded_html_document(
        body_html=body,
        title="SOP-DGM-10: Quy trình Đánh giá KPI Nhân sự, Nghiệm thu Công việc & Cổng Nâng cấp Kỹ năng Kỹ sư Phần mềm Bắt buộc",
        doc_code="SOP-DGM-10",
        sop_ref="SOP-DGM-10",
        classification="INTERNAL GOVERNANCE & ENGINEERING SOP",
        include_header=True,
    )


def seed_database(dbname):
    print(f"\n=== Seeding SOP-DGM-10 KPI & Software Engineer Skill Upgrade Framework in `{dbname}` ===")
    reg = Registry.new(dbname)
    with reg.cursor() as cr:
        # 1. Initialize the new models in schema
        reg.init_models(
            cr,
            [
                "dgm.hr.skill.track",
                "dgm.hr.employee.skill.gate",
                "dgm.hr.kpi.evaluation",
                "dgm.hr.work.review",
                "hr.employee",
            ],
            {"module": "insilos_al2c"},
            install=True,
        )

        env = api.Environment(cr, SUPERUSER_ID, {"no_document": True})

        # 2. Load security/ir.access.csv and views/dgm_hr_kpi_skill_views.xml
        for rel_path in (
            "security/ir.access.csv",
            "views/dgm_hr_kpi_skill_views.xml",
        ):
            full_path = os.path.join(ROOT_DIR, "addons/insilos_al2c", rel_path)
            if os.path.isfile(full_path):
                convert_file(
                    env,
                    "insilos_al2c",
                    rel_path,
                    {},
                    mode="init",
                    noupdate=False,
                    kind="data",
                )

        # 3. Call model-level seeder
        KpiEval = env["dgm.hr.kpi.evaluation"].sudo()
        if hasattr(KpiEval, "seed_dgm_kpi_and_skill_framework"):
            KpiEval.seed_dgm_kpi_and_skill_framework()

        # 4. Ensure TPL-HR-06 in Master Template Library and SOP-DGM-10 in HR & SOP folders
        hr_folder = _resolve_folder(
            env,
            preferred_id=3224 if dbname == "insilos20_dev" else 208,
            name_patterns=["01. Pháp lý & Hành chính", "01. Hành chính", "03 · Nhân Sự"],
        )
        sop_folder = _resolve_folder(
            env,
            preferred_id=4704 if dbname == "insilos20_dev" else 214,
            name_patterns=["07. Quy trình Chuẩn & Tự động hóa", "07. Quy trình", "02 · Quy Trình"],
        )
        lib_folder = _resolve_folder(
            env,
            preferred_id=4942 if dbname == "insilos20_dev" else 526,
            name_patterns=[MASTER_LIBRARY_FOLDER_NAME, "Bộ Mẫu Biểu Chuẩn Digimate"],
            parent_id=sop_folder.id if sop_folder else False,
        )
        if not lib_folder and sop_folder:
            lib_folder = env["documents.document"].sudo().create({
                "name": MASTER_LIBRARY_FOLDER_NAME,
                "type": "folder",
                "folder_id": sop_folder.id,
                "owner_id": False,
                "access_internal": "edit",
                "active": True,
            })

        tpl_hr_06_html = _build_tpl_hr_06_html()
        if lib_folder:
            _upsert_html_doc(
                env,
                folder_id=lib_folder.id,
                doc_name=TPL_HR_06_FILENAME,
                filename=TPL_HR_06_FILENAME,
                html_str=tpl_hr_06_html,
                code_marker="TPL-HR-06",
            )

        sop_10_html = _build_sop_dgm_10_html()
        for target_folder in (hr_folder, sop_folder):
            if target_folder:
                _upsert_html_doc(
                    env,
                    folder_id=target_folder.id,
                    doc_name=SOP_10_DOC_FILENAME,
                    filename=SOP_10_DOC_FILENAME,
                    html_str=sop_10_html,
                    code_marker="SOP-DGM-10_KPI_Danh_Gia_Nhan_Su",
                )

        # Ensure SOP-DGM-10 Knowledge Article has Drive Logo Brand Footer
        Article = env["knowledge.article"].sudo()
        kb_10 = Article.search([("name", "ilike", "SOP-DGM-10%")], order="id asc", limit=1)
        if not kb_10:
            kb_10 = Article.create({
                "name": "SOP-DGM-10: Quy trình Đánh giá KPI Nhân sự, Nghiệm thu Công việc & Cổng Nâng cấp Kỹ năng Kỹ sư Phần mềm Bắt buộc",
                "body": sop_10_html,
                "internal_permission": "write",
                "is_article_visible_by_everyone": True,
                "active": True,
            })
        env.flush_all()
        cr.execute(
            "UPDATE knowledge_article SET body = %s, active = TRUE WHERE id = %s",
            (sop_10_html, kb_10.id),
        )
        kb_10.invalidate_recordset(["body", "active"])

        # Ensure every evaluation's linked document_id (if any) has Drive Logo Brand Footer
        for ev in KpiEval.search([]):
            if ev.document_id and ev.document_id.attachment_id and ev.document_id.attachment_id.datas:
                raw_ev = base64.b64decode(ev.document_id.attachment_id.datas).decode("utf-8", errors="replace")
                if 'data-dgm-footer="drive-logo-v1"' not in raw_ev:
                    branded_ev = wrap_dgm_branded_html_document(
                        body_html=raw_ev,
                        title=ev.document_id.name or ev.name,
                        doc_code=ev.name or "KPI-2026-Q4",
                        sop_ref="SOP-DGM-10",
                        classification="HR CONFIDENTIAL • KPI EVALUATION",
                        include_header=True,
                    )
                    ev.document_id.attachment_id.with_context(no_document=True).write({
                        "datas": base64.b64encode(branded_ev.encode("utf-8")),
                        "mimetype": "text/html",
                    })
                _ensure_doc_active(env, ev.document_id)
                ev.document_id.write({"owner_id": False, "access_internal": "edit"})

        # 5. Enforce Zero Empty Folders Invariant (Rule 6)
        Document = env["documents.document"].sudo()
        for _ in range(5):
            cr.execute(
                """
                SELECT f.id
                  FROM documents_document f
                 WHERE f.type = 'folder' AND f.active = TRUE
                   AND NOT EXISTS (
                       SELECT 1 FROM documents_document c
                        WHERE c.folder_id = f.id AND c.active = TRUE
                   );
                """
            )
            empty_ids = [r[0] for r in cr.fetchall()]
            if not empty_ids:
                break
            Document.browse(empty_ids).write({"active": False})

        cr.commit()

    print(f"[✓] `{dbname}` SOP-DGM-10 KPI & Skill Upgrade Framework seeded and committed successfully.")


def main():
    db_list = sys.argv[1:] if len(sys.argv) > 1 else ["insilos20_dev", "innoria_prod"]
    for dbname in db_list:
        seed_database(dbname)
    print("\n=== ALL SOP-DGM-10 KPI & SKILL UPGRADE FRAMEWORK SEEDING COMPLETED (EXIT 0) ===")


if __name__ == "__main__":
    main()
