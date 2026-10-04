#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
INSILOS SOVEREIGN HARD FORK — COHORT 5 LIVE ORM PROBE
Verifies bidirectional ORM functionality across catalog.item / catalog.sku
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
    print("🔬 COHORT 5 LIVE ORM INTERACTIVE VERIFICATION PROBE")
    print("   Target: catalog.item (product.template) & catalog.sku (product.product)")
    print("================================================================================")

    config.parse_config(['-c', 'insilos.conf', '-d', 'odoo20_dev'])
    registry = Registry('odoo20_dev')
    with registry.cursor() as cr:
        env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})

        # 1. Model & Table resolution check
        log("Testing Sovereign Model & Table resolution...")
        item_model = env['catalog.item']
        legacy_item_model = env['product.template']
        assert item_model._name == 'catalog.item', f"item_model._name was {item_model._name}"
        assert legacy_item_model._name == 'catalog.item', f"legacy_item_model._name was {legacy_item_model._name}"
        assert item_model._table == 'catalog_item', f"item_model._table was {item_model._table}"
        log("Catalog Item model & table resolution verified.", "OK")

        sku_model = env['catalog.sku']
        legacy_sku_model = env['product.product']
        assert sku_model._name == 'catalog.sku', f"sku_model._name was {sku_model._name}"
        assert legacy_sku_model._name == 'catalog.sku', f"legacy_sku_model._name was {legacy_sku_model._name}"
        assert sku_model._table == 'catalog_sku', f"sku_model._table was {sku_model._table}"
        log("Catalog SKU model & table resolution verified.", "OK")

        # 2. Delegated inheritance verification (_inherits)
        log("Testing Delegated Inheritance resolution (_inherits)...")
        sample_sku = sku_model.search([], limit=1)
        assert sample_sku, "No SKU record found in database!"
        tmpl_rec = sample_sku.product_tmpl_id
        assert tmpl_rec._name == 'catalog.item', f"tmpl_rec._name was {tmpl_rec._name}"
        log(f"Delegated inheritance verified: SKU '{sample_sku.display_name}' points to item {tmpl_rec.id} ({tmpl_rec._name}).", "OK")

        # 3. Bidirectional Create / Read / Write / Unlink
        log("Testing Bidirectional ORM Write / Read / Delete...")
        new_item = item_model.create({
            'name': 'Insilos Autonomous Quantum Laser 4000',
            'type': 'consu',
        })
        log(f"Created catalog.item ID {new_item.id}: '{new_item.name}'", "OK")

        # Read back via legacy model name
        legacy_read = legacy_item_model.browse(new_item.id)
        assert legacy_read.exists(), "Legacy model cannot find newly created item!"
        assert legacy_read.name == 'Insilos Autonomous Quantum Laser 4000', f"Name mismatch: {legacy_read.name}"
        log("Read verified via legacy env['product.template'].", "OK")

        # Check auto-generated SKU from item
        auto_sku = new_item.product_variant_id
        assert auto_sku._name == 'catalog.sku', f"Auto SKU was {auto_sku._name}"
        log(f"Auto-generated SKU ID {auto_sku.id} verified via sovereign model: {auto_sku.display_name}", "OK")

        # Update SKU via legacy model
        legacy_sku = legacy_sku_model.browse(auto_sku.id)
        legacy_sku.write({'default_code': 'SOV-SKU-9999'})
        log("Updated SKU default_code via env['product.product'].", "OK")

        # Read back via sovereign SKU model
        sov_sku_read = sku_model.browse(auto_sku.id)
        assert sov_sku_read.default_code == 'SOV-SKU-9999', "Code mismatch!"
        log("Read verified via sovereign env['catalog.sku'].", "OK")

        # Clean up test records
        new_item.unlink()
        log("Test record unlinked cleanly.", "OK")

        cr.rollback()  # Clean transaction rollback

    log("🎉 COHORT 5 LIVE ORM PROBE PASSED 100%!", "OK")

if __name__ == "__main__":
    main()
