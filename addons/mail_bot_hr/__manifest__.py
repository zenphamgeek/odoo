{
    'name': "InsilosBot - HR",
    'summary': """Bridge module between hr and mailbot.""",
    'description': """This module adds the InsilosBot state and notifications in the user form modified by hr.""",
    'website': "https://insilos.com",
    'category': 'Productivity/Discuss',
    'depends': ['mail_bot', 'hr'],
    'auto_install': True,
    'data': [
        'views/res_users_views.xml',
    ],
    'author': 'Insilos',
    'license': 'LGPL-3',
}
