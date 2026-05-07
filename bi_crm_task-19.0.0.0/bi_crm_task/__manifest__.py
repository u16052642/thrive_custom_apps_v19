# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Create Task from Lead',
    'version': '19.0.0.0',
    'category': 'CRM',
    'license': 'OPL-1',
    'summary': 'This thrive apps helps user to easily create new task with deadline and project name directly from lead.',
    'description': """
    Task on Lead, Add Task from lead, Task Lead, Create Project Task from Lead, Add task from mail, Create task from mail.Task on lead, add task on lead, tasks on lead, lead tasks, automated task by lead, Generate task from lead.
""",
    'author': 'BROWSEINFO',
    'website': 'https://www.browseinfo.com/demo-request?app=bi_crm_task&version=19&edition=Community',
    'depends': ['base', 'crm', 'sale', 'project'],
    'data': [
            'security/ir.model.access.csv',
            'views/crm_lead_view.xml'
            ],
    'installable': True,
    'auto_install': False,
    'application': True,
    'live_test_url':'https://www.browseinfo.com/demo-request?app=bi_crm_task&version=19&edition=Community',
    "images":['static/description/Banner.gif'],
}
