#!/usr/bin/env python3
"""
tools/rebrand_seed_and_orm.py
Systematic replacement of legacy colors (#875A7B, #714B67) and backend URLs (/odoo/)
in seed XML schemas, ORM defaults, and view templates.
Complies with HARD_REFACTOR_PART_A and PART_B.
"""

import os
import re

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def replace_in_file(rel_path, replacements):
    full_path = os.path.join(ROOT_DIR, rel_path)
    if not os.path.exists(full_path):
        print(f'[WARN] File not found: {rel_path}')
        return 0
    with open(full_path, 'r', encoding='utf-8') as f:
        content = f.read()
    orig_content = content
    for pattern, repl in replacements:
        if isinstance(pattern, str):
            content = content.replace(pattern, repl)
        else:
            content = pattern.sub(repl, content)
    if content != orig_content:
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'[MODIFIED] {rel_path}')
        return 1
    return 0

def run_rebrand():
    total_modified = 0

    # 1. Base module seed: odoo/addons/base/data/ir_module_module.xml
    total_modified += replace_in_file('odoo/addons/base/data/ir_module_module.xml', [
        ('<field name="author">Odoo S.A.</field>', '<field name="author">Insilos</field>'),
        ('https://www.odoo.com', 'https://www.insilos.com'),
        ('https://odoo.com', 'https://insilos.com'),
        ('https://play.google.com/store/apps/details?id=com.odoo.mobile', 'https://insilos.com/app/mobile'),
    ])

    # 2. Discuss channel default avatar SVG & tests
    total_modified += replace_in_file('addons/mail/models/discuss/discuss_channel.py', [
        ('fill="#875a7b"', 'fill="#004455"'),
        ("replace('fill=\"#875a7b\"',", "replace('fill=\"#004455\"',"),
    ])
    total_modified += replace_in_file('addons/mail/tests/discuss/test_discuss_channel.py', [
        ("replace('fill=\"#875a7b\"',", "replace('fill=\"#004455\"',"),
    ])

    # 3. Web & UI colors
    total_modified += replace_in_file('addons/web/static/src/core/colors/colors.js', [
        ('["#875A7B", "#A5D8D7", "#DCD0D9"]', '["#004455", "#A5D8D7", "#DCD0D9"]'),
    ])
    total_modified += replace_in_file('addons/hr_recruitment_skills/static/src/components/match_scores_gauge/match_scores_gauge.js', [
        ('"#714B67",', '"#004455",'),
    ])
    total_modified += replace_in_file('addons/pos_self_order/static/src/app/kiosk_style.js', [
        ('if (!bgPrimary || bgPrimary === "#875A7B") {\n        bgPrimary = "#714B67";\n    }',
         'if (!bgPrimary || bgPrimary === "#875A7B" || bgPrimary === "#714B67") {\n        bgPrimary = "#004455";\n    }'),
    ])
    total_modified += replace_in_file('addons/lunch/views/lunch_product_views.xml', [
        ('color="#875A7B"', 'color="#004455"'),
    ])
    total_modified += replace_in_file('addons/web_unsplash/static/description/index.html', [
        ('color:#875A7B;', 'color:#004455;'),
    ])

    # 4. Enterprise webclient & project sharing meta theme-color
    total_modified += replace_in_file('enterprise/web_enterprise/views/webclient_templates.xml', [
        ('<meta name="theme-color" content="#714B67"/>', '<meta name="theme-color" content="#004455"/>'),
    ])
    total_modified += replace_in_file('enterprise/project_enterprise/views/project_sharing_templates.xml', [
        ('<meta name="theme-color" content="#875A7B"/>', '<meta name="theme-color" content="#004455"/>'),
    ])

    # 5. Enterprise hr_referral / hr_applicant / wizard
    total_modified += replace_in_file('enterprise/hr_referral/wizard/hr_referral_alert_mail_wizard.py', [
        ("url = '/odoo/action-hr_referral.action_hr_referral_welcome_screen'",
         "url = '/insilos/action-hr_referral.action_hr_referral_welcome_screen'"),
    ])
    total_modified += replace_in_file('enterprise/hr_referral/models/hr_applicant.py', [
        ("action_url = f'/odoo/action-{action_value}?active_model={self._name}'",
         "action_url = f'/insilos/action-{action_value}?active_model={self._name}'"),
        ('link1=Markup(\'<a href="/odoo/action-hr_referral.action_hr_referral_reward?active_model=hr.referral.reward">\')',
         'link1=Markup(\'<a href="/insilos/action-hr_referral.action_hr_referral_reward?active_model=hr.referral.reward">\')'),
        ("msg['url'] = '/odoo/action-hr_referral.action_hr_job_employee_referral'",
         "msg['url'] = '/insilos/action-hr_referral.action_hr_job_employee_referral'"),
    ])

    # 6. Enterprise payroll stats & belgian payroll xlsx
    total_modified += replace_in_file('enterprise/hr_payroll/static/src/components/dashboard/payroll_stats/payroll_stats.js', [
        ("const borderColor = this.props.is_sample ? '#dddddd' : '#875a7b';",
         "const borderColor = this.props.is_sample ? '#dddddd' : '#004455';"),
    ])
    total_modified += replace_in_file('enterprise/l10n_be_hr_payroll/wizard/l10n_be_social_balance_sheet.py', [
        ("'bg_color': '#875A7B'", "'bg_color': '#004455'"),
    ])
    total_modified += replace_in_file('enterprise/l10n_be_hr_payroll/wizard/l10n_be_social_security_certificate.py', [
        ("'bg_color': '#875A7B'", "'bg_color': '#004455'"),
    ])

    # 7. Enterprise test spreadsheet controllers
    total_modified += replace_in_file('enterprise/test_spreadsheet_edition/tests/test_spreadsheet_controllers.py', [
        ("self.assertEqual(data['company_colors'], ['#FFFFFF', '#875A7B'])",
         "self.assertEqual(data['company_colors'], ['#FFFFFF', '#004455'])"),
        ("self.assertEqual(data['company_colors'], ['#aa0000', '#aa1111', '#FFFFFF', '#875A7B', '#bb0000', '#bb1111'])",
         "self.assertEqual(data['company_colors'], ['#aa0000', '#aa1111', '#FFFFFF', '#004455', '#bb0000', '#bb1111'])"),
    ])
    total_modified += replace_in_file('enterprise/spreadsheet_sale_management/static/src/bundle/field_sync/field_sync_highlight_store.js', [
        ('color: "#875A7B"', 'color: "#004455"'),
    ])
    total_modified += replace_in_file('enterprise/spreadsheet_sale_management/static/tests/field_sync_action.test.js', [
        ('expect(highlightStore.highlights[0].color).toBe("#875A7B");',
         'expect(highlightStore.highlights[0].color).toBe("#004455");'),
    ])
    total_modified += replace_in_file('enterprise/test_spreadsheet_edition/static/tests/abstract_action.test.js', [
        ('company_colors: ["#875A7B", "not a valid color"],',
         'company_colors: ["#004455", "not a valid color"],'),
        ('expect(model.getters.getCustomColors()).toEqual(["#875A7B"]);',
         'expect(model.getters.getCustomColors()).toEqual(["#004455"]);'),
    ])

    # 8. Marketing automation templates
    marketing_tpl_files = [
        'enterprise/marketing_automation/data/templates/mail_template_body_welcome_template.xml',
        'enterprise/marketing_automation/data/templates/mail_template_body_yellow_discount_template.xml',
        'enterprise/marketing_automation_website_sale/views/mailing_arch_templates.xml',
    ]
    for f in marketing_tpl_files:
        total_modified += replace_in_file(f, [
            ('https://www.facebook.com/Odoo', 'https://www.facebook.com/Insilos'),
            ('https://www.linkedin.com/company/odoo', 'https://www.linkedin.com/company/insilos'),
            ('https://twitter.com/Odoo', 'https://twitter.com/Insilos'),
            ('https://www.instagram.com/explore/tags/odoo/', 'https://www.instagram.com/explore/tags/insilos/'),
            ('https://www.tiktok.com/@odoo', 'https://www.tiktok.com/@insilos'),
        ])

    # 9. Special account template gradients & URLs
    total_modified += replace_in_file('addons/account/data/mail_template_data.xml', [
        ('linear-gradient(140deg,#714B67 0%,#8a6381 55%,#bfa8c2 100%)', 'linear-gradient(140deg,#004455 0%,#00657f 55%,#0096B3 100%)'),
        ('linear-gradient(135deg,#714B67 0%,#9b77a3 100%)', 'linear-gradient(135deg,#004455 0%,#0096B3 100%)'),
        ('/odoo/accounting/action-account.action_account_moves_email', '/insilos/accounting/action-account.action_account_moves_email'),
        ('/odoo/accounting/{{ object.id }}/account.move/{{ invoices.id }}', '/insilos/accounting/{{ object.id }}/account.move/{{ invoices.id }}'),
    ])

    # 10. General XML/HTML color sweeping: replace #875A7B and #714B67 in all template XML files
    p_legacy = re.compile(r'#(?:875A7B|714B67)', re.IGNORECASE)

    for root_dir in ['addons', 'enterprise', 'odoo/addons']:
        for dirpath, _, filenames in os.walk(os.path.join(ROOT_DIR, root_dir)):
            if any(skip in dirpath for skip in ['node_modules', '.git', '__pycache__']):
                continue
            for f in filenames:
                if not f.endswith(('.xml', '.html')):
                    continue
                filepath = os.path.join(dirpath, f)
                rel_path = os.path.relpath(filepath, ROOT_DIR)
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as fp:
                    c = fp.read()
                if p_legacy.search(c):
                    c_new = re.sub(r'#875A7B', '#004455', c, flags=re.IGNORECASE)
                    c_new = re.sub(r'#714B67', '#004455', c_new, flags=re.IGNORECASE)
                    if c_new != c:
                        with open(filepath, 'w', encoding='utf-8') as fp:
                            fp.write(c_new)
                        print(f'[XML REBRAND COLOR] {rel_path}')
                        total_modified += 1

    # 11. Backend /odoo/ route replacements in ORM/templates/controllers
    orm_route_replacements = [
        ('enterprise/appointment/data/mail_template_data.xml', [
            ('/odoo/calendar.event/{{ object.id }}', '/insilos/calendar.event/{{ object.id }}')
        ]),
        ('enterprise/appointment/controllers/calendar.py', [
            ("request.redirect(f'/odoo/{attendee.event_id._name}/{id}?db={request.env.cr.dbname}')",
             "request.redirect(f'/insilos/{attendee.event_id._name}/{id}?db={request.env.cr.dbname}')")
        ]),
        ('enterprise/appointment/views/appointment_templates_appointments.xml', [
            ('/odoo/{{main_object._name}}/{{main_object.id}}?menu_id={{backend_menu_id}}',
             '/insilos/{{main_object._name}}/{{main_object.id}}?menu_id={{backend_menu_id}}'),
            ("'/odoo/action-appointment.appointment_type_action/%s'",
             "'/insilos/action-appointment.appointment_type_action/%s'")
        ]),
        ('enterprise/hr_expense_stripe/data/mail_template_data.xml', [
            ('{{ website_url }}/odoo/cards', '{{ website_url }}/insilos/cards')
        ]),
        ('enterprise/hr_expense_stripe/models/res_company.py', [
            ("f'{self.get_base_url()}/odoo/settings#hr_expense'",
             "f'{self.get_base_url()}/insilos/settings#hr_expense'"),
            ("f\"{self.get_base_url()}/odoo/settings#hr_expense\"",
             "f\"{self.get_base_url()}/insilos/settings#hr_expense\"")
        ]),
        ('enterprise/web_studio/data/mail_templates.xml', [
            ("'/odoo/res.partner/%s'", "'/insilos/res.partner/%s'")
        ]),
        ('enterprise/whatsapp/models/whatsapp_message.py', [
            ("url = f\"{self.get_base_url()}/odoo/{self.mail_message_id.model}/{self.mail_message_id.res_id}\"",
             "url = f\"{self.get_base_url()}/insilos/{self.mail_message_id.model}/{self.mail_message_id.res_id}\"")
        ]),
        ('enterprise/whatsapp/models/discuss_channel.py', [
            ("url = Markup('{base_url}/odoo/{model}/{res_id}')",
             "url = Markup('{base_url}/insilos/{model}/{res_id}')"),
            ("url = Markup('{base_url}/odoo/discuss.channel/{channel_id}')",
             "url = Markup('{base_url}/insilos/discuss.channel/{channel_id}')")
        ]),
        ('enterprise/hr_payroll/models/res_company.py', [
            ("warning_url = f\"{action.get_base_url()}/odoo/action-{action.id}\"",
             "warning_url = f\"{action.get_base_url()}/insilos/action-{action.id}\"")
        ]),
        ('enterprise/timesheet_grid/models/res_company.py', [
            ("f\"{self.get_base_url()}/odoo/action-{action_xmlid}\"",
             "f\"{self.get_base_url()}/insilos/action-{action_xmlid}\"")
        ]),
        ('enterprise/planning/models/hr.py', [
            ('f"/odoo/action-planning.planning_action_open_shift?', 'f"/insilos/action-planning.planning_action_open_shift?')
        ]),
        ('enterprise/planning/controllers/main.py', [
            ("request.redirect('/odoo/action-planning.planning_action_open_shift')",
             "request.redirect('/insilos/action-planning.planning_action_open_shift')")
        ]),
        ('enterprise/helpdesk/views/helpdesk_portal_templates.xml', [
            ("'/odoo/action-helpdesk.helpdesk_ticket_action_main_tree/%s?menu_id=%",
             "'/insilos/action-helpdesk.helpdesk_ticket_action_main_tree/%s?menu_id=%")
        ]),
        ('enterprise/helpdesk/views/helpdesk_team_views.xml', [
            ('/odoo/settings#email-alias-setting', '/insilos/settings#email-alias-setting')
        ]),
        ('enterprise/web_map/static/src/map_view/map_renderer.xml', [
            ('/odoo/action-base_setup.action_general_configuration', '/insilos/action-base_setup.action_general_configuration')
        ]),
        ('enterprise/social/views/social_post_template_views.xml', [
            ('/odoo/action-social.action_social_media', '/insilos/action-social.action_social_media')
        ]),
        ('enterprise/social/views/social_stream_views.xml', [
            ('/odoo/action-social.action_social_stream_post', '/insilos/action-social.action_social_stream_post')
        ]),
        ('enterprise/social/views/social_account_views.xml', [
            ('/odoo/action-social.action_social_media', '/insilos/action-social.action_social_media'),
            ('start posting from Odoo', 'start posting from Insilos')
        ]),
        ('enterprise/sale_subscription/controllers/portal.py', [
            ("backend_url = f'/odoo/action-{order_sudo._get_portal_return_action().id}/{order_sudo.id}'",
             "backend_url = f'/insilos/action-{order_sudo._get_portal_return_action().id}/{order_sudo.id}'")
        ]),
        ('enterprise/social_twitter/controllers/main.py', [
            ("request.redirect('/odoo/action-social.action_social_stream_post')",
             "request.redirect('/insilos/action-social.action_social_stream_post')"),
            ("request.redirect('/odoo')", "request.redirect('/insilos')"),
        ]),
        ('enterprise/social_facebook/controllers/main.py', [
            ("request.redirect('/odoo/action-social.action_social_stream_post')",
             "request.redirect('/insilos/action-social.action_social_stream_post')"),
            ("request.redirect('/odoo')", "request.redirect('/insilos')"),
        ]),
        ('enterprise/social_linkedin/controllers/main.py', [
            ("request.redirect('/odoo/action-social.action_social_stream_post')",
             "request.redirect('/insilos/action-social.action_social_stream_post')"),
            ("request.redirect('/odoo')", "request.redirect('/insilos')"),
        ]),
        ('enterprise/social_instagram/controllers/main.py', [
            ("request.redirect('/odoo/action-social.action_social_stream_post')",
             "request.redirect('/insilos/action-social.action_social_stream_post')"),
            ("request.redirect('/odoo')", "request.redirect('/insilos')"),
        ]),
        ('enterprise/pos_enterprise/controllers/main.py', [
            ("request.redirect('/odoo/action-pos_preparation_display.action_preparation_display')",
             "request.redirect('/insilos/action-pos_preparation_display.action_preparation_display')")
        ]),
        ('enterprise/sale_amazon/controllers/onboarding.py', [
            ("account_url = f'/odoo/action-sale_amazon.list_amazon_account_action/{account_id}'",
             "account_url = f'/insilos/action-sale_amazon.list_amazon_account_action/{account_id}'")
        ]),
        ('enterprise/sale_shopee/controllers/onboarding.py', [
            ("redirect_url = f'/odoo/action-sale_shopee.action_shopee_account_list/{account.id}'",
             "redirect_url = f'/insilos/action-sale_shopee.action_shopee_account_list/{account.id}'")
        ]),
        ('enterprise/sign/views/terms_views.xml', [
            ("'/odoo/action-sign.sign_settings_action'", "'/insilos/action-sign.sign_settings_action'")
        ]),
        ('enterprise/documents_sign/models/sign_request.py', [
            ("'url': f\"/odoo/action-documents.document_action_preference?{url_params}\"",
             "'url': f\"/insilos/action-documents.document_action_preference?{url_params}\"")
        ]),
        ('enterprise/documents/controllers/documents.py', [
            ("request.redirect(f'/odoo/documents/", "request.redirect(f'/insilos/documents/"),
            ("f'/odoo/documents/{quote(document_sudo.access_token, safe=\"\")}'",
             "f'/insilos/documents/{quote(document_sudo.access_token, safe=\"\")}'"),
        ]),
        ('enterprise/documents/views/documents_templates_portal.xml', [
            ("'/odoo/documents_portal'", "'/insilos/documents_portal'")
        ]),
        ('enterprise/web_grid/static/src/components/many2one_grid_row/many2one_grid_row.xml', [
            ("`/odoo/${this.urlRelation}/${this.resId}`", "`/insilos/${this.urlRelation}/${this.resId}`")
        ]),
        ('addons/mail_group/data/mail_templates.xml', [
            ('/odoo/action-mail_group.mail_group_action/{{group.id}}', '/insilos/action-mail_group.mail_group_action/{{group.id}}'),
            ('/odoo/action-mail_group.mail_group_action?view_type=form', '/insilos/action-mail_group.mail_group_action?view_type=form')
        ]),
        ('addons/calendar/controllers/main.py', [
            ("request.redirect('/odoo/calendar.event/%s?db=%s' % (id, request.env.cr.dbname))",
             "request.redirect('/insilos/calendar.event/%s?db=%s' % (id, request.env.cr.dbname))")
        ]),
        ('addons/calendar/data/mail_templates_chatter.xml', [
            ('{{base_url}}/odoo/{{activity.res_model}}/{{activity.res_id}}/calendar.event/{{activity.',
             '{{base_url}}/insilos/{{activity.res_model}}/{{activity.res_id}}/calendar.event/{{activity.')
        ]),
        ('addons/payment_razorpay/controllers/onboarding.py', [
            ("redirect_url = f\"/odoo/action-{action.id}/{int(provider.id)}\"",
             "redirect_url = f\"/insilos/action-{action.id}/{int(provider.id)}\"")
        ]),
        ('addons/hr_expense/models/hr_expense.py', [
            ("'url': f'/odoo/{manager.id}/expenses-to-process'",
             "'url': f'/insilos/{manager.id}/expenses-to-process'")
        ]),
        ('addons/hr_expense/views/res_config_settings_views.xml', [
            ('/odoo/settings#email-alias-setting', '/insilos/settings#email-alias-setting')
        ]),
        ('addons/base_install_request/data/mail_templates.xml', [
            ('t-attf-href="/odoo/{{ module_id.id }}/action-base_install_request.action_base_module_install_review',
             't-attf-href="/insilos/{{ module_id.id }}/action-base_install_request.action_base_module_install_review')
        ]),
        ('addons/project/models/project_task.py', [
            ("'url': f'/odoo/project/{self.project_id.id}/tasks/{self.id}'",
             "'url': f'/insilos/project/{self.project_id.id}/tasks/{self.id}'"),
            ("'url': f'/odoo/all-tasks/{self.id}'",
             "'url': f'/insilos/all-tasks/{self.id}'"),
            ("'url': f\"/odoo/{self.project_id.id}/action-project.act_project_project_2_project_task_all/{self.id}?",
             "'url': f\"/insilos/{self.project_id.id}/action-project.act_project_project_2_project_task_all/{self.id}?"),
        ]),
        ('addons/project/views/project_portal_project_project_templates.xml', [
            ("backend_url=\"'/odoo/project.project/%s' % (project.id)",
             "backend_url=\"'/insilos/project.project/%s' % (project.id)"),
        ]),
        ('addons/project/views/project_portal_project_task_templates.xml', [
            ("backend_url=\"'/odoo/action-project.action_view_my_task/%s' % (task.id)",
             "backend_url=\"'/insilos/action-project.action_view_my_task/%s' % (task.id)"),
        ]),
        ('addons/mrp/models/stock_orderpoint.py', [
            ("'url': f'/odoo/action-mrp.action_mrp_production_form/{production.id}'",
             "'url': f'/insilos/action-mrp.action_mrp_production_form/{production.id}'")
        ]),
        ('addons/mrp/wizard/product_replenish.py', [
            ("'url': f'/odoo/action-mrp.action_mrp_production_form/{production.id}'",
             "'url': f'/insilos/action-mrp.action_mrp_production_form/{production.id}'")
        ]),
        ('addons/hr/models/hr_employee.py', [
            ("link = Markup('<a href=\"/odoo/%(employee_id)s/action-hr.plan_wizard_action?active_model=hr.employee&",
             "link = Markup('<a href=\"/insilos/%(employee_id)s/action-hr.plan_wizard_action?active_model=hr.employee&")
        ]),
        ('addons/auth_totp_mail/models/res_users.py', [
            ("return '/odoo/action-auth_totp_mail.action_activate_two_factor_authentication'",
             "return '/insilos/action-auth_totp_mail.action_activate_two_factor_authentication'")
        ]),
        ('addons/base_import_module/models/base_import_module.py', [
            ("'url': '/odoo'", "'url': '/insilos'")
        ]),
        ('addons/purchase_stock/models/stock.py', [
            ("'url': f'/odoo/action-purchase.action_rfq_form/{order.id}'",
             "'url': f'/insilos/action-purchase.action_rfq_form/{order.id}'")
        ]),
        ('addons/purchase_stock/wizard/product_replenish.py', [
            ("'url': f'/odoo/action-purchase.action_rfq_form/{order_line.order_id.id}'",
             "'url': f'/insilos/action-purchase.action_rfq_form/{order_line.order_id.id}'")
        ]),
        ('addons/google_gmail/controllers/main.py', [
            ("'redirect_url': '/odoo'", "'redirect_url': '/insilos'"),
            ("return f'/odoo/{record._name}/{record.id}'", "return f'/insilos/{record._name}/{record.id}'"),
            ("return f'/odoo/my-preferences/{request.env.user.id}'", "return f'/insilos/my-preferences/{request.env.user.id}'"),
        ]),
        ('addons/microsoft_outlook/controllers/main.py', [
            ("'redirect_url': '/odoo'", "'redirect_url': '/insilos'"),
            ("return f'/odoo/{record._name}/{record.id}'", "return f'/insilos/{record._name}/{record.id}'"),
            ("return f'/odoo/my-preferences/{request.env.user.id}'", "return f'/insilos/my-preferences/{request.env.user.id}'"),
        ]),
        ('addons/auth_oauth/controllers/main.py', [
            ("url = '/odoo'", "url = '/insilos'"),
            ("url = '/odoo/action-%s' % action", "url = '/insilos/action-%s' % action")
        ]),
        ('addons/mass_mailing_sms/controllers/main.py', [
            ("return request.redirect('/odoo')", "return request.redirect('/insilos')")
        ]),
        ('addons/website/models/website.py', [
            ("'link': 'website_url' in rec and rec.website_url or f'/odoo/{model_name}/{rec.id}'",
             "'link': 'website_url' in rec and rec.website_url or f'/insilos/{model_name}/{rec.id}'"),
            ("return \"/odoo/action-website.website_preview?\" + urls.url_encode(action_params)",
             "return \"/insilos/action-website.website_preview?\" + urls.url_encode(action_params)")
        ]),
        ('addons/website/controllers/main.py', [
            ("action_url = f\"/odoo/action-website.website_configurator?menu_id={request.env.ref('website.menu_webs",
             "action_url = f\"/insilos/action-website.website_configurator?menu_id={request.env.ref('website.menu_webs"),
            ("return request.redirect(f\"/odoo/ir.ui.view/{page.get('view_id')}\")",
             "return request.redirect(f\"/insilos/ir.ui.view/{page.get('view_id')}\")")
        ]),
        ('addons/website_slides/views/website_slides_templates_course.xml', [
            ('t-attf-href="/odoo', 't-attf-href="/insilos')
        ]),
        ('addons/website_event_booth/views/event_booth_templates.xml', [
            ('t-attf-href="/odoo/event.event/{{event.id}}"', 't-attf-href="/insilos/event.event/{{event.id}}"')
        ]),
        ('addons/website_event/views/event_templates_list.xml', [
            ('href="/odoo/action-event.action_event_view?view_type=for', 'href="/insilos/action-event.action_event_view?view_type=for')
        ]),
        ('addons/website_event/views/event_templates_page_registration.xml', [
            ('t-attf-href="/odoo/event.event/{', 't-attf-href="/insilos/event.event/{')
        ]),
        ('addons/hr_recruitment_survey/views/survey_templates_statistics.xml', [
            ('t-attf-href="/odoo/action-hr_recruitment_survey.survey_survey_action_recruitment/{{survey.id}}"',
             't-attf-href="/insilos/action-hr_recruitment_survey.survey_survey_action_recruitment/{{survey.id}}"')
        ]),
        ('addons/website_sale/templates/shop_page_templates.xml', [
            ('href="/odoo/action-website_sale.product_template_action_website"',
             'href="/insilos/action-website_sale.product_template_action_website"')
        ]),
        ('addons/survey/views/survey_templates_management.xml', [
            ('t-attf-href="/odoo/action-survey.action_survey_form/{{survey.id}}"',
             't-attf-href="/insilos/action-survey.action_survey_form/{{survey.id}}"'),
            ("t-att-href=\"'/odoo/action-survey.action_survey_form/%s' % survey.id\"",
             "t-att-href=\"'/insilos/action-survey.action_survey_form/%s' % survey.id\""),
            ('t-attf-href="/odoo/action-survey.action_survey_user_input',
             't-attf-href="/insilos/action-survey.action_survey_user_input')
        ]),
        ('addons/im_livechat/views/im_livechat_chatbot_templates.xml', [
            ('t-attf-href="/odoo/action-im_livechat.chatbot_script_action/#{chatbot_script.id}"',
             't-attf-href="/insilos/action-im_livechat.chatbot_script_action/#{chatbot_script.id}"')
        ]),
        ('addons/im_livechat/static/src/core/public_web/livechat_rating_notification_message.xml', [
            ('t-attf-href="/odoo/discuss?active_id=discuss.channel_{{this.channel.id}}',
             't-attf-href="/insilos/discuss?active_id=discuss.channel_{{this.channel.id}}')
        ]),
        ('addons/data_recycle/views/data_recycle_templates.xml', [
            ('t-attf-href="/odoo/{{recycle_model_id}}/action-data_recycle.action',
             't-attf-href="/insilos/{{recycle_model_id}}/action-data_recycle.action')
        ]),
        ('addons/payment/views/payment_form_templates.xml', [
            ('href="/odoo/action-payment.action_start_payment_onboarding"',
             'href="/insilos/action-payment.action_start_payment_onboarding"'),
            ('href="/odoo/action-payment.action_payment_provider"',
             'href="/insilos/action-payment.action_payment_provider"'),
            ('href="/odoo/action-payment.action_payment_method"',
             'href="/insilos/action-payment.action_payment_method"')
        ]),
        ('addons/website_sale_slides/views/website_slides_templates.xml', [
            ('t-attf-href="/odoo/action-website_sale.product_template_action_website/{{channel.product_id.produ',
             't-attf-href="/insilos/action-website_sale.product_template_action_website/{{channel.product_id.produ')
        ]),
        ('addons/website_slides_survey/static/src/xml/website_slides_fullscreen.xml', [
            ("t-att-href=\"'/odoo/survey.survey/' + slide.certificationId\"",
             "t-att-href=\"'/insilos/survey.survey/' + slide.certificationId\"")
        ]),
        ('addons/html_editor/static/src/main/media/media_dialog/attachment_error.xml', [
            ("t-att-href=\"'/odoo/ir.ui.view/' + window.encodeURIComponent(view.id)\"",
             "t-att-href=\"'/insilos/ir.ui.view/' + window.encodeURIComponent(view.id)\"")
        ]),
        ('addons/social_media/demo/res_company_demo.xml', [
            ('https://www.instagram.com/explore/tags/odoo/', 'https://www.instagram.com/explore/tags/insilos/')
        ]),
    ]

    for rel_p, reps in orm_route_replacements:
        total_modified += replace_in_file(rel_p, reps)

    print(f'\n[DONE] Total files modified: {total_modified}')

if __name__ == '__main__':
    run_rebrand()
