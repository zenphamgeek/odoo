#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
INSILOS SOVEREIGN HARD FORK — COHORT 7 LIVE ORM PROBE
Verifies bidirectional ORM functionality across order.header / order.line
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
    print("🔬 COHORT 7 LIVE ORM INTERACTIVE VERIFICATION PROBE")
    print("   Target: order.header (sale.order) & order.line (sale.order.line)")
    print("================================================================================")

    config.parse_config(['-c', 'insilos.conf', '-d', 'odoo20_dev'])
    registry = Registry('odoo20_dev')
    with registry.cursor() as cr:
        env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})

        # 1. Model & Table resolution check
        log("Testing Sovereign Model & Table resolution...")
        so_model = env['order.header']
        legacy_so_model = env['sale.order']
        assert so_model._name == 'order.header', f"so_model._name was {so_model._name}"
        assert legacy_so_model._name == 'order.header', f"legacy_so_model._name was {legacy_so_model._name}"
        assert so_model._table == 'order_header', f"so_model._table was {so_model._table}"
        log("Order Header model & table resolution verified.", "OK")

        sol_model = env['order.line']
        legacy_sol_model = env['sale.order.line']
        assert sol_model._name == 'order.line', f"sol_model._name was {sol_model._name}"
        assert legacy_sol_model._name == 'order.line', f"legacy_sol_model._name was {legacy_sol_model._name}"
        assert sol_model._table == 'order_line', f"sol_model._table was {sol_model._table}"
        log("Order Line model & table resolution verified.", "OK")

        # 2. Relationship resolution check
        log("Testing Relational Field linkage between Order and Lines...")
        existing_order = so_model.search([], limit=1)
        if existing_order and existing_order.order_line:
            line = existing_order.order_line[0]
            assert line._name == 'order.line', f"line._name was {line._name}"
            assert line.order_id._name == 'order.header', f"line.order_id._name was {line.order_id._name}"
            log(f"Linkage verified: Order {existing_order.name} contains lines of type {line._name}.", "OK")
        else:
            log("No existing order with lines, proceeding to synthetic test.", "WARN")

        # 3. Bidirectional Create / Read / Write / Unlink
        log("Testing Bidirectional ORM Write / Read / Delete...")
        partner = env['party.master'].search([], limit=1)
        assert partner, "No party.master record found in database!"
        product = env['catalog.sku'].search([], limit=1)
        assert product, "No catalog.sku record found in database!"

        new_order = so_model.create({
            'partner_id': partner.id,
            'order_line': [
                (0, 0, {
                    'name': 'Insilos Industrial AI Control Gateway',
                    'product_id': product.id,
                    'product_uom_qty': 5.0,
                    'price_unit': 1200.0,
                })
            ]
        })
        log(f"Created order.header ID {new_order.id}: '{new_order.name}'", "OK")

        # Read back via legacy model name
        legacy_read = legacy_so_model.browse(new_order.id)
        assert legacy_read.exists(), "Legacy model cannot find newly created order!"
        assert len(legacy_read.order_line) == 1, "Order line count mismatch via legacy model!"
        log("Read verified via legacy env['sale.order'].", "OK")

        # Update line via legacy model
        legacy_line = legacy_read.order_line[0]
        legacy_line.write({'price_unit': 1350.0})
        log("Updated order line price via legacy env['sale.order.line'].", "OK")

        # Read back via sovereign line model
        sov_line_read = sol_model.browse(legacy_line.id)
        assert sov_line_read.price_unit == 1350.0, f"Price mismatch: {sov_line_read.price_unit}"
        log("Read verified via sovereign env['order.line'].", "OK")

        # Clean up test records
        new_order._action_cancel()
        new_order.unlink()
        log("Test order cancelled and unlinked cleanly.", "OK")

        cr.rollback()  # Clean transaction rollback

    log("🎉 COHORT 7 LIVE ORM PROBE PASSED 100%!", "OK")

if __name__ == "__main__":
    main()
