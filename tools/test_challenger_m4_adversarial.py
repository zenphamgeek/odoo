#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ADVERSARIAL EMPIRICAL HARNESS: Operational Governance (R4 & R1)
Challenger 1: Adversarial Verifier (Stage Gates, Premature Invoicing, SoD, Budget Burn, Discount Guardrails)
Database: Strictly targeting local dev instance insilos20_dev (127.0.0.1:5434)
"""

import os
import sys
import math
import time
import traceback

# Ensure repo root is on path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import odoo
from odoo import Command, fields
from odoo.exceptions import UserError, AccessError
from odoo.tools import config


class AdversarialTestResult:
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.findings = []
        self.attack_reports = {}

    def record_pass(self, test_name, detail=""):
        self.tests_run += 1
        self.tests_passed += 1
        print(f"  [PASS] {test_name}")
        if detail:
            print(f"         └─ {detail}")

    def record_fail(self, test_name, error, detail=""):
        self.tests_run += 1
        self.tests_failed += 1
        print(f"  [FAIL/VULNERABILITY] {test_name}")
        print(f"         └─ ERROR: {error}")
        if detail:
            print(f"         └─ DETAIL: {detail}")
        self.findings.append({
            'test': test_name,
            'error': str(error),
            'detail': detail,
        })


def setup_odoo_env():
    """Initialize Odoo configuration and environment targeting insilos20_dev."""
    conf_path = os.path.join(ROOT_DIR, 'insilos.conf')
    config.parse_config(['-c', conf_path, '-d', 'insilos20_dev'])
    
    db_name = config['db_name'][0] if isinstance(config['db_name'], (list, tuple)) else config['db_name']
    from odoo.orm.registry import Registry
    from odoo.orm.utils import SUPERUSER_ID
    from odoo.api import Environment

    odoo.netsvc.init_logger()
    registry = Registry.new(db_name, lock_wait=60)
    return registry


def run_all_adversarial_tests(env, results):
    print("=" * 80)
    print("EMPIRICAL CHALLENGER 1: ADVERSARIAL STRESS TEST SUITE (R4 & R1 GOVERNANCE)")
    print("Target Database: insilos20_dev (127.0.0.1:5434)")
    print("=" * 80)

    # Setup base entities
    Partner = env['res.partner']
    User = env['res.users']
    SaleOrder = env['sale.order']
    ProjectMilestone = env['project.milestone']
    ProjectProject = env['project.project']
    ProjectTask = env['project.task']
    AnalyticLine = env['account.analytic.line']
    Document = env['documents.document']
    ICP = env['ir.config_parameter'].sudo()

    # Configure baseline governance ICPs
    ICP.set_param('al2c.autonomy_enabled', 'True')
    ICP.set_param('al2c.max_discount', '10.0')
    ICP.set_param('al2c.max_tcv', '500000000')

    pricelist_vnd = env.ref('insilos_al2c.pricelist_vnd', raise_if_not_found=False)
    partner = Partner.create({
        'name': 'Adversarial Test Enterprise Customer',
        'is_company': True,
        'property_product_pricelist': pricelist_vnd.id if pricelist_vnd else False,
    })

    from odoo.tests import new_test_user

    ts = int(time.time())
    context_no_mail = {'no_reset_password': True, 'mail_create_nolog': True, 'mail_create_nosubscribe': True}
    pm_user = new_test_user(
        env,
        login=f'adv_pm_{ts}',
        name='Adversarial Test PM',
        groups='base.group_user,project.group_project_manager,sales_team.group_sale_manager',
        context=context_no_mail,
    )
    agent_user = new_test_user(
        env,
        login=f'adv_agent_{ts}',
        name='Adversarial Test Agent',
        groups='base.group_user,sales_team.group_sale_salesman,insilos_al2c.group_al2c_agent',
        context=context_no_mail,
    )
    salesman_user = new_test_user(
        env,
        login=f'adv_salesman_{ts}',
        name='Adversarial Test Salesman',
        groups='base.group_user,sales_team.group_sale_salesman',
        context=context_no_mail,
    )

    employee = env['hr.employee'].create({
        'name': 'Adversarial Test Consultant',
        'user_id': pm_user.id,
        'company_id': env.company.id,
    })

    sku_growth = env['product.product'].search([('default_code', '=', 'ERP-GROWTH')], limit=1)
    sku_starter = env['product.product'].search([('default_code', '=', 'ERP-STARTER')], limit=1)

    # =========================================================================
    # ATTACK 1: STAGE GATE SEQUENCE BYPASS
    # =========================================================================
    print("\n[ATTACK 1] STAGE GATE SEQUENCE BYPASS & UNORDERED SEQUENCES")
    
    # 1.1 Direct Gate Jump: Can someone mark Realize reached without Explore?
    try:
        so1 = SaleOrder.create({
            'partner_id': partner.id,
            'pricelist_id': pricelist_vnd.id if pricelist_vnd else False,
            'order_line': [Command.create({
                'product_id': sku_growth.id,
                'product_uom_qty': 1,
                'price_unit': sku_growth.list_price,
            })],
        })
        so1.action_confirm()
        project1 = so1.order_line.project_id
        milestones1 = project1.milestone_ids.sorted('sequence')
        ms_prepare = milestones1[0]
        ms_explore = milestones1[1]
        ms_realize = milestones1[2]
        ms_deploy = milestones1[3]

        # Prepare signed off
        doc_prep = Document.create({'name': 'Doc_Prep.pdf', 'mimetype': 'application/pdf'})
        ms_prepare.with_user(pm_user).action_register_signoff(doc_prep.id)

        # Explore is NOT signed off. Attempt to mark Realize reached!
        try:
            ms_realize.with_user(pm_user).write({'is_reached': True})
            results.record_fail("1.1 Jump Prepare->Realize without Explore", "Allowed marking Realize reached without Explore signoff!")
        except UserError as e:
            if "Prerequisite SAP Activate stage gate locked" in str(e):
                results.record_pass("1.1 Jump Prepare->Realize blocked", f"UserError raised: {e}")
            else:
                results.record_fail("1.1 Jump Prepare->Realize error mismatch", str(e))

        # Attempt to signoff Deploy directly without Explore or Realize!
        doc_deploy = Document.create({'name': 'Doc_Deploy.pdf', 'mimetype': 'application/pdf'})
        try:
            ms_deploy.with_user(pm_user).action_register_signoff(doc_deploy.id)
            results.record_fail("1.2 Jump Prepare->Deploy via action_register_signoff", "Allowed signing Deploy without Explore/Realize!")
        except UserError as e:
            if "Prerequisite SAP Activate stage gate locked" in str(e):
                results.record_pass("1.2 Jump Prepare->Deploy blocked", f"UserError raised: {e}")
            else:
                results.record_fail("1.2 Jump Prepare->Deploy error mismatch", str(e))

    except Exception as e:
        results.record_fail("1.1/1.2 Sequence Bypass Setup", e, traceback.format_exc())

    # 1.3 Unordered sequences on Activate phases: What if Explore has sequence 100 and Realize has sequence 10?
    try:
        custom_proj = ProjectProject.create({'name': 'Adversarial Custom Project Activate'})
        # Prepare: seq 10, Realize: seq 20, Explore: seq 50 (Explore placed after Realize in sequence!)
        ms_c_prep = ProjectMilestone.create({'name': 'Prepare Phase', 'project_id': custom_proj.id, 'sequence': 10})
        ms_c_realize = ProjectMilestone.create({'name': 'Realize Phase', 'project_id': custom_proj.id, 'sequence': 20})
        ms_c_explore = ProjectMilestone.create({'name': 'Explore Phase', 'project_id': custom_proj.id, 'sequence': 50})

        doc_c_prep = Document.create({'name': 'Doc_C_Prep.pdf', 'mimetype': 'application/pdf'})
        ms_c_prep.with_user(pm_user).action_register_signoff(doc_c_prep.id)

        # Realize has sequence 20 (< 50 Explore), but phase index is 2 (> 1 Explore). Can Realize be reached?
        try:
            ms_c_realize.with_user(pm_user).write({'is_reached': True})
            results.record_fail("1.3 Activate phase order vs sequence invert", "Allowed Realize to precede Explore due to sequence inversion!")
        except UserError as e:
            if "Prerequisite SAP Activate stage gate locked" in str(e) and "Explore" in str(e):
                results.record_pass("1.3 Activate phase order dominates sequence inversion", f"Blocked: {e}")
            else:
                results.record_fail("1.3 Activate phase order unexpected error", str(e))

    except Exception as e:
        results.record_fail("1.3 Unordered Sequence Inversion", e, traceback.format_exc())

    # 1.4 Non-Activate Custom Names with sequence ordering
    try:
        proj_custom = ProjectProject.create({'name': 'Adversarial Custom Names Project'})
        ms1 = ProjectMilestone.create({'name': 'Milestone Alpha', 'project_id': proj_custom.id, 'sequence': 10})
        ms2 = ProjectMilestone.create({'name': 'Milestone Beta', 'project_id': proj_custom.id, 'sequence': 20})

        # ms1 not reached, attempt to reach ms2
        try:
            ms2.with_user(pm_user).write({'is_reached': True})
            results.record_fail("1.4 Custom Name Sequence Gate", "Allowed Milestone Beta (seq 20) when Alpha (seq 10) unreached!")
        except UserError as e:
            if "Prerequisite SAP Activate stage gate locked" in str(e) and "Milestone Alpha" in str(e):
                results.record_pass("1.4 Custom Name Sequence Gate enforced", f"Blocked: {e}")
            else:
                results.record_fail("1.4 Custom Name unexpected error", str(e))

    except Exception as e:
        results.record_fail("1.4 Custom Name Sequence Gate", e, traceback.format_exc())

    # 1.5 Milestone Creation with is_reached=True directly at creation
    try:
        proj_create = ProjectProject.create({'name': 'Adversarial Create Project'})
        ms_a = ProjectMilestone.create({'name': 'Prepare Gate', 'project_id': proj_create.id, 'sequence': 10})
        
        # Try to create Explore with is_reached=True while Prepare is unapproved
        try:
            ms_b = ProjectMilestone.create({
                'name': 'Explore Gate',
                'project_id': proj_create.id,
                'sequence': 20,
                'is_reached': True,
            })
            results.record_fail("1.5 Create Milestone with is_reached=True bypass", "Allowed creating reached milestone when prior unreached!")
        except UserError as e:
            if "Prerequisite SAP Activate stage gate locked" in str(e):
                results.record_pass("1.5 Create Milestone with is_reached=True blocked", f"UserError on create: {e}")
            else:
                results.record_fail("1.5 Create Milestone unexpected error", str(e))

    except Exception as e:
        results.record_fail("1.5 Create Milestone Bypass", e, traceback.format_exc())


    # =========================================================================
    # ATTACK 2: PREMATURE INVOICING & LEAKED BILLING DELIVERIES
    # =========================================================================
    print("\n[ATTACK 2] PREMATURE INVOICING & MILESTONE BILLING GATES")

    try:
        so2 = SaleOrder.create({
            'partner_id': partner.id,
            'pricelist_id': pricelist_vnd.id if pricelist_vnd else False,
            'order_line': [Command.create({
                'product_id': sku_growth.id,
                'product_uom_qty': 1,
                'price_unit': sku_growth.list_price,
            })],
        })
        so2.action_confirm()
        line2 = so2.order_line
        project2 = line2.project_id
        ms_prep2 = project2.milestone_ids.sorted('sequence')[0]

        # Case 2.1: Initial unreached state
        self_inv_blocked = False
        try:
            so2._create_invoices()
        except UserError:
            self_inv_blocked = True
        
        if self_inv_blocked and line2.qty_delivered == 0.0 and line2.qty_to_invoice == 0.0:
            results.record_pass("2.1 Initial Milestone Invoicing Blocked", "qty_delivered=0.0, qty_to_invoice=0.0, _create_invoices() raises UserError")
        else:
            results.record_fail("2.1 Initial Milestone Invoicing Leaked", f"delivered={line2.qty_delivered}, to_invoice={line2.qty_to_invoice}")

        # Case 2.2: Marked is_reached=True WITHOUT al2c_signoff_document_id
        ms_prep2.with_user(pm_user).write({'is_reached': True})
        line2._compute_qty_delivered()

        self_inv2_blocked = False
        try:
            so2._create_invoices()
        except UserError:
            self_inv2_blocked = True

        if not ms_prep2.al2c_billing_eligible and line2.qty_delivered == 0.0 and line2.qty_to_invoice == 0.0 and self_inv2_blocked:
            results.record_pass("2.2 is_reached=True without signed document BLOCKS billing 100%", 
                                "al2c_billing_eligible=False, delivered=0.0, to_invoice=0.0, invoicing blocked")
        else:
            results.record_fail("2.2 Premature Invoicing Leak!", 
                                f"eligible={ms_prep2.al2c_billing_eligible}, delivered={line2.qty_delivered}, to_invoice={line2.qty_to_invoice}")

        # Case 2.3: Context final=True bypass attempt
        try:
            so2.with_context(final=True)._create_invoices()
            results.record_fail("2.3 final=True Context Bypass", "Created invoice with final=True context on unapproved deliverable!")
        except UserError:
            results.record_pass("2.3 final=True Context Bypass blocked", "UserError strictly raised even with final=True")

        # Case 2.4: Valid Signoff document enables EXACT milestone billing
        doc_valid = Document.create({'name': 'Signed_Charter_Acceptance.pdf', 'mimetype': 'application/pdf'})
        ms_prep2.with_user(pm_user).action_register_signoff(doc_valid.id)

        if ms_prep2.al2c_billing_eligible and abs(line2.qty_delivered - 0.15) < 0.001:
            invs = so2._create_invoices()
            if len(invs) == 1 and abs(invs[0].invoice_line_ids[0].quantity - 0.15) < 0.001:
                results.record_pass("2.4 Valid Signoff Enables Exact Deliverable (15%)", f"Invoice generated for exactly {invs[0].amount_untaxed:,.0f} VND")
            else:
                results.record_fail("2.4 Invoicing Quantity Mismatch", f"Invoice lines: {invs.invoice_line_ids.mapped('quantity')}")
        else:
            results.record_fail("2.4 Valid Signoff Delivery Calculation", f"eligible={ms_prep2.al2c_billing_eligible}, delivered={line2.qty_delivered}")

        # Case 2.5: Re-invoicing the same milestone immediately blocked
        try:
            so2._create_invoices()
            results.record_fail("2.5 Double Invoicing Vulnerability", "Allowed creating duplicate invoice for already billed milestone!")
        except UserError:
            results.record_pass("2.5 Double Invoicing Blocked", "UserError raised: subsequent invoicing blocked until next stage gate")

    except Exception as e:
        results.record_fail("ATTACK 2 Execution Failure", e, traceback.format_exc())


    # =========================================================================
    # ATTACK 3: SEGREGATION OF DUTIES (SoD) & ROLE PRIVILEGE STRESS
    # =========================================================================
    print("\n[ATTACK 3] SEGREGATION OF DUTIES (SoD) & ROLE PRIVILEGE STRESS")

    try:
        so3 = SaleOrder.create({
            'partner_id': partner.id,
            'pricelist_id': pricelist_vnd.id if pricelist_vnd else False,
            'order_line': [Command.create({
                'product_id': sku_growth.id,
                'product_uom_qty': 1,
                'price_unit': sku_growth.list_price,
            })],
        })
        so3.action_confirm()
        ms_sod = so3.order_line.project_id.milestone_ids.sorted('sequence')[0]
        test_doc = Document.create({'name': 'Fake_Signoff.pdf', 'mimetype': 'application/pdf'})

        # 3.1 Autonomous Agent User (group_al2c_agent)
        # a) action_register_signoff
        try:
            ms_sod.with_user(agent_user).action_register_signoff(test_doc.id)
            results.record_fail("3.1a Agent self-sign signoff", "group_al2c_agent called action_register_signoff without error!")
        except (UserError, AccessError) as e:
            if "Autonomous AI agents cannot self-sign" in str(e) or "AL2C-GOV-002" in str(e):
                results.record_pass("3.1a Agent self-sign blocked", f"Strictly raised: {e}")
            else:
                results.record_fail("3.1a Agent signoff error mismatch", str(e))

        # b) write to quantity_percentage
        try:
            ms_sod.with_user(agent_user).write({'quantity_percentage': 0.88})
            results.record_fail("3.1b Agent write quantity_percentage", "group_al2c_agent modified milestone quantity_percentage!")
        except (UserError, AccessError) as e:
            results.record_pass("3.1b Agent write quantity_percentage blocked", f"Raised: {e}")

        # c) write to is_reached
        try:
            ms_sod.with_user(agent_user).write({'is_reached': True})
            results.record_fail("3.1c Agent write is_reached", "group_al2c_agent modified milestone is_reached!")
        except (UserError, AccessError) as e:
            results.record_pass("3.1c Agent write is_reached blocked", f"Raised: {e}")

        # d) write to sequence
        try:
            ms_sod.with_user(agent_user).write({'sequence': 999})
            results.record_fail("3.1d Agent write sequence", "group_al2c_agent modified milestone sequence!")
        except (UserError, AccessError) as e:
            results.record_pass("3.1d Agent write sequence blocked", f"Raised: {e}")

        # e) write to deadline
        try:
            ms_sod.with_user(agent_user).write({'deadline': '2026-12-31'})
            results.record_fail("3.1e Agent write deadline", "group_al2c_agent modified milestone deadline!")
        except (UserError, AccessError) as e:
            results.record_pass("3.1e Agent write deadline blocked", f"Raised: {e}")

        # f) unlink
        try:
            ms_sod.with_user(agent_user).unlink()
            results.record_fail("3.1f Agent delete milestone", "group_al2c_agent deleted milestone!")
        except (UserError, AccessError) as e:
            results.record_pass("3.1f Agent delete milestone blocked", f"Raised: {e}")

        # 3.2 Basic Salesman User (sales_team.group_sale_salesman, non-PM)
        # a) action_register_signoff
        try:
            ms_sod.with_user(salesman_user).action_register_signoff(test_doc.id)
            results.record_fail("3.2a Salesman action_register_signoff", "Salesman called action_register_signoff!")
        except (UserError, AccessError) as e:
            if "Only Project Managers can register customer sign-off" in str(e):
                results.record_pass("3.2a Salesman signoff blocked", f"Raised: {e}")
            else:
                results.record_fail("3.2a Salesman signoff unexpected error", str(e))

        # b) write to quantity_percentage
        try:
            ms_sod.with_user(salesman_user).write({'quantity_percentage': 0.50})
            results.record_fail("3.2b Salesman write quantity_percentage", "Salesman modified milestone quantity_percentage!")
        except (UserError, AccessError) as e:
            results.record_pass("3.2b Salesman write quantity_percentage blocked", f"Raised: {e}")

        # c) write to is_reached
        try:
            ms_sod.with_user(salesman_user).write({'is_reached': True})
            results.record_fail("3.2c Salesman write is_reached", "Salesman modified milestone is_reached!")
        except (UserError, AccessError) as e:
            results.record_pass("3.2c Salesman write is_reached blocked", f"Raised: {e}")

        # d) unlink
        try:
            ms_sod.with_user(salesman_user).unlink()
            results.record_fail("3.2d Salesman delete milestone", "Salesman deleted milestone!")
        except (UserError, AccessError) as e:
            results.record_pass("3.2d Salesman delete milestone blocked", f"Raised: {e}")

        # 3.3 Milestone CREATE SoD check under agent_user and salesman_user
        try:
            # Can an agent create a milestone?
            ms_agent_created = ProjectMilestone.with_user(agent_user).create({
                'name': 'Agent Autonomous Milestone',
                'project_id': so3.order_line.project_id.id,
                'quantity_percentage': 0.35,
            })
            # Check if created successfully without error
            results.record_fail("3.3 Milestone CREATE SoD gap", 
                                f"Agent user was able to create milestone ID {ms_agent_created.id} with quantity_percentage=0.35! (write is blocked, but create lacks SoD check)")
        except (UserError, AccessError) as e:
            results.record_pass("3.3 Milestone CREATE SoD enforced", f"Create blocked: {e}")

    except Exception as e:
        results.record_fail("ATTACK 3 Execution Failure", e, traceback.format_exc())


    # =========================================================================
    # ATTACK 4: BUDGET BURN WARNING BOUNDARY & HARNESS STRESS
    # =========================================================================
    print("\n[ATTACK 4] BUDGET BURN WARNING BOUNDARY & HARNESS STRESS")

    try:
        project_burn = ProjectProject.create({
            'name': 'Adversarial Budget Burn Project',
            'allow_timesheets': True,
            'user_id': pm_user.id,
        })
        task_burn = ProjectTask.create({
            'name': 'Core Implementation Task',
            'project_id': project_burn.id,
            'allocated_hours': 100.0,
        })

        # 4.1 Boundary: 84.9% (effective=84.9h / allocated=100.0h) -> STRICTLY NO ALERT
        ts_84_9 = AnalyticLine.create({
            'name': 'Burn 84.9 hours',
            'project_id': project_burn.id,
            'task_id': task_burn.id,
            'employee_id': employee.id,
            'unit_amount': 84.9,
            'date': fields.Date.today(),
        })
        task_burn.invalidate_recordset(['effective_hours', 'al2c_burn_warning_sent'])
        burn_msg_84_9 = any("AL2C Budget Burn Warning" in (m.body or '') for m in task_burn.message_ids)
        if not task_burn.al2c_burn_warning_sent and not burn_msg_84_9:
            results.record_pass("4.1 Exact 84.9% Burn: NO Alert", f"effective={task_burn.effective_hours}, flag={task_burn.al2c_burn_warning_sent}")
        else:
            results.record_fail("4.1 Spurious Alert at 84.9%", f"flag={task_burn.al2c_burn_warning_sent}, msg_found={burn_msg_84_9}")

        # 4.2 Boundary: Exactly 85.0% (effective=85.0h) -> MUST TRIGGER ALERT
        ts_0_1 = AnalyticLine.create({
            'name': 'Burn 0.1 hours to reach 85.0',
            'project_id': project_burn.id,
            'task_id': task_burn.id,
            'employee_id': employee.id,
            'unit_amount': 0.1,
            'date': fields.Date.today(),
        })
        task_burn.invalidate_recordset(['effective_hours', 'al2c_burn_warning_sent'])
        burn_msg_85_0 = any("AL2C Budget Burn Warning" in (m.body or '') for m in task_burn.message_ids)
        pm_act_85_0 = task_burn.activity_ids.filtered(lambda a: a.user_id == pm_user)

        if task_burn.al2c_burn_warning_sent and burn_msg_85_0 and pm_act_85_0:
            results.record_pass("4.2 Exact 85.0% Burn: ALERT ACTIVATED", 
                                f"effective={task_burn.effective_hours}, chatter alert posted, PM activity scheduled")
        else:
            results.record_fail("4.2 Failed Alert at 85.0%", 
                                f"flag={task_burn.al2c_burn_warning_sent}, msg={burn_msg_85_0}, act={bool(pm_act_85_0)}")

        # 4.3 Boundary: 85.1% -> NO duplicate spam activity
        msg_count_before = len(task_burn.message_ids.filtered(lambda m: "AL2C Budget Burn Warning" in (m.body or '')))
        ts_85_1 = AnalyticLine.create({
            'name': 'Burn 0.1 hours to reach 85.1',
            'project_id': project_burn.id,
            'task_id': task_burn.id,
            'employee_id': employee.id,
            'unit_amount': 0.1,
            'date': fields.Date.today(),
        })
        task_burn.invalidate_recordset(['effective_hours', 'al2c_burn_warning_sent'])
        msg_count_after = len(task_burn.message_ids.filtered(lambda m: "AL2C Budget Burn Warning" in (m.body or '')))

        if task_burn.al2c_burn_warning_sent and msg_count_after == msg_count_before:
            results.record_pass("4.3 85.1% Burn: Idempotent (No Duplicate Spam)", "Warning flag maintained, 0 duplicate messages posted")
        else:
            results.record_fail("4.3 Duplicate Spam at 85.1%", f"msg_count before={msg_count_before}, after={msg_count_after}")

        # 4.4 Boundary: Burn reduction below 85% resets flag
        ts_84_9.write({'unit_amount': 70.0}) # Total now 70.2 hours = 70.2%
        task_burn.invalidate_recordset(['effective_hours', 'al2c_burn_warning_sent'])
        if not task_burn.al2c_burn_warning_sent and task_burn.effective_hours < 85.0:
            results.record_pass("4.4 Burn Reduction Below 85% Resets Warning Flag", f"effective={task_burn.effective_hours}, flag={task_burn.al2c_burn_warning_sent}")
        else:
            results.record_fail("4.4 Warning Flag Reset Failed", f"effective={task_burn.effective_hours}, flag={task_burn.al2c_burn_warning_sent}")

        # 4.5 Robustness Edge Case: allocated_hours = 0.0
        task_zero = ProjectTask.create({
            'name': 'Task Zero Allocated Hours',
            'project_id': project_burn.id,
            'allocated_hours': 0.0,
        })
        ts_zero = AnalyticLine.create({
            'name': 'Log 5h on zero task',
            'project_id': project_burn.id,
            'task_id': task_zero.id,
            'employee_id': employee.id,
            'unit_amount': 5.0,
            'date': fields.Date.today(),
        })
        task_zero.invalidate_recordset(['effective_hours', 'al2c_burn_warning_sent'])
        if not task_zero.al2c_burn_warning_sent and task_zero.effective_hours == 5.0:
            results.record_pass("4.5 Robustness on allocated_hours = 0.0 (ZeroDivisionError Guarded)", "effective=5.0, no division by zero, no spurious alert")
        else:
            results.record_fail("4.5 Failure on allocated_hours = 0.0", f"effective={task_zero.effective_hours}, flag={task_zero.al2c_burn_warning_sent}")

        # 4.6 Robustness Edge Case: allocated_hours = -10.0 (Negative)
        task_neg = ProjectTask.create({
            'name': 'Task Negative Allocated Hours',
            'project_id': project_burn.id,
            'allocated_hours': -10.0,
        })
        ts_neg = AnalyticLine.create({
            'name': 'Log 5h on negative task',
            'project_id': project_burn.id,
            'task_id': task_neg.id,
            'employee_id': employee.id,
            'unit_amount': 5.0,
            'date': fields.Date.today(),
        })
        task_neg.invalidate_recordset(['effective_hours', 'al2c_burn_warning_sent'])
        if not task_neg.al2c_burn_warning_sent and task_neg.effective_hours == 5.0:
            results.record_pass("4.6 Robustness on negative allocated_hours", "effective=5.0, no negative ratio alert")
        else:
            results.record_fail("4.6 Failure on negative allocated_hours", f"effective={task_neg.effective_hours}, flag={task_neg.al2c_burn_warning_sent}")

        # 4.7 Post-Timesheet Dynamic Budget Allocation Modification
        # Task with 100h, logged 80h (80% -> no alert). PM cuts allocated_hours to 90h (80/90 = 88.9% >= 85%)
        task_dyn = ProjectTask.create({
            'name': 'Task Dynamic Allocation',
            'project_id': project_burn.id,
            'allocated_hours': 100.0,
        })
        ts_dyn = AnalyticLine.create({
            'name': 'Log 80h',
            'project_id': project_burn.id,
            'task_id': task_dyn.id,
            'employee_id': employee.id,
            'unit_amount': 80.0,
            'date': fields.Date.today(),
        })
        task_dyn.invalidate_recordset(['effective_hours', 'al2c_burn_warning_sent'])
        self_dyn_before = task_dyn.al2c_burn_warning_sent  # should be False

        # Now PM reduces budget to 90.0 hours
        task_dyn.write({'allocated_hours': 90.0})
        task_dyn.invalidate_recordset(['effective_hours', 'al2c_burn_warning_sent'])

        if not self_dyn_before and task_dyn.al2c_burn_warning_sent:
            results.record_pass("4.7 Dynamic Allocated Hours Reduction Triggers Budget Burn Alert", 
                                f"Allocation cut to 90h with 80h logged (88.9%) triggered alert successfully")
        else:
            results.record_fail("4.7 Dynamic Allocation Reduction Failed to Trigger Alert", 
                                f"before={self_dyn_before}, after={task_dyn.al2c_burn_warning_sent}")

    except Exception as e:
        results.record_fail("ATTACK 4 Execution Failure", e, traceback.format_exc())


    # =========================================================================
    # ATTACK 5: DISCOUNT GUARDRAIL BOUNDARY (9.9% vs 10.0% vs 10.1%)
    # =========================================================================
    print("\n[ATTACK 5] DISCOUNT GUARDRAIL BOUNDARY & VND PRICING (9.9% vs 10.0% vs 10.1%)")

    try:
        # 5.1 Stated Discount Field Boundaries (al2c.max_discount = 10.0)
        # a) Stated 9.9% -> No breach
        so_st_9_9 = SaleOrder.with_user(agent_user).create({
            'partner_id': partner.id,
            'user_id': agent_user.id,
            'order_line': [Command.create({
                'product_id': sku_starter.id,
                'product_uom_qty': 1,
                'price_unit': 150_000_000.0,
                'discount': 9.9,
            })],
        })
        breaches_st_9_9 = so_st_9_9._al2c_threshold_breaches()
        disc_breach_9_9 = any("line discount" in b or "effective discount" in b for b in breaches_st_9_9)
        if not disc_breach_9_9:
            results.record_pass("5.1a Stated 9.9% Discount: NO Breach", f"Breaches: {breaches_st_9_9}")
        else:
            results.record_fail("5.1a False Positive at 9.9% Stated Discount", f"Breaches: {breaches_st_9_9}")

        # b) Stated 10.0% -> Exact ceiling, NO breach
        so_st_10_0 = SaleOrder.with_user(agent_user).create({
            'partner_id': partner.id,
            'user_id': agent_user.id,
            'order_line': [Command.create({
                'product_id': sku_starter.id,
                'product_uom_qty': 1,
                'price_unit': 150_000_000.0,
                'discount': 10.0,
            })],
        })
        breaches_st_10_0 = so_st_10_0._al2c_threshold_breaches()
        disc_breach_10_0 = any("line discount" in b or "effective discount" in b for b in breaches_st_10_0)
        if not disc_breach_10_0:
            results.record_pass("5.1b Stated 10.0% Discount: NO Breach (At Ceiling)", f"Breaches: {breaches_st_10_0}")
        else:
            results.record_fail("5.1b False Positive at 10.0% Stated Discount", f"Breaches: {breaches_st_10_0}")

        # c) Stated 10.1% -> MUST BREACH
        so_st_10_1 = SaleOrder.with_user(agent_user).create({
            'partner_id': partner.id,
            'user_id': agent_user.id,
            'order_line': [Command.create({
                'product_id': sku_starter.id,
                'product_uom_qty': 1,
                'price_unit': 150_000_000.0,
                'discount': 10.1,
            })],
        })
        breaches_st_10_1 = so_st_10_1._al2c_threshold_breaches()
        disc_breach_10_1 = any("line discount" in b and "exceeds 10.0%" in b for b in breaches_st_10_1)

        # Agent attempt to confirm without approval -> UserError
        agent_confirm_blocked = False
        try:
            so_st_10_1.with_user(agent_user).action_confirm()
        except UserError:
            agent_confirm_blocked = True

        if disc_breach_10_1 and agent_confirm_blocked:
            results.record_pass("5.1c Stated 10.1% Discount: BREACH & CONFIRMATION BLOCKED", 
                                f"Breach detected: {[b for b in breaches_st_10_1 if 'line discount' in b]}, confirmation blocked")
        else:
            results.record_fail("5.1c Failed Breach at 10.1% Stated Discount", 
                                f"breach_found={disc_breach_10_1}, confirm_blocked={agent_confirm_blocked}")

        # 5.2 Effective Discount Boundaries against 150M VND Catalog List Price
        # a) Effective 9.9%: price_unit = 150M * (1 - 0.099) = 135,150,000 VND
        so_eff_9_9 = SaleOrder.with_user(agent_user).create({
            'partner_id': partner.id,
            'user_id': agent_user.id,
            'order_line': [Command.create({
                'product_id': sku_starter.id,
                'product_uom_qty': 1,
                'price_unit': 135_150_000.0,
                'discount': 0.0,
            })],
        })
        breaches_eff_9_9 = so_eff_9_9._al2c_threshold_breaches()
        eff_breach_9_9 = any("effective discount" in b for b in breaches_eff_9_9)
        if not eff_breach_9_9:
            results.record_pass("5.2a Effective 9.9% Discount (135.15M VND): NO Breach", "Within 10.0% ceiling")
        else:
            results.record_fail("5.2a False Positive at 9.9% Effective Discount", f"Breaches: {breaches_eff_9_9}")

        # b) Effective 10.0%: price_unit = 150M * (1 - 0.10) = 135,000,000 VND
        so_eff_10_0 = SaleOrder.with_user(agent_user).create({
            'partner_id': partner.id,
            'user_id': agent_user.id,
            'order_line': [Command.create({
                'product_id': sku_starter.id,
                'product_uom_qty': 1,
                'price_unit': 135_000_000.0,
                'discount': 0.0,
            })],
        })
        breaches_eff_10_0 = so_eff_10_0._al2c_threshold_breaches()
        eff_breach_10_0 = any("effective discount" in b for b in breaches_eff_10_0)
        if not eff_breach_10_0:
            results.record_pass("5.2b Effective 10.0% Discount (135.0M VND): NO Breach (At Ceiling)", "Within 10.0% ceiling")
        else:
            results.record_fail("5.2b False Positive at 10.0% Effective Discount", f"Breaches: {breaches_eff_10_0}")

        # c) Effective 10.1%: price_unit = 150M * (1 - 0.101) = 134,850,000 VND
        so_eff_10_1 = SaleOrder.with_user(agent_user).create({
            'partner_id': partner.id,
            'user_id': agent_user.id,
            'order_line': [Command.create({
                'product_id': sku_starter.id,
                'product_uom_qty': 1,
                'price_unit': 134_850_000.0,
                'discount': 0.0,
            })],
        })
        breaches_eff_10_1 = so_eff_10_1._al2c_threshold_breaches()
        eff_breach_10_1 = any("effective discount" in b and "ceiling" in b for b in breaches_eff_10_1)

        agent_eff_blocked = False
        try:
            so_eff_10_1.with_user(agent_user).action_confirm()
        except UserError:
            agent_eff_blocked = True

        if eff_breach_10_1 and agent_eff_blocked:
            results.record_pass("5.2c Effective 10.1% Discount (134.85M VND): BREACH & CONFIRMATION BLOCKED",
                                f"Breach detected: {[b for b in breaches_eff_10_1 if 'effective discount' in b]}")
        else:
            results.record_fail("5.2c Failed Breach at 10.1% Effective Discount", 
                                f"breach_found={eff_breach_10_1}, confirm_blocked={agent_eff_blocked}")

        # 5.3 Combined Stated & Effective Discount
        # price_unit = 140M (eff ~6.67%), discount = 5.0%. Net = 140M * 0.95 = 133M -> 11.33% total discount
        so_comb = SaleOrder.with_user(agent_user).create({
            'partner_id': partner.id,
            'user_id': agent_user.id,
            'order_line': [Command.create({
                'product_id': sku_starter.id,
                'product_uom_qty': 1,
                'price_unit': 140_000_000.0,
                'discount': 5.0,
            })],
        })
        breaches_comb = so_comb._al2c_threshold_breaches()
        comb_breach = any("effective discount" in b and "11.33%" in b for b in breaches_comb)
        if comb_breach:
            results.record_pass("5.3 Combined Stated + Effective Discount (11.33%) Detected", 
                                f"Breach detected: {[b for b in breaches_comb if 'effective discount' in b]}")
        else:
            results.record_fail("5.3 Combined Discount Detection Failed", f"Breaches: {breaches_comb}")

    except Exception as e:
        results.record_fail("ATTACK 5 Execution Failure", e, traceback.format_exc())

    return results


def main():
    registry = setup_odoo_env()
    results = AdversarialTestResult()
    from odoo.orm.utils import SUPERUSER_ID
    from odoo.api import Environment
    
    with registry.cursor() as cr:
        try:
            env = Environment(cr, SUPERUSER_ID, {})
            run_all_adversarial_tests(env, results)
        finally:
            cr.rollback()
            print("\n[DATABASE ISOLATION] Transaction successfully rolled back (0 permanent writes).")

    print("\n" + "=" * 80)
    print(f"ADVERSARIAL HARNESS SUMMARY: {results.tests_passed}/{results.tests_run} Passed, {results.tests_failed} Failed")
    print("=" * 80)

    if results.tests_failed > 0:
        print("\nVULNERABILITIES / FINDINGS IDENTIFIED:")
        for idx, f in enumerate(results.findings, 1):
            print(f"{idx}. [{f['test']}] {f['error']}")
            if f['detail']:
                print(f"   Detail: {f['detail']}")
        sys.exit(1)
    else:
        print("\nALL ADVERSARIAL STRESS GATES PASSED CLEANLY (Zero Governance Regressions).")
        sys.exit(0)


if __name__ == '__main__':
    main()
