import odoo
from odoo.modules.registry import Registry
from odoo import api, SUPERUSER_ID
import os, hashlib, base64

odoo.tools.config.parse_config(['-c', '/etc/insilos.conf', '--db_host', 'pgbouncer-service', '--db_port', '6432', '--db_user', 'insilos', '-d', 'insilos'])
registry = Registry('insilos')

ICON_UPDATES = [
    ('Insilos Website', '/app/insilos/enterprise/insilos_website/static/description/icon.svg', 'insilos_website,static/description/icon.svg'),
    ('Marketing Automation', '/app/insilos/enterprise/marketing_automation/static/description/icon.png', 'marketing_automation,static/description/icon.png'),
    ('Apps', '/app/insilos/addons/base/static/description/modules.png', 'base,static/description/modules.png'),
    ('Settings', '/app/insilos/addons/base/static/description/settings.png', 'base,static/description/settings.png'),
    ('Tests', '/app/insilos/addons/base/static/description/exception.png', 'base,static/description/exception.png'),
]

filestore_dir = '/var/lib/insilos/filestore/filestore/insilos'

with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # 1. Update subscription parameters
    ICP = env['ir.config_parameter'].sudo()
    ICP.set_param('database.expiration_date', '2035-12-31 23:59:59')
    ICP.set_param('database.expiration_reason', 'registered')
    ICP.set_param('database.enterprise_code', 'INSILOS-ENT-2026-SOVEREIGN')
    
    # 2. Update Icons
    for menu_name, file_path, web_icon in ICON_UPDATES:
        if not os.path.exists(file_path):
            print(f'File missing: {file_path}')
            continue
        with open(file_path, 'rb') as f:
            raw = f.read()
        sha1 = hashlib.sha1(raw).hexdigest()
        store_fname = f'{sha1[:2]}/{sha1}'
        full_dest_dir = os.path.join(filestore_dir, sha1[:2])
        full_dest_path = os.path.join(filestore_dir, store_fname)
        os.makedirs(full_dest_dir, exist_ok=True)
        with open(full_dest_path, 'wb') as f:
            f.write(raw)
        os.chmod(full_dest_path, 0o644)
        
        # Find menu
        menus = env['ir.ui.menu'].search([('parent_id', '=', False), ('name', '=', menu_name)])
        if not menus:
            menus = env['ir.ui.menu'].search([('parent_id', '=', False), ('web_icon', '=', web_icon)])
        for m in menus:
            b64_data = base64.b64encode(raw)
            # Find or create attachment
            att = env['ir.attachment'].search([('res_model', '=', 'ir.ui.menu'), ('res_field', '=', 'web_icon_data'), ('res_id', '=', m.id)], limit=1)
            if att:
                cr.execute("""
                    UPDATE ir_attachment
                    SET checksum = %s, store_fname = %s, file_size = %s, db_datas = NULL, write_date = NOW()
                    WHERE id = %s
                """, (sha1, store_fname, len(raw), att.id))
            else:
                att = env['ir.attachment'].create({
                    'name': f'menu_{m.id}_icon',
                    'res_model': 'ir.ui.menu',
                    'res_field': 'web_icon_data',
                    'res_id': m.id,
                    'type': 'binary',
                    'datas': b64_data,
                })
            m.write({'web_icon_data': b64_data})
            print(f'Updated {m.name} -> sha1: {sha1}, store: {store_fname}')

    # 3. Clear web assets so bundle regenerates
    cr.execute("DELETE FROM ir_attachment WHERE name LIKE '%assets_%'")
    print(f'Cleared {cr.rowcount} web asset cache records.')
    
    cr.commit()
    print('DB Commit successful!')
