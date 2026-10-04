#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
INSILOS SOVEREIGN HARD FORK — COHORT 10 LIVE ORM PROBE
Verifies bidirectional ORM functionality across finance.journal.entry / finance.journal.line
================================================================================
"""
import sys
from pathlib import Path

REPO_ROOT = Path("/home/zen/O20")
sys.path.insert(0, str(REPO_ROOT))

import odoo
from odoo.tools import config
from odoo.orm.registry import Registry

def log(msg, level="INFO"):
    prefixes = {"INFO": "  •", "OK": "[✓]", "WARN": "[!]", "ERR": "[✖]"}
    print(f"{prefixes.get(level, '   ')} {msg}")

def main():
    print("================================================================================")
    print("🔬 COHORT 10 LIVE ORM INTERACTIVE VERIFICATION PROBE")
    print("   Target: finance.journal.entry (account.move) & finance.journal.line (account.move.line)")
    print("================================================================================")

    config.parse_config(['-c', 'insilos.conf', '-d', 'odoo20_dev'])
    registry = Registry('odoo20_dev')
    with registry.cursor() as cr:
        env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})

        # 1. Model & Table resolution check
        log("Testing Sovereign Model & Table resolution...")
        am_model = env['finance.journal.entry']
        legacy_am_model = env['account.move']
        assert am_model._name == 'finance.journal.entry', f"am_model._name was {am_model._name}"
        assert legacy_am_model._name == 'finance.journal.entry', f"legacy_am_model._name was {legacy_am_model._name}"
        assert am_model._table == 'finance_journal_entry', f"am_model._table was {am_model._table}"
        log("Journal Entry model & table resolution verified.", "OK")

        aml_model = env['finance.journal.line']
        legacy_aml_model = env['account.move.line']
        assert aml_model._name == 'finance.journal.line', f"aml_model._name was {aml_model._name}"
        assert legacy_aml_model._name == 'finance.journal.line', f"legacy_aml_model._name was {legacy_aml_model._name}"
        assert aml_model._table == 'finance_journal_line', f"aml_model._table was {aml_model._table}"
        log("Journal Item model & table resolution verified.", "OK")

        # 2. Relationship resolution check
        log("Testing Relational Field linkage between Entry and Items...")
        existing_move = am_model.search([('line_ids', '!=', False)], limit=1)
        if existing_move and existing_move.line_ids:
            item = existing_move.line_ids[0]
            assert item._name == 'finance.journal.line', f"item._name was {item._name}"
            assert item.move_id._name == 'finance.journal.entry', f"item.move_id._name was {item.move_id._name}"
            log(f"Linkage verified: Journal Entry {existing_move.name} contains items of type {item._name}.", "OK")
        else:
            log("No existing move with lines found, proceeding to synthetic test.", "WARN")

        # 3. Bidirectional Create / Read / Write / Unlink
        log("Testing Bidirectional ORM Write / Read / Delete...")
        journal = env['account.journal'].search([('type', '=', 'general')], limit=1)
        if not journal:
            journal = env['account.journal'].search([], limit=1)
        assert journal, "No account.journal record found in database!"
        account1 = env['account.account'].search([], limit=1)
        account2 = env['account.account'].search([('id', '!=', account1.id)], limit=1) or account1
        assert account1, "No account.account record found in database!"

        new_entry = am_model.create({
            'journal_id': journal.id,
            'move_type': 'entry',
            'line_ids': [
                (0, 0, {
                    'name': 'Insilos Ledger Adjustment - Debit',
                    'account_id': account1.id,
                    'debit': 5000.0,
                    'credit': 0.0,
                }),
                (0, 0, {
                    'name': 'Insilos Ledger Adjustment - Credit',
                    'account_id': account2.id,
                    'debit': 0.0,
                    'credit': 5000.0,
                })
            ]
        })
        log(f"Created finance.journal.entry ID {new_entry.id}: '{new_entry.name}'", "OK")

        # Read back via legacy model name
        legacy_read = legacy_am_model.browse(new_entry.id)
        assert legacy_read.exists(), "Legacy model cannot find newly created entry!"
        assert len(legacy_read.line_ids) == 2, "Line count mismatch via legacy model!"
        log("Read verified via legacy env['account.move'].", "OK")

        # Update line via legacy model
        legacy_line = legacy_read.line_ids[0]
        legacy_line.write({'name': 'Insilos Ledger Adjustment - Updated Debit'})
        log("Updated line via legacy env['account.move.line'].", "OK")

        # Read back via sovereign line model
        sov_line_read = aml_model.browse(legacy_line.id)
        assert sov_line_read.name == 'Insilos Ledger Adjustment - Updated Debit', f"Line name mismatch: {sov_line_read.name}"
        log("Read verified via sovereign env['finance.journal.line'].", "OK")

        # Clean up test records
        new_entry.unlink()
        log("Test entry unlinked cleanly.", "OK")

        cr.rollback()  # Clean transaction rollback

    log("🎉 COHORT 10 LIVE ORM PROBE PASSED 100%!", "OK")

if __name__ == "__main__":
    main()
