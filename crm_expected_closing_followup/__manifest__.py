{
    'name': 'CRM Expected Closing Followup',
    'version': '19.0.1.0.0',
    'category': 'Sales/CRM',
    'summary': 'Daily follow-up for missed expected closing in CRM',
    'description': 'Send automated emails for leads with missed expected closing dates.',
    'author': 'Vishnu Sasikumar',
    'depends': ['crm', 'mail'],
    'data': [
        'security/security_groups.xml',
        'data/expected_closing_mail_template.xml',
        'data/expected_closing_cron.xml',
    ],
    'images': ['static/description/banner.png'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}