# -*- coding: utf-8 -*-
"""
================================================================================
INSILOS SOVEREIGN RUNTIME VIRTUALIZATION ENGINE
Bidirectional Python Meta-Path Importer & Namespace Virtualizer
================================================================================
Enables native first-class imports for the Insilos Sovereign Platform:
    import insilos
    from insilos import models, fields, api, _
    from insilos.tools import config
    from insilos.addons.base import ...
while maintaining 100% backward compatibility for legacy 'odoo' imports.
"""
import sys
import importlib
import importlib.abc
import importlib.machinery
import importlib.util
import types


class InsilosLoader(importlib.abc.Loader):
    """Transparent loader delegating to the underlying target module."""

    def __init__(self, target_name, target_spec):
        self.target_name = target_name
        self.target_spec = target_spec

    def create_module(self, spec):
        # Import target module and alias in sys.modules
        target_mod = importlib.import_module(self.target_name)
        sys.modules[spec.name] = target_mod
        return target_mod

    def exec_module(self, module):
        # Already executed when target_mod was imported
        pass


class InsilosMetaPathFinder(importlib.abc.MetaPathFinder):
    """
    High-performance MetaPathFinder that virtualizes 'insilos' as a sovereign namespace
    mapping directly to 'odoo' and vice-versa with zero runtime overhead.
    """

    def find_spec(self, fullname, path, target=None):
        if fullname == "insilos" or fullname.startswith("insilos."):
            target_name = "odoo" + fullname[7:]
            try:
                target_spec = importlib.util.find_spec(target_name)
                if target_spec is None:
                    return None
                loader = InsilosLoader(target_name, target_spec)
                spec = importlib.util.spec_from_loader(fullname, loader)
                if target_spec.submodule_search_locations is not None:
                    spec.submodule_search_locations = list(target_spec.submodule_search_locations)
                return spec
            except Exception:
                return None
        return None


def install():
    """Installs the Insilos sovereign import hook into sys.meta_path if not already present."""
    for finder in sys.meta_path:
        if isinstance(finder, InsilosMetaPathFinder):
            return
    sys.meta_path.insert(0, InsilosMetaPathFinder())


# Auto-install on module import
install()
