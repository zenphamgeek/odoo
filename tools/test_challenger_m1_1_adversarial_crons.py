#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Challenger 1 Adversarial Challenge & Stress-Test Harness:
Milestone 1 — Autonomous Scheduled Daemons (`ir.cron`) & System Parameters (`autonomous on`)
Target Database: insilos20_dev (PostgreSQL 127.0.0.1:5434)
Platform: Insilos 20 LTS

Author: Empirical Challenger 1 (`challenger_m1_1`)
Date: 2026-10-14
"""

import sys
import os
import io
import re
import datetime
import traceback
import base64

import odoo
from odoo.modules.registry import Registry
from odoo.tools import config
from odoo.tools.pdf import PdfFileReader, PdfFileWriter
from odoo import fields

def generate_minimal_pdf_bytes(num_pages=1):
    """Generates valid minimal in-memory PDF with specified number of pages."""
    try:
        from reportlab.pdfgen import canvas
        buf = io.BytesIO()
        c = canvas.Canvas(buf)
        for i in range(num_pages):
            c.drawString(100, 700, f"DGM Page {i+1} Test Content")
            c.showPage()
        c.save()
        buf.seek(0)
        return buf.read()
    except ImportError:
        header = b"%PDF-1.4\n"
        return header + b"1 0 obj <</Type /Catalog /Pages 2 0 R>> endobj\n"


def run_challenger_audit():
    print("=" * 80)
    print("CHALLENGER 1: ADVERSARIAL STRESS-TEST HARNESS")
    print("Milestone 1: Autonomous Scheduled Daemons (ir.cron) & Autonomy Kill-Switches")
    print("=" * 80)

    config.parse_config(['-c', 'insilos.conf', '-d', 'insilos20_dev'])
    registry = Registry('insilos20_dev')

    total_assertions = 0
    passed_assertions = 0
    failed_assertions = []

    def check(condition, test_name, details=""):
        nonlocal total_assertions, passed_assertions, failed_assertions
        total_assertions += 1
        if condition:
            passed_assertions += 1
            print(f"  [PASS] {test_name}: {details}")
        else:
            print(f"  [FAIL] {test_name}: {details}")
            failed_assertions.append(f"{test_name}: {details}")

    with registry.cursor() as cr:
        env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
        ICP = env['ir.config_parameter'].sudo()
        guard = env['al2c.autonomy.guard']
        Doc = env['documents.document'].sudo()
        Scanner = env['al2c.compliance.scanner'].sudo()

        # Save baseline configuration
        orig_al2c = ICP.get_param('al2c.autonomy_enabled', 'True')
        orig_dgm = ICP.get_param('dgm.autonomy_enabled', 'True')

        try:
            # =========================================================================
            # SECTION 1: Kill-Switch & Parameter Edge Cases Matrix
            # =========================================================================
            print("\n>>> SECTION 1: Autonomy Kill-Switch Matrix & Invalid String Probing <<<")

            falsy_cases = [
                ('False', "Standard string 'False'"),
                ('false', "Lowercase string 'false'"),
                ('0', "Numeric string '0'"),
                ('', "Empty string ''"),
                ('no', "Negative string 'no'"),
                ('off', "Negative string 'off'"),
                (' off ', "Whitespace padded ' off '"),
                ('DISABLED', "Arbitrary invalid string 'DISABLED'"),
                ('random_invalid', "Garbage string 'random_invalid'"),
            ]

            for val, desc in falsy_cases:
                ICP.set_param('dgm.autonomy_enabled', val)
                guard_eval = guard._dgm_autonomy_enabled()
                check(guard_eval is False, f"Guard with dgm.autonomy_enabled={val!r}", f"{desc} evaluated to False")

                # Verify all 3 crons return skipped
                res_triage = Doc.cron_dgm_document_triage_split()
                check(res_triage.get('status') == 'skipped' and res_triage.get('reason') == 'autonomy_disabled',
                      f"Cron 1 Skip on {val!r}", f"res={res_triage}")

                res_legal = Scanner.cron_dgm_legal_entity_sla_watchdog()
                check(res_legal.get('status') == 'skipped' and res_legal.get('reason') == 'autonomy_disabled',
                      f"Cron 2 Skip on {val!r}", f"res={res_legal}")

                res_bhxh = Scanner.cron_dgm_bhxh_tk242_watchdog()
                check(res_bhxh.get('status') == 'skipped' and res_bhxh.get('reason') == 'autonomy_disabled',
                      f"Cron 3 Skip on {val!r}", f"res={res_bhxh}")

            # Test Global Kill-Switch (al2c.autonomy_enabled = False while dgm = True)
            ICP.set_param('dgm.autonomy_enabled', 'True')
            ICP.set_param('al2c.autonomy_enabled', 'False')
            check(guard._dgm_autonomy_enabled() is False, "Global al2c=False guard check", "Evaluates to False")
            check(Doc.cron_dgm_document_triage_split().get('status') == 'skipped', "Cron 1 Skip on Global al2c=False", "Skipped")
            check(Scanner.cron_dgm_legal_entity_sla_watchdog().get('status') == 'skipped', "Cron 2 Skip on Global al2c=False", "Skipped")
            check(Scanner.cron_dgm_bhxh_tk242_watchdog().get('status') == 'skipped', "Cron 3 Skip on Global al2c=False", "Skipped")

            # Test Truthy Matrix
            truthy_cases = ['True', 'true', '1', 'yes', 'on', ' YES ', ' ON ']
            for t_val in truthy_cases:
                ICP.set_param('al2c.autonomy_enabled', 'True')
                ICP.set_param('dgm.autonomy_enabled', t_val)
                check(guard._dgm_autonomy_enabled() is True, f"Truthy guard check for {t_val!r}", "Evaluates to True")

            # Restore operational status
            ICP.set_param('al2c.autonomy_enabled', 'True')
            ICP.set_param('dgm.autonomy_enabled', 'True')
            check(guard._dgm_autonomy_enabled() is True, "Guard restored to operational state", "True")

            # =========================================================================
            # SECTION 2: ir.cron XML Registration & Invariant Checks
            # =========================================================================
            print("\n>>> SECTION 2: ir.cron Declarations & Model Bindings <<<")
            cron_xml_ids = [
                ('insilos_al2c.ir_cron_dgm_document_triage_split', 'documents.document', 'model.cron_dgm_document_triage_split()'),
                ('insilos_al2c.ir_cron_dgm_legal_entity_sla_watchdog', 'al2c.compliance.scanner', 'model.cron_dgm_legal_entity_sla_watchdog()'),
                ('insilos_al2c.ir_cron_dgm_bhxh_tk242_watchdog', 'al2c.compliance.scanner', 'model.cron_dgm_bhxh_tk242_watchdog()'),
            ]

            for xml_id, expected_model, expected_code in cron_xml_ids:
                c = env.ref(xml_id, raise_if_not_found=False)
                check(c is not False and c.exists(), f"Cron {xml_id} exists", f"Found ID {c.id if c else None}")
                check(c.active is True, f"Cron {xml_id} active", "Active = True")
                check(c.model_id.model == expected_model, f"Cron {xml_id} model binding", f"Bound to {c.model_id.model}")
                check(c.code == expected_code, f"Cron {xml_id} execution code", f"Code: {c.code}")

            # =========================================================================
            # SECTION 3: cron_dgm_document_triage_split Stress Testing
            # =========================================================================
            print("\n>>> SECTION 3: Document Triage & Split Watchdog Stress Testing <<<")

            # Test 3.1: Empty Folder / Zero unrouted documents
            print("  --- Subtest 3.1: Zero unrouted documents handling ---")
            res_triage_empty = Doc.cron_dgm_document_triage_split(batch_limit=0)
            check(isinstance(res_triage_empty, dict) and res_triage_empty.get('status') == 'success',
                  "Triage with batch_limit=0", f"Output: {res_triage_empty}")
            check(res_triage_empty.get('scanned') == 0, "Triage batch_limit=0 scanned=0", "0 scanned")

            # Test 3.2: Hostile / Corrupted Documents Injection
            print("  --- Subtest 3.2: Adversarial & Corrupt Documents Ingestion ---")
            with cr.savepoint():
                # Document A: Corrupted non-PDF claiming to be application/pdf
                doc_corrupt_pdf = Doc.create({
                    'name': 'adversarial_corrupt.pdf',
                    'mimetype': 'application/pdf',
                    'raw': b'GARBAGE_NOT_A_VALID_PDF_HEADER_DATA_STREAM',
                })
                # Verify _get_is_multipage does not throw uncaught exception
                is_multi = doc_corrupt_pdf._get_is_multipage()
                check(is_multi is False, "Corrupt PDF _get_is_multipage graceful fallback", f"Result={is_multi}")

                # Document B: Null/empty payload and missing fields
                doc_null_payload = Doc.create({
                    'name': 'empty_payload.bin',
                    'raw': False,
                    'datas': False,
                    'mimetype': False,
                })
                check(doc_null_payload._get_is_multipage() is None, "Null payload _get_is_multipage", "Returns None for non-PDF")

                # Document C: Binary malformed bytes claiming text/plain
                doc_malformed_text = Doc.create({
                    'name': 'malformed_binary.txt',
                    'mimetype': 'text/plain',
                    'raw': b'\xff\xfe\x00\x80\x99\xff\xaa\xbb\xcc',
                })

                # Document D: SQL Injection / XSS injection attempt in name
                doc_injection = Doc.create({
                    'name': "<script>alert('pwned');</script>'; DROP TABLE documents_document; --",
                    'mimetype': 'text/plain',
                    'raw': b'Some innocent content for injection test',
                })

                # Document E: Valid 2-page PDF
                pdf_2page_bytes = generate_minimal_pdf_bytes(num_pages=2)
                doc_2page = Doc.create({
                    'name': 'valid_multipage_2p.pdf',
                    'mimetype': 'application/pdf',
                    'raw': pdf_2page_bytes,
                })
                check(doc_2page._get_is_multipage() is True, "Valid 2-page PDF detection", "Returns True")

                # Run classify_dgm_document directly on batch of adversarial docs
                adv_docs = doc_corrupt_pdf | doc_null_payload | doc_malformed_text | doc_injection | doc_2page
                classify_ok = adv_docs.classify_dgm_document()
                check(classify_ok is True, "classify_dgm_document() on hostile batch", "Completed with True")

                # Assert that 2-page doc got 'To Split' tag
                split_tag = env.ref('insilos_al2c.tag_document_to_split', raise_if_not_found=False)
                if not split_tag:
                    split_tag = env['documents.tag'].search([('name', '=ilike', 'To Split')], limit=1)
                check(split_tag in doc_2page.tag_ids, "2-page doc received 'To Split' tag", f"Tags: {doc_2page.tag_ids.mapped('name')}")

                # Run daemon cron_dgm_document_triage_split over these documents
                res_cron_adv = Doc.cron_dgm_document_triage_split(batch_limit=50)
                check(res_cron_adv.get('status') == 'success', "cron_dgm_document_triage_split over hostile batch", f"Output: {res_cron_adv}")

            # =========================================================================
            # SECTION 4: cron_dgm_legal_entity_sla_watchdog Stress Testing
            # =========================================================================
            print("\n>>> SECTION 4: Legal Entity & 24h Export SLA Watchdog Stress Testing <<<")

            # Test 4.1: Zero records scan
            res_legal_zero = Scanner.cron_dgm_legal_entity_sla_watchdog(batch_limit=0)
            check(isinstance(res_legal_zero, dict) and res_legal_zero.get('status') == 'success',
                  "Legal watchdog with batch_limit=0", f"Output: {res_legal_zero}")
            check(res_legal_zero.get('documents_scanned') == 0, "batch_limit=0 scanned 0 docs", "0 scanned")

            # Test 4.2: Adversarial Patterns Probing
            print("  --- Subtest 4.2: Obfuscated Legacy Entity Signatures ---")
            with cr.savepoint():
                # Test obfuscated legacy VAT variants
                vat_variants = [
                    ('0313.683.499', "Dotted VAT"),
                    ('0313-683-499', "Hyphenated VAT"),
                    ('0313 683 499', "Spaced VAT"),
                    ('0313683499', "Continuous VAT"),
                ]
                for vat_str, desc in vat_variants:
                    t_doc = Doc.create({
                        'name': f'test_vat_{desc}.txt',
                        'mimetype': 'text/plain',
                        'raw': f"Mã số thuế bên A: {vat_str}".encode('utf-8'),
                    })
                    scan_res = Scanner.scan_document(t_doc)
                    check(scan_res.get('is_compliant') is False, f"Detection of {desc} ({vat_str})", f"Deviations={scan_res.get('deviations')}")

                # Test obfuscated legacy entity names
                entity_variants = [
                    "CÔNG TY TNHH ỨNG DỤNG SÁNG TẠO",
                    "ung dung sang tao llc",
                    "Công ty TNHH Sáng Tạo Ứng Dụng",
                ]
                for ent_name in entity_variants:
                    t_doc = Doc.create({
                        'name': 'test_entity.txt',
                        'mimetype': 'text/plain',
                        'raw': f"Tên đơn vị: {ent_name}".encode('utf-8'),
                    })
                    scan_res = Scanner.scan_document(t_doc)
                    check(scan_res.get('is_compliant') is False, f"Detection of entity '{ent_name}'", f"Deviations={scan_res.get('deviations')}")

                # Test Outdated Ward
                t_doc_ward = Doc.create({
                    'name': 'test_ward.txt',
                    'mimetype': 'text/plain',
                    'raw': b"Dia chi: So 123, Phuong Tan Phu, Quan 7, TP.HCM",
                })
                scan_res_ward = Scanner.scan_document(t_doc_ward)
                check(scan_res_ward.get('is_compliant') is False, "Detection of Outdated Ward (Phường Tân Phú)", f"Deviations={scan_res_ward.get('deviations')}")

                # Test Canonical Entity Document (Must Pass as Compliant)
                t_doc_canonical = Doc.create({
                    'name': 'canonical_dgm.txt',
                    'mimetype': 'text/plain',
                    'raw': b"Cong ty Co phan Nguoi Ban So, MST: 0317958465, Phuong Tan My, Quan 7",
                })
                scan_res_canonical = Scanner.scan_document(t_doc_canonical)
                check(scan_res_canonical.get('is_compliant') is True, "Canonical DGM Entity Document Compliance", "is_compliant=True")

                # Test 4.3: Foreign Remittance 24h SLA Breaches
                print("  --- Subtest 4.3: Foreign Remittance 24h SLA Logic ---")
                Move = env['account.move'].sudo()
                Currency = env['res.currency'].sudo()
                usd_curr = Currency.search([('name', '=', 'USD')], limit=1)
                canva_partner = env['res.partner'].search([('name', 'ilike', 'Canva')], limit=1)
                if not canva_partner:
                    canva_partner = env['res.partner'].create({'name': 'Canva Pty Ltd (Challenger Test)'})

                two_days_ago = fields.Datetime.now() - datetime.timedelta(hours=48)
                six_hours_ago = fields.Datetime.now() - datetime.timedelta(hours=6)

                # Move 1: Breached (48h old, no e-invoice number)
                move_breached = Move.create({
                    'move_type': 'entry',
                    'ref': 'Canva Inward Wire Wire-2026-001',
                    'partner_id': canva_partner.id,
                    'currency_id': usd_curr.id if usd_curr else False,
                    'al2c_is_foreign_remittance': True,
                    'al2c_bank_credit_date': two_days_ago,
                    'al2c_einvoice_number': False,
                    'al2c_einvoice_state': 'draft',
                })

                # Move 2: Compliant (6h old, within 24h SLA)
                move_recent = Move.create({
                    'move_type': 'entry',
                    'ref': 'Canva Inward Wire Wire-2026-002',
                    'partner_id': canva_partner.id,
                    'currency_id': usd_curr.id if usd_curr else False,
                    'al2c_is_foreign_remittance': True,
                    'al2c_bank_credit_date': six_hours_ago,
                    'al2c_einvoice_number': False,
                    'al2c_einvoice_state': 'draft',
                })

                # Move 3: Compliant (48h old, but e-invoice issued)
                move_issued = Move.create({
                    'move_type': 'entry',
                    'ref': 'Canva Inward Wire Wire-2026-003',
                    'partner_id': canva_partner.id,
                    'currency_id': usd_curr.id if usd_curr else False,
                    'al2c_is_foreign_remittance': True,
                    'al2c_bank_credit_date': two_days_ago,
                    'al2c_einvoice_number': '1C25TBS-0000099',
                    'al2c_einvoice_state': 'issued',
                })

                sla_res = Scanner.scan_export_invoices_sla(hours_threshold=24)
                check(move_breached in sla_res.get('breached_moves'), "SLA Scanner caught 48h uninvoiced move", "Breached")
                check(move_recent not in sla_res.get('breached_moves'), "SLA Scanner spared <24h move", "Spared")
                check(move_issued not in sla_res.get('breached_moves'), "SLA Scanner spared issued e-invoice move", "Spared")

            # =========================================================================
            # SECTION 5: cron_dgm_bhxh_tk242_watchdog Stress Testing
            # =========================================================================
            print("\n>>> SECTION 5: BHXH (TZ0857G) Zero-Arrears & TK 242 Watchdog Stress Testing <<<")

            # Test 5.1: Live Watchdog Execution
            res_bhxh_live = Scanner.cron_dgm_bhxh_tk242_watchdog()
            check(res_bhxh_live.get('status') == 'success', "cron_dgm_bhxh_tk242_watchdog live execution", f"Output: {res_bhxh_live}")
            check('bhxh_zero_arrears_verified' in res_bhxh_live, "bhxh_zero_arrears_verified key present", "Present")
            check(res_bhxh_live.get('tk242_schedules_checked') == 2, "2 TK 242 schedules monitored", "VNPT and Viettel-CA")

            # Test 5.2: Injected BHXH C12-TS with outstanding debt ([Đ.2.2] > 0)
            with cr.savepoint():
                doc_debt = Doc.create({
                    'name': 'C12-TS_TZ0857G_Thang09_2026_Arrears.pdf',
                    'folder_id': 3248 if Doc.browse(3248).exists() else False,
                    'mimetype': 'text/plain',
                    'raw': "Thông báo kết quả đóng BHXH TZ0857G tháng 09/2026. Dòng [Đ.2.2] Số tiền còn nợ: 15.420.000 đồng.".encode('utf-8'),
                })
                res_bhxh_debt = Scanner.cron_dgm_bhxh_tk242_watchdog()
                check(res_bhxh_debt.get('bhxh_zero_arrears_verified') is False,
                      "Watchdog flagged outstanding C12-TS arrears",
                      f"Alerts={res_bhxh_debt.get('bhxh_alerts')}")

            # =========================================================================
            # SECTION 6: Zero-Branding Forensic Integrity
            # =========================================================================
            print("\n>>> SECTION 6: Zero-Branding Forensic Scrutiny <<<")
            crons = env['ir.cron'].search([('name', 'ilike', 'DGM Autonomous')])
            check(len(crons) == 3, "Exactly 3 DGM Autonomous crons exist", f"Found: {len(crons)}")
            for c in crons:
                for attr, val in [('name', c.name), ('code', c.code)]:
                    check('odoo' not in (val or '').lower(), f"Zero 'odoo' in cron {c.id} {attr}", f"Val={val}")
                    check('openerp' not in (val or '').lower(), f"Zero 'openerp' in cron {c.id} {attr}", f"Val={val}")

            # Audit ir_cron_data.xml for user-facing texts
            xml_path = '/home/zen/O20/addons/insilos_al2c/data/ir_cron_data.xml'
            with open(xml_path, 'r', encoding='utf-8') as f:
                content = f.read()
            for line in content.splitlines():
                line_str = line.strip()
                if line_str.startswith('<odoo') or line_str.startswith('</odoo'):
                    continue
                check('odoo' not in line_str.lower(), f"Zero 'odoo' in ir_cron_data.xml line", f"'{line_str[:50]}'")
                check('openerp' not in line_str.lower(), f"Zero 'openerp' in ir_cron_data.xml line", f"'{line_str[:50]}'")

            # Check al2c_tech_asset_data.xml line 11
            asset_xml_path = '/home/zen/O20/addons/insilos_al2c/data/al2c_tech_asset_data.xml'
            with open(asset_xml_path, 'r', encoding='utf-8') as f:
                asset_lines = f.readlines()
            if len(asset_lines) >= 11:
                line_11 = asset_lines[10]
                check('odoo' not in line_11.lower(), "al2c_tech_asset_data.xml line 11 sanitized", f"Line 11: {line_11.strip()}")

        finally:
            # Guarantee rollback / restoration of system parameters
            ICP.set_param('al2c.autonomy_enabled', orig_al2c)
            ICP.set_param('dgm.autonomy_enabled', orig_dgm)
            cr.rollback()  # Rollback all test database mutations

    print("\n" + "=" * 80)
    print(f"CHALLENGER 1 ADVERSARIAL STRESS-TEST COMPLETE: {passed_assertions}/{total_assertions} PASSED")
    if failed_assertions:
        print(f"FAILED ASSERTIONS ({len(failed_assertions)}):")
        for f in failed_assertions:
            print(f"  - {f}")
        return False
    else:
        print("ALL ADVERSARIAL STRESS-TEST CHECKS PASSED (100% EMPIRICAL CONFIRMATION)")
        print("=" * 80)
        return True

if __name__ == '__main__':
    success = run_challenger_audit()
    sys.exit(0 if success else 1)
