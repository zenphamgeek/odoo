# -*- coding: utf-8 -*-
# Part of Insilos. See LICENSE file for full copyright and licensing details.

{
    'name': 'FX Rate Scheduler',
    'version': '26.0.1.0.0',
    'category': 'Accounting/Accounting',
    'summary': 'DPAS-TSM Dual-Key Prefect-Airflow Slot-Sensing Transactional State Machine for Pinned Conversions',
    'description': """
Insilos DPAS-TSM Protocol for Pinned Conversions
================================================
Dual-Key Prefect-Airflow Slot-Sensing Transactional State Machine:
- Dual-Key Advisory Locks: 64-bit bigint composed of 32-bit namespace hash and 32-bit company ID.
- Slot-Sensing Transactional State Machine with transaction-scoped pg_try_advisory_xact_lock.
- Tenant boundary isolation with allowed_company_ids=[company.id].
- Decree 70 Statutory Barrier: Enforces statutory immutability on posted/cancelled invoices.
- Prefect-inspired Blake2b idempotency tokens.
- Airflow-inspired atomic savepoint isolation per conversion record.
""",
    'author': 'Insilos Core Team',
    'website': 'https://insilos.com',
    'license': 'LGPL-3',
    'depends': ['base', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
