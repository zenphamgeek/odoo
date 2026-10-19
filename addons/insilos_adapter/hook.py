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
import threading

_logger = logging.getLogger("insilos.adapter.hook")
_PATCH_LOCK = threading.Lock()


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

        persistent_custom = "/var/lib/insilos/filestore/custom_addons"
        if os.path.isdir(persistent_custom) and persistent_custom not in candidates:
            candidates.append(persistent_custom)

        for p in candidates:
            if os.path.isdir(p) and p not in odoo.addons.__path__:
                odoo.addons.__path__.append(p)

        # Crucial for PEP 420 _NamespacePath: prevent Python from resetting __path__ to sys.path
        if hasattr(odoo.addons, "__path__") and hasattr(odoo.addons.__path__, "_path_finder"):
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

        # Dynamically inject sovereign crash reporting domain mapping
        _inject_runtime_report_domain()

        # Patch router db_filter and serve_nodb to guarantee zero-drop reporting
        _patch_router_db_filter()

        # Dynamically patch sovereign model view & action aliasing
        _patch_sovereign_model_view_aliasing()

        # Enforce Sovereign v26.0 release & manifest compatibility series
        _patch_sovereign_version_26()

    except Exception as exc:
        _logger.warning("Error initializing insilos namespace aliases: %s", exc)


def _patch_sovereign_version_26() -> None:
    """Enforce Sovereign v26.0 release series and compatible manifest version validation (26.0, 20.0, 19.1)."""
    try:
        import odoo.release as release
        import odoo.modules.module as mod_module

        release.version_info = (26, 0, 0, release.FINAL, 0, '')
        release.series = release.serie = release.major_version = '26.0'
        release.version = '26.0'
        release.COMPATIBLE_SERIES = frozenset({'26.0', '20.0', '19.1'})

        def _sovereign_adapt_version(version: str) -> str:
            version_str_parts = str(version).split('.')
            if not (2 <= len(version_str_parts) <= 5):
                raise ValueError(f"Invalid version {version!r}, must have between 2 and 5 parts")
            serie = release.major_version
            if version.startswith(serie) and not version_str_parts[0].isdigit():
                version_str_parts[0] = ''.join(c for c in version_str_parts[0] if c.isdigit())
            try:
                version_parts = [int(v) for v in version_str_parts]
            except ValueError as e:
                raise ValueError(f"Invalid version {version!r}") from e
            compatible_series = getattr(release, 'COMPATIBLE_SERIES', {'26.0', '20.0', '19.1'})
            has_compat_prefix = any(str(version).startswith(f"{s}.") for s in compatible_series)
            if len(version_parts) <= 3 and not has_compat_prefix:
                return f"{serie}.{version}"
            return str(version)

        def _sovereign_check_version(version: str, should_raise: bool = True) -> bool:
            version = _sovereign_adapt_version(version)
            compatible_prefixes = tuple(f"{s}." for s in getattr(release, 'COMPATIBLE_SERIES', {'26.0', '20.0', '19.1'}))
            if version.startswith(compatible_prefixes):
                return True
            if should_raise:
                raise ValueError(
                    f"Invalid version {version!r}. Modules should have a version in format `x.y`, `x.y.z`,"
                    f" `26.0.x.y` or `26.0.x.y.z`."
                )
            return False

        mod_module.adapt_version = _sovereign_adapt_version
        mod_module.check_version = _sovereign_check_version
    except Exception as exc:
        _logger.debug("Failed patching sovereign version 26: %s", exc)


def _patch_sovereign_model_view_aliasing() -> None:
    """Patches ir.ui.view and ir.actions to resolve sovereign model aliases dynamically across all pod rollouts."""
    try:
        with _PATCH_LOCK:
            from odoo.addons.base.models.ir_ui_view import View
            from odoo.addons.base.models.ir_actions import IrActions
            from odoo.orm.models import SOVEREIGN_MODEL_ALIASES

        # 1. Patch View._get_default_view_domain
        if not getattr(View._get_default_view_domain, "_insilos_aliased", False):
            orig_domain = View._get_default_view_domain

            def _sovereign_default_view_domain(self, model=None, view_type=None, *args, **kwargs):
                target_model = model or getattr(self, 'model', None)
                models = [target_model] if target_model else []
                rev = getattr(self.pool, "REVERSE_MODEL_ALIASES", {})
                sov = getattr(self.pool, "SOVEREIGN_MODEL_ALIASES", SOVEREIGN_MODEL_ALIASES)
                if target_model in rev:
                    models.append(rev[target_model])
                if target_model in sov:
                    models.append(sov[target_model])
                models = list(set(models))
                from odoo.orm.domains import Domain
                if view_type:
                    return Domain([('model', 'in', models), ('type', '=', view_type), ('mode', '=', 'primary')])
                return Domain([('model', 'in', models), ('mode', '=', 'primary')])

            _sovereign_default_view_domain._insilos_aliased = True
            View._get_default_view_domain = _sovereign_default_view_domain

        # 2. Patch View.get_views
        if not getattr(View.get_views, "_insilos_aliased", False):
            orig_get_views = View.get_views

            def _sovereign_get_views(self, views, options=None):
                result = orig_get_views(self, views, options=options)
                if 'models' in result and isinstance(result['models'], dict):
                    rev = getattr(self.pool, "REVERSE_MODEL_ALIASES", {})
                    sov = getattr(self.pool, "SOVEREIGN_MODEL_ALIASES", SOVEREIGN_MODEL_ALIASES)
                    for alias, target in sov.items():
                        if target in result['models'] and alias not in result['models']:
                            result['models'][alias] = result['models'][target]
                    for alias, target in rev.items():
                        if target in result['models'] and alias not in result['models']:
                            result['models'][alias] = result['models'][target]
                return result

            _sovereign_get_views._insilos_aliased = True
            View.get_views = _sovereign_get_views

        # 3. Patch IrActions._get_bindings
        if not getattr(IrActions._get_bindings, "_insilos_aliased", False):
            orig_bindings = IrActions._get_bindings

            def _sovereign_get_bindings(self, model_name):
                result = orig_bindings(self, model_name)
                rev = getattr(self.pool, "REVERSE_MODEL_ALIASES", {})
                sov = getattr(self.pool, "SOVEREIGN_MODEL_ALIASES", SOVEREIGN_MODEL_ALIASES)
                alt_model = rev.get(model_name) or sov.get(model_name)
                if alt_model:
                    alt_result = orig_bindings(self, alt_model)
                    for key, actions in alt_result.items():
                        existing_ids = {a['id'] for a in result.get(key, [])}
                        for a in actions:
                            if a['id'] not in existing_ids:
                                result.setdefault(key, []).append(a)
                return result

            _sovereign_get_bindings._insilos_aliased = True
            IrActions._get_bindings = _sovereign_get_bindings

        # 4. Patch Many2many physical column self-healing
        from odoo.orm.fields_relational import Many2many
        if not getattr(Many2many.read, "_insilos_aliased", False):
            orig_m2m_read = Many2many.read
            orig_m2m_write_batch = Many2many.write_batch

            SOVEREIGN_TABLE_LEGACY = {
                'catalog_item': 'product_template',
                'catalog_sku': 'product_product',
                'party_master': 'res_partner',
                'organization_unit': 'res_company',
                'system_attachment': 'ir_attachment',
                'party_classification': 'res_partner_category',
                'procurement_order': 'purchase_order',
                'procurement_order_line': 'purchase_order_line',
                'order_header': 'sale_order',
                'order_line': 'sale_order_line',
                'logistics_transfer': 'stock_picking',
                'logistics_movement': 'stock_move',
                'manufacturing_order': 'mrp_production',
                'manufacturing_bom': 'mrp_bom',
                'finance_journal_entry': 'account_move',
                'finance_journal_line': 'account_move_line',
            }

            def _heal_m2m_columns(field, cr, model_table=None, comodel_table=None):
                if not field.relation:
                    return
                from odoo.tools import sql
                if field.column1 and not sql.column_exists(cr, field.relation, field.column1):
                    candidates = []
                    if model_table:
                        leg = SOVEREIGN_TABLE_LEGACY.get(model_table)
                        if leg:
                            candidates.extend([f'{leg}_id', f'{model_table}_id'])
                    for leg_k, leg_v in SOVEREIGN_TABLE_LEGACY.items():
                        candidates.extend([f'{leg_v}_id', f'{leg_k}_id'])
                    for c in candidates:
                        if sql.column_exists(cr, field.relation, c):
                            field.column1 = c
                            break
                if field.column2 and not sql.column_exists(cr, field.relation, field.column2):
                    candidates = []
                    if comodel_table:
                        leg = SOVEREIGN_TABLE_LEGACY.get(comodel_table)
                        if leg:
                            candidates.extend([f'{leg}_id', f'{comodel_table}_id'])
                    for leg_k, leg_v in SOVEREIGN_TABLE_LEGACY.items():
                        candidates.extend([f'{leg_v}_id', f'{leg_k}_id'])
                    for c in candidates:
                        if sql.column_exists(cr, field.relation, c):
                            field.column2 = c
                            break

            def _sovereign_m2m_read(self, records):
                _heal_m2m_columns(self, records.env.cr, records._table)
                return orig_m2m_read(self, records)

            def _sovereign_m2m_write_batch(self, records_commands_list, create=False):
                if records_commands_list:
                    recs = records_commands_list[0][0]
                    _heal_m2m_columns(self, recs.env.cr, recs._table)
                return orig_m2m_write_batch(self, records_commands_list, create=create)

            _sovereign_m2m_read._insilos_aliased = True
            _sovereign_m2m_write_batch._insilos_aliased = True
            Many2many.read = _sovereign_m2m_read
            Many2many.write_batch = _sovereign_m2m_write_batch

        _logger.info("Successfully installed Sovereign Model View Aliasing runtime hooks")
    except Exception as e:
        _logger.debug("Deferred sovereign model view aliasing patch: %s", e)


def _patch_router_db_filter() -> None:
    """Patches odoo.http.router.db_filter and serve_nodb to guarantee report.insilos.com routes correctly."""
    try:
        import sys
        if "odoo.http" not in sys.modules:
            return
        with _PATCH_LOCK:
            import odoo.tools.config as config
            from odoo.http import router as http_router
            orig_db_filter = getattr(http_router, "_orig_db_filter", http_router.db_filter)
            orig_serve_nodb = getattr(http_router, "_orig_serve_nodb", http_router.serve_nodb)

            def patched_db_filter(dbs, host=None):
                if host:
                    clean_host = host.partition(':')[0].removeprefix('www.')
                    if clean_host in ('report.insilos.com', 'report.insilost.com'):
                        # Sovereign invariant: report.insilos.com operates in pure NoDB headless mode.
                        # Zero database binding, zero web/website modules, maximum throughput.
                        return []
                return orig_db_filter(dbs, host)

            def patched_serve_nodb(request):
                host = request.httprequest.host if hasattr(request, 'httprequest') and request.httprequest else ''
                clean_host = host.partition(':')[0].removeprefix('www.')
                path = request.httprequest.path.rstrip('/')

                if clean_host in ('report.insilos.com', 'report.insilost.com'):
                    import json
                    from odoo.http import Response
                    if path in ('/api/v1/runtime-report', '/insilos/runtime_error/relay'):
                        try:
                            from odoo.addons.insilos_adapter.controllers.runtime_report_gateway import RuntimeReportGateway
                            gateway = RuntimeReportGateway()
                            if path == '/insilos/runtime_error/relay':
                                return gateway.local_runtime_error_relay()
                            else:
                                return gateway.ingress_runtime_report()
                        except Exception as e:
                            _logger.warning("Error in nodb gateway dispatch: %s", e)
                            return Response(json.dumps({'error': 'Internal Gateway Error', 'detail': str(e)}), status=500, content_type='application/json')
                    elif path in ('', '/', '/health', '/api/v1/health'):
                        return Response(
                            json.dumps({
                                'service': 'Insilos Sovereign Runtime Reporting Gateway',
                                'status': 'online',
                                'mode': 'headless-lightweight',
                                'protocol': 'AL2C-v1',
                                'web_module': 'disabled',
                                'endpoints': {
                                    'ingress': '/api/v1/runtime-report',
                                    'health': '/api/v1/health',
                                }
                            }),
                            status=200, content_type='application/json'
                        )
                    else:
                        return Response(
                            json.dumps({
                                'service': 'Insilos Sovereign Runtime Reporting Gateway',
                                'status': 'headless_api_only',
                                'message': 'Web UI and login modules are disabled on this endpoint for maximum performance.',
                                'path': path,
                            }),
                            status=200 if path in ('/web/login', '/web') else 404, content_type='application/json'
                        )

                return orig_serve_nodb(request)

            http_router._orig_db_filter = orig_db_filter
            http_router._orig_serve_nodb = orig_serve_nodb
            http_router.db_filter = patched_db_filter
            http_router.serve_nodb = patched_serve_nodb
    except Exception as e:
        _logger.debug("Deferred router db_filter / serve_nodb patching: %s", e)


def _inject_runtime_report_domain() -> None:
    """Ensures report.insilos.com is NOT bound to heavy tenant databases in dbfilter_map, ensuring NoDB headless mode."""
    try:
        import json
        import odoo.tools.config as config
        dfm = config.get("dbfilter_map")
        if dfm:
            if isinstance(dfm, str):
                try:
                    dfm_dict = json.loads(dfm)
                except Exception:
                    dfm_dict = {}
            elif isinstance(dfm, dict):
                dfm_dict = dfm
            else:
                dfm_dict = {}
            modified = False
            for k in ["report.insilos.com", "report.insilost.com"]:
                if k in dfm_dict:
                    dfm_dict.pop(k, None)
                    modified = True
            if modified:
                config["dbfilter_map"] = json.dumps(dfm_dict)
    except Exception as e:
        _logger.debug("Could not sanitize report domain in dbfilter_map: %s", e)


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
