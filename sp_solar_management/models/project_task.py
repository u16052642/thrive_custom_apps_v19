# -- encoding: utf-8 --
###############################################################################
#
# Copyright (C) 2022-Present Speeduplight (https://speeduplight.com/)
#
###############################################################################
from thrive import fields, models


class ProjectTask(models.Model):
    _inherit = 'project.task'

    lead_id = fields.Many2one('crm.lead', string='Lead')
    installation_id = fields.Many2one('solar.installation', string='Installation')

    team_type = fields.Selection(
        [
            ('survey', 'Survey Team'),
            ('installation', 'Installation Team'),
            ('qa', 'QA Team'),
        ],
        string='Team Type',
        tracking=True,
    )
    site_inspection_id = fields.Many2one(
        'solar.site.inspection',
        string='Site Inspection',
        ondelete='set null',
    )
    survey_team_id = fields.Many2one(
        'solar.survey.team',
        string='Survey Team',
        ondelete='set null',
    )
    site_customer_id = fields.Many2one(
        'res.partner',
        string='Customer',
        related='site_inspection_id.partner_id',
        readonly=True,
    )
    site_customer_phone = fields.Char(
        string='Phone',
        related='site_inspection_id.customer_phone',
        readonly=True,
    )
    site_customer_email = fields.Char(
        string='Email',
        related='site_inspection_id.customer_email',
        readonly=True,
    )
    site_street = fields.Char(
        string='Street',
        related='site_inspection_id.site_street',
        readonly=True,
    )
    site_street2 = fields.Char(
        string='Street 2',
        related='site_inspection_id.site_street2',
        readonly=True,
    )
    site_city = fields.Char(
        string='City',
        related='site_inspection_id.site_city',
        readonly=True,
    )
    site_state_id = fields.Many2one(
        'res.country.state',
        string='State',
        related='site_inspection_id.site_state_id',
        readonly=True,
    )
    site_zip = fields.Char(
        string='ZIP',
        related='site_inspection_id.site_zip',
        readonly=True,
    )
    site_country_id = fields.Many2one(
        'res.country',
        string='Country',
        related='site_inspection_id.site_country_id',
        readonly=True,
    )
