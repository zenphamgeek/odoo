#!/usr/bin/env python3
import ast
import os
import re

PAT = re.compile(r'\b(odoo(?:\s+s\.?a\.?)?|oca|odoo\s+community\s+association)\b', re.IGNORECASE)

# Technical allowlist for Python string literals that MUST NOT be altered
TECHNICAL_ALLOWLIST = {
    'odoo',
    'base',
    'ir.model',
    'odoo.addons',
    '@odoo/',
    'https://extract.api.odoo.com',
    'http://www.odoo.com',
    'https://www.odoo.com',
    'application/x-odoo',
    'Saodoo-001',
    'ODOO/',
    'INSILOS/',
}

class Visitor(ast.NodeVisitor):
    def __init__(self, filename):
        self.filename = filename
        self.hits = []

    def visit_Call(self, node):
        func_name = ''
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr

        # Check _("..."), _lt("..."), UserError("..."), ValidationError("...")
        if func_name in ('_', '_lt', 'UserError', 'ValidationError'):
            for arg in node.args:
                self._check_expr(arg, f"CALL:{func_name}")
        self.generic_visit(node)

    def visit_keyword(self, node):
        # Check string="...", help="..."
        if node.arg in ('string', 'help', 'placeholder', 'title'):
            self._check_expr(node.value, f"KEYWORD:{node.arg}")
        self.generic_visit(node)

    def _check_expr(self, expr, context):
        if isinstance(expr, ast.Constant) and isinstance(expr.value, str):
            val = expr.value.strip()
            if any(k in val for k in ['import ', 'from odoo', 'odoo.addons']):
                return
            if val in TECHNICAL_ALLOWLIST:
                return
            if PAT.search(val):
                self.hits.append((expr.lineno, context, val))
        elif isinstance(expr, ast.JoinedStr):
            # f-strings
            for part in expr.values:
                if isinstance(part, ast.Constant) and isinstance(part.value, str):
                    val = part.value.strip()
                    if val in TECHNICAL_ALLOWLIST:
                        continue
                    if PAT.search(val):
                        self.hits.append((expr.lineno, f"{context}:fstring", val))

def scan():
    all_hits = []
    for base in ['addons', 'enterprise', 'odoo/addons', 'odoo']:
        for root, dirs, files in os.walk(base):
            if any(x in root for x in ['.git', 'node_modules', '__pycache__', 'tests', 'test']):
                continue
            for f in files:
                if not f.endswith('.py'):
                    continue
                p = os.path.join(root, f)
                try:
                    with open(p, 'r', encoding='utf-8', errors='ignore') as fp:
                        tree = ast.parse(fp.read(), filename=p)
                    v = Visitor(p)
                    v.visit(tree)
                    if v.hits:
                        all_hits.append((p, v.hits))
                except Exception:
                    pass
    return all_hits

if __name__ == '__main__':
    all_hits = scan()
    total_files = len(all_hits)
    total_count = sum(len(hits) for p, hits in all_hits)
    print(f"Total files with Python AST branding hits: {total_files}")
    print(f"Total occurrences: {total_count}")
    for p, hits in all_hits:
        print(f"\nFile: {p} ({len(hits)} hits)")
        for lno, ctx, val in hits:
            print(f"  Line {lno} [{ctx}]: {val[:100]!r}")
