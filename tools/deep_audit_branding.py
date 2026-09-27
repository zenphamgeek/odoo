#!/usr/bin/env python3
import os
import re

PAT_ODOO = re.compile(r'\bodoo(?:\s+s\.?a\.?)?\b', re.IGNORECASE)
PAT_OCA = re.compile(r'\b(?:OCA|Odoo\s+Community\s+Association)\b', re.IGNORECASE)

xml_tag_text = re.compile(r'>([^<]+)<')
xml_attrs = re.compile(r'(?:string|help|title|placeholder|aria-label|alt|label)=["\']([^"\']+)["\']', re.IGNORECASE)

# Technical allowlist for XML tokens that are technical contracts
XML_TECHNICAL_ALLOWLIST = [
    'odoo/addons',
    '@odoo/',
    'odoo.define',
    'odoo.__session_info__',
    'odoo.csrf_token',
    'window.odoo',
    'data-model="odoo',
    'model="odoo',
    'http://www.odoo.com',
    'https://www.odoo.com',
]

def scan():
    hits = []
    for base in ['addons', 'enterprise', 'odoo/addons']:
        for root, dirs, files in os.walk(base):
            if any(x in root for x in ['.git', 'node_modules', '__pycache__']):
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
                                
                                # check tag content
                                for m in xml_tag_text.finditer(line):
                                    text = m.group(1).strip()
                                    if not text:
                                        continue
                                    if PAT_ODOO.search(text) or PAT_OCA.search(text):
                                        # check if it's purely technical
                                        if any(k in text for k in ['import ', 'odoo.', 'odoo/']):
                                            continue
                                        hits.append(('XML_TEXT', p, lno, text, sline))
                                
                                # check attributes
                                for m in xml_attrs.finditer(line):
                                    text = m.group(1).strip()
                                    if PAT_ODOO.search(text) or PAT_OCA.search(text):
                                        hits.append(('XML_ATTR', p, lno, text, sline))
                    except Exception:
                        pass

    print(f"Total XML candidates found: {len(hits)}")
    return hits

if __name__ == '__main__':
    hits = scan()
    # Group by file
    by_file = {}
    for kind, p, lno, text, sline in hits:
        by_file.setdefault(p, []).append((kind, lno, text, sline))
    
    print(f"Total files with hits: {len(by_file)}")
    for p, items in sorted(by_file.items()):
        print(f"\nFile: {p} ({len(items)} hits)")
        for kind, lno, text, sline in items[:5]:
            print(f"  [{kind}] Line {lno}: {text[:80]}")
        if len(items) > 5:
            print(f"  ... and {len(items)-5} more lines")
