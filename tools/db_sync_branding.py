#!/usr/bin/env python3
import psycopg2
import json
import re

def clean_text(text):
    if not text:
        return text
    res = text

    # Strip/replace external CDN pings and video embeds
    res = res.replace("https://download.odoocdn.com/digests/", "/")
    res = re.sub(r'https?://(?:[a-zA-Z0-9.-]+\.)?odoocdn\.com[^\s"\'<>]*', '', res)

    # Clean documentation and service links
    doc_urls = [
        ("https://www.odoo.com/documentation/latest/developer/reference/external_api.html#api-key", "https://insilos.com/documentation/latest/developer/reference/external_api.html#api-key"),
        ("https://www.odoo.com/documentation/latest/applications/general/auth/2fa.html", "https://insilos.com/documentation/latest/applications/general/auth/2fa.html"),
        ("https://www.odoo.com/documentation/latest/applications/sales/crm/track_leads/lead_scoring.html#predictive-lead-scoring", "https://insilos.com/documentation/latest/applications/sales/crm/track_leads/lead_scoring.html#predictive-lead-scoring"),
        ("https://www.odoo.com/documentation/latest/applications/websites/website/reporting/link_tracker.html", "https://insilos.com/documentation/latest/applications/websites/website/reporting/link_tracker.html"),
        ("https://www.odoo.com/documentation/latest/applications/hr/attendances/hardware.html", "https://insilos.com/documentation/latest/applications/hr/attendances/hardware.html"),
        ("https://www.odoo.com/survey/start/f13956e4-0104-48a0-967e-e5b6ffedd45d", "https://insilos.com/help"),
        ("https://www.odoo.com/openerp_enterprise/static/img/mail/odoo_logo_white.png", "https://insilos.com/logo.png"),
        ("https://www.odoo.com/web/image/38874595-16ef5349/odoo-mobile.png", "/web/static/img/insilos_logo.svg"),
        ("https://play.google.com/store/apps/details?id=com.odoo.mobile", "https://insilos.com/mobile"),
        ("https://itunes.apple.com/us/app/odoo/id1272543640", "https://insilos.com/mobile"),
        ("https://www.odoo.com/app/documents", "https://insilos.com"),
        ("https://www.odoo.com/app/sales", "https://insilos.com"),
        ("https://www.odoo.com/app/invoicing", "https://insilos.com"),
        ("https://www.odoo.com/documentation/", "https://insilos.com/documentation/"),
        ("https://www.odoo.com/documentation", "https://insilos.com/documentation"),
        ("https://www.odoo.com/contactus", "https://insilos.com/contactus"),
        ("https://www.odoo.com/trial", "https://insilos.com/trial"),
        ("https://www.odoo.com/help/", "https://insilos.com/help"),
        ("https://www.odoo.com/help", "https://insilos.com/help"),
        ("https://www.odoo.com?utm_source=db&amp;utm_medium=mail", "https://insilos.com"),
        ("https://www.odoo.com?utm_source=db&utm_medium=mail", "https://insilos.com"),
        ("https://www.odoo.com?utm_source=db&amp;utm_medium=auth", "https://insilos.com"),
        ("https://www.odoo.com?utm_source=db&utm_medium=auth", "https://insilos.com"),
        ("https://apps.odoo.com/apps/modules", "https://insilos.com/apps"),
        ("https://apps.odoo.com/apps/themes", "https://insilos.com/themes"),
        ("https://www.odoo.com", "https://insilos.com"),
        ("https://odoo.com", "https://insilos.com"),
        ("http://www.odoo.com", "https://insilos.com"),
        ("http://odoo.com", "https://insilos.com"),
        ("https://twitter.com/Odoo", "https://insilos.com"),
        ("https://www.youtube.com/channel/UCkQPikELWZFLgQNHd73jkdg", "https://insilos.com"),
        ("https://www.facebook.com/odoo", "https://insilos.com"),
    ]
    for old, new in doc_urls:
        res = res.replace(old, new)

    # Clean URL routes
    res = re.sub(r'/odoo/action-', '/insilos/action-', res)
    res = re.sub(r'/odoo/(\d+)/action-', r'/insilos/\1/action-', res)
    res = re.sub(r'/odoo/sdd-mandates/', '/insilos/sdd-mandates/', res)
    res = res.replace("url = '/odoo'", "url = '/insilos'")

    # Specific names & bot branding
    res = res.replace("OdooBot", "InsilosBot")
    res = res.replace("odoobot@example.com", "insilosbot@example.com")
    res = res.replace("Odoo S.A.", "Insilos")
    res = res.replace("The Odoo Team", "The Insilos Team")
    res = res.replace("Odoo support", "Insilos support")
    res = res.replace("Odoo Support", "Insilos Support")
    res = res.replace("Odoo website", "Insilos website")
    res = res.replace("Odoo Website", "Insilos Website")
    res = res.replace("Odoo POS", "Insilos POS")
    res = res.replace("alt=\"Odoo Logo\"", "alt=\"Insilos Logo\"")
    res = res.replace("alt=\"Odoo\"", "alt=\"Insilos\"")
    res = res.replace("src=\"/web/static/img/odoo_logo.svg\"", "src=\"/web/static/img/insilos_logo.svg\"")

    # Word boundary regex replacements for remaining user-facing text
    res = re.sub(r'\bOdoo\b', 'Insilos', res)
    res = re.sub(r'\bODOO\b', 'INSILOS', res)
    res = re.sub(r'\bodoo\b', 'insilos', res)
    return res

def clean_knowledge_article(html):
    if not html:
        return html
    res = clean_text(html)
    # Remove youtube video embeds
    res = re.sub(
        r'<div\s+data-embedded-props=[\'"].*?uEdaZRqa1FQ.*?data-embedded="video"\s*(?:/>|>\s*</div>)',
        '',
        res,
        flags=re.DOTALL
    )
    res = re.sub(
        r'<p[^>]*>\s*<span[^>]*>Not sure how to do it\? Check the video below.*?</span>\s*</p>',
        '',
        res,
        flags=re.DOTALL
    )
    res = re.sub(
        r'<span[^>]*>Not sure how to do it\? Check the video below.*?</span>',
        '',
        res,
        flags=re.DOTALL
    )
    return res

def clean_dict_values(d, is_knowledge=False):
    if not isinstance(d, dict):
        return d
    out = {}
    for k, v in d.items():
        if isinstance(v, str):
            out[k] = clean_knowledge_article(v) if is_knowledge else clean_text(v)
        elif isinstance(v, dict):
            out[k] = clean_dict_values(v, is_knowledge=is_knowledge)
        else:
            out[k] = v
    return out

def main():
    conn = psycopg2.connect(host='127.0.0.1', port=5434, dbname='odoo20_dev', user='odoo', password='1NN0R1@2026')
    cur = conn.cursor()

    print("=== 1. Cleaning ir_act_window and ir_actions (help & name) ===")
    cur.execute("SELECT id, name, help FROM ir_act_window WHERE help::text ILIKE '%odoo%' OR name::text ILIKE '%odoo%'")
    windows = cur.fetchall()
    print(f"Found {len(windows)} ir_act_window records to clean")
    for w_id, w_name, w_help in windows:
        new_name = clean_dict_values(w_name) if isinstance(w_name, dict) else clean_text(w_name)
        new_help = clean_dict_values(w_help) if isinstance(w_help, dict) else clean_text(w_help)
        cur.execute("UPDATE ir_act_window SET name = %s, help = %s WHERE id = %s", (
            json.dumps(new_name) if isinstance(new_name, dict) else new_name,
            json.dumps(new_help) if isinstance(new_help, dict) else new_help,
            w_id
        ))
    print(f"Updated {len(windows)} ir_act_window records")

    print("=== 2. Cleaning digest_tip records ===")
    cur.execute("SELECT id, name, tip_description FROM digest_tip WHERE tip_description::text ILIKE '%odoo%' OR name::text ILIKE '%odoo%'")
    tips = cur.fetchall()
    print(f"Found {len(tips)} digest_tip records to clean")
    for tip_id, tip_name, tip_desc in tips:
        new_name = clean_dict_values(tip_name) if isinstance(tip_name, dict) else clean_text(tip_name)
        new_desc = clean_dict_values(tip_desc) if isinstance(tip_desc, dict) else clean_text(tip_desc)
        cur.execute("UPDATE digest_tip SET name = %s, tip_description = %s WHERE id = %s", (
            json.dumps(new_name) if isinstance(new_name, dict) else new_name,
            json.dumps(new_desc) if isinstance(new_desc, dict) else new_desc,
            tip_id
        ))
    print(f"Updated {len(tips)} digest_tip records")

    print("=== 3. Cleaning digest_digest records ===")
    cur.execute("SELECT id, name FROM digest_digest WHERE name::text ILIKE '%odoo%'")
    for d_id, d_name in cur.fetchall():
        new_name = clean_dict_values(d_name) if isinstance(d_name, dict) else clean_text(d_name)
        cur.execute("UPDATE digest_digest SET name = %s WHERE id = %s", (
            json.dumps(new_name) if isinstance(new_name, dict) else new_name,
            d_id
        ))
        print(f"Updated digest_digest {d_id}")

    print("=== 4. Cleaning res_partner and bot records ===")
    cur.execute("UPDATE res_partner SET name = 'InsilosBot', complete_name = 'InsilosBot', commercial_company_name = 'InsilosBot', email = 'insilosbot@example.com', email_normalized = 'insilosbot@example.com' WHERE id = 2")
    cur.execute("UPDATE res_partner SET name = 'Insilos POS', complete_name = 'Insilos POS', commercial_company_name = 'Insilos POS' WHERE id = 12")
    cur.execute("UPDATE discuss_channel SET name = 'Administrator, InsilosBot' WHERE id = 3")
    cur.execute("UPDATE calendar_calendar SET name = 'InsilosBot' WHERE id = 1")
    cur.execute("UPDATE calendar_user SET name = 'InsilosBot' WHERE id = 1")

    print("=== 5. Cleaning mail_message records ===")
    cur.execute("SELECT id, body FROM mail_message WHERE body ILIKE '%odoo%'")
    for m_id, m_body in cur.fetchall():
        new_body = clean_text(m_body)
        cur.execute("UPDATE mail_message SET body = %s WHERE id = %s", (new_body, m_id))
        print(f"Updated mail_message {m_id}")

    print("=== 6. Updating web_tour_tour url routes ===")
    cur.execute("UPDATE web_tour_tour SET url = REPLACE(url, '/odoo', '/insilos') WHERE url ILIKE '%/odoo%'")
    print(f"Updated {cur.rowcount} web_tour_tour records")

    print("=== 7. Cleaning knowledge_article records ===")
    cur.execute("SELECT id, name, body, template_name, template_body FROM knowledge_article WHERE template_body::text ILIKE '%odoo%' OR template_name::text ILIKE '%odoo%' OR body ILIKE '%odoo%'")
    for a_id, a_name, a_body, t_name, t_body in cur.fetchall():
        new_name = clean_dict_values(a_name) if isinstance(a_name, dict) else clean_text(a_name)
        new_body = clean_knowledge_article(a_body)
        new_tname = clean_dict_values(t_name) if isinstance(t_name, dict) else clean_text(t_name)
        new_tbody = clean_dict_values(t_body, is_knowledge=True) if isinstance(t_body, dict) else clean_knowledge_article(t_body)
        cur.execute("""
            UPDATE knowledge_article 
            SET name = %s, body = %s, template_name = %s, template_body = %s 
            WHERE id = %s
        """, (
            json.dumps(new_name) if isinstance(new_name, dict) else new_name,
            new_body,
            json.dumps(new_tname) if isinstance(new_tname, dict) else new_tname,
            json.dumps(new_tbody) if isinstance(new_tbody, dict) else new_tbody,
            a_id
        ))
        print(f"Updated knowledge_article {a_id}")

    print("=== 8. Cleaning documents_document records ===")
    cur.execute("SELECT id, name, url FROM documents_document WHERE id = 14 OR url ILIKE '%youtu%' OR name::text ILIKE '%odoo%'")
    for d_id, d_name, d_url in cur.fetchall():
        new_name = clean_dict_values(d_name) if isinstance(d_name, dict) else clean_text(d_name)
        new_url = "https://insilos.com" if (d_url and "youtu" in d_url) else clean_text(d_url)
        cur.execute("UPDATE documents_document SET name = %s, url = %s WHERE id = %s", (
            json.dumps(new_name) if isinstance(new_name, dict) else new_name,
            new_url,
            d_id
        ))
        print(f"Updated documents_document {d_id}")

    print("=== 9. Cleaning iap_service records ===")
    cur.execute("SELECT id, name, description FROM iap_service WHERE description::text ILIKE '%odoo%' OR name::text ILIKE '%odoo%'")
    for s_id, s_name, s_desc in cur.fetchall():
        new_name = clean_dict_values(s_name) if isinstance(s_name, dict) else clean_text(s_name)
        new_desc = clean_dict_values(s_desc) if isinstance(s_desc, dict) else clean_text(s_desc)
        cur.execute("UPDATE iap_service SET name = %s, description = %s WHERE id = %s", (
            json.dumps(new_name) if isinstance(new_name, dict) else new_name,
            json.dumps(new_desc) if isinstance(new_desc, dict) else new_desc,
            s_id
        ))
        print(f"Updated iap_service {s_id}")

    print("=== 10. Cleaning ir_act_url and ir_act_server ===")
    cur.execute("UPDATE ir_act_url SET url = 'https://insilos.com/apps' WHERE id = 37")
    cur.execute("UPDATE ir_act_url SET url = 'https://insilos.com/themes' WHERE id = 38")
    cur.execute("UPDATE ir_act_server SET name = jsonb_set(name::jsonb, '{en_US}', '\"Databases: pull databases and synchronize\"') WHERE id = 1250")
    cur.execute("UPDATE ir_actions SET name = jsonb_set(name::jsonb, '{en_US}', '\"Invoice report generated by Insilos\"') WHERE id = 532")

    print("=== 11. Cleaning event_stage and res_company ===")
    cur.execute("SELECT id, description FROM event_stage WHERE description::text ILIKE '%odoo%'")
    for es_id, es_desc in cur.fetchall():
        new_desc = clean_dict_values(es_desc) if isinstance(es_desc, dict) else clean_text(es_desc)
        cur.execute("UPDATE event_stage SET description = %s WHERE id = %s", (
            json.dumps(new_desc) if isinstance(new_desc, dict) else new_desc,
            es_id
        ))
        print(f"Updated event_stage {es_id}")

    cur.execute("SELECT id, invoice_terms_html FROM res_company WHERE invoice_terms_html::text ILIKE '%odoo%'")
    for rc_id, rc_terms in cur.fetchall():
        new_terms = clean_dict_values(rc_terms) if isinstance(rc_terms, dict) else clean_text(rc_terms)
        cur.execute("UPDATE res_company SET invoice_terms_html = %s WHERE id = %s", (
            json.dumps(new_terms) if isinstance(new_terms, dict) else new_terms,
            rc_id
        ))
        print(f"Updated res_company {rc_id}")

    print("=== 12. Cleaning hr_payroll_note and forum_forum ===")
    cur.execute("SELECT id, note FROM hr_payroll_note WHERE note::text ILIKE '%odoo%'")
    for hn_id, hn_note in cur.fetchall():
        new_note = clean_text(hn_note)
        cur.execute("UPDATE hr_payroll_note SET note = %s WHERE id = %s", (new_note, hn_id))
        print(f"Updated hr_payroll_note {hn_id}")

    cur.execute("SELECT id, faq FROM forum_forum WHERE faq::text ILIKE '%odoo%'")
    for ff_id, ff_faq in cur.fetchall():
        new_faq = clean_dict_values(ff_faq) if isinstance(ff_faq, dict) else clean_text(ff_faq)
        cur.execute("UPDATE forum_forum SET faq = %s WHERE id = %s", (
            json.dumps(new_faq) if isinstance(new_faq, dict) else new_faq,
            ff_id
        ))
        print(f"Updated forum_forum {ff_id}")

    print("=== 13. Cleaning AI models (ai_topic, ai_composer, ai_agent) ===")
    cur.execute("SELECT id, name, description, instructions FROM ai_topic WHERE name::text ILIKE '%odoo%' OR description::text ILIKE '%odoo%' OR instructions::text ILIKE '%odoo%'")
    for t_id, t_name, t_desc, t_inst in cur.fetchall():
        new_desc = clean_dict_values(t_desc) if isinstance(t_desc, dict) else clean_text(t_desc)
        new_inst = clean_dict_values(t_inst) if isinstance(t_inst, dict) else clean_text(t_inst)
        cur.execute("UPDATE ai_topic SET description = %s, instructions = %s WHERE id = %s", (
            json.dumps(new_desc) if isinstance(new_desc, dict) else new_desc,
            json.dumps(new_inst) if isinstance(new_inst, dict) else new_inst,
            t_id
        ))
        print(f"Updated ai_topic {t_id}")

    cur.execute("SELECT id, default_prompt FROM ai_composer WHERE default_prompt::text ILIKE '%odoo%'")
    for c_id, c_prompt in cur.fetchall():
        new_prompt = clean_text(c_prompt)
        cur.execute("UPDATE ai_composer SET default_prompt = %s WHERE id = %s", (new_prompt, c_id))
        print(f"Updated ai_composer {c_id}")

    cur.execute("""
        SELECT a.id, a.partner_id, p.name, a.subtitle, a.system_prompt 
        FROM ai_agent a 
        JOIN res_partner p ON a.partner_id = p.id 
        WHERE p.name ILIKE '%odoo%' OR a.subtitle::text ILIKE '%odoo%' OR a.system_prompt ILIKE '%odoo%'
    """)
    for agent_id, partner_id, a_name, a_sub, a_prompt in cur.fetchall():
        new_name = clean_text(a_name)
        new_sub = clean_dict_values(a_sub) if isinstance(a_sub, dict) else clean_text(a_sub)
        new_prompt = clean_text(a_prompt)
        cur.execute("UPDATE res_partner SET name = %s WHERE id = %s", (new_name, partner_id))
        cur.execute("UPDATE ai_agent SET subtitle = %s, system_prompt = %s WHERE id = %s", (
            json.dumps(new_sub) if isinstance(new_sub, dict) else new_sub,
            new_prompt,
            agent_id
        ))
        print(f"Updated ai_agent {agent_id}: {a_name} -> {new_name}")

    print("=== 14. Cleaning ir_model_fields_selection ===")
    cur.execute("SELECT id, name FROM ir_model_fields_selection WHERE name::text ILIKE '%odoo%'")
    for sel_id, sel_name in cur.fetchall():
        new_name = clean_dict_values(sel_name) if isinstance(sel_name, dict) else clean_text(sel_name)
        cur.execute("UPDATE ir_model_fields_selection SET name = %s WHERE id = %s", (
            json.dumps(new_name) if isinstance(new_name, dict) else new_name,
            sel_id
        ))
        print(f"Updated ir_model_fields_selection {sel_id}: {sel_name} -> {new_name}")

    print("=== 15. Cleaning res_groups ===")
    cur.execute("SELECT id, name, comment FROM res_groups WHERE name::text ILIKE '%odoo%' OR comment::text ILIKE '%odoo%'")
    for g_id, g_name, g_comm in cur.fetchall():
        new_name = clean_dict_values(g_name) if isinstance(g_name, dict) else clean_text(g_name)
        new_comm = clean_dict_values(g_comm) if isinstance(g_comm, dict) else clean_text(g_comm)
        cur.execute("UPDATE res_groups SET name = %s, comment = %s WHERE id = %s", (
            json.dumps(new_name) if isinstance(new_name, dict) else new_name,
            json.dumps(new_comm) if isinstance(new_comm, dict) else new_comm,
            g_id
        ))
        print(f"Updated res_groups {g_id}")

    print("=== 16. Cleaning ir_ui_view names ===")
    cur.execute("UPDATE ir_ui_view SET name = 'Insilos Information' WHERE id = 1101")
    cur.execute("UPDATE ir_ui_view SET name = 'Show Insilos Information' WHERE id = 1102")
    cur.execute("UPDATE ir_ui_view SET name = 'Insilos Menu' WHERE id = 1295")
    cur.execute("UPDATE ir_ui_view SET name = 'Insilos Courses Homepage' WHERE id = 14724")

    print("=== 17. Cleaning mail_mail and utm_source ===")
    cur.execute("SELECT id, body_html FROM mail_mail WHERE body_html ILIKE '%odoo%'")
    for mm_id, mm_body in cur.fetchall():
        new_body = clean_text(mm_body)
        cur.execute("UPDATE mail_mail SET body_html = %s WHERE id = %s", (new_body, mm_id))
        print(f"Updated mail_mail {mm_id}")
    cur.execute("UPDATE utm_source SET name = 'Insilos Agent' WHERE id = 19")
    cur.execute("UPDATE res_partner SET commercial_company_name = 'Insilos Agent', complete_name = 'Insilos Agent' WHERE id = 7")
    cur.execute("UPDATE mail_message SET subject = REPLACE(subject, 'Odoo', 'Insilos') WHERE subject ILIKE '%odoo%'")

    print("=== 18. Cleaning mail_template records ===")
    cur.execute('''
        SELECT id, name, subject, body_html 
        FROM mail_template 
        WHERE (body_html::text ILIKE '%odoo%' OR name::text ILIKE '%odoo%' OR subject::text ILIKE '%odoo%')
    ''')
    templates = cur.fetchall()
    print(f"Found {len(templates)} mail templates to clean")
    for t_id, name, subj, body in templates:
        new_name = clean_dict_values(name) if isinstance(name, dict) else clean_text(name)
        new_subj = clean_dict_values(subj) if isinstance(subj, dict) else clean_text(subj)
        new_body = clean_dict_values(body) if isinstance(body, dict) else clean_text(body)
        cur.execute('''
            UPDATE mail_template 
            SET name = %s, subject = %s, body_html = %s 
            WHERE id = %s
        ''', (
            json.dumps(new_name) if isinstance(new_name, dict) else new_name,
            json.dumps(new_subj) if isinstance(new_subj, dict) else new_subj,
            json.dumps(new_body) if isinstance(new_body, dict) else new_body,
            t_id
        ))
    print(f"Updated {len(templates)} mail templates")

    print("=== 19. Neutralizing telemetry crons ===")
    cur.execute("""
        UPDATE ir_cron 
        SET active = False, 
            cron_name = CASE 
                WHEN cron_name = 'Publisher: Update Notification' THEN 'Insilos: Update Notification'
                WHEN cron_name = 'Databases: pull databases from Odoo.com and synchronize' THEN 'Databases: pull databases and synchronize'
                ELSE cron_name 
            END
        WHERE id IN (5, 91) OR cron_name ILIKE '%publisher%' OR cron_name ILIKE '%telemetry%'
    """)

    conn.commit()
    conn.close()
    print("All database branding synchronization completed successfully!")

if __name__ == '__main__':
    main()
