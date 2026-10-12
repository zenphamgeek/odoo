# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    al2c_qualification_state = fields.Selection([
        ('unqualified', 'Unqualified / Inbound'),
        ('in_progress', 'Qualification In Progress'),
        ('qualified', 'Qualified (SQL)'),
        ('disqualified', 'Disqualified'),
        ('nurture', 'Nurture Stream'),
    ], string='Autonomous Qualification State', default='unqualified', tracking=True)

    al2c_touch_count = fields.Integer(string='Qualification Touch Count', default=0, tracking=True)
    al2c_touch_cap = fields.Integer(string='Touch Cap', default=3)

    # BANT Criteria
    al2c_bant_budget = fields.Boolean(string='Budget Confirmed', tracking=True)
    al2c_bant_budget_amount = fields.Monetary(
        string='Estimated Budget',
        currency_field='company_currency',
        help='Estimated customer budget allocation in VND.',
    )
    al2c_bant_authority = fields.Boolean(string='Authority / Decision Maker Identified', tracking=True)
    al2c_bant_authority_name = fields.Char(string='Decision Maker Name / Title')
    al2c_bant_need = fields.Text(string='Identified Business Need & Pain Points')
    al2c_bant_timeline = fields.Selection([
        ('immediate', '< 1 Month (Immediate)'),
        ('1_3_months', '1 - 3 Months (Standard)'),
        ('3_6_months', '3 - 6 Months (Mid-term)'),
        ('longer', '> 6 Months (Long-term)'),
    ], string='Procurement Timeline', tracking=True)

    # MEDDICC Criteria
    al2c_meddicc_metrics = fields.Text(string='Metrics (Quantified Economic Value / ROI)')
    al2c_meddicc_economic_buyer = fields.Char(string='Economic Buyer')
    al2c_meddicc_decision_criteria = fields.Text(string='Decision Criteria')
    al2c_meddicc_decision_process = fields.Text(string='Decision Process')
    al2c_meddicc_identify_pain = fields.Text(string='Identified Pain')
    al2c_meddicc_champion = fields.Char(string='Internal Champion')

    # Sentiment & Score
    al2c_sentiment = fields.Selection([
        ('positive', 'Positive'),
        ('neutral', 'Neutral'),
        ('negative', 'Negative'),
    ], string='Lead Sentiment', default='neutral', tracking=True)

    al2c_qualification_score = fields.Float(
        string='Qualification Score (%)',
        compute='_compute_al2c_qualification_score',
        store=True,
        tracking=True,
    )

    value_case_id = fields.Many2one(
        'al2c.value.case',
        string='Enterprise Value Case',
        copy=False,
        tracking=True,
    )
    fts_item_ids = fields.One2many(
        'al2c.fts.item',
        'lead_id',
        string='Fit-to-Standard Scope Items',
    )

    @api.depends(
        'al2c_bant_budget', 'al2c_bant_budget_amount',
        'al2c_bant_authority', 'al2c_meddicc_economic_buyer',
        'al2c_bant_need', 'al2c_meddicc_identify_pain',
        'al2c_bant_timeline', 'al2c_meddicc_metrics',
        'al2c_meddicc_decision_criteria',
    )
    def _compute_al2c_qualification_score(self):
        for lead in self:
            criteria_met = 0
            if lead.al2c_bant_budget or (lead.al2c_bant_budget_amount and lead.al2c_bant_budget_amount > 0):
                criteria_met += 1
            if lead.al2c_bant_authority or lead.al2c_meddicc_economic_buyer:
                criteria_met += 1
            if lead.al2c_bant_need or lead.al2c_meddicc_identify_pain:
                criteria_met += 1
            if lead.al2c_bant_timeline:
                criteria_met += 1
            if lead.al2c_meddicc_metrics:
                criteria_met += 1
            if lead.al2c_meddicc_decision_criteria:
                criteria_met += 1
            lead.al2c_qualification_score = (criteria_met / 6.0) * 100.0

    def action_process_qualification_turn(self, message_text="", extracted_data=None):
        """
        Process one conversational qualification turn.
        Caps autonomous touches at al2c_touch_cap (default 3) to prevent spamming.
        Advances to SQL upon satisfactory BANT/MEDDICC qualification, or routes to nurture/disqualification.
        """
        self.ensure_one()
        if self.al2c_touch_count >= self.al2c_touch_cap and self.al2c_qualification_state in ('qualified', 'disqualified', 'nurture'):
            return True

        self.al2c_touch_count += 1
        vals = {}

        if extracted_data:
            for k, v in extracted_data.items():
                if hasattr(self, k):
                    vals[k] = v
        elif message_text:
            text_lower = message_text.lower()
            if any(term in text_lower for term in ['budget', 'ngân sách', 'vnd', 'usd', 'tỷ', 'triệu', 'triệu vnd']):
                vals['al2c_bant_budget'] = True
            if any(term in text_lower for term in ['cio', 'ceo', 'cfo', 'director', 'giám đốc', 'trưởng phòng', 'quyết định', 'decision maker']):
                vals['al2c_bant_authority'] = True
            if any(term in text_lower for term in ['q1', 'q2', 'q3', 'q4', 'tháng tới', 'month', 'sớm', 'ngay']):
                vals['al2c_bant_timeline'] = '1_3_months'
            if any(term in text_lower for term in ['cần', 'nhu cầu', 'khó khăn', 'pain', 'need', 'yêu cầu', 'triển khai']):
                vals['al2c_bant_need'] = message_text

            if any(term in text_lower for term in ['không có nhu cầu', 'không phù hợp', 'not interested', 'dừng', 'unsubscribe']):
                vals['al2c_sentiment'] = 'negative'
            elif any(term in text_lower for term in ['quan tâm', 'hợp tác', 'demo', 'báo giá', 'quote', 'interested', 'rất tốt']):
                vals['al2c_sentiment'] = 'positive'

        if vals:
            self.write(vals)

        # Evaluate qualification gates
        if self.al2c_sentiment == 'negative':
            self.al2c_qualification_state = 'disqualified'
            self.message_post(
                body=_("Autonomous Qualification: Lead marked Disqualified based on negative sentiment or lack of ICP fit.")
            )
        elif self.al2c_bant_budget and self.al2c_bant_authority and self.al2c_bant_need and self.al2c_bant_timeline:
            self.al2c_qualification_state = 'qualified'
            # Advance stage to Qualified / Proposition if available
            target_stage = self.env['crm.stage'].search([
                ('name', 'ilike', 'qualified'),
            ], limit=1)
            if not target_stage:
                target_stage = self.env['crm.stage'].search([
                    ('name', 'ilike', 'proposition'),
                ], limit=1)
            if target_stage:
                self.stage_id = target_stage.id

            self.message_post(
                body=_("🎯 <b>Autonomous BANT/MEDDICC Qualified:</b> Lead promoted to SQL (Score: %.0f%%).<br/>"
                       "• <b>Need:</b> %s<br/>"
                       "• <b>Authority:</b> %s<br/>"
                       "• <b>Timeline:</b> %s<br/>"
                       "• <b>Budget Confirmed:</b> %s") % (
                    self.al2c_qualification_score,
                    self.al2c_bant_need or 'Identified',
                    self.al2c_bant_authority_name or 'Identified',
                    dict(self._fields['al2c_bant_timeline'].selection).get(self.al2c_bant_timeline, ''),
                    _('Yes') if self.al2c_bant_budget else _('No'),
                )
            )
            # Create high-priority activity for Account Executive
            self.activity_schedule(
                'mail.mail_activity_data_todo',
                summary=_("Executive Discovery & Demo Call (Autonomous SQL Handoff)"),
                note=_("Customer has satisfied BANT qualification criteria. Prepare solution demo and proposal."),
                user_id=self.user_id.id if self.user_id else self.env.user.id,
            )
        elif self.al2c_touch_count >= self.al2c_touch_cap:
            self.al2c_qualification_state = 'nurture'
            self.message_post(
                body=_("Autonomous Qualification: Maximum touch cap (%d) reached without meeting all BANT criteria. Routing to marketing nurture stream.") % self.al2c_touch_cap
            )
        else:
            self.al2c_qualification_state = 'in_progress'
            self.message_post(
                body=_("Autonomous Qualification: Dialog turn %d/%d processed. Qualification score: %.0f%%.") % (
                    self.al2c_touch_count, self.al2c_touch_cap, self.al2c_qualification_score
                )
            )

        return True
