#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Install test for the 26 ported modules in 5 topological waves.
"""

import sys
import os
import time

sys.path.insert(0, '/home/zen/O20')

import odoo
from odoo.tools import config
from odoo.modules.registry import Registry

conf_file = '/home/zen/O20/insilos.conf' if os.path.exists('/home/zen/O20/insilos.conf') else '/home/zen/O20/odoo.conf'
config.parse_config(['-c', conf_file, '-d', 'odoo20_dev'])

WAVES = [
    # Wave 1: Foundations
    [
        'openrouter_ai',
        'ai_vision_iap',
        'industry_templates',
        'insilos_hs_sync',
        'insilos_hse_compliance',
        'insilos_knowledge_graph',
        'insilos_pubsub_bridge',
        'insilos_website',
        'insilos_theme_genesis',
        'cloud_storage_s3',
        'l10n_vn_demo',
    ],
    # Wave 2: Platforms
    [
        'insilos_logistics_idp',
        'insilos_capital_markets_decision_governance',
        'insilos_tenant_control',
        'industry_fsm_theme',
    ],
    # Wave 3: Vertical Business Apps
    [
        'insilos_chemical_trade_compliance',
        'insilos_preferential_origin',
        'insilos_industry_showcase',
        'insilos_market_data',
        'insilos_treasury_market_risk',
        'pos_react',
        'pos_discount_react',
        'pos_hr_react',
    ],
    # Wave 4: Trading & Agent AI
    [
        'insilos_market_terminal',
        'insilos_finance_agent_os',
    ],
    # Wave 5: Cross-Domain Intelligence
    [
        'insilos_esg_bridge',
    ],
]

def install_wave(wave_num, modules):
    print(f"\n{'=' * 60}")
    print(f"INSTALLING WAVE {wave_num}: {len(modules)} modules")
    print(f"Modules: {', '.join(modules)}")
    print(f"{'=' * 60}")

    registry = Registry('odoo20_dev')
    with registry.cursor() as cr:
        env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
        mods = env['ir.module.module'].search([('name', 'in', modules)])
        for m in mods:
            if m.state != 'installed':
                print(f"Marking {m.name} for immediate install (state was: {m.state})...")
                m.button_immediate_install()
                cr.commit()
                print(f"  ✓ Installed {m.name}")
            else:
                print(f"  ✓ {m.name} is already installed")

def verify_all_installed():
    print(f"\n{'=' * 60}")
    print("FINAL INSTALLATION VERIFICATION")
    print(f"{'=' * 60}")
    registry = Registry('odoo20_dev')
    all_mods = [m for w in WAVES for m in w]
    with registry.cursor() as cr:
        env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
        mods = env['ir.module.module'].search([('name', 'in', all_mods)])
        states = {m.name: m.state for m in mods}
        for name in all_mods:
            state = states.get(name, "NOT FOUND")
            status_symbol = "✓" if state == 'installed' else "❌"
            print(f"  {status_symbol} [{state:12}] {name}")
        
        not_installed = [m for m in all_mods if states.get(m) != 'installed']
        if not_installed:
            print(f"\n❌ Uninstalled modules: {not_installed}")
            return False
        print("\n🎉 ALL 26 MODULES INSTALLED SUCCESSFULLY!")
        return True

def main():
    start_time = time.time()
    for i, wave in enumerate(WAVES, 1):
        install_wave(i, wave)
    success = verify_all_installed()
    print(f"Completed in {time.time() - start_time:.2f}s")
    if not success:
        sys.exit(1)

if __name__ == '__main__':
    main()
