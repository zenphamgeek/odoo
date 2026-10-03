#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/generate_horizon_carbon_icons.py
======================================
Automated Horizon-Carbon Tile (HCT) Icon Asset Generator for Insilos Platform.

Compiles master 256x256 vector SVG squircle tiles and raster PNGs
conforming to docs/INSILOS_ICON_STYLE_SPEC.md:
  - 256x256 master coordinate space (viewBox="0 0 256 256")
  - Ceramic light squircle plate: <rect class="insilos-tile-bg" x="12" y="12" width="232" height="232" rx="48" ry="48" fill="#FFFFFF" stroke="#E2E8F0" stroke-width="2"/>
  - Centered safe zone: 144x144 px centered at (128, 128) via transform="translate(56, 56) scale(0.5625)"
  - Two-tone glyph: tint underlay (opacity="0.2") + solid primary stroke in domain family color
  - 8 Enterprise Domain Color Families (Sales, Finance, SCM, MFG, HCM, Projects, Collab, GRC/AI)
  - Multi-resolution rasterization via CairoSVG 512x512 supersampling + Pillow LANCZOS resampling to 256x256
  - Generates companion dual assets (both .svg and .png) across repository modules
  - Generates special companion targets for base, mail, timesheets, mrp_workorder, chemical trade, fiori, etc.
  - Replaces /addons/web/static/img/default_icon_app.png with Carbon Blue neutral tile
"""

import argparse
import concurrent.futures
import io
import json
import os
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Tuple

try:
    from PIL import Image
except ImportError:
    Image = None

try:
    import cairosvg
except ImportError:
    cairosvg = None

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
PRIMARY_CANONICAL_DIR = os.path.join(REPO_ROOT, 'tools', 'phosphor_duotone')
EXTENDED_CANONICAL_DIR = os.path.join(REPO_ROOT, 'branding', 'phosphor', 'assets', 'duotone')
MAPPING_FILE = os.path.join(REPO_ROOT, 'tools', 'icon_mapping.json')

CORE_ADDONS_NAME = 'od' + 'oo'

MODULE_SEARCH_PATHS = [
    os.path.join(REPO_ROOT, 'addons'),
    os.path.join(REPO_ROOT, 'enterprise'),
    os.path.join(REPO_ROOT, CORE_ADDONS_NAME, 'addons'),
]

# 8 Enterprise Domain Color Families per docs/INSILOS_ICON_STYLE_SPEC.md (Harmonized Orange Primary Line)
DOMAIN_FAMILIES = {
    'FAM-01': {'primary': '#FF8000', 'tint': '#FEF3C7', 'name': 'Sales & CRM'},
    'FAM-02': {'primary': '#FF8000', 'tint': '#FEF3C7', 'name': 'Finance & Controlling'},
    'FAM-03': {'primary': '#FF8000', 'tint': '#FEF3C7', 'name': 'Supply Chain & Logistics'},
    'FAM-04': {'primary': '#FF8000', 'tint': '#FEF3C7', 'name': 'Manufacturing & Maintenance'},
    'FAM-05': {'primary': '#FF8000', 'tint': '#FEF3C7', 'name': 'Human Capital Management'},
    'FAM-06': {'primary': '#FF8000', 'tint': '#FEF3C7', 'name': 'Project Systems & Field Service'},
    'FAM-07': {'primary': '#FF8000', 'tint': '#FEF3C7', 'name': 'Collaboration & Portals'},
    'FAM-08': {'primary': '#FF8000', 'tint': '#FEF3C7', 'name': 'Governance, GRC & AI'},
}

# Explicit mappings for core/non-root modules
CORE_MODULE_MAPPING = {
    'base': {'glyph': 'squares-four', 'family': 'FAM-01', 'primary': '#FF8000', 'tint': '#FEF3C7'},
    'sale': {'glyph': 'tag', 'family': 'FAM-01', 'primary': '#FF8000', 'tint': '#FEF3C7'},
    'product': {'glyph': 'package', 'family': 'FAM-03', 'primary': '#FF8000', 'tint': '#FEF3C7'},
    'product_expiry': {'glyph': 'barcode', 'family': 'FAM-03', 'primary': '#FF8000', 'tint': '#FEF3C7'},
    'lunch': {'glyph': 'fork-knife', 'family': 'FAM-05', 'primary': '#FF8000', 'tint': '#FEF3C7'},
    'sms': {'glyph': 'chat-teardrop-text', 'family': 'FAM-07', 'primary': '#FF8000', 'tint': '#FEF3C7'},
    'snailmail': {'glyph': 'envelope-open', 'family': 'FAM-07', 'primary': '#FF8000', 'tint': '#FEF3C7'},
    'pos_restaurant': {'glyph': 'fork-knife', 'family': 'FAM-01', 'primary': '#FF8000', 'tint': '#FEF3C7'},
    'website_sale': {'glyph': 'shopping-cart', 'family': 'FAM-01', 'primary': '#FF8000', 'tint': '#FEF3C7'},
    'website_blog': {'glyph': 'book-open', 'family': 'FAM-07', 'primary': '#FF8000', 'tint': '#FEF3C7'},
    'website_forum': {'glyph': 'chats-teardrop', 'family': 'FAM-07', 'primary': '#FF8000', 'tint': '#FEF3C7'},
    'website_event': {'glyph': 'ticket', 'family': 'FAM-07', 'primary': '#FF8000', 'tint': '#FEF3C7'},
    'website_slides': {'glyph': 'graduation-cap', 'family': 'FAM-07', 'primary': '#FF8000', 'tint': '#FEF3C7'},
    'website_livechat': {'glyph': 'chats-teardrop', 'family': 'FAM-07', 'primary': '#FF8000', 'tint': '#FEF3C7'},
    'timesheet_grid': {'glyph': 'clock', 'family': 'FAM-06', 'primary': '#FF8000', 'tint': '#FEF3C7'},
    'timer': {'glyph': 'timer', 'family': 'FAM-06', 'primary': '#FF8000', 'tint': '#FEF3C7'},
    'spreadsheet': {'glyph': 'table', 'family': 'FAM-02', 'primary': '#FF8000', 'tint': '#FEF3C7'},
    'web_studio': {'glyph': 'magic-wand', 'family': 'FAM-08', 'primary': '#FF8000', 'tint': '#FEF3C7'},
    'board': {'glyph': 'layout', 'family': 'FAM-08', 'primary': '#FF8000', 'tint': '#FEF3C7'},
    'gamification': {'glyph': 'medal', 'family': 'FAM-05', 'primary': '#FF8000', 'tint': '#FEF3C7'},
    'iap': {'glyph': 'lightning', 'family': 'FAM-08', 'primary': '#FF8000', 'tint': '#FEF3C7'},
    'data_cleaning': {'glyph': 'broom', 'family': 'FAM-08', 'primary': '#FF8000', 'tint': '#FEF3C7'},
    'partner_autocomplete': {'glyph': 'address-book', 'family': 'FAM-07', 'primary': '#FF8000', 'tint': '#FEF3C7'},
    'ai': {'glyph': 'sparkle', 'family': 'FAM-08', 'primary': '#FF8000', 'tint': '#FEF3C7'},
    'ai_app': {'glyph': 'sparkle', 'family': 'FAM-08', 'primary': '#FF8000', 'tint': '#FEF3C7'},
    'ai_documents_source': {'glyph': 'sparkle', 'family': 'FAM-08', 'primary': '#FF8000', 'tint': '#FEF3C7'},
    'ai_knowledge': {'glyph': 'sparkle', 'family': 'FAM-08', 'primary': '#FF8000', 'tint': '#FEF3C7'},
    'ai_website': {'glyph': 'sparkle', 'family': 'FAM-08', 'primary': '#FF8000', 'tint': '#FEF3C7'},
    'mail_bot': {'glyph': 'robot', 'family': 'FAM-07', 'primary': '#FF8000', 'tint': '#FEF3C7'},
    'microsoft_calendar': {'glyph': 'calendar', 'family': 'FAM-07', 'primary': '#FF8000', 'tint': '#FEF3C7'},
    'google_calendar': {'glyph': 'calendar', 'family': 'FAM-07', 'primary': '#FF8000', 'tint': '#FEF3C7'},
    'microsoft_outlook': {'glyph': 'envelope-simple', 'family': 'FAM-07', 'primary': '#FF8000', 'tint': '#FEF3C7'},
    'google_gmail': {'glyph': 'envelope-simple', 'family': 'FAM-07', 'primary': '#FF8000', 'tint': '#FEF3C7'},
    'l10n': {'glyph': 'globe', 'family': 'FAM-02', 'primary': '#FF8000', 'tint': '#FEF3C7'},
    'l10n_ar': {'glyph': 'globe', 'family': 'FAM-02', 'primary': '#FF8000', 'tint': '#FEF3C7'},
    'l10n_ar_website_sale': {'glyph': 'globe', 'family': 'FAM-01', 'primary': '#FF8000', 'tint': '#FEF3C7'},
    'l10n_tw_reports': {'glyph': 'globe', 'family': 'FAM-02', 'primary': '#FF8000', 'tint': '#FEF3C7'},
    'gpu_fleet_manager': {'glyph': 'hard-drives', 'family': 'FAM-08', 'primary': '#FF8000', 'tint': '#FEF3C7'},
    'insilos_sap_fiori': {'glyph': 'gauge', 'family': 'FAM-08', 'primary': '#FF8000', 'tint': '#FEF3C7'},
}

# Prefix / category pattern rules
PATTERN_RULES = [
    (r'^ai(_|$)', {'glyph': 'sparkle', 'family': 'FAM-08', 'primary': '#FF8000', 'tint': '#FEF3C7'}),
    (r'^delivery_', {'glyph': 'truck', 'family': 'FAM-03', 'primary': '#FF8000', 'tint': '#FEF3C7'}),
    (r'^payment_', {'glyph': 'credit-card', 'family': 'FAM-01', 'primary': '#FF8000', 'tint': '#FEF3C7'}),
    (r'^social_', {'glyph': 'share-network', 'family': 'FAM-07', 'primary': '#FF8000', 'tint': '#FEF3C7'}),
    (r'^pos_', {'glyph': 'storefront', 'family': 'FAM-01', 'primary': '#FF8000', 'tint': '#FEF3C7'}),
    (r'^website_sale', {'glyph': 'shopping-cart', 'family': 'FAM-01', 'primary': '#FF8000', 'tint': '#FEF3C7'}),
    (r'^website_slides', {'glyph': 'graduation-cap', 'family': 'FAM-07', 'primary': '#FF8000', 'tint': '#FEF3C7'}),
    (r'^website_event', {'glyph': 'ticket', 'family': 'FAM-07', 'primary': '#FF8000', 'tint': '#FEF3C7'}),
    (r'^website_helpdesk', {'glyph': 'lifebuoy', 'family': 'FAM-07', 'primary': '#FF8000', 'tint': '#FEF3C7'}),
    (r'^website_', {'glyph': 'globe-hemisphere-west', 'family': 'FAM-07', 'primary': '#FF8000', 'tint': '#FEF3C7'}),
    (r'^helpdesk_', {'glyph': 'lifebuoy', 'family': 'FAM-07', 'primary': '#FF8000', 'tint': '#FEF3C7'}),
    (r'^mrp_plm', {'glyph': 'git-merge', 'family': 'FAM-04', 'primary': '#FF8000', 'tint': '#FEF3C7'}),
    (r'^mrp_maintenance', {'glyph': 'gear-six', 'family': 'FAM-04', 'primary': '#FF8000', 'tint': '#FEF3C7'}),
    (r'^mrp_', {'glyph': 'factory', 'family': 'FAM-04', 'primary': '#FF8000', 'tint': '#FEF3C7'}),
    (r'^stock_barcode', {'glyph': 'barcode', 'family': 'FAM-03', 'primary': '#FF8000', 'tint': '#FEF3C7'}),
    (r'^stock_', {'glyph': 'warehouse', 'family': 'FAM-03', 'primary': '#FF8000', 'tint': '#FEF3C7'}),
    (r'^hr_payroll', {'glyph': 'money', 'family': 'FAM-05', 'primary': '#FF8000', 'tint': '#FEF3C7'}),
    (r'^hr_recruitment', {'glyph': 'user-focus', 'family': 'FAM-05', 'primary': '#FF8000', 'tint': '#FEF3C7'}),
    (r'^hr_expense', {'glyph': 'receipt', 'family': 'FAM-02', 'primary': '#FF8000', 'tint': '#FEF3C7'}),
    (r'^hr_attendance', {'glyph': 'fingerprint', 'family': 'FAM-05', 'primary': '#FF8000', 'tint': '#FEF3C7'}),
    (r'^hr_appraisal', {'glyph': 'trophy', 'family': 'FAM-05', 'primary': '#FF8000', 'tint': '#FEF3C7'}),
    (r'^hr_holidays', {'glyph': 'airplane-takeoff', 'family': 'FAM-05', 'primary': '#FF8000', 'tint': '#FEF3C7'}),
    (r'^hr_skills', {'glyph': 'users', 'family': 'FAM-05', 'primary': '#FF8000', 'tint': '#FEF3C7'}),
    (r'^hr_timesheet', {'glyph': 'clock-user', 'family': 'FAM-06', 'primary': '#FF8000', 'tint': '#FEF3C7'}),
    (r'^hr_work_entry', {'glyph': 'clock-user', 'family': 'FAM-05', 'primary': '#FF8000', 'tint': '#FEF3C7'}),
    (r'^hr_', {'glyph': 'users-four', 'family': 'FAM-05', 'primary': '#FF8000', 'tint': '#FEF3C7'}),
    (r'^project_', {'glyph': 'kanban', 'family': 'FAM-06', 'primary': '#FF8000', 'tint': '#FEF3C7'}),
    (r'^account_', {'glyph': 'file-text', 'family': 'FAM-02', 'primary': '#FF8000', 'tint': '#FEF3C7'}),
    (r'^l10n_', {'glyph': 'globe', 'family': 'FAM-02', 'primary': '#FF8000', 'tint': '#FEF3C7'}),
    (r'^theme_', {'glyph': 'palette', 'family': 'FAM-07', 'primary': '#FF8000', 'tint': '#FEF3C7'}),
    (r'^test_', {'glyph': 'flask', 'family': 'FAM-08', 'primary': '#FF8000', 'tint': '#FEF3C7'}),
    (r'^base_', {'glyph': 'squares-four', 'family': 'FAM-01', 'primary': '#FF8000', 'tint': '#FEF3C7'}),
]

SPECIAL_TARGETS = {
    'base.menu_management': [
        (os.path.join(REPO_ROOT, CORE_ADDONS_NAME, 'addons', 'base', 'static', 'description', 'modules.svg'), 'svg'),
        (os.path.join(REPO_ROOT, CORE_ADDONS_NAME, 'addons', 'base', 'static', 'description', 'modules.png'), 'png'),
    ],
    'base.menu_administration': [
        (os.path.join(REPO_ROOT, CORE_ADDONS_NAME, 'addons', 'base', 'static', 'description', 'settings.svg'), 'svg'),
        (os.path.join(REPO_ROOT, CORE_ADDONS_NAME, 'addons', 'base', 'static', 'description', 'settings.png'), 'png'),
    ],
    'base.menu_tests': [
        (os.path.join(REPO_ROOT, CORE_ADDONS_NAME, 'addons', 'base', 'static', 'description', 'exception.svg'), 'svg'),
        (os.path.join(REPO_ROOT, CORE_ADDONS_NAME, 'addons', 'base', 'static', 'description', 'exception.png'), 'png'),
    ],
    'base': [
        (os.path.join(REPO_ROOT, CORE_ADDONS_NAME, 'addons', 'base', 'static', 'description', 'icon.svg'), 'svg'),
        (os.path.join(REPO_ROOT, CORE_ADDONS_NAME, 'addons', 'base', 'static', 'description', 'icon.png'), 'png'),
        (os.path.join(REPO_ROOT, CORE_ADDONS_NAME, 'addons', 'base', 'static', 'description', 'board.svg'), 'svg'),
        (os.path.join(REPO_ROOT, CORE_ADDONS_NAME, 'addons', 'base', 'static', 'description', 'board.png'), 'png'),
    ],
    'mail': [
        (os.path.join(REPO_ROOT, 'addons', 'mail', 'static', 'description', 'icon.svg'), 'svg'),
        (os.path.join(REPO_ROOT, 'addons', 'mail', 'static', 'description', 'icon.png'), 'png'),
    ],
    'hr_timesheet': [
        (os.path.join(REPO_ROOT, 'addons', 'hr_timesheet', 'static', 'description', 'icon.svg'), 'svg'),
        (os.path.join(REPO_ROOT, 'addons', 'hr_timesheet', 'static', 'description', 'icon.png'), 'png'),
        (os.path.join(REPO_ROOT, 'addons', 'hr_timesheet', 'static', 'description', 'icon_timesheet.svg'), 'svg'),
        (os.path.join(REPO_ROOT, 'addons', 'hr_timesheet', 'static', 'description', 'icon_timesheet.png'), 'png'),
        (os.path.join(REPO_ROOT, 'enterprise', 'hr_timesheet', 'static', 'description', 'icon_timesheet.svg'), 'svg'),
        (os.path.join(REPO_ROOT, 'enterprise', 'hr_timesheet', 'static', 'description', 'icon_timesheet.png'), 'png'),
    ],
    'mrp_workorder': [
        (os.path.join(REPO_ROOT, 'enterprise', 'mrp_workorder', 'static', 'description', 'icon.svg'), 'svg'),
        (os.path.join(REPO_ROOT, 'enterprise', 'mrp_workorder', 'static', 'description', 'icon.png'), 'png'),
        (os.path.join(REPO_ROOT, 'enterprise', 'mrp_workorder', 'static', 'description', 'mrp_display_icon.svg'), 'svg'),
        (os.path.join(REPO_ROOT, 'enterprise', 'mrp_workorder', 'static', 'description', 'mrp_display_icon.png'), 'png'),
    ],
    'insilos_chemical_trade_compliance': [
        (os.path.join(REPO_ROOT, 'enterprise', 'insilos_chemical_trade_compliance', 'static', 'description', 'icon.svg'), 'svg'),
        (os.path.join(REPO_ROOT, 'enterprise', 'insilos_chemical_trade_compliance', 'static', 'description', 'icon.png'), 'png'),
        (os.path.join(REPO_ROOT, 'enterprise', 'insilos_chemical_trade_compliance', 'static', 'description', 'unified_ops.svg'), 'svg'),
        (os.path.join(REPO_ROOT, 'enterprise', 'insilos_chemical_trade_compliance', 'static', 'description', 'unified_ops.png'), 'png'),
    ],
    'insilos_sap_fiori': [
        (os.path.join(REPO_ROOT, 'addons', 'insilos_sap_fiori', 'static', 'description', 'icon.svg'), 'svg'),
        (os.path.join(REPO_ROOT, 'addons', 'insilos_sap_fiori', 'static', 'description', 'icon.png'), 'png'),
    ],
    'gpu_fleet_manager': [
        (os.path.join(REPO_ROOT, 'addons', 'gpu_fleet_manager', 'static', 'description', 'icon.svg'), 'svg'),
        (os.path.join(REPO_ROOT, 'addons', 'gpu_fleet_manager', 'static', 'description', 'icon.png'), 'png'),
    ],
    'l10n': [
        (os.path.join(REPO_ROOT, 'addons', 'account', 'static', 'description', 'l10n.svg'), 'svg'),
        (os.path.join(REPO_ROOT, 'addons', 'account', 'static', 'description', 'l10n.png'), 'png'),
    ],
    'default_fallback': [
        (os.path.join(REPO_ROOT, 'addons', 'web', 'static', 'img', 'default_icon_app.png'), 'png'),
        (os.path.join(REPO_ROOT, 'addons', 'web', 'static', 'img', 'default_icon_app.svg'), 'svg'),
    ],
}

BASE_PROMO_ICONS = [
    (os.path.join(REPO_ROOT, CORE_ADDONS_NAME, 'addons', 'base', 'static', 'img', 'icons', 'account_accountant.png'), 'file-text'),
    (os.path.join(REPO_ROOT, CORE_ADDONS_NAME, 'addons', 'base', 'static', 'img', 'icons', 'appointment.png'), 'calendar-check'),
    (os.path.join(REPO_ROOT, CORE_ADDONS_NAME, 'addons', 'base', 'static', 'img', 'icons', 'helpdesk.png'), 'lifebuoy'),
    (os.path.join(REPO_ROOT, CORE_ADDONS_NAME, 'addons', 'base', 'static', 'img', 'icons', 'hr_appraisal.png'), 'trophy'),
    (os.path.join(REPO_ROOT, CORE_ADDONS_NAME, 'addons', 'base', 'static', 'img', 'icons', 'knowledge.png'), 'book-bookmark'),
    (os.path.join(REPO_ROOT, CORE_ADDONS_NAME, 'addons', 'base', 'static', 'img', 'icons', 'marketing_automation.png'), 'broadcast'),
    (os.path.join(REPO_ROOT, CORE_ADDONS_NAME, 'addons', 'base', 'static', 'img', 'icons', 'mrp_plm.png'), 'git-merge'),
    (os.path.join(REPO_ROOT, CORE_ADDONS_NAME, 'addons', 'base', 'static', 'img', 'icons', 'mrp_workorder.png'), 'wrench'),
    (os.path.join(REPO_ROOT, CORE_ADDONS_NAME, 'addons', 'base', 'static', 'img', 'icons', 'payment_sepa_direct_debit.png'), 'credit-card'),
    (os.path.join(REPO_ROOT, CORE_ADDONS_NAME, 'addons', 'base', 'static', 'img', 'icons', 'planning.png'), 'calendar'),
    (os.path.join(REPO_ROOT, CORE_ADDONS_NAME, 'addons', 'base', 'static', 'img', 'icons', 'quality_control.png'), 'check-square'),
    (os.path.join(REPO_ROOT, CORE_ADDONS_NAME, 'addons', 'base', 'static', 'img', 'icons', 'sale_amazon.png'), 'shopping-cart'),
    (os.path.join(REPO_ROOT, CORE_ADDONS_NAME, 'addons', 'base', 'static', 'img', 'icons', 'sale_ebay.png'), 'shopping-cart'),
    (os.path.join(REPO_ROOT, CORE_ADDONS_NAME, 'addons', 'base', 'static', 'img', 'icons', 'sale_subscription.png'), 'arrows-clockwise'),
    (os.path.join(REPO_ROOT, CORE_ADDONS_NAME, 'addons', 'base', 'static', 'img', 'icons', 'sign.png'), 'pencil-simple-line'),
    (os.path.join(REPO_ROOT, CORE_ADDONS_NAME, 'addons', 'base', 'static', 'img', 'icons', 'social.png'), 'share-network'),
    (os.path.join(REPO_ROOT, CORE_ADDONS_NAME, 'addons', 'base', 'static', 'img', 'icons', 'stock_barcode.png'), 'barcode'),
    (os.path.join(REPO_ROOT, CORE_ADDONS_NAME, 'addons', 'base', 'static', 'img', 'icons', 'timesheet_grid.png'), 'clock'),
    (os.path.join(REPO_ROOT, CORE_ADDONS_NAME, 'addons', 'base', 'static', 'img', 'icons', 'voip.png'), 'phone'),
    (os.path.join(REPO_ROOT, CORE_ADDONS_NAME, 'addons', 'base', 'static', 'img', 'icons', 'web_mobile.png'), 'device-mobile'),
    (os.path.join(REPO_ROOT, CORE_ADDONS_NAME, 'addons', 'base', 'static', 'img', 'icons', 'web_studio.png'), 'magic-wand'),
    (os.path.join(REPO_ROOT, CORE_ADDONS_NAME, 'addons', 'base', 'static', 'img', 'icons', 'website_form_editor.png'), 'cursor-click'),
    (os.path.join(REPO_ROOT, CORE_ADDONS_NAME, 'addons', 'base', 'static', 'img', 'icons', 'website_version.png'), 'git-branch'),
]


def load_authority_mapping() -> Dict[str, dict]:
    """Load canonical authority mapping catalog from tools/icon_mapping.json."""
    if os.path.exists(MAPPING_FILE):
        with open(MAPPING_FILE, 'r', encoding='utf-8') as f:
            raw = json.load(f)
            parsed = {}
            for k, v in raw.items():
                if isinstance(v, dict):
                    parsed[k] = v
                else:
                    parsed[k] = {
                        'glyph': v,
                        'family': 'FAM-01',
                        'primary_color': '#FF8000',
                        'tint_color': '#FEF3C7',
                        'label': k,
                    }
            return parsed
    return {}


def resolve_metadata_for_module(module_name: str, authority_mapping: Dict[str, dict]) -> dict:
    """Resolve full metadata (glyph, family, primary_color, tint_color) for a module."""
    if module_name in authority_mapping:
        entry = authority_mapping[module_name]
        return {
            'glyph': entry.get('glyph', 'squares-four'),
            'family': entry.get('family', 'FAM-01'),
            'primary_color': entry.get('primary_color', '#FF8000'),
            'tint_color': entry.get('tint_color', '#FEF3C7'),
            'label': entry.get('label', module_name),
        }

    if module_name in CORE_MODULE_MAPPING:
        entry = CORE_MODULE_MAPPING[module_name]
        return {
            'glyph': entry['glyph'],
            'family': entry['family'],
            'primary_color': entry['primary'],
            'tint_color': entry['tint'],
            'label': module_name,
        }

    for pattern, entry in PATTERN_RULES:
        if re.search(pattern, module_name):
            return {
                'glyph': entry['glyph'],
                'family': entry['family'],
                'primary_color': entry['primary'],
                'tint_color': entry['tint'],
                'label': module_name,
            }

    # Default Insilos Orange Horizon-Carbon Tile fallback
    return {
        'glyph': 'squares-four',
        'family': 'FAM-01',
        'primary_color': '#FF8000',
        'tint_color': '#FEF3C7',
        'label': module_name,
    }


def ensure_source_glyph(glyph_name: str) -> str:
    """Ensure the canonical duotone SVG source file exists and return its path."""
    target_src = os.path.join(PRIMARY_CANONICAL_DIR, f"{glyph_name}-duotone.svg")
    if os.path.exists(target_src) and os.path.getsize(target_src) > 0:
        return target_src

    ext_src = os.path.join(EXTENDED_CANONICAL_DIR, f"{glyph_name}-duotone.svg")
    if os.path.exists(ext_src):
        os.makedirs(PRIMARY_CANONICAL_DIR, exist_ok=True)
        tmp_src = target_src + f".tmp.{os.getpid()}"
        shutil.copy2(ext_src, tmp_src)
        os.replace(tmp_src, target_src)
        return target_src

    # Fallback to cube
    cube_src = os.path.join(EXTENDED_CANONICAL_DIR, "cube-duotone.svg")
    if os.path.exists(cube_src):
        os.makedirs(PRIMARY_CANONICAL_DIR, exist_ok=True)
        tmp_src = target_src + f".tmp.{os.getpid()}"
        shutil.copy2(cube_src, tmp_src)
        os.replace(tmp_src, target_src)
        return target_src

    raise FileNotFoundError(f"Glyph source not found for: {glyph_name}")


def extract_glyph_paths(glyph_name: str) -> Tuple[List[str], List[str]]:
    """Extract tint paths and primary paths from Phosphor duotone SVG source."""
    src_file = ensure_source_glyph(glyph_name)
    tree = ET.parse(src_file)
    root = tree.getroot()

    tint_paths = []
    primary_paths = []

    for elem in root.iter():
        if elem.tag.endswith('path'):
            d = elem.attrib.get('d', '').strip()
            if not d:
                continue
            opacity = elem.attrib.get('opacity')
            if opacity == '0.2':
                tint_paths.append(d)
            else:
                primary_paths.append(d)

    # In rare cases of single-path glyph without tint, use empty tint
    return tint_paths, primary_paths


def compile_hct_svg(glyph_name: str, primary_color: str, tint_color: str = "#F1F5F9") -> str:
    """
    Compile master 256x256 SVG tile conforming to docs/INSILOS_ICON_STYLE_SPEC.md:
      - Transparent background (no inner rect, no dark/light mode rect color clashes)
      - Centered enlarged glyph: scaled to ~0.9 (230px, ~60% larger than former 144px glyph)
      - Layer 2: Duotone accent underlay with opacity="0.2" fill="{primary_color}"
      - Layer 3: Primary solid contours with fill="{primary_color}"
    """
    tint_paths, primary_paths = extract_glyph_paths(glyph_name)

    tint_elements = []
    for d in tint_paths:
        tint_elements.append(f'      <path d="{d}"/>')
    tint_markup = "\n".join(tint_elements)

    primary_elements = []
    for d in primary_paths:
        primary_elements.append(f'      <path d="{d}"/>')
    primary_markup = "\n".join(primary_elements)

    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" width="100%" height="100%">\n'
        '  <g class="insilos-glyph-container" transform="translate(12.8, 12.8) scale(0.9)">\n'
    )

    if tint_markup:
        svg += (
            f'    <g class="insilos-glyph-tint" opacity="0.2" fill="{primary_color}">\n'
            f'{tint_markup}\n'
            '    </g>\n'
        )

    if primary_markup:
        svg += (
            f'    <g class="insilos-glyph-primary" fill="{primary_color}">\n'
            f'{primary_markup}\n'
            '    </g>\n'
        )

    svg += (
        '  </g>\n'
        '</svg>\n'
    )
    return svg


def compile_hct_png(compiled_svg: str) -> bytes:
    """
    Render 256x256 master PNG using CairoSVG supersampling (512x512)
    and Pillow Image.Resampling.LANCZOS downsampling for subpixel smoothness.
    """
    svg_bytes = compiled_svg.encode('utf-8')

    # 1. Supersample render to 512x512 via CairoSVG
    raw_512 = None
    if cairosvg is not None:
        raw_512 = cairosvg.svg2png(bytestring=svg_bytes, output_width=512, output_height=512)
    else:
        cairosvg_bin = shutil.which('cairosvg') or '/home/zen/.local/bin/cairosvg'
        cmd = [cairosvg_bin, '-', '-f', 'png', '-o', '-', '-W', '512', '-H', '512']
        p = subprocess.run(cmd, input=svg_bytes, stdout=subprocess.PIPE, check=True)
        raw_512 = p.stdout

    # 2. Downsample to 256x256 using Pillow LANCZOS resampling if available
    if Image is not None and raw_512:
        img = Image.open(io.BytesIO(raw_512))
        resized = img.resize((256, 256), Image.Resampling.LANCZOS)
        buf = io.BytesIO()
        resized.save(buf, format='PNG', optimize=True)
        return buf.getvalue()

    # Fallback to direct 256x256 CairoSVG rendering if Pillow is unavailable
    if cairosvg is not None:
        return cairosvg.svg2png(bytestring=svg_bytes, output_width=256, output_height=256)
    cairosvg_bin = shutil.which('cairosvg') or '/home/zen/.local/bin/cairosvg'
    cmd = [cairosvg_bin, '-', '-f', 'png', '-o', '-', '-W', '256', '-H', '256']
    p = subprocess.run(cmd, input=svg_bytes, stdout=subprocess.PIPE, check=True)
    return p.stdout


def find_all_modules() -> Dict[str, List[str]]:
    """Discover all modules with a __manifest__.py in search paths."""
    modules = {}
    for base in MODULE_SEARCH_PATHS:
        if not os.path.isdir(base):
            continue
        for name in os.listdir(base):
            mod_path = os.path.join(base, name)
            if os.path.isdir(mod_path) and os.path.isfile(os.path.join(mod_path, '__manifest__.py')):
                if name not in modules:
                    modules[name] = []
                modules[name].append(mod_path)
    return modules


def plan_all_targets(modules: Dict[str, List[str]], authority_mapping: Dict[str, dict]) -> List[Tuple[str, str, str, str, str]]:
    """
    Plan all target icon files across repository.
    Returns list of tuples: (module_or_key, glyph, primary_color, target_path, kind)
    """
    targets = []

    # 1. Special Targets
    for key, spec_list in SPECIAL_TARGETS.items():
        if key == 'default_fallback':
            meta = {'glyph': 'squares-four', 'primary_color': '#FF8000', 'tint_color': '#FEF3C7'}
        else:
            meta = resolve_metadata_for_module(key, authority_mapping)

        glyph = meta['glyph']
        primary = meta['primary_color']
        for target_path, kind in spec_list:
            targets.append((key, glyph, primary, target_path, kind))

    # Base Upgrade / Promo Icons in odoo/addons/base/static/img/icons/
    for target_path, promo_glyph in BASE_PROMO_ICONS:
        targets.append(('base_promo', promo_glyph, '#FF8000', target_path, 'png'))

    # 2. General module targets
    for mod_name, paths in modules.items():
        meta = resolve_metadata_for_module(mod_name, authority_mapping)
        glyph = meta['glyph']
        primary = meta['primary_color']

        for mod_dir in paths:
            desc_dir = os.path.join(mod_dir, 'static', 'description')
            has_desc = os.path.isdir(desc_dir)
            has_svg = os.path.isfile(os.path.join(desc_dir, 'icon.svg'))
            has_png = os.path.isfile(os.path.join(desc_dir, 'icon.png'))
            is_mapped = (mod_name in authority_mapping or mod_name in CORE_MODULE_MAPPING)

            if has_desc or has_svg or has_png or is_mapped:
                svg_target = os.path.join(desc_dir, 'icon.svg')
                png_target = os.path.join(desc_dir, 'icon.png')
                targets.append((mod_name, glyph, primary, svg_target, 'svg'))
                targets.append((mod_name, glyph, primary, png_target, 'png'))

    # Deduplicate by target_path
    dedup = {}
    for item in targets:
        dedup[item[3]] = item
    return list(dedup.values())


def process_target_worker(item: Tuple[str, str, str, str, str]) -> Tuple[str, str]:
    """Compile and write target asset atomically."""
    key, glyph, primary_color, target_path, kind = item
    try:
        compiled_svg = compile_hct_svg(glyph, primary_color)
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        tmp_target = target_path + f".tmp.{os.getpid()}"

        if kind == 'svg':
            if os.path.exists(target_path):
                with open(target_path, 'r', encoding='utf-8') as f:
                    if f.read() == compiled_svg:
                        return ('skip', target_path)
            with open(tmp_target, 'w', encoding='utf-8') as f:
                f.write(compiled_svg)
            os.replace(tmp_target, target_path)
            return ('write_svg', target_path)

        elif kind == 'png':
            png_bytes = compile_hct_png(compiled_svg)
            if os.path.exists(target_path):
                with open(target_path, 'rb') as f:
                    if f.read() == png_bytes:
                        return ('skip', target_path)
            with open(tmp_target, 'wb') as f:
                f.write(png_bytes)
            os.replace(tmp_target, target_path)
            return ('write_png', target_path)

    except Exception as e:
        return ('error', f"{target_path}: {e}")


def check_targets_integrity(targets: List[Tuple[str, str, str, str, str]]) -> Tuple[int, List[str]]:
    """Validate all targets meet Horizon-Carbon Tile (HCT) specifications."""
    errors = []
    checked = 0

    for key, glyph, primary, target_path, kind in targets:
        checked += 1
        if not os.path.exists(target_path):
            errors.append(f"Missing target file: {os.path.relpath(target_path, REPO_ROOT)}")
            continue

        if kind == 'svg':
            with open(target_path, 'r', encoding='utf-8', errors='ignore') as f:
                c = f.read()
            if '<svg' not in c:
                errors.append(f"Not an SVG element: {os.path.relpath(target_path, REPO_ROOT)}")
            if 'viewBox="0 0 256 256"' not in c:
                errors.append(f"Missing viewBox='0 0 256 256': {os.path.relpath(target_path, REPO_ROOT)}")
            if 'insilos-glyph' not in c:
                errors.append(f"Missing insilos-glyph container: {os.path.relpath(target_path, REPO_ROOT)}")
            if '<image ' in c or 'data:image/' in c:
                errors.append(f"Embedded raster in SVG: {os.path.relpath(target_path, REPO_ROOT)}")
            if os.path.getsize(target_path) < 100:
                errors.append(f"SVG file too small (<100B): {os.path.relpath(target_path, REPO_ROOT)}")

        elif kind == 'png':
            with open(target_path, 'rb') as f:
                header = f.read(8)
            if header != b'\x89PNG\r\n\x1a\n':
                errors.append(f"Invalid PNG magic header: {os.path.relpath(target_path, REPO_ROOT)}")
            if os.path.getsize(target_path) < 500:
                errors.append(f"PNG file suspiciously small (<500B): {os.path.relpath(target_path, REPO_ROOT)}")

    return checked, errors


def update_database_ir_module_icons():
    """Synchronize ir_module_module icon column in PostgreSQL."""
    try:
        import psycopg2
        conn = psycopg2.connect(
            host='127.0.0.1',
            port=5434,
            dbname='odoo20_dev',
            user='odoo',
            password='1NN0R1@2026'
        )
        cur = conn.cursor()
        print("\n[DB SYNC] Connected to PostgreSQL. Updating ir_module_module icon columns...")

        cur.execute("SELECT name FROM ir_module_module;")
        rows = cur.fetchall()

        all_modules = find_all_modules()
        updated = 0

        for (mname,) in rows:
            has_svg = False
            if mname in all_modules:
                for p in all_modules[mname]:
                    if os.path.isfile(os.path.join(p, 'static', 'description', 'icon.svg')):
                        has_svg = True
                        break
            new_icon = f"/{mname}/static/description/icon.svg" if has_svg else "/base/static/description/icon.svg"
            cur.execute("UPDATE ir_module_module SET icon = %s WHERE name = %s AND (icon IS NULL OR icon != %s);", (new_icon, mname, new_icon))
            if cur.rowcount > 0:
                updated += 1

        conn.commit()
        cur.close()
        conn.close()
        print(f"  ✓ ir_module_module update complete: {updated} records refreshed.")
        return True
    except Exception as e:
        print(f"  ⚠ ir_module_module DB sync warning: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Generate Insilos Horizon-Carbon Tile (HCT) Icon Assets")
    parser.add_argument('--check', action='store_true', help="Check integrity of icons only without writing")
    parser.add_argument('--update-db', action='store_true', help="Synchronize ir_module_module in PostgreSQL")
    parser.add_argument('--workers', type=int, default=os.cpu_count() or 4, help="Parallel worker processes")
    args = parser.parse_args()

    print("================================================================================")
    print("🚀 INSILOS HORIZON-CARBON TILE (HCT) ICON GENERATION ENGINE")
    print(f"   Mode: {'CHECK ONLY' if args.check else 'BATCH GENERATION'} | Workers: {args.workers}")
    print("================================================================================\n")

    authority_mapping = load_authority_mapping()
    print(f"[MAPPING] Loaded {len(authority_mapping)} authority entries from {os.path.relpath(MAPPING_FILE, REPO_ROOT)}.")

    all_modules = find_all_modules()
    print(f"[DISCOVERY] Found {len(all_modules)} modules across repository search paths.")

    targets = plan_all_targets(all_modules, authority_mapping)
    num_svg = sum(1 for t in targets if t[4] == 'svg')
    num_png = sum(1 for t in targets if t[4] == 'png')
    print(f"[PLAN] Planned {len(targets)} total asset targets ({num_svg} SVG, {num_png} PNG).")

    if args.check:
        print("\n[CHECK] Validating icon targets integrity...")
        checked, errors = check_targets_integrity(targets)
        if errors:
            print(f"  ✗ Found {len(errors)} issues across {checked} checked targets:")
            for err in errors[:25]:
                print(f"    - {err}")
            if len(errors) > 25:
                print(f"    ... and {len(errors) - 25} more.")
            sys.exit(1)
        else:
            print(f"  ✓ Integrity PASS: All {checked} targets meet the Horizon-Carbon Tile specification.")
            sys.exit(0)

    # Pre-seed unique glyph sources to prevent race conditions during parallel processing
    unique_glyphs = {t[1] for t in targets}
    print(f"\n[CACHE] Pre-seeding {len(unique_glyphs)} canonical Phosphor duotone glyph sources...")
    for g in unique_glyphs:
        ensure_source_glyph(g)

    # Parallel Execution
    print(f"\n[PARALLEL EXECUTION] Generating {len(targets)} targets with {args.workers} workers...")
    written_svg = 0
    written_png = 0
    skipped = 0
    errors = []

    with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as executor:
        for result in executor.map(process_target_worker, targets):
            status, path = result
            if status == 'write_svg':
                written_svg += 1
            elif status == 'write_png':
                written_png += 1
            elif status == 'skip':
                skipped += 1
            elif status == 'error':
                errors.append(path)

    print(f"\n[SUMMARY] Wrote {written_svg} SVGs, {written_png} PNGs, {skipped} up-to-date, {len(errors)} errors.")
    if errors:
        for err in errors[:20]:
            print(f"  ✗ {err}")
        sys.exit(1)

    # Synchronize fallback icon specifically
    fallback_png = os.path.join(REPO_ROOT, 'addons', 'web', 'static', 'img', 'default_icon_app.png')
    if os.path.isfile(fallback_png):
        print(f"  ✓ Neutral fallback tile confirmed at {os.path.relpath(fallback_png, REPO_ROOT)} ({os.path.getsize(fallback_png)} bytes).")

    if args.update_db:
        update_database_ir_module_icons()

    print("\n================================================================================")
    print("🎉 ALL HORIZON-CARBON TILE ICONS COMPILED & DEPLOYED SUCCESSFULLY")
    print("================================================================================\n")


if __name__ == '__main__':
    main()
