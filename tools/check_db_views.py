#!/usr/bin/env python3
import psycopg2
import re

conn = psycopg2.connect('host=127.0.0.1 port=5434 dbname=odoo20_dev user=odoo password=1NN0R1@2026')
cur = conn.cursor()

cur.execute('SELECT id, key, name, arch_db::text FROM ir_ui_view WHERE arch_db::text ~* %s', ('odoo',))
rows = cur.fetchall()
print(f'Total ir_ui_view rows containing odoo: {len(rows)}')

protected = [
    'odoo.__session_info__', 'odoo.define', 'window.odoo', 'web.layout.odooscript',
    's_mega_menu_odoo_menu', 't-set="odoo_logo"', 'qrcode_odoo_logo', 'Odoo_logo_O.svg',
    'odoo_signed.png', 'odoo_link', 'by_odoo', 'o_odoo', 'oi_odoo', 'data-model="odoo',
    'model="odoo', 'odoo/addons', '@odoo/', 'odoo.preparation_display', 'odoo.csrf_token',
    'odoo.pos_self_order', 'odoo.loadMenusPromise', 'odoo.reloadMenus', 'application/x-odoo',
    'layout_invoices_generated_by_odoo', 'account_invoices_generated_by_odoo', 'web.odoo_ui_icons'
]

user_facing_hits = []
for id_, key, name, arch in rows:
    cleaned = arch
    for p in protected:
        cleaned = re.sub(re.escape(p), '', cleaned, flags=re.IGNORECASE)
    for m in re.finditer(r'>([^<]*\bodoo\b[^<]*)<', cleaned, re.IGNORECASE):
        user_facing_hits.append((id_, key, name, 'TEXT', m.group(1).strip()[:100]))
    for m in re.finditer(r'''(?:string|help|placeholder|title|confirm)=["']([^"']*\bodoo\b[^"']*)["']''', cleaned, re.IGNORECASE):
        user_facing_hits.append((id_, key, name, 'ATTR', m.group(1).strip()[:100]))

print(f'User facing ir_ui_view hits in DB: {len(user_facing_hits)}')
for id_, key, name, kind, val in user_facing_hits:
    print(f'[{kind}] id={id_} key={key} name={name} -> {val!r}')
