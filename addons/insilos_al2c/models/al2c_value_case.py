# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class Al2cValueCase(models.Model):
    """
    Value Case Architecture (AL2C-VAL-101):
    Quantifies economic value, TCO reduction, ROI, and payback period.
    Propagates across the full lifecycle: Lead (Discover) -> Sale Order (Solution) -> Project (Realize) -> Subscription (Operate).
    """
    _name = 'al2c.value.case'
    _description = 'AL2C Enterprise Value Case'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string='Value Case Title', required=True, tracking=True)
    partner_id = fields.Many2one('res.partner', string='Target Enterprise', tracking=True)
    lead_id = fields.Many2one('crm.lead', string='Source Opportunity', tracking=True)
    sale_order_ids = fields.One2many('sale.order', 'value_case_id', string='Linked Sales Orders')
    project_ids = fields.One2many('project.project', 'value_case_id', string='Realization Projects')

    state = fields.Selection([
        ('draft', 'Draft Case'),
        ('quantified', 'Quantified & Proposed'),
        ('signed_off', 'Customer Agreed'),
        ('realized', 'Value Realized (Post-Go-Live)'),
    ], string='Status', default='draft', tracking=True)

    company_currency = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
        required=True,
    )

    tco_current_vnd = fields.Monetary(
        string='Current Baseline TCO (Annual)',
        currency_field='company_currency',
        help='Customer annual IT & operational expense without Insilos platform.',
        tracking=True,
    )
    tco_future_vnd = fields.Monetary(
        string='Target Insilos TCO (Annual)',
        currency_field='company_currency',
        help='Projected annual platform license, hosting, and operational cost.',
        tracking=True,
    )

    net_annual_benefit_vnd = fields.Monetary(
        string='Net Annual Benefit',
        currency_field='company_currency',
        compute='_compute_metrics',
        store=True,
        tracking=True,
    )
    roi_percentage = fields.Float(
        string='Projected 3-Year ROI (%)',
        compute='_compute_metrics',
        store=True,
        tracking=True,
    )
    payback_months = fields.Float(
        string='Payback Period (Months)',
        compute='_compute_metrics',
        store=True,
        tracking=True,
    )

    driver_ids = fields.One2many('al2c.value.driver', 'case_id', string='Quantitative Value Drivers')

    @api.depends('tco_current_vnd', 'tco_future_vnd', 'driver_ids.annual_benefit_vnd')
    def _compute_metrics(self):
        for case in self:
            driver_sum = sum(case.driver_ids.mapped('annual_benefit_vnd'))
            tco_delta = max(case.tco_current_vnd - case.tco_future_vnd, 0)
            net_annual = driver_sum + tco_delta
            case.net_annual_benefit_vnd = net_annual

            cost_base = case.tco_future_vnd or 1.0
            if cost_base > 0 and net_annual > 0:
                # 3-year net ROI: (3 * net_benefit) / (3 * cost_base) * 100
                case.roi_percentage = round((net_annual / cost_base) * 100.0, 1)
                # Payback in months: (investment / annual_benefit) * 12
                case.payback_months = round((case.tco_future_vnd / net_annual) * 12.0, 1) if net_annual else 0.0
            else:
                case.roi_percentage = 0.0
                case.payback_months = 0.0

    def action_quantify(self):
        for case in self:
            if not case.driver_ids and not (case.tco_current_vnd and case.tco_future_vnd):
                raise UserError(_("Cannot quantify value case without value drivers or baseline TCO inputs."))
            case.state = 'quantified'
        return True

    def action_mark_realized(self):
        for case in self:
            case.state = 'realized'
            case.message_post(body=_("<b>Value Case Realized:</b> Confirmed post-implementation benefit delivery."))
        return True


class Al2cValueDriver(models.Model):
    """Individual quantifiable business driver contributing to the enterprise value case."""
    _name = 'al2c.value.driver'
    _description = 'AL2C Value Case Driver'
    _order = 'annual_benefit_vnd desc'

    case_id = fields.Many2one('al2c.value.case', string='Value Case', required=True, ondelete='cascade')
    name = fields.Char(string='Value Driver Name', required=True)
    category = fields.Selection([
        ('efficiency', 'Process Efficiency & Automation'),
        ('revenue', 'Revenue Acceleration & Conversion'),
        ('compliance', 'Regulatory Compliance & Fine Avoidance (PDPL/Decree 70)'),
        ('license_consolidation', 'Legacy Software License Replacement'),
    ], string='Driver Category', default='efficiency', required=True)

    annual_benefit_vnd = fields.Monetary(
        string='Annual Benefit (VND)',
        currency_field='company_currency',
        required=True,
    )
    confidence_level = fields.Selection([
        ('high', 'High (Validated Client Metric)'),
        ('medium', 'Medium (Benchmarked Industry Average)'),
        ('exploratory', 'Exploratory (Estimated Opportunity)'),
    ], string='Confidence Level', default='medium')

    company_currency = fields.Many2one(
        'res.currency',
        related='case_id.company_currency',
        string='Currency',
    )
    notes = fields.Text(string='Calculation Rationale & Assumptions')
