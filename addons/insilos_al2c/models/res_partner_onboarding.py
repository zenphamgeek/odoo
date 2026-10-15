# -*- coding: utf-8 -*-
import base64
import html
import logging
import re

from odoo import SUPERUSER_ID, api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

GENERIC_EMAIL_DOMAINS = {
    'gmail.com', 'googlemail.com', 'yahoo.com', 'yahoo.com.vn',
    'outlook.com', 'hotmail.com', 'live.com', 'icloud.com',
    'msn.com', 'aol.com', 'protonmail.com', 'proton.me', 'zoho.com',
}

TIER_DEFAULT_CREDIT_LIMIT = {
    'tier_s': 2_000_000_000.0,
    'tier_a': 500_000_000.0,
    'tier_b': 100_000_000.0,
    'tier_c': 0.0,
}

GROUP_BASE_SCORE = {
    'strategic_b2b': 45,
    'global_platform': 45,
    'gov_edu': 45,
    'infra_vendor': 35,
    'sme_commercial': 20,
}

GROUP_LABELS = {
    'strategic_b2b': 'Đối tác Chiến lược & Tập đoàn (Strategic B2B / Telco)',
    'global_platform': 'Nền tảng Quốc tế & Xuất khẩu 0% VAT (Global Platform)',
    'sme_commercial': 'Khách hàng Doanh nghiệp SME (SME Commercial)',
    'gov_edu': 'Khối Giáo dục & Hành chính công (Gov / Edu)',
    'infra_vendor': 'Nhà cung cấp Hạ tầng & Pháp lý (Infra / Tax / CA Vendor)',
}

TIER_LABELS = {
    'tier_s': 'Hạng S — Đối tác Chiến lược / Key Account (TCV ≥ 500M VND • Công nợ 30-45 ngày)',
    'tier_a': 'Hạng A — Đối tác Trọng điểm B2B (TCV 100M-500M VND • Công nợ Milestone 15-30 ngày)',
    'tier_b': 'Hạng B — Đối tác Thương mại Chuẩn / Fast-Track (TCV < 100M VND • Chuẩn)',
    'tier_c': 'Hạng C — Đối tác Mới / Thử nghiệm (Provisional • Trả trước 100%)',
}

PAYMENT_RAIL_LABELS = {
    'vcb_digibiz': 'VCB DigiBiz 11-Column / Napas247 (VND)',
    'swift_usd': 'SWIFT Foreign Wire USD/AUD (0% Export SLA)',
    'prepaid_only': '100% Prepayment Only (Trả trước 100%)',
}

ONBOARDING_STATE_LABELS = {
    'provisional': 'Tạm thời — Mở cho Sales (Provisional • Sales Unblocked)',
    'docs_ready': 'Đã tạo Bộ Hồ sơ Đi kèm (Companion Docs Generated)',
    'under_review': 'Chờ Phê duyệt Mã Partner (Pending Finance/Legal Approval)',
    'approved': 'Đã Phê duyệt Mã Chính thức (Official Partner Code Active)',
    'suspended': 'Tạm khóa Thanh toán (Payment Gate Hold)',
}


class ResPartnerOnboarding(models.Model):
    _inherit = 'res.partner'

    dgm_partner_group = fields.Selection(
        selection=[
            ('strategic_b2b', 'Đối tác Chiến lược & Tập đoàn (Strategic B2B / Telco)'),
            ('global_platform', 'Nền tảng Quốc tế & Xuất khẩu 0% VAT (Global Platform)'),
            ('sme_commercial', 'Khách hàng Doanh nghiệp SME (SME Commercial)'),
            ('gov_edu', 'Khối Giáo dục & Hành chính công (Gov / Edu)'),
            ('infra_vendor', 'Nhà cung cấp Hạ tầng & Pháp lý (Infra / Tax / CA Vendor)'),
        ],
        string='Nhóm Đối tác (Partner Group)',
        default='sme_commercial',
        tracking=True,
        index=True,
    )

    dgm_partner_tier = fields.Selection(
        selection=[
            ('tier_s', 'Hạng S — Đối tác Chiến lược / Key Account (TCV ≥ 500M VND • Công nợ 30-45 ngày)'),
            ('tier_a', 'Hạng A — Đối tác Trọng điểm B2B (TCV 100M-500M VND • Công nợ Milestone 15-30 ngày)'),
            ('tier_b', 'Hạng B — Đối tác Thương mại Chuẩn / Fast-Track (TCV < 100M VND • Chuẩn)'),
            ('tier_c', 'Hạng C — Đối tác Mới / Thử nghiệm (Provisional • Trả trước 100%)'),
        ],
        string='Hạng Đối tác (Partner Tier)',
        compute='_compute_dgm_tier_and_terms',
        store=True,
        readonly=False,
        tracking=True,
        index=True,
    )

    dgm_tier_score = fields.Integer(
        string='Điểm Xếp hạng (Tier Score 0-100)',
        compute='_compute_dgm_tier_and_terms',
        store=True,
        readonly=False,
    )

    dgm_credit_limit_vnd = fields.Float(
        string='Hạn mức Công nợ (Credit Limit VND)',
        compute='_compute_dgm_tier_and_terms',
        store=True,
        readonly=False,
    )

    dgm_allowed_payment_rail = fields.Selection(
        selection=[
            ('vcb_digibiz', 'VCB DigiBiz 11-Column / Napas247 (VND)'),
            ('swift_usd', 'SWIFT Foreign Wire USD/AUD (0% Export SLA)'),
            ('prepaid_only', '100% Prepayment Only (Trả trước 100%)'),
        ],
        string='Kênh Thanh toán Chuẩn (Allowed Payment Rail)',
        compute='_compute_dgm_tier_and_terms',
        store=True,
        readonly=False,
    )

    dgm_onboarding_state = fields.Selection(
        selection=[
            ('provisional', 'Tạm thời — Mở cho Sales (Provisional • Sales Unblocked)'),
            ('docs_ready', 'Đã tạo Bộ Hồ sơ Đi kèm (Companion Docs Generated)'),
            ('under_review', 'Chờ Phê duyệt Mã Partner (Pending Finance/Legal Approval)'),
            ('approved', 'Đã Phê duyệt Mã Chính thức (Official Partner Code Active)'),
            ('suspended', 'Tạm khóa Thanh toán (Payment Gate Hold)'),
        ],
        string='Trạng thái On-boarding (SOP-DGM-06)',
        default='provisional',
        tracking=True,
        index=True,
        copy=False,
    )

    dgm_provisional_code = fields.Char(
        string='Mã Tạm thời (Provisional Code)',
        copy=False,
        index=True,
        help='Mã tạm thời TMP-DGM-XXXX cấp ngay lập tức để Sales tạo báo giá, xác nhận đơn hàng và thu tiền tạm ứng không bị nghẽn.',
    )

    dgm_partner_code = fields.Char(
        string='Mã Đối tác Chính thức (Official Partner Code)',
        copy=False,
        index=True,
        tracking=True,
        help='Mã chính thức PTN-DGM-2026-XXXX cấp sau khi hoàn tất bộ 4 chứng từ On-boarding và được phê duyệt.',
    )

    dgm_sales_flex_mode = fields.Boolean(
        string='Ưu tiên Linh hoạt Sales (Sales Unblocked Mode)',
        default=True,
        help='Đảm bảo Sales Team không bao giờ bị chặn khi tạo Lead, gửi Báo giá, hay xác nhận Sale Order.',
    )

    dgm_canonical_partner_id = fields.Many2one(
        'res.partner',
        string='Đối tác Gốc Chuẩn hóa (Canonical Partner)',
        copy=False,
        index=True,
        help='Liên kết tự động tới đối tác chuẩn khi phát hiện trùng Mã số thuế (VAT) hoặc tên miền email doanh nghiệp.',
    )

    dgm_conflict_warning = fields.Char(
        string='Cảnh báo Trùng lặp Đối tác (Non-Blocking)',
        copy=False,
    )

    dgm_onboarding_folder_id = fields.Many2one(
        'documents.document',
        string='Thư mục Hồ sơ On-boarding',
        copy=False,
    )

    dgm_onboarding_doc_ids = fields.Many2many(
        'documents.document',
        'dgm_partner_onboarding_doc_rel',
        'partner_id',
        'document_id',
        string='Bộ Chứng từ On-boarding Đi kèm (TPL-ONB-01..04)',
        copy=False,
    )

    dgm_onboarding_doc_count = fields.Integer(
        string='Số lượng Chứng từ Đi kèm',
        compute='_compute_dgm_onboarding_docs',
        store=True,
    )

    dgm_all_companion_docs_ready = fields.Boolean(
        string='Đủ 4 Chứng từ On-boarding Chuẩn',
        compute='_compute_dgm_onboarding_docs',
        store=True,
    )

    dgm_approved_by = fields.Many2one(
        'res.users',
        string='Người Phê duyệt Mã Partner',
        copy=False,
        readonly=True,
    )

    dgm_approved_date = fields.Datetime(
        string='Thời điểm Phê duyệt Mã Partner',
        copy=False,
        readonly=True,
    )

    dgm_payment_gate_override = fields.Boolean(
        string='Cho phép Ngoại lệ Thanh toán (Payment Gate Override)',
        default=False,
        copy=False,
    )

    def init(self):
        if hasattr(super(), "init"):
            super().init()
        self.env.cr.execute(
            """
            SELECT relname, relkind
              FROM pg_class
             WHERE relname IN ('res_partner', 'party_master', 'documents_document')
               AND relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
            """
        )
        rels = dict(self.env.cr.fetchall() or [])
        partner_tbl = (
            "party_master"
            if rels.get("res_partner") == "v" and rels.get("party_master") == "r"
            else "res_partner"
        )
        for raw_sql in (
            "CREATE INDEX IF NOT EXISTS idx_res_partner_dgm_onboarding_cover ON res_partner (is_company, customer_rank DESC, active, dgm_onboarding_state, dgm_partner_tier) WHERE active = TRUE",
            "CREATE INDEX IF NOT EXISTS idx_res_partner_dgm_partner_code ON res_partner (dgm_partner_code) WHERE dgm_partner_code IS NOT NULL",
        ):
            if rels.get(partner_tbl) == "r":
                self.env.cr.execute(raw_sql.replace(" ON res_partner ", f" ON {partner_tbl} "))
        if rels.get("documents_document") == "r":
            self.env.cr.execute(
                "CREATE INDEX IF NOT EXISTS idx_documents_partner_folder_rel ON documents_document (partner_id, folder_id) WHERE active = TRUE AND partner_id IS NOT NULL"
            )

    # -------------------------------------------------------------------------
    # Computed Methods
    # -------------------------------------------------------------------------
    @api.depends('dgm_onboarding_doc_ids', 'dgm_onboarding_doc_ids.active')
    def _compute_dgm_onboarding_docs(self):
        for partner in self:
            active_docs = partner.dgm_onboarding_doc_ids.filtered(lambda d: d.active and d.type != 'folder')
            count = len(active_docs)
            partner.dgm_onboarding_doc_count = count
            partner.dgm_all_companion_docs_ready = count >= 4

    @api.depends(
        'dgm_partner_group',
        'vat',
        'country_id',
        'bank_ids',
        'dgm_all_companion_docs_ready',
        'dgm_onboarding_state',
    )
    def _compute_dgm_tier_and_terms(self):
        for partner in self:
            group = partner.dgm_partner_group or 'sme_commercial'
            score = GROUP_BASE_SCORE.get(group, 20)

            has_vat = bool(partner.vat and str(partner.vat).strip())
            is_foreign = bool(partner.country_id and partner.country_id.code not in ('VN', False))
            if has_vat or is_foreign:
                score += 20

            has_bank = bool(partner.bank_ids)
            if has_bank or group in ('strategic_b2b', 'global_platform', 'gov_edu', 'infra_vendor'):
                score += 15

            if partner.dgm_all_companion_docs_ready or partner.dgm_onboarding_state == 'approved':
                score += 20

            score = min(100, max(0, score))
            partner.dgm_tier_score = score

            # Determine tier if not explicitly locked or compute from group/score
            current_tier = partner._origin.dgm_partner_tier if partner._origin else False
            if group in ('strategic_b2b', 'global_platform', 'gov_edu') or score >= 85:
                tier = 'tier_s'
            elif group == 'infra_vendor' or score >= 65:
                tier = 'tier_a'
            elif has_vat or is_foreign or score >= 35:
                tier = 'tier_b'
            else:
                tier = 'tier_c'

            if current_tier and current_tier in TIER_DEFAULT_CREDIT_LIMIT and group == (partner._origin.dgm_partner_group or 'sme_commercial'):
                tier = current_tier

            partner.dgm_partner_tier = tier
            partner.dgm_credit_limit_vnd = TIER_DEFAULT_CREDIT_LIMIT.get(tier, 0.0)

            if group in ('global_platform', 'gov_edu') or is_foreign:
                partner.dgm_allowed_payment_rail = 'swift_usd'
            elif tier == 'tier_c':
                partner.dgm_allowed_payment_rail = 'prepaid_only'
            else:
                partner.dgm_allowed_payment_rail = 'vcb_digibiz'

    # -------------------------------------------------------------------------
    # Code Generators & Anti-Conflict Deduplication
    # -------------------------------------------------------------------------
    @api.model
    def _next_dgm_provisional_code(self, partner_id=None):
        seq_val = self.env['ir.sequence'].sudo().next_by_code('dgm.partner.provisional')
        if seq_val:
            return seq_val
        suffix = f"{partner_id:04d}" if partner_id else f"{self.sudo().search_count([]) + 1:04d}"
        return f"TMP-DGM-{suffix}"

    @api.model
    def _next_dgm_partner_code(self, partner_id=None):
        seq_val = self.env['ir.sequence'].sudo().next_by_code('dgm.partner.official')
        if seq_val:
            return seq_val
        approved_count = self.sudo().search_count([('dgm_partner_code', '=like', 'PTN-DGM-2026-%')])
        next_num = max(approved_count + 1, 7)
        while self.sudo().search_count([('dgm_partner_code', '=', f"PTN-DGM-2026-{next_num:04d}")]) > 0:
            next_num += 1
        return f"PTN-DGM-2026-{next_num:04d}"

    @staticmethod
    def _normalize_vat_code(vat_str):
        if not vat_str:
            return ''
        return re.sub(r'[^0-9A-Za-z\-]', '', str(vat_str).strip()).upper()

    @staticmethod
    def _extract_business_domain(email_str):
        if not email_str or '@' not in str(email_str):
            return ''
        domain = str(email_str).strip().lower().split('@')[-1].strip(' >')
        if domain in GENERIC_EMAIL_DOMAINS:
            return ''
        return domain

    def _resolve_or_link_existing_partner(self):
        """Conflict-free deduplication: detects existing canonical partner by VAT or business email domain
        and links `dgm_canonical_partner_id` (and reuses canonical partner code if approved)
        WITHOUT raising any blocking error for Sales Team!
        """
        Partner = self.env['res.partner'].sudo()
        vat_candidates = None
        for partner in self:
            if not (partner.id and isinstance(partner.id, int) and partner.id > 0):
                continue
            if partner.dgm_canonical_partner_id:
                continue
            if not partner.is_company and not partner.vat:
                continue
            norm_vat = self._normalize_vat_code(partner.vat)
            biz_domain = self._extract_business_domain(partner.email)
            if not norm_vat and not biz_domain:
                continue
            existing = Partner.browse()

            if norm_vat:
                if vat_candidates is None:
                    vat_candidates = Partner.search([
                        ('id', '!=', partner.id),
                        ('active', '=', True),
                        ('vat', '!=', False),
                    ], order='id asc')
                for cand in vat_candidates:
                    if cand.id == partner.id:
                        continue
                    if self._normalize_vat_code(cand.vat) == norm_vat:
                        if cand.dgm_onboarding_state == 'approved' or not existing:
                            existing = cand
                            if cand.dgm_onboarding_state == 'approved':
                                break

            if not existing and biz_domain and partner.is_company:
                candidates = Partner.search([
                    ('id', '!=', partner.id),
                    ('active', '=', True),
                    ('is_company', '=', True),
                    ('email', 'ilike', f'%@{biz_domain}'),
                ], order='id asc', limit=5)
                for cand in candidates:
                    if self._extract_business_domain(cand.email) == biz_domain:
                        existing = cand
                        break

            if existing:
                canonical = existing.dgm_canonical_partner_id or existing
                warn_msg = (
                    f"Phát hiện đối tác trùng MST/Domain với [{canonical.dgm_partner_code or canonical.dgm_provisional_code or canonical.id}] "
                    f"{canonical.name}. Đã liên kết tự động về hồ sơ chuẩn để không chặn Sales!"
                )
                update_vals = {
                    'dgm_canonical_partner_id': canonical.id,
                    'dgm_conflict_warning': warn_msg,
                }
                if canonical.dgm_partner_code and not partner.dgm_partner_code:
                    update_vals['dgm_partner_code'] = canonical.dgm_partner_code
                if canonical.dgm_onboarding_state == 'approved' and partner.dgm_onboarding_state == 'provisional':
                    update_vals['dgm_onboarding_state'] = 'approved'
                if canonical.dgm_onboarding_doc_ids and not partner.dgm_onboarding_doc_ids:
                    update_vals['dgm_onboarding_doc_ids'] = [(6, 0, canonical.dgm_onboarding_doc_ids.ids)]
                partner.sudo().write(update_vals)
        return True

    def action_check_partner_conflict(self):
        """Interactive & programmatic helper to check and resolve partner VAT/domain conflicts non-blockingly."""
        self.ensure_one()
        self._resolve_or_link_existing_partner()
        if self.dgm_canonical_partner_id:
            canon = self.dgm_canonical_partner_id
            if isinstance(canon, int):
                canon = self.env['res.partner'].sudo().browse(canon)
            return {
                'has_conflict': True,
                'canonical_partner_id': canon.id,
                'canonical_partner_name': canon.name,
                'canonical_partner_code': canon.dgm_partner_code or canon.dgm_provisional_code,
                'message': self.dgm_conflict_warning,
            }
        return {
            'has_conflict': False,
            'canonical_partner_id': False,
            'canonical_partner_name': False,
            'canonical_partner_code': self.dgm_partner_code or self.dgm_provisional_code,
            'message': 'Không phát hiện trùng lặp MST/Domain.',
        }

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('dgm_onboarding_state'):
                vals['dgm_onboarding_state'] = 'provisional'
            if 'dgm_sales_flex_mode' not in vals:
                vals['dgm_sales_flex_mode'] = True
        records = super().create(vals_list)
        for rec in records:
            if not rec.dgm_provisional_code and rec.id and isinstance(rec.id, int) and rec.id > 0:
                rec.sudo().write({
                    'dgm_provisional_code': f"TMP-DGM-{rec.id:04d}",
                })
        try:
            records._resolve_or_link_existing_partner()
        except Exception as exc:
            _logger.debug("Non-blocking partner conflict resolution skipped on create: %s", exc)
        return records

    def write(self, vals):
        res = super().write(vals)
        if not self.env.context.get('skip_dgm_conflict_check') and ('vat' in vals or 'email' in vals):
            try:
                self.with_context(skip_dgm_conflict_check=True)._resolve_or_link_existing_partner()
            except Exception as exc:
                _logger.debug("Non-blocking partner conflict resolution skipped on write: %s", exc)
        return res

    # -------------------------------------------------------------------------
    # Companion Document Templates & Auto-Generator (TPL-ONB-01 .. TPL-ONB-04)
    # -------------------------------------------------------------------------
    def _get_or_create_dgm_onboarding_folder(self):
        """Locates `03. Hợp đồng & Thương mại (Commercial & Contracts)` ->
        `Hồ sơ On-boarding Đối tác (Partner KYC & MSA)` -> Partner Subfolder.
        Strictly maintains `access_internal = 'edit'` and `owner_id = False` per Rule 6.
        """
        self.ensure_one()
        Doc = self.env['documents.document'].sudo()

        if self.dgm_onboarding_folder_id and self.dgm_onboarding_folder_id.exists() and self.dgm_onboarding_folder_id.active:
            if self.dgm_onboarding_folder_id.owner_id or self.dgm_onboarding_folder_id.access_internal != 'edit':
                self.dgm_onboarding_folder_id.write({'owner_id': False, 'access_internal': 'edit'})
            return self.dgm_onboarding_folder_id

        # 1. Locate DGM Root Folder
        root_folder = self.env.ref('insilos_al2c.folder_dgm_root', raise_if_not_found=False)
        if not root_folder or not root_folder.exists():
            root_folder = Doc.search([
                ('type', '=', 'folder'),
                ('folder_id', '=', False),
                ('name', 'ilike', 'DGM'),
                ('active', '=', True),
            ], order='id asc', limit=1)

        # 2. Locate 03. Hợp đồng & Thương mại
        contracts_folder = self.env.ref('insilos_al2c.folder_dgm_contracts', raise_if_not_found=False)
        if not contracts_folder or not contracts_folder.exists():
            domain = [('type', '=', 'folder'), ('name', 'ilike', '03. Hợp đồng'), ('active', '=', True)]
            if root_folder:
                domain.append(('folder_id', '=', root_folder.id))
            contracts_folder = Doc.search(domain, order='id asc', limit=1)
        if not contracts_folder and root_folder:
            contracts_folder = Doc.create({
                'name': '03. Hợp đồng & Thương mại (Commercial & Contracts)',
                'type': 'folder',
                'folder_id': root_folder.id,
                'access_internal': 'edit',
                'access_via_link': 'view',
                'owner_id': False,
                'company_id': False,
            })

        parent_id = contracts_folder.id if contracts_folder else (root_folder.id if root_folder else False)

        # 3. Locate or create container `Hồ sơ On-boarding Đối tác (Partner KYC & MSA)`
        hub_name = 'Hồ sơ On-boarding Đối tác (Partner KYC & MSA)'
        hub_folder = Doc.search([
            ('type', '=', 'folder'),
            ('folder_id', '=', parent_id),
            ('name', '=', hub_name),
            ('active', '=', True),
        ], order='id asc', limit=1)
        if not hub_folder:
            hub_folder = Doc.create({
                'name': hub_name,
                'type': 'folder',
                'folder_id': parent_id,
                'access_internal': 'edit',
                'access_via_link': 'view',
                'owner_id': False,
                'company_id': False,
                'sequence': 5,
            })
        elif hub_folder.owner_id or hub_folder.access_internal != 'edit':
            hub_folder.write({'owner_id': False, 'access_internal': 'edit'})

        # 4. Locate or create Partner Subfolder
        code_badge = self.dgm_partner_code or self.dgm_provisional_code or f"TMP-DGM-{self.id:04d}"
        clean_name = (self.name or 'Partner').strip()
        partner_folder_name = f"{code_badge} · {clean_name}"

        partner_folder = Doc.search([
            ('type', '=', 'folder'),
            ('folder_id', '=', hub_folder.id),
            '|',
            ('partner_id', '=', self.id),
            ('name', 'ilike', clean_name),
            ('active', '=', True),
        ], order='id asc', limit=1)

        if not partner_folder:
            partner_folder = Doc.create({
                'name': partner_folder_name,
                'type': 'folder',
                'folder_id': hub_folder.id,
                'partner_id': self.id,
                'access_internal': 'edit',
                'access_via_link': 'view',
                'owner_id': False,
                'company_id': False,
            })
        else:
            partner_folder.write({
                'name': partner_folder_name,
                'partner_id': self.id,
                'owner_id': False,
                'access_internal': 'edit',
            })

        self.sudo().write({'dgm_onboarding_folder_id': partner_folder.id})
        return partner_folder

    def _render_companion_templates_payload(self):
        """Returns the 4 standardized SOP-DGM-06 HTML Companion Documents (`TPL-ONB-01`..`TPL-ONB-04`)
        populated with the partner's live metadata and Digimate JSC statutory credentials.
        """
        self.ensure_one()
        code = self.dgm_partner_code or self.dgm_provisional_code or f"TMP-DGM-{self.id:04d}"
        safe_code = re.sub(r'[^0-9A-Za-z_\-]', '_', code)
        p_name = html.escape(self.name or 'Đối tác')
        p_vat = html.escape(self.vat or 'N/A (Cross-Border / Chưa cấp MST)')
        p_street = html.escape(self.street or 'Theo địa chỉ đăng ký kinh doanh')
        p_email = html.escape(self.email or 'finance@partner.example')
        p_country = html.escape(self.country_id.name if self.country_id else 'Việt Nam')
        group_label = html.escape(GROUP_LABELS.get(self.dgm_partner_group, self.dgm_partner_group or ''))
        tier_label = html.escape(TIER_LABELS.get(self.dgm_partner_tier, self.dgm_partner_tier or ''))
        rail_label = html.escape(PAYMENT_RAIL_LABELS.get(self.dgm_allowed_payment_rail, self.dgm_allowed_payment_rail or ''))
        state_label = html.escape(ONBOARDING_STATE_LABELS.get(self.dgm_onboarding_state, self.dgm_onboarding_state or ''))
        credit_str = f"{self.dgm_credit_limit_vnd:,.0f} VND"
        bank_acc = html.escape(self.bank_ids[:1].acc_number if self.bank_ids else 'Theo thông báo tài khoản thụ hưởng chính thức')
        approver_raw = getattr(self.dgm_approved_by, 'name', None) or 'Lê Xuân Hoàng (Chủ tịch HĐQT & TGĐ) / Mai Thị Hồng Thắm (CFO)'
        approver_name = html.escape(approver_raw)
        approved_dt = str(self.dgm_approved_date or fields.Datetime.now())[:19]

        # Specific commercial clauses by partner group
        if self.dgm_partner_group == 'global_platform':
            msa_terms = (
                "Áp dụng thuế suất GTGT 0% (Dịch vụ phần mềm & nội dung số xuất khẩu theo Nghị định 70/2025/NĐ-CP và Luật Thuế GTGT 48/2024/QH15). "
                "Cam kết SLA xuất hóa đơn điện tử (1C26TAA) trong vòng 24 giờ kể từ thời điểm ngân hàng báo Có ngoại tệ USD/AUD về tài khoản VCB 1202703007."
            )
        elif self.dgm_partner_group == 'strategic_b2b':
            msa_terms = (
                "Áp dụng mô hình triển khai SAP Activate 5 giai đoạn (Prepare, Explore, Realize, Deploy, Run) hoặc cử kỹ sư Onsite B2B. "
                "Nghiệm thu theo Biên bản xác nhận Timesheet / Milestone điện tử, điều khoản công nợ Net 30-40 ngày và Overtime 2 bậc minh bạch."
            )
        elif self.dgm_partner_group == 'gov_edu':
            msa_terms = (
                "Tuân thủ thỏa thuận bảo vệ dữ liệu học sinh & giáo dục công lập (CA-NDPA v1.5 / FERPA / COPPA 45-day privacy SLA) "
                "và Nghị định 13/2023/NĐ-CP. Không lưu trữ trái phép PII người học."
            )
        elif self.dgm_partner_group == 'infra_vendor':
            msa_terms = (
                "Nhà cung cấp hạ tầng viễn thông, chữ ký số và hóa đơn điện tử. Bắt buộc xuất hóa đơn GTGT điện tử hợp lệ ghi đúng "
                "CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ - MST 0317958465 và phân bổ chi phí trả trước qua Tài khoản 242 theo kỳ hạn hợp đồng."
            )
        else:
            msa_terms = (
                "Khung thương mại tiêu chuẩn B2B SME: linh hoạt xác nhận đơn hàng ngay cho Sales Team với Mã Tạm thời (TMP-DGM), "
                "hoàn tất đối soát chứng từ và phê duyệt Mã Đối tác chính thức (PTN-DGM-2026) trước khi giải ngân hoặc cấp hạn mức công nợ."
            )

        base_style = """
        <style>
            body { font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: #0f172a; line-height: 1.55; padding: 28px; max-width: 920px; margin: 0 auto; }
            .header-box { border-bottom: 3px solid #1e3a8a; padding-bottom: 14px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: flex-start; }
            .badge { display: inline-block; padding: 4px 10px; border-radius: 6px; font-weight: 700; font-size: 12px; background: #dbeafe; color: #1e40af; }
            table { width: 100%; border-collapse: collapse; margin: 14px 0; }
            th, td { border: 1px solid #cbd5e1; padding: 9px 12px; text-align: left; font-size: 13.5px; }
            th { background: #f1f5f9; font-weight: 600; width: 32%; }
            h1 { font-size: 20px; color: #1e3a8a; margin: 6px 0; }
            h2 { font-size: 15px; color: #0f172a; margin-top: 18px; border-left: 4px solid #2563eb; padding-left: 8px; }
            .sig-grid { display: flex; justify-content: space-between; margin-top: 28px; gap: 20px; }
            .sig-col { width: 48%; border: 1px dashed #94a3b8; padding: 14px; border-radius: 8px; }
        </style>
        """

        doc_01 = f"""<!DOCTYPE html>
<html lang="vi"><head><meta charset="utf-8"/><title>TPL-ONB-01 KYC &amp; Tiering - {p_name}</title>{base_style}</head>
<body>
    <div class="header-box">
        <div>
            <div><strong>CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ (DIGIMATE JSC)</strong></div>
            <div>MST: <strong>0317958465</strong> • Đ/c: Số 52 Đường B4, Phường Tây Thạnh / Số 11 Đường số 3, KDC CityLand, Phường Tân Mỹ, TP.HCM</div>
        </div>
        <div class="badge">TPL-ONB-01 • SOP-DGM-06</div>
    </div>
    <h1>PHIẾU KHAI BÁO KYC, ĐÁNH GIÁ TÍN NHIỆM &amp; XẾP HẠNG ĐỐI TÁC</h1>
    <p>Hồ sơ định danh pháp nhân và phân hạng rủi ro tín dụng trước khi cấp Mã Đối tác Chính thức vào hệ thống ERP Insilos 20.</p>
    <table>
        <tr><th>Mã Đối tác (Partner Code)</th><td><strong>{html.escape(code)}</strong> ({state_label})</td></tr>
        <tr><th>Tên Pháp nhân Đối tác</th><td><strong>{p_name}</strong></td></tr>
        <tr><th>Mã số thuế / Định danh (VAT/Tax ID)</th><td><strong>{p_vat}</strong> ({p_country})</td></tr>
        <tr><th>Địa chỉ Trụ sở Pháp lý</th><td>{p_street}</td></tr>
        <tr><th>Email Nhận Hóa đơn Điện tử &amp; Đối soát</th><td>{p_email}</td></tr>
        <tr><th>Phân nhóm Đối tác (Partner Group)</th><td>{group_label}</td></tr>
        <tr><th>Xếp hạng Đối tác (Partner Tier)</th><td><strong>{tier_label}</strong></td></tr>
        <tr><th>Điểm Tín nhiệm Tự động (Tier Score)</th><td><strong>{self.dgm_tier_score} / 100 điểm</strong></td></tr>
        <tr><th>Hạn mức Công nợ Tối đa (Credit Limit)</th><td><strong>{credit_str}</strong></td></tr>
        <tr><th>Kênh Thanh toán Được Phép (Payment Rail)</th><td>{rail_label}</td></tr>
        <tr><th>Tài khoản Ngân hàng Đối tác</th><td>{bank_acc}</td></tr>
    </table>
    <h2>Cam kết Linh hoạt Sales-First (Zero Bottleneck Policy)</h2>
    <p>Đối tác được cấp ngay mã tạm <code>{html.escape(self.dgm_provisional_code or code)}</code> để Sales Team gửi báo giá, ký hợp đồng và xác nhận Sale Order không độ trễ. Toàn bộ kiểm soát hạn mức và cổng thanh toán tự động kích hoạt trước kỳ giải ngân hoặc thanh toán công nợ.</p>
</body></html>"""

        doc_02 = f"""<!DOCTYPE html>
<html lang="vi"><head><meta charset="utf-8"/><title>TPL-ONB-02 Mutual NDA ISO27001 - {p_name}</title>{base_style}</head>
<body>
    <div class="header-box">
        <div>
            <div><strong>CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ (DIGIMATE JSC)</strong></div>
            <div>MST: <strong>0317958465</strong> • ISO/IEC 27001 &amp; ISO/IEC 27701 Privacy Governance</div>
        </div>
        <div class="badge">TPL-ONB-02 • NDA</div>
    </div>
    <h1>THỎA THUẬN BẢO MẬT THÔNG TIN SONG NGỮ (MUTUAL NON-DISCLOSURE AGREEMENT)</h1>
    <table>
        <tr><th>Bên A (Party A)</th><td><strong>CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ (DIGIMATE JSC)</strong> — MST: <strong>0317958465</strong><br/>Địa chỉ: Số 52 Đường B4, Phường Tây Thạnh (Số 11, Đường số 3, KDC CityLand, Phường Tân Mỹ), TP.HCM</td></tr>
        <tr><th>Bên B (Party B)</th><td><strong>{p_name}</strong> — MST: <strong>{p_vat}</strong><br/>Địa chỉ: {p_street}</td></tr>
        <tr><th>Mã Hồ sơ Liên kết</th><td><strong>{html.escape(code)}</strong></td></tr>
    </table>
    <h2>Điều 1. Phạm vi Bảo mật &amp; Bảo vệ Dữ liệu Cá nhân (ISO/IEC 27001 &amp; Nghị định 13/2023/NĐ-CP)</h2>
    <p>Hai Bên cam kết bảo mật tuyệt đối toàn bộ mã nguồn, kiến trúc hệ thống, đơn giá thương mại, thông tin khách hàng và dữ liệu cá nhân (PII) được trao đổi trong quá trình hợp tác theo tiêu chuẩn ISO/IEC 27001, ISO/IEC 27701 và Nghị định 13/2023/NĐ-CP.</p>
    <h2>Điều 2. Không Tiết lộ Khóa Bí mật &amp; Tự động Ẩn Danh (Zero-Leak Sanitization)</h2>
    <p>Mọi tài liệu kỹ thuật, nhật ký vận hành và báo cáo đối soát giữa Bên A và Bên B không được chứa khóa mật (API Keys, DSN, Token) và phải che khuyết (Partial Masking) dữ liệu nhạy cảm theo nguyên tắc Need-to-Know.</p>
    <div class="sig-grid">
        <div class="sig-col"><strong>ĐẠI DIỆN BÊN A (DIGIMATE JSC)</strong><br/>Lê Xuân Hoàng — Chủ tịch HĐQT &amp; TGĐ<br/><em>(Đã ký số HSM Viettel-CA — MST 0317958465)</em></div>
        <div class="sig-col"><strong>ĐẠI DIỆN BÊN B ({p_name})</strong><br/>Đại diện Pháp luật / Ủy quyền<br/><em>(Xác nhận đồng thuận điện tử)</em></div>
    </div>
</body></html>"""

        doc_03 = f"""<!DOCTYPE html>
<html lang="vi"><head><meta charset="utf-8"/><title>TPL-ONB-03 Master Commercial Frame - {p_name}</title>{base_style}</head>
<body>
    <div class="header-box">
        <div>
            <div><strong>CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ (DIGIMATE JSC)</strong></div>
            <div>MST: <strong>0317958465</strong> • Tài khoản VCB: <strong>1202703007</strong> (CN Tân Định)</div>
        </div>
        <div class="badge">TPL-ONB-03 • MSA &amp; SLA</div>
    </div>
    <h1>HỢP ĐỒNG NGUYÊN TẮC / KHUNG THƯƠNG MẠI &amp; CAM KẾT CHẤT LƯỢNG DỊCH VỤ (MSA &amp; SLA)</h1>
    <table>
        <tr><th>Pháp nhân Cung cấp / Ký kết</th><td><strong>CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ (DIGIMATE JSC)</strong> (MST: 0317958465)</td></tr>
        <tr><th>Đối tác Ký kết</th><td><strong>{p_name}</strong> (MST: {p_vat}) — Mã: <strong>{html.escape(code)}</strong></td></tr>
        <tr><th>Phân nhóm &amp; Hạng Đối tác</th><td>{group_label} • <strong>{tier_label}</strong></td></tr>
        <tr><th>Hạn mức Tín dụng &amp; Thanh toán</th><td>Hạn mức: <strong>{credit_str}</strong> • Kênh: <strong>{rail_label}</strong></td></tr>
    </table>
    <h2>Điều khoản Thương mại &amp; Thuế Đặc thù theo Nhóm Đối tác</h2>
    <p>{html.escape(msa_terms)}</p>
    <h2>Quy định Xuất Hóa đơn Điện tử Chuẩn Nghị định 70/2025/NĐ-CP</h2>
    <p>Mọi hóa đơn GTGT đầu ra (Ký hiệu <code>1C26TAA</code>) và hóa đơn đầu vào phải ghi nhận chính xác tên pháp nhân <strong>CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ</strong>, Mã số thuế <strong>0317958465</strong>.</p>
</body></html>"""

        doc_04 = f"""<!DOCTYPE html>
<html lang="vi"><head><meta charset="utf-8"/><title>TPL-ONB-04 Payment Gate Approval Cert - {p_name}</title>{base_style}</head>
<body>
    <div class="header-box">
        <div>
            <div><strong>CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ (DIGIMATE JSC)</strong></div>
            <div>MST: <strong>0317958465</strong> • Cổng Kiểm soát Thanh toán Nội bộ (SOP-DGM-06)</div>
        </div>
        <div class="badge">TPL-ONB-04 • PAYMENT GATE CERT</div>
    </div>
    <h1>CHỨNG NHẬN PHÊ DUYỆT MÃ ĐỐI TÁC &amp; QUY TẮC CỔNG THANH TOÁN (PAYMENT GATE)</h1>
    <table>
        <tr><th>Mã Đối tác Chính thức</th><td><strong>{html.escape(self.dgm_partner_code or 'ĐANG CHỜ CẤP MÃ CHÍNH THỨC (PROVISIONAL: ' + code + ')')}</strong></td></tr>
        <tr><th>Mã Tạm thời (Sales Flex)</th><td><code>{html.escape(self.dgm_provisional_code or code)}</code></td></tr>
        <tr><th>Tên Đối tác</th><td><strong>{p_name}</strong> (MST: <strong>{p_vat}</strong>)</td></tr>
        <tr><th>Trạng thái Phê duyệt</th><td><strong>{state_label}</strong></td></tr>
        <tr><th>Kênh Thanh toán Phê duyệt</th><td><strong>{rail_label}</strong></td></tr>
        <tr><th>Người Phê duyệt &amp; Thời điểm</th><td>{approver_name} ({approved_dt})</td></tr>
    </table>
    <h2>Danh mục Kiểm tra Bắt buộc Trước Khi Thanh toán / Giải ngân (Pre-Payment Gate Checklist)</h2>
    <ul>
        <li><strong>[✓] TPL-ONB-01:</strong> Phiếu Khai báo KYC &amp; Xếp hạng Tín nhiệm Đối tác ({tier_label}).</li>
        <li><strong>[✓] TPL-ONB-02:</strong> Thỏa thuận Bảo mật Thông tin Song ngữ (ISO/IEC 27001 &amp; Nghị định 13/2023/NĐ-CP).</li>
        <li><strong>[✓] TPL-ONB-03:</strong> Khung Thương mại Nguyên tắc (MSA) &amp; Cam kết SLA theo nhóm đối tác.</li>
        <li><strong>[✓] TPL-ONB-04:</strong> Chứng nhận Phê duyệt Mã Đối tác &amp; Kiểm soát Tách biệt Nhiệm vụ (Maker-Checker SoD).</li>
    </ul>
    <p><em>Ghi chú vận hành: Các khoản thu tiền từ khách hàng (Inbound Receipts) luôn được phép ghi nhận tự động 24/7. Các khoản chi thanh toán ra ngoài (Outbound Disbursements) bắt buộc Đối tác phải ở trạng thái <strong>Approved</strong> với đầy đủ 4 chứng từ đi kèm.</em></p>
</body></html>"""

        return [
            {
                'tpl_code': 'TPL-ONB-01',
                'filename': f"01_KYC_Tiering_Dossier_{safe_code}.html",
                'doc_name': f"[TPL-ONB-01] Phiếu Khai báo KYC & Xếp hạng Đối tác — {self.name} ({code})",
                'html': doc_01,
            },
            {
                'tpl_code': 'TPL-ONB-02',
                'filename': f"02_Mutual_NDA_ISO27001_{safe_code}.html",
                'doc_name': f"[TPL-ONB-02] Thỏa thuận Bảo mật Song ngữ NDA ISO 27001 — {self.name} ({code})",
                'html': doc_02,
            },
            {
                'tpl_code': 'TPL-ONB-03',
                'filename': f"03_Master_Commercial_Frame_{safe_code}.html",
                'doc_name': f"[TPL-ONB-03] Hợp đồng Nguyên tắc & Khung Thương mại SLA — {self.name} ({code})",
                'html': doc_03,
            },
            {
                'tpl_code': 'TPL-ONB-04',
                'filename': f"04_Payment_Gate_Approval_Cert_{safe_code}.html",
                'doc_name': f"[TPL-ONB-04] Chứng nhận Phê duyệt Mã Partner & Cổng Thanh toán — {self.name} ({code})",
                'html': doc_04,
            },
        ]

    def action_generate_onboarding_documents(self):
        """Idempotently generates the 4 companion onboarding documents (`TPL-ONB-01`..`TPL-ONB-04`)
        inside `03. Hợp đồng & Thương mại (Commercial & Contracts)` -> `Hồ sơ On-boarding Đối tác (Partner KYC & MSA)`
        -> `<Partner Folder>`, linking them to `dgm_onboarding_doc_ids`.
        """
        Doc = self.env['documents.document'].sudo()
        Attachment = self.env['ir.attachment'].sudo()
        tag_comm = self.env.ref('insilos_al2c.tag_dgm_contract_comm', raise_if_not_found=False)

        for partner in self:
            if not (partner.id and isinstance(partner.id, int) and partner.id > 0):
                raise UserError(_("Invalid partner ID for onboarding document generation."))
            if not partner.dgm_provisional_code:
                partner.sudo().write({'dgm_provisional_code': f"TMP-DGM-{partner.id:04d}"})

            folder = partner._get_or_create_dgm_onboarding_folder()
            templates = partner._render_companion_templates_payload()
            doc_ids = []

            for tpl in templates:
                raw_bytes = tpl['html'].encode('utf-8')
                b64_datas = base64.b64encode(raw_bytes)
                prefix_marker = f"[{tpl['tpl_code']}]"

                existing_doc = Doc.search([
                    ('folder_id', '=', folder.id),
                    ('name', 'ilike', prefix_marker),
                    ('type', '!=', 'folder'),
                ], order='id asc', limit=1)

                if existing_doc:
                    if existing_doc.attachment_id:
                        existing_doc.attachment_id.write({
                            'name': tpl['filename'],
                            'datas': b64_datas,
                            'mimetype': 'text/html',
                        })
                    else:
                        att = Attachment.create({
                            'name': tpl['filename'],
                            'res_model': 'documents.document',
                            'res_id': existing_doc.id,
                            'type': 'binary',
                            'datas': b64_datas,
                            'mimetype': 'text/html',
                        })
                        existing_doc.write({'attachment_id': att.id})

                    existing_doc.write({
                        'name': tpl['doc_name'],
                        'partner_id': partner.id,
                        'active': True,
                        'access_internal': 'edit',
                        'owner_id': False,
                    })
                    doc_rec = existing_doc
                else:
                    att = Attachment.create({
                        'name': tpl['filename'],
                        'res_model': 'res.partner',
                        'res_id': partner.id,
                        'type': 'binary',
                        'datas': b64_datas,
                        'mimetype': 'text/html',
                    })
                    create_vals = {
                        'name': tpl['doc_name'],
                        'folder_id': folder.id,
                        'attachment_id': att.id,
                        'partner_id': partner.id,
                        'type': 'binary',
                        'access_internal': 'edit',
                        'access_via_link': 'view',
                        'owner_id': False,
                        'company_id': False,
                        'active': True,
                    }
                    if tag_comm and tag_comm.exists():
                        create_vals['tag_ids'] = [(4, tag_comm.id)]
                    doc_rec = Doc.create(create_vals)
                    att.write({'res_model': 'documents.document', 'res_id': doc_rec.id})

                doc_ids.append(doc_rec.id)

            new_state = partner.dgm_onboarding_state
            if new_state == 'provisional':
                new_state = 'docs_ready'

            partner.sudo().write({
                'dgm_onboarding_doc_ids': [(6, 0, doc_ids)],
                'dgm_onboarding_state': new_state,
            })
            partner._compute_dgm_onboarding_docs()
            partner._compute_dgm_tier_and_terms()

        return True

    # -------------------------------------------------------------------------
    # Onboarding Workflow Transitions & Payment Gate Enforcement
    # -------------------------------------------------------------------------
    def action_submit_for_approval(self):
        for partner in self:
            if not partner.dgm_all_companion_docs_ready:
                partner.action_generate_onboarding_documents()
            partner.write({'dgm_onboarding_state': 'under_review'})
        return True

    def action_approve_partner_onboarding(self):
        """Approves the partner onboarding, generating companion documents if missing,
        assigning official `dgm_partner_code` (`PTN-DGM-2026-XXXX`), setting `dgm_onboarding_state = 'approved'`,
        and refreshing `04_Payment_Gate_Approval_Cert` with the official Partner Code.
        """
        for partner in self:
            if not (partner.id and isinstance(partner.id, int) and partner.id > 0):
                raise UserError(_("Invalid partner ID for partner onboarding approval."))
            if not partner.dgm_provisional_code:
                partner.sudo().write({'dgm_provisional_code': f"TMP-DGM-{partner.id:04d}"})
            if not partner.dgm_partner_code:
                official_code = self._next_dgm_partner_code(partner.id)
            else:
                official_code = partner.dgm_partner_code

            partner.sudo().write({
                'dgm_partner_code': official_code,
                'dgm_onboarding_state': 'approved',
                'dgm_approved_by': self.env.user.id or SUPERUSER_ID,
                'dgm_approved_date': fields.Datetime.now(),
            })
            # Generate or refresh all 4 companion documents so TPL-ONB-04 reflects the official PTN-DGM-2026-XXXX code
            partner.action_generate_onboarding_documents()
            partner.sudo().write({'dgm_onboarding_state': 'approved'})
        return True

    def action_fast_track_onboard(self):
        """1-Click Fast-Track Onboarding for Sales & Finance:
        Automatically resolves conflicts, generates the 4 companion documents (`TPL-ONB-01..04`),
        and approves the official Partner Code (`PTN-DGM-2026-XXXX`) in a single non-blocking step!
        """
        for partner in self:
            partner._resolve_or_link_existing_partner()
            partner.action_generate_onboarding_documents()
            partner.action_approve_partner_onboarding()
        return True

    def action_suspend_partner_payment_gate(self):
        self.write({'dgm_onboarding_state': 'suspended'})
        return True

    def check_dgm_partner_payment_gate(self, payment_type='outbound', force_override=False):
        """Enforces SOP-DGM-06 Partner Payment Gate:
        - Inbound customer payments (`payment_type == 'inbound'`): ALWAYS allowed (zero blocking for incoming revenue!).
          If partner is Tier B and in `'docs_ready'` or `'under_review'`, auto-advances approval.
        - Outbound vendor/partner payments (`payment_type == 'outbound'`): Requires `dgm_onboarding_state == 'approved'`,
          a valid `dgm_partner_code` (`PTN-DGM-...`), and `dgm_all_companion_docs_ready == True`,
          UNLESS `force_override` or `dgm_payment_gate_override` is enabled.
        """
        for partner in self:
            if payment_type == 'inbound':
                if partner.dgm_onboarding_state in ('docs_ready', 'under_review') and partner.dgm_partner_tier == 'tier_b':
                    partner.sudo().action_approve_partner_onboarding()
                continue

            if force_override or partner.dgm_payment_gate_override or self.env.context.get('dgm_bypass_payment_gate'):
                continue

            # Allow employee work contacts (internal payroll is governed by SOP-DGM-HR-02)
            if getattr(partner, 'employee', False) or self.env['hr.employee'].sudo().search_count([('work_contact_id', '=', partner.id)], limit=1):
                continue

            # Check canonical partner if linked
            target = partner
            if partner.dgm_canonical_partner_id and partner.dgm_canonical_partner_id.dgm_onboarding_state == 'approved':
                target = partner.dgm_canonical_partner_id

            is_approved = (
                target.dgm_onboarding_state == 'approved'
                and bool(target.dgm_partner_code and str(target.dgm_partner_code).startswith('PTN-DGM-'))
                and target.dgm_all_companion_docs_ready
            )
            if not is_approved:
                raise UserError(_(
                    "⛔ [SOP-DGM-06 Cổng Kiểm soát Thanh toán] Không thể thực hiện chi thanh toán (Outbound Payment) "
                    "cho đối tác '%(partner)s' (Mã hiện tại: %(code)s • Trạng thái: %(state)s).\n\n"
                    "Yêu cầu bắt buộc trước khi thanh toán:\n"
                    "1. Khởi tạo đủ 4 chứng từ On-boarding đi kèm (TPL-ONB-01..04: KYC, NDA, MSA, Payment Gate Cert).\n"
                    "2. Phê duyệt Mã Đối tác Chính thức (PTN-DGM-2026-XXXX).\n\n"
                    "👉 Giải pháp nhanh: Nhấn nút 'Phê duyệt Mã Partner (1-Click)' hoặc 'Fast-Track Onboard' trên hồ sơ Đối tác.",
                    partner=partner.display_name,
                    code=partner.dgm_partner_code or partner.dgm_provisional_code or 'Chưa cấp',
                    state=partner.dgm_onboarding_state or 'provisional',
                ))
        return True


class AccountPaymentOnboardingGate(models.Model):
    _inherit = 'account.payment'

    dgm_payment_gate_override = fields.Boolean(
        string='Bỏ qua Cổng Kiểm soát On-boarding (Override)',
        default=False,
        copy=False,
    )

    def action_post(self):
        for payment in self:
            if payment.partner_id:
                payment.partner_id.check_dgm_partner_payment_gate(
                    payment_type=payment.payment_type or 'outbound',
                    force_override=payment.dgm_payment_gate_override,
                )
        return super().action_post()
