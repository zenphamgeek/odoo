# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'InsilosBot',
    'version': '1.2',
    'category': 'Productivity/Discuss',
    'summary': 'Add InsilosBot in discussions',
    'website': 'https://insilos.com',
    'depends': ['mail'],
    'auto_install': True,
    'data': [
        'views/res_users_views.xml',
        'data/mailbot_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'mail_bot/static/src/scss/odoobot_style.scss',
        ],
    },
    'author': 'Insilos',
    'license': 'LGPL-3',
}
