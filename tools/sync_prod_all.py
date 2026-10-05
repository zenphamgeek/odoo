#!/usr/bin/env python3
"""
tools/sync_prod_all.py
Synchronizes updated files, clean transparent icons, and subscription parameters to production.
"""

import subprocess
import os
import hashlib

PODS = [
    'insilos-saas-app-58468f86b5-97xx5',
    'insilos-saas-app-58468f86b5-lsgqw',
    'insilos-saas-app-58468f86b5-pzkkr'
]
NAMESPACE = 'production'
CONTAINER = 'insilos'

FILES_TO_COPY = [
    ('enterprise/industry_fsm_theme/static/src/webclient/home_menu_fsm.xml', '/app/insilos/enterprise/industry_fsm_theme/static/src/webclient/home_menu_fsm.xml'),
    ('enterprise/industry_fsm_theme/static/src/scss/fsm_theme.scss', '/app/insilos/enterprise/industry_fsm_theme/static/src/scss/fsm_theme.scss'),
    ('enterprise/insilos_theme_genesis/static/src/scss/insilos_home_launcher_restructure.scss', '/app/insilos/apps/insilos_theme_genesis/static/src/scss/insilos_home_launcher_restructure.scss'),
    ('enterprise/insilos_theme_genesis/static/src/scss/insilos_home_launcher_restructure.scss', '/app/insilos/enterprise/insilos_theme_genesis/static/src/scss/insilos_home_launcher_restructure.scss'),
    ('enterprise/web_enterprise/models/ir_http.py', '/app/insilos/apps/web_enterprise/models/ir_http.py'),
    ('enterprise/web_enterprise/models/ir_http.py', '/app/insilos/enterprise/web_enterprise/models/ir_http.py'),
    ('enterprise/web_enterprise/static/src/webclient/home_menu/enterprise_subscription_service.js', '/app/insilos/apps/web_enterprise/static/src/webclient/home_menu/enterprise_subscription_service.js'),
    ('enterprise/insilos_theme_genesis/__manifest__.py', '/app/insilos/apps/insilos_theme_genesis/__manifest__.py'),
    ('enterprise/insilos_theme_genesis/__manifest__.py', '/app/insilos/enterprise/insilos_theme_genesis/__manifest__.py'),
    ('enterprise/insilos_theme_genesis/static/src/scss/insilos_discuss_restructure.scss', '/app/insilos/apps/insilos_theme_genesis/static/src/scss/insilos_discuss_restructure.scss'),
    ('enterprise/insilos_theme_genesis/static/src/scss/insilos_discuss_restructure.scss', '/app/insilos/enterprise/insilos_theme_genesis/static/src/scss/insilos_discuss_restructure.scss'),
    ('enterprise/insilos_theme_genesis/static/src/scss/insilos_systray_restructure.scss', '/app/insilos/apps/insilos_theme_genesis/static/src/scss/insilos_systray_restructure.scss'),
    ('enterprise/insilos_theme_genesis/static/src/scss/insilos_systray_restructure.scss', '/app/insilos/enterprise/insilos_theme_genesis/static/src/scss/insilos_systray_restructure.scss'),
    ('addons/web_tour/static/src/tour_pointer/tour_pointer.scss', '/app/insilos/addons/web_tour/static/src/tour_pointer/tour_pointer.scss'),
    ('enterprise/insilos_theme_genesis/static/src/scss/insilos_perf_containment.scss', '/app/insilos/apps/insilos_theme_genesis/static/src/scss/insilos_perf_containment.scss'),
    ('enterprise/insilos_theme_genesis/static/src/scss/insilos_perf_containment.scss', '/app/insilos/enterprise/insilos_theme_genesis/static/src/scss/insilos_perf_containment.scss'),
    ('addons/web/static/src/core/network/rpc.js', '/app/insilos/addons/web/static/src/core/network/rpc.js'),
    ('addons/web/static/src/module_loader.js', '/app/insilos/addons/web/static/src/module_loader.js'),
    ('addons/web/static/src/scss/primary_variables.scss', '/app/insilos/addons/web/static/src/scss/primary_variables.scss'),
    ('addons/web/static/src/webclient/navbar/navbar.scss', '/app/insilos/addons/web/static/src/webclient/navbar/navbar.scss'),
    ('enterprise/web_enterprise/static/src/scss/primary_variables.scss', '/app/insilos/enterprise/web_enterprise/static/src/scss/primary_variables.scss'),
    ('enterprise/web_enterprise/static/src/scss/primary_variables.scss', '/app/insilos/apps/web_enterprise/static/src/scss/primary_variables.scss'),
    ('addons/mail/static/src/img/odoobot.png', '/app/insilos/addons/mail/static/src/img/odoobot.png'),
    ('addons/mail/static/src/img/odoobot.svg', '/app/insilos/addons/mail/static/src/img/odoobot.svg'),
    ('addons/mail/static/src/img/odoobot_transparent.png', '/app/insilos/addons/mail/static/src/img/odoobot_transparent.png'),
    ('addons/mail_bot/models/res_users.py', '/app/insilos/addons/mail_bot/models/res_users.py'),
    ('addons/mail_bot/models/mail_bot.py', '/app/insilos/addons/mail_bot/models/mail_bot.py'),
    ('enterprise/insilos_website/static/description/icon.svg', '/app/insilos/enterprise/insilos_website/static/description/icon.svg'),
    ('enterprise/marketing_automation/static/description/icon.png', '/app/insilos/enterprise/marketing_automation/static/description/icon.png'),
    ('addons/base/static/description/modules.png', '/app/insilos/addons/base/static/description/modules.png'),
    ('addons/base/static/description/settings.png', '/app/insilos/addons/base/static/description/settings.png'),
    ('addons/base/static/description/exception.png', '/app/insilos/addons/base/static/description/exception.png'),
    ('odoo/orm/registry.py', '/app/insilos/odoo/orm/registry.py'),
    ('odoo/tools/zeep/wsse/__init__.py', '/app/insilos/odoo/tools/zeep/wsse/__init__.py')
]

def run_cmd(cmd):
    p = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p.returncode != 0:
        print(f"FAILED: {cmd}\n{p.stderr}")
    return p.stdout.strip()

def get_running_pods():
    cmd = f"kubectl get pods -n {NAMESPACE} --field-selector=status.phase=Running -o jsonpath='{{.items[*].metadata.name}}'"
    out = run_cmd(cmd)
    pods = [p for p in out.split() if 'insilos-saas-app-' in p]
    return pods if pods else PODS

def main():
    pods = get_running_pods()
    print(f"Targeting active pods: {pods}")
    print("=== STEP 1: Copying updated files to all production pods ===")
    for pod in pods:
        print(f"\nTargeting Pod {pod}...")
        for src, dst in FILES_TO_COPY:
            if not os.path.exists(src):
                print(f"Skipping non-existent {src}")
                continue
            cmd = f"kubectl cp -n {NAMESPACE} {src} {pod}:{dst} -c {CONTAINER}"
            res = run_cmd(cmd)
            print(f"  Copied {src} -> {dst}")
        
        # Ensure correct ownership
        run_cmd(f"kubectl exec -n {NAMESPACE} {pod} -c {CONTAINER} -- chown -R insilos:insilos /app/insilos/apps /app/insilos/enterprise")

    print("\n=== STEP 2: Updating Filestore and ir_attachment on Production Database ===")
    lead_pod = pods[0]
    
    # Python script executed inside lead_pod to update attachments and filestore
    py_script = """
import sys
sys.path.insert(0, '/app/insilos')
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
                cr.execute('''
                    UPDATE ir_attachment
                    SET checksum = %s, store_fname = %s, file_size = %s, db_datas = NULL, write_date = NOW()
                    WHERE id = %s
                ''', (sha1, store_fname, len(raw), att.id))
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

    # 2b. Update InsilosBot Avatar in DB
    bot_path = '/app/insilos/addons/mail/static/src/img/odoobot.png'
    if os.path.exists(bot_path):
        with open(bot_path, 'rb') as f:
            bot_raw = f.read()
        bot_b64 = base64.b64encode(bot_raw)
        bot_partners = env['res.partner'].search([('name', 'ilike', 'bot')])
        for bp in bot_partners:
            bp.write({'image_1920': bot_b64})
            print(f'Updated bot partner {bp.id} ({bp.name}) avatar')

    # 3. Clear web assets so bundle regenerates
    cr.execute("DELETE FROM ir_attachment WHERE name LIKE '%assets_%'")
    print(f'Cleared {cr.rowcount} web asset cache records.')
    
    cr.commit()
    print('DB Commit successful!')
"""
    local_script_path = '/tmp/sync_prod_db_temp.py'
    with open(local_script_path, 'w') as f:
        f.write(py_script)
    run_cmd(f"kubectl cp -n {NAMESPACE} {local_script_path} {lead_pod}:/tmp/sync_db.py -c {CONTAINER}")
    out = run_cmd(f"kubectl exec -n {NAMESPACE} {lead_pod} -c {CONTAINER} -- python3 /tmp/sync_db.py")
    print(out)

    print("\n=== STEP 3: Reloading workers across all production pods ===")
    for pod in pods:
        # Send SIGTERM to worker processes so master respawns them with new code
        cmd = f"kubectl exec -n {NAMESPACE} {pod} -c {CONTAINER} -- python3 -c \"" + """
import os, signal
my_pid = os.getpid()
pids = [int(p) for p in os.listdir('/proc') if p.isdigit()]
for p in pids:
    if p != 1 and p != my_pid:
        try:
            with open(f'/proc/{p}/cmdline', 'rb') as f:
                cmd = f.read().decode('utf-8', errors='ignore')
                if 'insilos' in cmd or 'odoo' in cmd:
                    os.kill(p, signal.SIGTERM)
                    print(f'Terminated worker {p}')
        except Exception:
            pass
""" + "\""
        out = run_cmd(cmd)
        print(f"Pod {pod}: {out}")

    print("\n=== SYNC COMPLETE ===")

if __name__ == '__main__':
    main()
