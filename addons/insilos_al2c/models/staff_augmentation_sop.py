# -*- coding: utf-8 -*-
import base64
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class SaleOrderStaffAugmentation(models.Model):
    _inherit = 'sale.order'

    dgm_is_staff_augmentation = fields.Boolean(
        string="Hợp đồng Biệt phái Nhân sự (SOP-DGM-07)",
        default=False,
    )
    dgm_assigned_employee_id = fields.Many2one(
        'hr.employee',
        string="Nhân sự Biệt phái (Onsite Engineer)",
    )
    dgm_min_monthly_hours = fields.Float(
        string="Cam kết Giờ Tối thiểu / Tháng",
        default=140.0,
    )
    dgm_max_standard_hours = fields.Float(
        string="Trần Giờ Tiêu chuẩn / Tháng",
        default=180.0,
    )
    dgm_hourly_rate_vnd = fields.Float(
        string="Đơn giá Giờ Chuẩn (VNĐ)",
        default=350000.0,
    )
    dgm_payment_term_days = fields.Integer(
        string="Thời hạn Thanh toán (Ngày làm việc)",
        default=40,
        help="Net 40 business days after VAT invoice & timesheet",
    )
    dgm_replacement_notice_days = fields.Integer(
        string="Thời hạn Báo trước Thay thế (Ngày)",
        default=30,
    )
    dgm_free_trial_days = fields.Integer(
        string="Số ngày Thử việc Miễn phí khi Thay thế",
        default=5,
    )

    def compute_staff_aug_monthly_settlement(
        self,
        logged_hours,
        ot_weekday_hours=0.0,
        ot_weekend_hours=0.0,
        is_replacement_trial=False,
    ):
        """
        Calculates monthly Staff Augmentation settlement according to MTI & AIfin Contract SLA (SOP-DGM-07):
        - Standard band: 140h - 180h
        - If is_replacement_trial=True: deduct up to (dgm_free_trial_days * 8h = 40h) free replacement trial
        - Weekday OT: 100% of hourly rate
        - Weekend/Holiday OT: 150% of hourly rate
        - Returns dict with breakdown, SLA status, and invoice line recommendations.
        """
        self.ensure_one()
        if logged_hours < 0 or ot_weekday_hours < 0 or ot_weekend_hours < 0:
            raise ValidationError(_("Số giờ chấm công không được nhỏ hơn 0."))

        rate = self.dgm_hourly_rate_vnd or 350000.0
        min_h = self.dgm_min_monthly_hours or 140.0
        max_h = self.dgm_max_standard_hours or 180.0
        trial_deducted_hours = (
            min(logged_hours, (self.dgm_free_trial_days or 5) * 8.0)
            if is_replacement_trial
            else 0.0
        )
        billable_std_hours = max(0.0, logged_hours - trial_deducted_hours)

        if billable_std_hours < min_h and not is_replacement_trial:
            sla_status = 'under_minimum_sla'
            sla_note = (
                f"Cảnh báo SLA: Giờ chuẩn thực tế ({billable_std_hours}h) thấp hơn "
                f"cam kết tối thiểu ({min_h}h/tháng)."
            )
        elif billable_std_hours > max_h:
            sla_status = 'above_sla_band_ot'
            sla_note = (
                f"Vượt khung giờ chuẩn ({max_h}h): {billable_std_hours - max_h}h chuyển sang đối soát OT."
            )
        else:
            sla_status = 'within_sla_band'
            sla_note = f"Đạt chuẩn SLA ({min_h}h – {max_h}h/tháng)."

        base_amount = billable_std_hours * rate
        ot_weekday_amount = ot_weekday_hours * rate * 1.0
        ot_weekend_amount = ot_weekend_hours * rate * 1.5
        subtotal_vnd = base_amount + ot_weekday_amount + ot_weekend_amount
        vat_amount_vnd = round(subtotal_vnd * 0.08)  # 8% VAT per Decree 174/2025/ND-CP
        total_with_vat_vnd = subtotal_vnd + vat_amount_vnd

        return {
            'order_name': self.name,
            'partner_name': self.partner_id.name,
            'partner_code': self.partner_id.dgm_partner_code or 'PENDING-ONB',
            'logged_hours': logged_hours,
            'trial_deducted_hours': trial_deducted_hours,
            'billable_std_hours': billable_std_hours,
            'ot_weekday_hours': ot_weekday_hours,
            'ot_weekend_hours': ot_weekend_hours,
            'hourly_rate_vnd': rate,
            'base_amount_vnd': base_amount,
            'ot_weekday_amount_vnd': ot_weekday_amount,
            'ot_weekend_amount_vnd': ot_weekend_amount,
            'subtotal_vnd': subtotal_vnd,
            'vat_amount_vnd': vat_amount_vnd,
            'total_with_vat_vnd': total_with_vat_vnd,
            'sla_status': sla_status,
            'sla_note': sla_note,
            'payment_term_days': self.dgm_payment_term_days or 40,
            'payment_gate_ready': bool(
                self.partner_id.dgm_onboarding_state == 'approved'
                and self.partner_id.dgm_partner_code
            ),
        }

    def action_generate_staff_aug_acceptance_doc(
        self,
        period_label="10/2026",
        logged_hours=160.0,
        ot_weekday_hours=0.0,
        ot_weekend_hours=0.0,
    ):
        """
        Generates a downloadable HTML/Print-to-PDF Monthly Timesheet & Billing Acceptance Certificate
        (Biên bản Nghiệm thu Timesheet & Đề nghị Thanh toán Staff Augmentation) in documents.document.
        """
        self.ensure_one()
        settlement = self.compute_staff_aug_monthly_settlement(
            logged_hours, ot_weekday_hours, ot_weekend_hours
        )
        partner = self.partner_id
        if not partner.dgm_onboarding_folder_id and hasattr(
            partner, 'action_generate_companion_templates'
        ):
            partner.action_generate_companion_templates()
        folder = partner.dgm_onboarding_folder_id or self.env.ref(
            'insilos_al2c.documents_dgm_partner_onboarding_folder',
            raise_if_not_found=False,
        )

        doc_name = (
            f"[TPL-ONB-05] Biên bản Nghiệm thu Timesheet & Đề nghị Thanh toán "
            f"({period_label}) - {partner.name}.html"
        )
        html_body = f"""<!DOCTYPE html>
<html lang="vi">
<head><meta charset="utf-8"/><title>{doc_name}</title>
<style>
  body {{ font-family: 'Inter', Arial, sans-serif; color: #0f172a; margin: 32px; line-height: 1.5; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 16px; }}
  th, td {{ border: 1px solid #cbd5e1; padding: 8px 12px; font-size: 13px; }}
  th {{ background: #f1f5f9; text-align: left; }}
</style>
</head>
<body>
  <h2 style="text-align:center;">CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM<br/>Độc lập - Tự do - Hạnh phúc</h2>
  <hr/>
  <h3 style="text-align:center;">BIÊN BẢN NGHIỆM THU BẢNG CHẤM CÔNG (TIMESHEET) &amp; ĐỀ NGHỊ THANH TOÁN<br/>
  <small>Kỳ đối soát: {period_label} | Hợp đồng / SO: {self.name} | Theo quy định SOP-DGM-07</small></h3>
  <p><strong>Bên A (Khách hàng):</strong> {partner.name} (Mã ĐT: {settlement['partner_code']} | MST: {partner.vat or 'N/A'})</p>
  <p><strong>Bên B (Nhà cung cấp):</strong> CÔNG TY CỔ PHẦN DIGIMATE (MST: 0317958465)</p>
  <table>
    <thead>
      <tr><th>Hạng mục Đối soát</th><th>Số giờ</th><th>Hệ số</th><th>Đơn giá (VNĐ/giờ)</th><th>Thành tiền (VNĐ)</th></tr>
    </thead>
    <tbody>
      <tr><td>Giờ làm việc tiêu chuẩn (Khung SLA 140–180h)</td><td>{settlement['billable_std_hours']:,.1f}</td><td>100%</td><td>{settlement['hourly_rate_vnd']:,.0f}</td><td>{settlement['base_amount_vnd']:,.0f}</td></tr>
      <tr><td>Làm thêm giờ Ngày thường (OT Thứ 2 – Thứ 6)</td><td>{settlement['ot_weekday_hours']:,.1f}</td><td>100%</td><td>{settlement['hourly_rate_vnd']:,.0f}</td><td>{settlement['ot_weekday_amount_vnd']:,.0f}</td></tr>
      <tr><td>Làm thêm giờ Cuối tuần / Lễ (OT Thứ 7, CN)</td><td>{settlement['ot_weekend_hours']:,.1f}</td><td>150%</td><td>{settlement['hourly_rate_vnd'] * 1.5:,.0f}</td><td>{settlement['ot_weekend_amount_vnd']:,.0f}</td></tr>
      <tr><td colspan="4"><strong>Cộng tiền dịch vụ (Chưa thuế GTGT)</strong></td><td><strong>{settlement['subtotal_vnd']:,.0f}</strong></td></tr>
      <tr><td colspan="4">Thuế GTGT (8% theo Nghị định 174/2025/NĐ-CP)</td><td>{settlement['vat_amount_vnd']:,.0f}</td></tr>
      <tr><td colspan="4"><strong>TỔNG CỘNG THANH TOÁN (VNĐ)</strong></td><td><strong>{settlement['total_with_vat_vnd']:,.0f}</strong></td></tr>
    </tbody>
  </table>
  <p><strong>Đánh giá SLA:</strong> {settlement['sla_note']}</p>
  <p><strong>Điều khoản Thanh toán:</strong> Net {settlement['payment_term_days']} ngày làm việc kể từ ngày nhận đủ Hóa đơn GTGT hợp lệ và Biên bản nghiệm thu Timesheet.</p>
</body>
</html>"""

        Attachment = self.env['ir.attachment'].sudo()
        Document = self.env['documents.document'].sudo()
        raw_bytes = html_body.encode('utf-8')
        b64_datas = base64.b64encode(raw_bytes)

        existing = Document.search(
            [
                ('name', '=', doc_name),
                ('folder_id', '=', folder.id if folder else False),
            ],
            limit=1,
        )
        if existing:
            if existing.attachment_id:
                existing.attachment_id.write(
                    {'datas': b64_datas, 'mimetype': 'text/html'}
                )
            return existing

        att = Attachment.create(
            {
                'name': doc_name,
                'datas': b64_datas,
                'mimetype': 'text/html',
                'res_model': 'sale.order',
                'res_id': self.id,
            }
        )
        return Document.create(
            {
                'name': doc_name,
                'folder_id': folder.id if folder else False,
                'owner_id': False,
                'partner_id': partner.id,
                'type': 'binary',
                'attachment_id': att.id,
                'access_internal': 'edit',
                'access_via_link': 'none',
            }
        )
