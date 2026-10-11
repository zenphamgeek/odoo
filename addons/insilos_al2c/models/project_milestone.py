# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError

ACTIVATE_DEFAULT_WEIGHTS = {
    'prepare': 0.15,
    'explore': 0.25,
    'realize': 0.35,
    'deploy': 0.15,
    'run': 0.10,
}


class ProjectMilestone(models.Model):
    _inherit = 'project.milestone'

    al2c_signoff_document_id = fields.Many2one(
        'documents.document',
        string='Customer Sign-Off Document',
        tracking=True,
        help='Signed customer acceptance certificate required under Decree 70/2025 before milestone is eligible for autonomous billing.',
    )
    al2c_billing_eligible = fields.Boolean(
        string='Billing Eligible',
        compute='_compute_al2c_billing_eligible',
        store=True,
        tracking=True,
        help='Indicates whether this milestone has been reached AND has a valid signed customer acceptance token attached.',
    )

    @api.depends('is_reached', 'al2c_signoff_document_id')
    def _compute_al2c_billing_eligible(self):
        for ms in self:
            ms.al2c_billing_eligible = bool(ms.is_reached and ms.al2c_signoff_document_id)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('quantity_percentage'):
                name_lower = (vals.get('name') or '').strip().lower()
                for phase, weight in ACTIVATE_DEFAULT_WEIGHTS.items():
                    if phase in name_lower:
                        vals['quantity_percentage'] = weight
                        break
        return super().create(vals_list)

    def action_register_signoff(self, document_id):
        """Register a signed acceptance document for this milestone."""
        self.ensure_one()
        doc = self.env['documents.document'].sudo().browse(document_id)
        if not doc.exists():
            raise UserError(_("Referenced acceptance document does not exist."))
        self.sudo().write({
            'al2c_signoff_document_id': doc.id,
            'is_reached': True,
        })
        return True

