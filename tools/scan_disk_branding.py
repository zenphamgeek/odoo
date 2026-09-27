#!/usr/bin/env python3
import os
import re

xml_patterns = [
    re.compile(r'>[^<]*\b[oO]doo\b[^<]*<'),
    re.compile(r'string=["\'][^"\']*\b[oO]doo\b[^"\']*["\']', re.IGNORECASE),
    re.compile(r'placeholder=["\'][^"\']*\b[oO]doo\b[^"\']*["\']', re.IGNORECASE),
    re.compile(r'title=["\'][^"\']*\b[oO]doo\b[^"\']*["\']', re.IGNORECASE),
    re.compile(r'alt=["\'][^"\']*\b[oO]doo\b[^"\']*["\']', re.IGNORECASE),
    re.compile(r'https?://(?:www\.)?odoo\.com(?:/[^\s"\'<>]*)?', re.IGNORECASE),
]

js_patterns = [
    re.compile(r'title\s*:\s*["\'][^"\']*\b[oO]doo\b[^"\']*["\']', re.IGNORECASE),
    re.compile(r'name\s*:\s*["\'][^"\']*\b[oO]doo\b[^"\']*["\']', re.IGNORECASE),
    re.compile(r'placeholder\s*:\s*["\'][^"\']*\b[oO]doo\b[^"\']*["\']', re.IGNORECASE),
    re.compile(r'text\s*:\s*["\'][^"\']*\b[oO]doo\b[^"\']*["\']', re.IGNORECASE),
    re.compile(r'_t\(["\'][^"\']*\b[oO]doo\b[^"\']*["\']\)', re.IGNORECASE),
]

py_patterns = [
    re.compile(r'_\(["\'][^"\']*\b[oO]doo\b[^"\']*["\']\)', re.IGNORECASE),
    re.compile(r'_lt\(["\'][^"\']*\b[oO]doo\b[^"\']*["\']\)', re.IGNORECASE),
    re.compile(r'string=["\'][^"\']*\b[oO]doo\b[^"\']*["\']', re.IGNORECASE),
    re.compile(r'help=["\'][^"\']*\b[oO]doo\b[^"\']*["\']', re.IGNORECASE),
]

skip_keywords = [
    'odoo.__session_info__',
    'odoo.define',
    'window.odoo',
    'odoo.preparation_display',
    'xmlns',
    'package',
    'odoo.csrf_token',
    'odoo.pos_self_order',
    'odoo.loadMenusPromise',
    'odoo.reloadMenus',
    'data-model="odoo',
    'type="xml"',
    'model="odoo',
    'odoo/addons',
    '@odoo/',
    'import odoo',
    'from odoo',
]

found = []
for base in ['addons', 'enterprise']:
    for root, dirs, files in os.walk(base):
        if any(x in root for x in ['.git', 'node_modules', '__pycache__', 'tests', 'test', 'l10n_']):
            continue
        for f in files:
            p = os.path.join(root, f)
            if f.endswith('.xml'):
                try:
                    with open(p, 'r', encoding='utf-8', errors='ignore') as fp:
                        for lno, line in enumerate(fp, 1):
                            sline = line.strip()
                            if sline.startswith('<!--') or sline.startswith('*') or sline.startswith('//'):
                                continue
                            if any(k in sline for k in skip_keywords):
                                continue
                            for pat in xml_patterns:
                                m = pat.findall(line)
                                if m:
                                    filtered = [x for x in m if not any(k in x for k in skip_keywords)]
                                    if filtered:
                                        found.append((p, lno, filtered, sline))
                                        break
                except Exception:
                    pass
            elif f.endswith('.js'):
                try:
                    with open(p, 'r', encoding='utf-8', errors='ignore') as fp:
                        for lno, line in enumerate(fp, 1):
                            sline = line.strip()
                            if sline.startswith('//') or sline.startswith('*'):
                                continue
                            if any(k in sline for k in skip_keywords):
                                continue
                            for pat in js_patterns:
                                m = pat.findall(line)
                                if m:
                                    found.append((p, lno, m, sline))
                                    break
                except Exception:
                    pass
            elif f.endswith('.py'):
                try:
                    with open(p, 'r', encoding='utf-8', errors='ignore') as fp:
                        for lno, line in enumerate(fp, 1):
                            sline = line.strip()
                            if sline.startswith('#'):
                                continue
                            if any(k in sline for k in skip_keywords):
                                continue
                            for pat in py_patterns:
                                m = pat.findall(line)
                                if m:
                                    found.append((p, lno, m, sline))
                                    break
                except Exception:
                    pass

print(f"Total disk matches found: {len(found)}")
# Group by file
by_file = {}
for p, lno, m, sline in found:
    by_file.setdefault(p, []).append((lno, m, sline))

for p, items in sorted(by_file.items()):
    print(f"\nFile: {p} ({len(items)} hits)")
    for lno, m, sline in items[:5]:
        print(f"  Line {lno}: {sline[:120]}")
    if len(items) > 5:
        print(f"  ... and {len(items)-5} more lines")
