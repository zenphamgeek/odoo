#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
INSILOS SOVEREIGN HARD FORK — COHORT 8 LIVE ORM PROBE
Verifies bidirectional ORM functionality across logistics.transfer / logistics.movement
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
    print("🔬 COHORT 8 LIVE ORM INTERACTIVE VERIFICATION PROBE")
    print("   Target: logistics.transfer (stock.picking) & logistics.movement (stock.move)")
    print("================================================================================")

    config.parse_config(['-c', 'insilos.conf', '-d', 'odoo20_dev'])
    registry = Registry('odoo20_dev')
    with registry.cursor() as cr:
        env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})

        # 1. Model & Table resolution check
        log("Testing Sovereign Model & Table resolution...")
        sp_model = env['logistics.transfer']
        legacy_sp_model = env['stock.picking']
        assert sp_model._name == 'logistics.transfer', f"sp_model._name was {sp_model._name}"
        assert legacy_sp_model._name == 'logistics.transfer', f"legacy_sp_model._name was {legacy_sp_model._name}"
        assert sp_model._table == 'logistics_transfer', f"sp_model._table was {sp_model._table}"
        log("Logistics Transfer model & table resolution verified.", "OK")

        sm_model = env['logistics.movement']
        legacy_sm_model = env['stock.move']
        assert sm_model._name == 'logistics.movement', f"sm_model._name was {sm_model._name}"
        assert legacy_sm_model._name == 'logistics.movement', f"legacy_sm_model._name was {legacy_sm_model._name}"
        assert sm_model._table == 'logistics_movement', f"sm_model._table was {sm_model._table}"
        log("Logistics Movement model & table resolution verified.", "OK")

        # 2. Relationship resolution check
        log("Testing Relational Field linkage between Transfer and Movements...")
        existing_picking = sp_model.search([], limit=1)
        if existing_picking and existing_picking.move_ids:
            move = existing_picking.move_ids[0]
            assert move._name == 'logistics.movement', f"move._name was {move._name}"
            assert move.picking_id._name == 'logistics.transfer', f"move.picking_id._name was {move.picking_id._name}"
            log(f"Linkage verified: Transfer {existing_picking.name} contains moves of type {move._name}.", "OK")
        else:
            log("No existing picking with moves, proceeding to synthetic test.", "WARN")

        # 3. Bidirectional Create / Read / Write / Unlink
        log("Testing Bidirectional ORM Write / Read / Delete...")
        partner = env['party.master'].search([], limit=1)
        assert partner, "No party.master record found in database!"
        product = env['catalog.sku'].search([('type', '=', 'consu')], limit=1)
        if not product:
            product = env['catalog.sku'].search([], limit=1)
        assert product, "No catalog.sku record found in database!"
        picking_type = env['stock.picking.type'].search([], limit=1)
        assert picking_type, "No stock.picking.type record found!"
        location = env['stock.location'].search([('usage', '=', 'internal')], limit=1)
        location_dest = env['stock.location'].search([('usage', '=', 'customer')], limit=1) or location

        new_picking = sp_model.create({
            'picking_type_id': picking_type.id,
            'location_id': location.id,
            'location_dest_id': location_dest.id,
            'partner_id': partner.id,
            'move_ids': [
                (0, 0, {
                    'description_picking': 'Insilos Autonomous AGV Pallet Dispatch',
                    'product_id': product.id,
                    'product_uom_qty': 10.0,
                    'product_uom': product.uom_id.id,
                    'location_id': location.id,
                    'location_dest_id': location_dest.id,
                })
            ]
        })
        log(f"Created logistics.transfer ID {new_picking.id}: '{new_picking.name}'", "OK")

        # Read back via legacy model name
        legacy_read = legacy_sp_model.browse(new_picking.id)
        assert legacy_read.exists(), "Legacy model cannot find newly created transfer!"
        assert len(legacy_read.move_ids) == 1, "Move count mismatch via legacy model!"
        log("Read verified via legacy env['stock.picking'].", "OK")

        # Update move via legacy model
        legacy_move = legacy_read.move_ids[0]
        legacy_move.write({'product_uom_qty': 15.0})
        log("Updated move qty via legacy env['stock.move'].", "OK")

        # Read back via sovereign movement model
        sov_move_read = sm_model.browse(legacy_move.id)
        assert sov_move_read.product_uom_qty == 15.0, f"Qty mismatch: {sov_move_read.product_uom_qty}"
        log("Read verified via sovereign env['logistics.movement'].", "OK")

        # Clean up test records
        new_picking.action_cancel()
        new_picking.unlink()
        log("Test picking cancelled and unlinked cleanly.", "OK")

        cr.rollback()  # Clean transaction rollback

    log("🎉 COHORT 8 LIVE ORM PROBE PASSED 100%!", "OK")

if __name__ == "__main__":
    main()
