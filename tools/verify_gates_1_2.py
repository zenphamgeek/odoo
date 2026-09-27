#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verification Ladder Gates 1 & 2:
Gate 1: Python Compilation (py_compile)
Gate 2: XML Well-formedness & QWeb Syntax (lxml.etree)
"""

import os
import sys
import py_compile
from lxml import etree

MODULES = [
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

ENTERPRISE_DIR = '/home/zen/O20/enterprise'

def run_gate1():
    print("=" * 60)
    print("GATE 1: PYTHON SYNTAX AND COMPILATION AUDIT")
    print("=" * 60)
    py_files = []
    for mod in MODULES:
        mod_dir = os.path.join(ENTERPRISE_DIR, mod)
        for root, dirs, files in os.walk(mod_dir):
            for f in files:
                if f.endswith('.py'):
                    py_files.append(os.path.join(root, f))
    
    print(f"Auditing {len(py_files)} Python files across 26 modules...")
    errors = []
    for p in py_files:
        try:
            py_compile.compile(p, doraise=True)
        except py_compile.PyCompileError as e:
            errors.append((p, str(e)))
    
    if errors:
        print(f"FAILED: {len(errors)} compilation errors encountered:")
        for path, err in errors:
            print(f"  ❌ {path}: {err}")
        return False
    else:
        print(f"PASSED: All {len(py_files)} Python files compiled with zero errors! ✓")
        return True

def run_gate2():
    print("\n" + "=" * 60)
    print("GATE 2: XML & QWEB WELL-FORMEDNESS AUDIT")
    print("=" * 60)
    xml_files = []
    for mod in MODULES:
        mod_dir = os.path.join(ENTERPRISE_DIR, mod)
        for root, dirs, files in os.walk(mod_dir):
            for f in files:
                if f.endswith('.xml'):
                    xml_files.append(os.path.join(root, f))
    
    print(f"Auditing {len(xml_files)} XML files across 26 modules...")
    errors = []
    parser = etree.XMLParser(recover=False)
    for x in xml_files:
        try:
            etree.parse(x, parser=parser)
        except Exception as e:
            errors.append((x, str(e)))

    if errors:
        print(f"FAILED: {len(errors)} XML parse errors encountered:")
        for path, err in errors:
            print(f"  ❌ {path}: {err}")
        return False
    else:
        print(f"PASSED: All {len(xml_files)} XML files parsed with zero errors! ✓")
        return True

if __name__ == '__main__':
    g1 = run_gate1()
    g2 = run_gate2()
    if not (g1 and g2):
        sys.exit(1)
    print("\nGATES 1 & 2 PASSED COMPLETELY! ✓✓")
