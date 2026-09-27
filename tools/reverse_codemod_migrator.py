#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reverse Codemod Migration Engine
Ports and normalizes all 26 custom enterprise modules from /home/zen/insilos_ee
to /home/zen/O20/enterprise/ with strict preservation of custom business models.
"""

import os
import shutil
import re
import sys
import glob
import py_compile
from concurrent.futures import ProcessPoolExecutor, as_completed
from lxml import etree

SRC_ROOT = '/home/zen/insilos_ee'
DEST_ROOT = '/home/zen/O20/enterprise'

MODULE_SOURCES = {
    'insilos_hs_sync': os.path.join(SRC_ROOT, 'insilos/apps/insilos_hs_sync'),
    'insilos_hse_compliance': os.path.join(SRC_ROOT, 'insilos/apps/insilos_hse_compliance'),
    'insilos_knowledge_graph': os.path.join(SRC_ROOT, 'insilos/apps/insilos_knowledge_graph'),
    'insilos_pubsub_bridge': os.path.join(SRC_ROOT, 'insilos/apps/insilos_pubsub_bridge'),
    'insilos_logistics_idp': os.path.join(SRC_ROOT, 'insilos/apps/insilos_logistics_idp'),
    'insilos_capital_markets_decision_governance': os.path.join(SRC_ROOT, 'insilos/apps/insilos_capital_markets_decision_governance'),
    'insilos_tenant_control': os.path.join(SRC_ROOT, 'insilos/apps/insilos_tenant_control'),
    'insilos_chemical_trade_compliance': os.path.join(SRC_ROOT, 'insilos/apps/insilos_chemical_trade_compliance'),
    'insilos_preferential_origin': os.path.join(SRC_ROOT, 'insilos/apps/insilos_preferential_origin'),
    'insilos_industry_showcase': os.path.join(SRC_ROOT, 'insilos/apps/insilos_industry_showcase'),
    'insilos_market_data': os.path.join(SRC_ROOT, 'insilos/apps/insilos_market_data'),
    'insilos_treasury_market_risk': os.path.join(SRC_ROOT, 'insilos/apps/insilos_treasury_market_risk'),
    'insilos_market_terminal': os.path.join(SRC_ROOT, 'insilos/apps/insilos_market_terminal'),
    'insilos_finance_agent_os': os.path.join(SRC_ROOT, 'insilos/apps/insilos_finance_agent_os'),
    'insilos_esg_bridge': os.path.join(SRC_ROOT, 'insilos/apps/insilos_esg_bridge'),
    'insilos_website': os.path.join(SRC_ROOT, 'insilos/addons/insilos_website'),
    'insilos_theme_genesis': os.path.join(SRC_ROOT, 'insilos/addons/insilos_theme_genesis'),
    'industry_templates': os.path.join(SRC_ROOT, 'insilos/apps/industry_templates'),
    'openrouter_ai': os.path.join(SRC_ROOT, 'insilos/apps/openrouter_ai'),
    'ai_vision_iap': os.path.join(SRC_ROOT, 'insilos/apps/ai_vision_iap'),
    'industry_fsm_theme': os.path.join(SRC_ROOT, 'insilos/apps/industry_fsm_theme'),
    'pos_react': os.path.join(SRC_ROOT, 'insilos/apps/pos_react'),
    'pos_discount_react': os.path.join(SRC_ROOT, 'insilos/apps/pos_discount_react'),
    'pos_hr_react': os.path.join(SRC_ROOT, 'insilos/apps/pos_hr_react'),
    'cloud_storage_s3': os.path.join(SRC_ROOT, 'insilos/addons/cloud_storage_s3'),
    'l10n_vn_demo': os.path.join(SRC_ROOT, 'insilos/addons/l10n_vn_demo'),
}

# Protected custom business model prefixes that MUST NOT be touched
# e.g. is.hse.*, is.chemical.*, is.esg.*, is.hs.*, is.pubsub.*, is.customs.*, is.industry.*
PROTECTED_IS_PREFIXES = (
    'chemical', 'customs', 'esg', 'hs', 'hse', 'industry', 'pubsub'
)

# Technical metadata models that were rewritten to is.* in hardfork and MUST be reverted to ir.*
METADATA_IS_MODELS = [
    'ui.view',
    'actions.act_window',
    'actions.act_window.view',
    'actions.client',
    'actions.server',
    'actions.report',
    'actions.act_url',
    'actions.todo',
    'actions.actions',
    'attachment',
    'config_parameter',
    'rule',
    'cron',
    'model',
    'model.access',
    'model.fields',
    'model.data',
    'sequence',
    'default',
    'filters',
    'logging',
    'mail_server',
    'qweb',
    'asset',
    'module.module',
    'module.category',
    'exports',
    'exports.line',
]

CORE_RS_MODELS = [
    'partner',
    'users',
    'company',
    'groups',
    'groups.privilege',
    'config.settings',
    'currency',
    'currency.rate',
    'country',
    'lang',
    'bank',
]

def copy_module(name, src_dir, dest_dir):
    """Cleanly copy module source directory to enterprise."""
    target_path = os.path.join(dest_dir, name)
    if os.path.exists(target_path):
        shutil.rmtree(target_path)
    shutil.copytree(
        src_dir,
        target_path,
        ignore=shutil.ignore_patterns('*.pyc', '__pycache__', '.git', '.pytest_cache', '*.swp', '.DS_Store')
    )
    return target_path

def rename_specific_files(module_path):
    """Rename metadata files (e.g. security/is.model.access.csv -> ir.model.access.csv)."""
    renamed = []
    # 1. security CSV
    old_csv = os.path.join(module_path, 'security', 'is.model.access.csv')
    new_csv = os.path.join(module_path, 'security', 'ir.model.access.csv')
    if os.path.exists(old_csv):
        os.rename(old_csv, new_csv)
        renamed.append(('is.model.access.csv', 'ir.model.access.csv'))
    
    # 2. specific model python files
    re_map = {
        'is_attachment.py': 'ir_attachment.py',
        'rs_config_settings.py': 'res_config_settings.py',
        'rs_partner.py': 'res_partner.py',
        'rs_config_settings_views.xml': 'res_config_settings_views.xml',
        'rs_partner_demo.xml': 'res_partner_demo.xml',
        'is_cron.xml': 'ir_cron.xml',
    }
    for root, dirs, files in os.walk(module_path):
        for f in files:
            if f in re_map:
                old_p = os.path.join(root, f)
                new_p = os.path.join(root, re_map[f])
                os.rename(old_p, new_p)
                renamed.append((f, re_map[f]))
    return renamed

def transform_python_file(content):
    """Apply reverse codemod on Python source."""
    # 1. Imports
    content = re.sub(r'\bfrom\s+insilos\b', 'from odoo', content)
    content = re.sub(r'\bimport\s+insilos\b', 'import odoo', content)
    content = re.sub(r'([\'\"])insilos\.(addons|tools|osv|service|tests|http|sql_db|release|exceptions|orm|api|fields|models)\b', r'\1odoo.\2', content)
    content = re.sub(r'patch\([\'\"]insilos\.', r"patch('odoo.", content)
    content = re.sub(r'([\'\"])insilos/addons/', r'\1odoo/addons/', content)
    content = re.sub(
        r'from\s+odoo\.addons\.databases\.api\s+import\s+InsilosDatabaseApi',
        'try:\n    from odoo.addons.databases.api import InsilosDatabaseApi\nexcept ImportError:\n    from odoo.addons.databases.api import OdooDatabaseApi as InsilosDatabaseApi',
        content
    )

    # 2. Re-import renames in __init__.py files
    content = re.sub(r'\bfrom\s+\.\s+import\s+is_attachment\b', 'from . import ir_attachment', content)
    content = re.sub(r'\bfrom\s+\.\s+import\s+rs_config_settings\b', 'from . import res_config_settings', content)
    content = re.sub(r'\bfrom\s+\.\s+import\s+rs_partner\b', 'from . import res_partner', content)

    # 3. Core model string references
    for rs_mod in sorted(CORE_RS_MODELS, key=len, reverse=True):
        pattern = r'([\'\"])rs\.' + re.escape(rs_mod) + r'([\'\"])'
        replacement = r'\1res.' + rs_mod + r'\2'
        content = re.sub(pattern, replacement, content)

    # 4. Metadata model string references (ir.*)
    for is_mod in sorted(METADATA_IS_MODELS, key=len, reverse=True):
        pattern = r'([\'\"])is\.' + re.escape(is_mod) + r'([\'\"])'
        replacement = r'\1ir.' + is_mod + r'\2'
        content = re.sub(pattern, replacement, content)

    # 6. SQL table names in raw queries
    sql_tables = {
        'rs_partner': 'res_partner',
        'rs_users': 'res_users',
        'rs_company': 'res_company',
        'rs_groups': 'res_groups',
        'rs_country': 'res_country',
        'rs_currency': 'res_currency',
        'is_attachment': 'ir_attachment',
    }
    for old_t, new_t in sql_tables.items():
        content = re.sub(rf'\b{old_t}\b', new_t, content)

    return content

def transform_xml_file(content):
    """Apply reverse codemod on XML views and data."""
    # 1. Root tags: <insilos> -> <odoo>, </insilos> -> </odoo>, <insilos/> -> <odoo/>
    content = re.sub(r'<insilos(\s*[/]?>)', r'<odoo\1', content)
    content = re.sub(r'<insilos\s+', '<odoo ', content)
    content = re.sub(r'</insilos\s*>', '</odoo>', content)

    # 2. QWeb directives
    qweb_directives = [
        'esc', 'call', 'if', 'elif', 'else', 'foreach', 'as', 'set',
        'value', 'out', 'field', 'component', 'inherit', 'inherit-mode',
        'key', 'ref', 'model', 'translation'
    ]
    for d in qweb_directives:
        content = re.sub(rf'\bx-{d}=', rf't-{d}=', content)
    content = re.sub(r'\bx-att-', r't-att-', content)
    content = re.sub(r'\bx-on-', r't-on-', content)
    content = re.sub(r'\bx-name=', r't-name=', content)

    # 3. Model attributes in records
    for is_mod in sorted(METADATA_IS_MODELS, key=len, reverse=True):
        pattern = r'model=([\'\"])is\.' + re.escape(is_mod) + r'([\'\"])'
        replacement = r'model=\1ir.' + is_mod + r'\2'
        content = re.sub(pattern, replacement, content)

    for rs_mod in sorted(CORE_RS_MODELS, key=len, reverse=True):
        pattern = r'model=([\'\"])rs\.' + re.escape(rs_mod) + r'([\'\"])'
        replacement = r'model=\1res.' + rs_mod + r'\2'
        content = re.sub(pattern, replacement, content)

    # 3b. Quoted models in XML (comodels in JSON fields, domains, contexts)
    for rs_mod in sorted(CORE_RS_MODELS, key=len, reverse=True):
        pattern = r'([\'\"])rs\.' + re.escape(rs_mod) + r'([\'\"])'
        replacement = r'\1res.' + rs_mod + r'\2'
        content = re.sub(pattern, replacement, content)
    for is_mod in sorted(METADATA_IS_MODELS, key=len, reverse=True):
        pattern = r'([\'\"])is\.' + re.escape(is_mod) + r'([\'\"])'
        replacement = r'\1ir.' + is_mod + r'\2'
        content = re.sub(pattern, replacement, content)

    # 4. Field values in records: <field name="model">rs.partner</field>
    for rs_mod in sorted(CORE_RS_MODELS, key=len, reverse=True):
        content = re.sub(
            rf'(<field[^>]*name=[\'"](?:model|res_model)[\'"][^>]*>)\s*rs\.{re.escape(rs_mod)}\s*(</field>)',
            rf'\1res.{rs_mod}\2',
            content
        )
    for is_mod in sorted(METADATA_IS_MODELS, key=len, reverse=True):
        content = re.sub(
            rf'(<field[^>]*name=[\'"](?:model|res_model)[\'"][^>]*>)\s*is\.{re.escape(is_mod)}\s*(</field>)',
            rf'\1ir.{is_mod}\2',
            content
        )

    # 5. Model ID refs in XML: ref="base.model_rs_partner" -> ref="base.model_res_partner"
    for rs_mod in ['partner', 'users', 'company', 'groups', 'currency', 'country', 'lang']:
        content = re.sub(rf'model_rs_{rs_mod}\b', f'model_res_{rs_mod}', content)

    # 6. Specific view ID and file references in XML
    content = re.sub(r'rs_config_settings_view', 'res_config_settings_view', content)

    return content

def transform_manifest_file(content):
    """Normalize file references in __manifest__.py and ensure Odoo 20 version compatibility."""
    content = re.sub(r'security/is\.model\.access\.csv', 'security/ir.model.access.csv', content)
    content = re.sub(r'views/rs_config_settings_views\.xml', 'views/res_config_settings_views.xml', content)
    content = re.sub(r'data/is_cron\.xml', 'data/ir_cron.xml', content)
    content = re.sub(r'demo/rs_partner_demo\.xml', 'demo/res_partner_demo.xml', content)
    # Ensure Odoo 20 compatibility: 19.0.x.x.x -> 20.0.x.x.x
    content = re.sub(r'([\'\"])19\.0\.', r'\g<1>20.0.', content)
    # Ensure author is present
    if "'author'" not in content and '"author"' not in content:
        content = re.sub(r'(\s*)([\'\"]depends[\'\"]\s*:)', r"\1'author': 'Insilos',\n\1\2", content)
    return content

def transform_csv_file(content):
    """Normalize access rights CSV."""
    content = re.sub(r'\bis\.model\.access\b', 'ir.model.access', content)
    content = re.sub(r'\bmodel_rs_partner\b', 'model_res_partner', content)
    content = re.sub(r'\bmodel_rs_users\b', 'model_res_users', content)
    content = re.sub(r'\bmodel_rs_company\b', 'model_res_company', content)
    return content

def transform_js_file(content):
    """Normalize JS import specifiers."""
    content = re.sub(r'([\'\"])@insilos/silo-mock\1', r'\1@odoo/hoot-mock\1', content)
    content = re.sub(r'([\'\"])@insilos/silo-dom\1', r'\1@odoo/hoot-dom\1', content)
    content = re.sub(r'([\'\"])@insilos/silo\1', r'\1@odoo/hoot\1', content)
    content = re.sub(r'([\'\"])@insilos/owl\1', r'\1@odoo/owl\1', content)
    content = re.sub(r'([\'\"])@insilos/wli\1', r'\1@odoo/owl\1', content)
    content = re.sub(r'([\'\"])@insilos/web/', r'\1@web/', content)
    content = re.sub(r'([\'\"])@insilos/web\1', r'\1@web\1', content)
    # Also repair any existing mismatched quotes
    content = re.sub(r'\'(@web/[^\'\"]+)\"', r"'\1'", content)
    content = re.sub(r'\"(@web/[^\'\"]+)\'', r'"\1"', content)
    return content

def process_file(fpath):
    """Dispatches appropriate transformation based on file extension."""
    fname = os.path.basename(fpath)
    ext = os.path.splitext(fpath)[1].lower()

    with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
        original = f.read()

    modified = original

    if fname == '__manifest__.py':
        modified = transform_manifest_file(modified)
        modified = transform_python_file(modified)
    elif ext == '.py':
        modified = transform_python_file(modified)
    elif ext == '.xml':
        modified = transform_xml_file(modified)
    elif ext == '.csv':
        modified = transform_csv_file(modified)
    elif ext in ('.js', '.ts'):
        modified = transform_js_file(modified)

    if modified != original:
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(modified)
        return True
    return False

def post_process_module(name, mod_path):
    if name == 'ai_vision_iap':
        iap_svc_path = os.path.join(mod_path, 'models', 'iap_service.py')
        if not os.path.exists(iap_svc_path):
            with open(iap_svc_path, 'w', encoding='utf-8') as f:
                f.write("""# Part of Insilos. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

class IapService(models.Model):
    _inherit = 'iap.service'

    credit_cost = fields.Float(
        string='Credit Cost',
        default=1.0,
        help="Credit amount charged per service invocation. 0 = free.",
    )

    @api.model
    def cost_for(self, technical_name, default=1.0):
        service = self.search([('technical_name', '=', technical_name)], limit=1)
        if not service:
            return default
        return service.credit_cost
""")
        init_path = os.path.join(mod_path, 'models', '__init__.py')
        with open(init_path, 'r', encoding='utf-8') as f:
            c = f.read()
        if 'iap_service' not in c:
            with open(init_path, 'w', encoding='utf-8') as f:
                f.write("from . import iap_service\n" + c)

    elif name == 'insilos_website':
        # In Odoo 20, default website is in module 'base' (base.default_website), not 'website'
        for root, dirs, files in os.walk(mod_path):
            for f in files:
                if f.endswith(('.xml', '.py')):
                    fpath = os.path.join(root, f)
                    with open(fpath, 'r', encoding='utf-8') as fp:
                        c = fp.read()
                    if 'website.default_website' in c:
                        c = c.replace('website.default_website', 'base.default_website')
                        with open(fpath, 'w', encoding='utf-8') as fp:
                            fp.write(c)

    elif name == 'l10n_vn_demo':
        sale_demo = os.path.join(mod_path, 'demo', 'sale_demo.xml')
        if os.path.exists(sale_demo):
            with open(sale_demo, 'r', encoding='utf-8') as fp:
                c = fp.read()
            if 'base.user_demo' in c:
                c = c.replace('base.user_demo', 'base.user_admin')
                with open(sale_demo, 'w', encoding='utf-8') as fp:
                    fp.write(c)

def process_single_module(name):
    """End-to-end processing for a single module."""
    src_dir = MODULE_SOURCES[name]
    dest_dir = DEST_ROOT
    mod_path = copy_module(name, src_dir, dest_dir)
    renamed = rename_specific_files(mod_path)
    
    modified_count = 0
    total_files = 0
    for root, dirs, files in os.walk(mod_path):
        for f in files:
            fpath = os.path.join(root, f)
            total_files += 1
            if process_file(fpath):
                modified_count += 1

    post_process_module(name, mod_path)

    return {
        'module': name,
        'path': mod_path,
        'renamed_files': renamed,
        'total_files': total_files,
        'modified_files': modified_count
    }

def main():
    print("=" * 70)
    print("INSILOS -> ODOO 20 REVERSE CODEMOD MIGRATION ENGINE")
    print("=" * 70)
    print(f"Source: {SRC_ROOT}")
    print(f"Target: {DEST_ROOT}")
    print(f"Total modules to port: {len(MODULE_SOURCES)}")
    print("-" * 70)

    # Parallel processing of all 26 modules
    with ProcessPoolExecutor() as executor:
        futures = {executor.submit(process_single_module, mod): mod for mod in MODULE_SOURCES}
        results = []
        for future in as_completed(futures):
            res = future.result()
            results.append(res)
            print(f"  ✓ [{res['module']}] Ported: {res['total_files']} files, {res['modified_files']} transformed, {len(res['renamed_files'])} renamed")

    print("-" * 70)
    print("ALL 26 MODULES PORTED AND CODEMODDED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == '__main__':
    main()
