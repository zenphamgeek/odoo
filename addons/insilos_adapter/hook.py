# -*- coding: utf-8 -*-
# Part of Insilos. See LICENSE file for full copyright and licensing details.

"""
Insilos Python Import Hook Adapter (PEP 451 MetaPathFinder & Loader)
===================================================================
Provides transparent resolution for the 'insilos' namespace mapping to 'odoo':
    import insilos
    from insilos import models, fields, api, http, tools
    from insilos.addons import crm, account
    from insilos.models import Model

This adapter operates strictly outside core upstream files, adhering to
the Hexagonal (Ports & Adapters) architecture pattern.
"""

import importlib
import importlib.abc
import importlib.machinery
import importlib.util
import logging
import os
import sys

_logger = logging.getLogger("insilos.adapter.hook")


def _ensure_odoo_addons_paths() -> None:
    """Ensure standard repository addons paths are available in odoo.addons.__path__."""
    try:
        import odoo
        import odoo.addons

        # Locate repository root relative to current file, odoo module, or cwd
        repo_roots = []
        try:
            current_file_dir = os.path.dirname(os.path.abspath(__file__))
            # addons/insilos_adapter/hook.py -> repo_root is 2 levels up
            repo_roots.append(os.path.dirname(os.path.dirname(current_file_dir)))
            repo_roots.append(os.path.dirname(current_file_dir))
        except Exception:
            pass

        if hasattr(odoo, "__path__") and odoo.__path__:
            first_path = list(odoo.__path__)[0]
            repo_roots.append(os.path.dirname(os.path.abspath(first_path)))

        candidates = []
        for r in repo_roots:
            if r and os.path.isdir(r):
                candidates.extend([
                    os.path.join(r, "odoo", "addons"),
                    os.path.join(r, "addons"),
                    os.path.join(r, "enterprise"),
                ])

        cwd = os.getcwd()
        candidates.extend([
            os.path.join(cwd, "odoo", "addons"),
            os.path.join(cwd, "addons"),
            os.path.join(cwd, "enterprise"),
            "/home/zen/O20/odoo/addons",
            "/home/zen/O20/addons",
            "/home/zen/O20/enterprise",
        ])

        for p in candidates:
            if os.path.isdir(p) and p not in odoo.addons.__path__:
                odoo.addons.__path__.append(p)

        # Crucial for PEP 420 _NamespacePath: prevent Python from resetting __path__ to sys.path
        if hasattr(odoo.addons, "__path__"):
            odoo.addons.__path__._path_finder = lambda *a: None

        importlib.invalidate_caches()
    except Exception as exc:
        _logger.debug("Failed ensuring odoo.addons paths: %s", exc)


class InsilosLoader(importlib.abc.Loader):
    """PEP 451 Loader that transparently proxies modules to odoo."""

    def __init__(self, target_module, insilos_name: str):
        self.target_module = target_module
        self.insilos_name = insilos_name

    def create_module(self, spec):
        return self.target_module

    def exec_module(self, module):
        # Register the alias in sys.modules
        sys.modules[self.insilos_name] = self.target_module
        if "." in self.insilos_name:
            parent_name, attr = self.insilos_name.rsplit(".", 1)
            parent_mod = sys.modules.get(parent_name)
            if parent_mod:
                try:
                    setattr(parent_mod, attr, self.target_module)
                except Exception:
                    pass


class InsilosMetaPathFinder(importlib.abc.MetaPathFinder):
    """PEP 451 MetaPathFinder mapping 'insilos' namespace to 'odoo'."""

    def find_spec(self, fullname: str, path=None, target=None):
        if fullname != "insilos" and not fullname.startswith("insilos."):
            return None

        _ensure_odoo_addons_paths()
        odoo_name = "odoo" + fullname[len("insilos"):]

        try:
            target_mod = importlib.import_module(odoo_name)
        except ImportError:
            return None

        is_pkg = hasattr(target_mod, "__path__")
        loader = InsilosLoader(target_mod, fullname)
        spec = importlib.util.spec_from_loader(
            fullname,
            loader,
            is_package=is_pkg,
        )
        if is_pkg and hasattr(target_mod, "__path__"):
            spec.submodule_search_locations = list(target_mod.__path__)

        return spec


_FINDER_INSTANCE = None


def _odoo_getattr(name: str):
    """Dynamic attribute accessor for odoo module to support insilos.<submodule>."""
    try:
        mod = importlib.import_module(f"odoo.{name}")
        import odoo
        setattr(odoo, name, mod)
        return mod
    except ImportError:
        raise AttributeError(f"module 'odoo' has no attribute {name!r}")


def _addons_getattr(name: str):
    """Dynamic attribute accessor for odoo.addons module to support insilos.addons.<addon>."""
    _ensure_odoo_addons_paths()
    try:
        mod = importlib.import_module(f"odoo.addons.{name}")
        import odoo.addons
        setattr(odoo.addons, name, mod)
        return mod
    except ImportError:
        raise AttributeError(f"module 'odoo.addons' has no attribute {name!r}")


def install() -> None:
    """Install the Insilos PEP 451 import hook into sys.meta_path."""
    global _FINDER_INSTANCE

    _ensure_odoo_addons_paths()

    # Insert finder if not present
    if not any(isinstance(finder, InsilosMetaPathFinder) for finder in sys.meta_path):
        _FINDER_INSTANCE = InsilosMetaPathFinder()
        sys.meta_path.insert(0, _FINDER_INSTANCE)

    # Alias top-level insilos to odoo
    try:
        import odoo
        sys.modules["insilos"] = odoo

        # Install __getattr__ on odoo module if not present
        if not hasattr(odoo, "__getattr__"):
            odoo.__getattr__ = _odoo_getattr

        import odoo.addons
        sys.modules["insilos.addons"] = odoo.addons
        if not hasattr(odoo.addons, "__getattr__"):
            odoo.addons.__getattr__ = _addons_getattr

    except Exception as exc:
        _logger.warning("Error initializing insilos namespace aliases: %s", exc)


def uninstall() -> None:
    """Uninstall the Insilos import hook from sys.meta_path."""
    global _FINDER_INSTANCE
    sys.meta_path[:] = [f for f in sys.meta_path if not isinstance(f, InsilosMetaPathFinder)]
    _FINDER_INSTANCE = None
