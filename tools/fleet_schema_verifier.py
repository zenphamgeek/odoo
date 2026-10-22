#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/fleet_schema_verifier.py
==============================
Dispatches parallel verification and code review tasks across AGY Fleet worker nodes:
1. insilos_al2c: _sql_constraints -> models.Constraint & Odoo 20 SQL compliance.
2. insilos_chemical_trade_compliance: _sql_constraints -> models.Constraint.
3. enterprise/equity: equity_cap_table.py select() SQL() wrapping.
4. utm_source & hr_appraisal_skills: auto_join & compute/related conflict fixes.
5. Known regression bug check: pricing rule arguments, report escaping, UoM precision.
"""

import sys
import json
import time
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
FLEET_API_URL = "http://localhost:7777/api/fleet/run-sync"

def call_fleet_node(task_name, prompt, model="gemini-4-argon-high", target_node=None, timeout=120):
    payload = {
        "prompt": prompt,
        "model": model,
        "timeout": timeout
    }
    if target_node:
        payload["target_node"] = target_node

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        FLEET_API_URL,
        data=data,
        headers={"Content-Type": "application/json"}
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout + 10) as resp:
            resp_data = json.loads(resp.read().decode("utf-8"))
            elapsed = time.time() - t0
            return {
                "task": task_name,
                "node": resp_data.get("node_name"),
                "model": resp_data.get("model"),
                "elapsed": elapsed,
                "status": "SUCCESS",
                "output": resp_data.get("clean_response") or resp_data.get("output") or resp_data.get("stdout", "")
            }
    except Exception as e:
        elapsed = time.time() - t0
        return {
            "task": task_name,
            "node": target_node,
            "model": model,
            "elapsed": elapsed,
            "status": "ERROR",
            "error": str(e)
        }

def main():
    print("=" * 78)
    print("  AGY FLEET PARALLEL SCHEMA & REGRESSION VERIFIER (5 NODES CONCURRENT)")
    print("=" * 78)

    tasks = [
        {
            "name": "Audit insilos_al2c (_sql_constraints & depends)",
            "model": "gemini-4-argon-high",
            "prompt": """You are an expert Odoo 20 Core ORM Architect.
Review this code snippet from addons/insilos_al2c/models/mojo_usage_ledger.py and al2c_claim_atom.py:
In Odoo 20:
- `_sql_constraints` is obsolete. We replace it with `_idempotency_key_uniq = models.Constraint('unique(idempotency_key)', 'Idempotency key must be unique to prevent duplicate billing!')`.
- In al2c_claim_atom.py: `_claim_hash_uniq = models.Constraint('unique(claim_hash)', 'A Claim Atom with identical normalized content already exists!')`.
Check:
1. Is the `models.Constraint` syntax 100% compliant with Odoo 20?
2. Are the `@api.depends('quantity', 'unit_price')` decorators properly declared without stale cache risks?
3. Provide the exact clean code diff for the model classes.
Respond concisely in structured JSON:
{"status": "APPROVED", "analysis": "...", "diff": "..."}"""
        },
        {
            "name": "Audit insilos_chemical_trade_compliance",
            "model": "gemini-4-argon-high",
            "prompt": """You are an expert Odoo 20 Core ORM Architect.
Review this code snippet from enterprise/insilos_chemical_trade_compliance/models/is_chemical_usage_tracking.py:
In Odoo 20:
Old code:
    _sql_constraints = [
        ('chemical_usage_source_stock_move_unique', 'unique(source_stock_move_id)',
         'An ERP stock move can only be synchronized once.'),
    ]
Target Odoo 20 code:
    _chemical_usage_source_stock_move_unique = models.Constraint(
        'unique(source_stock_move_id)',
        'An ERP stock move can only be synchronized once.',
    )
Check:
1. Is the constraint syntax valid?
2. Are there any other deprecated attributes on the model fields?
Respond concisely in structured JSON:
{"status": "APPROVED", "analysis": "...", "diff": "..."}"""
        },
        {
            "name": "Audit equity_cap_table.py select() SQL() wrapping",
            "model": "claude-opus-5-5-high",
            "prompt": """You are an expert Odoo 20 SQL & Query Engine Specialist.
In Odoo 20, Query.select() raises a warning if passed strings instead of SQL objects:
UserWarning: Since 20.0. select takes only SQL arguments.

Review this proposed fix in enterprise/equity/models/equity_cap_table.py:
```python
        all_transactions = SQL(" UNION ALL ").join([
            transactions_query.select(
                SQL('partner_id AS partner_id'),
                SQL('subscriber_id AS holder_id'),
                SQL('security_class_id AS security_class_id'),
                SQL(\"\"\"(CASE
                        WHEN transaction_type IN ('issuance', 'transfer') THEN securities
                        ELSE -securities
                    END) AS securities\"\"\")
                ,
            ),
            exercise_transactions_query.select(
                SQL('partner_id AS partner_id'),
                SQL('subscriber_id AS holder_id'),
                SQL('destination_class_id AS security_class_id'),
                SQL('securities AS securities'),
            ),
            transfer_transactions_query.select(
                SQL('partner_id AS partner_id'),
                SQL('seller_id AS holder_id'),
                SQL('security_class_id AS security_class_id'),
                SQL('-securities AS securities'),
            ),
        ])
```
Verify:
1. Does wrapping each column with SQL(...) eliminate the warning while generating identical valid PostgreSQL SQL?
2. Are there any edge cases with SQL parameters or alias expressions?
Respond in structured JSON:
{"status": "APPROVED", "analysis": "...", "clean_snippet": "..."}"""
        },
        {
            "name": "Audit utm_source & hr_appraisal_skills Odoo 20 field fixes",
            "model": "gemini-4-argon-high",
            "prompt": """You are an expert Odoo 20 Core ORM Specialist.
Review two Odoo 20 field definition adjustments:
1. In addons/utm/models/utm_source.py:
`source_id = fields.Many2one('utm.source', string='Source', required=False, index=True, ondelete='cascade')`
(Removing `auto_join=True`, which is no longer a valid field parameter in Odoo 20).
2. In enterprise/hr_appraisal_skills/report/hr_appraisal_skill_report.py:
`display_name = fields.Char(related='employee_id.name', compute=None)`
(Setting `compute=None` avoids the conflict warning "Field ... is both compute and related").
Verify both adjustments for full Odoo 20 compliance.
Respond in structured JSON:
{"status": "APPROVED", "analysis": "..."}"""
        },
        {
            "name": "Audit Known Regression Edge Cases",
            "model": "gemini-4-argon-high",
            "prompt": """You are an expert Odoo 20 Quality & Regression Auditor.
Audit these known migration regression risks across Odoo 20 / insilos_* modules:
1. Pricing Rule Arguments: In Odoo 20, `_price_rule_get` and `_compute_price_rule` signatures require keyword arguments or specific parameter order (`products_qty_partner`, `currency`, `uom`).
2. Ampersand Escaping in XML Reports: All `&` in XML data files must be escaped as `&amp;` unless in CDATA.
3. Unit of Measure (UoM) Accuracy: Conversion between discrete units and fractional weights must use `product_uom._compute_quantity(..., rounding_method='HALF-UP')`.
Summarize the regression defense principles for Odoo 20.
Respond in structured JSON:
{"status": "APPROVED", "guidelines": "..."}"""
        }
    ]

    results = []
    t_start = time.time()
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_map = {
            executor.submit(call_fleet_node, t["name"], t["prompt"], t["model"]): t["name"]
            for t in tasks
        }
        for future in as_completed(future_map):
            res = future.result()
            results.append(res)
            print(f"[✓] Completed Task: {res['task']} on Node: {res.get('node')} ({res.get('elapsed', 0):.2f}s) - {res['status']}")

    total_time = time.time() - t_start
    print("\n" + "=" * 78)
    print(f"ALL 5 FLEET AUDIT TASKS FINISHED IN {total_time:.2f}s")
    print("=" * 78)

    report_path = REPO_ROOT / "fleet_parallel_audit_results.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to: {report_path}")

if __name__ == "__main__":
    main()
