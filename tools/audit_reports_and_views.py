#!/usr/bin/env python3
import os
import re

pat_odoo = re.compile(r'\bodoo\b', re.IGNORECASE)
pat_oca = re.compile(r'\b(?:oca|odoo community association)\b', re.IGNORECASE)
pat_sa = re.compile(r'\bodoo\s+s\.?a\.?\b', re.IGNORECASE)

xml_attrs = re.compile(r'''(?:string|help|placeholder|title|confirm)=["']([^"']+)["']''', re.IGNORECASE)

results = []

for base in ['addons', 'enterprise', 'odoo/addons']:
    for root, dirs, files in os.walk(base):
        if any(x in root for x in ['.git', 'node_modules', '__pycache__', 'tests', 'test']):
            continue
        for f in files:
            if not f.endswith('.xml'):
                continue
            p = os.path.join(root, f)
            try:
                with open(p, 'r', encoding='utf-8', errors='ignore') as fp:
                    content = fp.read()
                
                # Check attributes
                for m in xml_attrs.finditer(content):
                    val = m.group(1).strip()
                    if pat_odoo.search(val) or pat_oca.search(val) or pat_sa.search(val):
                        results.append(('ATTR', p, val))
                
                # Check tags
                for m in re.finditer(r'>([^<]+)<', content):
                    val = m.group(1).strip()
                    if not val:
                        continue
                    if val.startswith('<!--') or val.startswith('//'):
                        continue
                    if any(k in val for k in ['odoo.', 'odoo/', '@odoo/', 'import odoo']):
                        continue
                    if pat_odoo.search(val) or pat_oca.search(val) or pat_sa.search(val):
                        if val.lower() in ['odoo', '<odoo>', '</odoo>']:
                            continue
                        results.append(('TAG', p, val))
            except Exception as e:
                pass

print(f'Total matches: {len(results)}')
by_type = {}
for kind, p, val in results:
    is_report = any(k in p.lower() for k in ['report', 'invoice', 'template', 'receipt', 'order', 'slip', 'delivery'])
    cat = 'REPORT' if is_report else ('ATTR' if kind == 'ATTR' else 'VIEW_TEXT')
    by_type.setdefault(cat, []).append((p, val))

for cat in sorted(by_type.keys()):
    print(f'\n=== {cat} ({len(by_type[cat])}) ===')
    for p, val in by_type[cat]:
        print(f'  {p} -> {val[:100]!r}')
