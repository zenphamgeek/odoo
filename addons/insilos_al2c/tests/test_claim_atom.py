# -*- coding: utf-8 -*-
from odoo import Command
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import TransactionCase, tagged
from .test_al2c import _isolate_dev_db


@tagged('post_install', '-at_install', 'insilos_al2c')
class TestAl2cClaimAtom(TransactionCase):
    """
    Tests for AL2C-MKT-402: Claim Atom Data Model & Semantic Entailment Guard.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        _isolate_dev_db(cls)
        cls.manager_group = cls.env.ref('sales_team.group_sale_manager')
        cls.user_salesman = cls.env['res.users'].create({
            'name': 'Content Author Rep',
            'login': 'author_rep',
            'email': 'author.rep@example.com',
            'group_ids': [Command.set([cls.env.ref('base.group_user').id])],
        })
        cls.user_manager = cls.env['res.users'].create({
            'name': 'PMM Lead',
            'login': 'pmm_lead',
            'email': 'pmm.lead@example.com',
            'group_ids': [Command.set([cls.env.ref('base.group_user').id, cls.manager_group.id])],
        })
        cls.kb_starter = cls.env.ref('insilos_al2c.kb_sku_erp_starter')
        cls.sku_starter = cls.env.ref('insilos_al2c.product_erp_starter')

    def test_claim_atom_lifecycle_and_entailment_gate(self):
        # 1. Create a draft claim atom
        atom = self.env['al2c.claim.atom'].create({
            'name': 'ERP Starter Postgres Isolation',
            'claim_text': 'Insilos ERP Starter deploys with strict tenant schema isolation on PostgreSQL 17.',
            'claim_type': 'feature',
            'sku_id': self.sku_starter.id,
            'source_article_id': self.kb_starter.id,
        })
        self.assertTrue(atom.claim_hash)
        self.assertEqual(len(atom.claim_hash), 64, "Claim hash must be a valid SHA-256 hexadecimal string")
        self.assertEqual(atom.verification_state, 'draft')

        # 2. An unverified atom does not pass external marketing entailment check
        with self.assertRaises(ValidationError):
            self.env['al2c.claim.atom'].verify_marketing_assertion(
                'Insilos ERP Starter deploys with strict tenant schema isolation on PostgreSQL 17.'
            )

        # 3. Non-manager cannot verify the atom
        with self.assertRaises(AccessError):
            atom.with_user(self.user_salesman).action_verify()

        # 4. Manager verifies the atom
        atom.with_user(self.user_manager).action_verify()
        self.assertEqual(atom.verification_state, 'verified')
        self.assertEqual(atom.verified_by_uid, self.user_manager)

        # 5. Verified statement now passes entailment verification
        matched_atom = self.env['al2c.claim.atom'].verify_marketing_assertion(
            'Insilos ERP Starter deploys with strict tenant schema isolation on PostgreSQL 17.'
        )
        self.assertEqual(matched_atom, atom)

        # 6. Hallucinated / unbacked claim is blocked
        with self.assertRaises(ValidationError):
            self.env['al2c.claim.atom'].verify_marketing_assertion(
                'Insilos guarantees free unlimited on-site 24/7 consulting with zero latency worldwide.'
            )

    def test_claim_hash_unique_constraint_physical_assertion(self):
        """Assert unique constraint/index physically exists on al2c_claim_atom.claim_hash in PostgreSQL."""
        self.env.cr.execute("""
            SELECT 1 FROM pg_constraint
            WHERE conrelid = 'al2c_claim_atom'::regclass
              AND conname LIKE '%claim_hash_uniq%'
              AND contype = 'u'
        """)
        self.assertTrue(self.env.cr.fetchone(), "Physical unique constraint 'claim_hash_uniq' missing on al2c_claim_atom")

        self.env.cr.execute("""
            SELECT 1 FROM pg_index i
            JOIN pg_class c ON c.oid = i.indexrelid
            JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
            WHERE i.indrelid = 'al2c_claim_atom'::regclass
              AND a.attname = 'claim_hash'
              AND i.indisunique = true
        """)
        self.assertTrue(self.env.cr.fetchone(), "Physical unique index on claim_hash missing on al2c_claim_atom")
