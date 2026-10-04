#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
INSILOS SOVEREIGN HARD FORK — COHORT 9 LIVE ORM PROBE
Verifies bidirectional ORM functionality across manufacturing.order / manufacturing.bom
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
    print("🔬 COHORT 9 LIVE ORM INTERACTIVE VERIFICATION PROBE")
    print("   Target: manufacturing.order (mrp.production) & manufacturing.bom (mrp.bom)")
    print("================================================================================")

    config.parse_config(['-c', 'insilos.conf', '-d', 'odoo20_dev'])
    registry = Registry('odoo20_dev')
    with registry.cursor() as cr:
        env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})

        # 1. Model & Table resolution check
        log("Testing Sovereign Model & Table resolution...")
        mo_model = env['manufacturing.order']
        legacy_mo_model = env['mrp.production']
        assert mo_model._name == 'manufacturing.order', f"mo_model._name was {mo_model._name}"
        assert legacy_mo_model._name == 'manufacturing.order', f"legacy_mo_model._name was {legacy_mo_model._name}"
        assert mo_model._table == 'manufacturing_order', f"mo_model._table was {mo_model._table}"
        log("Manufacturing Order model & table resolution verified.", "OK")

        bom_model = env['manufacturing.bom']
        legacy_bom_model = env['mrp.bom']
        assert bom_model._name == 'manufacturing.bom', f"bom_model._name was {bom_model._name}"
        assert legacy_bom_model._name == 'manufacturing.bom', f"legacy_bom_model._name was {legacy_bom_model._name}"
        assert bom_model._table == 'manufacturing_bom', f"bom_model._table was {bom_model._table}"
        log("Manufacturing BOM model & table resolution verified.", "OK")

        # 2. Relationship resolution check
        log("Testing Relational Field linkage between Order and BOM...")
        existing_mo = mo_model.search([('bom_id', '!=', False)], limit=1)
        if existing_mo:
            assert existing_mo.bom_id._name == 'manufacturing.bom', f"bom_id._name was {existing_mo.bom_id._name}"
            log(f"Linkage verified: Production Order {existing_mo.name} references BOM {existing_mo.bom_id.code or existing_mo.bom_id.id}.", "OK")
        else:
            log("No existing MO with BOM found, proceeding to synthetic test.", "WARN")

        # 3. Bidirectional Create / Read / Write / Unlink
        log("Testing Bidirectional ORM Write / Read / Delete...")
        product = env['catalog.sku'].search([('type', '=', 'consu')], limit=1)
        if not product:
            product = env['catalog.sku'].search([], limit=1)
        assert product, "No catalog.sku record found in database!"
        picking_type = env['stock.picking.type'].search([('code', '=', 'mrp_operation')], limit=1)
        if not picking_type:
            picking_type = env['stock.picking.type'].search([], limit=1)
        assert picking_type, "No stock.picking.type record found!"

        # Create BOM via sovereign model
        new_bom = bom_model.create({
            'product_tmpl_id': product.product_tmpl_id.id,
            'product_qty': 1.0,
            'code': 'BOM-TEST-INSILOS-GENESIS',
        })
        log(f"Created manufacturing.bom ID {new_bom.id}: '{new_bom.code}'", "OK")

        # Create MO via sovereign model
        new_mo = mo_model.create({
            'product_id': product.id,
            'product_qty': 2.0,
            'bom_id': new_bom.id,
            'picking_type_id': picking_type.id,
        })
        log(f"Created manufacturing.order ID {new_mo.id}: '{new_mo.name}'", "OK")

        # Read back via legacy model name
        legacy_read = legacy_mo_model.browse(new_mo.id)
        assert legacy_read.exists(), "Legacy model cannot find newly created MO!"
        assert legacy_read.bom_id.id == new_bom.id, "BOM reference mismatch via legacy model!"
        log("Read verified via legacy env['mrp.production'].", "OK")

        # Update BOM code via legacy model
        legacy_bom = legacy_bom_model.browse(new_bom.id)
        legacy_bom.write({'code': 'BOM-TEST-UPDATED'})
        log("Updated BOM code via legacy env['mrp.bom'].", "OK")

        # Read back via sovereign model
        sov_bom_read = bom_model.browse(new_bom.id)
        assert sov_bom_read.code == 'BOM-TEST-UPDATED', f"BOM code mismatch: {sov_bom_read.code}"
        log("Read verified via sovereign env['manufacturing.bom'].", "OK")

        # Clean up test records
        new_mo.action_cancel()
        new_mo.unlink()
        new_bom.unlink()
        log("Test MO and BOM cleaned up cleanly.", "OK")

        cr.rollback()  # Clean transaction rollback

    log("🎉 COHORT 9 LIVE ORM PROBE PASSED 100!", "OK")

if __name__ == "__main__":
    main()
