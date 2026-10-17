# -*- coding: utf-8 -*-
"""
SOP-DGM-11: PDCA Project Templates, 360-Degree HR Appraisals & Software Enterprise OKR Cascade.
===============================================================================================
Models:
1. `dgm.okr.objective`: Software Enterprise OKR Objective (Company -> Department/Squad -> Individual)
2. `dgm.okr.key.result`: Measurable Key Result (KR) with check-in cascade
3. `dgm.hr.appraisal.sheet`: 360-Degree HR Appraisal & 9-Box Talent Calibration Sheet (PDCA)
4. `dgm.project.pdca.template`: Standardized Software Project PDCA Template
"""
import logging
from odoo import api, fields, models

from .dgm_hr_kpi_skill import _safe_iter_records

_logger = logging.getLogger(__name__)


OKR_TIER_SELECTION = [
    ('company', 'Cấp Công ty (Company Strategic OKR — Digimate / Innoria)'),
    ('department', 'Cấp Khối / Squad Kỹ thuật (Engineering / B2B Onsite / GRC Squad OKR)'),
    ('individual', 'Cấp Cá nhân Kỹ sư / Nhân sự (Individual Engineer OKR)'),
]

PDCA_STAGE_SELECTION = [
    ('plan', 'P (Plan) — Hoạch định Mục tiêu & Trọng số KR'),
    ('do', 'D (Do) — Thực thi Sprint, Dự án & Nâng cấp Kỹ năng'),
    ('check', 'C (Check) — Đo lường KR, Kiểm toán Chất lượng & Đánh giá 360°'),
    ('act', 'A (Act) — Chuẩn hóa Quy trình, Cải tiến & Chốt Hạng Appraisal'),
]

OKR_CONFIDENCE_SELECTION = [
    ('on_track', '🟢 On Track (Độ tự tin cao ≥ 0.70)'),
    ('at_risk', '🟡 At Risk (Cần can thiệp PDCA 0.40 – 0.69)'),
    ('off_track', '🔴 Off Track (Nguy cơ lệch mục tiêu < 0.40)'),
]

KR_METRIC_UNIT_SELECTION = [
    ('pct', 'Tỷ lệ Phần trăm (%)'),
    ('hours', 'Giờ công Billable (Hours)'),
    ('vnd_m', 'Doanh thu / Giá trị (Triệu VNĐ)'),
    ('count', 'Số lượng Giao phẩm / PR / Chứng chỉ'),
    ('ms', 'Độ trễ / Hiệu năng (ms)'),
]

CALIBRATION_BOX_SELECTION = [
    ('box_9_star', '9-Box [9] Top Talent / Future Leader (Hiệu suất Cao • Tiềm năng Cao — Mở khóa Thăng cấp)'),
    ('box_8_high_perf', '9-Box [8] High Impact Engineer (Hiệu suất Cao • Nòng cốt Kỹ thuật)'),
    ('box_6_emerging', '9-Box [6] Emerging Potential (Tiềm năng Cao • Cần Hoàn tất Cổng Kỹ năng Bắt buộc)'),
    ('box_5_core', '9-Box [5] Solid Core Contributor (Đạt chuẩn Ổn định)'),
    ('box_2_pip', '9-Box [2] Action Required / PIP 30 Ngày (Cần Đào tạo Kèm cặp)'),
]

APPRAISAL_STATE_SELECTION = [
    ('self_review', 'Bước 1: Nhân sự Tự đánh giá (Plan/Do)'),
    ('360_feedback', 'Bước 2: Thu thập Phản hồi 360° & Khách hàng B2B (Check)'),
    ('manager_calibration', 'Bước 3: Tech Lead & HR Hiệu chuẩn 9-Box (Check/Act)'),
    ('signed_off', 'Bước 4: Ban Giám đốc Phê duyệt & Chốt Đãi ngộ (Act Completed)'),
]

DELIVERY_METHODOLOGY_SELECTION = [
    ('sap_activate_pdca', 'SAP Activate 5-Phase + Vòng lặp PDCA (Trọn gói Turnkey ERP — KTT/Swarovski)'),
    ('b2b_onsite_agile', 'Agile Scrum + B2B Onsite SLA 140-180h (Phái cử Kỹ sư — MTI/AIfin)'),
    ('ai_mojo_rd', 'AI Agentic & Mojo Kernel R&D Loop (Phát triển Sản phẩm Lõi — Innoria/Canva)'),
    ('iso_grc_audit', 'ISO/IEC 27001 & 27701 Security Compliance PDCA (Kiểm toán & Bảo mật)'),
]


class DgmOkrObjective(models.Model):
    _name = 'dgm.okr.objective'
    _description = 'DGM Software Enterprise OKR Objective (PDCA)'
    _order = 'period_code desc, okr_tier asc, code asc, id asc'

    code = fields.Char(
        string='Mã Mục tiêu (OKR Code)',
        required=True,
        index=True,
        default='OKR-2026-Q4-C01',
    )
    name = fields.Char(
        string='Mục tiêu Chiến lược (Objective)',
        required=True,
    )
    period_code = fields.Char(
        string='Kỳ OKR (Quý / Năm)',
        default='2026-Q4',
        required=True,
        index=True,
    )
    okr_tier = fields.Selection(
        OKR_TIER_SELECTION,
        required=True,
        default='company',
        index=True,
        string='Cấp độ Mục tiêu (OKR Tier)',
    )
    parent_objective_id = fields.Many2one(
        'dgm.okr.objective',
        string='OKR Cấp trên Liên kết (Parent Alignment)',
        ondelete='restrict',
        index=True,
    )
    child_objective_ids = fields.One2many(
        'dgm.okr.objective',
        'parent_objective_id',
        string='OKR Cấp dưới',
    )
    owner_employee_id = fields.Many2one(
        'hr.employee',
        string='Chủ sở hữu Mục tiêu (OKR Owner)',
        index=True,
    )
    department_name = fields.Char(
        string='Khối / Phòng ban',
    )
    project_template_code = fields.Char(
        string='Mã Mẫu Dự án Liên kết (Project Template Ref)',
    )
    pdca_stage = fields.Selection(
        PDCA_STAGE_SELECTION,
        default='check',
        required=True,
        index=True,
        string='Giai đoạn Vòng lặp PDCA',
    )
    key_result_ids = fields.One2many(
        'dgm.okr.key.result',
        'objective_id',
        string='Kết quả Then chốt (Key Results)',
    )
    progress_pct = fields.Float(
        compute='_compute_okr_metrics',
        store=True,
        string='Tiến độ Hoàn thành OKR (%)',
    )
    okr_score = fields.Float(
        compute='_compute_okr_metrics',
        store=True,
        string='Điểm OKR Chuẩn Google/Intel (0.00 – 1.00)',
    )
    confidence_level = fields.Selection(
        OKR_CONFIDENCE_SELECTION,
        compute='_compute_okr_metrics',
        store=True,
        string='Mức độ Tự tin Đạt Mục tiêu (Confidence)',
    )
    pdca_retrospective = fields.Text(
        string='Nhật ký Cải tiến Liên tục (PDCA Check & Act Notes)',
    )
    active = fields.Boolean(default=True)

    @api.depends(
        'key_result_ids.progress_pct',
        'key_result_ids.kr_score',
        'key_result_ids.weight',
    )
    def _compute_okr_metrics(self):
        for rec in _safe_iter_records(self):
            rec.progress_pct = 0.0
            rec.okr_score = 0.0
            rec.confidence_level = 'off_track'

            krs = _safe_iter_records(getattr(rec, 'key_result_ids', []))
            if krs:
                total_w = sum(max(0.0, float(getattr(kr, 'weight', 0.0) or 0.0)) for kr in krs)
                if total_w > 0:
                    prog = sum(
                        float(getattr(kr, 'progress_pct', 0.0) or 0.0)
                        * max(0.0, float(getattr(kr, 'weight', 0.0) or 0.0))
                        for kr in krs
                    ) / total_w
                else:
                    prog = sum(float(getattr(kr, 'progress_pct', 0.0) or 0.0) for kr in krs) / len(krs)
                prog = max(0.0, min(100.0, prog))
                score = round(prog / 100.0, 2)
                rec.progress_pct = round(prog, 2)
                rec.okr_score = score
                if score >= 0.70:
                    rec.confidence_level = 'on_track'
                elif score >= 0.40:
                    rec.confidence_level = 'at_risk'
                else:
                    rec.confidence_level = 'off_track'


class DgmOkrKeyResult(models.Model):
    _name = 'dgm.okr.key.result'
    _description = 'DGM Software Enterprise Key Result (KR)'
    _order = 'objective_id, code asc, id asc'

    code = fields.Char(
        string='Mã Kết quả Then chốt (KR Code)',
        required=True,
        index=True,
        default='KR-2026-Q4-01',
    )
    name = fields.Char(
        string='Kết quả Then chốt Đo lường được (Measurable Key Result)',
        required=True,
    )
    objective_id = fields.Many2one(
        'dgm.okr.objective',
        string='Mục tiêu OKR',
        required=True,
        ondelete='cascade',
        index=True,
    )
    owner_employee_id = fields.Many2one(
        'hr.employee',
        string='Nhân sự Chịu trách nhiệm',
        index=True,
    )
    metric_unit = fields.Selection(
        KR_METRIC_UNIT_SELECTION,
        default='pct',
        required=True,
        string='Đơn vị Đo lường',
    )
    start_value = fields.Float(
        default=0.0,
        string='Giá trị Khởi đầu (Baseline)',
    )
    target_value = fields.Float(
        required=True,
        default=100.0,
        string='Giá trị Mục tiêu (Target)',
    )
    current_value = fields.Float(
        default=0.0,
        string='Giá trị Đạt được Hiện tại (Actual)',
    )
    weight = fields.Float(
        default=50.0,
        string='Trọng số KR (%)',
    )
    progress_pct = fields.Float(
        compute='_compute_kr_progress',
        store=True,
        string='Tiến độ KR (%)',
    )
    kr_score = fields.Float(
        compute='_compute_kr_progress',
        store=True,
        string='Điểm KR (0.00 – 1.00)',
    )
    linked_skill_track_id = fields.Many2one(
        'dgm.hr.skill.track',
        string='Kỹ năng Bắt buộc Liên kết',
    )
    evidence_ref = fields.Char(
        string='Minh chứng Đo lường (Commit / E-Invoice / Report)',
    )

    @api.depends('start_value', 'target_value', 'current_value', 'metric_unit')
    def _compute_kr_progress(self):
        for rec in _safe_iter_records(self):
            rec.progress_pct = 0.0
            rec.kr_score = 0.0

            start_v = float(getattr(rec, 'start_value', 0.0) or 0.0)
            target_v = float(getattr(rec, 'target_value', 100.0) or 100.0)
            curr_v = float(getattr(rec, 'current_value', 0.0) or 0.0)

            if target_v != start_v:
                if target_v > start_v:
                    ratio = (curr_v - start_v) / (target_v - start_v)
                else:
                    ratio = (start_v - curr_v) / (start_v - target_v)
            else:
                ratio = 1.0 if curr_v >= target_v else 0.0

            pct = max(0.0, min(100.0, ratio * 100.0))
            rec.progress_pct = round(pct, 2)
            rec.kr_score = round(pct / 100.0, 2)

    def action_update_kr_checkin(self, new_value=None, evidence_ref=None, pdca_stage=None):
        """
        PDCA Check-in action: updates `current_value` (and optional `evidence_ref` / `pdca_stage`),
        recomputes `progress_pct` & `kr_score`, cascades recomputation to `objective_id` (and parent),
        and syncs the employee's `dgm.hr.appraisal.sheet` and `dgm.hr.kpi.evaluation`.
        """
        emp_ids = set()
        obj_ids = set()
        for rec in _safe_iter_records(self):
            vals = {}
            if new_value is not None:
                vals['current_value'] = float(new_value)
            if evidence_ref is not None:
                vals['evidence_ref'] = str(evidence_ref)
            if vals:
                if hasattr(rec, 'write') and callable(rec.write):
                    rec.write(vals)
                else:
                    for k, v in vals.items():
                        setattr(rec, k, v)
            rec._compute_kr_progress()

            obj = getattr(rec, 'objective_id', None)
            if obj:
                if pdca_stage:
                    if hasattr(obj, 'write') and callable(obj.write):
                        obj.write({'pdca_stage': pdca_stage})
                    else:
                        setattr(obj, 'pdca_stage', pdca_stage)
                obj._compute_okr_metrics()
                if getattr(obj, 'id', None):
                    obj_ids.add(obj.id)
                parent_obj = getattr(obj, 'parent_objective_id', None)
                if parent_obj:
                    parent_obj._compute_okr_metrics()
                    if getattr(parent_obj, 'id', None):
                        obj_ids.add(parent_obj.id)
                obj_owner = getattr(obj, 'owner_employee_id', None)
                if obj_owner and getattr(obj_owner, 'id', None):
                    emp_ids.add(obj_owner.id)

            kr_owner = getattr(rec, 'owner_employee_id', None)
            if kr_owner and getattr(kr_owner, 'id', None):
                emp_ids.add(kr_owner.id)

        env = getattr(self, 'env', None)
        if env:
            Appraisal = env['dgm.hr.appraisal.sheet'].sudo()
            KpiEval = env['dgm.hr.kpi.evaluation'].sudo()
            Employee = env['hr.employee'].sudo()

            if obj_ids:
                linked_appraisals = Appraisal.search([('okr_objective_ids', 'in', list(obj_ids))])
                for ap in linked_appraisals:
                    ap._compute_appraisal_calibration()
                    if ap.employee_id:
                        emp_ids.add(ap.employee_id.id)

            if emp_ids:
                emp_appraisals = Appraisal.search([('employee_id', 'in', list(emp_ids))])
                for ap in emp_appraisals:
                    ap._compute_appraisal_calibration()
                emp_evals = KpiEval.search([('employee_id', 'in', list(emp_ids))])
                for ev in emp_evals:
                    ev._compute_kpi_scores_and_skill_gate()
                emps = Employee.browse(list(emp_ids)).exists()
                if emps:
                    emps._compute_dgm_kpi_summary()
        return True


class DgmHrAppraisalSheet(models.Model):
    _name = 'dgm.hr.appraisal.sheet'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'DGM 360-Degree HR Appraisal & Career Calibration Sheet (PDCA)'
    _order = 'period_code desc, code asc, id desc'

    code = fields.Char(
        string='Mã Phiếu Đánh giá 360° (Appraisal Code)',
        required=True,
        index=True,
        default='APR-2026-Q4-DGM001',
    )
    name = fields.Char(
        string='Tiêu đề Kỳ Đánh giá 360° & Hiệu chuẩn 9-Box',
        required=True,
    )
    employee_id = fields.Many2one(
        'hr.employee',
        string='Nhân sự / Kỹ sư',
        required=True,
        ondelete='cascade',
        index=True,
    )
    period_code = fields.Char(
        string='Kỳ Đánh giá (Quý / Năm)',
        default='2026-Q4',
        required=True,
        index=True,
    )
    kpi_evaluation_id = fields.Many2one(
        'dgm.hr.kpi.evaluation',
        string='Bảng KPI Liên kết',
        ondelete='set null',
    )
    okr_objective_ids = fields.Many2many(
        'dgm.okr.objective',
        'dgm_appraisal_okr_rel',
        'appraisal_id',
        'objective_id',
        string='OKRs Cam kết trong Kỳ',
    )
    okr_achievement_score = fields.Float(
        compute='_compute_appraisal_calibration',
        store=True,
        string='Điểm Hoàn thành OKR (0.00 – 1.00)',
    )
    okr_achievement_pct = fields.Float(
        compute='_compute_appraisal_calibration',
        store=True,
        string='Tỷ lệ Đạt OKR (%)',
    )
    self_assessment_score = fields.Float(
        default=90.0,
        string='Điểm Tự Đánh giá (Self-Appraisal /100)',
    )
    peer_client_360_score = fields.Float(
        default=92.0,
        string='Điểm Phản hồi 360° & Đối tác B2B (/100)',
    )
    manager_technical_score = fields.Float(
        default=93.0,
        string='Điểm Đánh giá Chuyên môn Tech Lead (/100)',
    )
    skill_gate_passed = fields.Boolean(
        compute='_compute_appraisal_calibration',
        store=True,
        string='Đạt 100% Cổng Nâng cấp Kỹ năng Bắt buộc',
    )
    calibrated_total_score = fields.Float(
        compute='_compute_appraisal_calibration',
        store=True,
        string='Điểm Appraisal Hiệu chuẩn Cuối cùng (/100)',
    )
    calibration_box = fields.Selection(
        CALIBRATION_BOX_SELECTION,
        compute='_compute_appraisal_calibration',
        store=True,
        string='Ma trận Nhân tài 9-Box (Talent Calibration)',
    )
    self_reflection_text = fields.Text(
        string='1. Tự Đánh giá của Nhân sự (Self-Reflection)',
    )
    peer_client_feedback_text = fields.Text(
        string='2. Phản hồi 360° từ Đồng nghiệp & Khách hàng B2B (MTI/AIfin/KTT)',
    )
    manager_appraisal_text = fields.Text(
        string='3. Đánh giá của Tech Lead / Quản lý Trực tiếp',
    )
    pdca_next_quarter_plan = fields.Text(
        string='4. Kế hoạch Hành động PDCA & Lộ trình OKR/Kỹ năng Quý tới',
    )
    state = fields.Selection(
        APPRAISAL_STATE_SELECTION,
        default='signed_off',
        required=True,
        index=True,
        string='Trạng thái Quy trình Appraisal',
    )
    active = fields.Boolean(default=True)

    @api.depends(
        'okr_objective_ids.okr_score',
        'okr_objective_ids.progress_pct',
        'self_assessment_score',
        'peer_client_360_score',
        'manager_technical_score',
        'kpi_evaluation_id.raw_weighted_score',
        'kpi_evaluation_id.final_kpi_score',
        'kpi_evaluation_id.all_mandatory_skills_completed',
        'employee_id.dgm_skill_gate_ids.state',
        'employee_id.dgm_skill_gate_ids.is_mandatory',
        'employee_id.dgm_skill_gate_ids.is_mandatory_for_next_level',
        'employee_id.dgm_skill_gate_ids.active',
    )
    def _compute_appraisal_calibration(self):
        for rec in _safe_iter_records(self):
            rec.okr_achievement_score = 0.0
            rec.okr_achievement_pct = 0.0
            rec.skill_gate_passed = False
            rec.calibrated_total_score = 0.0
            rec.calibration_box = 'box_5_core'

            objs = [
                o for o in _safe_iter_records(getattr(rec, 'okr_objective_ids', []))
                if getattr(o, 'active', True)
            ]
            if objs:
                avg_pct = sum(float(getattr(o, 'progress_pct', 0.0) or 0.0) for o in objs) / len(objs)
                rec.okr_achievement_pct = round(avg_pct, 2)
                rec.okr_achievement_score = round(avg_pct / 100.0, 2)
            else:
                rec.okr_achievement_pct = 90.0
                rec.okr_achievement_score = 0.90

            emp = getattr(rec, 'employee_id', None)
            gates = [
                g for g in _safe_iter_records(getattr(emp, 'dgm_skill_gate_ids', []))
                if getattr(g, 'active', True)
            ] if emp else []
            mand_gates = [
                g for g in gates
                if getattr(g, 'is_mandatory_for_next_level', False) or getattr(g, 'is_mandatory', False)
            ]
            if mand_gates:
                gate_passed = all(getattr(g, 'state', '') == 'certified' for g in mand_gates)
            elif getattr(rec, 'kpi_evaluation_id', None):
                gate_passed = bool(getattr(rec.kpi_evaluation_id, 'all_mandatory_skills_completed', True))
            else:
                gate_passed = True

            rec.skill_gate_passed = gate_passed

            raw_cal = round(
                0.35 * rec.okr_achievement_pct
                + 0.25 * float(getattr(rec, 'manager_technical_score', 0.0) or 0.0)
                + 0.25 * float(getattr(rec, 'peer_client_360_score', 0.0) or 0.0)
                + 0.15 * float(getattr(rec, 'self_assessment_score', 0.0) or 0.0),
                2,
            )

            if not rec.skill_gate_passed:
                rec.calibrated_total_score = round(min(raw_cal, 84.90), 2)
                if raw_cal >= 75.0:
                    rec.calibration_box = 'box_6_emerging'
                else:
                    rec.calibration_box = 'box_2_pip'
            else:
                rec.calibrated_total_score = raw_cal
                if raw_cal >= 92.0:
                    rec.calibration_box = 'box_9_star'
                elif raw_cal >= 85.0:
                    rec.calibration_box = 'box_8_high_perf'
                elif raw_cal >= 75.0:
                    rec.calibration_box = 'box_5_core'
                else:
                    rec.calibration_box = 'box_2_pip'

    def action_sign_off_appraisal(self):
        for rec in _safe_iter_records(self):
            rec.write({'state': 'signed_off'})
            rec._compute_appraisal_calibration()
        return True


class DgmProjectPdcaTemplate(models.Model):
    _name = 'dgm.project.pdca.template'
    _description = 'DGM Standardized Software Project PDCA Template'
    _order = 'code asc, id asc'

    code = fields.Char(
        string='Mã Mẫu Dự án PDCA',
        required=True,
        index=True,
        default='PRJ-TPL-PDCA-01',
    )
    name = fields.Char(
        string='Tên Khung Mẫu Dự án Phần mềm (PDCA Template)',
        required=True,
    )
    delivery_methodology = fields.Selection(
        DELIVERY_METHODOLOGY_SELECTION,
        required=True,
        default='sap_activate_pdca',
        string='Phương pháp Luận Triển khai (Methodology)',
    )
    linked_project_id = fields.Many2one(
        'project.project',
        string='Dự án Mẫu Liên kết (project.project)',
    )
    plan_phase_gate = fields.Text(
        string='P (Plan) — Hồ sơ Khởi tạo, Kiến trúc & Định nghĩa OKR Dự án',
    )
    do_phase_gate = fields.Text(
        string='D (Do) — Quy chuẩn Sprint, Code Review & Giờ công Billable',
    )
    check_phase_gate = fields.Text(
        string='C (Check) — Kiểm thử Tự động E2E, Adversarial Audit & Nghiệm thu UAT',
    )
    act_phase_gate = fields.Text(
        string='A (Act) — Bàn giao Go-Live, Đối soát Hóa đơn 1C26TAA & Bài học Kinh nghiệm',
    )
    mandatory_deliverable_codes = fields.Char(
        string='Bộ Mã Biểu mẫu Bắt buộc (TPL-PRJ-01..06)',
    )
    target_margin_pct = fields.Float(
        default=45.0,
        string='Biên lợi nhuận Mục tiêu (%)',
    )
    target_sla_uptime_pct = fields.Float(
        default=99.95,
        string='Cam kết SLA Chất lượng (%)',
    )
    active = fields.Boolean(default=True)


class HrEmployeeOkrAppraisalExtension(models.Model):
    _inherit = 'hr.employee'

    dgm_okr_objective_ids = fields.One2many(
        'dgm.okr.objective',
        'owner_employee_id',
        string='Mục tiêu OKR Cá nhân & Squad (SOP-DGM-11)',
    )
    dgm_appraisal_sheet_ids = fields.One2many(
        'dgm.hr.appraisal.sheet',
        'employee_id',
        string='Hồ sơ Đánh giá 360° & Hiệu chuẩn 9-Box (SOP-DGM-11)',
    )
