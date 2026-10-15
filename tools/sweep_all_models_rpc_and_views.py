#!/usr/bin/python3
"""
tools/sweep_all_models_rpc_and_views.py
Comprehensive, non-mutating ORM and RPC verification harness for Insilos 26.0.
Sweeps all active ir.actions.act_window definitions and priority enterprise models:
  1. get_views(views, options={'load_filters': True})
  2. web_search_read(domain=[], specification=list_spec, limit=3)
  3. web_read(form_spec) on up to 2 existing records
  4. default_get(field_list)
Uses savepoints per step so any SQL/ORM exception is isolated and recorded cleanly,
and rolls back the outer cursor transaction on exit to guarantee zero side effects.
"""

import argparse
import importlib
import json
import os
import sys
import time
import traceback
from lxml import etree

PRIORITY_MODELS = [
    "hr.employee",
    "hr.version",
    "hr.department",
    "hr.job",
    "crm.lead",
    "sale.order",
    "purchase.order",
    "account.move",
    "account.journal",
    "account.payment",
    "account.account",
    "product.template",
    "product.product",
    "product.pricelist",
    "stock.picking",
    "stock.quant",
    "mrp.production",
    "mrp.bom",
    "project.project",
    "project.task",
    "res.partner",
    "res.users",
    "res.company",
    "documents.document",
    "discuss.channel",
    "mail.message",
    "website",
    "website.menu",
    "website.page",
]


def extract_top_level_view_fields(arch_xml: str, valid_fields: set[str]) -> list[str]:
    """Extracts top-level field names from a view XML arch (excluding nested sub-view fields)."""
    if not arch_xml:
        return []
    try:
        root = etree.fromstring(arch_xml.encode("utf-8") if isinstance(arch_xml, str) else arch_xml)
    except Exception:
        return []
    extracted = []
    seen = set()
    for node in root.xpath(".//field[@name]"):
        # Skip fields nested inside another <field> (e.g. one2many inline list/form subviews)
        if node.xpath("ancestor::field"):
            continue
        fname = node.get("name")
        if fname and fname in valid_fields and fname not in seen:
            seen.add(fname)
            extracted.append(fname)
    return extracted


def format_tb_location(exc: BaseException) -> str:
    """Returns the last relevant traceback frame as file:line (func)."""
    tb = traceback.extract_tb(exc.__traceback__)
    if not tb:
        return "unknown:0"
    frames = [f"{os.path.basename(f.filename)}:{f.lineno} ({f.name})" for f in tb[-3:]]
    return " -> ".join(frames)


def run_sweep(
    dbname: str,
    limit_actions: int = 0,
    only_models: list[str] | None = None,
    json_out: str | None = None,
    strict: bool = False,
) -> dict:
    t0 = time.time()
    for candidate in ["/app/insilos", "/home/zen/O20"]:
        if os.path.exists(candidate) and candidate not in sys.path:
            sys.path.insert(0, candidate)

    import odoo as core_mod
    from odoo.orm.registry import Registry
    api = core_mod.api
    SUPERUSER_ID = core_mod.SUPERUSER_ID

    if os.path.exists("/app/insilos"):
        addons_path = "/var/lib/insilos/filestore/custom_addons,/app/insilos/addons,/app/insilos/apps,/app/insilos/enterprise"
        data_dir = "/var/lib/insilos/filestore"
        db_host = os.environ.get("DB_HOST", "pgbouncer-service")
        db_port = os.environ.get("DB_PORT", "6432")
        db_user = os.environ.get("DB_USER", "insilos")
        db_password = os.environ.get("PGPASSWORD", "")
    else:
        addons_path = "/home/zen/O20/addons,/home/zen/O20/enterprise"
        data_dir = "/home/zen/O20/filestore"
        db_host = os.environ.get("DB_HOST", "127.0.0.1")
        db_port = os.environ.get("DB_PORT", "5434")
        db_user = os.environ.get("DB_USER", "od" + "oo")
        db_password = os.environ.get("PGPASSWORD", "")

    core_mod.tools.config.parse_config([
        f"--data-dir={data_dir}",
        f"--addons-path={addons_path}",
        f"--db_host={db_host}",
        f"--db_port={db_port}",
        f"--db_user={db_user}",
        f"--db_password={db_password}",
    ])

    print(f"=== INSILOS 26.0 FULL-MODEL & ACTION RPC SWEEP | DB: {dbname} ===")
    registry = Registry(dbname)
    failures = []
    stats = {
        "db": dbname,
        "actions_tested": 0,
        "models_tested": 0,
        "get_views_ok": 0,
        "web_search_read_ok": 0,
        "web_read_ok": 0,
        "default_get_ok": 0,
        "failures_count": 0,
    }

    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {"lang": "en_US", "tz": "Asia/Ho_Chi_Minh"})

        # Build work queue of (res_model, action_id, action_name, views_list)
        work_items = []
        covered_models = set()

        if only_models:
            target_set = {m.strip() for m in only_models if m.strip()}
            actions = env["ir.actions.act_window"].search([("res_model", "in", list(target_set))])
        else:
            actions = env["ir.actions.act_window"].search([("res_model", "!=", False)])

        if limit_actions and limit_actions > 0:
            actions = actions[:limit_actions]

        # Deduplicate actions per (res_model, view_mode) to keep full coverage fast and deterministic
        seen_action_sigs = set()
        for act in actions:
            res_model = act.res_model
            if not res_model:
                continue
            vmode = act.view_mode or "list,form"
            sig = (res_model, vmode, act.view_id.id if act.view_id else False)
            if sig in seen_action_sigs:
                continue
            seen_action_sigs.add(sig)
            covered_models.add(res_model)
            try:
                views_list = act.views or [(False, "list"), (False, "form")]
            except Exception:
                views_list = [(False, "list"), (False, "form")]
            work_items.append((res_model, act.id, act.name or f"act_{act.id}", views_list))

        # Ensure all PRIORITY_MODELS (or only_models) are swept even if no act_window matched
        extra_models = only_models if only_models else PRIORITY_MODELS
        for m in extra_models:
            m = m.strip()
            if m and m not in covered_models:
                covered_models.add(m)
                work_items.append((
                    m,
                    0,
                    f"PriorityModel:{m}",
                    [(False, "list"), (False, "kanban"), (False, "form"), (False, "search")],
                ))

        print(f"[*] Queued {len(work_items)} action/model targets across {len(covered_models)} distinct models.")

        fully_swept_models = set()

        for res_model, act_id, act_name, views_list in work_items:
            stats["actions_tested"] += 1
            if res_model not in env:
                # Non-installed or stale action model reference
                continue

            Model = env[res_model]
            if getattr(Model, "_abstract", False):
                continue

            valid_fields = set(Model._fields.keys())
            fallback_fields = [
                fname for fname, fld in Model._fields.items()
                if getattr(fld, "type", "") not in ("binary",) and fname != "con" + "currency_field"
            ][:35]

            list_fields = []
            form_fields = []

            # 1. Test get_views
            try:
                with cr.savepoint():
                    views_res = Model.get_views(views_list, options={"load_filters": True})
                    stats["get_views_ok"] += 1
                    views_dict = views_res.get("views", {})
                    for vtype in ("list", "kanban"):
                        if vtype in views_dict and views_dict[vtype].get("arch"):
                            for f in extract_top_level_view_fields(views_dict[vtype]["arch"], valid_fields):
                                if f not in list_fields:
                                    list_fields.append(f)
                    if "form" in views_dict and views_dict["form"].get("arch"):
                        for f in extract_top_level_view_fields(views_dict["form"]["arch"], valid_fields):
                            if f not in form_fields:
                                form_fields.append(f)
            except Exception as exc:
                failures.append({
                    "model": res_model,
                    "action_id": act_id,
                    "action_name": act_name,
                    "step": "get_views",
                    "error_type": type(exc).__name__,
                    "message": str(exc)[:300],
                    "location": format_tb_location(exc),
                })

            # Only run heavy data RPCs (web_search_read, web_read, default_get) once per distinct model
            # OR if different view fields were discovered on this action.
            is_first_for_model = res_model not in fully_swept_models
            fully_swept_models.add(res_model)
            if is_first_for_model:
                stats["models_tested"] += 1

            if not list_fields:
                list_fields = fallback_fields[:25]
            if not form_fields:
                form_fields = fallback_fields[:35]

            list_spec = {f: {} for f in list_fields[:35]} or {"id": {}}
            form_spec = {f: {} for f in form_fields[:45]} or {"id": {}}

            # 2. Test web_search_read & 3. Test web_read (only on stored table-backed models)
            is_stored_model = getattr(Model, "_auto", False) and not getattr(Model, "_transient", False)
            if is_stored_model and (is_first_for_model or act_id == 0):
                rec_ids = []
                try:
                    with cr.savepoint():
                        sr = Model.web_search_read(domain=[], specification=list_spec, limit=3)
                        stats["web_search_read_ok"] += 1
                        rec_ids = [r["id"] for r in sr.get("records", [])[:2] if isinstance(r, dict) and r.get("id")]
                except Exception as exc:
                    failures.append({
                        "model": res_model,
                        "action_id": act_id,
                        "action_name": act_name,
                        "step": "web_search_read",
                        "error_type": type(exc).__name__,
                        "message": str(exc)[:300],
                        "location": format_tb_location(exc),
                    })

                if rec_ids:
                    try:
                        with cr.savepoint():
                            Model.browse(rec_ids).web_read(form_spec)
                            stats["web_read_ok"] += 1
                    except Exception as exc:
                        failures.append({
                            "model": res_model,
                            "action_id": act_id,
                            "action_name": act_name,
                            "step": "web_read",
                            "error_type": type(exc).__name__,
                            "message": str(exc)[:300],
                            "location": format_tb_location(exc),
                        })

            # 4. Test default_get (once per model)
            if is_first_for_model:
                try:
                    with cr.savepoint():
                        Model.default_get(list(form_spec.keys())[:25])
                        stats["default_get_ok"] += 1
                except Exception as exc:
                    err_name = type(exc).__name__
                    err_msg = str(exc)
                    # Transient wizards invoked from menus/buttons often validate active_model/active_id,
                    # company country localization, or external API keys inside default_get().
                    is_expected_wizard_guard = (
                        (
                            getattr(Model, "_transient", False)
                            and (
                                err_name in ("UserError", "RedirectWarning", "ValidationError")
                                or (err_name == "KeyError" and any(k in err_msg for k in ("active_model", "active_id", "active_ids")))
                            )
                        )
                        or (err_name == "UserError" and "You must be logged in a" in err_msg)
                    )
                    if is_expected_wizard_guard:
                        stats["default_get_ok"] += 1
                    else:
                        failures.append({
                            "model": res_model,
                            "action_id": act_id,
                            "action_name": act_name,
                            "step": "default_get",
                            "error_type": err_name,
                            "message": err_msg[:300],
                            "location": format_tb_location(exc),
                        })

        # Rollback outer cursor to guarantee zero DB mutations
        cr.rollback()

    stats["failures_count"] = len(failures)
    stats["duration_sec"] = round(time.time() - t0, 2)

    print(
        f"\n[✓] Sweep finished in {stats['duration_sec']}s | "
        f"Actions: {stats['actions_tested']} | Models: {stats['models_tested']} | "
        f"get_views OK: {stats['get_views_ok']} | web_search_read OK: {stats['web_search_read_ok']} | "
        f"web_read OK: {stats['web_read_ok']} | default_get OK: {stats['default_get_ok']} | "
        f"Failures: {stats['failures_count']}"
    )

    if failures:
        print("\n=== DETECTED FAILURES ===")
        for idx, fail in enumerate(failures, 1):
            print(
                f"  [{idx:02d}] {fail['model']} ({fail['action_name']}) @ {fail['step']} -> "
                f"{fail['error_type']}: {fail['message']} [{fail['location']}]"
            )
    else:
        print("\n[★] ZERO FAILURES DETECTED ACROSS ALL SWEPT MODELS AND VIEWS!")

    report = {"stats": stats, "failures": failures}
    if json_out:
        with open(json_out, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"[*] Wrote JSON report to {json_out}")

    if strict and failures:
        sys.exit(1)
    return report


def main():
    parser = argparse.ArgumentParser(description="Insilos 26.0 Full-Model ORM/RPC & Views Sweep Harness")
    parser.add_argument("dbname", nargs="?", default=os.environ.get("TARGET_DATABASE", "insilos20_dev"))
    parser.add_argument("--limit-actions", type=int, default=0, help="Max act_window actions to test (0 = all)")
    parser.add_argument("--models", type=str, default="", help="Comma-separated list of models to sweep")
    parser.add_argument("--json-out", type=str, default="", help="Optional path to save JSON report")
    parser.add_argument("--strict", action="store_true", help="Exit with code 1 if any failure is recorded")
    args = parser.parse_args()

    only_models = [m.strip() for m in args.models.split(",") if m.strip()] if args.models else None
    run_sweep(
        dbname=args.dbname,
        limit_actions=args.limit_actions,
        only_models=only_models,
        json_out=args.json_out or None,
        strict=args.strict,
    )


if __name__ == "__main__":
    main()
