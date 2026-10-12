# -*- coding: utf-8 -*-
from datetime import date, timedelta
from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import AccessError, UserError
from odoo import Command


@tagged('post_install', '-at_install', 'insilos_al2c', 'security', 'audit')
class TestSecurityAuditDeep(TransactionCase):
    """
    Comprehensive Enterprise Security & Compliance Audit Test Suite (AL2C-SEC-AUDIT):
    1. Segregation of Duties (SoD) enforcement on quotations & Guardrails 1 & 2.
    2. Dispute status tampering prevention & dunning freeze integrity.
    3. IDOR prevention across customer portal identities & multi-tenant boundaries.
    4. Residual brand leakage audit (Zero-Signature Insilos / Innoria compliance).
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.currency_vnd = cls.env.ref('base.VND', raise_if_not_found=False) or cls.company.currency_id

        # Security Groups
        cls.group_portal = cls.env.ref('base.group_portal')
        cls.group_internal = cls.env.ref('base.group_user')
        cls.group_agent = cls.env.ref('insilos_al2c.group_al2c_agent')
        cls.group_salesman = cls.env.ref('sales_team.group_sale_salesman')
        cls.group_sale_manager = cls.env.ref('sales_team.group_sale_manager')
        cls.group_account_manager = cls.env.ref('account.group_account_manager')

        # Test Partners (Tenant separation)
        cls.partner_a = cls.env['res.partner'].create({
            'name': 'Alpha Enterprise Solutions Corp',
            'is_company': True,
            'email': 'procurement@alpha-enterprise.vn',
        })
        cls.partner_b = cls.env['res.partner'].create({
            'name': 'Beta Logistics Global JSC',
            'is_company': True,
            'email': 'billing@beta-logistics.vn',
        })

        # Test Users
        cls.portal_user_a = cls.env['res.users'].create({
            'name': 'Customer Portal Alpha User',
            'login': 'portal_alpha_auditor',
            'email': 'portal_alpha@example.com',
            'partner_id': cls.partner_a.id,
            'group_ids': [(6, 0, [cls.group_portal.id])],
        })

        cls.portal_user_b = cls.env['res.users'].create({
            'name': 'Customer Portal Beta User',
            'login': 'portal_beta_auditor',
            'email': 'portal_beta@example.com',
            'partner_id': cls.partner_b.id,
            'group_ids': [(6, 0, [cls.group_portal.id])],
        })

        cls.salesman_user = cls.env['res.users'].create({
            'name': 'Regular Sales Representative',
            'login': 'salesman_auditor',
            'email': 'salesman@example.com',
            'group_ids': [(6, 0, [cls.group_internal.id, cls.group_salesman.id])],
        })

        cls.agent_user = cls.env['res.users'].create({
            'name': 'Autonomous CPQ Agent Bot',
            'login': 'agent_cpq_auditor',
            'email': 'agent_cpq@example.com',
            'group_ids': [(6, 0, [cls.group_internal.id, cls.group_agent.id, cls.group_salesman.id])],
        })

        cls.sales_manager = cls.env['res.users'].create({
            'name': 'Enterprise Sales Director',
            'login': 'sales_director_auditor',
            'email': 'sales_director@example.com',
            'group_ids': [(6, 0, [cls.group_internal.id, cls.group_sale_manager.id])],
        })

        cls.billing_manager = cls.env['res.users'].create({
            'name': 'Head of Billing & Receivables',
            'login': 'billing_head_auditor',
            'email': 'billing_head@example.com',
            'group_ids': [(6, 0, [cls.group_internal.id, cls.group_account_manager.id])],
        })

        cls.public_user = cls.env.ref('base.public_user')

        # Test SKU
        cls.product = cls.env['product.product'].search([('sale_ok', '=', True), ('list_price', '>', 0)], limit=1)
        if not cls.product:
            cls.product = cls.env['product.product'].create({
                'name': 'Enterprise Platform Standard License',
                'list_price': 100_000_000.0,
                'sale_ok': True,
            })

        # Ensure parameters are calibrated for testing
        cls.env['ir.config_parameter'].sudo().set_param('al2c.autonomy_enabled', 'True')
        cls.env['ir.config_parameter'].sudo().set_param('al2c.max_discount', '10.0')
        cls.env['ir.config_parameter'].sudo().set_param('al2c.max_tcv', '500000000')

        # Ensure mail templates reflect AL2C customizations
        imd = cls.env['ir.model.data'].sudo()
        data_records = imd.search([('module', 'in', ['sale', 'account']), ('name', 'in', ['email_template_edi_sale', 'email_template_edi_invoice'])])
        if data_records:
            data_records.write({'noupdate': False})

        tpl_sale = cls.env.ref('sale.email_template_edi_sale', raise_if_not_found=False)
        if tpl_sale and 'innoria' not in (tpl_sale.body_html or '').lower():
            from odoo.tools.convert import convert_file
            convert_file(cls.env, 'insilos_al2c', 'views/mail_templates.xml', {}, 'update', False)

    # =========================================================================
    # SUITE 1: SEGREGATION OF DUTIES (SoD) & GUARDRAIL BYPASS ATTEMPTS
    # =========================================================================
    def test_sod_bypass_attempts(self):
        """
        Verify that autonomous agents and regular salesmen cannot bypass Deal Desk
        guardrails (Guardrail 1: Discount > 10%, Guardrail 2: Total TCV > 500M VND),
        cannot self-approve, and cannot circumvent re-approval sentinels.
        """
        SaleOrder = self.env['sale.order']

        # 1. Guardrail 1: Autonomous Agent creates order with 25% discount (> 10% ceiling)
        so_discount = SaleOrder.with_user(self.agent_user).create({
            'partner_id': self.partner_a.id,
            'user_id': self.agent_user.id,
            'order_line': [Command.create({
                'product_id': self.product.id,
                'product_uom_qty': 1,
                'price_unit': self.product.list_price,
                'discount': 25.0,
            })],
        })
        self.assertTrue(so_discount.al2c_approval_required, "Quotation with 25% discount must require Deal Desk approval.")

        # Attempt to confirm directly raises approval block
        with self.assertRaises(UserError) as cm:
            so_discount.with_user(self.agent_user).action_confirm()
        self.assertIn("deal-desk approval", str(cm.exception).lower())

        # Attempt self-approval via write
        with self.assertRaises(AccessError):
            so_discount.with_user(self.agent_user).write({'al2c_approved': True})

        # Attempt self-approval via button action
        with self.assertRaises(AccessError):
            so_discount.with_user(self.agent_user).action_approve_deal_desk()

        # Attempt self-approval during creation
        with self.assertRaises(AccessError):
            SaleOrder.with_user(self.agent_user).create({
                'partner_id': self.partner_a.id,
                'al2c_approved': True,
                'order_line': [Command.create({
                    'product_id': self.product.id,
                    'product_uom_qty': 1,
                    'price_unit': self.product.list_price,
                })],
            })

        # Regular human salesman cannot self-approve either
        with self.assertRaises(AccessError):
            so_discount.with_user(self.salesman_user).write({'al2c_approved': True})
        with self.assertRaises(AccessError):
            so_discount.with_user(self.salesman_user).action_approve_deal_desk()

        # Legitimate approval by Enterprise Sales Director
        so_discount.with_user(self.sales_manager).action_approve_deal_desk()
        self.assertTrue(so_discount.al2c_approved)

        # Agent can now confirm the approved quotation
        so_discount.with_user(self.agent_user).action_confirm()
        self.assertEqual(so_discount.state, 'sale')

        # 2. Guardrail 2: Autonomous Agent creates order with TCV > 500,000,000 VND
        so_tcv = SaleOrder.with_user(self.agent_user).create({
            'partner_id': self.partner_a.id,
            'user_id': self.agent_user.id,
            'order_line': [Command.create({
                'product_id': self.product.id,
                'product_uom_qty': 1,
                'price_unit': 600_000_000.0,
                'discount': 0.0,
            })],
        })
        self.assertTrue(so_tcv.al2c_approval_required, "Quotation with TCV 600M VND must require Deal Desk approval.")
        with self.assertRaises(UserError):
            so_tcv.with_user(self.agent_user).action_confirm()

        # 3. Re-Approval Sentinel: Tampering with approved order lines resets approval
        so_tamper = SaleOrder.with_user(self.agent_user).create({
            'partner_id': self.partner_a.id,
            'user_id': self.agent_user.id,
            'order_line': [Command.create({
                'product_id': self.product.id,
                'product_uom_qty': 1,
                'price_unit': 100_000_000.0,
                'discount': 0.0,
            })],
        })
        # Manager approves
        so_tamper.with_user(self.sales_manager).action_approve_deal_desk()
        self.assertTrue(so_tamper.al2c_approved)

        # Agent tampers with line discount directly via sale.order.line
        so_tamper.order_line.with_user(self.agent_user).write({'discount': 40.0})
        self.assertFalse(so_tamper.al2c_approved, "Tampering with line discount must automatically revoke Deal Desk approval.")
        with self.assertRaises(UserError):
            so_tamper.with_user(self.agent_user).action_confirm()

        # 4. Method-Level Deny-List (AL2C-GOV-204)
        guard = self.env['al2c.autonomy.guard'].with_user(self.agent_user)
        with self.assertRaises(AccessError):
            guard._al2c_check_method_allowed('account.move', 'button_draft')
        with self.assertRaises(AccessError):
            guard._al2c_check_method_allowed('account.move', 'action_cancel_einvoice')
        with self.assertRaises(AccessError):
            guard._al2c_check_method_allowed('hr.payslip', 'action_payslip_done')
        with self.assertRaises(AccessError):
            guard._al2c_check_method_allowed('sale.order', 'action_approve_deal_desk')
        with self.assertRaises(AccessError):
            guard._al2c_check_method_allowed('al2c.dispute', 'action_resolve_dispute')

    # =========================================================================
    # SUITE 2: DISPUTE TAMPERING & UNAUTHORIZED DUNNING UNFREEZING
    # =========================================================================
    def test_dispute_status_tampering_and_unfreezing(self):
        """
        Verify that commercial disputes freeze the automated dunning ladder,
        and that portal users, non-managers, and autonomous agents cannot
        arbitrarily resolve disputes or lift dunning freezes.
        """
        Move = self.env['account.move']
        Dispute = self.env['al2c.dispute']

        past_due = date.today() - timedelta(days=35)
        invoice = Move.create({
            'partner_id': self.partner_b.id,
            'move_type': 'out_invoice',
            'invoice_date': past_due,
            'invoice_date_due': past_due,
            'invoice_line_ids': [Command.create({
                'name': 'Cloud ERP Platform Subscription',
                'quantity': 1,
                'price_unit': 80_000_000.0,
            })],
        })
        invoice.action_post()

        # Trigger dunning progression to d30_suspension
        invoice._al2c_update_dunning_stage()
        self.assertEqual(invoice.al2c_dunning_stage, 'd30_suspension')

        # Reset stage to current and open commercial dispute
        invoice.write({'al2c_dunning_stage': 'current'})
        dispute = Dispute.create({
            'invoice_id': invoice.id,
            'reason': 'rate_mismatch',
            'disputed_amount': 80_000_000.0,
        })
        self.assertEqual(dispute.state, 'open')
        self.assertTrue(invoice.al2c_has_open_dispute, "Invoice must register active open dispute.")

        # Dunning ladder is frozen: updates do not advance beyond 'current'
        invoice._al2c_update_dunning_stage()
        self.assertEqual(invoice.al2c_dunning_stage, 'current', "Dunning ladder must remain frozen while dispute is open.")

        # Attempt 1: Customer Portal user tries to resolve dispute
        with self.assertRaises(AccessError):
            dispute.with_user(self.portal_user_b).action_resolve_dispute()
        with self.assertRaises(AccessError):
            dispute.with_user(self.portal_user_b).action_cancel_dispute()
        with self.assertRaises(AccessError):
            dispute.with_user(self.portal_user_b).write({'state': 'resolved'})

        # Attempt 2: Regular Salesman (non-manager) tries to resolve dispute
        with self.assertRaises(AccessError):
            dispute.with_user(self.salesman_user).action_resolve_dispute()
        with self.assertRaises(AccessError):
            dispute.with_user(self.salesman_user).action_cancel_dispute()
        with self.assertRaises(AccessError):
            dispute.with_user(self.salesman_user).write({'state': 'resolved'})

        # Attempt 3: Autonomous Agent tries to resolve dispute
        with self.assertRaises(AccessError):
            dispute.with_user(self.agent_user).action_resolve_dispute()
        with self.assertRaises(AccessError):
            dispute.with_user(self.agent_user).action_cancel_dispute()
        with self.assertRaises(AccessError):
            dispute.with_user(self.agent_user).write({'state': 'resolved'})

        # Verify dispute is still open and dunning still frozen
        self.assertEqual(dispute.state, 'open')
        self.assertTrue(invoice.al2c_has_open_dispute)

        # Legitimate resolution by Head of Billing & Receivables (account.group_account_manager)
        dispute.with_user(self.billing_manager).action_resolve_dispute("Credit note adjustment agreed with client.")
        self.assertEqual(dispute.state, 'resolved')
        self.assertFalse(invoice.al2c_has_open_dispute, "Dunning freeze must be lifted upon authorized resolution.")

        # Dunning ladder can now resume normal operations
        invoice._al2c_update_dunning_stage()
        self.assertEqual(invoice.al2c_dunning_stage, 'd30_suspension')

    # =========================================================================
    # SUITE 3: IDOR PREVENTION ACROSS CUSTOMER PORTAL USERS
    # =========================================================================
    def test_idor_prevention_portal_users(self):
        """
        Verify IDOR immunity: Customer Portal User A cannot read or modify
        records belonging to Customer B (Sale Orders, Invoices, Disputes, Value Cases, FTS Items).
        Public and portal users cannot access confidential architecture or pricing models.
        """
        SaleOrder = self.env['sale.order']
        Move = self.env['account.move']
        ValueCase = self.env['al2c.value.case']
        FtsItem = self.env['al2c.fts.item']
        Dispute = self.env['al2c.dispute']

        # Create confidential records belonging to Customer B
        so_b = SaleOrder.create({
            'partner_id': self.partner_b.id,
            'order_line': [Command.create({
                'product_id': self.product.id,
                'product_uom_qty': 2,
                'price_unit': self.product.list_price,
            })],
        })

        invoice_b = Move.create({
            'partner_id': self.partner_b.id,
            'move_type': 'out_invoice',
            'invoice_date': date.today(),
            'invoice_line_ids': [Command.create({
                'name': 'Logistics Optimization Module',
                'quantity': 1,
                'price_unit': 120_000_000.0,
            })],
        })
        invoice_b.action_post()

        case_b = ValueCase.create({
            'name': 'Beta Logistics 3-Year TCO & ROI Value Case',
            'partner_id': self.partner_b.id,
            'tco_current_vnd': 900_000_000.0,
            'tco_future_vnd': 350_000_000.0,
        })

        fts_b = FtsItem.create({
            'name': 'Core WMS API Decoupled Connector',
            'sale_order_id': so_b.id,
            'clean_core_class': 'class_c',
            'description': 'Proprietary architectural integration blueprint.',
        })

        dispute_b = Dispute.create({
            'invoice_id': invoice_b.id,
            'reason': 'timesheet_billing',
            'disputed_amount': 40_000_000.0,
        })

        # IDOR 1: Portal User A attempts to read Customer B's Sale Order
        with self.assertRaises(AccessError):
            so_b.with_user(self.portal_user_a).read(['name', 'amount_total'])

        # IDOR 2: Portal User A attempts to read Customer B's Invoice
        with self.assertRaises(AccessError):
            invoice_b.with_user(self.portal_user_a).read(['name', 'amount_total'])

        # IDOR 3: Portal User A attempts to read Customer B's Dispute
        with self.assertRaises(AccessError):
            dispute_b.with_user(self.portal_user_a).read(['name', 'disputed_amount'])

        # IDOR 4: Portal Users (both A and B) cannot access internal Value Cases
        with self.assertRaises(AccessError):
            case_b.with_user(self.portal_user_a).read(['name', 'roi_percentage'])
        with self.assertRaises(AccessError):
            case_b.with_user(self.portal_user_b).read(['name', 'roi_percentage'])
        with self.assertRaises(AccessError):
            ValueCase.with_user(self.portal_user_a).create({
                'name': 'Rogue Value Case',
                'partner_id': self.partner_a.id,
            })

        # IDOR 5: Portal Users cannot access Fit-to-Standard Clean Core items
        with self.assertRaises(AccessError):
            fts_b.with_user(self.portal_user_a).read(['name', 'clean_core_class'])
        with self.assertRaises(AccessError):
            fts_b.with_user(self.portal_user_b).read(['name', 'clean_core_class'])
        with self.assertRaises(AccessError):
            FtsItem.with_user(self.portal_user_a).create({
                'name': 'Rogue Scope Item',
                'sale_order_id': so_b.id,
            })

        # IDOR 6: Public / Anonymous users cannot access Value Cases or FTS items
        with self.assertRaises(AccessError):
            case_b.with_user(self.public_user).read(['name'])
        with self.assertRaises(AccessError):
            fts_b.with_user(self.public_user).read(['name'])

    # =========================================================================
    # SUITE 4: ZERO RESIDUAL BRANDING & COMPLIANCE SIGNATURE AUDIT
    # =========================================================================
    def test_zero_residual_branding_strings(self):
        """
        Verify that all user-facing email and report templates have ZERO residual
        'Odoo' or 'OpenERP' strings in rendered content or headers/footers, and
        strictly adhere to Insilos / Innoria enterprise standards with ISO 27001
        and Decree 13/2023 / Decree 70/2025 statutory markers.
        """
        # 1. Quotation Email Template
        template_sale = self.env.ref('sale.email_template_edi_sale', raise_if_not_found=False)
        self.assertIsNotNone(template_sale, "sale.email_template_edi_sale must exist.")
        sale_html = template_sale.body_html or ""
        self.assertNotIn("odoo", sale_html.lower(), "sale.email_template_edi_sale must not contain residual 'Odoo' references.")
        self.assertNotIn("openerp", sale_html.lower(), "sale.email_template_edi_sale must not contain residual 'OpenERP' references.")
        self.assertIn("innoria", sale_html.lower(), "sale.email_template_edi_sale must contain official Innoria branding.")

        # 2. Invoice Email Template
        template_inv = self.env.ref('account.email_template_edi_invoice', raise_if_not_found=False)
        self.assertIsNotNone(template_inv, "account.email_template_edi_invoice must exist.")
        inv_html = template_inv.body_html or ""
        self.assertNotIn("odoo", inv_html.lower(), "account.email_template_edi_invoice must not contain residual 'Odoo' references.")
        self.assertNotIn("openerp", inv_html.lower(), "account.email_template_edi_invoice must not contain residual 'OpenERP' references.")
        self.assertIn("innoria", inv_html.lower(), "account.email_template_edi_invoice must contain official Innoria branding.")

        # 3. Notification Layouts
        layout_main = self.env.ref('insilos_al2c.mail_notification_layout_inherit_al2c', raise_if_not_found=False)
        self.assertIsNotNone(layout_main, "mail_notification_layout_inherit_al2c must be defined.")
        layout_arch = layout_main.arch_db or ""
        self.assertIn("ISO/IEC 27001", layout_arch, "Notification layout must display ISO/IEC 27001 certification marker.")
        self.assertIn("13/2023/NĐ-CP", layout_arch, "Notification layout must display Decree 13/2023 statutory marker.")

        # 4. External Report Layouts
        report_layout = self.env.ref('insilos_al2c.external_layout_ibm_sap', raise_if_not_found=False)
        self.assertIsNotNone(report_layout, "external_layout_ibm_sap must be defined.")
        report_arch = report_layout.arch_db or ""
        self.assertNotIn("odoo", report_arch.lower(), "Report layout must not contain residual 'Odoo' branding.")
        self.assertNotIn("openerp", report_arch.lower(), "Report layout must not contain residual 'OpenERP' branding.")
        self.assertIn("INNORIA ENTERPRISE PLATFORM", report_arch)
        self.assertIn("70/2025/NĐ-CP", report_arch, "Report layout must reference statutory e-invoicing Decree 70/2025.")

    # =========================================================================
    # MASTER AUDIT DISPATCHER METHOD
    # =========================================================================
    def test_security_audit_deep(self):
        """
        Master Deep Security Audit Entrypoint.
        Executes all sub-suites sequentially to ensure 100% compliance gate pass.
        """
        self.test_sod_bypass_attempts()
        self.test_dispute_status_tampering_and_unfreezing()
        self.test_idor_prevention_portal_users()
        self.test_zero_residual_branding_strings()
