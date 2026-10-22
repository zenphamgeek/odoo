#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Empirical Challenger 2 Adversarial Audit Harness:
Milestone 1 — Autonomous Scheduled Daemons (`ir.cron`) & System Parameters (`autonomous on`)
Database: insilos20_dev (PostgreSQL 127.0.0.1:5434)
"""

import sys
import os
import time

import odoo
from odoo.modules.registry import Registry
from odoo.tools import config

def run_adversarial_audit():
    print("=" * 80)
    print("STARTING EMPIRICAL CHALLENGER 2 ADVERSARIAL AUDIT")
    print("Milestone 1: Autonomous Scheduled Daemons & System Parameters")
    print("=" * 80)

    config.parse_config(['-c', 'insilos.conf', '-d', 'insilos20_dev'])
    registry = Registry.new('insilos20_dev', lock_wait=180)

    total_checks = 0
    passed_checks = 0

    def assert_check(condition, test_name, details=""):
        nonlocal total_checks, passed_checks
        total_checks += 1
        if condition:
            passed_checks += 1
            print(f"  [PASS] {test_name}: {details}")
        else:
            print(f"  [FAIL] {test_name}: {details}")
            raise AssertionError(f"Check failed: {test_name} - {details}")

    # -------------------------------------------------------------
    # 1. System Parameters Verification
    # -------------------------------------------------------------
    print("\n--- 1. System Parameters Verification ---")
    with registry.cursor() as cr:
        env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
        ICP = env['ir.config_parameter'].sudo()

        al2c_on = ICP.get_param('al2c.autonomy_enabled')
        assert_check(al2c_on == 'True', "al2c.autonomy_enabled", f"Value is '{al2c_on}' (expected 'True')")

        dgm_on = ICP.get_param('dgm.autonomy_enabled')
        assert_check(dgm_on == 'True', "dgm.autonomy_enabled", f"Value is '{dgm_on}' (expected 'True')")

        guard_model = env['al2c.autonomy.guard']
        guard_active = guard_model._dgm_autonomy_enabled()
        assert_check(guard_active is True, "al2c.autonomy.guard._dgm_autonomy_enabled()", "Guard evaluates to True")

    # -------------------------------------------------------------
    # 2. ir.cron Records & Configuration Inspection
    # -------------------------------------------------------------
    print("\n--- 2. ir.cron Records Inspection ---")
    with registry.cursor() as cr:
        env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})

        cron_triage = env.ref('insilos_al2c.ir_cron_dgm_document_triage_split', raise_if_not_found=False)
        assert_check(cron_triage is not False and cron_triage.exists(), "Cron 1 Existence", "ir_cron_dgm_document_triage_split exists")
        assert_check(cron_triage.active is True, "Cron 1 Active", "Active is True")
        assert_check(cron_triage.model_id.model == 'documents.document', "Cron 1 Model", f"Model is {cron_triage.model_id.model}")
        assert_check(cron_triage.state == 'code', "Cron 1 State", f"State is {cron_triage.state}")
        assert_check(cron_triage.code == 'model.cron_dgm_document_triage_split()', "Cron 1 Code", f"Code is {cron_triage.code}")
        assert_check(cron_triage.interval_number == 1 and cron_triage.interval_type == 'hours', "Cron 1 Interval", f"{cron_triage.interval_number} {cron_triage.interval_type}")

        cron_legal = env.ref('insilos_al2c.ir_cron_dgm_legal_entity_sla_watchdog', raise_if_not_found=False)
        assert_check(cron_legal is not False and cron_legal.exists(), "Cron 2 Existence", "ir_cron_dgm_legal_entity_sla_watchdog exists")
        assert_check(cron_legal.active is True, "Cron 2 Active", "Active is True")
        assert_check(cron_legal.model_id.model == 'al2c.compliance.scanner', "Cron 2 Model", f"Model is {cron_legal.model_id.model}")
        assert_check(cron_legal.state == 'code', "Cron 2 State", f"State is {cron_legal.state}")
        assert_check(cron_legal.code == 'model.cron_dgm_legal_entity_sla_watchdog()', "Cron 2 Code", f"Code is {cron_legal.code}")
        assert_check(cron_legal.interval_number == 1 and cron_legal.interval_type == 'hours', "Cron 2 Interval", f"{cron_legal.interval_number} {cron_legal.interval_type}")

        cron_bhxh = env.ref('insilos_al2c.ir_cron_dgm_bhxh_tk242_watchdog', raise_if_not_found=False)
        assert_check(cron_bhxh is not False and cron_bhxh.exists(), "Cron 3 Existence", "ir_cron_dgm_bhxh_tk242_watchdog exists")
        assert_check(cron_bhxh.active is True, "Cron 3 Active", "Active is True")
        assert_check(cron_bhxh.model_id.model == 'al2c.compliance.scanner', "Cron 3 Model", f"Model is {cron_bhxh.model_id.model}")
        assert_check(cron_bhxh.state == 'code', "Cron 3 State", f"State is {cron_bhxh.state}")
        assert_check(cron_bhxh.code == 'model.cron_dgm_bhxh_tk242_watchdog()', "Cron 3 Code", f"Code is {cron_bhxh.code}")
        assert_check(cron_bhxh.interval_number == 1 and cron_bhxh.interval_type == 'days', "Cron 3 Interval", f"{cron_bhxh.interval_number} {cron_bhxh.interval_type}")

    # -------------------------------------------------------------
    # 3. Direct Model Calls Execution
    # -------------------------------------------------------------
    print("\n--- 3. Direct Model Method Invocations ---")
    with registry.cursor() as cr:
        env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
        res1 = env['documents.document'].cron_dgm_document_triage_split(batch_limit=10)
        cr.commit()
        assert_check(isinstance(res1, dict) and res1.get('status') == 'success', "Model Call 1", f"cron_dgm_document_triage_split: {res1}")

    with registry.cursor() as cr:
        env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
        res2 = env['al2c.compliance.scanner'].cron_dgm_legal_entity_sla_watchdog(batch_limit=10)
        cr.commit()
        assert_check(isinstance(res2, dict) and res2.get('status') == 'success', "Model Call 2", f"cron_dgm_legal_entity_sla_watchdog: {res2}")

    with registry.cursor() as cr:
        env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
        res3 = env['al2c.compliance.scanner'].cron_dgm_bhxh_tk242_watchdog()
        cr.commit()
        assert_check(isinstance(res3, dict) and res3.get('status') == 'success', "Model Call 3", f"cron_dgm_bhxh_tk242_watchdog: {res3}")

    # -------------------------------------------------------------
    # 4. Direct Cron Trigger (c.method_direct_trigger())
    # -------------------------------------------------------------
    print("\n--- 4. c.method_direct_trigger() Invocations ---")
    with registry.cursor() as cr:
        env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
        cron_triage = env.ref('insilos_al2c.ir_cron_dgm_document_triage_split')
        t0 = time.time()
        trigger_res1 = cron_triage.method_direct_trigger()
        cr.commit()
        t1 = time.time()
        assert_check(trigger_res1 is True, "method_direct_trigger Cron 1", f"Result={trigger_res1} (elapsed {t1-t0:.2f}s)")

    with registry.cursor() as cr:
        env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
        cron_legal = env.ref('insilos_al2c.ir_cron_dgm_legal_entity_sla_watchdog')
        t0 = time.time()
        trigger_res2 = cron_legal.method_direct_trigger()
        cr.commit()
        t1 = time.time()
        assert_check(trigger_res2 is True, "method_direct_trigger Cron 2", f"Result={trigger_res2} (elapsed {t1-t0:.2f}s)")

    with registry.cursor() as cr:
        env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
        cron_bhxh = env.ref('insilos_al2c.ir_cron_dgm_bhxh_tk242_watchdog')
        t0 = time.time()
        trigger_res3 = cron_bhxh.method_direct_trigger()
        cr.commit()
        t1 = time.time()
        assert_check(trigger_res3 is True, "method_direct_trigger Cron 3", f"Result={trigger_res3} (elapsed {t1-t0:.2f}s)")

    # -------------------------------------------------------------
    # 5. Idempotency Check: Consecutive Runs Stability
    # -------------------------------------------------------------
    print("\n--- 5. Idempotency & Consecutive Runs ---")
    with registry.cursor() as cr:
        env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
        cron_triage = env.ref('insilos_al2c.ir_cron_dgm_document_triage_split')
        trigger_res1_b = cron_triage.method_direct_trigger()
        cr.commit()
        assert_check(trigger_res1_b is True, "Idempotency Cron 1 (Run 2)", f"Direct trigger Run 2 returned {trigger_res1_b}")

    with registry.cursor() as cr:
        env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
        cron_legal = env.ref('insilos_al2c.ir_cron_dgm_legal_entity_sla_watchdog')
        trigger_res2_b = cron_legal.method_direct_trigger()
        cr.commit()
        assert_check(trigger_res2_b is True, "Idempotency Cron 2 (Run 2)", f"Direct trigger Run 2 returned {trigger_res2_b}")

    with registry.cursor() as cr:
        env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
        cron_bhxh = env.ref('insilos_al2c.ir_cron_dgm_bhxh_tk242_watchdog')
        trigger_res3_b = cron_bhxh.method_direct_trigger()
        cr.commit()
        assert_check(trigger_res3_b is True, "Idempotency Cron 3 (Run 2)", f"Direct trigger Run 2 returned {trigger_res3_b}")

    with registry.cursor() as cr:
        env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
        res1_b = env['documents.document'].cron_dgm_document_triage_split(batch_limit=10)
        cr.commit()
        assert_check(res1_b.get('status') == 'success', "Model Call 1 Idempotency", f"Repeated run: {res1_b}")

    with registry.cursor() as cr:
        env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
        res2_b = env['al2c.compliance.scanner'].cron_dgm_legal_entity_sla_watchdog(batch_limit=10)
        cr.commit()
        assert_check(res2_b.get('status') == 'success', "Model Call 2 Idempotency", f"Repeated run: {res2_b}")

    with registry.cursor() as cr:
        env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
        res3_b = env['al2c.compliance.scanner'].cron_dgm_bhxh_tk242_watchdog()
        cr.commit()
        assert_check(res3_b.get('status') == 'success', "Model Call 3 Idempotency", f"Repeated run: {res3_b}")

    # -------------------------------------------------------------
    # 6. Kill-Switch Behavior Under Autonomy Disabled
    # -------------------------------------------------------------
    print("\n--- 6. Kill-Switch Stress Testing ---")
    with registry.cursor() as cr:
        env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
        ICP = env['ir.config_parameter'].sudo()
        guard_model = env['al2c.autonomy.guard']

        # Subcase 6A: dgm.autonomy_enabled = False
        ICP.set_param('dgm.autonomy_enabled', 'False')
        assert_check(guard_model._dgm_autonomy_enabled() is False, "Kill-Switch dgm=False", "Guard is False")
        skip1 = env['documents.document'].cron_dgm_document_triage_split()
        assert_check(skip1.get('status') == 'skipped', "Cron 1 Skipped on dgm=False", f"{skip1}")
        skip2 = env['al2c.compliance.scanner'].cron_dgm_legal_entity_sla_watchdog()
        assert_check(skip2.get('status') == 'skipped', "Cron 2 Skipped on dgm=False", f"{skip2}")
        skip3 = env['al2c.compliance.scanner'].cron_dgm_bhxh_tk242_watchdog()
        assert_check(skip3.get('status') == 'skipped', "Cron 3 Skipped on dgm=False", f"{skip3}")

        # Subcase 6B: al2c.autonomy_enabled = False, dgm.autonomy_enabled = True
        ICP.set_param('dgm.autonomy_enabled', 'True')
        ICP.set_param('al2c.autonomy_enabled', 'False')
        assert_check(guard_model._dgm_autonomy_enabled() is False, "Kill-Switch al2c=False", "Guard is False")
        skip1_b = env['documents.document'].cron_dgm_document_triage_split()
        assert_check(skip1_b.get('status') == 'skipped', "Cron 1 Skipped on al2c=False", f"{skip1_b}")

        # Subcase 6C: Restore parameters
        ICP.set_param('al2c.autonomy_enabled', 'True')
        ICP.set_param('dgm.autonomy_enabled', 'True')
        assert_check(guard_model._dgm_autonomy_enabled() is True, "Kill-Switch Restored", "Guard restored to True")
        cr.commit()

    # -------------------------------------------------------------
    # 7. Zero-Branding Forensic Validation
    # -------------------------------------------------------------
    print("\n--- 7. Zero-Branding Forensic Check ---")
    with registry.cursor() as cr:
        env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
        crons = [
            env.ref('insilos_al2c.ir_cron_dgm_document_triage_split'),
            env.ref('insilos_al2c.ir_cron_dgm_legal_entity_sla_watchdog'),
            env.ref('insilos_al2c.ir_cron_dgm_bhxh_tk242_watchdog'),
        ]
        for c in crons:
            name_lower = (c.name or '').lower()
            code_lower = (c.code or '').lower()
            assert_check("odoo" not in name_lower, f"Zero Branding Name {c.id}", f"Name '{c.name}' has no 'odoo'")
            assert_check("openerp" not in name_lower, f"Zero Branding Name {c.id}", f"Name '{c.name}' has no 'openerp'")
            assert_check("odoo" not in code_lower, f"Zero Branding Code {c.id}", f"Code '{c.code}' has no 'odoo'")
            assert_check("openerp" not in code_lower, f"Zero Branding Code {c.id}", f"Code '{c.code}' has no 'openerp'")

    # Check ir_cron_data.xml for user-facing strings
    cron_xml_path = '/home/zen/O20/addons/insilos_al2c/data/ir_cron_data.xml'
    with open(cron_xml_path, 'r', encoding='utf-8') as f:
        xml_lines = f.readlines()
    for idx, line in enumerate(xml_lines, 1):
        stripped = line.strip()
        if stripped.startswith('<odoo') or stripped.startswith('</odoo'):
            continue
        line_lower = line.lower()
        assert_check("odoo" not in line_lower, f"XML Zero Branding line {idx}", f"Line {idx} free of 'odoo'")
        assert_check("openerp" not in line_lower, f"XML Zero Branding line {idx}", f"Line {idx} free of 'openerp'")

    print("\n" + "=" * 80)
    print(f"AUDIT COMPLETE: {passed_checks}/{total_checks} CHECKS PASSED (100%)")
    print("=" * 80)
    return total_checks, passed_checks

if __name__ == '__main__':
    run_adversarial_audit()
