# -*- coding: utf-8 -*-
# Part of Insilos. See LICENSE file for full copyright and licensing details.

{
    'name': 'Insilos Ports & Adapters Gateway',
    'version': '20.0.1.0.0',
    'category': 'Technical',
    'summary': 'Hexagonal Adapter and Perimeter Gateway for Insilos Platform',
    'description': """
Insilos Ports & Adapters (Hexagonal Architecture) Gateway
==========================================================
Provides:
1. Python Import Hook Adapter for the 'insilos' namespace (PEP 451 MetaPathFinder).
   Allows custom modules and external scripts to import models, fields, api, http,
   tools, and addons directly from 'insilos'.
2. API Perimeter Gateway Controller at '/insilos/api/v1/...'.
   Enforces 'Server: insilos/20.0' headers, cleans and normalizes JSON payloads,
   and prevents leakage of internal Odoo stack traces upon unexpected errors.
""",
    'author': 'Insilos Core Team',
    'website': 'https://insilos.com',
    'license': 'LGPL-3',
    'depends': ['base'],
    'data': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
