# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    al2c_triage_category = fields.Selection([
        ('general', 'General Inquiry'),
        ('bug', 'Software Bug / Defect'),
        ('howto', 'How-To / Usage Guidance'),
        ('billing', 'Billing & Decree 70 E-Invoice'),
        ('mojo', 'Mojo AI App / Token Support'),
    ], string='Autonomous L1 Category', tracking=True)

    al2c_resolution_article_id = fields.Many2one(
        'knowledge.article',
        string='Grounding Knowledge Article',
        help='Knowledge article used by L1 agent to ground the automated resolution.',
    )
    al2c_autonomous_resolved = fields.Boolean(
        string='Autonomously Resolved by L1',
        default=False,
        tracking=True,
    )
    al2c_confidence_score = fields.Float(
        string='Resolution Confidence (%)',
        default=0.0,
        tracking=True,
    )

    def action_autonomous_triage(self):
        """
        AL2C-HLP-001: Helpdesk L1 Autonomous Triage & Knowledge Resolution.
        Categorizes inbound tickets, queries enterprise Knowledge articles,
        posts grounded resolution for standard how-to/billing/Mojo inquiries,
        or routes bugs directly to L2 engineering.
        """
        for ticket in self:
            content = f"{ticket.name or ''} {ticket.description or ''}".lower()

            # 1. Automated Categorization
            if any(k in content for k in ['hóa đơn', 'invoice', 'decree 70', 'nghị định 70', 'e-invoice', 'vat', 'thuế', 'thanh toán', 'cqt']):
                category = 'billing'
            elif any(k in content for k in ['mojo', 'token', 'tokens', 'inference', 'gpu', 'quota', 'burn', 'api key']):
                category = 'mojo'
            elif any(k in content for k in ['lỗi', 'error', 'bug', 'traceback', 'crash', 'hỏng', 'exception', '500']):
                category = 'bug'
            elif any(k in content for k in ['hướng dẫn', 'how to', 'sử dụng', 'cách dùng', 'cấu hình', 'config', 'setup']):
                category = 'howto'
            else:
                category = 'general'

            ticket.al2c_triage_category = category

            # 2. Query Knowledge Base for Grounding Article
            article = False
            if category == 'billing':
                article = self.env['knowledge.article'].search([
                    ('name', 'ilike', 'Compliance'),
                ], limit=1)
            elif category == 'mojo':
                article = self.env['knowledge.article'].search([
                    ('name', 'ilike', 'Mojo'),
                ], limit=1)
            elif category in ('howto', 'general'):
                article = self.env['knowledge.article'].search([
                    ('name', 'ilike', 'Products'),
                ], limit=1)

            # 3. Autonomous Resolution or L2 Escalation
            if article and category in ('howto', 'billing', 'mojo'):
                ticket.al2c_resolution_article_id = article.id
                ticket.al2c_confidence_score = 92.0
                ticket.al2c_autonomous_resolved = True

                ticket.message_post(
                    body=_("🤖 <b>Insilos Autonomous L1 Resolution:</b><br/>"
                           "• <b>Triage Category:</b> %s<br/>"
                           "• <b>Grounded Article:</b> %s<br/>"
                           "• <b>Resolution Guidance:</b> Based on Insilos official documentation, your inquiry has been resolved. "
                           "Please refer to the attached article reference for step-by-step procedures.<br/>"
                           "If you require further specialized assistance, reply to this thread to request human specialist review.") % (
                        dict(ticket._fields['al2c_triage_category'].selection).get(category, category),
                        article.name,
                    )
                )

                # Move to solved/closed stage if stage exists
                if ticket.team_id:
                    solved_stage = ticket.team_id.stage_ids.filtered(lambda s: s.fold or 'solved' in s.name.lower() or 'closed' in s.name.lower())
                    if solved_stage:
                        ticket.stage_id = solved_stage[0].id

            elif category == 'bug':
                ticket.al2c_confidence_score = 65.0
                ticket.al2c_autonomous_resolved = False

                ticket.message_post(
                    body=_("🤖 <b>Insilos Autonomous L1 Triage:</b><br/>"
                           "• <b>Triage Category:</b> Software Bug / Defect<br/>"
                           "• <b>Action:</b> Critical defect detected. Autonomous triage has routed this ticket to L2 Senior Engineering for diagnostic inspection.")
                )
                ticket.activity_schedule(
                    'mail.mail_activity_data_todo',
                    summary=_("L2 Engineering Investigation (Ticket #%s)") % ticket.id,
                    note=_("Defect reported by customer:\n%s") % (ticket.description or ticket.name),
                    user_id=ticket.user_id.id if ticket.user_id else self.env.user.id,
                )
            else:
                ticket.al2c_confidence_score = 50.0
                ticket.al2c_autonomous_resolved = False
                ticket.message_post(
                    body=_("🤖 <b>Insilos Autonomous L1 Triage:</b> Inquiry categorized as General. Assigned to customer success queue.")
                )

        return True
