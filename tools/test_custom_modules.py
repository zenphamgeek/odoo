"""
Comprehensive Test Runner for Ported Insilos Enterprise Modules on Odoo 20.
Executes test suites in transaction-isolated environments and reports results.
"""
import sys
import unittest
import importlib
from pathlib import Path
from odoo.tools import config
from odoo.orm.registry import Registry
import odoo

conf_file = '/home/zen/O20/insilos.conf' if Path('/home/zen/O20/insilos.conf').exists() else '/home/zen/O20/odoo.conf'
config.parse_config(['-c', conf_file, '-d', 'odoo20_dev'])
registry = Registry('odoo20_dev')

# Test candidates across key ported enterprise modules
TEST_TARGETS = [
    ('industry_templates', 'test_template_registry', 'TestIndustryTemplatesRegistry'),
    ('insilos_hs_sync', 'test_hs_reports_and_onboarding', 'TestHsReportsAndOnboarding'),
    ('insilos_pubsub_bridge', 'test_pubsub_ingest', 'TestPubSubIngest'),
    ('insilos_market_data', 'test_instrument_mapping', 'TestInstrumentMapping'),
    ('insilos_preferential_origin', 'test_origin', 'TestOriginEngine'),
    ('insilos_website', 'test_demo_request', 'TestDemoRequest'),
    ('openrouter_ai', 'test_durable_log', 'TestDurableLog'),
]

results = []

for mod_name, test_file, cls_name in TEST_TARGETS:
    try:
        mod_path = f'odoo.addons.{mod_name}.tests.{test_file}'
        imported_mod = importlib.import_module(mod_path)
        test_cls = getattr(imported_mod, cls_name, None)
        if not test_cls:
            results.append((f'{mod_name}.{test_file}', 'SKIPPED', f'Class {cls_name} not found'))
            continue
        
        methods = [m for m in dir(test_cls) if m.startswith('test_') and callable(getattr(test_cls, m))]
        print(f'\n--- Testing {mod_name} ({cls_name}): {len(methods)} tests ---')
        
        for m in methods:
            with registry.cursor() as cr:
                env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
                try:
                    case = test_cls(m)
                    test_cls.registry = registry
                    test_cls.cr = cr
                    test_cls.env = env
                    case.registry = registry
                    case.cr = cr
                    case.env = env
                    
                    if hasattr(case, 'setUpClass'):
                        try:
                            case.setUpClass()
                        except Exception:
                            pass
                    
                    if hasattr(case, 'setUp'):
                        case.setUp()
                    
                    getattr(case, m)()
                    
                    if hasattr(case, 'tearDown'):
                        try:
                            case.tearDown()
                        except Exception:
                            pass
                    if hasattr(case, 'doCleanups'):
                        try:
                            case.doCleanups()
                        except Exception:
                            pass
                    
                    results.append((f'{mod_name}::{cls_name}::{m}', 'PASS', None))
                    print(f'  [PASS] {m}')
                except Exception as e:
                    results.append((f'{mod_name}::{cls_name}::{m}', 'FAIL', str(e)))
                    print(f'  [FAIL] {m} -> {e}')
                finally:
                    if hasattr(env, '_state_stack__'):
                        env._state_stack__.clear()
                    cr.rollback()
    except Exception as e:
        results.append((f'{mod_name}.{test_file}', 'ERROR', str(e)))
        print(f'  [ERROR] {mod_name}.{test_file} -> {e}')

print('\n' + '=' * 60)
print('SUMMARY OF TEST EXECUTION')
print('=' * 60)
passed = sum(1 for r in results if r[1] == 'PASS')
failed = sum(1 for r in results if r[1] == 'FAIL')
errors = sum(1 for r in results if r[1] == 'ERROR')
skipped = sum(1 for r in results if r[1] == 'SKIPPED')

print(f'Total: {len(results)} | Passed: {passed} | Failed: {failed} | Errors: {errors} | Skipped: {skipped}')
print('=' * 60)
