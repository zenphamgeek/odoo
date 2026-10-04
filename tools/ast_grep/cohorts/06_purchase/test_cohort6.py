#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
INSILOS SOVEREIGN HARD FORK — COHORT 6 LIVE ORM PROBE
Verifies bidirectional ORM functionality across procurement.order / procurement.order.line
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
    print("🔬 COHORT 6 LIVE ORM INTERACTIVE VERIFICATION PROBE")
    print("   Target: procurement.order (purchase.order) & procurement.order.line")
    print("================================================================================")

    config.parse_config(['-c', 'insilos.conf', '-d', 'odoo20_dev'])
    registry = Registry('odoo20_dev')
    with registry.cursor() as cr:
        env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})

        # 1. Model & Table resolution check
        log("Testing Sovereign Model & Table resolution...")
        po_model = env['procurement.order']
        legacy_po_model = env['purchase.order']
        assert po_model._name == 'procurement.order', f"po_model._name was {po_model._name}"
        assert legacy_po_model._name == 'procurement.order', f"legacy_po_model._name was {legacy_po_model._name}"
        assert po_model._table == 'procurement_order', f"po_model._table was {po_model._table}"
        log("Procurement Order model & table resolution verified.", "OK")

        pol_model = env['procurement.order.line']
        legacy_pol_model = env['purchase.order.line']
        assert pol_model._name == 'procurement.order.line', f"pol_model._name was {pol_model._name}"
        assert legacy_pol_model._name == 'procurement.order.line', f"legacy_pol_model._name was {legacy_pol_model._name}"
        assert pol_model._table == 'procurement_order_line', f"pol_model._table was {pol_model._table}"
        log("Procurement Order Line model & table resolution verified.", "OK")

        # 2. Relationship resolution check
        log("Testing Relational Field linkage between Order and Lines...")
        existing_order = po_model.search([], limit=1)
        if existing_order and existing_order.order_line:
            line = existing_order.order_line[0]
            assert line._name == 'procurement.order.line', f"line._name was {line._name}"
            assert line.order_id._name == 'procurement.order', f"line.order_id._name was {line.order_id._name}"
            log(f"Linkage verified: Order {existing_order.name} contains lines of type {line._name}.", "OK")
        else:
            log("No existing order with lines, proceeding to synthetic test.", "WARN")

        # 3. Bidirectional Create / Read / Write / Unlink
        log("Testing Bidirectional ORM Write / Read / Delete...")
        partner = env['party.master'].search([], limit=1)
        assert partner, "No party.master record found in database!"
        product = env['catalog.sku'].search([], limit=1)
        assert product, "No catalog.sku record found in database!"

        new_order = po_model.create({
            'partner_id': partner.id,
            'order_line': [
                (0, 0, {
                    'name': 'SS400 Industrial Steel Component',
                    'product_id': product.id,
                    'product_qty': 10.0,
                    'price_unit': 250.0,
                })
            ]
        })
        log(f"Created procurement.order ID {new_order.id}: '{new_order.name}'", "OK")

        # Read back via legacy model name
        legacy_read = legacy_po_model.browse(new_order.id)
        assert legacy_read.exists(), "Legacy model cannot find newly created order!"
        assert len(legacy_read.order_line) == 1, "Order line count mismatch via legacy model!"
        log("Read verified via legacy env['purchase.order'].", "OK")

        # Update line via legacy model
        legacy_line = legacy_read.order_line[0]
        legacy_line.write({'price_unit': 300.0})
        log("Updated order line price via legacy env['purchase.order.line'].", "OK")

        # Read back via sovereign line model
        sov_line_read = pol_model.browse(legacy_line.id)
        assert sov_line_read.price_unit == 300.0, f"Price mismatch: {sov_line_read.price_unit}"
        log("Read verified via sovereign env['procurement.order.line'].", "OK")

        # Clean up test records
        new_order.button_cancel()
        new_order.unlink()
        log("Test procurement order cancelled and unlinked cleanly.", "OK")

        cr.rollback()  # Clean transaction rollback

    log("🎉 COHORT 6 LIVE ORM PROBE PASSED 100%!", "OK")

if __name__ == "__main__":
    main()
