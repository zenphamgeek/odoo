# -*- coding: utf-8 -*-
# Part of Insilos. See LICENSE file for full copyright and licensing details.

{
    'name': 'Insilos SAP Fiori Horizon & Enterprise Lexicon',
    'version': '20.0.1.0.0',
    'category': 'Customization',
    'summary': 'SAP Enterprise Lexicon Terminology & Fiori 4 Horizon High-Density UI/UX Design System',
    'description': """
Insilos Enterprise SAP Lexicon & Fiori Horizon Design System
=============================================================
1. SAP Enterprise Lexicon:
   - Business Partner (BP) architecture across res.partner
   - Material Master (MM) taxonomy across product templates & variants
   - Sales & Distribution (SD) terminology for inquiries, quotations, and sales orders
   - Materials Management (MM) for purchase requisitions, RFQs, POs, and goods receipts
   - Financial Accounting & Controlling (FI/CO) for accounting documents, G/L accounts, cost centers
   - Production Planning (PP) for production orders, BOMs, and routing resources
2. SAP Fiori 4 / Horizon Ergonomics:
   - High-density compact data grids with sticky headers
   - Semantic status architecture (Positive, Warning, Critical, Information)
   - Object Header card styling with executive KPI indicators
   - Native Phosphor Duotone icon integration
    """,
    'author': 'Insilos Core Team',
    'website': 'https://insilos.com',
    'license': 'LGPL-3',
    'depends': ['base', 'web'],
    'data': [
        'data/sap_menu_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'insilos_sap_fiori/static/src/scss/fiori_horizon.scss',
            'insilos_sap_fiori/static/src/scss/fiori_status_badges.scss',
            'insilos_sap_fiori/static/src/scss/fiori_kpi_cards.scss',
            'insilos_sap_fiori/static/src/js/sap_lexicon_service.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
