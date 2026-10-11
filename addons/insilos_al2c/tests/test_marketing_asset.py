# -*- coding: utf-8 -*-
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install', 'insilos_al2c')
class TestAl2cMarketingAssetKit(TransactionCase):
    """
    Test suite for AL2C-MKT-403: Automated Asset Kit Generation with 100% Claim Atom Grounding.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env['product.template'].search([('default_code', '=', 'ERP-STARTER')], limit=1)
        cls.article = cls.env['knowledge.article'].search([('name', 'ilike', 'Products')], limit=1)

        # Create verified claim atom
        cls.verified_atom = cls.env['al2c.claim.atom'].create({
            'name': 'ERP Starter 4-Week Activation Claim',
            'sku_id': cls.product.id,
            'claim_text': 'Delivers core accounting and inventory operational readiness in under 4 weeks.',
            'source_article_id': cls.article.id if cls.article else False,
            'verification_state': 'verified',
        })

    def test_marketing_kit_generation_with_verified_claim(self):
        """Marketing kit generates one-pager, battlecard, social posts, and nurture series when grounded in verified claims."""
        kit = self.env['al2c.marketing.kit'].create({
            'name': 'ERP Starter Campaign Kit Q1',
            'product_template_id': self.product.id,
            'claim_atom_ids': [(6, 0, [self.verified_atom.id])],
        })
        self.assertEqual(kit.state, 'draft')
        self.assertFalse(kit.grounding_verified)

        kit.action_generate_asset_kit()

        self.assertEqual(kit.state, 'generated')
        self.assertTrue(kit.grounding_verified)
        self.assertIn("Executive Solution Brief", kit.one_pager_content)
        self.assertIn("Competitive Battlecard", kit.battlecard_content)
        self.assertIn("Post 1 (Executive Angle)", kit.social_posts_content)
        self.assertIn("Touch 1 (Day 1 - Problem Recognition)", kit.nurture_journey_content)
        self.assertIn(self.verified_atom.claim_text, kit.one_pager_content)

    def test_unverified_claim_blocks_kit_generation(self):
        """Unverified claim atom strictly blocks marketing kit generation (AL2C-MKT-402 grounding gate)."""
        unverified_atom = self.env['al2c.claim.atom'].create({
            'name': 'Unverified 99% AI Claim',
            'sku_id': self.product.id,
            'claim_text': 'Guarantees 99% reduction in enterprise operating costs within 48 hours.',
            'source_article_id': self.article.id if self.article else False,
            'verification_state': 'draft',
        })
        kit = self.env['al2c.marketing.kit'].create({
            'name': 'ERP Starter Aggressive Campaign Kit',
            'product_template_id': self.product.id,
            'claim_atom_ids': [(6, 0, [unverified_atom.id])],
        })

        with self.assertRaises(UserError):
            kit.action_generate_asset_kit()
