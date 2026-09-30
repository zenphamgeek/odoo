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

        # If this module is a package, install recursive __getattr__ for subpackages
        if hasattr(self.target_module, "__path__"):
            odoo_pkg = "odoo" + self.insilos_name[len("insilos"):]
            _install_getattr_on_module(self.target_module, odoo_pkg)


class InsilosMetaPathFinder(importlib.abc.MetaPathFinder):
    """PEP 451 MetaPathFinder mapping 'insilos' namespace to 'odoo'."""

    def find_spec(self, fullname: str, path=None, target=None):
        if fullname != "insilos" and not fullname.startswith("insilos."):
            return None

        _ensure_odoo_addons_paths()
        odoo_name = "odoo" + fullname[len("insilos"):]

        # Fast path: check if odoo module is already in sys.modules
        target_mod = sys.modules.get(odoo_name)
        if target_mod is None:
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


def _submod_getattr(pkg_name: str):
    """Factory for dynamic attribute accessors on packages."""
    def _getattr(name: str):
        try:
            target_pkg = pkg_name
            if target_pkg.startswith("insilos."):
                target_pkg = "odoo." + target_pkg[len("insilos."):]
            elif target_pkg == "insilos":
                target_pkg = "odoo"

            if target_pkg == "odoo.addons":
                _ensure_odoo_addons_paths()

            odoo_full = f"{target_pkg}.{name}"
            mod = importlib.import_module(odoo_full)

            # Register in both odoo and insilos namespaces in sys.modules
            insilos_full = "insilos" + odoo_full[4:]

            sys.modules[odoo_full] = mod
            sys.modules[insilos_full] = mod

            # Set attribute on parent package
            pkg = sys.modules.get(pkg_name)
            if pkg:
                try:
                    setattr(pkg, name, mod)
                except Exception:
                    pass

            # Also set attribute on counterpart package
            alt_pkg_name = "insilos" + target_pkg[4:] if target_pkg.startswith("odoo") else "odoo" + target_pkg[len("insilos"):]
            alt_pkg = sys.modules.get(alt_pkg_name)
            if alt_pkg and alt_pkg is not pkg:
                try:
                    setattr(alt_pkg, name, mod)
                except Exception:
                    pass

            return mod
        except ImportError:
            raise AttributeError(f"module {pkg_name!r} has no attribute {name!r}")
    return _getattr


def _install_getattr_on_module(mod, pkg_name: str) -> None:
    """Safely attach or wrap __getattr__ on a module object."""
    if mod is None:
        return
    orig_getattr = getattr(mod, "__getattr__", None)
    if orig_getattr is None:
        mod.__getattr__ = _submod_getattr(pkg_name)
    else:
        if getattr(orig_getattr, "_insilos_wrapped", False):
            return
        sub_getattr = _submod_getattr(pkg_name)
        def _wrapped_getattr(name: str):
            try:
                return orig_getattr(name)
            except (AttributeError, KeyError):
                return sub_getattr(name)
        _wrapped_getattr._insilos_wrapped = True
        mod.__getattr__ = _wrapped_getattr


def _patch_mute_logger() -> None:
    """Bridge mute_logger so muting 'insilos.X' also mutes 'odoo.X' and vice versa."""
    try:
        from odoo.tools.misc import mute_logger
        if getattr(mute_logger, "_insilos_patched", False):
            return
        orig_init = mute_logger.__init__

        def new_init(self, *loggers):
            expanded = []
            seen = set()
            for l in loggers:
                if l not in seen:
                    expanded.append(l)
                    seen.add(l)
                if isinstance(l, str):
                    partner = None
                    if l.startswith("insilos."):
                        partner = "odoo." + l[len("insilos."):]
                    elif l == "insilos":
                        partner = "odoo"
                    elif l.startswith("odoo."):
                        partner = "insilos." + l[len("odoo."):]
                    elif l == "odoo":
                        partner = "insilos"
                    if partner and partner not in seen:
                        expanded.append(partner)
                        seen.add(partner)
            orig_init(self, *expanded)

        mute_logger.__init__ = new_init
        mute_logger._insilos_patched = True
    except Exception as exc:
        _logger.debug("Failed patching mute_logger: %s", exc)


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

        # Install dynamic __getattr__ on odoo module
        _install_getattr_on_module(odoo, "odoo")

        import odoo.addons
        sys.modules["insilos.addons"] = odoo.addons
        _install_getattr_on_module(odoo.addons, "odoo.addons")

        # Install dynamic __getattr__ on key subpackages
        for p in [
            "odoo.modules",
            "odoo.tools",
            "odoo.http",
            "odoo.tests",
            "odoo.orm",
            "odoo.service",
            "odoo.cli",
        ]:
            try:
                m = importlib.import_module(p)
                _install_getattr_on_module(m, p)
            except Exception:
                pass

        # Proactively alias key core subpackages into sys.modules and odoo/insilos attributes
        core_subpackages = [
            "models", "fields", "api", "tools", "http",
            "modules", "sql_db", "exceptions", "release",
            "service", "cli", "orm", "tests", "osv"
        ]
        for name in core_subpackages:
            try:
                mod = importlib.import_module(f"odoo.{name}")
                sys.modules[f"insilos.{name}"] = mod
                setattr(odoo, name, mod)
            except Exception:
                pass

        # Install mute_logger bridge
        _patch_mute_logger()

        # Install logger manager aliasing bridge
        _patch_logger_manager()

    except Exception as exc:
        _logger.warning("Error initializing insilos namespace aliases: %s", exc)


def _alias_core_loggers() -> None:
    """Proactively alias core odoo and insilos loggers in logging.Logger.manager."""
    try:
        import logging
        manager = logging.Logger.manager
        core_subs = [
            "",
            "registry",
            "sql_db",
            "modules.loading",
            "modules.module",
            "service.server",
            "service.server.ThreadedServer",
            "service.server.PreforkServer",
            "http",
            "http.server",
            "http.router",
            "models",
            "fields",
            "tools.config",
            "addons.bus.websocket",
            "addons.base.models.ir_cron",
            "addons.base.models.ir_model",
            "addons.base.models.ir_ui_view",
            "addons.base.models.res_partner",
            "addons.base.models.ir_config_parameter",
            "addons.base.models.ir_actions.server_action_safe_eval",
        ]
        for sub in core_subs:
            odoo_name = f"odoo.{sub}" if sub else "odoo"
            insilos_name = f"insilos.{sub}" if sub else "insilos"
            l = logging.getLogger(odoo_name)
            manager.loggerDict[insilos_name] = l
            manager.loggerDict[odoo_name] = l

        for name, log_obj in list(manager.loggerDict.items()):
            if isinstance(log_obj, logging.Logger):
                if name == "odoo":
                    manager.loggerDict["insilos"] = log_obj
                elif name.startswith("odoo."):
                    manager.loggerDict[f"insilos.{name[5:]}"] = log_obj
                elif name == "insilos":
                    manager.loggerDict["odoo"] = log_obj
                elif name.startswith("insilos."):
                    manager.loggerDict[f"odoo.{name[8:]}"] = log_obj
    except Exception as exc:
        _logger.debug("Failed pre-aliasing core loggers: %s", exc)


def _patch_logger_manager() -> None:
    """Bridge logging.Logger.manager so logging.getLogger('insilos.*') and
    logging.getLogger('odoo.*') resolve to the exact same logger instances.
    """
    try:
        import logging
        manager = logging.Logger.manager
        if getattr(manager, "_insilos_aliased", False):
            return

        orig_getLogger = manager.getLogger

        def _bridged_getLogger(name, *args, **kwargs):
            if not isinstance(name, str):
                return orig_getLogger(name, *args, **kwargs)

            # Determine counterpart name
            if name == "insilos":
                odoo_name = "odoo"
                insilos_name = "insilos"
            elif name.startswith("insilos."):
                odoo_name = "odoo." + name[len("insilos."):]
                insilos_name = name
            elif name == "odoo":
                odoo_name = "odoo"
                insilos_name = "insilos"
            elif name.startswith("odoo."):
                odoo_name = name
                insilos_name = "insilos." + name[len("odoo."):]
            else:
                return orig_getLogger(name, *args, **kwargs)

            # Resolve canonical logger under odoo_name
            target_logger = orig_getLogger(odoo_name, *args, **kwargs)

            # Cross-alias in manager.loggerDict
            manager.loggerDict[insilos_name] = target_logger
            manager.loggerDict[odoo_name] = target_logger

            return target_logger

        manager.getLogger = _bridged_getLogger
        manager._insilos_aliased = True

        # Pre-alias core loggers right away
        _alias_core_loggers()

    except Exception as exc:
        _logger.debug("Failed patching logging.Logger.manager: %s", exc)


def uninstall() -> None:
    """Uninstall the Insilos import hook from sys.meta_path."""
    global _FINDER_INSTANCE
    sys.meta_path[:] = [f for f in sys.meta_path if not isinstance(f, InsilosMetaPathFinder)]
    _FINDER_INSTANCE = None
