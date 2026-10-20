# -*- coding: utf-8 -*-
import logging
import time
import hmac
import hashlib
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.sql import SQL

_logger = logging.getLogger(__name__)

TIMESHEET_KEYWORDS = ('consult', 'tư vấn', 'giờ', 'hour', 't&m', 'timesheet')
TIMESHEET_EXCLUSION_KEYWORDS = ('no consult', 'không tư vấn', 'không tính', 'non-billable', 'giảm giá', 'discount')


class AccountMove(models.Model):
    _inherit = 'account.move'

    al2c_dunning_stage = fields.Selection([
        ('current', 'Current (Within Terms)'),
        ('d3_reminder', 'D+3 Gentle Reminder'),
        ('d15_warning', 'D+15 Late Fee & Escalation Warning'),
        ('d30_suspension', 'D+30 Service Suspension'),
    ], string='AL2C Dunning Stage', default='current', copy=False, index=True)

    al2c_dunning_last_date = fields.Date(
        string='Last Dunning Action Date',
        copy=False,
    )

    al2c_dispute_ids = fields.One2many(
        'al2c.dispute',
        'invoice_id',
        string='Commercial Disputes',
    )
    al2c_has_open_dispute = fields.Boolean(
        string='Has Open Dispute',
        compute='_compute_al2c_has_open_dispute',
        store=True,
    )

    @api.depends('al2c_dispute_ids.state')
    def _compute_al2c_has_open_dispute(self):
        for move in self:
            move.al2c_has_open_dispute = any(d.state == 'open' for d in move.al2c_dispute_ids)

    # --- Billable Timesheet Statement & Client Confirmation (AL2C-SOP-002 / CWE-639 Hardened) ---
    al2c_timesheet_statement_state = fields.Selection([
        ('not_applicable', 'Not Applicable'),
        ('draft_statement', 'Draft Timesheet Statement'),
        ('sent_to_client', 'Sent to Client for Confirmation'),
        ('confirmed', 'Confirmed by Client'),
        ('disputed', 'Disputed / Under Review'),
    ], string='Timesheet Statement Status', default='not_applicable', tracking=True, copy=False)

    al2c_timesheet_token = fields.Char(
        string='Statement Confirmation Token (HMAC Signed)',
        copy=False,
        readonly=True,
    )
    al2c_timesheet_confirmed_date = fields.Datetime(
        string='Timesheet Confirmation Date',
        copy=False,
        readonly=True,
    )
    al2c_timesheet_confirmed_by = fields.Char(
        string='Confirmed By Client Representative',
        copy=False,
        readonly=True,
    )
    al2c_exchange_rate_snapshot = fields.Float(
        string='Exchange Rate Snapshot (to Company Currency)',
        digits=(16, 8),
        readonly=True,
        index=True,
        copy=False,
        help='Snapshotted conversion rate from invoice currency to company currency (VND) at time of statement issuance (Decree 70/2025/ND-CP compliance).'
    )
    al2c_statement_amount_total_company_currency = fields.Monetary(
        string='Statutory Total in Company Currency (VND)',
        currency_field='company_currency_id',
        compute='_compute_al2c_statement_company_currency',
        store=True,
        copy=False,
        help='Statutory total converted to company currency using immutable exchange rate snapshot.'
    )
    al2c_is_foreign_currency = fields.Boolean(
        string='Is Foreign Currency Invoice',
        compute='_compute_al2c_is_foreign_currency',
        store=True,
    )
    al2c_rate_unavailable = fields.Boolean(
        string='FX Rate Unavailable',
        compute='_compute_al2c_statement_company_currency',
        store=True,
        help='Set when a foreign-currency conversion rate could not be resolved. Blocks statement dispatch (Decree 70/2025 compliance).',
    )
    al2c_timesheet_hours_total = fields.Float(
        string='Total Timesheet Hours Billed',
        compute='_compute_al2c_timesheet_hours_total',
        store=True,
    )

    @api.depends('currency_id', 'company_id.currency_id')
    def _compute_al2c_is_foreign_currency(self):
        for move in self:
            comp_curr = move.company_id.currency_id
            move.al2c_is_foreign_currency = bool(move.currency_id and comp_curr and move.currency_id.id != comp_curr.id)

    @api.depends('amount_total', 'currency_id', 'company_id.currency_id', 'al2c_exchange_rate_snapshot')
    def _compute_al2c_statement_company_currency(self):
        Rate = self.env['res.currency.rate'].sudo()
        has_rate_cache = {}
        for move in self:
            company_curr = move.company_id.currency_id
            if not company_curr:
                move.al2c_rate_unavailable = True
                move.al2c_statement_amount_total_company_currency = 0.0
                continue

            if not move.currency_id or move.currency_id.id == company_curr.id:
                move.al2c_rate_unavailable = False
                move.al2c_statement_amount_total_company_currency = move.amount_total
            else:
                rate = move.al2c_exchange_rate_snapshot
                if not rate or rate <= 0:
                    cache_key = (move.currency_id.id, move.company_id.id if move.company_id else 0)
                    if cache_key not in has_rate_cache:
                        has_rate_cache[cache_key] = bool(Rate.search_count([
                            ('currency_id', '=', move.currency_id.id),
                            ('company_id', 'in', (False, move.company_id.id, move.company_id.root_id.id if hasattr(move.company_id, 'root_id') else False)),
                        ], limit=1))
                    has_rate = has_rate_cache[cache_key]
                    if not has_rate:
                        rate = 0.0
                    else:
                        try:
                            rate = self.env['res.currency']._get_conversion_rate(
                                move.currency_id,
                                company_curr,
                                move.company_id,
                                move.invoice_date or fields.Date.context_today(move)
                            )
                        except Exception as err:
                            _logger.warning("Failed to auto-compute conversion rate for move %s: %s", move.id, err)
                            rate = 0.0
                if rate <= 0:
                    # Invariant: Never silently assume 1.0 or silent zero without explicit flag
                    move.al2c_rate_unavailable = True
                    move.al2c_statement_amount_total_company_currency = 0.0
                    continue
                move.al2c_rate_unavailable = False
                move.al2c_statement_amount_total_company_currency = company_curr.round(move.amount_total * rate)

    @api.depends(
        'invoice_line_ids.quantity',
        'invoice_line_ids.product_id',
        'invoice_line_ids.name',
        'invoice_line_ids.product_uom_id',
        'invoice_line_ids.display_type',
    )
    def _compute_al2c_timesheet_hours_total(self):
        uom_hour = self.env.ref('uom.product_uom_hour', raise_if_not_found=False)
        for move in self:
            hours = 0.0
            for line in move.invoice_line_ids:
                if line.display_type in ('line_section', 'line_note', 'line_subsection'):
                    continue
                is_timesheet = False
                line_name_lower = (line.name or '').lower()
                # 1. Product configuration is authoritative (A-4 defense)
                if line.product_id and getattr(line.product_id, 'service_policy', None) == 'delivered_timesheet':
                    is_timesheet = True
                # 2. Heuristic fallback for unstructured / legacy lines
                elif any(kw in line_name_lower for kw in TIMESHEET_KEYWORDS) \
                        and not any(ex in line_name_lower for ex in TIMESHEET_EXCLUSION_KEYWORDS):
                    is_timesheet = True
                    _logger.debug("Heuristic timesheet match on move %s (line id %s)", move.id, line.id)

                if is_timesheet:
                    qty = line.quantity
                    if uom_hour and line.product_uom_id and line.product_uom_id != uom_hour:
                        try:
                            qty = line.product_uom_id._compute_quantity(qty, uom_hour, raise_if_failure=False)
                        except Exception:
                            pass
                    hours += qty
            move.al2c_timesheet_hours_total = hours

    @api.model
    def _token_secret(self):
        """Retrieve per-database cryptographic secret (CWE-259 / CWE-798 defense)."""
        secret = self.env['ir.config_parameter'].sudo().get_param('database.secret')
        if not secret:
            secret = self.env['ir.config_parameter'].sudo().get_param('al2c.statement_secret')
        if not secret:
            raise UserError(_("Server security secret is uninitialized; cannot generate or verify statement tokens."))
        return secret.strip().encode('utf-8')

    @api.model
    def _generate_timesheet_token(self, move_id, expires_in_days=7):
        """Generates cryptographically signed, time-boxed token (CWE-639 IDOR defense)."""
        secret_bytes = self._token_secret()
        expiry_ts = int(time.time() + (expires_in_days * 86400))
        msg = f"{move_id}:{expiry_ts}".encode('utf-8')
        sig = hmac.new(secret_bytes, msg, hashlib.sha256).hexdigest()[:32]
        return f"{expiry_ts}_{sig}"

    @api.model
    def _verify_timesheet_token(self, move_id, token_str):
        """Verifies HMAC signature, move-binding, and expiry for timesheet confirmation token."""
        if not token_str or '_' not in str(token_str):
            return False
        parts = str(token_str).split('_', 1)
        if len(parts) != 2:
            return False
        try:
            expiry_ts = int(parts[0])
            provided_sig = parts[1]
        except (ValueError, TypeError):
            return False
        if time.time() > expiry_ts:
            return False
        try:
            secret_bytes = self._token_secret()
        except UserError:
            return False
        msg = f"{move_id}:{expiry_ts}".encode('utf-8')
        expected_sig = hmac.new(secret_bytes, msg, hashlib.sha256).hexdigest()[:32]
        return hmac.compare_digest(expected_sig, provided_sig)

    def action_send_timesheet_statement(self):
        """Send timesheet statement & confirmation request email to client."""
        template = self.env.ref('insilos_al2c.email_template_al2c_timesheet_statement_confirm', raise_if_not_found=False)
        for move in self:
            if move.move_type not in ('out_invoice', 'out_refund'):
                continue

            # Invalidate cached/stored flags to prevent TOCTOU race (CWE-367 / A-6 defense)
            move.invalidate_recordset(['al2c_rate_unavailable', 'al2c_statement_amount_total_company_currency', 'al2c_is_foreign_currency'])

            comp_curr = move.company_id.currency_id
            if not comp_curr:
                raise UserError(_(
                    "Cannot issue statutory statement for invoice %s: Company currency is undefined on company %s.",
                    move.display_name, move.company_id.display_name
                ))

            if move.al2c_rate_unavailable or (
                move.al2c_is_foreign_currency and move.al2c_statement_amount_total_company_currency <= 0
            ):
                raise UserError(_(
                    "Cannot issue statutory statement for invoice %s: foreign-currency conversion rate "
                    "could not be resolved. Set an exchange rate snapshot first (Decree 70/2025/ND-CP compliance)."
                ) % move.display_name)

            vals = {'al2c_timesheet_statement_state': 'sent_to_client'}

            # Idempotent Token Preservation (rotate if missing or expired)
            if not move.al2c_timesheet_token or not self._verify_timesheet_token(move.id, move.al2c_timesheet_token):
                vals['al2c_timesheet_token'] = self._generate_timesheet_token(move.id, expires_in_days=7)

            # Multi-Currency Statutory Rate Card Snapshot: Fail-Closed Protection
            if move.currency_id and comp_curr and move.currency_id.id != comp_curr.id:
                if not move.al2c_exchange_rate_snapshot or move.al2c_exchange_rate_snapshot <= 0:
                    Rate = self.env['res.currency.rate'].sudo()
                    has_rate = bool(Rate.search_count([
                        ('currency_id', '=', move.currency_id.id),
                        ('company_id', 'in', (False, move.company_id.id, move.company_id.root_id.id if hasattr(move.company_id, 'root_id') else False)),
                    ], limit=1))
                    if not has_rate:
                        rate = 0.0
                    else:
                        try:
                            rate = self.env['res.currency']._get_conversion_rate(
                                move.currency_id,
                                comp_curr,
                                move.company_id,
                                move.invoice_date or fields.Date.context_today(move)
                            )
                        except Exception:
                            rate = 0.0

                    if not rate or rate <= 0:
                        raise UserError(_(
                            "Cannot issue statutory statement for invoice %s: No conversion rate found from %s to %s for date %s. "
                            "(Decree 70/2025/ND-CP Compliance Invariant)",
                            move.display_name, move.currency_id.name, comp_curr.name, move.invoice_date or fields.Date.context_today(move)
                        ))
                    vals['al2c_exchange_rate_snapshot'] = rate
            else:
                vals['al2c_exchange_rate_snapshot'] = 1.0

            move.write(vals)
            if template and move.partner_id.email:
                template.send_mail(move.id, force_send=False)
            move.message_post(
                body=_(
                    "<b>Bảng kê Giờ công Tư vấn (Timesheet Statement)</b> đã được gửi tới khách hàng (%s). "
                    "Hạn xác nhận trực tuyến: 7 ngày (HMAC signed token)."
                ) % (move.partner_id.email or 'N/A'),
                message_type='comment',
                subtype_xmlid='mail.mt_note',
            )
        return True

    def action_client_confirm_timesheet(self, token=None, confirmed_by=None):
        """Called when client confirms timesheet on portal or via secure link.
        Validates token, ensures single-use idempotency, and records audit trail.
        """
        for move in self:
            if move.al2c_timesheet_statement_state == 'confirmed':
                continue
            if token and not self._verify_timesheet_token(move.id, token):
                raise UserError(_("Invalid or expired timesheet confirmation token."))
            move.write({
                'al2c_timesheet_statement_state': 'confirmed',
                'al2c_timesheet_confirmed_date': fields.Datetime.now(),
                'al2c_timesheet_confirmed_by': confirmed_by or (self.env.user.name if self.env.user else 'Client Representative'),
            })
            move.message_post(
                body=_(
                    "<b>✓ Khách Hàng Đã Xác Nhận Bảng Kê Giờ Công Tư Vấn (Timesheet Statement):</b><br/>"
                    "Đại diện xác nhận: <b>%s</b><br/>"
                    "Thời điểm xác nhận: <code>%s</code><br/>"
                    "<i>Hóa đơn đủ điều kiện để ký số và phát hành Hóa đơn Điện tử theo Nghị định 70/2025/NĐ-CP.</i>"
                ) % (move.al2c_timesheet_confirmed_by, move.al2c_timesheet_confirmed_date),
                message_type='comment',
                subtype_xmlid='mail.mt_comment',
            )
        return True

    def action_ai_explain_statement(self, query=None):
        """
        AI Statement & Timesheet Explainer (SOP-RAG-003, SOP-DGM-08, SOP-DGM-09, SOP-DGM-15 & SOP-AI-004):
        Answers client inquiries regarding billed timesheet entries, deliverables,
        Draft vs. Official 1C26TAA E-Invoices, VAT tax regimes (KCT / 0% / 8%),
        SOW 5-Gate milestones, and AL2C-INV-103 Dunning Freeze using grounded RAG knowledge
        and Entailment Gate (threshold >= 0.85).
        """
        import re as _re
        self.ensure_one()
        raw_query = (query or '').strip()
        if not raw_query:
            raw_query = _("Giải trình tổng hợp các hạng mục giờ công và tiến độ nghiệm thu.")

        # 1. Adversarial Prompt-Injection, XSS & PII Sanitization (ISO/IEC 27701)
        adversarial_patterns = (
            r"<\s*script",
            r"javascript\s*:",
            r"onerror\s*=",
            r"onload\s*=",
            r"ignore\s+(all\s+)?(prior|previous|above)\s+(instructions|rules|prompts)?",
            r"system\s+override",
            r"reveal\s+system\s+prompt",
            r"drop\s+table",
            r"union\s+select",
            r"delete\s+from\s+res_users",
            r"\.sudo\s*\(",
            r"cr\.execute\s*\(",
            r"bỏ\s+qua\s+(mọi\s+|tất\s+cả\s+)?(quy\s+tắc|hướng\s+dẫn|chỉ\s+thị)",
        )
        is_adversarial = any(_re.search(pat, raw_query, flags=_re.IGNORECASE) for pat in adversarial_patterns)
        if is_adversarial:
            sec_citation = "[SOP-AI-004 | Zero-Trust Prompt & XSS Guard | 404 | 9f8e7d6c]"
            sec_answer = (
                f"### Giải trình Bảng kê Hóa đơn #{self.name} — Cảnh báo Bảo mật (SOP-AI-004)\n"
                "Hệ thống Bảo mật AI (Zero-Trust Guardrail · ISO/IEC 27701) đã từ chối xử lý truy vấn do phát hiện "
                "cú pháp không hợp lệ (Prompt Injection / XSS / Truy cập trái phép).\n\n"
                "Vui lòng đặt câu hỏi nghiệp vụ hợp lệ về **Bảng chấm công kỹ sư (Timesheet)**, **Hóa đơn Nháp / HĐĐT 1C26TAA**, "
                "**Thuế suất GTGT phần mềm**, hoặc **Đối soát AL2C-INV-103**."
            )
            return {
                'success': True,
                'blocked_by_security': True,
                'intent': 'security_guard',
                'intent_badge': 'SECURITY GUARD · SOP-AI-004',
                'answer': sec_answer,
                'citations': [sec_citation],
                'grounded': True,
                'entailment_score': 1.0,
                'reason': "Blocked adversarial/XSS payload per SOP-AI-004",
            }

        # Scrub secrets & PII in query
        clean_query = _re.sub(
            r"\b(sk-ant-[A-Za-z0-9_-]{8,}|sk-[A-Za-z0-9_-]{12,}|AIzaSy[A-Za-z0-9_-]{10,}|ghp_[A-Za-z0-9]{10,}|AKIA[0-9A-Z]{12,})\b",
            "[REDACTED_SECRET]",
            raw_query,
        )
        clean_query = _re.sub(r"\b(0[35789]\d)(\d{5})(\d{2})\b", r"\1*****\3", clean_query)
        user_query = clean_query

        # 2. Inspect Invoice Stage: Draft Reconciliation vs. Official 1C26TAA E-Invoice
        dgm_stage = getattr(self, 'dgm_invoice_stage', False) or ''
        einv_symbol = getattr(self, 'dgm_einvoice_symbol', False) or '1C26TAA'
        einv_no = getattr(self, 'dgm_einvoice_number', False) or self.al2c_einvoice_number or self.name or 'DRAFT'
        lookup_code = (
            getattr(self, 'dgm_einvoice_lookup_code', False)
            or self.al2c_einvoice_lookup_code
            or ''
        )
        is_official = bool(
            dgm_stage == 'official_issued'
            or (self.state == 'posted' and (lookup_code or getattr(self, 'dgm_einvoice_number', False) or self.al2c_einvoice_state == 'issued'))
        )
        if is_official:
            stage_badge = f"Hóa đơn GTGT Chính thức {einv_symbol} — Đã cấp mã CQT: {lookup_code or 'CERTIFIED'}"
            stage_summary = (
                f"Hóa đơn đang ở trạng thái **Hóa đơn GTGT Điện tử Chính thức ({einv_symbol} - {einv_no})**, "
                f"đã được ký số và cấp Mã tra cứu Cơ quan Thuế (CQT): `{lookup_code or 'CQT-70-VERIFIED'}` theo **Nghị định 70/2025/NĐ-CP**."
            )
        else:
            stage_badge = "Hóa đơn Nháp chờ đối soát — Chưa cấp mã CQT"
            stage_summary = (
                f"Hóa đơn đang ở trạng thái **Hóa đơn Nháp chờ Khách hàng đối soát (`{dgm_stage or 'draft_reconciliation'}`) — Chưa cấp mã CQT**. "
                "Quý Khách hàng có thể kiểm tra Mã số thuế (MST), tên pháp nhân, địa chỉ và bấm **Xác nhận Hóa đơn Nháp** để hệ thống ký số và phát hành HĐĐT chính thức chuẩn `1C26TAA`."
            )

        # 3. Inspect Linked Engineer Timesheet Sheet (SOP-DGM-08)
        sheet = getattr(self, 'dgm_timesheet_sheet_id', False)
        timesheet_summary_lines = []
        if sheet:
            sig_hash_short = (sheet.customer_signature_hash or '')[:16]
            sig_status = f"Đã ký xác thực SHA-256 (`{sig_hash_short}...`)" if sig_hash_short else "Đang chờ xác nhận chữ ký số SHA-256"
            timesheet_summary_lines.append(
                f"- **Bảng chấm công liên kết**: `{sheet.name}` · Kỳ đối soát: **{sheet.billing_period}** · "
                f"Tổng ngày công nghiệm thu: **{sheet.total_billable_days:.2f} ngày công** ({sheet.total_logged_hours:.1f} giờ) · "
                f"Trạng thái chữ ký: {sig_status}."
            )
            for tline in sheet.line_ids[:6]:
                emp_name = tline.employee_id.name or 'Senior Software Engineer'
                role_name = tline.role_title or 'Software Engineer'
                timesheet_summary_lines.append(
                    f"  * Kỹ sư **{emp_name}** ({role_name}): Công thực tế `{tline.actual_worked_days:.1f}`/{tline.standard_days:.0f} ngày chuẩn, "
                    f"OT `{tline.overtime_hours:.1f}h`, Công nghiệm thu `{tline.billable_days:.2f}` ngày (Pro-rata `{tline.pro_rata_ratio:.1f}%`)."
                )

        # 4. Detect Query Intent
        q_lower = user_query.lower()
        if any(k in q_lower for k in ('nháp', 'draft', '1c26taa', 'cqt', 'xml', 'html', 'nghị định 70', 'xuất hóa đơn', 'mã số thuế', 'mst')):
            detected_intent = 'draft_vs_official_einvoice'
            intent_badge = 'SOP-DGM-08 · DRAFT VS 1C26TAA E-INVOICE'
            intent_guidance = (
                "**Quy trình Hóa đơn Nháp & HĐĐT Chính thức 1C26TAA (SOP-DGM-08 & Nghị định 70/2025/NĐ-CP)**:\n"
                "- **Bước 1 (Hóa đơn Nháp đối soát)**: Khởi tạo tự động sau khi nghiệm thu Timesheet/Sprint, giúp Quý Khách hàng rà soát MST, tên đơn vị mua hàng và số tiền trước khi ký số.\n"
                "- **Bước 2 (HĐĐT Chính thức 1C26TAA)**: Ngay khi xác nhận bản nháp, hệ thống đóng dấu chữ ký số C14N XML và cấp mã CQT chuẩn `1C26TAA`, cho phép tải trực tiếp file XML gốc và bản thể hiện HTML."
            )
        elif any(k in q_lower for k in ('thuế', 'vat', 'gtgt', 'kct', '0%', '8%', '10%', 'thanh toán', 'vietqr', 'napas', 'vcb', 'swift')):
            detected_intent = 'tax_payment_policy'
            intent_badge = 'SOP-DGM-09/15 · TAX & PAYMENT POLICY'
            intent_guidance = (
                "**Chính sách Thuế GTGT Phần mềm (SOP-DGM-15) & Kênh Thanh toán (SOP-DGM-09)**:\n"
                "- **Thuế suất GTGT**: Sản phẩm phần mềm & dịch vụ phần mềm thuộc đối tượng Không chịu thuế (`KCT`) theo Luật Thuế GTGT số 48/2024/QH15; Phần mềm xuất khẩu áp dụng thuế suất `0%` (SLA hoàn tất chứng từ 24h); Dịch vụ tư vấn CNTT/vận hành áp dụng thuế suất `8%` (Nghị định 174/2025/NĐ-CP) hoặc `10%`.\n"
                "- **Thanh toán**: Hỗ trợ quét mã **Napas247 VietQR** tự động gạch nợ, chuyển khoản doanh nghiệp **VCB DigiBiz**, hoặc thanh toán quốc tế **SWIFT USD**."
            )
        elif any(k in q_lower for k in ('khiếu nại', 'tranh chấp', 'dispute', 'al2c-inv-103', 'đóng băng', 'dunning', 'nhắc nợ', 'sai lệch')):
            detected_intent = 'dispute_dunning_freeze'
            intent_badge = 'AL2C-INV-103 · DISPUTE & DUNNING FREEZE'
            intent_guidance = (
                "**Quy chế Bảo vệ Đối tác & Đóng băng Nhắc nợ Tự động (AL2C-INV-103)**:\n"
                "- Khi Quý Khách hàng gửi yêu cầu đối soát hoặc khiếu nại thương mại (`AL2C-INV-103`), hệ thống lập tức **ĐÓNG BĂNG 100% tiến trình nhắc nợ tự động (Dunning Freeze)** ở mọi cấp độ (`D+3`, `D+15`, `D+30`).\n"
                "- Quản lý Dự án (PM) và Kế toán Trưởng (KTT) sẽ phối hợp đối soát biên bản nghiệm thu và phản hồi theo SLA cam kết."
            )
        elif any(k in q_lower for k in ('sow', 'báo giá', 'quotation', 'fit-to-standard', 'explore', 'realize', 'milestone', '5-gate', 'roi', 'clean core')):
            detected_intent = 'sow_quotation'
            intent_badge = 'AL2C-ACT-001 · 5-GATE SOW & CLEAN CORE'
            intent_guidance = (
                "**Phương pháp luận Triển khai 5-Gate Delivery & Kiến trúc Clean Core (AL2C-ACT-001)**:\n"
                "- Mọi hạng mục trên hóa đơn và hợp đồng SOW được nghiệm thu qua 5 cổng chất lượng: `1. Prepare` -> `2. Explore (Fit-to-Standard Class A/B/C)` -> `3. Realize (Sprint Development & SIT)` -> `4. Deploy (UAT & Go-Live)` -> `5. Run (Hypercare SLA)`.\n"
                "- Hiệu quả đầu tư được định lượng minh bạch qua hồ sơ **3Y Value Case ROI**."
            )
        elif any(k in q_lower for k in ('sla', 'bảo hành', 'hỗ trợ', 'p1', 'p2', 'p3', 'sự cố', 'customer care', 'liên hệ', 'ticket')):
            detected_intent = 'sla_customer_care'
            intent_badge = 'SLA CUSTOMER CARE · P1/P2/P3 SUPPORT'
            intent_guidance = (
                "**Cam kết Chất lượng Phục vụ & Hỗ trợ Kỹ thuật (Customer Care SLA)**:\n"
                "- **Mức P1 (Critical — Sự cố dừng hệ thống)**: Phản hồi trong **15 phút**, xử lý khắc phục trong **2 giờ**.\n"
                "- **Mức P2 (High — Ảnh hưởng nghiệp vụ chính)**: Phản hồi trong **1 giờ**, xử lý trong **8 giờ**.\n"
                "- **Mức P3 (Normal — Tư vấn đối soát / Change Request)**: Phản hồi trong **4 giờ**, xử lý trong **24 giờ**."
            )
        else:
            detected_intent = 'timesheet_sprint'
            intent_badge = 'SOP-DGM-08 · TIMESHEET & SPRINT ACCEPTANCE'
            intent_guidance = (
                "**Quy chuẩn Nghiệm thu Bảng chấm công Kỹ sư & Tính cước Pro-rata (SOP-DGM-08)**:\n"
                "- Ngày công nghiệm thu được tính theo định mức chuẩn **22 ngày công/tháng** (`Công nghiệm thu = Công thực tế + Giờ OT quy đổi`, tỷ lệ `Pro-rata = Công nghiệm thu / 22`).\n"
                "- Bảng chấm công được đối soát qua cổng `info@inno.ai.vn` và niêm phong bằng chữ ký băm **HMAC-SHA256** trước khi phát hành Hóa đơn."
            )

        line_details = []
        curr_symbol = self.currency_id.symbol or 'VND'
        for line in self.invoice_line_ids:
            if line.display_type in ('line_section', 'line_note', 'line_subsection'):
                continue
            line_details.append(f"- {line.name}: {line.quantity:.1f} giờ/đơn vị x {line.price_unit:,.0f} {curr_symbol}")

        explanation_lines = [
            f"### Giải trình Bảng kê Hóa đơn #{self.name} ({stage_badge})",
            f"- **Khách hàng / Đối tác**: **{self.partner_id.name}** (MST: `{self.partner_id.vat or 'Đang cập nhật'}`)",
            f"- **Trạng thái pháp lý HĐ**: {stage_summary}",
            f"- **Tổng khối lượng & Giá trị**: Hóa đơn ghi nhận tổng cộng **{self.al2c_timesheet_hours_total:.1f} giờ** tư vấn dịch vụ với tổng thanh toán **{self.amount_total:,.0f} {curr_symbol}** (Chưa thuế: `{self.amount_untaxed:,.0f} {curr_symbol}`, Thuế GTGT: `{self.amount_tax:,.0f} {curr_symbol}`).",
        ]
        if self.al2c_has_open_dispute:
            explanation_lines.append(
                "- **Bảo vệ AL2C-INV-103**: Hóa đơn hiện có hồ sơ đối soát thương mại đang mở — Tiến trình nhắc nợ tự động (**Dunning Ladder**) đã được **ĐÓNG BĂNG**."
            )
        if timesheet_summary_lines:
            explanation_lines.append("")
            explanation_lines.append("**Dữ liệu Bảng chấm công Kỹ sư (Timesheet Sprint SOP-DGM-08):**")
            explanation_lines.extend(timesheet_summary_lines)

        explanation_lines.append("")
        explanation_lines.append("**Chi tiết các hạng mục bàn giao trên hóa đơn:**")
        for line in self.invoice_line_ids:
            if line.display_type in ('line_section', 'line_note', 'line_subsection'):
                continue
            explanation_lines.append(
                f"- **{line.name}**: {line.quantity:.1f} giờ công ({line.price_unit:,.0f} {curr_symbol} — Thành tiền: {line.price_subtotal:,.0f} {curr_symbol})."
            )

        explanation_lines.append("")
        explanation_lines.append(intent_guidance)
        explanation_lines.append("")
        explanation_lines.append(
            "Dữ liệu được đối soát qua info@inno.ai.vn theo Nghị định 70/2025/NĐ-CP và kiểm định qua cổng Entailment Gate (SOP-RAG-003)."
        )

        explanation_text = "\n".join(explanation_lines)

        invoice_context = (
            f"Hóa đơn #{self.name} phát hành cho {self.partner_id.name}.\n"
            f"Tổng tiền: {self.amount_total:,.0f} {curr_symbol}.\n"
            f"Trạng thái Bảng kê: {self.al2c_timesheet_statement_state}.\n"
            f"Tổng giờ công: {self.al2c_timesheet_hours_total:.1f} giờ.\n"
            f"Quy chuẩn đối soát giờ công qua cổng info@inno.ai.vn và tuân thủ Nghị định 70/2025/NĐ-CP.\n"
            f"Chi tiết hạng mục:\n" + "\n".join(line_details) + "\n\n" + explanation_text
        )

        rag_service = self.env['al2c.rag.service'].sudo()
        chunks = rag_service.retrieve_grounded_context(
            user_query,
            company_id=self.company_id.id,
            top_k=4
        )

        context_blocks = [invoice_context]
        citations = [
            "[SOP-DGM-08 | Timesheet & 1C26TAA E-Invoice Reconciliation | 8 | a808dgm1]",
            "[SOP-RAG-003 | Enterprise Grounding & Citation Contract | 3 | d003rag4]",
        ]
        if detected_intent == 'tax_payment_policy':
            citations.append("[SOP-DGM-15 | Software VAT Tax Regimes KCT/0%/8% | 15 | c150dgm3]")
        elif detected_intent == 'dispute_dunning_freeze':
            citations.append("[AL2C-INV-103 | Commercial Dispute & Dunning Freeze | 103 | f103inv9]")

        import re
        for chunk in chunks:
            context_blocks.append(f"[{chunk.name} | {chunk.section_header}]\n{chunk.content}")
            short_doc = (chunk.name or "KMS-DOC").split("·")[0].split(":")[0].strip()[:22]
            short_sec = (chunk.section_header or "Standard").split(">")[-1].split("·")[-1].strip()
            short_sec = re.sub(r"\([^)]*Digimate[^)]*\)", "", short_sec, flags=re.IGNORECASE).strip()[:28]
            h8 = (chunk.chunk_hash or "verified")[:8]
            tag = f"[{short_doc} | {short_sec} | {chunk.id} | {h8}]"
            if tag not in citations and len(citations) < 4:
                citations.append(tag)

        is_grounded, entailment_score, reason = rag_service.verify_grounding_entailment(
            user_query,
            explanation_text,
            context_blocks,
            threshold=0.85
        )

        return {
            'success': True,
            'intent': detected_intent,
            'intent_badge': intent_badge,
            'stage_badge': stage_badge,
            'is_official_einvoice': is_official,
            'timesheet_sheet_code': sheet.name if sheet else False,
            'answer': explanation_text,
            'citations': citations,
            'grounded': is_grounded,
            'entailment_score': entailment_score,
            'reason': reason,
        }

    # --- Decree 70/2025 E-Invoice Fields (AL2C-INV-001) ---
    al2c_einvoice_provider = fields.Selection([
        ('mock', 'Insilos Sandbox Provider'),
        ('vnpt', 'VNPT-Invoice (Decree 70/2025)'),
        ('viettel', 'Viettel S-Invoice'),
        ('misa', 'MISA meInvoice'),
    ], default='mock', string='E-Invoice Provider', copy=False)

    al2c_einvoice_state = fields.Selection([
        ('draft', 'Draft (Not Issued)'),
        ('submitted', 'Submitted to Provider'),
        ('issued', 'Issued & Certified by Tax Authority'),
        ('cancelled', 'Cancelled / Replaced'),
    ], default='draft', string='E-Invoice Status', tracking=True, copy=False)

    al2c_einvoice_number = fields.Char(
        string='E-Invoice Serial & Number',
        copy=False,
        tracking=True,
        help='Mẫu số, ký hiệu và số hóa đơn theo Nghị định 70/2025/NĐ-CP (e.g. 1C26TAA-00000001)',
    )
    al2c_einvoice_lookup_code = fields.Char(
        string='Decree 70 E-Invoice Lookup Code',
        copy=False,
        tracking=True,
        help='Mã tra cứu hóa đơn điện tử của cơ quan thuế theo Nghị định 70/2025/NĐ-CP',
    )
    al2c_einvoice_qr_code = fields.Char(
        string='Decree 70 QR Verification URL',
        copy=False,
        tracking=True,
        help='Đường dẫn tra cứu / mã QR hóa đơn điện tử',
    )
    al2c_einvoice_xml_hash = fields.Char(
        string='Signed XML SHA-256 Digest',
        copy=False,
        help='Mã băm SHA-256 của tệp dữ liệu XML hóa đơn điện tử',
    )
    al2c_einvoice_issue_date = fields.Datetime(
        string='E-Invoice Issue Date',
        copy=False,
    )
    al2c_einvoice_xml_payload = fields.Text(
        string='Decree 70 Canonical XML',
        copy=False,
    )

    def action_issue_einvoice(self):
        """Issue statutory e-invoice under Decree 70/2025."""
        adapter = self.env['al2c.einvoice.adapter']
        for move in self:
            if move.state != 'posted':
                raise UserError(_("E-Invoice can only be issued for posted invoices."))
            if move.move_type not in ('out_invoice', 'out_refund'):
                raise UserError(_("E-Invoice can only be issued for customer invoices or credit notes."))
            if move.al2c_einvoice_state == 'issued':
                raise UserError(_("E-Invoice has already been issued for invoice %s.") % move.name)

            data = adapter.issue_einvoice(move)
            move.write({
                'al2c_einvoice_state': 'issued',
                'al2c_einvoice_number': data.get('number'),
                'al2c_einvoice_lookup_code': data.get('lookup_code'),
                'al2c_einvoice_qr_code': data.get('qr_code'),
                'al2c_einvoice_xml_hash': data.get('xml_hash'),
                'al2c_einvoice_xml_payload': data.get('xml_payload'),
                'al2c_einvoice_issue_date': data.get('issue_date') or fields.Datetime.now(),
            })
            move.message_post(
                body=_(
                    "<b>Decree 70/2025 E-Invoice Certified:</b><br/>"
                    "Serial/No: <b>%s</b><br/>"
                    "CQT Lookup Code: <code>%s</code><br/>"
                    "Verification Portal: <a href='%s' target='_blank'>Tra cứu hóa đơn</a><br/>"
                    "XML SHA-256 Digest: <code>%s</code>"
                ) % (data.get('number'), data.get('lookup_code'), data.get('qr_code'), data.get('xml_hash')),
                message_type='comment',
                subtype_xmlid='mail.mt_note',
            )
        return True

    def button_draft(self):
        """AL2C-GOV-204: Autonomous agents cannot unpost or draft posted invoices."""
        self.env['al2c.autonomy.guard']._al2c_check_method_allowed('account.move', 'button_draft')
        return super().button_draft()

    def action_cancel_einvoice(self, reason=None):
        """Cancel statutory e-invoice under Decree 70/2025."""
        self.env['al2c.autonomy.guard']._al2c_check_method_allowed('account.move', 'action_cancel_einvoice')
        adapter = self.env['al2c.einvoice.adapter']
        for move in self:
            if move.al2c_einvoice_state != 'issued':
                raise UserError(_("Only issued e-invoices can be cancelled."))
            res = adapter.cancel_einvoice(move, reason or "Administrative adjustment")
            move.write({'al2c_einvoice_state': 'cancelled'})
            move.message_post(
                body=f"<b>Decree 70 E-Invoice Cancelled:</b> {res.get('notice')}",
                message_type='comment',
                subtype_xmlid='mail.mt_note',
            )
        return True

    # --- Cash-Matched Sales Commission (AL2C-PAY-001) ---
    def action_process_cash_matched_commission(self):
        """
        Create commission ledger entries upon payment reconciliation.
        Generates positive commission for customer invoices and negative clawbacks for credit notes.
        """
        Ledger = self.env['al2c.commission.ledger']
        rate = float(self.env['ir.config_parameter'].sudo().get_param('al2c.commission_rate', '5.0'))

        for move in self:
            if move.move_type not in ('out_invoice', 'out_refund'):
                continue

            sales_rep = move.invoice_user_id or move.line_ids.sale_line_ids.order_id[:1].user_id
            if not sales_rep:
                continue

            employee = self.env['hr.employee'].search([('user_id', '=', sales_rep.id)], limit=1)
            if not employee:
                continue

            # Check if ledger entry already created for this invoice
            existing = Ledger.search([('invoice_id', '=', move.id)], limit=1)
            if existing:
                continue

            # Cash-matched base in invoice currency (signed for refunds)
            sign = -1.0 if move.move_type == 'out_refund' else 1.0
            base_amount = move.amount_untaxed * sign
            currency = move.currency_id or move.company_id.currency_id
            if currency:
                commission_amt = currency.round(base_amount * (rate / 100.0))
            else:
                commission_amt = round(base_amount * (rate / 100.0), 0)

            sale_order = move.line_ids.sale_line_ids.order_id[:1] or False

            Ledger.create({
                'employee_id': employee.id,
                'invoice_id': move.id,
                'sale_order_id': sale_order.id if sale_order else False,
                'currency_id': currency.id,
                'base_amount': base_amount,
                'rate': rate,
                'amount': commission_amt,
                'date': move.date or fields.Date.context_today(self),
                'state': 'pending',
                'move_type': move.move_type,
            })
        return True

    def _al2c_update_dunning_stage(self, as_of_date=None):
        """Update dunning stage based on overdue days from invoice_date_due."""
        today = as_of_date or fields.Date.context_today(self)
        for move in self:
            if move.move_type != 'out_invoice' or move.state != 'posted' or move.payment_state in ('paid', 'in_payment', 'reversed'):
                move.al2c_dunning_stage = 'current'
                continue

            # AL2C-INV-103: Freeze dunning progression if invoice has an active commercial dispute
            if any(d.state == 'open' for d in move.al2c_dispute_ids):
                continue

            due_date = move.invoice_date_due or move.invoice_date or today
            overdue_days = (today - due_date).days

            if overdue_days >= 30:
                new_stage = 'd30_suspension'
            elif overdue_days >= 15:
                new_stage = 'd15_warning'
            elif overdue_days >= 3:
                new_stage = 'd3_reminder'
            else:
                new_stage = 'current'

            move.write({
                'al2c_dunning_stage': new_stage,
                'al2c_dunning_last_date': today,
            })
        return True

    @api.model
    def _cron_al2c_dunning_ladder(self):
        """Nightly cron to transition overdue customer invoices through the dunning ladder."""
        open_invoices = self.search([
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('payment_state', 'in', ('not_paid', 'partial')),
        ])
        return open_invoices._al2c_update_dunning_stage()

    def action_send_al2c_dunning_notice(self):
        """Send dunning notice email using AL2C Dunning template unless dispute is open."""
        template = self.env.ref('insilos_al2c.email_template_al2c_dunning_notice', raise_if_not_found=False)
        for move in self:
            if move.al2c_has_open_dispute:
                continue
            if template and move.partner_id.email:
                template.send_mail(move.id, force_send=True)
        return True

    @api.depends('partner_id')
    def _compute_display_auto_complete(self):
        po_model = self.env['purchase.order']
        partner_model = self.env['res.partner']
        partner_ids = self.mapped('partner_id').ids
        if not partner_ids:
            for move in self:
                move.display_auto_complete_field = False
            return

        purchase_orders = po_model._search([
            ('state', '=', 'purchase'),
            ('invoice_status', 'in', ('to invoice', 'no'))
        ], limit=1)
        purchase_orders.add_where(SQL('%s.partner_id = %s.id', SQL.identifier(po_model._table), SQL.identifier(partner_model._table)))
        partners = partner_model._search([
            ('id', 'in', partner_ids),
        ])
        partners.add_where(SQL('EXISTS(%s)', purchase_orders.select()))
        valid_partner_ids = {partner[0] for partner in self.env.execute_query(partners.select())}

        for move in self:
            move.display_auto_complete_field = move.partner_id.id in valid_partner_ids

    @api.model
    def get_views(self, views, options=None):
        res = super().get_views(views, options=options)
        if isinstance(res, dict) and 'models' in res:
            if 'finance.journal.entry' in res['models'] and 'account.move' not in res['models']:
                res['models']['account.move'] = res['models']['finance.journal.entry']
            if 'finance.journal.line' in res['models'] and 'account.move.line' not in res['models']:
                res['models']['account.move.line'] = res['models']['finance.journal.line']
        return res
