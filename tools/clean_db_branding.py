#!/usr/bin/env python3
"""
tools/clean_db_branding.py
Synchronizes and cleans PostgreSQL database branding records in odoo20_dev.
Complies with doc/HARD_REFACTOR_PART_A_BRANDING_ASSETS_TAXONOMY.md.
"""

import json
import re
import psycopg2

def clean_database():
    print("[DB CLEAN] Connecting to odoo20_dev database...")
    conn = psycopg2.connect("host=127.0.0.1 port=5434 dbname=odoo20_dev user=odoo password=1NN0R1@2026")
    cur = conn.cursor()

    # 1. knowledge_article id 31 (Company Newsletter)
    print("  -> Cleaning knowledge_article id 31...")
    cur.execute("""
        UPDATE knowledge_article 
        SET template_body = jsonb_set(template_body, '{en_US}', 
            to_jsonb(replace(template_body->>'en_US', 'Odooers', 'teammates')))
        WHERE id = 31 AND template_body->>'en_US' LIKE '%Odooers%';
    """)
    print(f"     Updated {cur.rowcount} row(s)")

    # 2. ir_model_constraint id 492
    print("  -> Cleaning ir_model_constraint...")
    cur.execute("""
        UPDATE ir_model_constraint
        SET message = jsonb_set(message, '{en_US}',
            to_jsonb(replace(message->>'en_US', 'Odoo', 'Insilos')))
        WHERE message->>'en_US' LIKE '%notifications in Odoo%';
    """)
    print(f"     Updated {cur.rowcount} row(s)")

    # 3. ir_model name & explanation
    print("  -> Cleaning ir_model name & explanation...")
    cur.execute("""
        UPDATE ir_model
        SET name = jsonb_set(name, '{en_US}',
            to_jsonb(replace(name->>'en_US', 'Odoo AI', 'Insilos AI')))
        WHERE id = 8579 AND name->>'en_US' LIKE '%Odoo AI%';
    """)
    print(f"     Updated {cur.rowcount} row(s) in ir_model.name")

    cur.execute("""
        UPDATE ir_model
        SET explanation = replace(replace(replace(explanation, 'Odoo uses this', 'Insilos uses this'), 'Odoo database', 'Insilos database'), 'Odoo supports', 'Insilos supports')
        WHERE explanation LIKE '%Odoo%';
    """)
    print(f"     Updated {cur.rowcount} row(s) in ir_model.explanation")

    # 4. ir_model_fields field_description
    print("  -> Cleaning ir_model_fields field_description...")
    field_desc_updates = [
        (40936, "Delete synced events from Insilos"),
        (41351, "Delete synced events from Insilos"),
        (42973, "Insilos API User"),
        (42974, "Insilos API Key"),
        (805, "Insilos Enterprise Module"),
        (23799, "Link your stripe issuing account to manage company credit cards for your employees through Insilos"),
        (3376, "InsilosBot Status"),
        (3377, "InsilosBot Failed"),
        (7229, "Insilos Enterprise Module"),
    ]
    for fid, desc in field_desc_updates:
        cur.execute("""
            UPDATE ir_model_fields
            SET field_description = jsonb_set(COALESCE(field_description, '{}'::jsonb), '{en_US}', to_jsonb(%s::text))
            WHERE id = %s;
        """, (desc, fid))
    print(f"     Updated {len(field_desc_updates)} field descriptions")

    # 5. ir_model_fields help tooltips
    print("  -> Cleaning ir_model_fields user-facing help tooltips...")
    cur.execute("""
        SELECT id, help->>'en_US' 
        FROM ir_model_fields 
        WHERE help IS NOT NULL AND help->>'en_US' ~* '\\y(odoo|odoobot)\\y';
    """)
    help_rows = cur.fetchall()
    print(f"     Found {len(help_rows)} help tooltips to clean")
    cleaned_help_count = 0
    for fid, htext in help_rows:
        new_text = re.sub(r'\bOdooBot\b', 'InsilosBot', htext)
        new_text = re.sub(r'\bodoobot\b', 'insilosbot', new_text)
        new_text = re.sub(r'\bOdoo\b', 'Insilos', new_text)
        new_text = re.sub(r'example\.odoo\.com', 'example.insilos.com', new_text)
        new_text = re.sub(r'odoo@example\.com', 'insilos@example.com', new_text)
        new_text = re.sub(r'@odoo\.official', '@insilos.official', new_text)
        new_text = re.sub(r'notification@odoo\.com', 'notification@insilos.com', new_text)
        new_text = re.sub(r'\bodoo\.com/pricing\b', 'insilos.com/pricing', new_text)
        new_text = re.sub(r'\bodoo\.com\b', 'insilos.com', new_text)
        if new_text != htext:
            cur.execute("""
                UPDATE ir_model_fields
                SET help = jsonb_set(help, '{en_US}', to_jsonb(%s::text))
                WHERE id = %s;
            """, (new_text, fid))
            cleaned_help_count += 1
    print(f"     Updated {cleaned_help_count} help tooltips")

    # 6. ir_asset name
    print("  -> Cleaning ir_asset...")
    cur.execute("""
        UPDATE ir_asset 
        SET name = 'Insilos Menu 000 SCSS'
        WHERE id = 87 AND name = 'Odoo Menu 000 SCSS';
    """)
    print(f"     Updated {cur.rowcount} row(s)")

    # 7. ir_ui_view arch_db view 3947 & view 3678
    print("  -> Cleaning ir_ui_view views 3947 & 3678...")
    cur.execute("""
        UPDATE ir_ui_view
        SET arch_db = jsonb_set(arch_db, '{en_US}',
            to_jsonb(replace(arch_db->>'en_US', 'FOR WEBSITES BUILT WITH ODOO', 'FOR WEBSITES BUILT WITH INSILOS')))
        WHERE id = 3947 AND arch_db->>'en_US' LIKE '%FOR WEBSITES BUILT WITH ODOO%';
    """)
    cur.execute("""
        UPDATE ir_ui_view
        SET arch_db = jsonb_set(arch_db, '{en_US}',
            to_jsonb(replace(arch_db->>'en_US', 'Odoo India pvt. Ltd', 'Insilos Technologies Ltd')))
        WHERE id = 3678 AND arch_db->>'en_US' LIKE '%Odoo India pvt. Ltd%';
    """)
    print("     Updated specific view rows")

    # 8. Clean ir_ui_view legacy colors across all views
    print("  -> Cleaning ir_ui_view legacy colors in arch_db...")
    cur.execute("""
        SELECT id, arch_db->>'en_US' FROM ir_ui_view
        WHERE arch_db IS NOT NULL AND arch_db->>'en_US' ~* '#875a7b|#714b67';
    """)
    view_rows = cur.fetchall()
    for vid, varch in view_rows:
        new_arch = re.sub(r'#875A7B', '#004455', varch, flags=re.IGNORECASE)
        new_arch = re.sub(r'#714B67', '#004455', new_arch, flags=re.IGNORECASE)
        if new_arch != varch:
            cur.execute("""
                UPDATE ir_ui_view
                SET arch_db = jsonb_set(arch_db, '{en_US}', to_jsonb(%s::text))
                WHERE id = %s;
            """, (new_arch, vid))
    cur.execute("""
        UPDATE ir_ui_view
        SET arch_prev = replace(replace(arch_prev, '#875A7B', '#004455'), '#714B67', '#004455')
        WHERE arch_prev ~* '#875a7b|#714b67';
    """)
    print(f"     Updated {len(view_rows)} view arch_db records and cleaned arch_prev")

    # 9. Clean mail_template body_html legacy colors and URLs
    print("  -> Cleaning mail_template body_html legacy colors & URLs...")
    cur.execute(r"""
        SELECT id, body_html->>'en_US' FROM mail_template
        WHERE body_html IS NOT NULL AND (body_html->>'en_US' ~* '#875a7b|#714b67|linear-gradient\(140deg,#714B67|/odoo/accounting/');
    """)
    template_rows = cur.fetchall()
    for tid, tbody in template_rows:
        new_body = re.sub(r'#875A7B', '#004455', tbody, flags=re.IGNORECASE)
        new_body = re.sub(r'#714B67', '#004455', new_body, flags=re.IGNORECASE)
        new_body = new_body.replace(
            'linear-gradient(140deg,#714B67 0%,#8a6381 55%,#bfa8c2 100%)',
            'linear-gradient(140deg,#004455 0%,#00657f 55%,#0096B3 100%)'
        )
        new_body = new_body.replace(
            'linear-gradient(135deg,#714B67 0%,#9b77a3 100%)',
            'linear-gradient(135deg,#004455 0%,#0096B3 100%)'
        )
        new_body = new_body.replace('/odoo/accounting/', '/insilos/accounting/')
        if new_body != tbody:
            cur.execute("""
                UPDATE mail_template
                SET body_html = jsonb_set(body_html, '{en_US}', to_jsonb(%s::text))
                WHERE id = %s;
            """, (new_body, tid))
    print(f"     Updated {len(template_rows)} mail_template body_html records")

    # 10. Clean digest_tip colors
    print("  -> Cleaning digest_tip legacy colors...")
    cur.execute("""
        SELECT id, tip_description->>'en_US' FROM digest_tip
        WHERE tip_description IS NOT NULL AND tip_description->>'en_US' ~* '#875a7b|#714b67';
    """)
    tip_rows = cur.fetchall()
    for tid, tdesc in tip_rows:
        new_desc = re.sub(r'#875A7B', '#004455', tdesc, flags=re.IGNORECASE)
        new_desc = re.sub(r'#714B67', '#004455', new_desc, flags=re.IGNORECASE)
        if new_desc != tdesc:
            cur.execute("""
                UPDATE digest_tip
                SET tip_description = jsonb_set(tip_description, '{en_US}', to_jsonb(%s::text))
                WHERE id = %s;
            """, (new_desc, tid))
    print(f"     Updated {len(tip_rows)} digest_tip records")

    # 11. Clean im_livechat_channel
    print("  -> Cleaning im_livechat_channel colors...")
    cur.execute("""
        UPDATE im_livechat_channel
        SET button_background_color = '#004455'
        WHERE button_background_color ~* '#875a7b|#714b67';
    """)
    cur.execute("""
        UPDATE im_livechat_channel
        SET header_background_color = '#004455'
        WHERE header_background_color ~* '#875a7b|#714b67';
    """)
    print("     Updated im_livechat_channel colors")

    # 12. Clean mail_mail sent/draft records
    print("  -> Cleaning mail_mail body_html...")
    cur.execute("""
        UPDATE mail_mail
        SET body_html = replace(replace(body_html, '#875A7B', '#004455'), '#714B67', '#004455')
        WHERE body_html ~* '#875a7b|#714b67';
    """)
    print(f"     Updated {cur.rowcount} mail_mail row(s)")

    # 13. Specific mail_template email addresses
    print("  -> Cleaning specific mail_template emails...")
    cur.execute("""
        UPDATE mail_template
        SET email_from = 'iap@insilos.com', email_to = 'iap@insilos.com'
        WHERE id = 94;
    """)
    cur.execute("""
        UPDATE mail_template
        SET email_from = 'noreply@insilos.com'
        WHERE id = 30;
    """)
    print("     Updated mail_template records 94 and 30")

    # 14. ir_module_module shortdesc, summary, author, and website
    print("  -> Cleaning ir_module_module shortdesc, summary, author & website...")
    module_shortdescs = {
        'mail_bot': 'InsilosBot',
        'mail_bot_hr': 'InsilosBot - HR',
        'test_populate': 'Insilos Populate Tests',
        'l10n_mx_edi_landing': 'Mexico Localization for Stock/Landing',
        'l10n_mx_reports': 'Mexican Localization Reports',
        'l10n_mx_xml_polizas': 'Mexican XML Polizas Export',
    }
    for mname, sdesc in module_shortdescs.items():
        cur.execute("""
            UPDATE ir_module_module
            SET shortdesc = jsonb_set(COALESCE(shortdesc, '{}'::jsonb), '{en_US}', to_jsonb(%s::text))
            WHERE name = %s;
        """, (sdesc, mname))

    module_summaries = {
        'mail_bot': 'Add InsilosBot in discussions',
        'web_studio': 'Create and customize your Insilos apps',
        'web_mobile': 'Insilos Mobile Core module',
        'pos_mobile': 'Insilos Mobile Point of Sale module',
        'web_map': 'Defines the map view for Insilos enterprise',
        'web_cohort': 'Basic Cohort view for Insilos',
        'web_grid': 'Basic 2D Grid view for Insilos',
        'website_helpdesk_forum': 'Help Center for helpdesk based on Insilos Forum',
        'whatsapp_sign': 'This module enables users to send signature requests via WhatsApp in Insilos Sign',
        'databases': 'Manage a fleet of Insilos databases',
        'populate': 'Generate synthetic data for an Insilos database',
        'test_populate': "Test module for Insilos's Populate",
    }
    for mname, summ in module_summaries.items():
        cur.execute("""
            UPDATE ir_module_module
            SET summary = jsonb_set(COALESCE(summary, '{}'::jsonb), '{en_US}', to_jsonb(%s::text))
            WHERE name = %s;
        """, (summ, mname))

    cur.execute("""
        UPDATE ir_module_module
        SET summary = jsonb_set(summary, '{en_US}',
            to_jsonb(replace(summary->>'en_US', 'Odoo environment', 'Insilos environment')))
        WHERE name = 'ai_app' AND summary->>'en_US' LIKE '%Odoo%';
    """)
    cur.execute("""
        UPDATE ir_module_module
        SET summary = jsonb_set(summary, '{en_US}',
            to_jsonb(replace(summary->>'en_US', 'within Odoo', 'within Insilos')))
        WHERE name = 'voip' AND summary->>'en_US' LIKE '%Odoo%';
    """)

    # Author updates
    cur.execute("""
        UPDATE ir_module_module
        SET author = 'Insilos'
        WHERE author IN ('Odoo S.A.', 'Odoo SA', 'Odoo', 'Odoo S.A', 'Odoo Sa', 'Odoo PS');
    """)
    print(f"     Updated {cur.rowcount} direct Odoo author module(s)")

    cur.execute("""
        UPDATE ir_module_module
        SET author = replace(replace(replace(author, 'Odoo S.A.', 'Insilos'), 'Odoo SA', 'Insilos'), 'Odoo', 'Insilos')
        WHERE author ~* 'odoo';
    """)
    print(f"     Updated {cur.rowcount} composite Odoo author module(s)")

    # Website updates
    cur.execute(r"""
        UPDATE ir_module_module
        SET website = replace(replace(website, 'www.odoo.com', 'www.insilos.com'), 'odoo.com', 'insilos.com')
        WHERE website ~* 'odoo\.com';
    """)
    print(f"     Updated {cur.rowcount} module website(s)")

    cur.execute("""
        UPDATE ir_module_module
        SET website = 'https://insilos.com/app/mobile'
        WHERE website LIKE '%play.google.com/store/apps/details?id=com.odoo.mobile%';
    """)

    conn.commit()
    conn.close()
    print("[PASS] Database branding cleaning completed successfully.")

if __name__ == '__main__':
    clean_database()
