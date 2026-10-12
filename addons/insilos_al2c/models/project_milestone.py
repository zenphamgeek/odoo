# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from . import sale_order_line

ACTIVATE_DEFAULT_WEIGHTS = {
    'prepare': 0.15,
    'explore': 0.25,
    'realize': 0.35,
    'deploy': 0.15,
    'run': 0.10,
}

ACTIVATE_PHASES = ['prepare', 'explore', 'realize', 'deploy', 'run']

ACTIVATE_DEFAULT_SEQUENCES = {
    'prepare': 10,
    'explore': 20,
    'realize': 30,
    'deploy': 40,
    'run': 50,
}

RESTRICTED_ALTERATION_FIELDS = {
    'quantity_percentage',
    'deadline',
    'sequence',
    'is_reached',
    'al2c_signoff_document_id',
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

    def _get_activate_phase_index(self):
        self.ensure_one()
        name_lower = (self.name or '').strip().lower()
        for idx, phase in enumerate(ACTIVATE_PHASES):
            if phase in name_lower:
                return idx
        return None

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            name_lower = (vals.get('name') or '').strip().lower()
            if not vals.get('quantity_percentage'):
                for phase, weight in ACTIVATE_DEFAULT_WEIGHTS.items():
                    if phase in name_lower:
                        vals['quantity_percentage'] = weight
                        break
            if not vals.get('sequence'):
                for phase, seq in ACTIVATE_DEFAULT_SEQUENCES.items():
                    if phase in name_lower:
                        vals['sequence'] = seq
                        break
        records = super().create(vals_list)
        for rec in records:
            if rec.is_reached:
                rec._check_prerequisite_milestones()
        return records

    def _check_prerequisite_milestones(self):
        """Enforce sequential SAP Activate Quality Gates (Q-Gates):
        Cannot complete, reach, or sign-off milestone N if any prior milestone in sequence
        or phase order within the same project lacks verified customer sign-off (Decree 70/2025).
        """
        for ms in self:
            if not ms.project_id:
                continue
            all_milestones = self.search([
                ('project_id', '=', ms.project_id.id),
                ('id', '!=', ms.id),
            ], order='sequence asc, id asc')

            ms_phase_idx = ms._get_activate_phase_index()

            prior_milestones = self.env['project.milestone']
            for other in all_milestones:
                other_phase_idx = other._get_activate_phase_index()
                is_prior = False
                if other.sequence < ms.sequence:
                    is_prior = True
                elif ms_phase_idx is not None and other_phase_idx is not None:
                    if other_phase_idx < ms_phase_idx:
                        is_prior = True
                if is_prior:
                    prior_milestones |= other

            unreached_prior = prior_milestones.filtered(lambda p: not p.al2c_billing_eligible)
            if unreached_prior:
                raise UserError(_(
                    "Prerequisite SAP Activate stage gate locked: Cannot reach, approve, or bill milestone '%(current)s' "
                    "until prerequisite stage '%(prior)s' has verified customer sign-off (al2c_billing_eligible).",
                    current=ms.name,
                    prior=", ".join(unreached_prior.mapped('name')),
                ))

    def write(self, vals):
        # 1. SoD: Block autonomous agents from altering milestone weights, schedule, or completion
        if not self.env.su and self.env.user.has_group('insilos_al2c.group_al2c_agent'):
            if RESTRICTED_ALTERATION_FIELDS.intersection(vals.keys()):
                raise UserError(_(
                    "Segregation of Duties (AL2C-GOV-002): Autonomous AI agents cannot alter project milestone "
                    "weights, schedules, or completion status. A human Project Manager is required."
                ))

        # 2. SoD: Restrict alteration of milestone scope/weights/deadlines/status to Project Managers
        if not self.env.su and not self.env.user.has_group('project.group_project_manager'):
            if RESTRICTED_ALTERATION_FIELDS.intersection(vals.keys()):
                raise UserError(_(
                    "Segregation of Duties (SoD): Only Project Managers can alter project milestone "
                    "weights, deadlines, sequence, or sign-off status."
                ))

        # 3. Stage Gates: If marking is_reached, verify prerequisite gates
        if vals.get('is_reached'):
            self._check_prerequisite_milestones()

        res = super().write(vals)

        if 'al2c_signoff_document_id' in vals or 'is_reached' in vals:
            for ms in self:
                if ms.sale_line_id:
                    ms.sudo().sale_line_id._compute_qty_delivered()
        return res

    def unlink(self):
        if not self.env.su and self.env.user.has_group('insilos_al2c.group_al2c_agent'):
            raise UserError(_("Autonomous AI agents cannot delete project milestones under SoD governance."))
        if not self.env.su and not self.env.user.has_group('project.group_project_manager'):
            raise UserError(_("Segregation of Duties: Only Project Managers can delete project milestones."))
        return super().unlink()

    def action_register_signoff(self, document_id):
        """Register a signed acceptance document for this milestone."""
        self.ensure_one()

        # 1. SoD: Block autonomous agents
        if self.env.user.has_group('insilos_al2c.group_al2c_agent'):
            raise UserError(_(
                "Autonomous AI agents cannot self-sign delivery milestone acceptance tokens under SoD governance (AL2C-GOV-002). "
                "A human Project Manager must perform verification."
            ))

        # 2. SoD: Restrict to Project Managers
        if not self.env.su and not self.env.user.has_group('project.group_project_manager'):
            raise UserError(_(
                "Segregation of Duties: Only Project Managers can register customer sign-off on milestones."
            ))

        doc = self.env['documents.document'].sudo().browse(document_id)
        if not doc.exists():
            raise UserError(_("Referenced acceptance document does not exist."))

        # 3. Sequential Activate Gate Check
        self._check_prerequisite_milestones()

        self.sudo().write({
            'al2c_signoff_document_id': doc.id,
            'is_reached': True,
        })
        if self.sale_line_id:
            self.sudo().sale_line_id._compute_qty_delivered()
        return True
