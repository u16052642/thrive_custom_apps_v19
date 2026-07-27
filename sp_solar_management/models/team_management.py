# -- encoding: utf-8 --
###############################################################################
#
# Copyright (C) 2022-Present Speeduplight (https://speeduplight.com/)
#
###############################################################################
from thrive import fields, models


class SolarSurveyTeam(models.Model):
    _name = 'solar.survey.team'
    _description = 'Solar Survey Team'
    _order = 'name'

    name = fields.Char(string='Team Name', required=True)
    team_project = fields.Char(string='Team Project')
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
    )
    manager_id = fields.Many2one('res.users', string='Project Manager')
    member_ids = fields.Many2many('res.users', string='Team Members')


class SolarInstallationTeam(models.Model):
    _name = 'solar.installation.team'
    _description = 'Solar Installation Team'
    _order = 'name'

    name = fields.Char(string='Team Name', required=True)
    team_project = fields.Char(string='Team Project')
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
    )
    manager_id = fields.Many2one('res.users', string='Project Manager')
    coordinator_id = fields.Many2one('res.users', string='Coordinator')
    team_leader_id = fields.Many2one('res.users', string='Team Leader')
    engineer_ids = fields.Many2many('res.users', string='Engineers')
    technician_count = fields.Integer(string='Technician Count')


class SolarQATeam(models.Model):
    _name = 'solar.qa.team'
    _description = 'Solar QA Team'
    _order = 'name'

    name = fields.Char(string='Team Name', required=True)
    team_project = fields.Char(string='Team Project')
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
    )
    manager_id = fields.Many2one('res.users', string='Project Manager')
    member_ids = fields.Many2many('res.users', string='Team Members')
