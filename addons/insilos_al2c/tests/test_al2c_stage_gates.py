# -*- coding: utf-8 -*-
from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged, new_test_user
from .test_al2c import _isolate_dev_db, PHASES


@tagged('post_install', '-at_install', 'insilos_al2c')
class TestAl2cStageGates(TransactionCase):
    """
    R4 Project Governance Test Suite:
    1. Sequential SAP Activate stage gate progression (Prepare -> Explore -> Realize -> Deploy -> Run)
       requiring formal milestone verification before subsequent stage gates can be approved.
    2. Milestone billing gated by al2c_billing_eligible (signed customer signoff document).
       _create_invoices() blocks billing until prerequisite stage deliverables are approved.
    3. Real-time task budget burn warnings when timesheet hours cross 85% of allocated hours.
    4. Segregation of Duties (SoD): block autonomous agent users (group_al2c_agent) from calling
       action_register_signoff; restrict milestone alterations to Project Managers.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        _isolate_dev_db(cls)

        # Users
        cls.pm_user = new_test_user(
            cls.env,
            login='al2c_stage_pm',
            name='Project Manager Sarah',
            groups='base.group_user,project.group_project_manager,sales_team.group_sale_salesman',
        )
        cls.agent_user = new_test_user(
            cls.env,
            login='al2c_stage_agent',
            name='Autonomous Agent X',
            groups='base.group_user,sales_team.group_sale_salesman,insilos_al2c.group_al2c_agent',
        )
        cls.consultant_user = new_test_user(
            cls.env,
            login='al2c_stage_consultant',
            name='Consultant Alex',
            groups='base.group_user,hr_timesheet.group_hr_timesheet_user',
        )

        cls.employee = cls.env['hr.employee'].create({
            'name': 'Consultant Alex',
            'user_id': cls.consultant_user.id,
            'company_id': cls.env.company.id,
        })

        # Customer & Product
        cls.partner = cls.env['res.partner'].create({
            'name': 'Enterprise Client Vietnam Corp',
            'email': 'procurement@client.vn',
            'is_company': True,
        })
        cls.sku_growth = cls.env['product.product'].search([('default_code', '=', 'ERP-GROWTH')], limit=1)

    def _create_and_confirm_so(self):
        so = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'pricelist_id': self.pricelist.id,
            'order_line': [Command.create({
                'product_id': self.sku_growth.id,
                'product_uom_qty': 1,
                'price_unit': self.sku_growth.list_price,
            })],
        })
        so.action_confirm()
        return so

    def test_activate_stage_gate_sequential_enforcement(self):
        """Test 1: Subsequent stage gates cannot be reached or signed off until
        earlier stages have verified customer acceptance (al2c_billing_eligible == True).
        """
        so = self._create_and_confirm_so()
        line = so.order_line
        project = line.project_id
        self.assertTrue(project, "Project must be created upon SO confirmation")

        milestones = project.milestone_ids.sorted('sequence')
        self.assertEqual(len(milestones), 5)
        self.assertEqual(milestones.mapped('name'), PHASES)

        ms_prepare = milestones[0]
        ms_explore = milestones[1]
        ms_realize = milestones[2]

        doc = self.env['documents.document'].create({
            'name': 'Explore_Signoff.pdf',
            'mimetype': 'application/pdf',
        })

        # 1. Attempt to reach Explore while Prepare is unapproved -> UserError
        with self.assertRaises(UserError) as cm:
            ms_explore.with_user(self.pm_user).write({'is_reached': True})
        self.assertIn("Prerequisite SAP Activate stage gate locked", str(cm.exception))

        # 2. Attempt to sign off Explore directly while Prepare is unapproved -> UserError
        with self.assertRaises(UserError) as cm:
            ms_explore.with_user(self.pm_user).action_register_signoff(doc.id)
        self.assertIn("Prerequisite SAP Activate stage gate locked", str(cm.exception))

        # 3. Mark Prepare reached without sign-off doc
        ms_prepare.with_user(self.pm_user).write({'is_reached': True})
        self.assertFalse(ms_prepare.al2c_billing_eligible)

        # Attempt Explore again: still blocked because Prepare lacks customer sign-off doc
        with self.assertRaises(UserError) as cm:
            ms_explore.with_user(self.pm_user).write({'is_reached': True})
        self.assertIn("Prerequisite SAP Activate stage gate locked", str(cm.exception))

        # 4. Attach valid sign-off document to Prepare as PM
        doc_prep = self.env['documents.document'].create({
            'name': 'Prepare_Signoff.pdf',
            'mimetype': 'application/pdf',
        })
        ms_prepare.with_user(self.pm_user).action_register_signoff(doc_prep.id)
        self.assertTrue(ms_prepare.al2c_billing_eligible)

        # 5. Now Explore can be reached and signed off
        doc_exp = self.env['documents.document'].create({
            'name': 'Explore_Acceptance.pdf',
            'mimetype': 'application/pdf',
        })
        ms_explore.with_user(self.pm_user).action_register_signoff(doc_exp.id)
        self.assertTrue(ms_explore.al2c_billing_eligible)

        # 6. Attempt to skip Realize and reach Deploy -> UserError
        ms_deploy = milestones[3]
        with self.assertRaises(UserError) as cm:
            ms_deploy.with_user(self.pm_user).write({'is_reached': True})
        self.assertIn("Prerequisite SAP Activate stage gate locked", str(cm.exception))

    def test_milestone_billing_gated_by_signoff_document(self):
        """Test 2: Milestone delivery quantity increases ONLY when al2c_billing_eligible
        is True (signed customer signoff document attached). _create_invoices() blocks
        billing until prerequisite deliverables are approved.
        """
        so = self._create_and_confirm_so()
        line = so.order_line
        project = line.project_id
        milestones = project.milestone_ids.sorted('sequence')
        ms_prepare = milestones[0]

        # Initial state: 0 delivered, nothing to invoice
        self.assertEqual(line.qty_delivered, 0.0)
        with self.assertRaises(UserError):
            so._create_invoices()

        # Mark Prepare as reached WITHOUT signoff document
        ms_prepare.with_user(self.pm_user).write({'is_reached': True})
        line._compute_qty_delivered()
        self.assertEqual(
            line.qty_delivered, 0.0,
            "Delivered quantity must NOT increase without signed customer acceptance doc (Decree 70/2025)",
        )
        with self.assertRaises(UserError):
            so._create_invoices()

        # Attach customer sign-off document to Prepare
        doc = self.env['documents.document'].create({
            'name': 'Charter_Signoff_Decree70.pdf',
            'mimetype': 'application/pdf',
        })
        ms_prepare.with_user(self.pm_user).action_register_signoff(doc.id)
        self.assertTrue(ms_prepare.al2c_billing_eligible)

        # Delivered qty now equals Prepare weight: 15% (0.15)
        self.assertAlmostEqual(line.qty_delivered, 0.15, places=2)

        # Billing triggers successfully for exactly 15%
        invoices = so._create_invoices()
        self.assertEqual(len(invoices), 1)
        inv = invoices[0]
        inv_line = inv.invoice_line_ids.filtered(lambda l: l.product_id == self.sku_growth)
        self.assertAlmostEqual(inv_line.quantity, 0.15, places=2)

        # Further invoicing is blocked until next stage is approved
        with self.assertRaises(UserError):
            so._create_invoices()

    def test_timesheet_budget_burn_85_percent_warning(self):
        """Test 3: Real-time task budget burn warnings trigger when timesheet
        hours logged on project.task cross 85% of allocated hours.
        """
        project = self.env['project.project'].create({
            'name': 'AL2C Implementation Client Delta',
            'allow_timesheets': True,
            'user_id': self.pm_user.id,
        })
        task = self.env['project.task'].create({
            'name': 'Realize: Core Financial Configuration',
            'project_id': project.id,
            'allocated_hours': 100.0,
        })

        # 1. Log 50 hours (50% burn) -> No warning
        ts1 = self.env['account.analytic.line'].create({
            'name': 'General ledger setup',
            'task_id': task.id,
            'project_id': project.id,
            'unit_amount': 50.0,
            'employee_id': self.employee.id,
        })
        self.assertFalse(task.al2c_burn_warning_sent)
        self.assertFalse(any("AL2C Budget Burn Warning" in (m.body or '') for m in task.message_ids))

        # 2. Log 30 more hours (total 80 hours = 80%) -> No warning
        ts2 = self.env['account.analytic.line'].create({
            'name': 'Bank reconciliation rules',
            'task_id': task.id,
            'project_id': project.id,
            'unit_amount': 30.0,
            'employee_id': self.employee.id,
        })
        self.assertFalse(task.al2c_burn_warning_sent)

        # 3. Log 6 more hours (total 86 hours = 86% >= 85%) -> Alert triggers!
        ts3 = self.env['account.analytic.line'].create({
            'name': 'Fixed assets ledger',
            'task_id': task.id,
            'project_id': project.id,
            'unit_amount': 6.0,
            'employee_id': self.employee.id,
        })
        self.assertTrue(task.al2c_burn_warning_sent)

        # Check chatter on task and project
        task_warning = any("AL2C Budget Burn Warning" in (m.body or '') for m in task.message_ids)
        project_warning = any("AL2C Budget Burn Warning" in (m.body or '') for m in project.message_ids)
        self.assertTrue(task_warning, "Task chatter must receive budget burn warning")
        self.assertTrue(project_warning, "Project chatter must receive budget burn warning")

        # Check scheduled To-Do activity for PM
        pm_activity = task.activity_ids.filtered(lambda a: a.user_id == self.pm_user)
        self.assertTrue(pm_activity, "Project Manager must have an activity scheduled upon budget burn")
        self.assertIn("AL2C Budget Burn Warning", pm_activity.summary)

        # 4. Burn reduction below 85%: warning flag resets
        ts3.write({'unit_amount': 1.0})  # total now 81 hours = 81%
        self.assertFalse(task.al2c_burn_warning_sent)

    def test_sod_blocks_unauthorized_milestone_signoffs_and_alterations(self):
        """Test 4: Segregation of Duties (SoD) blocks autonomous agent users
        (group_al2c_agent) from calling action_register_signoff or altering milestones;
        restricts milestone alterations to Project Managers.
        """
        so = self._create_and_confirm_so()
        milestones = so.order_line.project_id.milestone_ids.sorted('sequence')
        ms_prepare = milestones[0]

        doc = self.env['documents.document'].create({
            'name': 'Customer_Token.pdf',
            'mimetype': 'application/pdf',
        })

        # 1. Autonomous agent user CANNOT call action_register_signoff
        with self.assertRaises(UserError) as cm:
            ms_prepare.with_user(self.agent_user).action_register_signoff(doc.id)
        self.assertIn("Autonomous AI agents cannot self-sign", str(cm.exception))

        # 2. Autonomous agent user CANNOT write to restricted milestone fields directly
        with self.assertRaises(UserError) as cm:
            ms_prepare.with_user(self.agent_user).write({'is_reached': True})
        self.assertIn("Autonomous AI agents cannot alter project milestone", str(cm.exception))

        with self.assertRaises(UserError) as cm:
            ms_prepare.with_user(self.agent_user).write({'quantity_percentage': 0.50})
        self.assertIn("Autonomous AI agents cannot alter project milestone", str(cm.exception))

        # 3. Autonomous agent user CANNOT delete milestone
        with self.assertRaises(UserError) as cm:
            ms_prepare.with_user(self.agent_user).unlink()
        self.assertIn("Autonomous AI agents cannot delete", str(cm.exception))

        # 4. Regular consultant (non-PM) CANNOT call action_register_signoff
        with self.assertRaises(UserError) as cm:
            ms_prepare.with_user(self.consultant_user).action_register_signoff(doc.id)
        self.assertIn("Only Project Managers can register customer sign-off", str(cm.exception))

        # 5. Regular consultant CANNOT alter milestone weights or deadlines
        with self.assertRaises(UserError) as cm:
            ms_prepare.with_user(self.consultant_user).write({'quantity_percentage': 0.50})
        self.assertIn("Only Project Managers can alter project milestone", str(cm.exception))

        # 6. Project Manager CAN perform verification and register signoff
        res = ms_prepare.with_user(self.pm_user).action_register_signoff(doc.id)
        self.assertTrue(res)
        self.assertTrue(ms_prepare.al2c_billing_eligible)
