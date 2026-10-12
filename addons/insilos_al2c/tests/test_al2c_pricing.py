# -*- coding: utf-8 -*-
from odoo import Command
from odoo.tests import TransactionCase, new_test_user, tagged
from .test_al2c import _isolate_dev_db

try:
    from odoo.addons.sale_subscription.models.product_pricelist_item import ProductPricelistItem as SubPricelistItem
    _orig_sub_is_applicable_for = SubPricelistItem._is_applicable_for
    if 'kwargs' not in _orig_sub_is_applicable_for.__code__.co_varnames:
        def _patched_sub_is_applicable_for(self, product, qty_in_product_uom, *args, uom=None, **kwargs):
            if self.plan_id and not product.recurring_invoice:
                return False
            if not self.plan_id and product.recurring_invoice and not getattr(product, 'allow_one_time_sale', False):
                return False
            return super(SubPricelistItem, self)._is_applicable_for(product, qty_in_product_uom, uom=uom, **kwargs)
        SubPricelistItem._is_applicable_for = _patched_sub_is_applicable_for
except Exception:
    pass

CATALOG_SRS_PRICES = {
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

VAT_CLASSIFICATIONS = {
    'kct': [
        'ERP-STARTER', 'ERP-GROWTH', 'ERP-ENT', 'SAAS-USER-M', 'GRC-ESSENTIALS',
        'GRC-RISK-REGISTER', 'GRC-AUDIT-PACK', 'AI-POC', 'AI-PILOT', 'AI-PROD',
        'MOJO-APP-SUB', 'MOJO-TOKENS', 'MOJO-ONPREM',
    ],
    'vat_8': [
        'SAAS-SLA-PLUS', 'AI-DISCOVERY', 'AMS-BRONZE', 'AMS-SILVER', 'AMS-GOLD',
        'TRAINING-DAY', 'CONSULT-HOUR',
    ],
    'vat_10': [
        'SAAS-HOSTING-PRO',
    ],
}

TRACKING_POLICIES = {
    'project_only': [
        'ERP-STARTER', 'ERP-GROWTH', 'ERP-ENT', 'GRC-ESSENTIALS', 'GRC-RISK-REGISTER',
        'GRC-AUDIT-PACK', 'AI-DISCOVERY', 'AI-POC', 'AI-PILOT', 'MOJO-ONPREM',
    ],
    'task_in_project': [
        'AI-PROD',
    ],
    'task_global_project': [
        'CONSULT-HOUR',
    ],
    'no': [
        'SAAS-USER-M', 'SAAS-HOSTING-PRO', 'SAAS-SLA-PLUS', 'MOJO-APP-SUB', 'MOJO-TOKENS',
        'AMS-BRONZE', 'AMS-SILVER', 'AMS-GOLD', 'TRAINING-DAY',
    ],
}

SUBSCRIPTION_SKUS = [
    'SAAS-USER-M', 'SAAS-HOSTING-PRO', 'SAAS-SLA-PLUS', 'MOJO-APP-SUB',
    'AMS-BRONZE', 'AMS-SILVER', 'AMS-GOLD',
]


@tagged('post_install', '-at_install', 'insilos_al2c')
class TestAl2cPricing(TransactionCase):
    """
    Comprehensive tests for AL2C Product Catalog Alignment, VND-denominated pricing,
    Decree 174/2025 and Law 48/2024 statutory tax classification mapping, tracking policies,
    and CPQ discount guardrails (R1).
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        _isolate_dev_db(cls)
        # Ensure template prices are aligned with SRS v1.1
        cls.env['product.template']._al2c_align_catalog_prices()

        pricelist_vnd = cls.env.ref('insilos_al2c.pricelist_vnd', raise_if_not_found=False)
        cls.partner = cls.env['res.partner'].create({
            'name': 'Innoria Enterprise Test Partner',
            'is_company': True,
            'property_product_pricelist': pricelist_vnd.id if pricelist_vnd else False,
        })
        cls.agent = new_test_user(
            cls.env,
            login='al2c_pricing_agent',
            name='AL2C Pricing Agent',
            groups='sales_team.group_sale_salesman,insilos_al2c.group_al2c_agent',
        )
        cls.icp = cls.env['ir.config_parameter'].sudo()
        cls.icp.set_param('al2c.autonomy_enabled', 'True')
        cls.icp.set_param('al2c.max_discount', '10')
        cls.icp.set_param('al2c.max_tcv', '500000000')

    def _product_template(self, sku):
        return self.env['product.template'].search([('default_code', '=', sku)], limit=1)

    def _product_variant(self, sku):
        return self.env['product.product'].search([('default_code', '=', sku)], limit=1)

    def test_catalog_vnd_list_prices(self):
        """Test that all 21 SKUs have correct VND list_price without USD float artifacts."""
        for sku, expected_price in CATALOG_SRS_PRICES.items():
            tmpl = self._product_template(sku)
            self.assertTrue(tmpl, f"Product template for SKU {sku} must exist")
            self.assertAlmostEqual(
                tmpl.list_price,
                expected_price,
                places=0,
                msg=f"SKU {sku} list_price must be {expected_price} VND, got {tmpl.list_price}",
            )
            # Ensure no legacy USD-scale float artifact (< 100,000 VND)
            self.assertGreaterEqual(
                tmpl.list_price,
                350_000.0,
                f"SKU {sku} list_price appears to be a USD float artifact: {tmpl.list_price}",
            )
            variant = self._product_variant(sku)
            self.assertTrue(variant, f"Product variant for SKU {sku} must exist")
            self.assertAlmostEqual(
                variant.lst_price,
                expected_price,
                places=0,
                msg=f"SKU {sku} variant lst_price must match {expected_price} VND",
            )

    def test_pricelist_vnd_fixed_prices(self):
        """Test that pricelist_vnd has exact fixed price entries matching SRS v1.1 Section 5.1."""
        pricelist = self.env.ref('insilos_al2c.pricelist_vnd', raise_if_not_found=False)
        self.assertTrue(pricelist, "pricelist_vnd record must exist")
        self.assertEqual(pricelist.currency_id.name, 'VND')

        for sku, expected_price in CATALOG_SRS_PRICES.items():
            tmpl = self._product_template(sku)
            item = self.env['product.pricelist.item'].search([
                ('pricelist_id', '=', pricelist.id),
                ('product_tmpl_id', '=', tmpl.id),
            ], limit=1)
            self.assertTrue(item, f"Pricelist item for {sku} must exist in pricelist_vnd")
            self.assertEqual(item.compute_price, 'fixed')
            self.assertAlmostEqual(
                item.fixed_price,
                expected_price,
                places=0,
                msg=f"Pricelist item fixed_price for {sku} must be {expected_price} VND, got {item.fixed_price}",
            )

    def test_tracking_policies_and_subscriptions(self):
        """Test tracking policies, subscription flags, and linked project templates across 21 SKUs."""
        for policy, skus in TRACKING_POLICIES.items():
            for sku in skus:
                tmpl = self._product_template(sku)
                self.assertTrue(tmpl, f"Template for {sku} must exist")
                self.assertEqual(
                    tmpl.service_tracking,
                    policy,
                    f"SKU {sku} service_tracking must be '{policy}', got '{tmpl.service_tracking}'",
                )

        for sku in CATALOG_SRS_PRICES:
            tmpl = self._product_template(sku)
            is_sub = sku in SUBSCRIPTION_SKUS
            self.assertEqual(
                bool(tmpl.recurring_invoice),
                is_sub,
                f"SKU {sku} recurring_invoice must be {is_sub}, got {tmpl.recurring_invoice}",
            )

        # Implementation templates
        for sku in ['ERP-STARTER', 'ERP-GROWTH', 'ERP-ENT', 'GRC-ESSENTIALS', 'AI-DISCOVERY', 'AI-POC', 'AI-PILOT', 'MOJO-ONPREM']:
            tmpl = self._product_template(sku)
            self.assertTrue(tmpl.project_template_id, f"SKU {sku} must have linked project_template_id")
            self.assertTrue(tmpl.project_template_id.is_template)

        # Global project pool for consulting
        consult_tmpl = self._product_template('CONSULT-HOUR')
        self.assertTrue(consult_tmpl.project_id, "CONSULT-HOUR must link to project_consulting_pool")
        self.assertEqual(consult_tmpl.project_id, self.env.ref('insilos_al2c.project_consulting_pool'))

    def test_al2c_vat_class_tax_mapping_and_amounts(self):
        """Test Law 48/2024 (KCT), Decree 174/2025 (8%), and Standard (10%) VAT wiring on sale order lines."""
        for vat_class, skus in VAT_CLASSIFICATIONS.items():
            for sku in skus:
                tmpl = self._product_template(sku)
                self.assertEqual(
                    tmpl.al2c_vat_class,
                    vat_class,
                    f"SKU {sku} al2c_vat_class must be '{vat_class}', got '{tmpl.al2c_vat_class}'",
                )

        p_starter = self._product_variant('ERP-STARTER')      # KCT (0% VAT) - 150M VND
        p_sla = self._product_variant('SAAS-SLA-PLUS')        # VAT 8% - 20M VND
        p_hosting = self._product_variant('SAAS-HOSTING-PRO')  # VAT 10% - 15M VND

        so = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                Command.create({
                    'product_id': p_starter.id,
                    'product_uom_qty': 1,
                    'price_unit': 150_000_000.0,
                }),
                Command.create({
                    'product_id': p_sla.id,
                    'product_uom_qty': 1,
                    'price_unit': 20_000_000.0,
                }),
                Command.create({
                    'product_id': p_hosting.id,
                    'product_uom_qty': 1,
                    'price_unit': 15_000_000.0,
                }),
            ],
        })

        line_starter = so.order_line.filtered(lambda l: l.product_id == p_starter)
        line_sla = so.order_line.filtered(lambda l: l.product_id == p_sla)
        line_hosting = so.order_line.filtered(lambda l: l.product_id == p_hosting)

        # 1. KCT Line: VAT Exempt under Law 48/2024
        self.assertEqual(line_starter.al2c_vat_class, 'kct')
        self.assertAlmostEqual(line_starter.price_subtotal, 150_000_000.0, places=0)
        self.assertAlmostEqual(line_starter.price_tax, 0.0, places=0)
        self.assertAlmostEqual(line_starter.price_total, 150_000_000.0, places=0)

        # 2. SLA Line: 8% VAT under Decree 174/2025
        self.assertEqual(line_sla.al2c_vat_class, 'vat_8')
        self.assertAlmostEqual(line_sla.price_subtotal, 20_000_000.0, places=0)
        self.assertAlmostEqual(line_sla.price_tax, 1_600_000.0, places=0, msg="20M * 8% must be 1.6M VND")
        self.assertAlmostEqual(line_sla.price_total, 21_600_000.0, places=0)

        # 3. Hosting Line: 10% VAT Standard
        self.assertEqual(line_hosting.al2c_vat_class, 'vat_10')
        self.assertAlmostEqual(line_hosting.price_subtotal, 15_000_000.0, places=0)
        self.assertAlmostEqual(line_hosting.price_tax, 1_500_000.0, places=0, msg="15M * 10% must be 1.5M VND")
        self.assertAlmostEqual(line_hosting.price_total, 16_500_000.0, places=0)

        # Order level aggregates
        self.assertAlmostEqual(so.amount_untaxed, 185_000_000.0, places=0)
        self.assertAlmostEqual(so.amount_tax, 3_100_000.0, places=0)
        self.assertAlmostEqual(so.amount_total, 188_100_000.0, places=0)

    def test_effective_discount_guardrail_vnd_scale(self):
        """Test Deal Desk effective discount ceiling (AL2C-SAL-302) using VND list price."""
        p_starter = self._product_variant('ERP-STARTER')  # list_price = 150M VND

        # Case 1: Standard price (150M VND) -> 0% discount, no breach
        so_full = self.env['sale.order'].with_user(self.agent).create({
            'partner_id': self.partner.id,
            'user_id': self.agent.id,
            'order_line': [Command.create({
                'product_id': p_starter.id,
                'product_uom_qty': 1,
                'price_unit': 150_000_000.0,
            })],
        })
        breaches_full = so_full._al2c_threshold_breaches()
        self.assertFalse(
            any("effective discount" in r or "line discount" in r for r in breaches_full),
            f"Full price quotation should not trigger discount breach, got breaches: {breaches_full}",
        )

        # Case 2: 140M VND unit price (effective discount ~6.67% <= 10% max) -> no breach
        so_mild = self.env['sale.order'].with_user(self.agent).create({
            'partner_id': self.partner.id,
            'user_id': self.agent.id,
            'order_line': [Command.create({
                'product_id': p_starter.id,
                'product_uom_qty': 1,
                'price_unit': 140_000_000.0,
            })],
        })
        self.assertFalse(
            any("effective discount" in r or "line discount" in r for r in so_mild._al2c_threshold_breaches()),
            "6.67% discount should be within the 10% ceiling",
        )

        # Case 3: 130M VND unit price (effective discount ~13.33% > 10% max) -> triggers breach!
        so_heavy = self.env['sale.order'].with_user(self.agent).create({
            'partner_id': self.partner.id,
            'user_id': self.agent.id,
            'order_line': [Command.create({
                'product_id': p_starter.id,
                'product_uom_qty': 1,
                'price_unit': 130_000_000.0,
            })],
        })
        breaches = so_heavy._al2c_threshold_breaches()
        self.assertTrue(
            any("effective discount" in r and "ceiling" in r for r in breaches),
            f"13.33% effective discount must trigger breach on 150M list price, breaches: {breaches}",
        )

        # Case 4: Stated discount field 15% -> triggers line discount breach
        so_stated = self.env['sale.order'].with_user(self.agent).create({
            'partner_id': self.partner.id,
            'user_id': self.agent.id,
            'order_line': [Command.create({
                'product_id': p_starter.id,
                'product_uom_qty': 1,
                'price_unit': 150_000_000.0,
                'discount': 15.0,
            })],
        })
        breaches_stated = so_stated._al2c_threshold_breaches()
        self.assertTrue(
            any("line discount" in r and "exceeds" in r for r in breaches_stated),
            f"15% stated discount must trigger breach, breaches: {breaches_stated}",
        )
