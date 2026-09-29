#!/usr/bin/env python3
"""
tools/sync_bot_avatars_db.py
Synchronizes canonical Insilos Bot Avatar into PostgreSQL database via Odoo ORM:
- res.partner records: ID 2 (OdooBot), ID 10 (Welcome Bot), ID 14 (Helpdesk Bot)
- chatbot.script records: ID 1 (Welcome Bot), ID 2 (Helpdesk Bot)
"""

import os
import sys
import base64
import logging

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger('sync_bot_avatars')

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
ODOOBOT_PNG_PATH = os.path.join(REPO_ROOT, 'addons', 'mail', 'static', 'src', 'img', 'odoobot.png')

def sync_avatars():
    if not os.path.exists(ODOOBOT_PNG_PATH):
        raise FileNotFoundError(f"Missing canonical avatar file: {ODOOBOT_PNG_PATH}")

    with open(ODOOBOT_PNG_PATH, 'rb') as f:
        image_bytes = f.read()
    image_b64 = base64.b64encode(image_bytes)

    print(f"Loaded canonical Insilos bot avatar: {len(image_bytes)} bytes")

    import odoo
    from odoo.modules.registry import Registry
    from odoo import api

    conf_name = 'insilos.conf' if os.path.exists(os.path.join(REPO_ROOT, 'insilos.conf')) else 'odoo.conf'
    odoo.tools.config.parse_config(['-c', os.path.join(REPO_ROOT, conf_name), '-d', 'odoo20_dev'])
    registry = Registry('odoo20_dev')

    with registry.cursor() as cr:
        env = api.Environment(cr, odoo.SUPERUSER_ID, {})

        # 1. Update res.partner records
        partner_ids = [2, 10, 14]
        partners = env['res.partner'].browse(partner_ids).exists()
        print(f"Updating {len(partners)} bot partner records...")
        for partner in partners:
            print(f"  -> Updating res.partner [{partner.id}] '{partner.name}'...")
            partner.write({'image_1920': image_b64})
            print(f"     ✓ Updated image_1920 for partner {partner.id}")

        # Check for any other bot partners
        other_bots = env['res.partner'].search([('name', 'ilike', 'bot'), ('id', 'not in', partner_ids)])
        for p in other_bots:
            print(f"  -> Updating additional bot partner [{p.id}] '{p.name}'...")
            p.write({'image_1920': image_b64})

        # 2. Update chatbot.script records
        if 'chatbot.script' in env:
            scripts = env['chatbot.script'].browse([1, 2]).exists()
            print(f"Updating {len(scripts)} chatbot script records...")
            for script in scripts:
                print(f"  -> Updating chatbot.script [{script.id}] '{script.title}'...")
                script.write({'image_1920': image_b64})
                print(f"     ✓ Updated image_1920 for chatbot.script {script.id}")

        cr.commit()
        print("✓ All bot avatars synchronized and committed to PostgreSQL database successfully.")

if __name__ == '__main__':
    sync_avatars()
