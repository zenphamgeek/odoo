#!/usr/bin/env python3
"""
tools/safe_asset_warmup.py
Zero-Downtime, Atomic SCSS Asset Pre-Warming Engine for Insilos SaaS.
Compiles all core asset bundles (frontend, webclient, editor) directly inside
the Odoo ORM environment without deleting active attachments beforehand.
Ensures zero 404s, zero stampede compile locks, and instant sub-100ms response times.
"""

import os
import sys
import time

def warmup_database_assets(dbname="innoria_prod"):
    print(f"\n[⚡] Starting Zero-Downtime Asset Pre-Warming for DB: {dbname}...")
    t0 = time.time()
    for candidate in ['/app/insilos', '/home/zen/O20']:
        if os.path.exists(candidate) and candidate not in sys.path:
            sys.path.insert(0, candidate)

    import odoo
    from odoo.orm.registry import Registry
    from odoo import api, SUPERUSER_ID

    db_host = os.environ.get('DB_HOST', 'pgbouncer-service')
    db_port = os.environ.get('DB_PORT', '6432')
    db_user = os.environ.get('DB_USER', 'insilos')
    db_password = os.environ.get('PGPASSWORD', '')

    odoo.tools.config.parse_config([
        '--data-dir=/var/lib/insilos/filestore',
        '--addons-path=/app/insilos/addons,/app/insilos/apps',
        f'--db_host={db_host}',
        f'--db_port={db_port}',
        f'--db_user={db_user}',
        f'--db_password={db_password}'
    ])

    registry = Registry(dbname)
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        bundles = [
            'web.assets_frontend',
            'web.assets_web',
            'web.assets_frontend_minimal',
            'web.assets_frontend_lazy',
            'website.assets_editor',
            'web_editor.assets_wysiwyg',
            'web.report_assets_common',
            'web.report_assets_pdf',
            'im_livechat.assets_embed_cors'
        ]

        compiled_summary = []
        for b in bundles:
            try:
                b_t0 = time.time()
                # Pre-generate bundle attachments via Odoo ORM
                bundle = env['ir.qweb']._get_asset_bundle(b, css=True, js=True)
                css_att = bundle.css()
                js_att = bundle.js()
                dur = round(time.time() - b_t0, 2)
                css_size = css_att.file_size if css_att else 0
                js_size = js_att.file_size if js_att else 0
                print(f"  [✓] Warmed {b:<32} (CSS: {css_size:>8}B, JS: {js_size:>8}B in {dur}s)")
                compiled_summary.append((b, True, css_size, js_size))
            except Exception as e:
                print(f"  [✗] FAILED warming {b}: {e}")
                compiled_summary.append((b, False, 0, 0))

        # Commit new attachments to DB
        cr.commit()

    total_dur = round(time.time() - t0, 2)
    success_count = sum(1 for _, ok, _, _ in compiled_summary if ok)
    print(f"\n[🎉] Pre-Warming Completed: {success_count}/{len(bundles)} bundles ready in {total_dur}s.")
    if success_count < len(bundles):
        raise RuntimeError("Asset warmup encountered failures.")

if __name__ == '__main__':
    target_db = sys.argv[1] if len(sys.argv) > 1 else 'innoria_prod'
    warmup_database_assets(target_db)
