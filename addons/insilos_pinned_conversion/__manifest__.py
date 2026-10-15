# -*- coding: utf-8 -*-
# Part of Insilos. See LICENSE file for full copyright and licensing details.

{
    'name': 'Pinned FX Rates',
    'version': '20.0.1.0.0',
    'category': 'Accounting/Accounting',
    'summary': 'DERS-ZLRR and Decree 70 Statutory Barrier for Pinned FX Currency Conversions',
    'description': """
Insilos DERS-ZLRR & Decree 70 Statutory Barrier for Pinned Conversions
======================================================================
- DERS-ZLRR: Deterministic Ephemeral Rate-Window Snapshotting with Zero-Lock Read Reconciliation.
- Decree 70 Statutory Barrier: Enforces draft state and un-sent EDI barriers on contract revaluation.
- Deterministic 64-bit transaction-scoped advisory locks with savepoint double-entry balancing.
""",
    'author': 'Insilos Core Team',
    'website': 'https://insilos.com',
    'license': 'LGPL-3',
    'depends': ['base', 'account'],
    'data': [
        'data/ir_cron_data.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
