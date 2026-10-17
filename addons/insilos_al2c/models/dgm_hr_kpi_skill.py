# -*- coding: utf-8 -*-
"""
SOP-DGM-10: Employee KPI Evaluation, Work Performance Appraisal &
Mandatory Software Engineer Skill Upgrade Gate Architecture.
=============================================================================
Models:
1. `dgm.hr.skill.track`: Canonical engineering skill & competency tracks
2. `dgm.hr.employee.skill.gate`: Mandatory skill assignments, progress & certification
3. `dgm.hr.work.review`: Sprint, milestone & project work performance reviews
4. `dgm.hr.kpi.evaluation`: 4-pillar weighted KPI evaluation & gate capping
5. `hr.employee`: Extension with DGM employee code, current KPI and skill status
"""
import base64
import html
import logging
from pathlib import Path

from odoo import api, fields, models, _
from odoo.exceptions import UserError

try:
    from .dgm_brand_footer import (
        get_digimate_logo_data_uri,
        get_digimate_logo_url,
        render_dgm_brand_footer_html,
        render_dgm_brand_header_html,
        wrap_dgm_branded_html_document,
    )
except ImportError:
    import importlib.util as _importlib_util
    _bf_path = Path(__file__).resolve().parent / "dgm_brand_footer.py"
    _bf_spec = _importlib_util.spec_from_file_location("dgm_brand_footer", _bf_path)
    _bf_mod = _importlib_util.module_from_spec(_bf_spec)
    _bf_spec.loader.exec_module(_bf_mod)
    get_digimate_logo_data_uri = _bf_mod.get_digimate_logo_data_uri
    get_digimate_logo_url = _bf_mod.get_digimate_logo_url
    render_dgm_brand_footer_html = _bf_mod.render_dgm_brand_footer_html
    render_dgm_brand_header_html = _bf_mod.render_dgm_brand_header_html
    wrap_dgm_branded_html_document = _bf_mod.wrap_dgm_branded_html_document

_logger = logging.getLogger(__name__)


def _safe_iter_records(records):
    if records is None:
        return []
    try:
        return list(records)
    except TypeError:
        return [records]


def _safe_today():
    today_fn = getattr(fields.Date, 'today', None)
    if callable(today_fn):
        return today_fn()
    return '2026-10-16'


def _safe_to_date(val):
    to_date_fn = getattr(fields.Date, 'to_date', None)
    if callable(to_date_fn):
        return to_date_fn(val)
    return val


SKILL_CATEGORY_SELECTION = [
    ('erp_owl', '1. Kiến trúc Insilos ERP / OWL 3 & Sovereign Dark Mode'),
    ('ai_mojo', '2. AI Agentic, Grounded RAG & Mojo Systems Engineering'),
    ('cloud_db', '3. Cloud-Native K8s, PostgreSQL Concurrency & DevSecOps'),
    ('sec_privacy', '4. Bảo mật ISO/IEC 27001, ISO 27701 & Nghị định 13/2023/NĐ-CP'),
    ('b2b_delivery', '5. Triển khai B2B Onsite (MTI/AIfin/KTT) & SAP Activate'),
    ('qa_e2e', '6. Kiểm thử Tự động, Adversarial Security & Playwright E2E'),
]

ENGINEER_LEVEL_SELECTION = [
    ('l1_junior', 'L1 — Kỹ sư Phần mềm Sơ cấp (Junior Software Engineer)'),
    ('l2_mid', 'L2 — Kỹ sư Phần mềm Độc lập (Mid-Level Software Engineer)'),
    ('l3_senior', 'L3 — Kỹ sư Phần mềm Cao cấp / Onsite B2B (Senior Software Engineer)'),
    ('l4_lead', 'L4 — Kỹ sư Trưởng / Kiến trúc sư (Staff / Tech Lead)'),
    ('l5_principal', 'L5 — Kiến trúc sư Trưởng / CTO (Principal / Executive Tech)'),
]

SKILL_GATE_STATE_SELECTION = [
    ('planned', 'Kế hoạch Đào tạo (Planned)'),
    ('assigned', 'Đã giao Lộ trình (Assigned)'),
    ('in_progress', 'Đang học & Thực hành (In Progress)'),
    ('submitted', 'Chờ Tech Lead / CTO Nghiệm thu (Submitted)'),
    ('certified', 'Đã Đạt Chuẩn Nâng cấp Kỹ năng (Certified • Gate Passed)'),
    ('failed', 'Chưa Đạt / Cần Đào tạo Lại (Failed)'),
    ('overdue', 'Quá hạn Cần Cải thiện (Overdue / Action Required)'),
]

RANK_GRADE_SELECTION = [
    ('tier_s', 'Hạng S (Xuất sắc ≥ 92đ & Đạt 100% Kỹ năng Bắt buộc) — Thưởng 150% & Xét Thăng cấp'),
    ('tier_a', 'Hạng A (Tốt 85–91.9đ & Đạt 100% Kỹ năng Bắt buộc) — Thưởng 120% KPI'),
    ('tier_b', 'Hạng B (Đạt chuẩn 75–84.9đ hoặc Chưa xong Kỹ năng Bắt buộc) — Thưởng 100% Chuẩn'),
    ('tier_c', 'Hạng C (Cần cải thiện 60–74.9đ) — Lộ trình Đào tạo Bắt buộc 30 ngày (PIP)'),
    ('tier_d', 'Hạng D (Không đạt < 60đ) — Cảnh báo Hiệu suất & Tái đào tạo'),
]

KPI_STATE_SELECTION = [
    ('draft', 'Đang theo dõi trong kỳ (Active Tracking)'),
    ('self_submitted', 'Nhân sự Tự đánh giá (Self-Appraisal)'),
    ('manager_reviewed', 'Tech Lead / Quản lý Đã chấm (Manager Reviewed)'),
    ('approved', 'Ban Giám đốc Phê duyệt Chính thức (Approved)'),
]


CANONICAL_SKILL_TRACKS = [
    {
        'sequence': 10,
        'code': 'SKL-ERP-OWL3',
        'name': 'Kiến trúc Insilos WebClient, OWL 2/3 Hybrid Reactivity & Props Guard',
        'category': 'erp_owl',
        'domain': 'erp_owl',
        'target_engineer_level': 'l2_mid',
        'is_mandatory': True,
        'required_hours': 24.0,
        'training_hours': 24.0,
        'passing_score': 85.0,
        'curriculum_summary': (
            'Làm chủ kiến trúc reactive OWL 3, signal/proxy binding, frozen props guard '
            'trong makeProps, zero-DOM-mutation và kế thừa an toàn trên view hooks.'
        ),
        'description': (
            'Làm chủ kiến trúc reactive OWL 3, signal/proxy binding, frozen props guard '
            'trong makeProps, zero-DOM-mutation và kế thừa an toàn trên view hooks.'
        ),
        'verification_cmd': 'node enterprise/documents/static/tests/documents_test.js',
    },
    {
        'sequence': 20,
        'code': 'SKL-ERP-SCSS-DARK',
        'name': 'Sovereign Dual-Bundle Dark Mode SCSS & Zero-Bare-Hex Token Standards',
        'category': 'erp_owl',
        'domain': 'erp_owl',
        'target_engineer_level': 'l2_mid',
        'is_mandatory': True,
        'required_hours': 16.0,
        'training_hours': 16.0,
        'passing_score': 90.0,
        'curriculum_summary': (
            'Chuẩn hóa thiết kế token Insilos: cấm bare hex fallback trong var(), tách biệt '
            'hoàn toàn web.assets_backend và web.assets_web_dark, cấm wildcard glob CSS.'
        ),
        'description': (
            'Chuẩn hóa thiết kế token Insilos: cấm bare hex fallback trong var(), tách biệt '
            'hoàn toàn web.assets_backend và web.assets_web_dark, cấm wildcard glob CSS.'
        ),
        'verification_cmd': 'python3 tools/unslop_scss_rigorous.py',
    },
    {
        'sequence': 30,
        'code': 'SKL-AI-MOJO',
        'name': 'Lập trình Hệ thống Hiệu năng Cao với Mojo, Python Interop & AI Hardware SIMD',
        'category': 'ai_mojo',
        'domain': 'ai_mojo',
        'target_engineer_level': 'l3_senior',
        'is_mandatory': True,
        'required_hours': 32.0,
        'training_hours': 32.0,
        'passing_score': 85.0,
        'curriculum_summary': (
            'Viết kernel Mojo tối ưu hóa SIMD, quản lý bộ nhớ không garbage collection, '
            'liên kết zero-copy với Python runtime và xử lý streaming LLM token.'
        ),
        'description': (
            'Viết kernel Mojo tối ưu hóa SIMD, quản lý bộ nhớ không garbage collection, '
            'liên kết zero-copy với Python runtime và xử lý streaming LLM token.'
        ),
        'verification_cmd': 'mojo test -I /home/zen/O20/mojo_kernels',
    },
    {
        'sequence': 40,
        'code': 'SKL-AI-RAG',
        'name': 'Kiến trúc Grounded RAG, Zero-Hallucination Citation & AGY Fleet Orchestration',
        'category': 'ai_mojo',
        'domain': 'ai_mojo',
        'target_engineer_level': 'l3_senior',
        'is_mandatory': True,
        'required_hours': 24.0,
        'training_hours': 24.0,
        'passing_score': 85.0,
        'curriculum_summary': (
            'Xây dựng pipeline RAG tự chủ có trích dẫn nguồn chuẩn xác, chống ảo giác (zero-hallucination), '
            'điều phối tác vụ qua fleet_run/fleet_parallel và MCP protocol.'
        ),
        'description': (
            'Xây dựng pipeline RAG tự chủ có trích dẫn nguồn chuẩn xác, chống ảo giác (zero-hallucination), '
            'điều phối tác vụ qua fleet_run/fleet_parallel và MCP protocol.'
        ),
        'verification_cmd': 'python3 -m unittest discover -s addons/insilos_al2c/tests -p "test_rag*.py"',
    },
    {
        'sequence': 50,
        'code': 'SKL-K8S-PG',
        'name': 'Cloud-Native Kubernetes Production, PostgreSQL Bipartite Advisory Locks & Zero-Downtime',
        'category': 'cloud_db',
        'domain': 'cloud_db',
        'target_engineer_level': 'l3_senior',
        'is_mandatory': True,
        'required_hours': 28.0,
        'training_hours': 28.0,
        'passing_score': 85.0,
        'curriculum_summary': (
            'Vận hành cụm K8s production, cấu hình PgBouncer transaction pooling, cơ chế tự phục hồi '
            'table compatibility view (relkind=v) và khóa chống race condition pg_advisory_xact_lock.'
        ),
        'description': (
            'Vận hành cụm K8s production, cấu hình PgBouncer transaction pooling, cơ chế tự phục hồi '
            'table compatibility view (relkind=v) và khóa chống race condition pg_advisory_xact_lock.'
        ),
        'verification_cmd': 'kubectl get pods -n production -l app=innoria-prod-app',
    },
    {
        'sequence': 60,
        'code': 'SKL-SEC-ISO27001',
        'name': 'Bảo mật Thông tin ISO/IEC 27001:2022, ISO 27701 & Nghị định 13/2023/NĐ-CP Zero-Leak PII',
        'category': 'sec_privacy',
        'domain': 'sec_privacy',
        'target_engineer_level': 'l2_mid',
        'is_mandatory': True,
        'required_hours': 16.0,
        'training_hours': 16.0,
        'passing_score': 90.0,
        'curriculum_summary': (
            'Thực thi kiểm soát bảo vệ dữ liệu cá nhân theo Nghị định 13/2023/NĐ-CP, che mờ PII một phần '
            '(partial masking), cơ chế tiết lộ có kiểm toán 30 giây và chống rò rỉ secret trong telemetry.'
        ),
        'description': (
            'Thực thi kiểm soát bảo vệ dữ liệu cá nhân theo Nghị định 13/2023/NĐ-CP, che mờ PII một phần '
            '(partial masking), cơ chế tiết lộ có kiểm toán 30 giây và chống rò rỉ secret trong telemetry.'
        ),
        'verification_cmd': 'python3 tools/test_adversarial_security.py',
    },
    {
        'sequence': 70,
        'code': 'SKL-B2B-ACTIVATE',
        'name': 'Quy trình Triển khai B2B Staff Augmentation (SOP-DGM-06/07/08) & SAP Activate 5 Phases',
        'category': 'b2b_delivery',
        'domain': 'b2b_delivery',
        'target_engineer_level': 'l2_mid',
        'is_mandatory': True,
        'required_hours': 20.0,
        'training_hours': 20.0,
        'passing_score': 85.0,
        'curriculum_summary': (
            'Chuẩn hóa quy trình bàn giao kỹ sư Onsite B2B (MTI, AIfin, KTT), định mức 140–180h/tháng, '
            'chốt bảng chấm công, nghiệm thu điện tử SHA-256 và đối soát hóa đơn nháp MTI.'
        ),
        'description': (
            'Chuẩn hóa quy trình bàn giao kỹ sư Onsite B2B (MTI, AIfin, KTT), định mức 140–180h/tháng, '
            'chốt bảng chấm công, nghiệm thu điện tử SHA-256 và đối soát hóa đơn nháp MTI.'
        ),
        'verification_cmd': 'python3 tools/test_dgm_partner_onboarding.py',
    },
    {
        'sequence': 80,
        'code': 'SKL-QA-PLAYWRIGHT',
        'name': 'Kiểm thử Tự động Đa tầng, Adversarial Security & Headless Playwright E2E Dual-Theme',
        'category': 'qa_e2e',
        'domain': 'qa_e2e',
        'target_engineer_level': 'l2_mid',
        'is_mandatory': True,
        'required_hours': 24.0,
        'training_hours': 24.0,
        'passing_score': 85.0,
        'curriculum_summary': (
            'Viết kịch bản kiểm thử tự động E2E trên cả Light Mode và Dark Mode, kiểm tra rò rỉ dữ liệu '
            'chéo (IDOR/XSS/SQLi) và đảm bảo 0 lỗi console/layout trước khi đẩy code.'
        ),
        'description': (
            'Viết kịch bản kiểm thử tự động E2E trên cả Light Mode và Dark Mode, kiểm tra rò rỉ dữ liệu '
            'chéo (IDOR/XSS/SQLi) và đảm bảo 0 lỗi console/layout trước khi đẩy code.'
        ),
        'verification_cmd': 'python3 tools/test_adversarial_security.py',
    },
]


class DgmHrSkillTrack(models.Model):
    _name = 'dgm.hr.skill.track'
    _description = 'DGM Software Engineer Mandatory Skill & Competency Track'
    _order = 'sequence, code'

    sequence = fields.Integer(default=10)
    code = fields.Char(
        string='Mã Học phần / Kỹ năng',
        required=True,
        index=True,
    )
    name = fields.Char(
        string='Tên Chuyên đề Nâng cấp Kỹ năng',
        required=True,
    )
    domain = fields.Char(
        string='Miền Năng lực (Domain)',
        default='erp_owl',
    )
    category = fields.Selection(
        SKILL_CATEGORY_SELECTION,
        string='Nhóm Năng lực Kỹ thuật',
        required=True,
        default='erp_owl',
        index=True,
    )
    target_engineer_level = fields.Selection(
        ENGINEER_LEVEL_SELECTION,
        string='Cấp bậc Kỹ sư Áp dụng',
        required=True,
        default='l3_senior',
        index=True,
    )
    is_mandatory = fields.Boolean(
        default=True,
        string='Bắt buộc hoàn thành (Mandatory Gate)',
    )
    training_hours = fields.Float(
        default=24.0,
        string='Thời lượng Đào tạo Chuẩn (Giờ)',
    )
    required_hours = fields.Float(
        default=24.0,
        string='Thời lượng Đào tạo Chuẩn (Giờ)',
    )
    passing_score = fields.Float(
        default=85.0,
        string='Điểm Đạt Tối thiểu (/100)',
    )
    description = fields.Text(
        string='Mô tả Học phần & Mục tiêu Đào tạo',
    )
    curriculum_summary = fields.Text(
        string='Nội dung Chương trình & Tiêu chuẩn Đầu ra (DoD)',
    )
    verification_cmd = fields.Char(
        string='Lệnh / Bài thi Kiểm định Thực chiến (Practical Lab / DoD Gate)',
    )
    active = fields.Boolean(default=True)

    @api.model_create_multi
    def create(self, vals_list):
        for v in vals_list:
            if 'training_hours' in v and 'required_hours' not in v:
                v['required_hours'] = v['training_hours']
            elif 'required_hours' in v and 'training_hours' not in v:
                v['training_hours'] = v['required_hours']
            if 'description' in v and 'curriculum_summary' not in v:
                v['curriculum_summary'] = v['description']
            elif 'curriculum_summary' in v and 'description' not in v:
                v['description'] = v['curriculum_summary']
            if 'domain' in v and 'category' not in v:
                v['category'] = v['domain']
            elif 'category' in v and 'domain' not in v:
                v['domain'] = v['category']
        return super().create(vals_list)

    def write(self, vals):
        v = dict(vals)
        if 'training_hours' in v and 'required_hours' not in v:
            v['required_hours'] = v['training_hours']
        elif 'required_hours' in v and 'training_hours' not in v:
            v['training_hours'] = v['required_hours']
        if 'description' in v and 'curriculum_summary' not in v:
            v['curriculum_summary'] = v['description']
        elif 'curriculum_summary' in v and 'description' not in v:
            v['description'] = v['curriculum_summary']
        if 'domain' in v and 'category' not in v:
            v['category'] = v['domain']
        elif 'category' in v and 'domain' not in v:
            v['domain'] = v['category']
        return super().write(v)


class DgmHrEmployeeSkillGate(models.Model):
    _name = 'dgm.hr.employee.skill.gate'
    _description = 'DGM Employee Mandatory Skill Upgrade Assignment & Gate'
    _order = 'is_mandatory desc, id asc'

    employee_id = fields.Many2one(
        'hr.employee',
        string='Nhân sự / Kỹ sư',
        required=True,
        ondelete='cascade',
        index=True,
    )
    skill_track_id = fields.Many2one(
        'dgm.hr.skill.track',
        string='Chuyên đề Kỹ năng',
        required=True,
        ondelete='restrict',
        index=True,
    )
    track_code = fields.Char(
        related='skill_track_id.code',
        store=True,
        string='Mã Kỹ năng',
    )
    track_name = fields.Char(
        related='skill_track_id.name',
        store=True,
        string='Tên Kỹ năng',
    )
    category = fields.Selection(
        related='skill_track_id.category',
        store=True,
    )
    domain = fields.Char(
        related='skill_track_id.domain',
        store=True,
    )
    is_mandatory = fields.Boolean(
        default=True,
        string='Bắt buộc hoàn thành (Mandatory Gate)',
    )
    is_mandatory_for_next_level = fields.Boolean(
        default=True,
        string='Bắt buộc cho Cấp bậc Tiếp theo',
    )
    active = fields.Boolean(default=True)
    current_level = fields.Integer(
        default=3,
        string='Mức Kỹ năng Hiện tại (1-5)',
    )
    target_level = fields.Integer(
        default=4,
        string='Mức Kỹ năng Yêu cầu (1-5)',
    )
    completed_hours = fields.Float(
        default=0.0,
        string='Số giờ Đã học / Thực hành',
    )
    required_hours = fields.Float(
        related='skill_track_id.required_hours',
        store=True,
    )
    assessment_score = fields.Float(
        default=0.0,
        string='Điểm Kiểm định Thực chiến (/100)',
    )
    passing_score = fields.Float(
        related='skill_track_id.passing_score',
        store=True,
    )
    deadline_date = fields.Date(
        string='Hạn chót Hoàn thành (SLA)',
        default=lambda self: _safe_to_date('2026-12-15'),
    )
    certified_date = fields.Date(
        string='Ngày Đạt Chứng chỉ / Nghiệm thu',
    )
    completed_date = fields.Date(
        string='Ngày Hoàn thành',
    )
    evidence_ref = fields.Char(
        string='Minh chứng Thực chiến (Commit / PR / Evidence Ref)',
    )
    evidence_artifact = fields.Char(
        string='Minh chứng Commit / PR / Chứng chỉ',
    )
    state = fields.Selection(
        SKILL_GATE_STATE_SELECTION,
        default='planned',
        required=True,
        index=True,
        string='Trạng thái Cổng Kỹ năng',
    )
    progress_pct = fields.Float(
        compute='_compute_skill_gate_progress',
        store=True,
        string='Tiến độ Hoàn thành (%)',
    )

    @api.depends('completed_hours', 'required_hours', 'state', 'assessment_score')
    def _compute_skill_gate_progress(self):
        for rec in _safe_iter_records(self):
            if rec.state == 'certified':
                rec.progress_pct = 100.0
            elif rec.state == 'submitted':
                rec.progress_pct = 90.0
            elif rec.state == 'in_progress':
                req = float(getattr(rec, 'required_hours', 24.0) or 24.0)
                comp = float(getattr(rec, 'completed_hours', 0.0) or 0.0)
                ratio = (comp / req * 100.0) if req > 0 else 50.0
                rec.progress_pct = round(min(85.0, max(10.0, ratio)), 1)
            elif rec.state == 'failed':
                rec.progress_pct = 0.0
            else:
                rec.progress_pct = 0.0

    @api.model_create_multi
    def create(self, vals_list):
        for v in vals_list:
            if 'is_mandatory' in v and 'is_mandatory_for_next_level' not in v:
                v['is_mandatory_for_next_level'] = v['is_mandatory']
            elif 'is_mandatory_for_next_level' in v and 'is_mandatory' not in v:
                v['is_mandatory'] = v['is_mandatory_for_next_level']
            if 'evidence_ref' in v and 'evidence_artifact' not in v:
                v['evidence_artifact'] = v['evidence_ref']
            elif 'evidence_artifact' in v and 'evidence_ref' not in v:
                v['evidence_ref'] = v['evidence_artifact']
            if 'certified_date' in v and 'completed_date' not in v:
                v['completed_date'] = v['certified_date']
            elif 'completed_date' in v and 'certified_date' not in v:
                v['certified_date'] = v['completed_date']
        records = super().create(vals_list)
        self._trigger_employee_kpi_recompute(records)
        return records

    def write(self, vals):
        v = dict(vals)
        if 'is_mandatory' in v and 'is_mandatory_for_next_level' not in v:
            v['is_mandatory_for_next_level'] = v['is_mandatory']
        elif 'is_mandatory_for_next_level' in v and 'is_mandatory' not in v:
            v['is_mandatory'] = v['is_mandatory_for_next_level']
        if 'evidence_ref' in v and 'evidence_artifact' not in v:
            v['evidence_artifact'] = v['evidence_ref']
        elif 'evidence_artifact' in v and 'evidence_ref' not in v:
            v['evidence_ref'] = v['evidence_artifact']
        if 'certified_date' in v and 'completed_date' not in v:
            v['completed_date'] = v['certified_date']
        elif 'completed_date' in v and 'certified_date' not in v:
            v['certified_date'] = v['completed_date']
        res = super().write(v)
        self._trigger_employee_kpi_recompute(self)
        return res

    @classmethod
    def _trigger_employee_kpi_recompute(cls, gates):
        emp_ids = set()
        for g in _safe_iter_records(gates):
            emp = getattr(g, 'employee_id', None)
            if emp:
                emp_ids.add(getattr(emp, 'id', None))
        for eid in emp_ids:
            if not eid:
                continue
            try:
                env = getattr(gates, 'env', None)
                if env:
                    Employee = env['hr.employee'].sudo()
                    KpiEval = env['dgm.hr.kpi.evaluation'].sudo()
                    emp_rec = Employee.browse(eid).exists()
                    if emp_rec:
                        evals = KpiEval.search([('employee_id', '=', emp_rec.id)])
                        for ev in evals:
                            ev._compute_kpi_scores_and_skill_gate()
                        if 'dgm.hr.appraisal.sheet' in env:
                            Appraisal = env['dgm.hr.appraisal.sheet'].sudo()
                            appraisals = Appraisal.search([('employee_id', '=', emp_rec.id)])
                            for ap in appraisals:
                                ap._compute_appraisal_calibration()
                        if hasattr(emp_rec, '_compute_dgm_kpi_summary'):
                            emp_rec._compute_dgm_kpi_summary()
            except Exception as e:
                _logger.warning("Error triggering employee KPI recompute for emp_id %s: %s", eid, e)

    def action_submit_skill_evidence(self, evidence_ref=None, hours=None):
        for rec in _safe_iter_records(self):
            ref_val = str(evidence_ref or getattr(rec, 'evidence_ref', '') or getattr(rec, 'evidence_artifact', '') or 'PR-SUBMITTED-2026').strip()
            req_hours = float(getattr(rec, 'required_hours', 24.0) or 24.0)
            comp_h = float(hours) if hours is not None else max(float(getattr(rec, 'completed_hours', 0.0) or 0.0), req_hours)
            rec.write({
                'evidence_ref': ref_val,
                'evidence_artifact': ref_val,
                'completed_hours': comp_h,
                'state': 'submitted',
            })
            rec._compute_skill_gate_progress()
        self._trigger_employee_kpi_recompute(self)
        return True

    def action_certify_skill_upgrade(self, score=None, evidence_ref=None):
        for rec in _safe_iter_records(self):
            min_pass = float(getattr(rec, 'passing_score', 85.0) or 85.0)
            curr_score = float(getattr(rec, 'assessment_score', 0.0) or 0.0)
            final_score = float(score) if score is not None else max(curr_score, min_pass)
            if final_score < min_pass:
                raise UserError(
                    _(
                        "Vi phạm Cổng Kiểm định Kỹ năng (SOP-DGM-10): Điểm thực chiến (%.1f) thấp hơn ngưỡng đạt chuẩn tối thiểu (%.1f) cho chuyên đề '%s'."
                    )
                    % (final_score, min_pass, getattr(rec, 'track_code', '') or getattr(rec, 'track_name', 'Skill Track'))
                )
            req_hours = float(getattr(rec, 'required_hours', 24.0) or 24.0)
            new_hours = max(float(getattr(rec, 'completed_hours', 0.0) or 0.0), req_hours)
            new_level = max(int(getattr(rec, 'current_level', 3) or 3), int(getattr(rec, 'target_level', 4) or 4))
            ev_ref = str(evidence_ref or getattr(rec, 'evidence_ref', '') or getattr(rec, 'evidence_artifact', '') or 'PR-VERIFIED-2026').strip()
            vals = {
                'assessment_score': final_score,
                'completed_hours': new_hours,
                'current_level': new_level,
                'certified_date': _safe_today(),
                'completed_date': _safe_today(),
                'evidence_ref': ev_ref,
                'evidence_artifact': ev_ref,
                'state': 'certified',
            }
            if hasattr(rec, 'write') and callable(rec.write):
                rec.write(vals)
            else:
                for k, v in vals.items():
                    setattr(rec, k, v)
            rec._compute_skill_gate_progress()
        self._trigger_employee_kpi_recompute(self)
        return True


class DgmHrWorkReview(models.Model):
    _name = 'dgm.hr.work.review'
    _description = 'DGM Project & Sprint Work Performance Review'
    _order = 'review_date desc, id desc'

    name = fields.Char(
        string='Mã Đánh giá Công việc',
        required=True,
        default='WRK-2026-Q4',
    )
    kpi_evaluation_id = fields.Many2one(
        'dgm.hr.kpi.evaluation',
        string='Kỳ Đánh giá KPI',
        ondelete='cascade',
        index=True,
    )
    evaluation_id = fields.Many2one(
        'dgm.hr.kpi.evaluation',
        string='Kỳ Đánh giá KPI (Legacy)',
        ondelete='cascade',
        index=True,
    )
    employee_id = fields.Many2one(
        'hr.employee',
        string='Nhân sự',
        required=True,
        ondelete='cascade',
        index=True,
    )
    reviewer_id = fields.Many2one(
        'res.users',
        string='Người Đánh giá',
    )
    reviewer_name = fields.Char(
        string='Người Đánh giá / Phê duyệt',
        default='Lê Xuân Hoàng — Chủ tịch HĐQT & Tổng Giám đốc',
    )
    review_type = fields.Selection(
        [
            ('peer', 'Đồng nghiệp (Peer Review)'),
            ('lead', 'Tech Lead / Quản lý Trực tiếp'),
            ('client', 'Khách hàng B2B Onsite'),
            ('executive', 'Ban Giám đốc (Executive)'),
        ],
        default='lead',
        string='Loại Đánh giá',
    )
    score = fields.Float(
        string='Điểm Đánh giá (/100)',
        default=95.0,
    )
    feedback = fields.Text(
        string='Nhận xét & Phản hồi',
    )
    project_name = fields.Char(
        string='Dự án / Khách hàng B2B',
        required=True,
        default='Insilos Core / B2B Onsite',
    )
    sprint_or_milestone = fields.Char(
        string='Sprint / Giai đoạn Nghiệm thu',
        default='2026-Q4 (Tháng 10–12/2026)',
    )
    deliverables_completed = fields.Text(
        string='Kết quả Giao phẩm & Đóng góp Kỹ thuật (Deliverables)',
    )
    task_completion_rate = fields.Float(
        string='Tỷ lệ Hoàn thành Công việc (%)',
        default=96.0,
    )
    code_quality_score = fields.Float(
        string='Điểm Chất lượng Code & Kiến trúc (/100)',
        default=95.0,
    )
    review_date = fields.Date(
        string='Ngày Nghiệm thu',
        default=lambda self: _safe_today(),
    )
    state = fields.Selection(
        [
            ('draft', 'Dự thảo (Draft)'),
            ('submitted', 'Chờ Quản lý Duyệt (Submitted)'),
            ('verified', 'Đã Xác nhận Đạt Chuẩn (Verified)'),
        ],
        default='verified',
        string='Trạng thái Nghiệm thu',
    )
    active = fields.Boolean(default=True)

    @api.model_create_multi
    def create(self, vals_list):
        for v in vals_list:
            if 'kpi_evaluation_id' in v and 'evaluation_id' not in v:
                v['evaluation_id'] = v['kpi_evaluation_id']
            elif 'evaluation_id' in v and 'kpi_evaluation_id' not in v:
                v['kpi_evaluation_id'] = v['evaluation_id']
            if 'score' in v and 'code_quality_score' not in v:
                v['code_quality_score'] = v['score']
            elif 'code_quality_score' in v and 'score' not in v:
                v['score'] = v['code_quality_score']
            if 'feedback' in v and 'deliverables_completed' not in v:
                v['deliverables_completed'] = v['feedback']
            elif 'deliverables_completed' in v and 'feedback' not in v:
                v['feedback'] = v['deliverables_completed']
        return super().create(vals_list)

    def write(self, vals):
        v = dict(vals)
        if 'kpi_evaluation_id' in v and 'evaluation_id' not in v:
            v['evaluation_id'] = v['kpi_evaluation_id']
        elif 'evaluation_id' in v and 'kpi_evaluation_id' not in v:
            v['kpi_evaluation_id'] = v['evaluation_id']
        if 'score' in v and 'code_quality_score' not in v:
            v['code_quality_score'] = v['score']
        elif 'code_quality_score' in v and 'score' not in v:
            v['score'] = v['code_quality_score']
        if 'feedback' in v and 'deliverables_completed' not in v:
            v['deliverables_completed'] = v['feedback']
        elif 'deliverables_completed' in v and 'feedback' not in v:
            v['feedback'] = v['deliverables_completed']
        return super().write(v)


class DgmHrKpiEvaluation(models.Model):
    _name = 'dgm.hr.kpi.evaluation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'DGM Employee KPI & Work Performance Appraisal'
    _order = 'period_code desc, id desc'

    name = fields.Char(
        string='Mã Kỳ Đánh giá KPI',
        required=True,
        default='KPI-2026-Q4',
        index=True,
        tracking=True,
    )
    employee_id = fields.Many2one(
        'hr.employee',
        string='Nhân sự / Kỹ sư',
        required=True,
        ondelete='cascade',
        index=True,
        tracking=True,
    )
    period_code = fields.Char(
        string='Kỳ Đánh giá (Quý / Năm)',
        required=True,
        default='2026-Q4',
        index=True,
    )
    engineer_level = fields.Selection(
        ENGINEER_LEVEL_SELECTION,
        string='Cấp bậc Kỹ sư (Engineer Level)',
        required=True,
        default='l3_senior',
        tracking=True,
    )
    work_review_ids = fields.One2many(
        'dgm.hr.work.review',
        'kpi_evaluation_id',
        string='Chi tiết Đánh giá Công việc & Dự án',
    )
    skill_gate_ids = fields.Many2many(
        'dgm.hr.employee.skill.gate',
        string='Cổng Kỹ năng Bắt buộc',
        compute='_compute_kpi_scores_and_skill_gate',
        store=True,
    )

    # Pillar 1: Delivery & Billable SLA (35% weight)
    kpi_sprint_completion_pct = fields.Float(
        string='Tỷ lệ Hoàn thành Sprint / Mốc SOW (%)',
        default=95.0,
    )
    kpi_billable_hours_actual = fields.Float(
        string='Số giờ Billable / Thực chiến Thực tế (Giờ)',
        default=168.0,
    )
    kpi_billable_hours_target = fields.Float(
        string='Định mức Giờ công Chuẩn (Giờ)',
        default=160.0,
    )
    delivery_score = fields.Float(
        string='Điểm Trụ cột 1 — Giao phẩm & Tiến độ (35%)',
        compute='_compute_kpi_scores_and_skill_gate',
        store=True,
    )
    score_delivery = fields.Float(
        string='Điểm Trụ cột 1 — Giao phẩm & Tiến độ (35%)',
        compute='_compute_kpi_scores_and_skill_gate',
        store=True,
    )

    # Pillar 2: Code & Engineering Quality (25% weight)
    kpi_code_review_pass_rate = fields.Float(
        string='Tỷ lệ Đạt Chuẩn Code Review / Clean Architecture (%)',
        default=96.0,
    )
    kpi_zero_regression_score = fields.Float(
        string='Điểm Zero-Regression & Test Coverage (/100)',
        default=98.0,
    )
    kpi_production_defect_count = fields.Integer(
        string='Số lỗi Nghiêm trọng trên Production (P0/P1 Defects)',
        default=0,
    )
    quality_score = fields.Float(
        string='Điểm Trụ cột 2 — Chất lượng Kỹ thuật (25%)',
        compute='_compute_kpi_scores_and_skill_gate',
        store=True,
    )
    score_quality = fields.Float(
        string='Điểm Trụ cột 2 — Chất lượng Kỹ thuật (25%)',
        compute='_compute_kpi_scores_and_skill_gate',
        store=True,
    )

    # Pillar 3: B2B Client CSAT & SOP Compliance (20% weight)
    collaboration_score = fields.Float(
        string='Điểm Trụ cột 3a — CSAT Khách hàng / Hợp tác (/100)',
        default=95.0,
    )
    kpi_client_csat_score = fields.Float(
        string='Điểm Đánh giá từ Khách hàng B2B / Tech Lead (/100)',
        default=95.0,
    )
    sop_compliance_score = fields.Float(
        string='Điểm Trụ cột 3b — Tuân thủ Quy trình SOP & ISO 27001 (/100)',
        default=100.0,
    )
    kpi_sop_compliance_score = fields.Float(
        string='Điểm Tuân thủ Quy trình SOP & Bảo mật ISO 27001 (/100)',
        default=100.0,
    )
    score_work_eval = fields.Float(
        string='Điểm Trụ cột 3 — Nghiệm thu Công việc & Tuân thủ (20%)',
        compute='_compute_kpi_scores_and_skill_gate',
        store=True,
    )

    # Pillar 4: Mandatory Software Engineer Skill Upgrade Gate (20% weight)
    mandatory_skill_total = fields.Integer(
        string='Tổng Chuyên đề Kỹ năng Bắt buộc',
        compute='_compute_kpi_scores_and_skill_gate',
        store=True,
    )
    mandatory_skill_certified = fields.Integer(
        string='Số Chuyên đề Bắt buộc Đã Đạt Chuẩn',
        compute='_compute_kpi_scores_and_skill_gate',
        store=True,
    )
    mandatory_skill_completion_pct = fields.Float(
        string='Tỷ lệ Hoàn thành Kỹ năng Bắt buộc (%)',
        compute='_compute_kpi_scores_and_skill_gate',
        store=True,
    )
    all_mandatory_skills_completed = fields.Boolean(
        string='Đạt 100% Cổng Kỹ năng Bắt buộc (Skill Gate Passed)',
        compute='_compute_kpi_scores_and_skill_gate',
        store=True,
    )
    score_skill_upgrade = fields.Float(
        string='Điểm Trụ cột 4 — Nâng cấp Kỹ năng Bắt buộc (20%)',
        compute='_compute_kpi_scores_and_skill_gate',
        store=True,
    )

    # Final Weighted & Gate-Capped Outputs
    raw_weighted_score = fields.Float(
        string='Điểm KPI Trọng số Gốc (Trước Cổng Kỹ năng)',
        compute='_compute_kpi_scores_and_skill_gate',
        store=True,
    )
    weighted_kpi_score = fields.Float(
        string='Điểm KPI Trọng số Chính thức (/100)',
        compute='_compute_kpi_scores_and_skill_gate',
        store=True,
        tracking=True,
    )
    final_kpi_score = fields.Float(
        string='Điểm KPI Chính thức Cuối kỳ (/100)',
        compute='_compute_kpi_scores_and_skill_gate',
        store=True,
        tracking=True,
    )
    skill_gate_capped = fields.Boolean(
        string='Bị Giới hạn Hạng do Chưa Hoàn thành Kỹ năng Bắt buộc',
        compute='_compute_kpi_scores_and_skill_gate',
        store=True,
    )
    rank_grade = fields.Selection(
        RANK_GRADE_SELECTION,
        string='Xếp hạng Hiệu suất & Đãi ngộ (KPI Grade)',
        compute='_compute_kpi_scores_and_skill_gate',
        store=True,
        tracking=True,
    )
    promotion_eligible = fields.Boolean(
        string='Đủ Điều kiện Xét Thăng cấp & Tăng lương',
        compute='_compute_kpi_scores_and_skill_gate',
        store=True,
    )
    bonus_multiplier_pct = fields.Float(
        string='Hệ số Thưởng Hiệu suất KPI (%)',
        compute='_compute_kpi_scores_and_skill_gate',
        store=True,
    )
    work_evaluation_summary = fields.Text(
        string='Nhận xét Tổng hợp Hiệu suất Công việc & Giao phẩm',
    )
    training_roadmap_note = fields.Text(
        string='Kế hoạch Nâng cấp Kỹ năng & Yêu cầu Đào tạo Bắt buộc',
    )
    document_id = fields.Many2one(
        'documents.document',
        string='Hồ sơ Phiếu Đánh giá KPI (Documents)',
        copy=False,
    )
    state = fields.Selection(
        KPI_STATE_SELECTION,
        default='approved',
        required=True,
        tracking=True,
        string='Trạng thái Phê duyệt',
    )
    active = fields.Boolean(default=True)

    @api.depends(
        'kpi_sprint_completion_pct',
        'kpi_billable_hours_actual',
        'kpi_billable_hours_target',
        'kpi_code_review_pass_rate',
        'kpi_zero_regression_score',
        'kpi_production_defect_count',
        'collaboration_score',
        'kpi_client_csat_score',
        'sop_compliance_score',
        'kpi_sop_compliance_score',
        'employee_id.dgm_skill_gate_ids.state',
        'employee_id.dgm_skill_gate_ids.is_mandatory_for_next_level',
        'employee_id.dgm_skill_gate_ids.is_mandatory',
        'employee_id.dgm_skill_gate_ids.assessment_score',
        'employee_id.dgm_skill_gate_ids.progress_pct',
        'employee_id.dgm_skill_gate_ids.active',
    )
    def _compute_kpi_scores_and_skill_gate(self):
        for rec in _safe_iter_records(self):
            # Pillar 1: Delivery & Billable SLA (35%)
            target_h = float(rec.kpi_billable_hours_target or 160.0)
            actual_h = float(rec.kpi_billable_hours_actual or 0.0)
            hours_ratio = min(105.0, (actual_h / target_h) * 100.0) if target_h > 0 else 100.0
            deliv = round(
                min(100.0, 0.6 * float(rec.kpi_sprint_completion_pct or 0.0) + 0.4 * hours_ratio),
                2,
            )
            rec.delivery_score = deliv
            rec.score_delivery = deliv

            # Pillar 2: Code & Engineering Quality (25%)
            defect_penalty = int(rec.kpi_production_defect_count or 0) * 8.0
            qual = round(
                max(
                    0.0,
                    min(
                        100.0,
                        0.5 * float(rec.kpi_code_review_pass_rate or 0.0)
                        + 0.5 * float(rec.kpi_zero_regression_score or 0.0)
                        - defect_penalty,
                    ),
                ),
                2,
            )
            rec.quality_score = qual
            rec.score_quality = qual

            # Pillar 3: B2B Client CSAT & SOP Compliance (20%)
            collab = float(rec.collaboration_score or rec.kpi_client_csat_score or 95.0)
            rec.collaboration_score = collab
            rec.kpi_client_csat_score = collab
            sop = float(rec.sop_compliance_score or rec.kpi_sop_compliance_score or 100.0)
            rec.sop_compliance_score = sop
            rec.kpi_sop_compliance_score = sop
            work_eval = round(min(100.0, 0.6 * collab + 0.4 * sop), 2)
            rec.score_work_eval = work_eval

            # Pillar 4: Mandatory Software Engineer Skill Upgrade Gate (20%)
            emp = getattr(rec, 'employee_id', None)
            gates = _safe_iter_records(getattr(emp, 'dgm_skill_gate_ids', [])) if emp else []
            active_gates = [g for g in gates if getattr(g, 'active', True)]
            rec.skill_gate_ids = [(6, 0, [g.id for g in active_gates if getattr(g, 'id', None)])]

            mand_gates = [
                g for g in active_gates
                if getattr(g, 'is_mandatory_for_next_level', False) or getattr(g, 'is_mandatory', False)
            ]
            cert_gates = [g for g in mand_gates if getattr(g, 'state', '') == 'certified']
            rec.mandatory_skill_total = len(mand_gates)
            rec.mandatory_skill_certified = len(cert_gates)

            if rec.mandatory_skill_total > 0:
                rec.mandatory_skill_completion_pct = round(
                    (len(cert_gates) / len(mand_gates)) * 100.0, 2
                )
                rec.all_mandatory_skills_completed = (len(cert_gates) == len(mand_gates))
                avg_gate_score = (
                    sum(
                        (
                            float(getattr(g, 'assessment_score', 0.0) or 0.0)
                            if getattr(g, 'state', '') == 'certified'
                            else float(getattr(g, 'progress_pct', 0.0) or 0.0) * 0.8
                        )
                        for g in mand_gates
                    )
                    / len(mand_gates)
                )
                rec.score_skill_upgrade = round(min(100.0, avg_gate_score), 2)
            else:
                rec.mandatory_skill_completion_pct = 100.0
                rec.all_mandatory_skills_completed = True
                rec.score_skill_upgrade = 100.0

            # Weighted Score & Mandatory Skill Upgrade Gate Cap
            raw = (
                0.35 * rec.delivery_score
                + 0.25 * rec.quality_score
                + 0.20 * rec.score_work_eval
                + 0.20 * rec.score_skill_upgrade
            )
            rec.raw_weighted_score = round(raw, 2)

            if not rec.all_mandatory_skills_completed:
                rec.skill_gate_capped = True
                rec.weighted_kpi_score = round(min(raw, 84.9), 2)
                rec.final_kpi_score = rec.weighted_kpi_score
                if raw >= 75.0:
                    rec.rank_grade = 'tier_b'
                elif raw >= 60.0:
                    rec.rank_grade = 'tier_c'
                else:
                    rec.rank_grade = 'tier_d'
                rec.promotion_eligible = False
                rec.bonus_multiplier_pct = (
                    100.0
                    if rec.rank_grade == 'tier_b'
                    else (50.0 if rec.rank_grade == 'tier_c' else 0.0)
                )
            else:
                rec.skill_gate_capped = False
                rec.weighted_kpi_score = round(raw, 2)
                rec.final_kpi_score = rec.weighted_kpi_score
                if raw >= 92.0:
                    rec.rank_grade = 'tier_s'
                    rec.promotion_eligible = True
                    rec.bonus_multiplier_pct = 150.0
                elif raw >= 85.0:
                    rec.rank_grade = 'tier_a'
                    rec.promotion_eligible = True
                    rec.bonus_multiplier_pct = 120.0
                elif raw >= 75.0:
                    rec.rank_grade = 'tier_b'
                    rec.promotion_eligible = False
                    rec.bonus_multiplier_pct = 100.0
                elif raw >= 60.0:
                    rec.rank_grade = 'tier_c'
                    rec.promotion_eligible = False
                    rec.bonus_multiplier_pct = 50.0
                else:
                    rec.rank_grade = 'tier_d'
                    rec.promotion_eligible = False
                    rec.bonus_multiplier_pct = 0.0

    def _compute_kpi_scores(self):
        return self._compute_kpi_scores_and_skill_gate()

    def _render_kpi_evaluation_html(self):
        emp = getattr(self, 'employee_id', None)
        emp_name = html.escape(str(getattr(emp, 'name', '') or 'Kỹ sư Phần mềm'))
        emp_code = html.escape(str(getattr(emp, 'registration_number', '') or getattr(emp, 'barcode', '') or 'DGM-EMP'))
        job_title = html.escape(str(getattr(emp, 'job_title', '') or 'Software Engineer'))
        period_str = html.escape(str(getattr(self, 'period_code', '') or '2026-Q4'))
        level_map = dict(ENGINEER_LEVEL_SELECTION)
        rank_map = dict(RANK_GRADE_SELECTION)
        level_label = html.escape(level_map.get(getattr(self, 'engineer_level', 'l3_senior'), 'L3 Senior'))
        rank_label = html.escape(rank_map.get(getattr(self, 'rank_grade', 'tier_b'), 'Hạng B'))

        gates = _safe_iter_records(getattr(emp, 'dgm_skill_gate_ids', [])) if emp else []
        gate_rows = []
        for idx, g in enumerate(gates, start=1):
            t_code = html.escape(str(getattr(g, 'track_code', '') or ''))
            t_name = html.escape(str(getattr(g, 'track_name', '') or ''))
            g_state = html.escape(str(getattr(g, 'state', '') or ''))
            g_hours = f"{float(getattr(g, 'completed_hours', 0.0) or 0.0):.1f}/{float(getattr(g, 'required_hours', 24.0) or 24.0):.1f}h"
            g_score = f"{float(getattr(g, 'assessment_score', 0.0) or 0.0):.1f}/{float(getattr(g, 'passing_score', 85.0) or 85.0):.1f}"
            g_prog = f"{float(getattr(g, 'progress_pct', 0.0) or 0.0):.1f}%"
            gate_rows.append(
                f"<tr>"
                f"<td>{idx}</td>"
                f"<td><code>{t_code}</code> — <strong>{t_name}</strong></td>"
                f"<td style='text-align:center;'>{g_hours}</td>"
                f"<td style='text-align:center;'>{g_score}</td>"
                f"<td style='text-align:center;'>{g_prog}</td>"
                f"<td style='text-align:center;'><strong>{g_state.upper()}</strong></td>"
                f"</tr>"
            )
        gates_tbody = "\n".join(gate_rows) or "<tr><td colspan='6'>Chưa có chuyên đề kỹ năng được gán.</td></tr>"

        cap_notice = ""
        if getattr(self, 'skill_gate_capped', False):
            cap_notice = (
                "<div style='margin: 12px 0; padding: 10px 14px; border: 2px dashed var(--insilos-border-subtle, #d97706); border-radius: 6px;'>"
                "<strong>⚠️ CẢNH BÁO CỔNG KỸ NĂNG BẮT BUỘC (MANDATORY SKILL UPGRADE GATE CAP):</strong> "
                "Điểm trọng số gốc đạt mức cao nhưng nhân sự chưa hoàn thành 100% chuyên đề nâng cấp kỹ năng bắt buộc trong kỳ. "
                "Điểm KPI chính thức tạm thời giới hạn ở mức tối đa <strong>84.9đ (Hạng B)</strong> cho đến khi hoàn tất nghiệm thu kỹ năng."
                "</div>"
            )

        body_html = f"""
        <section class="dgm-kpi-appraisal-doc">
          <h2 style="margin-top:0;">PHIẾU ĐÁNH GIÁ KPI, NGHIỆM THU CÔNG VIỆC &amp; CỔNG KỸ NĂNG KỸ SƯ (SOP-DGM-10)</h2>
          <p><strong>Kỳ đánh giá:</strong> {period_str} | <strong>Mã hồ sơ:</strong> <code>{html.escape(str(self.name or 'KPI-2026-Q4'))}</code></p>
          <table>
            <tbody>
              <tr>
                <th style="width:22%;">Họ và tên Nhân sự</th>
                <td style="width:28%;"><strong>{emp_name}</strong> (<code>{emp_code}</code>)</td>
                <th style="width:22%;">Chức danh &amp; Cấp bậc</th>
                <td style="width:28%;">{job_title}<br/><small>{level_label}</small></td>
              </tr>
              <tr>
                <th>Điểm KPI Trọng số Gốc</th>
                <td><strong>{float(self.raw_weighted_score or 0.0):.2f} / 100</strong></td>
                <th>Điểm KPI Chính thức</th>
                <td><strong>{float(self.final_kpi_score or self.weighted_kpi_score or 0.0):.2f} / 100</strong></td>
              </tr>
              <tr>
                <th>Xếp hạng Hiệu suất</th>
                <td><strong>{rank_label}</strong></td>
                <th>Hệ số Thưởng &amp; Thăng cấp</th>
                <td>Thưởng: <strong>{float(self.bonus_multiplier_pct or 0.0):.0f}%</strong> | Thăng cấp: <strong>{'ĐỦ ĐIỀU KIỆN' if self.promotion_eligible else 'CHƯA ĐỦ ĐIỀU KIỆN'}</strong></td>
              </tr>
            </tbody>
          </table>
          {cap_notice}
          <h3>1. Bảng Điểm 4 Trụ Cột KPI Trọng Số (4-Pillar Weighted Appraisal)</h3>
          <table>
            <thead>
              <tr>
                <th>Trụ cột Đánh giá (KPI Pillar)</th>
                <th style="text-align:center;">Trọng số</th>
                <th>Chỉ số Đo lường Chi tiết</th>
                <th style="text-align:right;">Điểm Đạt (/100)</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td><strong>Trụ cột 1: Giao phẩm &amp; Tiến độ Dự án (Delivery &amp; Billable SLA)</strong></td>
                <td style="text-align:center;">35%</td>
                <td>Sprint/SOW: {float(self.kpi_sprint_completion_pct or 0.0):.1f}% | Giờ công: {float(self.kpi_billable_hours_actual or 0.0):.1f}/{float(self.kpi_billable_hours_target or 160.0):.1f}h</td>
                <td style="text-align:right;"><strong>{float(self.delivery_score or self.score_delivery or 0.0):.2f}</strong></td>
              </tr>
              <tr>
                <td><strong>Trụ cột 2: Chất lượng Code &amp; Kiến trúc (Code &amp; Architecture Quality)</strong></td>
                <td style="text-align:center;">25%</td>
                <td>Code Review: {float(self.kpi_code_review_pass_rate or 0.0):.1f}% | Zero-Regression: {float(self.kpi_zero_regression_score or 0.0):.1f} | Lỗi P0/P1: {int(self.kpi_production_defect_count or 0)}</td>
                <td style="text-align:right;"><strong>{float(self.quality_score or self.score_quality or 0.0):.2f}</strong></td>
              </tr>
              <tr>
                <td><strong>Trụ cột 3: Đánh giá Công việc B2B &amp; Tuân thủ SOP (Work Eval &amp; SOP)</strong></td>
                <td style="text-align:center;">20%</td>
                <td>CSAT Khách hàng/PM: {float(self.collaboration_score or self.kpi_client_csat_score or 0.0):.1f} | Tuân thủ SOP &amp; ISO 27001: {float(self.sop_compliance_score or self.kpi_sop_compliance_score or 0.0):.1f}</td>
                <td style="text-align:right;"><strong>{float(self.score_work_eval or 0.0):.2f}</strong></td>
              </tr>
              <tr>
                <td><strong>Trụ cột 4: Cổng Nâng cấp Kỹ năng Bắt buộc (Mandatory Skill Gate)</strong></td>
                <td style="text-align:center;">20%</td>
                <td>Đã đạt: {int(self.mandatory_skill_certified or 0)}/{int(self.mandatory_skill_total or 0)} chuyên đề ({float(self.mandatory_skill_completion_pct or 0.0):.1f}%)</td>
                <td style="text-align:right;"><strong>{float(self.score_skill_upgrade or 0.0):.2f}</strong></td>
              </tr>
            </tbody>
          </table>

          <h3>2. Trạng thái Cổng Nâng cấp Kỹ năng Kỹ sư Phần mềm Bắt buộc</h3>
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>Mã &amp; Tên Chuyên đề Kỹ năng</th>
                <th style="text-align:center;">Thời lượng</th>
                <th style="text-align:center;">Điểm Kiểm định</th>
                <th style="text-align:center;">Tiến độ</th>
                <th style="text-align:center;">Trạng thái Gate</th>
              </tr>
            </thead>
            <tbody>
              {gates_tbody}
            </tbody>
          </table>
          <p><strong>Nhận xét Đánh giá Công việc:</strong> {html.escape(str(self.work_evaluation_summary or 'Hoàn thành tốt nhiệm vụ kỹ thuật và cam kết SLA dự án.'))}</p>
          <p><strong>Lộ trình Đào tạo &amp; Phát triển:</strong> {html.escape(str(self.training_roadmap_note or 'Duy trì chuẩn kỹ năng OWL 3, Sovereign Dark Mode, Mojo AI và ISO/IEC 27001.'))}</p>
        </section>
        """
        return wrap_dgm_branded_html_document(
            body_html,
            title=f"Phiếu Đánh giá KPI & Cổng Kỹ năng — {emp_name} ({period_str})",
            doc_code=str(self.name or "KPI-2026-Q4"),
            sop_ref="SOP-DGM-10",
            classification="HR CONFIDENTIAL • KPI EVALUATION",
            include_header=True,
        )

    def action_generate_kpi_evaluation_document(self):
        Document = self.env['documents.document'].sudo()
        Attachment = self.env['ir.attachment'].sudo()

        for rec in _safe_iter_records(self):
            html_content = rec._render_kpi_evaluation_html()
            b64_datas = base64.b64encode(html_content.encode('utf-8'))
            emp = getattr(rec, 'employee_id', None)
            emp_code = getattr(emp, 'registration_number', '') or getattr(emp, 'barcode', '') or 'DGM'
            doc_name = f"TPL-KPI-01_Phieu_KPI_{emp_code}_{getattr(rec, 'period_code', '2026-Q4')}.html"

            # Resolve HR Documents folder (e.g. 3224)
            target_folder = Document.browse(3224).exists()
            if not target_folder or getattr(target_folder, 'type', '') != 'folder' or not getattr(target_folder, 'active', False):
                target_folder = Document.search(
                    [
                        ('type', '=', 'folder'),
                        ('active', '=', True),
                        '|',
                        ('name', 'ilike', '01. Pháp lý'),
                        ('name', 'ilike', 'Nhân Sự'),
                    ],
                    order='id asc',
                    limit=1,
                )

            folder_id = target_folder.id if target_folder else False

            existing_doc = getattr(rec, 'document_id', None)
            if existing_doc and existing_doc.exists():
                if existing_doc.attachment_id:
                    existing_doc.attachment_id.with_context(no_document=True).write({
                        'datas': b64_datas,
                        'name': doc_name,
                        'mimetype': 'text/html',
                    })
                existing_doc.write({
                    'name': doc_name,
                    'owner_id': False,
                    'access_internal': 'edit',
                    'active': True,
                })
            else:
                att = Attachment.create({
                    'name': doc_name,
                    'type': 'binary',
                    'datas': b64_datas,
                    'mimetype': 'text/html',
                    'res_model': 'documents.document',
                    'res_id': 0,
                })
                doc = Document.create({
                    'name': doc_name,
                    'folder_id': folder_id,
                    'owner_id': False,
                    'type': 'binary',
                    'attachment_id': att.id,
                    'access_internal': 'edit',
                    'access_via_link': 'view',
                    'active': True,
                })
                att.write({'res_id': doc.id})
                rec.write({'document_id': doc.id})
        return True

    def action_approve_kpi_evaluation(self):
        for rec in _safe_iter_records(self):
            rec.write({'state': 'approved'})
            rec.action_generate_kpi_evaluation_document()
        return True

    def render_sop_dgm_10_master_html(self):
        SkillTrack = self.env['dgm.hr.skill.track'].sudo()
        tracks = SkillTrack.search([('active', '=', True)], order='sequence, code')
        track_rows = []
        for idx, t in enumerate(tracks, start=1):
            t_code = html.escape(str(t.code or ''))
            t_name = html.escape(str(t.name or ''))
            t_dod = html.escape(str(t.curriculum_summary or t.description or ''))
            t_hours = f"{float(t.required_hours or t.training_hours or 24.0):.1f}h"
            t_pass = f"{float(t.passing_score or 85.0):.1f}"
            t_cmd = html.escape(str(t.verification_cmd or 'pytest'))
            track_rows.append(
                f"<tr>"
                f"<td>{idx}</td>"
                f"<td><code>{t_code}</code></td>"
                f"<td><strong>{t_name}</strong><br/><small>{t_dod}</small></td>"
                f"<td style='text-align:center;'>{t_hours}</td>"
                f"<td style='text-align:center;'>{t_pass}</td>"
                f"<td><code>{t_cmd}</code></td>"
                f"</tr>"
            )
        tracks_tbody = "\n".join(track_rows)

        body_html = f"""
        <section class="dgm-sop-doc">
          <h2>QUY TRÌNH ĐÁNH GIÁ KPI, NGHIỆM THU CÔNG VIỆC &amp; CỔNG NÂNG CẤP KỸ NĂNG KỸ SƯ PHẦN MỀM BẮT BUỘC (SOP-DGM-10)</h2>
          <p>
            Quy trình này quy định cơ chế đánh giá hiệu suất nhân sự và kiểm soát chất lượng kỹ sư phần mềm
            tại <strong>CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ (DIGIMATE JSC)</strong>.
          </p>

          <h3>1. Cơ Chế 4 Trụ Cột Đánh Giá KPI (4-Pillar Appraisal Framework)</h3>
          <table>
            <thead>
              <tr>
                <th>Trụ cột</th>
                <th style="text-align:center;">Trọng số</th>
                <th>Chỉ số Đánh giá</th>
                <th>Ngưỡng Chuẩn</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td><strong>Trụ cột 1: Giao phẩm &amp; Tiến độ (Delivery SLA)</strong></td>
                <td style="text-align:center;">35%</td>
                <td>Tỷ lệ hoàn thành Sprint (≥95%) và Giờ công Billable (140-180h/tháng).</td>
                <td>Đạt chuẩn SOW dự án.</td>
              </tr>
              <tr>
                <td><strong>Trụ cột 2: Chất lượng Kỹ thuật &amp; Kiến trúc</strong></td>
                <td style="text-align:center;">25%</td>
                <td>Tỷ lệ qua Code Review (≥95%), Zero-Regression (≥95%), Phạt 8đ/lỗi Production.</td>
                <td>Zero Critical Defects.</td>
              </tr>
              <tr>
                <td><strong>Trụ cột 3: Nghiệm thu Công việc B2B &amp; Tuân thủ SOP</strong></td>
                <td style="text-align:center;">20%</td>
                <td>Đánh giá CSAT từ Tech Lead/Khách hàng B2B (≥90) và Tuân thủ SOP/ISO 27001 (≥95).</td>
                <td>CSAT ≥ 90đ, SOP ≥ 95đ.</td>
              </tr>
              <tr>
                <td><strong>Trụ cột 4: Cổng Nâng cấp Kỹ năng Bắt buộc (Skill Gate)</strong></td>
                <td style="text-align:center;">20%</td>
                <td>Hoàn thành 100% chuyên đề kỹ năng bắt buộc theo cấp bậc kỹ sư.</td>
                <td>100% Certified (≥85đ/môn).</td>
              </tr>
            </tbody>
          </table>

          <h3>2. Quy Tắc Khóa Cổng Kỹ Năng Bắt Buộc (Mandatory Skill Upgrade Gate Cap Invariant)</h3>
          <ul>
            <li><strong>Chốt chặn Hạng S / Hạng A:</strong> Nếu kỹ sư có điểm công việc rất cao (raw ≥ 85.0đ) nhưng chưa hoàn thành 100% chuyên đề kỹ năng bắt buộc (có ít nhất 1 môn In Progress / Planned), hệ thống tự động khóa trần ở mức tối đa <strong>84.9đ (Hạng B)</strong>, không đủ điều kiện xét thăng cấp (promotion_eligible = False) và mức thưởng chuẩn 100%.</li>
            <li><strong>Mở khóa Tự động:</strong> Ngay khi chuyên đề kỹ năng còn thiếu được nghiệm thu và cấp chứng chỉ (action_certify_skill_upgrade), hệ thống tự động tính toán lại KPI, gỡ bỏ giới hạn trần và nâng hạng tương ứng (Hạng A 120% hoặc Hạng S 150% &amp; Đủ điều kiện thăng cấp).</li>
          </ul>

          <h3>3. Danh Mục 8 Chuyên Đề Kỹ Năng Kỹ Sư Phần Mềm Bắt Buộc (2026)</h3>
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>Mã Học phần</th>
                <th>Tên Chuyên đề &amp; Chuẩn Đầu ra (Definition of Done)</th>
                <th style="text-align:center;">Giờ Chuẩn</th>
                <th style="text-align:center;">Điểm Đạt</th>
                <th>Lệnh Kiểm định Tự động</th>
              </tr>
            </thead>
            <tbody>
              {tracks_tbody}
            </tbody>
          </table>
        </section>
        """
        return wrap_dgm_branded_html_document(
            body_html,
            title="SOP-DGM-10: Quy trình Đánh giá KPI Nhân sự, Nghiệm thu Công việc & Cổng Nâng cấp Kỹ năng Kỹ sư Phần mềm Bắt buộc",
            doc_code="SOP-DGM-10",
            sop_ref="SOP-DGM-10",
            classification="CORPORATE HR & ENGINEERING STANDARD",
            include_header=True,
        )

    @api.model
    def seed_dgm_kpi_and_skill_framework(self):
        SkillTrack = self.env['dgm.hr.skill.track'].sudo()
        SkillGate = self.env['dgm.hr.employee.skill.gate'].sudo()
        WorkReview = self.env['dgm.hr.work.review'].sudo()
        KpiEval = self.env['dgm.hr.kpi.evaluation'].sudo()
        Employee = self.env['hr.employee'].sudo()
        Document = self.env['documents.document'].sudo()
        Attachment = self.env['ir.attachment'].sudo()

        # 1. Seed 8 canonical skill tracks
        track_by_code = {}
        for tr_vals in CANONICAL_SKILL_TRACKS:
            vals = dict(tr_vals)
            vals['domain'] = vals.get('category', 'erp_owl')
            vals['training_hours'] = vals.get('required_hours', 24.0)
            vals['description'] = vals.get('curriculum_summary', '')
            vals['active'] = True
            existing_tr = SkillTrack.search([('code', '=', tr_vals['code'])], limit=1)
            if existing_tr:
                existing_tr.write(vals)
                track_by_code[tr_vals['code']] = existing_tr
            else:
                track_by_code[tr_vals['code']] = SkillTrack.create(vals)

        # 2. Seed Skill Gates, Work Reviews, and 2026-Q4 KPI Evaluations for all 9 DGM employees
        roster_Blueprints = [
            {
                'reg_no': 'DGM-001',
                'fallback_name': 'Lê Xuân Hoàng',
                'engineer_level': 'l5_principal',
                'tracks': [
                    ('SKL-ERP-OWL3', 'certified', 24.0, 98.0, 'ARCH-OWL3-2026-001'),
                    ('SKL-AI-MOJO', 'certified', 32.0, 97.0, 'ARCH-MOJO-2026-001'),
                    ('SKL-SEC-ISO27001', 'certified', 16.0, 99.0, 'ISO27001-BOARD-001'),
                ],
                'sprint_pct': 99.0,
                'billable_actual': 176.0,
                'billable_target': 160.0,
                'cr_pass': 99.0,
                'zero_reg': 99.0,
                'defects': 0,
                'csat': 99.0,
                'sop_comp': 100.0,
                'project': 'Insilos Sovereign ERP & AL2C Executive Architecture',
                'deliverables': 'Điều hành chiến lược sản phẩm Insilos Odoo 20, phê duyệt kiến trúc AL2C Lead-to-Cash và chuẩn hóa quản trị SOP-DGM-01..10.',
            },
            {
                'reg_no': 'DGM-002',
                'fallback_name': 'Nguyễn Hoài Ân',
                'engineer_level': 'l5_principal',
                'tracks': [
                    ('SKL-AI-MOJO', 'certified', 32.0, 99.0, 'MOJO-SIMD-2026-002'),
                    ('SKL-AI-RAG', 'certified', 24.0, 98.0, 'RAG-ENTAIL-2026-002'),
                    ('SKL-K8S-PG', 'certified', 28.0, 97.0, 'K8S-PGBOUNCER-002'),
                    ('SKL-SEC-ISO27001', 'certified', 16.0, 98.0, 'ISO27001-CTO-002'),
                ],
                'sprint_pct': 98.5,
                'billable_actual': 174.0,
                'billable_target': 160.0,
                'cr_pass': 99.0,
                'zero_reg': 98.5,
                'defects': 0,
                'csat': 98.0,
                'sop_comp': 100.0,
                'project': 'Mojo AI Engine, Sovereign RAG & K8s Production Cluster',
                'deliverables': 'Kiến trúc sư trưởng hệ thống Mojo AI, Grounded RAG Citation Contract và hạ tầng Kubernetes Zero-Downtime.',
            },
            {
                'reg_no': 'DGM-003',
                'fallback_name': 'Mai Thị Hồng Thắm',
                'engineer_level': 'l4_lead',
                'tracks': [
                    ('SKL-SEC-ISO27001', 'certified', 16.0, 98.0, 'ISO27701-FINHR-003'),
                    ('SKL-B2B-ACTIVATE', 'certified', 20.0, 96.0, 'FINOPS-MTI-003'),
                    ('SKL-ERP-OWL3', 'certified', 24.0, 92.0, 'HR-DASHBOARD-003'),
                ],
                'sprint_pct': 98.0,
                'billable_actual': 168.0,
                'billable_target': 160.0,
                'cr_pass': 96.0,
                'zero_reg': 97.0,
                'defects': 0,
                'csat': 98.0,
                'sop_comp': 100.0,
                'project': 'Statutory VN 2026 Payroll (VCB DigiBiz) & Decree 70 E-Invoicing',
                'deliverables': 'Chuẩn hóa bảng lương BHXH TZ0857G, xuất VCB DigiBiz 11 cột và đối soát hóa đơn điện tử 1C26TAA.',
            },
            {
                'reg_no': 'DGM-004',
                'fallback_name': 'Bùi Hữu Tài',
                'engineer_level': 'l3_senior',
                'tracks': [
                    ('SKL-B2B-ACTIVATE', 'certified', 20.0, 95.0, 'MTI-ONSITE-004'),
                    ('SKL-ERP-OWL3', 'certified', 24.0, 93.0, 'OWL3-COMP-004'),
                    ('SKL-K8S-PG', 'certified', 28.0, 91.0, 'PG-LOCK-004'),
                    ('SKL-SEC-ISO27001', 'certified', 16.0, 94.0, 'SEC-AUDIT-004'),
                ],
                'sprint_pct': 96.0,
                'billable_actual': 176.0,
                'billable_target': 160.0,
                'cr_pass': 95.0,
                'zero_reg': 96.0,
                'defects': 0,
                'csat': 96.0,
                'sop_comp': 100.0,
                'project': 'MTI Technology Dedicated ODC Engineering (DIGIMATE2401-001)',
                'deliverables': 'Phát triển microservices cốt lõi cho MTI Technology, đạt 100% SLA nghiệm thu chấm công và chất lượng code.',
            },
            {
                'reg_no': 'DGM-005',
                'fallback_name': 'Huỳnh Trần Quang Khánh',
                'engineer_level': 'l4_lead',
                'tracks': [
                    ('SKL-ERP-OWL3', 'certified', 24.0, 97.0, 'OWL3-HYBRID-005'),
                    ('SKL-ERP-SCSS-DARK', 'certified', 20.0, 96.0, 'DARK-BUNDLE-005'),
                    ('SKL-K8S-PG', 'certified', 28.0, 95.0, 'PG-VIEW-BRIDGE-005'),
                    ('SKL-QA-PLAYWRIGHT', 'certified', 24.0, 96.0, 'E2E-DUAL-THEME-005'),
                ],
                'sprint_pct': 97.5,
                'billable_actual': 172.0,
                'billable_target': 160.0,
                'cr_pass': 98.0,
                'zero_reg': 98.0,
                'defects': 0,
                'csat': 97.0,
                'sop_comp': 100.0,
                'project': 'Insilos Core WebClient, OWL 3 Runtime & Dual-Theme Architecture',
                'deliverables': 'Dẫn dắt kỹ thuật nền tảng OWL 3, Sovereign Dark Mode và hệ thống kiểm định tự động 6 tầng.',
            },
            {
                'reg_no': 'DGM-006',
                'fallback_name': 'Ngô Thanh Lộc',
                'engineer_level': 'l3_senior',
                'tracks': [
                    ('SKL-B2B-ACTIVATE', 'certified', 20.0, 91.0, 'MTI-DELIVERY-006'),
                    ('SKL-ERP-SCSS-DARK', 'certified', 20.0, 89.0, 'SCSS-CLEAN-006'),
                    ('SKL-SEC-ISO27001', 'certified', 16.0, 92.0, 'ISO27001-DEV-006'),
                ],
                'sprint_pct': 91.0,
                'billable_actual': 164.0,
                'billable_target': 160.0,
                'cr_pass': 90.0,
                'zero_reg': 91.0,
                'defects': 0,
                'csat': 90.0,
                'sop_comp': 96.0,
                'project': 'MTI Technology Dedicated ODC Engineering (DIGIMATE2401-001)',
                'deliverables': 'Thực hiện đầy đủ các gói công việc Frontend/Backend cho dự án MTI Technology đúng tiến độ cam kết.',
            },
            {
                'reg_no': 'DGM-007',
                'fallback_name': 'Lê Cao Bảo Phúc',
                'engineer_level': 'l2_mid',
                'tracks': [
                    ('SKL-B2B-ACTIVATE', 'certified', 20.0, 93.0, 'MTI-SPRINT-007'),
                    ('SKL-SEC-ISO27001', 'certified', 16.0, 94.0, 'SEC-PASS-007'),
                    ('SKL-ERP-OWL3', 'in_progress', 18.0, 80.0, 'LAB-OWL3-WIP-007'),
                ],
                'sprint_pct': 95.0,
                'billable_actual': 168.0,
                'billable_target': 160.0,
                'cr_pass': 94.0,
                'zero_reg': 95.0,
                'defects': 0,
                'csat': 94.0,
                'sop_comp': 98.0,
                'project': 'MTI Technology Onsite Delivery & Insilos Portal Integration',
                'deliverables': 'Hiệu suất giao phẩm dự án rất tốt (raw >= 90), đang hoàn thiện nốt bài lab bắt buộc SKL-ERP-OWL3 (18/24h) để mở khóa Hạng A/S.',
            },
            {
                'reg_no': 'DGM-008',
                'fallback_name': 'Thái Nguyễn Đăng Khoa',
                'engineer_level': 'l1_junior',
                'tracks': [
                    ('SKL-SEC-ISO27001', 'certified', 16.0, 92.0, 'SEC-JUNIOR-008'),
                    ('SKL-ERP-SCSS-DARK', 'certified', 20.0, 90.0, 'DARK-SCSS-008'),
                    ('SKL-QA-PLAYWRIGHT', 'in_progress', 18.0, 80.0, 'PLAYWRIGHT-WIP-008'),
                ],
                'sprint_pct': 94.0,
                'billable_actual': 164.0,
                'billable_target': 160.0,
                'cr_pass': 93.0,
                'zero_reg': 94.0,
                'defects': 0,
                'csat': 93.0,
                'sop_comp': 98.0,
                'project': 'Insilos UI Components & Automated E2E Verification Suite',
                'deliverables': 'Hoàn thành tốt các tác vụ phát triển giao diện, cần hoàn tất chứng chỉ bắt buộc SKL-QA-PLAYWRIGHT để mở khóa giới hạn Hạng B.',
            },
            {
                'reg_no': 'DGM-009',
                'fallback_name': 'Trần Văn Huỳnh Phố',
                'engineer_level': 'l3_senior',
                'tracks': [
                    ('SKL-B2B-ACTIVATE', 'certified', 20.0, 97.0, 'AIFIN-SLA-009'),
                    ('SKL-ERP-OWL3', 'certified', 24.0, 95.0, 'OWL3-AIFIN-009'),
                    ('SKL-K8S-PG', 'certified', 28.0, 96.0, 'PG-PERF-009'),
                    ('SKL-SEC-ISO27001', 'certified', 16.0, 96.0, 'ISO27001-AIFIN-009'),
                ],
                'sprint_pct': 98.0,
                'billable_actual': 176.0,
                'billable_target': 160.0,
                'cr_pass': 97.0,
                'zero_reg': 98.0,
                'defects': 0,
                'csat': 98.0,
                'sop_comp': 100.0,
                'project': 'AIfin Company Global Staff Augmentation (DIGIMATE-AIFIN-VN_2610-001)',
                'deliverables': 'Kỹ sư chủ lực dự án AIfin Global, hoàn thành xuất sắc 100% mốc bàn giao kỹ thuật và 4/4 chứng chỉ kỹ năng bắt buộc.',
            },
        ]

        all_emps = Employee.search([('active', '=', True)])
        emp_by_reg = {e.registration_number: e for e in all_emps if e.registration_number}

        seeded_evals = []
        for bp in roster_Blueprints:
            emp = emp_by_reg.get(bp['reg_no'])
            if not emp:
                emp = Employee.search([('name', 'ilike', bp['fallback_name'])], limit=1)
            if not emp:
                continue

            emp_vals = {}
            if emp.dgm_engineer_level != bp['engineer_level']:
                emp_vals['dgm_engineer_level'] = bp['engineer_level']
            if not getattr(emp, 'dgm_employee_code', None):
                emp_vals['dgm_employee_code'] = emp.registration_number or bp['reg_no']
            if emp_vals:
                emp.write(emp_vals)

            # Upsert skill gates for this employee
            for tr_code, g_state, comp_h, sc_val, ev_ref in bp['tracks']:
                tr_rec = track_by_code.get(tr_code)
                if not tr_rec:
                    continue
                existing_gate = SkillGate.search(
                    [
                        ('employee_id', '=', emp.id),
                        ('skill_track_id', '=', tr_rec.id),
                    ],
                    limit=1,
                )
                gate_vals = {
                    'employee_id': emp.id,
                    'skill_track_id': tr_rec.id,
                    'current_level': 4 if g_state == 'certified' else 3,
                    'target_level': 4,
                    'completed_hours': comp_h,
                    'assessment_score': sc_val,
                    'deadline_date': _safe_to_date('2026-12-15'),
                    'completed_date': _safe_today() if g_state == 'certified' else False,
                    'certified_date': _safe_today() if g_state == 'certified' else False,
                    'evidence_ref': ev_ref,
                    'evidence_artifact': ev_ref,
                    'state': g_state,
                    'is_mandatory_for_next_level': True,
                    'is_mandatory': True,
                    'active': True,
                }
                if existing_gate:
                    existing_gate.write(gate_vals)
                else:
                    SkillGate.create(gate_vals)

            # Upsert 2026-Q4 KPI Evaluation
            eval_name = f"KPI-2026-Q4-{bp['reg_no']}"
            existing_eval = KpiEval.search(
                [
                    ('employee_id', '=', emp.id),
                    ('period_code', '=', '2026-Q4'),
                ],
                limit=1,
            )
            eval_vals = {
                'name': eval_name,
                'employee_id': emp.id,
                'period_code': '2026-Q4',
                'engineer_level': bp['engineer_level'],
                'kpi_sprint_completion_pct': bp['sprint_pct'],
                'kpi_billable_hours_actual': bp['billable_actual'],
                'kpi_billable_hours_target': bp['billable_target'],
                'kpi_code_review_pass_rate': bp['cr_pass'],
                'kpi_zero_regression_score': bp['zero_reg'],
                'kpi_production_defect_count': bp['defects'],
                'collaboration_score': bp['csat'],
                'kpi_client_csat_score': bp['csat'],
                'sop_compliance_score': bp['sop_comp'],
                'kpi_sop_compliance_score': bp['sop_comp'],
                'work_evaluation_summary': bp['deliverables'],
                'training_roadmap_note': (
                    'Đã hoàn thành 100% cổng kỹ năng bắt buộc trong kỳ 2026-Q4.'
                    if all(t[1] == 'certified' for t in bp['tracks'])
                    else 'Yêu cầu hoàn thành học phần bắt buộc đang In Progress trước hạn SLA 15/12/2026 để mở khóa Hạng A/S.'
                ),
                'state': 'approved',
                'active': True,
            }
            if existing_eval:
                existing_eval.write(eval_vals)
                ev_rec = existing_eval
            else:
                ev_rec = KpiEval.create(eval_vals)

            # Upsert Work Review linked to this evaluation
            wr_name = f"WRK-2026-Q4-{bp['reg_no']}"
            existing_wr = WorkReview.search(
                [
                    ('employee_id', '=', emp.id),
                    ('name', '=', wr_name),
                ],
                limit=1,
            )
            wr_vals = {
                'name': wr_name,
                'kpi_evaluation_id': ev_rec.id,
                'evaluation_id': ev_rec.id,
                'employee_id': emp.id,
                'project_name': bp['project'],
                'sprint_or_milestone': '2026-Q4 (Tháng 10–12/2026)',
                'deliverables_completed': bp['deliverables'],
                'task_completion_rate': bp['sprint_pct'],
                'code_quality_score': bp['cr_pass'],
                'score': bp['cr_pass'],
                'feedback': bp['deliverables'],
                'reviewer_id': 2,
                'reviewer_name': 'Lê Xuân Hoàng — Chủ tịch HĐQT & Tổng Giám đốc',
                'review_type': 'lead',
                'review_date': _safe_today(),
                'state': 'verified',
                'active': True,
            }
            if existing_wr:
                existing_wr.write(wr_vals)
            else:
                WorkReview.create(wr_vals)

            ev_rec._compute_kpi_scores_and_skill_gate()
            ev_rec.action_generate_kpi_evaluation_document()
            emp._compute_dgm_kpi_summary()
            seeded_evals.append(ev_rec)

        # 3. Create/update master SOP-DGM-10 branded HTML document in HR folder and SOP folder
        master_doc_filename = "SOP-DGM-10_KPI_Danh_Gia_Nhan_Su_Va_Khung_Nang_Luc_Ky_Su_Phan_Mem_2026.html"
        master_html = self.render_sop_dgm_10_master_html()
        master_b64 = base64.b64encode(master_html.encode('utf-8'))

        hr_folder = Document.browse(3224).exists()
        if not hr_folder or getattr(hr_folder, 'type', '') != 'folder' or not getattr(hr_folder, 'active', False):
            hr_folder = Document.search(
                [
                    ('type', '=', 'folder'),
                    ('active', '=', True),
                    '|',
                    ('name', 'ilike', '01. Pháp lý'),
                    ('name', 'ilike', 'Nhân Sự'),
                ],
                order='id asc',
                limit=1,
            )

        sop_folder = Document.browse(4704).exists()
        if not sop_folder or getattr(sop_folder, 'type', '') != 'folder' or not getattr(sop_folder, 'active', False):
            sop_folder = Document.search(
                [
                    ('type', '=', 'folder'),
                    ('active', '=', True),
                    '|',
                    ('name', 'ilike', '07. Quy trình'),
                    ('name', 'ilike', 'Quy Trình'),
                ],
                order='id asc',
                limit=1,
            )

        for folder in [f for f in (hr_folder, sop_folder) if f]:
            existing_doc = Document.search(
                [
                    ('folder_id', '=', folder.id),
                    ('name', '=', master_doc_filename),
                ],
                limit=1,
            )
            if existing_doc:
                if existing_doc.attachment_id:
                    existing_doc.attachment_id.with_context(no_document=True).write({
                        'datas': master_b64,
                        'name': master_doc_filename,
                        'mimetype': 'text/html',
                    })
                existing_doc.write({
                    'name': master_doc_filename,
                    'owner_id': False,
                    'access_internal': 'edit',
                    'active': True,
                })
            else:
                att = Attachment.create({
                    'name': master_doc_filename,
                    'type': 'binary',
                    'datas': master_b64,
                    'mimetype': 'text/html',
                    'res_model': 'documents.document',
                    'res_id': 0,
                })
                doc = Document.create({
                    'name': master_doc_filename,
                    'folder_id': folder.id,
                    'owner_id': False,
                    'type': 'binary',
                    'attachment_id': att.id,
                    'access_internal': 'edit',
                    'access_via_link': 'view',
                    'active': True,
                })
                att.write({'res_id': doc.id})

        # 4. Upsert SOP-DGM-10 Knowledge Article with Drive Logo Brand Footer
        if 'knowledge.article' in self.env:
            Article = self.env['knowledge.article'].sudo()
            kb_title = "SOP-DGM-10: Quy trình Đánh giá KPI Nhân sự, Nghiệm thu Công việc & Cổng Nâng cấp Kỹ năng Kỹ sư Phần mềm Bắt buộc"
            existing_kb = Article.search([('name', 'ilike', 'SOP-DGM-10%')], limit=1)
            if existing_kb:
                existing_kb.write({'name': kb_title, 'body': master_html, 'active': True})
            else:
                Article.create({'name': kb_title, 'body': master_html, 'internal_permission': 'write'})

        return {
            'skill_tracks': len(track_by_code),
            'employees_evaluated': len(seeded_evals),
            'master_doc_filename': master_doc_filename,
        }


class HrEmployeeKpiSkillExtension(models.Model):
    _inherit = 'hr.employee'

    dgm_employee_code = fields.Char(
        string='Mã Nhân viên DGM',
        compute='_compute_dgm_employee_code',
        store=True,
        index=True,
    )
    dgm_engineer_level = fields.Selection(
        ENGINEER_LEVEL_SELECTION,
        string='Cấp bậc Kỹ sư / Chuyên môn (SOP-DGM-10)',
        default='l3_senior',
        index=True,
    )
    dgm_skill_gate_ids = fields.One2many(
        'dgm.hr.employee.skill.gate',
        'employee_id',
        string='Lộ trình Nâng cấp Kỹ năng Bắt buộc (SOP-DGM-10)',
    )
    dgm_kpi_evaluation_ids = fields.One2many(
        'dgm.hr.kpi.evaluation',
        'employee_id',
        string='Hồ sơ Đánh giá KPI & Hiệu suất (SOP-DGM-10)',
    )
    dgm_work_review_ids = fields.One2many(
        'dgm.hr.work.review',
        'employee_id',
        string='Đánh giá Công việc & Dự án (SOP-DGM-10)',
    )
    dgm_current_kpi_score = fields.Float(
        string='Điểm KPI Hiện tại (/100)',
        compute='_compute_dgm_kpi_summary',
        store=True,
    )
    dgm_latest_kpi_score = fields.Float(
        string='Điểm KPI Kỳ Gần nhất (/100)',
        compute='_compute_dgm_kpi_summary',
        store=True,
    )
    dgm_current_kpi_rank = fields.Selection(
        RANK_GRADE_SELECTION,
        string='Xếp hạng KPI Hiện tại',
        compute='_compute_dgm_kpi_summary',
        store=True,
    )
    dgm_latest_kpi_grade = fields.Selection(
        RANK_GRADE_SELECTION,
        string='Xếp hạng KPI Kỳ Gần nhất',
        compute='_compute_dgm_kpi_summary',
        store=True,
    )
    dgm_mandatory_skill_pct = fields.Float(
        string='Tỷ lệ Hoàn thành Kỹ năng Bắt buộc (%)',
        compute='_compute_dgm_kpi_summary',
        store=True,
    )
    dgm_skill_gate_passed = fields.Boolean(
        string='Đạt 100% Cổng Kỹ năng Bắt buộc',
        compute='_compute_dgm_kpi_summary',
        store=True,
    )
    dgm_skill_gate_capped = fields.Boolean(
        string='Đang Bị Giới hạn Hạng do Chưa Xong Kỹ năng',
        compute='_compute_dgm_kpi_summary',
        store=True,
    )
    dgm_promotion_eligible = fields.Boolean(
        string='Đủ Điều kiện Thăng cấp & Thưởng Vượt khung',
        compute='_compute_dgm_kpi_summary',
        store=True,
    )

    @api.depends('registration_number', 'barcode')
    def _compute_dgm_employee_code(self):
        for rec in _safe_iter_records(self):
            rec.dgm_employee_code = rec.registration_number or rec.barcode or (f"DGM-{rec.id:03d}" if rec.id else "")

    @api.depends(
        'dgm_kpi_evaluation_ids.weighted_kpi_score',
        'dgm_kpi_evaluation_ids.final_kpi_score',
        'dgm_kpi_evaluation_ids.rank_grade',
        'dgm_kpi_evaluation_ids.mandatory_skill_completion_pct',
        'dgm_kpi_evaluation_ids.all_mandatory_skills_completed',
        'dgm_kpi_evaluation_ids.skill_gate_capped',
        'dgm_kpi_evaluation_ids.promotion_eligible',
        'dgm_skill_gate_ids.state',
        'dgm_skill_gate_ids.is_mandatory_for_next_level',
        'dgm_skill_gate_ids.is_mandatory',
        'dgm_skill_gate_ids.active',
    )
    def _compute_dgm_kpi_summary(self):
        for emp in _safe_iter_records(self):
            emp.dgm_current_kpi_score = 0.0
            emp.dgm_latest_kpi_score = 0.0
            emp.dgm_current_kpi_rank = 'tier_b'
            emp.dgm_latest_kpi_grade = 'tier_b'
            emp.dgm_mandatory_skill_pct = 0.0
            emp.dgm_skill_gate_passed = False
            emp.dgm_skill_gate_capped = False
            emp.dgm_promotion_eligible = False

            evals = _safe_iter_records(getattr(emp, 'dgm_kpi_evaluation_ids', []))
            active_evals = [e for e in evals if getattr(e, 'active', True)]
            if active_evals:
                latest = active_evals[0]
                score_val = float(getattr(latest, 'weighted_kpi_score', 0.0) or getattr(latest, 'final_kpi_score', 0.0) or 0.0)
                rank_val = getattr(latest, 'rank_grade', 'tier_b') or 'tier_b'
                emp.dgm_current_kpi_score = score_val
                emp.dgm_latest_kpi_score = score_val
                emp.dgm_current_kpi_rank = rank_val
                emp.dgm_latest_kpi_grade = rank_val
                emp.dgm_mandatory_skill_pct = float(
                    getattr(latest, 'mandatory_skill_completion_pct', 0.0) or 0.0
                )
                emp.dgm_skill_gate_passed = bool(
                    getattr(latest, 'all_mandatory_skills_completed', False)
                )
                emp.dgm_skill_gate_capped = bool(getattr(latest, 'skill_gate_capped', False))
                emp.dgm_promotion_eligible = bool(getattr(latest, 'promotion_eligible', False))
            else:
                gates = _safe_iter_records(getattr(emp, 'dgm_skill_gate_ids', []))
                active_gates = [g for g in gates if getattr(g, 'active', True)]
                mand = [
                    g for g in active_gates
                    if getattr(g, 'is_mandatory_for_next_level', False) or getattr(g, 'is_mandatory', True)
                ]
                cert = [g for g in mand if getattr(g, 'state', '') == 'certified']
                if mand:
                    emp.dgm_mandatory_skill_pct = round((len(cert) / len(mand)) * 100.0, 2)
                    emp.dgm_skill_gate_passed = len(cert) == len(mand)
                else:
                    emp.dgm_mandatory_skill_pct = 100.0
                    emp.dgm_skill_gate_passed = True

    def get_dgm_kpi_skill_dashboard_payload(self):
        emp = _safe_iter_records(self)[0]
        evals = _safe_iter_records(getattr(emp, 'dgm_kpi_evaluation_ids', []))
        active_evals = [e for e in evals if getattr(e, 'active', True)]
        latest = active_evals[0] if active_evals else (evals[0] if evals else None)
        gates = [g for g in _safe_iter_records(getattr(emp, 'dgm_skill_gate_ids', [])) if getattr(g, 'active', True)]
        reviews = [w for w in _safe_iter_records(getattr(emp, 'dgm_work_review_ids', [])) if getattr(w, 'active', True)]

        return {
            'employee_id': getattr(emp, 'id', 0),
            'employee_code': getattr(emp, 'dgm_employee_code', '') or getattr(emp, 'registration_number', '') or 'DGM-EMP',
            'employee_name': getattr(emp, 'name', ''),
            'engineer_level': getattr(emp, 'dgm_engineer_level', 'l3_senior'),
            'period_code': getattr(latest, 'period_code', '2026-Q4') if latest else '2026-Q4',
            'raw_weighted_score': float(getattr(latest, 'raw_weighted_score', 0.0) or 0.0) if latest else 0.0,
            'current_kpi_score': float(getattr(emp, 'dgm_current_kpi_score', 0.0) or 0.0),
            'current_kpi_rank': getattr(emp, 'dgm_current_kpi_rank', 'tier_b') or 'tier_b',
            'mandatory_skill_total': int(getattr(latest, 'mandatory_skill_total', len(gates)) or 0) if latest else len(gates),
            'mandatory_skill_certified': int(getattr(latest, 'mandatory_skill_certified', 0) or 0) if latest else 0,
            'mandatory_skill_pct': float(getattr(emp, 'dgm_mandatory_skill_pct', 0.0) or 0.0),
            'all_mandatory_skills_completed': bool(getattr(emp, 'dgm_skill_gate_passed', False)),
            'skill_gate_capped': bool(getattr(emp, 'dgm_skill_gate_capped', False)),
            'promotion_eligible': bool(getattr(emp, 'dgm_promotion_eligible', False)),
            'bonus_multiplier_pct': float(getattr(latest, 'bonus_multiplier_pct', 100.0) or 100.0) if latest else 100.0,
            'pillars': {
                'delivery_score': float(getattr(latest, 'delivery_score', 0.0) or getattr(latest, 'score_delivery', 0.0) or 0.0) if latest else 0.0,
                'quality_score': float(getattr(latest, 'quality_score', 0.0) or getattr(latest, 'score_quality', 0.0) or 0.0) if latest else 0.0,
                'score_work_eval': float(getattr(latest, 'score_work_eval', 0.0) or 0.0) if latest else 0.0,
                'score_skill_upgrade': float(getattr(latest, 'score_skill_upgrade', 0.0) or 0.0) if latest else 0.0,
                'score_delivery': float(getattr(latest, 'score_delivery', 0.0) or 0.0) if latest else 0.0,
                'score_quality': float(getattr(latest, 'score_quality', 0.0) or 0.0) if latest else 0.0,
            },
            'skill_gates': [
                {
                    'id': getattr(g, 'id', 0),
                    'track_code': getattr(g, 'track_code', ''),
                    'track_name': getattr(g, 'track_name', ''),
                    'category': getattr(g, 'category', ''),
                    'domain': getattr(g, 'domain', ''),
                    'is_mandatory': bool(getattr(g, 'is_mandatory', True)),
                    'is_mandatory_for_next_level': bool(getattr(g, 'is_mandatory_for_next_level', True)),
                    'completed_hours': float(getattr(g, 'completed_hours', 0.0) or 0.0),
                    'required_hours': float(getattr(g, 'required_hours', 24.0) or 24.0),
                    'assessment_score': float(getattr(g, 'assessment_score', 0.0) or 0.0),
                    'passing_score': float(getattr(g, 'passing_score', 85.0) or 85.0),
                    'progress_pct': float(getattr(g, 'progress_pct', 0.0) or 0.0),
                    'state': getattr(g, 'state', 'assigned'),
                    'evidence_ref': getattr(g, 'evidence_ref', ''),
                    'evidence_artifact': getattr(g, 'evidence_artifact', ''),
                }
                for g in gates
            ],
            'work_reviews': [
                {
                    'id': getattr(w, 'id', 0),
                    'name': getattr(w, 'name', ''),
                    'project_name': getattr(w, 'project_name', ''),
                    'sprint_or_milestone': getattr(w, 'sprint_or_milestone', ''),
                    'deliverables_completed': getattr(w, 'deliverables_completed', ''),
                    'task_completion_rate': float(getattr(w, 'task_completion_rate', 0.0) or 0.0),
                    'code_quality_score': float(getattr(w, 'code_quality_score', 0.0) or 0.0),
                    'score': float(getattr(w, 'score', 0.0) or 0.0),
                    'reviewer_name': getattr(w, 'reviewer_name', ''),
                    'state': getattr(w, 'state', 'verified'),
                }
                for w in reviews
            ],
        }
