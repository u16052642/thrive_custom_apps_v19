# -*- coding: utf-8 -*-
{
    'name': 'CRM Inactivity Inquiry Report ',
    'version': '19.0.1',
    'author': 'AppsComp Widgets Pvt Ltd',
    'category': 'Sales',
    'website': 'www.appscomp.com',
    "description":"The scheduled action will be created; and it will check automatically (CRM/Lead), which is not updated in the past 2 days (e.g., New Lead or Oppurtunity has been created in the past 2 days, but no activities followed for those entries.) by sales persons and specific Lead/Oppurtunities’ entries information with Excel report attachment through an email to the sales management.",
    "summary": "The scheduled action will be created; and it will check automatically (CRM/Lead), which is not updated in the past 2 days (e.g., New Lead or Oppurtunity has been created in the past 2 days, but no activities followed for those entries.) by sales persons and specific Lead/Oppurtunities’ entries information with Excel report attachment through an email to the sales management.",
    'images': ['static/description/banner.png'],
    #'images': ['static/description/banner.gif'],
    #'price': '',
    "live_test_url": "https://youtu.be/QCTPvMGXf_M",
    'depends': ['base','mass_mailing','crm', 'product','hr'],
    'data': [
        'data/crm_cron_file.xml',

    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'OPL-1',
}
