{
    'name': 'CRM Stage Notifications',
    'summary': 'Automatically send SMS, Viber, and Email notifications when '
               'CRM leads change stages',

    'author': 'Kitworks Systems',
    'website': 'https://github.com/kitworks-systems/addons',

    'category': 'Marketing',
    'license': 'LGPL-3',
    'version': '19.0.1.1.1',

    'depends': ['crm', 'sms',
                'generic_mixin', 'mail'],
    'data': [
        'views/crm_stage_view.xml',
        'views/crm_lead_view.xml',
    ],
    'installable': True,

    'images': [
        'static/description/cover.png',
        'static/description/icon.png',
    ],

}
