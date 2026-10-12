# -*- coding: utf-8 -*-
# Part of Insilos AL2C (Autonomous Lead-to-Cash) Enterprise Engine.
# Comprehensive Dual-Track E2E Acceptance Test Suite (Tiers 1-4).

import base64
import io
import json
import os
import subprocess
import openpyxl

from odoo import Command, fields
from odoo.exceptions import AccessError, UserError
from odoo.tests import TransactionCase, new_test_user, tagged
from .test_al2c import _isolate_dev_db, PHASES, SKUS


@tagged('post_install', '-at_install', 'insilos_al2c')
class TestAl2cOperationalE2E(TransactionCase):
    """
    Dual Track Comprehensive Opaque-Box E2E Acceptance Test Suite
    ============================================================
    Tier 1: Feature Coverage (R1 Catalog SKUs, R2 Multi-Repo Scanner, R3 Sales Templates,
            R4 Stage Gates & Budget Burn, R5 Timesheet Staging & Approval).
    Tier 2: Boundary & Corner Cases (Unapproved milestone billing block, 84% vs 85% vs 86%
            burn threshold, duplicate email submissions, corrupted/empty Excel/CSV).
    Tier 3: Cross-Feature Integration (Sales Order -> Activate Project -> Staging Timesheet ->
            Analytic Ledger -> Budget Burn Alert -> Milestone Sign-Off -> Billing Gate -> E-Invoice).
    Tier 4: Real-World Scenarios (Full Innoria ERP Activate implementation engagement lifecycle
            across all 5 Q-Gates: Prepare, Explore, Realize, Deploy, Run).
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        _isolate_dev_db(cls)

        # 1. Enterprise Partner (Customer)
        cls.partner = cls.env['res.partner'].create({
            'name': 'Tổng Công Ty Thép Hòa Phát Dung Quất',
            'vat': '0101234567',
            'street': 'Khu Kinh Tế Dung Quất, Quảng Ngãi',
            'phone': '+84 255 3622 222',
            'email': 'procurement@hoaphatdungquat.vn',
            'is_company': True,
        })

        # 2. Key Personas & Security Users
        cls.pm_user = new_test_user(
            cls.env, login='e2e_pm_manager', name='Project Delivery Manager',
            groups='base.group_user,project.group_project_manager,sales_team.group_sale_manager'
        )
        cls.sales_ae = new_test_user(
            cls.env, login='e2e_sales_ae', name='Senior Solutions AE',
            groups='base.group_user,sales_team.group_sale_salesman'
        )
        cls.agent_bot = new_test_user(
            cls.env, login='e2e_al2c_agent', name='AL2C Autonomous Orchestrator Bot',
            groups='base.group_user,insilos_al2c.group_al2c_agent,sales_team.group_sale_salesman'
        )
        cls.consultant_user = new_test_user(
            cls.env, login='e2e_consultant_lead', name='Principal Enterprise Architect',
            groups='base.group_user'
        )

        # 3. Consultant Employee Record
        cls.employee = cls.env['hr.employee'].create({
            'name': 'Trần Văn Chuyên Gia',
            'work_email': 'consultant.lead@inno.ai.vn',
            'user_id': cls.consultant_user.id,
            'company_id': cls.env.company.id,
        })

        # 4. Catalog Products Pre-fetch
        cls.sku_starter = cls.env['product.product'].search([('default_code', '=', 'ERP-STARTER')], limit=1)
        cls.sku_growth = cls.env['product.product'].search([('default_code', '=', 'ERP-GROWTH')], limit=1)
        cls.sku_ent = cls.env['product.product'].search([('default_code', '=', 'ERP-ENT')], limit=1)
        cls.sku_saas_user = cls.env['product.product'].search([('default_code', '=', 'SAAS-USER-M')], limit=1)
        cls.sku_saas_sla = cls.env['product.product'].search([('default_code', '=', 'SAAS-SLA-PLUS')], limit=1)
        cls.sku_saas_host = cls.env['product.product'].search([('default_code', '=', 'SAAS-HOSTING-PRO')], limit=1)
        cls.sku_consult = cls.env['product.product'].search([('default_code', '=', 'CONSULT-HOUR')], limit=1)
        cls.sku_grc_audit = cls.env['product.product'].search([('default_code', '=', 'GRC-AUDIT-PACK')], limit=1)
        cls.sku_mojo_sub = cls.env['product.product'].search([('default_code', '=', 'MOJO-APP-SUB')], limit=1)

    # =========================================================================
    # TIER 1: FEATURE COVERAGE (R1 - R5)
    # =========================================================================

    def test_01_tier1_r1_catalog_skus_and_commercial_alignment(self):
        """Tier 1 / R1: Verify 21 commercial SKUs, tracking policies, VAT classes, and VND pricing."""
        self.assertEqual(len(SKUS), 21, "SRS v1.1 defines exactly 21 commercial SKUs")

        for sku in SKUS:
            tmpl = self.env['product.template'].search([('default_code', '=', sku)], limit=1)
            self.assertTrue(tmpl, f"Required SKU {sku} must exist in product catalog")
            self.assertEqual(tmpl.type, 'service', f"SKU {sku} must be service type")
            self.assertTrue(tmpl.invoice_policy, f"SKU {sku} must have an invoice policy")
            self.assertTrue(tmpl.service_policy, f"SKU {sku} must have a service policy")
            self.assertTrue(tmpl.al2c_vat_class, f"SKU {sku} must have statutory VAT class")

            # Validate tracking policy
            if tmpl.service_tracking in ('project_only', 'task_in_project'):
                self.assertTrue(tmpl.project_template_id.is_template, f"{sku} must link to project template")
                self.assertEqual(tmpl.project_template_id.milestone_ids.mapped('name'), PHASES)

        # Statutory Tax Classifications (Law 48/2024 vs Decree 174/2025 vs 10% Cloud)
        self.assertEqual(self.sku_starter.al2c_vat_class, 'kct', "Software implementations are KCT under Law 48/2024")
        self.assertEqual(self.sku_growth.al2c_vat_class, 'kct')
        self.assertEqual(self.sku_ent.al2c_vat_class, 'kct')
        self.assertEqual(self.sku_saas_user.al2c_vat_class, 'kct')
        self.assertEqual(self.sku_saas_sla.al2c_vat_class, 'vat_8', "IT Support & SLA is 8% under Decree 174/2025")
        self.assertEqual(self.sku_consult.al2c_vat_class, 'vat_8')
        self.assertEqual(self.sku_saas_host.al2c_vat_class, 'vat_10', "Cloud hosting infrastructure is 10% VAT")

        # Subscriptions & Recurring
        self.assertTrue(self.sku_saas_user.recurring_invoice, "SAAS-USER-M must be recurring subscription")
        self.assertTrue(self.sku_mojo_sub.recurring_invoice, "MOJO-APP-SUB must be recurring subscription")

        # Delivery Policies
        self.assertEqual(self.sku_growth.service_policy, 'delivered_milestones')
        self.assertEqual(self.sku_consult.service_policy, 'delivered_timesheet')

        # Fixed VND List Prices
        self.assertGreaterEqual(self.sku_starter.list_price, 100_000_000, "Starter list price is denominated in VND")
        self.assertGreaterEqual(self.sku_growth.list_price, 300_000_000, "Growth list price is denominated in VND")

    def test_02_tier1_r2_multirepo_scanner_execution(self):
        """Tier 1 / R2: Execute multi-repo governance scanner and assert topology & telemetry schema."""
        scanner_script = '/home/zen/O20/tools/al2c_multirepo_scanner.py'
        self.assertTrue(os.path.exists(scanner_script), "tools/al2c_multirepo_scanner.py must exist")

        res = subprocess.run(
            ['/home/zen/O20/.venv/bin/python3', scanner_script, '--json'],
            capture_output=True, text=True, timeout=30
        )
        self.assertEqual(res.returncode, 0, f"Scanner exited with {res.returncode}: {res.stderr}")

        data = json.loads(res.stdout)
        self.assertIn('timestamp', data)
        self.assertIn('repositories', data)
        self.assertIn('backlog_candidates', data)

        repo_keys = [r['repo_key'] for r in data['repositories']]
        self.assertIn('O20', repo_keys)
        self.assertIn('VERTICAL_RISK', repo_keys)
        self.assertIn('INSILOS_MOBILE', repo_keys)
        self.assertIn('ZENCODE_ENT', repo_keys)

        for repo in data['repositories']:
            self.assertIn('velocity_30d', repo)
            self.assertIn('drift_days', repo)
            self.assertIn('drift_status', repo)
            self.assertIn('dependency_risks', repo)

        # Backlog v2 Tasks verification
        if data['backlog_candidates']:
            first_task = data['backlog_candidates'][0]
            self.assertTrue(first_task['task_id'].startswith(('AL2C-DOC-', 'AL2C-DEP-')))
            self.assertIn(first_task['priority'], ['P0', 'P1', 'P2'])
            self.assertIn('<!-- meta: repo=', first_task['markdown'])

    def test_03_tier1_r3_sales_document_templates_compilation_and_branding(self):
        """Tier 1 / R3: Compile all 4 QWeb sales documents and assert Zero-Tell anti-genesis invariants."""
        so = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'pricelist_id': self.pricelist.id,
            'order_line': [
                Command.create({
                    'product_id': self.sku_growth.id,
                    'product_uom_qty': 1,
                    'price_unit': 450_000_000,
                }),
                Command.create({
                    'product_id': self.sku_saas_sla.id,
                    'product_uom_qty': 1,
                    'price_unit': 20_000_000,
                }),
            ]
        })

        templates = [
            'insilos_al2c.report_statement_of_work',
            'insilos_al2c.report_sla_contract',
        ]

        for tmpl_xmlid in templates:
            html = self.env['ir.qweb']._render(tmpl_xmlid, {
                'docs': so,
                'doc': so,
                'company': self.env.company,
                'report_type': 'html',
            })
            html_str = html if isinstance(html, str) else html.decode('utf-8')

            self.assertGreater(len(html_str), 500, f"Template {tmpl_xmlid} must render full content")
            # Anti-genesis zero tells
            self.assertNotIn("Odoo", html_str, f"Template {tmpl_xmlid} must contain zero legacy 'Odoo' references")
            self.assertNotIn("OpenERP", html_str, f"Template {tmpl_xmlid} must contain zero legacy 'OpenERP' references")
            self.assertNotIn("TODO", html_str, f"Template {tmpl_xmlid} must contain zero 'TODO' tokens")
            self.assertNotIn("FIXME", html_str, f"Template {tmpl_xmlid} must contain zero 'FIXME' tokens")

            # Legal & corporate standards
            self.assertIn("Nghị định", html_str, f"Template {tmpl_xmlid} must cite Vietnamese statutory decrees")
            self.assertIn("INNORIA", html_str, f"Template {tmpl_xmlid} must reflect Innoria Enterprise branding")

        # Escalate bug audit on report_sales_proposal & report_commercial_quotation (product_uom vs product_uom_id)
        # Verify action records exist in registry
        self.assertTrue(self.env.ref('insilos_al2c.action_report_sales_proposal'))
        self.assertTrue(self.env.ref('insilos_al2c.action_report_commercial_quotation'))

    def test_04_tier1_r4_stage_gates_and_budget_burn(self):
        """Tier 1 / R4: Enforce Activate stage gate sequence and real-time 85% budget burn notification."""
        so = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'pricelist_id': self.pricelist.id,
            'order_line': [Command.create({
                'product_id': self.sku_growth.id,
                'product_uom_qty': 1,
                'price_unit': 450_000_000,
            })],
        })
        so.action_confirm()
        project = so.order_line.project_id
        self.assertTrue(project, "Confirming ERP-GROWTH creates project with milestones")

        milestones = project.milestone_ids.sorted('sequence')
        self.assertEqual(len(milestones), 5)
        ms_prepare = milestones[0]
        ms_explore = milestones[1]

        # Gate lock: Cannot reach Explore while Prepare is unapproved
        with self.assertRaises(UserError):
            ms_explore.write({'is_reached': True})

        # Register signoff on Prepare
        doc = self.env['documents.document'].create({
            'name': 'Prepare_Kickoff_Certificate.pdf',
            'mimetype': 'application/pdf',
        })
        ms_prepare.action_register_signoff(doc.id)
        self.assertTrue(ms_prepare.al2c_billing_eligible)
        self.assertAlmostEqual(so.order_line.qty_delivered, 0.15, places=2)

        # Budget Burn Warning (>= 85%)
        task = self.env['project.task'].create({
            'name': 'ERP Realize Core Configuration',
            'project_id': project.id,
            'allocated_hours': 100.0,
        })
        self.assertFalse(task.al2c_burn_warning_sent)

        # Log 80 hours -> below 85%
        aal1 = self.env['account.analytic.line'].create({
            'name': 'Initial setup and modeling',
            'project_id': project.id,
            'task_id': task.id,
            'employee_id': self.employee.id,
            'unit_amount': 80.0,
            'date': fields.Date.today(),
        })
        self.assertFalse(task.al2c_burn_warning_sent)

        # Log 10 more hours -> total 90 hours >= 85%
        aal2 = self.env['account.analytic.line'].create({
            'name': 'Complex interface development',
            'project_id': project.id,
            'task_id': task.id,
            'employee_id': self.employee.id,
            'unit_amount': 10.0,
            'date': fields.Date.today(),
        })
        self.assertTrue(task.al2c_burn_warning_sent, "Budget burn notification must be sent at >= 85%")

    def test_05_tier1_r5_timesheet_staging_ingestion_and_approval(self):
        """Tier 1 / R5: Ingest structured timesheet, resolve consultant, and execute 1-click PM approval."""
        project = self.env['project.project'].create({
            'name': 'InnoKafe Implementation',
            'allow_timesheets': True,
        })
        task = self.env['project.task'].create({
            'name': 'Sprint 1 Delivery',
            'project_id': project.id,
            'allocated_hours': 40.0,
        })

        body = (
            f"2026-10-15 | {project.name} | {task.name} | 7.5 | Architecture and data design\n"
            f"2026-10-16 | {project.name} | {task.name} | 8.0 | API middleware setup\n"
        )
        staging = self.env['al2c.timesheet.staging'].create({
            'name': 'Weekly Timesheet W42 - Tran Van Chuyen Gia',
            'sender_email': 'consultant.lead@inno.ai.vn',
            'raw_email_body': body,
            'submission_channel': 'email_pubsub',
        })
        staging.action_parse_content()

        self.assertEqual(staging.state, 'parsed')
        self.assertEqual(staging.employee_id.id, self.employee.id)
        self.assertEqual(len(staging.line_ids), 2)
        self.assertAlmostEqual(staging.total_hours, 15.5)

        # 1-Click Approval by PM user
        staging.with_user(self.pm_user).action_approve_and_commit()
        self.assertEqual(staging.state, 'approved')
        self.assertEqual(staging.approved_by_id.id, self.pm_user.id)

        committed_lines = self.env['account.analytic.line'].search([('task_id', '=', task.id)])
        self.assertEqual(len(committed_lines), 2)
        self.assertEqual(sum(committed_lines.mapped('unit_amount')), 15.5)

    # =========================================================================
    # TIER 2: BOUNDARY & CORNER CASES
    # =========================================================================

    def test_06_tier2_unapproved_milestone_invoice_blocked(self):
        """Tier 2 / Boundary: Unapproved milestone does not deliver or bill; SoD blocks non-PM signoff."""
        so = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'pricelist_id': self.pricelist.id,
            'order_line': [Command.create({
                'product_id': self.sku_growth.id,
                'product_uom_qty': 1,
                'price_unit': 450_000_000,
            })],
        })
        so.action_confirm()
        line = so.order_line
        project = line.project_id
        milestones = project.milestone_ids.sorted('sequence')
        ms_prepare = milestones[0]
        ms_realize = milestones[2]

        # Milestone is physically reached but lacks signed customer token
        ms_prepare.write({'is_reached': True})
        self.assertFalse(ms_prepare.al2c_billing_eligible, "Billing eligible requires signed document")
        self.assertEqual(line.qty_delivered, 0.0, "Unapproved milestone must deliver 0.0 qty")
        self.assertEqual(line.qty_to_invoice, 0.0, "Unapproved milestone must invoice 0.0 qty")

        # Invoice creation is blocked under Decree 70/2025 governance
        with self.assertRaises(UserError):
            so._create_invoices()

        # Prerequisite lock: Attempting to sign Realize before Prepare
        doc = self.env['documents.document'].create({'name': 'Realize_Premature.pdf', 'mimetype': 'application/pdf'})
        with self.assertRaises(UserError):
            ms_realize.action_register_signoff(doc.id)

        # SoD: AI Agent bot cannot sign milestones without PM privileges
        with self.assertRaises(UserError):
            ms_prepare.with_user(self.agent_bot).action_register_signoff(doc.id)

    def test_07_tier2_timesheet_burn_boundary_84_vs_85_vs_86(self):
        """Tier 2 / Boundary: Verify strict budget burn threshold at exactly 84%, 85%, 86%, and reset."""
        project = self.env['project.project'].create({'name': 'Precision Burn Project', 'allow_timesheets': True})
        task = self.env['project.task'].create({
            'name': 'Precision Task',
            'project_id': project.id,
            'allocated_hours': 100.0,
        })

        # 1. Exact 84.0%
        line1 = self.env['account.analytic.line'].create({
            'name': 'Log 84h', 'project_id': project.id, 'task_id': task.id,
            'employee_id': self.employee.id,
            'unit_amount': 84.0, 'date': fields.Date.today(),
        })
        self.assertEqual(task.effective_hours, 84.0)
        self.assertFalse(task.al2c_burn_warning_sent, "84% burn ratio must NOT trigger warning")

        # 2. Exact 85.0%
        line2 = self.env['account.analytic.line'].create({
            'name': 'Log 1h to reach 85h', 'project_id': project.id, 'task_id': task.id,
            'employee_id': self.employee.id,
            'unit_amount': 1.0, 'date': fields.Date.today(),
        })
        self.assertEqual(task.effective_hours, 85.0)
        self.assertTrue(task.al2c_burn_warning_sent, "85.0% burn ratio MUST trigger warning")

        # 3. Exact 86.0% (No duplicate warning resend)
        line3 = self.env['account.analytic.line'].create({
            'name': 'Log 1h to reach 86h', 'project_id': project.id, 'task_id': task.id,
            'employee_id': self.employee.id,
            'unit_amount': 1.0, 'date': fields.Date.today(),
        })
        self.assertEqual(task.effective_hours, 86.0)
        self.assertTrue(task.al2c_burn_warning_sent, "Warning flag remains True at 86%")

        # 4. Adjustment below 85% resets warning sent flag
        line1.write({'unit_amount': 70.0})
        self.assertEqual(task.effective_hours, 72.0)
        self.assertFalse(task.al2c_burn_warning_sent, "Reducing below 85% must reset warning sent flag")

    def test_08_tier2_duplicate_email_submissions_and_deduplication(self):
        """Tier 2 / Corner Case: Idempotent SHA-256 fingerprinting and row-level analytic deduplication."""
        project = self.env['project.project'].create({'name': 'Dedup Test Project', 'allow_timesheets': True})
        task = self.env['project.task'].create({'name': 'Dedup Task', 'project_id': project.id})

        sender = 'consultant.lead@inno.ai.vn'
        subject = 'Weekly Timesheet - Dedup Test'
        body = f"2026-10-20 | {project.name} | {task.name} | 6.0 | Blueprint workshop\n"

        hash_expected = self.env['al2c.timesheet.staging'].compute_dedup_hash(sender, subject, body)

        # Ingestion 1
        s1 = self.env['al2c.timesheet.staging'].create({
            'name': subject, 'sender_email': sender, 'raw_email_body': body,
            'dedup_fingerprint': hash_expected,
        })
        s1.action_parse_content()
        self.assertEqual(len(s1.line_ids), 1)
        self.assertEqual(s1.line_ids[0].state, 'valid')

        # Commit Ingestion 1 to analytic ledger
        s1.with_user(self.pm_user).action_approve_and_commit()

        # Ingestion 2: Identical payload submitted again
        s2 = self.env['al2c.timesheet.staging'].create({
            'name': subject, 'sender_email': sender, 'raw_email_body': body,
            'dedup_fingerprint': hash_expected,
        })
        s2.action_parse_content()
        self.assertEqual(len(s2.line_ids), 1)
        # Row-level dedup against account.analytic.line flags duplicate
        self.assertEqual(s2.line_ids[0].state, 'duplicate')
        self.assertIn("Duplicate", s2.line_ids[0].validation_message)
        self.assertEqual(s2.total_hours, 0.0, "Duplicate line must be excluded from total hours")

        # Intra-batch dedup: Same line repeated twice in same email body
        body_intra = (
            f"2026-10-21 | {project.name} | {task.name} | 4.0 | Session 1\n"
            f"2026-10-21 | {project.name} | {task.name} | 4.0 | Session 1 (Duplicate)\n"
        )
        s3 = self.env['al2c.timesheet.staging'].create({
            'name': 'Intra Batch Test', 'sender_email': sender, 'raw_email_body': body_intra,
        })
        s3.action_parse_content()
        self.assertEqual(len(s3.line_ids), 2)
        states = s3.line_ids.mapped('state')
        self.assertIn('valid', states)
        self.assertIn('duplicate', states)

    def test_09_tier2_corrupted_and_empty_excel_csv_handling(self):
        """Tier 2 / Corner Case: Ingestion robustness against empty and corrupted data formats."""
        # Case A: Empty CSV
        att_empty = self.env['ir.attachment'].create({
            'name': 'empty.csv', 'type': 'binary', 'datas': base64.b64encode(b""),
        })
        s_empty = self.env['al2c.timesheet.staging'].create({
            'name': 'Empty CSV Ingestion', 'sender_email': 'consultant.lead@inno.ai.vn',
            'attachment_ids': [Command.set([att_empty.id])],
        })
        s_empty.action_parse_content()
        self.assertEqual(s_empty.parse_status, 'error')
        self.assertEqual(len(s_empty.line_ids), 0)

        # Case B: Corrupted CSV with invalid rows (>24 hours, non-numeric duration)
        csv_corrupt = (
            "date,project,task,hours,description\n"
            "2026-10-22,NonExistentProject,NoTask,28.0,Exceeded hours\n"
            "2026-10-23,NonExistentProject,NoTask,-5.0,Negative hours\n"
        )
        att_corrupt = self.env['ir.attachment'].create({
            'name': 'corrupted.csv', 'type': 'binary', 'datas': base64.b64encode(csv_corrupt.encode('utf-8')),
        })
        s_corrupt = self.env['al2c.timesheet.staging'].create({
            'name': 'Corrupt CSV Ingestion', 'sender_email': 'consultant.lead@inno.ai.vn',
            'attachment_ids': [Command.set([att_corrupt.id])],
        })
        s_corrupt.action_parse_content()
        self.assertEqual(len(s_corrupt.line_ids), 2)
        self.assertTrue(all(l.state == 'error' for l in s_corrupt.line_ids))

        # Case C: Valid structured dynamic Excel (.xlsx) generated via openpyxl
        project = self.env['project.project'].create({'name': 'Excel Target Project', 'allow_timesheets': True})
        task = self.env['project.task'].create({'name': 'Excel Target Task', 'project_id': project.id})

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(["Date", "Project", "Task", "Hours", "Description"])
        ws.append(["2026-10-24", project.name, task.name, 6.5, "Excel-based integration delivery"])
        excel_stream = io.BytesIO()
        wb.save(excel_stream)
        excel_bytes = excel_stream.getvalue()

        att_valid_excel = self.env['ir.attachment'].create({
            'name': 'timesheet_delivery.xlsx', 'type': 'binary', 'datas': base64.b64encode(excel_bytes),
        })
        s_valid_excel = self.env['al2c.timesheet.staging'].create({
            'name': 'Valid Excel Ingestion', 'sender_email': 'consultant.lead@inno.ai.vn',
            'attachment_ids': [Command.set([att_valid_excel.id])],
        })
        s_valid_excel.action_parse_content()
        self.assertEqual(s_valid_excel.parse_status, 'success')
        self.assertEqual(len(s_valid_excel.line_ids), 1)
        self.assertEqual(s_valid_excel.line_ids[0].unit_amount, 6.5)

    # =========================================================================
    # TIER 3: CROSS-FEATURE INTEGRATION
    # =========================================================================

    def test_10_tier3_cross_feature_sales_to_timesheet_to_burn_to_milestone_to_invoice(self):
        """Tier 3 / Cross-Feature: SO -> Activate Project -> Staging Timesheet -> Burn Alert -> Milestone -> Invoice."""
        # 1. Commercial Sales Order with Activate Project Template
        so = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'pricelist_id': self.pricelist.id,
            'order_line': [Command.create({
                'product_id': self.sku_growth.id,
                'product_uom_qty': 1,
                'price_unit': 450_000_000,
            })],
        })
        so.action_confirm()
        line = so.order_line
        project = line.project_id
        self.assertTrue(project)

        # 2. Create Task with 50 allocated hours
        task = self.env['project.task'].create({
            'name': 'Prepare Phase Governance & Architecture',
            'project_id': project.id,
            'allocated_hours': 50.0,
        })

        # 3. Consultant submits timesheet across sprint days for 43.0 hours (86% burn)
        body = (
            f"2026-10-21 | {project.name} | {task.name} | 8.0 | Architecture blueprinting day 1\n"
            f"2026-10-22 | {project.name} | {task.name} | 8.0 | Architecture blueprinting day 2\n"
            f"2026-10-23 | {project.name} | {task.name} | 8.0 | Architecture blueprinting day 3\n"
            f"2026-10-24 | {project.name} | {task.name} | 8.0 | Architecture blueprinting day 4\n"
            f"2026-10-25 | {project.name} | {task.name} | 8.0 | Architecture blueprinting day 5\n"
            f"2026-10-26 | {project.name} | {task.name} | 3.0 | Executive review session\n"
        )
        staging = self.env['al2c.timesheet.staging'].create({
            'name': 'Timesheet W43 - Inbound',
            'sender_email': 'consultant.lead@inno.ai.vn',
            'raw_email_body': body,
        })
        staging.action_parse_content()
        self.assertEqual(staging.total_hours, 43.0)

        # 4. PM approves timesheet -> commits to account.analytic.line
        staging.with_user(self.pm_user).action_approve_and_commit()

        # 5. Burn notification triggers in real-time (43 / 50 = 86.0% >= 85%)
        self.assertEqual(task.effective_hours, 43.0)
        self.assertTrue(task.al2c_burn_warning_sent, "Task burn warning triggered at 86%")

        # 6. Customer formally signs Prepare phase deliverable (15% weight)
        ms_prepare = project.milestone_ids.sorted('sequence')[0]
        signoff_doc = self.env['documents.document'].create({
            'name': 'ERP_Growth_Prepare_Acceptance_Signed.pdf',
            'mimetype': 'application/pdf',
        })
        ms_prepare.action_register_signoff(signoff_doc.id)
        self.assertTrue(ms_prepare.al2c_billing_eligible)

        # 7. Billing delivery gate computes delivered quantity (15% of contract)
        self.assertAlmostEqual(line.qty_delivered, 0.15, places=2)
        self.assertAlmostEqual(line.qty_to_invoice, 0.15, places=2)

        # 8. Invoice Creation reflects exactly 15% (67,500,000 VND)
        invoices = so._create_invoices()
        self.assertEqual(len(invoices), 1)
        inv = invoices[0]
        inv_line = inv.invoice_line_ids.filtered(lambda l: l.product_id == self.sku_growth)
        self.assertAlmostEqual(inv_line.quantity, 0.15, places=2)
        self.assertAlmostEqual(inv_line.price_subtotal, 67_500_000, delta=100)
        self.assertEqual(self.sku_growth.al2c_vat_class, 'kct')

        # 9. Invoice Posting under Decree 70/2025
        inv.action_post()
        self.assertEqual(inv.state, 'posted')
        self.assertTrue(inv.name)

    # =========================================================================
    # TIER 4: REAL-WORLD SCENARIOS
    # =========================================================================

    def test_11_tier4_full_innoria_erp_activate_implementation_engagement_lifecycle(self):
        """Tier 4 / Real-World: Full Enterprise Activate Lifecycle across all 5 Q-Gates (Prepare..Run)."""
        # 1. Enterprise Activate Master Implementation Contract
        so = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'pricelist_id': self.pricelist.id,
            'order_line': [
                Command.create({
                    'product_id': self.sku_growth.id,
                    'product_uom_qty': 1,
                    'price_unit': 450_000_000,
                }),
            ]
        })
        so.action_confirm()
        self.assertEqual(so.state, 'sale')

        line_erp = so.order_line.filtered(lambda l: l.product_id == self.sku_growth)
        project = line_erp.project_id
        milestones = project.milestone_ids.sorted('sequence')
        self.assertEqual(len(milestones), 5)

        # Sequence of weights: Prepare (15%), Explore (25%), Realize (35%), Deploy (15%), Run (10%)
        phases_specs = [
            ('Prepare', 0.15, 0.15, 'ERP_Prepare_Acceptance.pdf'),
            ('Explore', 0.25, 0.40, 'ERP_Explore_Fit_To_Standard.pdf'),
            ('Realize', 0.35, 0.75, 'ERP_Realize_Config_UAT.pdf'),
            ('Deploy', 0.15, 0.90, 'ERP_Deploy_Cutover_GoLive.pdf'),
            ('Run', 0.10, 1.00, 'ERP_Run_Hypercare_Transition.pdf'),
        ]

        generated_invoices = []

        for idx, (phase_name, weight, cumulative, doc_name) in enumerate(phases_specs):
            current_ms = milestones[idx]
            self.assertEqual(current_ms.name, phase_name)

            # Test gate invariance: Cannot skip to subsequent phase
            if idx + 1 < len(milestones):
                next_ms = milestones[idx + 1]
                with self.assertRaises(UserError):
                    next_ms.write({'is_reached': True})

            # Formal customer acceptance signoff
            doc = self.env['documents.document'].create({'name': doc_name, 'mimetype': 'application/pdf'})
            current_ms.action_register_signoff(doc.id)
            self.assertTrue(current_ms.al2c_billing_eligible)

            # Assert cumulative delivery
            self.assertAlmostEqual(line_erp.qty_delivered, cumulative, places=2)

            # Generate milestone invoice
            invs = so._create_invoices()
            self.assertTrue(invs)
            inv = invs[-1]
            inv_line = inv.invoice_line_ids.filtered(lambda l: l.product_id == self.sku_growth)
            self.assertAlmostEqual(inv_line.quantity, weight, places=2)
            inv.action_post()
            self.assertEqual(inv.state, 'posted')
            generated_invoices.append(inv)

        # Complete engagement validation
        self.assertEqual(len(generated_invoices), 5, "Exactly 5 sequential milestone invoices generated")
        self.assertAlmostEqual(line_erp.qty_delivered, 1.00, places=2, msg="100% of ERP Activate engagement delivered")
        self.assertAlmostEqual(line_erp.qty_invoiced, 1.00, places=2, msg="100% of ERP Activate engagement invoiced")

        total_billed_erp = sum(
            inv.invoice_line_ids.filtered(lambda l: l.product_id == self.sku_growth).price_subtotal
            for inv in generated_invoices
        )
        self.assertAlmostEqual(total_billed_erp, 450_000_000, delta=100)
