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

    def _check_prerequisite_milestones(self):
        """Enforce sequential SAP Activate Quality Gates (Q-Gates):
        Cannot complete or sign-off milestone N if any prior milestone in sequence
        within the same project lacks verified customer sign-off (Decree 70/2025).
        """
        for ms in self:
            if not ms.project_id:
                continue
            prior_milestones = self.search([
                ('project_id', '=', ms.project_id.id),
                ('sequence', '<', ms.sequence),
                ('id', '!=', ms.id),
            ], order='sequence asc')
            unreached_prior = prior_milestones.filtered(lambda p: not p.al2c_billing_eligible)
            if unreached_prior:
                raise UserError(_(
                    "Prerequisite SAP Activate stage gate locked: Cannot reach or bill milestone '%(current)s' "
                    "until prerequisite stage '%(prior)s' has verified sign-off.",
                    current=ms.name,
                    prior=", ".join(unreached_prior.mapped('name')),
                ))

    def write(self, vals):
        if vals.get('is_reached'):
            self._check_prerequisite_milestones()
        res = super().write(vals)
        if 'al2c_signoff_document_id' in vals or 'is_reached' in vals:
            for ms in self:
                if ms.sale_line_id:
                    ms.sale_line_id._compute_qty_delivered()
        return res

    def action_register_signoff(self, document_id):
        """Register a signed acceptance document for this milestone."""
        self.ensure_one()
        # Segregation of Duties: Autonomous agents cannot self-sign milestones without PM privileges
        if self.env.user.has_group('insilos_al2c.group_al2c_agent') and not self.env.user.has_group('project.group_project_manager'):
            raise UserError(_(
                "Autonomous AI agents cannot self-sign delivery milestone acceptance tokens under SoD governance (AL2C-GOV-002). "
                "A human Project Manager must perform verification."
            ))

        doc = self.env['documents.document'].sudo().browse(document_id)
        if not doc.exists():
            raise UserError(_("Referenced acceptance document does not exist."))

        self._check_prerequisite_milestones()

        self.sudo().write({
            'al2c_signoff_document_id': doc.id,
            'is_reached': True,
        })
        if self.sale_line_id:
            self.sale_line_id._compute_qty_delivered()
        return True
