# Part of Insilos AL2C Enterprise. See LICENSE file for full copyright and licensing details.

from odoo.fields import Date
from odoo.tests.common import TransactionCase


class TestPricelistTypeDispatch(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pricelist = cls.env['product.pricelist'].create({
            'name': 'Dispatch Test Pricelist AL2C',
        })
        cls.template = cls.env['product.template'].create({
            'name': 'Test Template Alpha AL2C',
            'list_price': 100000.0,
        })
        cls.product = cls.template.product_variant_ids[0]

    def test_01_unknown_model_without_tmpl_fk_is_not_silently_templated(self):
        """Boundary: a recordset lacking product_tmpl_id must NOT be auto-classed
        as template purely from field absence. Guards against ID-space aliasing."""
        decoy = self.env['res.partner'].create({'name': 'Decoy Partner No Template AL2C'})
        # Because decoy has neither product_tmpl_id nor product_variant_ids,
        # is_template must be False, and accessing decoy.product_tmpl_id will raise AttributeError
        with self.assertRaises(AttributeError):
            self.pricelist._get_applicable_rules_domain(
                products=decoy,
                date=Date.today(),
            )

    def test_02_product_template_and_variant_classification(self):
        """Verify that genuine templates and variants generate distinct domain structures."""
        # 1. Template record
        domain_tmpl = self.pricelist._get_applicable_rules_domain(
            products=self.template,
            date=Date.today(),
        )
        domain_tmpl_str = str(domain_tmpl)
        # Template domain must search product_tmpl_id in [self.template.id]
        self.assertIn(str(self.template.id), domain_tmpl_str)

        # 2. Variant record
        domain_variant = self.pricelist._get_applicable_rules_domain(
            products=self.product,
            date=Date.today(),
        )
        domain_variant_str = str(domain_variant)
        # Variant domain must target product_id in [self.product.id]
        self.assertIn(str(self.product.id), domain_variant_str)

    def test_03_pricelist_item_two_factor_template_classification(self):
        """Verify that product_pricelist_item._is_applicable_for correctly distinguishes templates and variants."""
        item = self.env['product.pricelist.item'].create({
            'pricelist_id': self.pricelist.id,
            'applied_on': '1_product',
            'product_tmpl_id': self.template.id,
            'compute_price': 'fixed',
            'fixed_price': 80000.0,
        })
        # Applicable for template
        self.assertTrue(item._is_applicable_for(self.template, 1.0))
        # Applicable for variant belonging to template
        self.assertTrue(item._is_applicable_for(self.product, 1.0))
