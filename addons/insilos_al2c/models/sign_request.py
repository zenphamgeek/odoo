from hashlib import sha256
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SignLog(models.Model):
    _inherit = 'sign.log'

    def _get_or_check_hash(self, vals):
        """Returns the hash to write on sign log entries, ensuring previous_hash is a string."""
        if vals.get('action') not in ['sign', 'create']:
            return False
        domain = [('sign_request_id', '=', vals['sign_request_id']), ('action', 'in', ['create', 'sign'])]
        if 'id' in vals:
            domain.append(('id', '<', vals['id']))
        prev_activity = self.sudo().search(domain, limit=1, order='id desc')
        previous_hash = ""
        sign_request = not prev_activity and self.env['sign.request'].browse(vals['sign_request_id'])
        if sign_request and sign_request.template_id.document_ids:
            body = sign_request.template_id.document_ids[0].with_context(bin_size=False).attachment_id.datas or b''
        else:
            previous_hash = prev_activity.log_hash or ""
            body = self._compute_string_to_hash(vals)
        return sha256(((previous_hash or "") + str(body)).encode('utf-8')).hexdigest()


class SignRequest(models.Model):
    _inherit = 'sign.request'

    al2c_has_deviation = fields.Boolean(
        string='Clause Deviation Detected',
        default=False,
        tracking=True,
        help='Indicates whether unapproved liability, warranty, or penalty contract deviations were detected.'
    )
    al2c_deviation_summary = fields.Text(
        string='Deviation Summary',
        tracking=True,
    )
    al2c_clause_status = fields.Selection([
        ('standard', 'Standard Clauses'),
        ('deviated', 'Deviation Detected'),
        ('approved', 'General Counsel Approved'),
        ('rejected', 'GC Rejected'),
    ], string='Clause Compliance Status', default='standard', tracking=True)

    al2c_gc_approval_user_id = fields.Many2one(
        'res.users',
        string='Approved By General Counsel',
        tracking=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        default_role = self.env.ref('sign.sign_item_role_user', raise_if_not_found=False) or self.env['sign.item.role'].search([], limit=1)
        for vals in vals_list:
            if not vals.get('reference'):
                if vals.get('template_id'):
                    tmpl = self.env['sign.template'].browse(vals['template_id'])
                    vals['reference'] = tmpl.name or 'Signed Agreement'
                else:
                    vals['reference'] = 'Signed Agreement'
            if not vals.get('request_item_ids') and default_role:
                partner_id = self.env.user.partner_id.id
                vals['request_item_ids'] = [(0, 0, {
                    'partner_id': partner_id,
                    'role_id': default_role.id,
                })]
        return super().create(vals_list)

    def action_scan_contract_deviations(self, redline_text=None):
        """
        Scan contract text or customer redlines against standard legal baseline.
        Flags high-risk deviations in liability, warranties, indemnification, penalties.
        """
        HIGH_RISK_PATTERNS = [
            ('unlimited liability', 'Customer demands uncapped unlimited liability'),
            ('consequential damages', 'Customer altered consequential / indirect damages exclusion'),
            ('gross negligence', 'Unbalanced gross negligence liability clause'),
            ('liquidated damages', 'Liquidated damages / penalty exceeding statutory caps'),
            ('phạt vi phạm', 'Penalties exceeding 8% statutory cap under Vietnam Commercial Law'),
            ('indemnify and hold harmless', 'Broad unilateral indemnification obligation'),
            ('governing law', 'Foreign governing law or foreign jurisdiction clause'),
        ]

        for req in self:
            text_to_scan = (redline_text or req.message or '').lower()
            if not text_to_scan and req.attachment_ids:
                text_to_scan = ' '.join(req.attachment_ids.mapped('name')).lower()

            detected_issues = []
            for pattern, description in HIGH_RISK_PATTERNS:
                if pattern in text_to_scan:
                    detected_issues.append(f"- {description} (keyword: '{pattern}')")

            if detected_issues:
                summary = "Non-standard contract terms detected:\n" + "\n".join(detected_issues)
                req.write({
                    'al2c_has_deviation': True,
                    'al2c_clause_status': 'deviated',
                    'al2c_deviation_summary': summary,
                })
                # Create General Counsel approval activity
                gc_user = self.env.ref('base.user_admin', raise_if_not_found=False) or self.env.user
                activity_type = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
                if activity_type:
                    req.activity_schedule(
                        activity_type_id=activity_type.id,
                        user_id=gc_user.id,
                        summary='Contract Clause Deviation: General Counsel Approval Required',
                        note=summary,
                    )
                req.message_post(
                    body=f"<b>AL2C Security Sentinel:</b> {summary}<br/><i>Sent for General Counsel approval.</i>",
                    message_type='comment',
                    subtype_xmlid='mail.mt_note'
                )
            else:
                req.write({
                    'al2c_has_deviation': False,
                    'al2c_clause_status': 'standard',
                    'al2c_deviation_summary': False,
                })
        return True

    def action_approve_deviations(self, note=None):
        """General Counsel or Authorized Manager approves the contract deviations."""
        is_manager = self.env.user.has_group('sales_team.group_sale_manager') or self.env.is_admin()
        if not is_manager:
            raise UserError(_("Only General Counsel or a Sales Manager can approve contract clause deviations."))

        for req in self:
            req.sudo().write({
                'al2c_clause_status': 'approved',
                'al2c_gc_approval_user_id': self.env.user.id,
            })
            # Mark open deviation approval activities done
            activities = req.activity_ids.filtered(
                lambda a: 'General Counsel Approval Required' in (a.summary or '')
            )
            activities.sudo().unlink()
            req.sudo().message_post(
                body=f"<b>General Counsel Approval Granted</b> by {self.env.user.name}. {note or ''}",
                message_type='comment',
                subtype_xmlid='mail.mt_note'
            )
        return True

    def action_reject_deviations(self, reason=None):
        """General Counsel rejects the contract deviations."""
        is_manager = self.env.user.has_group('sales_team.group_sale_manager') or self.env.is_admin()
        if not is_manager:
            raise UserError(_("Only General Counsel or a Sales Manager can reject contract clause deviations."))

        for req in self:
            req.sudo().write({
                'al2c_clause_status': 'rejected',
            })
            activities = req.activity_ids.filtered(
                lambda a: 'General Counsel Approval Required' in (a.summary or '')
            )
            activities.sudo().unlink()
            req.sudo().message_post(
                body=f"<b>General Counsel Rejection:</b> {reason or 'Deviation rejected by GC.'}",
                message_type='comment',
                subtype_xmlid='mail.mt_note'
            )
        return True

    def _check_al2c_clause_guard(self):
        """Block signing or sending if unapproved deviations exist."""
        for req in self:
            if req.al2c_has_deviation and req.al2c_clause_status != 'approved':
                raise UserError(_(
                    "Contract has unapproved clause deviations. "
                    "General Counsel approval is strictly required before issuing or finalizing this agreement."
                ))

    def action_sign(self, *args, **kwargs):
        self._check_al2c_clause_guard()
        return super().action_sign(*args, **kwargs)
