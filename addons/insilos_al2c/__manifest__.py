{
    'name': 'Insilos Autonomous Lead-to-Cash (Foundation)',
    'version': '20.0.1.0.0',
    'category': 'Sales/Sales',
    'summary': 'AL2C Phase 0 & Phase 1: catalog as code, delivery templates, knowledge, guardrails, e-invoice, commissions, contract scanner',
    'description': """
Autonomous Lead-to-Cash foundation for Innoria / Insilos.

* Product catalog (ERP, SaaS, GRC, AI, Mojo AI Apps, Services) with service policies
* Activate-style project templates (Prepare, Explore, Realize, Deploy, Run)
* Quotation templates per bundle
* Knowledge tree and Documents workspace structure
* Autonomy kill-switch, per-agent daily budget and deal-desk approval on quotations
* Decree 70/2025 statutory e-invoice adapter interface
* Contract clause deviation scanner with General Counsel approval workflow
* Cash-matched sales commission and 2026 Vietnamese 5-bracket PIT & statutory insurance
""",
    'author': 'Innoria',
    'license': 'LGPL-3',
    'depends': [
        'sale_management',
        'sale_subscription',
        'sale_timesheet',
        'sale_project',
        'project',
        'project_enterprise',
        'knowledge',
        'documents',
        'documents_project',
        'crm',
        'account',
        'sign',
        'hr_payroll',
        'helpdesk',
        'portal',
        'auth_signup',
    ],
    'data': [
        'security/al2c_security.xml',
        'security/ir.access.csv',
        'data/ir_config_parameter_data.xml',
        'data/product_category_data.xml',
        'data/knowledge_data.xml',
        'data/project_template_data.xml',
        'data/product_template_data.xml',
        'data/product_price_data.xml',
        'data/sale_order_template_data.xml',
        'data/documents_data.xml',
        'data/al2c_claim_atom_data.xml',
        'data/hr_payroll_data.xml',
        'data/al2c_tech_asset_data.xml',
        'views/sale_order_views.xml',
        'views/product_template_views.xml',
        'views/crm_lead_views.xml',
        'views/account_move_views.xml',
        'views/al2c_value_case_views.xml',
        'views/al2c_dispute_views.xml',
        'views/al2c_tech_asset_views.xml',
        'views/al2c_runtime_incident_views.xml',
        'views/report_templates.xml',
        'views/mail_templates.xml',
        'views/portal_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'insilos_al2c/static/src/scss/portal_branding.scss',
        ],
    },
    'installable': True,
    'application': False,
}

