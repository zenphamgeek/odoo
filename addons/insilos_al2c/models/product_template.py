from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


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

    @api.model
    def _al2c_align_catalog_prices(self):
        """Align product.template.list_price and product.pricelist.item with VND catalog fixed prices per SRS v1.1 Section 5.1."""
        catalog_prices = {
            'ERP-STARTER': 150_000_000.0,
            'ERP-GROWTH': 450_000_000.0,
            'ERP-ENT': 1_200_000_000.0,
            'SAAS-USER-M': 350_000.0,
            'SAAS-HOSTING-PRO': 15_000_000.0,
            'SAAS-SLA-PLUS': 20_000_000.0,
            'GRC-ESSENTIALS': 180_000_000.0,
            'GRC-RISK-REGISTER': 120_000_000.0,
            'GRC-AUDIT-PACK': 250_000_000.0,
            'AI-DISCOVERY': 80_000_000.0,
            'AI-POC': 160_000_000.0,
            'AI-PILOT': 380_000_000.0,
            'AI-PROD': 650_000.0,
            'MOJO-APP-SUB': 25_000_000.0,
            'MOJO-TOKENS': 10_000_000.0,
            'MOJO-ONPREM': 500_000_000.0,
            'AMS-BRONZE': 15_000_000.0,
            'AMS-SILVER': 35_000_000.0,
            'AMS-GOLD': 65_000_000.0,
            'TRAINING-DAY': 15_000_000.0,
            'CONSULT-HOUR': 1_200_000.0,
        }
        pricelist_vnd = self.env.ref('insilos_al2c.pricelist_vnd', raise_if_not_found=False)
        PricelistItem = self.env['product.pricelist.item'].sudo()
        IMD = self.env['ir.model.data'].sudo()
        for sku, price in catalog_prices.items():
            tmpl = self.search([('default_code', '=', sku)], limit=1)
            if tmpl:
                tmpl.sudo().write({'list_price': price})
                if tmpl.product_variant_id:
                    tmpl.product_variant_id.sudo().write({'lst_price': price})
                domain = [('product_tmpl_id', '=', tmpl.id)]
                if pricelist_vnd:
                    domain.append(('pricelist_id', '=', pricelist_vnd.id))
                items = PricelistItem.search(domain)
                if items:
                    items.write({'fixed_price': price})

        # Ensure noupdate=False on pricelist items in ir_model_data so XML upgrades stay in sync
        imd_records = IMD.search([('module', '=', 'insilos_al2c'), ('model', '=', 'product.pricelist.item')])
        if imd_records:
            imd_records.write({'noupdate': False})
        return True


class UomUom(models.Model):
    _inherit = 'uom.uom'

    rounding = fields.Float(
        'Rounding Precision', default=0.01, digits=0, required=True,
        help="Compatibility shim for sale_subscription precision rounding."
    )

    @api.constrains('rounding')
    def _check_rounding_positive(self):
        for u in self:
            if hasattr(u, 'rounding') and (not u.rounding or u.rounding <= 0):
                raise ValidationError(_("UoM '%s' rounding precision must be strictly greater than 0.") % (u.name or ''))


from odoo import tools
if tools.config.get('test_enable') or tools.config.get('test_tags'):
    try:
        from ..tests import test_al2c_pricing  # noqa: F401
    except Exception:
        pass


