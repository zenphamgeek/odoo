# -*- coding: utf-8 -*-
from datetime import timedelta
from odoo import Command, fields
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import UserError
from .test_al2c import _isolate_dev_db, PHASES


@tagged('post_install', '-at_install', 'insilos_al2c')
class TestGoldenScenarioG1(TransactionCase):
    """
    Golden Scenario G1: SMB ERP Inbound to Cash (AL2C-EVAL-001)
    End-to-End Autonomous Pipeline:
      1. Inbound Lead Capture & Opportunity Enrichment
      2. CPQ Solution Order (ERP-GROWTH, 450M VND) with Deal Desk Guardrail Check
      3. Order Confirmation & Activate Project Instantiation (Prepare..Run)
      4. Phase 1 (Prepare) Milestone Acceptance
      5. Milestone Invoicing with Statutory VAT Classification (Law 48/2024 KCT)
      6. Invoice Posting (Decree 70 E-Invoice Generation readiness)
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        _isolate_dev_db(cls)
        cls.partner = cls.env['res.partner'].create({
            'name': 'Vina Logistics JSC',
            'email': 'contact@vinalogistics.vn',
            'phone': '+84 28 3822 0000',
            'vat': '0312345678',
            'is_company': True,
        })
        cls.sku_growth = cls.env['product.product'].search([('default_code', '=', 'ERP-GROWTH')], limit=1)

    def test_golden_scenario_g1_smb_inbound_to_cash(self):
        # 1. Inbound Lead Capture & Opportunity Enrichment
        lead = self.env['crm.lead'].create({
            'name': 'Vina Logistics - Insilos ERP Growth Inbound',
            'partner_id': self.partner.id,
            'contact_name': 'Nguyen Van A',
            'email_from': 'a.nguyen@vinalogistics.vn',
            'phone': '+84 903 123 456',
            'expected_revenue': 450_000_000,
            'type': 'opportunity',
        })
        self.assertTrue(lead.id)
        self.assertEqual(lead.partner_id, self.partner)

        # 2. CPQ Solution Order (ERP-GROWTH, 450M VND) with Deal Desk Guardrail Check
        so = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'opportunity_id': lead.id,
            'pricelist_id': self.pricelist.id,
            'order_line': [Command.create({
                'product_id': self.sku_growth.id,
                'product_uom_qty': 1,
                'price_unit': self.sku_growth.list_price,
                'discount': 0.0,
            })],
        })
        self.assertEqual(so.state, 'draft')
        self.assertFalse(so.al2c_approval_required, "Standard price with 0% discount requires no deal-desk approval")

        # 3. Order Confirmation & Activate Project Instantiation
        so.action_confirm()
        self.assertEqual(so.state, 'sale')
        line = so.order_line
        project = line.project_id
        self.assertTrue(project, "Confirming ERP-GROWTH instantiated an Activate project")
        self.assertEqual(project.partner_id, self.partner)
        self.assertEqual(len(project.milestone_ids), 5)
        self.assertEqual(project.milestone_ids.sorted('sequence').mapped('name'), PHASES)

        # 4. Phase 1 (Prepare) Milestone Acceptance
        milestone_prepare = project.milestone_ids.sorted('sequence')[0]
        self.assertEqual(milestone_prepare.name, 'Prepare')
        self.assertFalse(milestone_prepare.is_reached)
        self.assertEqual(line.qty_delivered, 0.0)

        # 4. Phase 1 (Prepare) Milestone Acceptance (SOW 15% Weight + Decree 70 Sign-off Token)
        signoff_doc = self.env['documents.document'].create({
            'name': 'ERP_Growth_Phase1_Prepare_Signed_Acceptance.pdf',
            'mimetype': 'application/pdf',
        })
        milestone_prepare.action_register_signoff(signoff_doc.id)
        self.assertTrue(milestone_prepare.is_reached)
        self.assertTrue(milestone_prepare.al2c_billing_eligible)
        self.assertEqual(milestone_prepare.al2c_signoff_document_id, signoff_doc)

        # Milestone reached (weight = 15% / 0.15 under AL2C-INV-101)
        self.assertAlmostEqual(line.qty_delivered, 0.15, places=2)
        self.assertAlmostEqual(line.qty_to_invoice, 0.15, places=2)

        # 5. Milestone Invoicing with Statutory VAT Classification
        invoices = so._create_invoices()
        self.assertEqual(len(invoices), 1)
        inv = invoices[0]
        self.assertEqual(inv.move_type, 'out_invoice')
        inv_line = inv.invoice_line_ids.filtered(lambda l: l.product_id == self.sku_growth)
        self.assertTrue(inv_line)
        self.assertAlmostEqual(inv_line.quantity, 0.15, places=2)
        # Verify statutory VAT classification (KCT Software under Law 48/2024/QH15)
        self.assertEqual(self.sku_growth.al2c_vat_class, 'kct')

        # 6. Post Invoice (Decree 70 E-Invoice Ready)
        inv.action_post()
        self.assertEqual(inv.state, 'posted')
        self.assertTrue(inv.name, "Posted invoice received an official sequential number")


@tagged('post_install', '-at_install', 'insilos_al2c')
class TestGoldenScenarioG2(TransactionCase):
    """
    Golden Scenario G2: Enterprise GRC RFP Solution (AL2C-EVAL-002)
    End-to-End Governance & High-Value CPQ:
      1. High-Value Enterprise Opportunity (750M VND TCV)
      2. Deal-Desk Guardrail Gate (TCV > 500M requires Sales Manager approval)
      3. Contract Clause Deviation Scanner flags customer redline with unlimited liability
      4. General Counsel review & formal approval activity clearance
      5. Order Confirmation & Activate Project instantiation
      6. Delivery Milestone 1 signoff & Decree 70/2025 E-Invoice issuance with CQT code & QR
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        _isolate_dev_db(cls)
        cls.partner = cls.env['res.partner'].create({
            'name': 'Vinacom Enterprise Telecommunications',
            'vat': '0102030405',
            'street': 'Cau Giay, Hanoi',
            'is_company': True,
        })
        cls.manager_user = cls.env['res.users'].create({
            'name': 'Deal Desk Sales Director',
            'login': 'sales_dir_g2',
            'email': 'dir@example.com',
            'group_ids': [(6, 0, [
                cls.env.ref('base.group_user').id,
                cls.env.ref('sales_team.group_sale_manager').id,
                cls.env.ref('project.group_project_manager').id,
                cls.env.ref('sign.group_sign_user').id,
            ])],
        })
        cls.agent_user = cls.env['res.users'].create({
            'name': 'Autonomous CPQ Agent',
            'login': 'agent_cpq_g2',
            'email': 'agent_cpq@example.com',
            'group_ids': [(6, 0, [
                cls.env.ref('base.group_user').id,
                cls.env.ref('insilos_al2c.group_al2c_agent').id,
                cls.env.ref('sign.group_sign_user').id,
            ])],
        })
        cls.sku_ent = cls.env['product.product'].search([('default_code', '=', 'ERP-ENT')], limit=1)

    def test_golden_scenario_g2_enterprise_grc_rfp(self):
        # 1. Opportunity & CPQ Quote creation (750M VND TCV)
        so = self.env['sale.order'].with_user(self.agent_user).create({
            'partner_id': self.partner.id,
            'pricelist_id': self.pricelist.id,
            'order_line': [Command.create({
                'product_id': self.sku_ent.id,
                'product_uom_qty': 1,
                'price_unit': 750_000_000,
            })],
        })
        # 2. Deal-Desk Guardrail Gate (TCV > 500M VND)
        self.assertTrue(so.al2c_approval_required, "TCV 750M VND exceeds 500M threshold")
        self.assertFalse(so.al2c_approved)

        # Autonomous confirmation blocked
        with self.assertRaises(UserError):
            so.with_user(self.agent_user).action_confirm()

        # Sales Manager reviews and approves quote
        so.with_user(self.manager_user).action_approve_deal_desk()
        self.assertTrue(so.al2c_approved)

        # 3. Contract Generation & Clause Deviation Scanner
        sign_template = self.env['sign.template'].create({
            'name': 'Enterprise MSA Template',
        })
        sign_req = self.env['sign.request'].create({
            'reference': 'Vinacom Enterprise Contract',
            'template_id': sign_template.id,
            'message': 'Customer redline: unlimited liability demanded for system downtime.',
        })
        sign_req.action_scan_contract_deviations()
        self.assertTrue(sign_req.al2c_has_deviation)
        self.assertEqual(sign_req.al2c_clause_status, 'deviated')

        # Agent cannot finalize contract while deviated
        with self.assertRaises(UserError):
            sign_req.with_user(self.agent_user).action_sign()

        # 4. General Counsel Approval
        sign_req.with_user(self.manager_user).action_approve_deviations(note="Approved per C-suite exception")
        self.assertEqual(sign_req.al2c_clause_status, 'approved')

        # 5. Order Confirmation & Delivery Project Instantiation
        so.action_confirm()
        self.assertEqual(so.state, 'sale')
        project = so.order_line.project_id
        self.assertTrue(project)

        # 6. Milestone 1 (Prepare - 15%) Sign-off & Decree 70 E-Invoice
        milestone = project.milestone_ids.sorted('sequence')[0]
        signoff = self.env['documents.document'].create({
            'name': 'Vinacom_Phase1_Signed.pdf',
            'mimetype': 'application/pdf',
        })
        milestone.with_user(self.manager_user).action_register_signoff(signoff.id)
        self.assertTrue(milestone.is_reached)

        invoices = so._create_invoices()
        inv = invoices[0]
        inv.action_post()

        # Issue statutory Decree 70/2025 E-Invoice
        inv.action_issue_einvoice()
        self.assertEqual(inv.al2c_einvoice_state, 'issued')
        self.assertTrue(inv.al2c_einvoice_number.startswith('1C26TAA-'))
        self.assertTrue(inv.al2c_einvoice_lookup_code.startswith('00'))
        self.assertIn('https://hoadondientu.gdt.gov.vn/tra-cuu', inv.al2c_einvoice_qr_code)


@tagged('post_install', '-at_install', 'insilos_al2c')
class TestGoldenScenarioG5(TransactionCase):
    """
    Golden Scenario G5: Overdue Invoice, Dunning Suspension & Cash-Matched Commission (AL2C-EVAL-002)
    End-to-End Collections & Finance Hardening:
      1. Customer Alpha Tech has unpaid overdue invoice (D+35 days overdue)
      2. Automated Dunning Ladder triggers 'd30_suspension' stage
      3. Credit Standing Gate blocks new autonomous sales orders for Alpha Tech
      4. Customer settles payment; Dunning resets to 'current'
      5. Cash-Matched Sales Commission triggers payout input for Sales AE
      6. Credit gate clears, allowing new order confirmation
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        _isolate_dev_db(cls)
        cls.partner = cls.env['res.partner'].create({
            'name': 'Alpha Tech Solutions',
            'email': 'finance@alphatech.vn',
            'is_company': True,
        })
        cls.sales_user = cls.env['res.users'].create({
            'name': 'Account Executive G5',
            'login': 'ae_g5',
            'email': 'ae_g5@innoria.com',
            'group_ids': [(6, 0, [
                cls.env.ref('base.group_user').id,
                cls.env.ref('insilos_al2c.group_al2c_agent').id,
            ])],
        })
        cls.employee = cls.env['hr.employee'].create({
            'name': 'Account Executive G5',
            'user_id': cls.sales_user.id,
        })
        cls.sku = cls.env['product.product'].search([('default_code', '=', 'ERP-STARTER')], limit=1)
        cls.pricelist_vnd = cls.env['product.pricelist'].create({
            'name': 'Pricelist VND G5',
            'currency_id': cls.env.ref('base.VND').id,
        })

    def test_golden_scenario_g5_dunning_suspension_and_commission(self):
        today = fields.Date.today()
        overdue_due_date = today - timedelta(days=35)

        # 1. Delinquent Invoice
        inv = self.env['account.move'].create({
            'partner_id': self.partner.id,
            'currency_id': self.env.ref('base.VND').id,
            'move_type': 'out_invoice',
            'invoice_date': overdue_due_date,
            'invoice_date_due': overdue_due_date,
            'invoice_user_id': self.sales_user.id,
            'invoice_line_ids': [Command.create({
                'product_id': self.sku.id,
                'quantity': 1,
                'price_unit': 120_000_000,
            })],
        })
        inv.action_post()

        # 2. Automated Dunning Ladder transition
        inv._al2c_update_dunning_stage(as_of_date=today)
        self.assertEqual(inv.al2c_dunning_stage, 'd30_suspension')

        # 3. Autonomous Credit Standing Gate
        new_so = self.env['sale.order'].with_user(self.sales_user).create({
            'partner_id': self.partner.id,
            'pricelist_id': self.pricelist_vnd.id,
            'order_line': [Command.create({
                'product_id': self.sku.id,
                'product_uom_qty': 1,
                'price_unit': self.sku.list_price,
            })],
        })
        # Confirmation strictly blocked by credit gate
        with self.assertRaises(UserError) as cm:
            new_so.action_confirm()
        self.assertIn("overdue by > 30 days", str(cm.exception))

        # 4. Customer settles cash / payment reconciliation
        # Simulate payment reconciliation
        inv.write({'payment_state': 'paid'})
        inv._al2c_update_dunning_stage(as_of_date=today)
        self.assertEqual(inv.al2c_dunning_stage, 'current', "Paid invoice resets dunning stage to current")

        # 5. Cash-Matched Commission Processing
        inv.action_process_cash_matched_commission()
        ledger_entries = self.env['al2c.commission.ledger'].search([('invoice_id', '=', inv.id)])
        self.assertEqual(len(ledger_entries), 1)
        entry = ledger_entries[0]
        self.assertEqual(entry.employee_id, self.employee)
        # 5% of 120M = 6,000,000 VND
        self.assertEqual(entry.amount, 6_000_000)

        # 6. Credit Gate clears: Sales Order now confirms cleanly!
        new_so.action_confirm()
        self.assertEqual(new_so.state, 'sale')


@tagged('post_install', '-at_install', 'insilos_al2c')
class TestGoldenScenarioG3(TransactionCase):
    """
    Golden Scenario G3: AI PoC -> Production Rollout Expansion (AL2C-EVAL-003)
    Lifecycle:
      1. Prospect purchases AI-POC (Proof of Concept)
      2. Project created with billable milestones
      3. PoC milestone sign-off completed and billed
      4. Autonomous expansion: Draft AI-PROD quote created crediting PoC investment
      5. AI-PROD confirmed, instantiating production rollout project
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Hanoi Smart FinTech JSC',
            'email': 'cto@hanoismartfintech.vn',
        })
        cls.sku_poc = cls.env['product.product'].search([('default_code', '=', 'AI-POC')], limit=1)
        cls.sku_prod = cls.env['product.product'].search([('default_code', '=', 'AI-PROD')], limit=1)
        cls.pricelist = cls.env['product.pricelist'].search([('currency_id.name', '=', 'VND')], limit=1)
        if not cls.pricelist:
            cls.pricelist = cls.env['product.pricelist'].create({
                'name': 'VND Standard',
                'currency_id': cls.env.ref('base.VND').id,
            })

    def test_golden_scenario_g3_ai_poc_to_production_rollout(self):
        # 1. PoC Order Creation & Confirmation
        so_poc = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'pricelist_id': self.pricelist.id,
            'order_line': [Command.create({
                'product_id': self.sku_poc.id,
                'product_uom_qty': 1,
                'price_unit': self.sku_poc.list_price,
            })],
        })
        so_poc.action_confirm()
        self.assertEqual(so_poc.state, 'sale')
        poc_project = so_poc.order_line.project_id
        self.assertTrue(poc_project, "PoC project must be instantiated from template")

        # 2. PoC Milestone Sign-Off & Billing
        milestone = poc_project.milestone_ids.sorted('sequence')[0]
        signoff = self.env['documents.document'].create({
            'name': 'HanoiFinTech_PoC_Acceptance.pdf',
            'mimetype': 'application/pdf',
        })
        milestone.action_register_signoff(signoff.id)
        self.assertTrue(milestone.is_reached)
        self.assertTrue(milestone.al2c_billing_eligible)

        invoices = so_poc._create_invoices()
        self.assertTrue(invoices)
        invoices.action_post()

        # 3. Autonomous Expansion to Production Rollout
        # Create AI-PROD quote crediting the PoC fee
        poc_credit = self.sku_poc.list_price
        so_prod = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'pricelist_id': self.pricelist.id,
            'order_line': [
                Command.create({
                    'product_id': self.sku_prod.id,
                    'product_uom_qty': 1,
                    'price_unit': self.sku_prod.list_price,
                }),
                Command.create({
                    'name': 'PoC Investment Credit applied to Production Rollout',
                    'product_id': self.sku_poc.id,
                    'product_uom_qty': 1,
                    'price_unit': -poc_credit,
                }),
            ],
        })
        # Verify credit applied
        expected_total = self.sku_prod.list_price - poc_credit
        self.assertAlmostEqual(so_prod.amount_untaxed, expected_total, delta=1.0)

        # Confirm production order
        so_prod.al2c_approved = True
        so_prod.action_confirm()
        self.assertEqual(so_prod.state, 'sale')
        prod_project = so_prod.order_line.filtered(lambda l: l.product_id == self.sku_prod).project_id
        self.assertTrue(prod_project, "Production rollout project instantiated from template")


@tagged('post_install', '-at_install', 'insilos_al2c')
class TestGoldenScenarioG4(TransactionCase):
    """
    Golden Scenario G4: Self-Serve Mojo App Subscription & Prepaid Token Burn-Down (AL2C-EVAL-003)
    Lifecycle:
      1. Customer orders MOJO-APP-SUB + MOJO-TOKENS
      2. Subscription activated & token credit applied to partner account
      3. Pod reports usage records via idempotent record_usage API
      4. Duplicated requests handled idempotently
      5. 80% usage threshold crossed -> Automated Sentinel alert & top-up activity
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Nexus AI Autonomous Logistics',
            'email': 'billing@nexusai.vn',
        })
        cls.sku_sub = cls.env['product.product'].search([('default_code', '=', 'MOJO-APP-SUB')], limit=1)
        cls.sku_tokens = cls.env['product.product'].search([('default_code', '=', 'MOJO-TOKENS')], limit=1)
        cls.pricelist = cls.env['product.pricelist'].search([('currency_id.name', '=', 'VND')], limit=1)
        if not cls.pricelist:
            cls.pricelist = cls.env['product.pricelist'].create({
                'name': 'VND Standard',
                'currency_id': cls.env.ref('base.VND').id,
            })

    def test_golden_scenario_g4_mojo_subscription_and_token_burn(self):
        # 1. Order Creation & Confirmation
        plan = self.env['sale.subscription.plan'].search([], limit=1)
        so = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'pricelist_id': self.pricelist.id,
            'plan_id': plan.id if plan else False,
            'order_line': [
                Command.create({
                    'product_id': self.sku_sub.id,
                    'product_uom_qty': 1,
                    'price_unit': self.sku_sub.list_price,
                }),
                Command.create({
                    'product_id': self.sku_tokens.id,
                    'product_uom_qty': 1,
                    'price_unit': self.sku_tokens.list_price,
                }),
            ],
        })
        so.al2c_approved = True
        so.action_confirm()
        self.assertEqual(so.state, 'sale')

        # 2. Token credit initialized (10,000,000 tokens pack)
        self.partner.action_topup_tokens(10_000_000.0)
        self.assertEqual(self.partner.al2c_mojo_token_balance, 10_000_000.0)

        # 3. Pod usage consumption & idempotency
        idempotency_key = "POD-RUN-BATCH-001"
        rec1 = self.env['al2c.mojo.usage.ledger'].record_usage(
            partner_id=self.partner.id,
            quantity=3_000_000.0,
            meter_type='tokens',
            idempotency_key=idempotency_key,
            subscription_id=so.id,
        )
        self.assertEqual(self.partner.al2c_mojo_token_balance, 7_000_000.0)

        # Duplicate delivery must be idempotent
        rec2 = self.env['al2c.mojo.usage.ledger'].record_usage(
            partner_id=self.partner.id,
            quantity=3_000_000.0,
            meter_type='tokens',
            idempotency_key=idempotency_key,
            subscription_id=so.id,
        )
        self.assertEqual(rec1.id, rec2.id)
        self.assertEqual(self.partner.al2c_mojo_token_balance, 7_000_000.0)

        # 4. Burn down crosses 80% threshold (additional 5.5M consumed -> 8.5M total = 85%)
        self.env['al2c.mojo.usage.ledger'].record_usage(
            partner_id=self.partner.id,
            quantity=5_500_000.0,
            meter_type='tokens',
            idempotency_key="POD-RUN-BATCH-002",
            subscription_id=so.id,
        )
        self.assertEqual(self.partner.al2c_mojo_token_balance, 1_500_000.0)
        self.assertTrue(self.partner.al2c_mojo_alert_80_sent)

        # 5. Top-up activity verified
        activities = self.partner.activity_ids
        if not activities:
            activities = self.env['mail.activity'].search([
                ('res_model', 'in', ('res.partner', 'party.master')),
                ('res_id', '=', self.partner.id),
            ])
        self.assertTrue(activities, "Top-up proposal activity must be active.")

