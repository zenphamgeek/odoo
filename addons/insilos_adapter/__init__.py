# -*- coding: utf-8 -*-
# Part of Insilos. See LICENSE file for full copyright and licensing details.

"""
Insilos Ports & Adapters Gateway Module
========================================
Installs the PEP 451 MetaPathFinder import hook upon package import,
and exposes the Perimeter Gateway controllers.
"""

from . import hook

# Auto-activate import hook on module import
hook.install()

# Expose HTTP controllers when Odoo runtime environment is present
try:
    from . import controllers
except Exception:
    controllers = None
