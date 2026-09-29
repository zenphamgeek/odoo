#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check Odoo registry loading and update_list for the 26 ported modules.
"""

import sys
import os

# Add Odoo root to python path
sys.path.insert(0, '/home/zen/O20')

import odoo
from odoo.tools import config

conf_file = '/home/zen/O20/insilos.conf' if os.path.exists('/home/zen/O20/insilos.conf') else '/home/zen/O20/odoo.conf'
config.parse_config(['-c', conf_file, '-d', 'odoo20_dev'])

TARGET_MODULES = [
    'insilos_hs_sync', 'insilos_hse_compliance', 'insilos_knowledge_graph',
    'insilos_pubsub_bridge', 'insilos_logistics_idp',
    'insilos_capital_markets_decision_governance', 'insilos_tenant_control',
    'insilos_chemical_trade_compliance', 'insilos_preferential_origin',
    'insilos_industry_showcase', 'insilos_market_data',
    'insilos_treasury_market_risk', 'insilos_market_terminal',
    'insilos_finance_agent_os', 'insilos_esg_bridge', 'insilos_website',
    'insilos_theme_genesis', 'industry_templates', 'openrouter_ai',
    'ai_vision_iap', 'industry_fsm_theme', 'pos_react', 'pos_discount_react',
    'pos_hr_react', 'cloud_storage_s3', 'l10n_vn_demo'
]

from odoo.modules.registry import Registry

def main():
    print("=" * 60)
    print("GATE 3: REGISTRY & MODULE DISCOVERY CHECK")
    print("=" * 60)
    
    registry = Registry('odoo20_dev')
    with registry.cursor() as cr:
        env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
        print("Running env['ir.module.module'].update_list()...")
        res = env['ir.module.module'].update_list()
        print(f"update_list result: {res}")
        cr.commit()

        # Query all target modules in ir.module.module
        modules = env['ir.module.module'].search([('name', 'in', TARGET_MODULES)])
        found_names = {m.name: m.state for m in modules}
        
        print(f"\nFound {len(found_names)} of {len(TARGET_MODULES)} modules in database:")
        for name in TARGET_MODULES:
            state = found_names.get(name, "NOT FOUND")
            print(f"  [{state:12}] {name}")
            
        missing = set(TARGET_MODULES) - set(found_names.keys())
        if missing:
            print(f"\n❌ Missing modules: {missing}")
            sys.exit(1)
        else:
            print("\n✓ ALL 26 MODULES DISCOVERED IN ODOO DATABASE!")

if __name__ == '__main__':
    main()
