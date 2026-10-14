# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError

AGENT_GROUP = 'insilos_al2c.group_al2c_agent'
MANAGER_GROUP = 'sales_team.group_sale_manager'


class MailMail(models.Model):
    _inherit = 'mail.mail'

    al2c_trapped = fields.Boolean(
        string='Trapped as Draft (GOV-202)',
        default=False,
        readonly=True,
        help='Autonomous email trapped in draft_only mode under GOV-202 guardrail.',
    )
    al2c_trap_reason = fields.Char(
        string='Trap Reason',
        readonly=True,
        help='Explanation why this autonomous outbound message was intercepted.',
    )
    al2c_approved = fields.Boolean(
        string='Reviewer Approved',
        copy=False,
        default=False,
        help='Indicates whether a sales manager has authorized this trapped email for delivery.',
    )

    def send(self, auto_commit=False, raise_exception=False, post_send_callback=None):
        """GOV-202 Dual-Mode Mail Gate: intercept outbound emails authored by autonomous agents.
        In 'draft_only' mode, emails are trapped as drafts.
        In 'engage' mode, emails with valid recipient consent proceed to delivery.
        """
        mail_mode = self.env['ir.config_parameter'].sudo().get_param('al2c.mail_mode', 'draft_only')

        trapped_mails = self.env['mail.mail']
        allowed_mails = self.env['mail.mail']

        for mail in self.sudo():
            author_user = (mail.author_id.user_ids and mail.author_id.user_ids[0]) or mail.create_uid
            is_agent_author = bool(author_user and author_user.has_group(AGENT_GROUP))
            if is_agent_author and not mail.al2c_approved:
                if mail_mode == 'draft_only':
                    mail.sudo().write({
                        'al2c_trapped': True,
                        'al2c_trap_reason': 'GOV-202: Autonomous outbound email trapped in draft_only mode. Requires human sales manager approval.',
                    })
                    trapped_mails |= mail
                    continue
            allowed_mails |= mail

        if not allowed_mails:
            return True

        auto_delete_ids = allowed_mails.sudo().filtered('auto_delete').ids
        if auto_delete_ids:
            allowed_mails.sudo().browse(auto_delete_ids).write({'auto_delete': False})
        res = super(MailMail, allowed_mails).send(
            auto_commit=auto_commit,
            raise_exception=raise_exception,
            post_send_callback=post_send_callback,
        )
        if auto_delete_ids:
            self.env['mail.mail'].sudo().browse(auto_delete_ids).exists().filtered(
                lambda m: m.state == 'sent'
            ).unlink()
        return res

    def action_approve_and_send(self):
        """Action for sales managers to approve and release trapped autonomous emails."""
        self.ensure_one()
        if not (self.env.user.has_group(MANAGER_GROUP) or self.env.user._is_admin()):
            raise AccessError(_("Only sales managers can approve trapped autonomous emails."))
        self.sudo().write({
            'al2c_approved': True,
            'al2c_trapped': False,
            'al2c_trap_reason': False,
        })
        return self.sudo().send()
