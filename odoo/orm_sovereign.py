# -*- coding: utf-8 -*-
# Part of Insilos Enterprise Platform.
# Copyright (C) 2026 Insilos Hard Fork Council. All Rights Reserved.
# Strict Database & Runtime Invariance Architecture.

"""
Insilos Sovereign ORM Model Registry & Exception Sanitization Facade.
=====================================================================
Provides SAP / Enterprise-grade nomenclature aliases without modifying
underlying PostgreSQL tables or schema structures.
"""

import logging
import re
from typing import Any, Dict

_LOGGER = logging.getLogger("insilos.orm.facade")

# Bijective Enterprise Model Nomenclature Registry
SOVEREIGN_MODEL_ALIASES: Dict[str, str] = {
    # Core Master Data
    "enterprise.business_partner": "res.partner",
    "insilos.business_partner": "res.partner",
    "enterprise.user": "res.users",
    "insilos.user": "res.users",
    "enterprise.company": "res.company",
    "enterprise.currency": "res.currency",
    "enterprise.country": "res.country",

    # System & Metamodel (Schema Read-Only)
    "enterprise.model": "ir.model",
    "enterprise.model.fields": "ir.model.fields",
    "enterprise.ui.view": "ir.ui.view",
    "enterprise.ui.menu": "ir.ui.menu",
    "enterprise.action": "ir.actions.act_window",

    # Sovereign Cohorts 1-10: Master Data, Supply Chain & Finance (IBM Taxonomy)
    "party.classification": "res.partner.category",
    "system.attachment": "ir.attachment",
    "organization.unit": "res.company",
    "party.master": "res.partner",
    "catalog.item": "product.template",
    "catalog.sku": "product.product",
    "procurement.order": "purchase.order",
    "procurement.order.line": "purchase.order.line",
    "order.header": "sale.order",
    "order.line": "sale.order.line",
    "logistics.transfer": "stock.picking",
    "logistics.movement": "stock.move",
    "manufacturing.order": "mrp.production",
    "manufacturing.bom": "mrp.bom",
    "finance.journal.entry": "account.move",
    "finance.journal.line": "account.move.line",

    # Sovereign Cohorts 11-12: Project Systems & Plant Maintenance
    "ps.project.definition": "project.project",
    "ps.wbs.element": "project.task",
    "ps.project.milestone": "project.milestone",
    "pm.technical.equipment": "maintenance.equipment",
    "pm.maintenance.order": "maintenance.request",
    "pm.maintenance.group": "maintenance.team",
}

# Reverse mapping for inspection & export
REVERSE_MODEL_ALIASES: Dict[str, str] = {v: k for k, v in SOVEREIGN_MODEL_ALIASES.items()}

_ORCHESTRATED = False


def patch_orm_sovereign() -> None:
    """
    Patches Environment and Registry to resolve enterprise aliases transparently.
    Idempotent and thread-safe.
    """
    global _ORCHESTRATED
    if _ORCHESTRATED:
        return

    try:
        from odoo.orm.environments import Environment
        from odoo.orm.registry import Registry

        # 1. Patch Environment.__getitem__ and Environment.__contains__
        orig_env_getitem = Environment.__getitem__
        orig_env_contains = Environment.__contains__

        def __sovereign_env_getitem__(self, model_name: str) -> Any:
            canonical_name = SOVEREIGN_MODEL_ALIASES.get(model_name, model_name)
            return orig_env_getitem(self, canonical_name)

        def __sovereign_env_contains__(self, model_name: str) -> bool:
            canonical_name = SOVEREIGN_MODEL_ALIASES.get(model_name, model_name)
            return orig_env_contains(self, canonical_name)

        Environment.__getitem__ = __sovereign_env_getitem__
        Environment.__contains__ = __sovereign_env_contains__

        # 2. Patch Registry.__getitem__
        orig_reg_getitem = Registry.__getitem__

        def __sovereign_reg_getitem__(self, model_name: str) -> Any:
            canonical_name = SOVEREIGN_MODEL_ALIASES.get(model_name, model_name)
            return orig_reg_getitem(self, canonical_name)

        Registry.__getitem__ = __sovereign_reg_getitem__

        _ORCHESTRATED = True
        _LOGGER.info("Sovereign ORM Registry Facade initialized successfully.")
    except Exception as exc:
        _LOGGER.critical("Fatal: Failed patching ORM Environment/Registry: %s", exc)
        raise


def sanitize_rpc_exception(exc: Exception) -> Dict[str, Any]:
    """
    Transforms internal database errors and stack traces into clean,
    hardened enterprise error payloads for JSON-RPC clients.
    """
    error_msg = str(exc)
    error_type = exc.__class__.__name__

    # Neutralize internal disk file paths
    error_msg = re.sub(r'File ".*?[\\/](?:odoo|addons)[\\/]', 'File "insilos://core/', error_msg)
    error_msg = re.sub(r'/home/[^/]+/[^/]+', '/opt/insilos', error_msg)

    # Sanitize physical DB table references to enterprise aliases
    for enterprise_name, physical_model in SOVEREIGN_MODEL_ALIASES.items():
        physical_table = physical_model.replace(".", "_")
        if physical_table in error_msg:
            error_msg = error_msg.replace(physical_table, enterprise_name)

    return {
        "code": 500,
        "name": f"Insilos.Enterprise.{error_type}",
        "message": error_msg,
        "data": {
            "platform": "Insilos Enterprise 20.0",
            "debug": False,
        }
    }
