from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    al2c_product_line = fields.Selection(
        [
            ('erp', 'ERP'),
            ('grc', 'GRC'),
            ('ai', 'AI Solutions'),
            ('mojo', 'Mojo AI Apps'),
            ('svc', 'Services'),
        ],
        string='Product Line',
        index=True,
    )
    al2c_vat_class = fields.Selection(
        [
            ('kct', 'KCT Software (VAT Exempt - Law 48/2024/QH15)'),
            ('vat_8', 'IT Services 8% (Decree 174/2025/ND-CP)'),
            ('vat_10', 'Standard 10% (Infrastructure / Hosting / Hardware)'),
        ],
        string='VAT Classification',
        default='kct',
        index=True,
        help='Vietnamese statutory tax classification under Law 48/2024/QH15 and Decree 174/2025/ND-CP.',
    )
    al2c_knowledge_article_id = fields.Many2one(
        'knowledge.article',
        string='Knowledge Article',
        help='Source-of-truth article for this SKU (used for grounding of sales and marketing content).',
        index='btree_not_null',
        ondelete='set null',
    )

    @api.model
    def _al2c_ensure_variant_xmlids(self):
        """Create ``insilos_al2c.<template xmlid>_variant`` for the single variant of
        every catalog template defined by this module (idempotent)."""
        IMD = self.env['ir.model.data'].sudo()
        records = IMD.search([('module', '=', 'insilos_al2c'), ('model', '=', self._name)])
        for imd in records:
            template = self.browse(imd.res_id).exists()
            variant = template.product_variant_id
            if not variant:
                continue
            name = '%s_variant' % imd.name
            existing = IMD.search([('module', '=', 'insilos_al2c'), ('name', '=', name)], limit=1)
            if existing:
                if existing.res_id != variant.id:
                    existing.res_id = variant.id
            else:
                IMD.create({
                    'module': 'insilos_al2c', 'name': name, 'model': variant._name,
                    'res_id': variant.id, 'noupdate': True,
                })
        return True

