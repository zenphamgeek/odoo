import re
from odoo import SUPERUSER_ID, api, fields, models
from odoo.exceptions import AccessError, UserError
from odoo.addons.sale.models.sale_order import SaleOrder as BaseSaleOrder

# Defensive hardening: ensure BaseSaleOrder._create_invoices accepts **kwargs (e.g. date passed by sale_subscription)
_orig_create_invoices = BaseSaleOrder._create_invoices
if 'kwargs' not in _orig_create_invoices.__code__.co_varnames:
    def _patched_create_invoices(self, final=False, grouped=False, **kwargs):
        return _orig_create_invoices(self, final=final, grouped=grouped)
    BaseSaleOrder._create_invoices = _patched_create_invoices

# Defensive hardening: ensure sale_subscription ProductPricelistItem._is_applicable_for accepts uom/kwargs in Odoo 20
try:
    from odoo.addons.sale_subscription.models.product_pricelist_item import ProductPricelistItem as SubPricelistItem
    _orig_sub_is_applicable_for = SubPricelistItem._is_applicable_for
    if 'kwargs' not in _orig_sub_is_applicable_for.__code__.co_varnames:
        def _patched_sub_is_applicable_for(self, product, qty_in_product_uom, *args, uom=None, **kwargs):
            if self.plan_id and not product.recurring_invoice:
                return False
            if not self.plan_id and product.recurring_invoice and not getattr(product, 'allow_one_time_sale', False):
                return False
            return super(SubPricelistItem, self)._is_applicable_for(product, qty_in_product_uom, uom=uom, **kwargs)
        SubPricelistItem._is_applicable_for = _patched_sub_is_applicable_for
except Exception:
    pass

AGENT_GROUP = 'insilos_al2c.group_al2c_agent'
APPROVER_GROUP = 'sales_team.group_sale_manager'
CPQ_AGENT = 'CPQ Agent'


class SaleOrder(models.Model):
    _name = 'sale.order'
    _inherit = ['sale.order', 'al2c.autonomy.guard']

    al2c_approved = fields.Boolean(
        string='Deal Desk Approved',
        copy=False,
        tracking=True,
        help='Required before an agent-created quotation above the discount or total-contract-value '
             'thresholds can be sent or confirmed. Only sales managers can set it.',
    )
    al2c_approval_required = fields.Boolean(
        string='Deal Desk Approval Required',
        compute='_compute_al2c_approval_required',
    )
    value_case_id = fields.Many2one(
        'al2c.value.case',
        string='Enterprise Value Case',
        copy=False,
        tracking=True,
    )
    fts_item_ids = fields.One2many(
        'al2c.fts.item',
        'sale_order_id',
        string='Fit-to-Standard Scope Items',
    )

    # ------------------------------------------------------------------
    # Thresholds
    # ------------------------------------------------------------------
    @api.model
    def _al2c_get_param_float(self, key, default):
        value = self.env['ir.config_parameter'].sudo().get_param(key, default)
        try:
            return float(value)
        except (TypeError, ValueError):
            return float(default)

    def _al2c_max_tcv_company_currency(self):
        """``al2c.max_tcv`` is expressed in VND; convert it to the company currency."""
        self.ensure_one()
        max_tcv_vnd = self._al2c_get_param_float('al2c.max_tcv', 500_000_000)
        company = self.company_id or self.env.company
        vnd = self.env.ref('base.VND', raise_if_not_found=False)
        if not vnd or vnd == company.currency_id:
            return max_tcv_vnd
        date = (self.date_order or fields.Datetime.now()).date()
        return vnd.with_context(active_test=False)._convert(max_tcv_vnd, company.currency_id, company, date, round=False)

    def _al2c_committed_tcv_company_currency(self):
        """Calculate total committed contract value (untaxed) in company currency.
        For subscriptions, multiplies monthly recurring amount by committed term (default 12 months).
        """
        self.ensure_one()
        company = self.company_id or self.env.company
        
        # Calculate untaxed TCV
        one_time_total = 0.0
        recurring_monthly = 0.0
        committed_months = 12  # Standard annual commitment default
        
        for line in self.order_line.filtered(lambda l: not l.display_type):
            prod = line.product_id
            if prod and prod.recurring_invoice:
                recurring_monthly += line.price_subtotal
            else:
                one_time_total += line.price_subtotal
                
        # If order has explicit subscription plan or dates
        if hasattr(self, 'plan_id') and self.plan_id:
            unit = getattr(self.plan_id, 'billing_period_unit', 'month')
            val = getattr(self.plan_id, 'billing_period_value', 1) or 1
            if unit == 'year':
                committed_months = 12 * val
            elif unit == 'month':
                committed_months = max(12, val)
                
        tcv_order_curr = one_time_total + (recurring_monthly * committed_months)
        
        if not self.currency_id or self.currency_id == company.currency_id:
            return tcv_order_curr
        date = (self.date_order or fields.Datetime.now()).date()
        return self.currency_id._convert(tcv_order_curr, company.currency_id, company, date, round=False)

    def _al2c_amount_total_company_currency(self):
        """Total order amount expressed in company currency."""
        self.ensure_one()
        company = self.company_id or self.env.company
        if not self.currency_id or self.currency_id == company.currency_id:
            return self.amount_total
        date = (self.date_order or fields.Datetime.now()).date()
        return self.currency_id._convert(self.amount_total, company.currency_id, company, date, round=False)

    def _al2c_is_agent_order(self):
        """An order is agent-driven when its creator, salesperson or the current
        user belongs to the AL2C agent group."""
        self.ensure_one()
        group = self.env.ref(AGENT_GROUP, raise_if_not_found=False)
        if not group:
            return False
        users = (self.create_uid | self.user_id | self.env.user).sudo()
        return bool(users & group.sudo().all_user_ids) if 'all_user_ids' in group._fields else bool(users & group.sudo().user_ids)

    def _al2c_threshold_breaches(self):
        """Return a list of human-readable reasons why deal-desk approval is needed (AL2C-SAL-301..304)."""
        self.ensure_one()
        reasons = []
        company = self.company_id or self.env.company
        
        # 1. Discount Ceiling & Effective Discount (AL2C-SAL-302)
        max_discount = self._al2c_get_param_float('al2c.max_discount', 10.0)
        lines = self.order_line.filtered(lambda l: not l.display_type and l.product_uom_qty > 0)
        
        for line in lines:
            prod_name = line.product_id.display_name or line.name or "Item"
            if "False" in prod_name and line.product_id.product_tmpl_id and line.product_id.product_tmpl_id.name:
                code_str = f"[{line.product_id.default_code}] " if line.product_id.default_code else ""
                prod_name = f"{code_str}{line.product_id.product_tmpl_id.name}"

            # Stated discount field
            if line.discount > max_discount:
                reasons.append(self.env._(
                    "line discount %(disc)s%% on %(prod)s exceeds %(max)s%%",
                    disc=round(line.discount, 2), prod=prod_name, max=max_discount))
                break
                
            # Effective discount against base list price (VND catalog scale per SRS v1.1)
            base_price = line.product_id.list_price if line.product_id else 0.0
            order_cur = self.currency_id or company.currency_id
            vnd = self.env.ref('base.VND', raise_if_not_found=False)
            if getattr(line.product_id, 'al2c_product_line', False) or (vnd and base_price >= 100_000):
                base_cur = vnd or company.currency_id
            else:
                base_cur = line.product_id.currency_id or company.currency_id

            if base_price > 0 and base_cur and order_cur and base_cur != order_cur:
                date = (self.date_order or fields.Datetime.now()).date()
                base_price = base_cur.with_context(active_test=False)._convert(
                    base_price, order_cur, company, date, round=False
                )
            if base_price > 0 and line.price_unit < base_price:
                eff_disc = (1.0 - (line.price_unit * (1.0 - line.discount / 100.0) / base_price)) * 100.0
                if eff_disc > max_discount:
                    reasons.append(self.env._(
                        "effective discount %(disc)s%% on %(prod)s exceeds %(max)s%% ceiling",
                        disc=round(eff_disc, 2), prod=prod_name, max=max_discount))
                    break
                    
        # 2. Untaxed Committed TCV Threshold (AL2C-SAL-301)
        max_tcv = self._al2c_max_tcv_company_currency()
        tcv = self._al2c_committed_tcv_company_currency()
        if tcv > max_tcv:
            reasons.append(self.env._(
                "committed TCV %(tcv)s %(cur)s exceeds the %(max)s %(cur)s limit",
                tcv=round(tcv, 2), max=round(max_tcv, 2), cur=company.currency_id.name))
                
        # 3. Gross Margin Floor >= 35% (AL2C-SAL-303)
        min_margin = self._al2c_get_param_float('al2c.min_margin', 35.0)
        total_cost = sum(
            (l.product_id.standard_price or 0.0) * l.product_uom_qty
            for l in lines if l.product_id and l.product_id.standard_price > 0
        )
        total_untaxed = sum(l.price_subtotal for l in lines)
        if total_cost > 0 and total_untaxed > 0:
            margin = ((total_untaxed - total_cost) / total_untaxed) * 100.0
            if margin < min_margin:
                reasons.append(self.env._(
                    "estimated gross margin %(margin)s%% is below the %(min)s%% floor",
                    margin=round(margin, 2), min=min_margin))
                    
        # 4. Customer Credit Standing Gate (AL2C-SAL-304)
        if self.partner_id:
            import datetime
            cutoff = fields.Date.today() - datetime.timedelta(days=30)
            overdue_count = self.env['account.move'].sudo().search_count([
                ('partner_id', 'child_of', self.partner_id.commercial_partner_id.id),
                ('move_type', '=', 'out_invoice'),
                ('state', '=', 'posted'),
                ('payment_state', 'in', ('not_paid', 'partial')),
                ('invoice_date_due', '<', cutoff),
            ])
            if overdue_count > 0:
                reasons.append(self.env._(
                    "customer %(partner)s has %(count)d invoice(s) overdue by > 30 days",
                    partner=self.partner_id.display_name, count=overdue_count))
                    
        # 5. Clean-Core Scope Check (AL2C-CRM-101)
        unapproved_class_d = self.fts_item_ids.filtered(
            lambda f: f.clean_core_class == 'class_d' and not f.approved_by_architect
        )
        if unapproved_class_d:
            reasons.append(self.env._(
                "order contains unapproved Class D (Clean-Core Prohibited) scope items: %(items)s",
                items=", ".join(unapproved_class_d.mapped('name'))
            ))

        return reasons

    @api.depends('order_line.discount', 'order_line.price_unit', 'amount_untaxed', 'currency_id', 'user_id', 'create_uid', 'partner_id', 'fts_item_ids.clean_core_class', 'fts_item_ids.approved_by_architect')
    def _compute_al2c_approval_required(self):
        for order in self:
            order.al2c_approval_required = bool(
                order.id and order._al2c_is_agent_order() and order._al2c_threshold_breaches()
            )

    def _al2c_check_deal_desk(self, action_label):
        for order in self:
            if not order._al2c_is_agent_order():
                continue
            if self.env.user.has_group(AGENT_GROUP):
                order._al2c_check_autonomy(CPQ_AGENT)
            if order.al2c_approved:
                continue
            reasons = order._al2c_threshold_breaches()
            if reasons:
                raise UserError(self.env._(
                    "Quotation %(name)s cannot be %(action)s without deal-desk approval: %(reasons)s. "
                    "A sales manager must tick 'Deal Desk Approved'.",
                    name=order.name, action=action_label, reasons='; '.join(reasons),
                ))

    # ------------------------------------------------------------------
    # Approval field protection & Re-approval Sentinel (AL2C-NEW-004)
    # ------------------------------------------------------------------
    def _al2c_check_approval_rights(self, vals):
        if 'al2c_approved' in vals and not self.env.su and not self.env.user.has_group(APPROVER_GROUP):
            raise AccessError(self.env._("Only sales managers can grant deal-desk approval."))
        if vals.get('al2c_approved') and self.env.user.has_group(AGENT_GROUP) and not self.env.su:
            raise AccessError(self.env._("An agent cannot approve quotations (segregation of duties)."))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._al2c_check_approval_rights(vals)
        return super().create(vals_list)

    def write(self, vals):
        self._al2c_check_approval_rights(vals)
        # AL2C-NEW-004: Re-approval sentinel
        # If lines, partner, or pricelist change on an approved order, reset approval
        modifying_commercials = any(k in vals for k in ('order_line', 'partner_id', 'pricelist_id'))
        if modifying_commercials and 'al2c_approved' not in vals:
            for order in self:
                if order.al2c_approved:
                    vals['al2c_approved'] = False
                    break
        return super().write(vals)

    # ------------------------------------------------------------------
    # Guarded actions
    # ------------------------------------------------------------------
    def action_quotation_send(self):
        self._al2c_check_deal_desk(self.env._("sent"))
        return super().action_quotation_send()

    def action_quotation_sent(self):
        self._al2c_check_deal_desk(self.env._("marked as sent"))
        return super().action_quotation_sent()

    def action_confirm(self):
        self._al2c_check_deal_desk(self.env._("confirmed"))
        res = super().action_confirm()
        for order in self:
            if order.value_case_id and order.project_ids:
                order.project_ids.write({'value_case_id': order.value_case_id.id})
        return res

    def action_approve_deal_desk(self):
        """Action for sales manager to grant deal desk approval."""
        self._al2c_check_method_allowed('sale.order', 'action_approve_deal_desk')
        self.write({'al2c_approved': True})
        return True

    def _get_al2c_report_content_hash(self, report_ref: str, template_version: str = "1.0") -> str:
        """Deterministic Content-Hash Idempotency Key for report generation.

        Borrowing Prefect's task-run result caching architecture:
        Keys the generated proposal artifact on sha256 of:
        (doc._name, doc.id, company_id, write_date, template_version, report_ref, amount_total, currency_id).
        Guarantees the non-repudiation and monetary freshness invariant:
        'One logical document state maps to exactly one rendered artifact.'
        """
        import hashlib
        self.ensure_one()
        wdate_str = self.write_date.isoformat() if self.write_date else 'new'
        company_id = self.company_id.id if self.company_id else 0
        amount_total = self.amount_total or 0.0
        currency_id = self.currency_id.id if self.currency_id else 0
        raw = f"{self._name}:{self.id}:{company_id}:{wdate_str}:{template_version}:{report_ref}:{amount_total}:{currency_id}"
        return hashlib.sha256(raw.encode('utf-8')).hexdigest()

    def _get_cached_report_attachment(
        self,
        report_ref: str,
        template_version: str = "1.0",
        create_content: bytes = None,
        filename: str = None,
    ):
        """Look up or race-safely store cached report artifact matching current document state.

        Guarantees non-repudiation, cache authenticity, and concurrency safety:
        1. Trust Filter (CWE-345): Only system-generated (create_uid = SUPERUSER_ID) binary PDFs
           matching the document's company are returned. User-uploaded attachments sharing
           the description token are rejected, preventing forgery and cache poisoning.
        2. Strict Input Validation (CWE-20): create_content must be bytes/bytearray.
        3. Real Concurrency Safety: Serializes concurrent creation via a transaction-scoped
           PostgreSQL advisory lock (pg_advisory_xact_lock) derived deterministically from
           the content hash, with re-check under lock.
        """
        self.ensure_one()
        content_hash = self._get_al2c_report_content_hash(report_ref, template_version=template_version)
        desc = f"al2c_report_hash:{content_hash}"
        Attachment = self.env['ir.attachment'].sudo()

        if create_content is not None and not isinstance(create_content, (bytes, bytearray)):
            raise ValueError("create_content must be raw PDF bytes")

        company_filter = [self.company_id.id, False] if self.company_id else [False]
        domain = [
            ('res_model', '=', self._name),
            ('res_id', '=', self.id),
            ('company_id', 'in', company_filter),
            ('type', '=', 'binary'),
            ('mimetype', '=', 'application/pdf'),
            ('description', '=', desc),
            ('create_uid', '=', SUPERUSER_ID),
        ]
        existing = Attachment.search(domain, order='id asc', limit=1)
        if existing:
            return existing

        if create_content is None:
            return existing

        # Concurrency safety: acquire transaction-scoped advisory lock keyed on content hash (NTP-independent 63-bit key)
        import hashlib
        if isinstance(content_hash, str):
            hash_bytes = content_hash.encode('utf-8')
        elif isinstance(content_hash, (bytes, bytearray)):
            hash_bytes = bytes(content_hash)
        else:
            hash_bytes = str(content_hash).encode('utf-8')
        lock_key = int.from_bytes(hashlib.sha256(hash_bytes).digest()[:8], 'big') & 0x7FFFFFFFFFFFFFFF
        self.env.cr.execute("SELECT pg_advisory_xact_lock(%s)", (lock_key,))

        # Re-check under the lock: a concurrent worker may have already committed
        existing = Attachment.search(domain, order='id asc', limit=1)
        if existing:
            return existing

        import base64
        from psycopg2.errors import UniqueViolation

        fname = filename or f"{self.name or 'report'}_{content_hash[:8]}.pdf"
        try:
            with self.env.cr.savepoint():
                return Attachment.create({
                    'name': fname,
                    'res_model': self._name,
                    'res_id': self.id,
                    'company_id': self.company_id.id if self.company_id else False,
                    'type': 'binary',
                    'datas': base64.b64encode(bytes(create_content)),
                    'description': desc,
                    'mimetype': 'application/pdf',
                })
        except UniqueViolation:
            # Genuine concurrency collision: another node won. Return the winner.
            winner = Attachment.search(domain, order='id asc', limit=1)
            if not winner:
                raise  # not actually a dedup collision; do not hide the real error
            return winner

    def _store_cached_report_attachment(
        self,
        report_ref: str,
        content: bytes,
        filename: str = None,
        template_version: str = "1.0",
    ):
        """Convenience method to store or retrieve cached report attachment race-safely."""
        return self._get_cached_report_attachment(
            report_ref,
            template_version=template_version,
            create_content=content,
            filename=filename,
        )

    @api.model
    def get_views(self, views, options=None):
        res = super().get_views(views, options=options)
        if isinstance(res, dict) and 'models' in res:
            if 'order.header' in res['models'] and 'sale.order' not in res['models']:
                res['models']['sale.order'] = res['models']['order.header']
            if 'order.line' in res['models'] and 'sale.order.line' not in res['models']:
                res['models']['sale.order.line'] = res['models']['order.line']
        return res


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    milestone_ids = fields.One2many(
        'project.milestone',
        'sale_line_id',
        string='Milestones',
    )
    al2c_vat_class = fields.Selection(
        [
            ('kct', 'KCT Software (VAT Exempt - Law 48/2024/QH15)'),
            ('vat_8', 'IT Services 8% (Decree 174/2025/ND-CP)'),
            ('vat_10', 'Standard 10% (Infrastructure / Hosting / Hardware)'),
        ],
        string='VAT Classification',
        compute='_compute_al2c_vat_class',
        store=True,
        readonly=False,
        index=True,
        help="Statutory Vietnamese tax classification mapped from product template under Law 48/2024 and Decree 174/2025.",
    )

    @api.depends('product_id', 'product_id.al2c_vat_class')
    def _compute_al2c_vat_class(self):
        for line in self:
            if line.product_id and line.product_id.al2c_vat_class:
                line.al2c_vat_class = line.product_id.al2c_vat_class
            elif not line.al2c_vat_class:
                line.al2c_vat_class = 'kct'

    def _al2c_get_tax_for_vat_class(self, company, vat_class):
        """Map statutory al2c_vat_class to appropriate account.tax record for company."""
        Tax = self.env['account.tax'].sudo()
        domain = [('type_tax_use', '=', 'sale')]
        if company:
            domain.append(('company_id', '=', company.id))

        if vat_class == 'kct':
            # Law 48/2024/QH15: VAT Exempt Software (0% VAT or exempt)
            kct_tax = Tax.search(domain + [('amount', '=', 0.0), ('name', 'ilike', 'KCT')], limit=1)
            if not kct_tax:
                kct_tax = Tax.search(domain + [('amount', '=', 0.0)], limit=1)
            return kct_tax or Tax.browse()

        elif vat_class == 'vat_8':
            # Decree 174/2025/ND-CP: 8% IT Services tax
            tax_8 = Tax.search(domain + [('amount', '=', 8.0)], limit=1)
            if not tax_8 and company:
                tax_8 = Tax.create({
                    'name': 'Thuế GTGT 8% (Nghị định 174/2025/NĐ-CP)',
                    'amount': 8.0,
                    'amount_type': 'percent',
                    'type_tax_use': 'sale',
                    'company_id': company.id,
                })
            return tax_8

        elif vat_class == 'vat_10':
            # Standard 10% Infrastructure / Hosting tax
            tax_10 = Tax.search(domain + [('amount', '=', 10.0)], limit=1)
            if not tax_10 and company:
                tax_10 = Tax.create({
                    'name': 'Thuế GTGT 10% (Bán hàng)',
                    'amount': 10.0,
                    'amount_type': 'percent',
                    'type_tax_use': 'sale',
                    'company_id': company.id,
                })
            return tax_10

        return Tax.browse()

    @api.depends('al2c_vat_class')
    def _compute_tax_ids(self):
        super()._compute_tax_ids()
        for line in self:
            if line.env.context.get('skip_al2c_tax_mapping'):
                continue
            vat_class = line.al2c_vat_class or (line.product_id and line.product_id.al2c_vat_class)
            if vat_class:
                company = line.company_id or line.order_id.company_id or self.env.company
                line.tax_ids = line._al2c_get_tax_for_vat_class(company, vat_class)

    @api.depends('milestone_ids.al2c_billing_eligible')
    def _compute_qty_delivered(self):
        super()._compute_qty_delivered()

    def _prepare_qty_delivered(self):
        delivered_qties = super()._prepare_qty_delivered()
        lines_by_milestones = self.filtered(lambda sol: sol.qty_delivered_method == 'milestones')
        if not lines_by_milestones:
            return delivered_qties

        # Decree 70/2025 & SAP Activate stage gate enforcement:
        # A milestone line only contributes to delivered quantity if it is reached AND has verified customer sign-off (al2c_billing_eligible == True).
        project_milestone_read_group = self.env['project.milestone']._read_group(
            [('sale_line_id', 'in', lines_by_milestones.ids), ('al2c_billing_eligible', '=', True)],
            ['sale_line_id'],
            ['quantity_percentage:sum'],
        )
        eligible_milestones_per_sol = {sale_line.id: percentage_sum for sale_line, percentage_sum in project_milestone_read_group}
        for line in lines_by_milestones:
            sol_id = line.id or line._origin.id
            delivered_qties[line] = eligible_milestones_per_sol.get(sol_id, 0.0) * line.product_uom_qty
        return delivered_qties

    def write(self, vals):
        res = super().write(vals)
        commercial_fields = {'price_unit', 'discount', 'product_uom_qty', 'product_id'}
        if commercial_fields.intersection(vals.keys()):
            for line in self:
                if line.order_id and line.order_id.al2c_approved:
                    line.order_id.sudo().write({'al2c_approved': False})
        return res

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        for line in lines:
            if line.order_id and line.order_id.al2c_approved:
                line.order_id.sudo().write({'al2c_approved': False})
        return lines

    def unlink(self):
        orders = self.mapped('order_id').filtered(lambda o: o.al2c_approved)
        res = super().unlink()
        for order in orders:
            order.sudo().write({'al2c_approved': False})
        return res


_AMP_FIXUP_RE = re.compile(r'&(?!(?:amp|lt|gt|quot|apos|#\d+|#x[0-9a-fA-F]+);)')


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    def _render_qweb_html(self, report_ref, docids, data=None):
        res, report_format = super()._render_qweb_html(report_ref, docids, data=data)
        report = self._get_report(report_ref)
        if report and report.report_name and report.report_name.startswith('insilos_al2c.'):
            try:
                if isinstance(res, (bytes, bytearray)):
                    html_str = res.decode('utf-8')
                    html_str = _AMP_FIXUP_RE.sub('&amp;', html_str)
                    res = html_str.encode('utf-8')
                elif isinstance(res, str):
                    res = _AMP_FIXUP_RE.sub('&amp;', res)
            except Exception:
                pass
        return res, report_format


