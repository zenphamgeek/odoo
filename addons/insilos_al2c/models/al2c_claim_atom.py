# -*- coding: utf-8 -*-
import hashlib
from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError

MANAGER_GROUP = 'sales_team.group_sale_manager'


class Al2cClaimAtom(models.Model):
    """Canonical atomic capability, benchmark, compliance, or pricing claim.
    Content generation engines and marketing automations must assemble verified
    Claim Atoms rather than generating free-form factual assertions.
    """
    _name = 'al2c.claim.atom'
    _description = 'AL2C Canonical Claim Atom'
    _order = 'sku_id, claim_type, name'

    name = fields.Char(string='Claim Headline', required=True)
    claim_text = fields.Text(string='Canonical Statement', required=True)
    claim_type = fields.Selection([
        ('feature', 'Feature & Architecture'),
        ('benchmark', 'Performance Benchmark'),
        ('compliance', 'Regulatory & Compliance'),
        ('pricing_rule', 'Pricing & Commercial Terms'),
        ('sla', 'Service Level Agreement'),
    ], string='Claim Type', required=True, default='feature')

    source_article_id = fields.Many2one(
        'knowledge.article',
        string='Authoritative Knowledge Article',
        ondelete='restrict',
        required=True,
    )
    sku_id = fields.Many2one(
        'product.template',
        string='Associated Product SKU',
        ondelete='cascade',
    )
    claim_hash = fields.Char(
        string='Claim Hash (SHA-256)',
        compute='_compute_claim_hash',
        store=True,
        index=True,
    )
    verification_state = fields.Selection([
        ('draft', 'Draft (Unverified)'),
        ('verified', 'Verified Canonical'),
        ('rejected', 'Rejected / Deprecated'),
    ], string='Verification State', default='draft', required=True)

    verified_by_uid = fields.Many2one('res.users', string='Verified By', readonly=True)
    verified_date = fields.Datetime(string='Verified Date', readonly=True)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('claim_hash_uniq', 'unique(claim_hash)', 'A Claim Atom with identical normalized content already exists!'),
    ]

    @api.depends('claim_text')
    def _compute_claim_hash(self):
        for atom in self:
            if atom.claim_text:
                normalized = atom.claim_text.strip().lower()
                atom.claim_hash = hashlib.sha256(normalized.encode('utf-8')).hexdigest()
            else:
                atom.claim_hash = False

    def action_verify(self):
        """Verify claim atom. Only sales/product marketing managers or admins can verify."""
        if not (self.env.user.has_group(MANAGER_GROUP) or self.env.user._is_admin()):
            raise AccessError(_("Only sales and marketing managers can verify canonical Claim Atoms."))
        self.write({
            'verification_state': 'verified',
            'verified_by_uid': self.env.user.id,
            'verified_date': fields.Datetime.now(),
        })
        return True

    def action_reject(self):
        self.write({
            'verification_state': 'rejected',
        })
        return True

    @api.model
    def verify_marketing_assertion(self, assertion_text):
        """Verify whether an external marketing assertion is backed by a verified Claim Atom.
        Raises ValidationError if no verified Claim Atom entails or backs the statement.
        """
        if not assertion_text or not assertion_text.strip():
            return False

        normalized = assertion_text.strip().lower()
        hash_val = hashlib.sha256(normalized.encode('utf-8')).hexdigest()

        # Check exact hash match
        matching_atom = self.search([
            ('claim_hash', '=', hash_val),
            ('verification_state', '=', 'verified'),
            ('active', '=', True),
        ], limit=1)

        if matching_atom:
            return matching_atom

        # Substring / keyword entailment search across active verified claims
        verified_atoms = self.search([
            ('verification_state', '=', 'verified'),
            ('active', '=', True),
        ])
        for atom in verified_atoms:
            atom_clean = atom.claim_text.strip().lower()
            if atom_clean in normalized or normalized in atom_clean:
                return atom

        raise ValidationError(
            _("Unverified Marketing Assertion: Statement '%(text)s' does not entail any verified canonical Claim Atom in the Knowledge repository.",
              text=assertion_text)
        )
