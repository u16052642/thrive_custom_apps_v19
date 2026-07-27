# -- encoding: utf-8 --
###############################################################################
#
# Copyright (C) 2022-Present Speeduplight (https://speeduplight.com/)
#
###############################################################################
from thrive import api, fields, models


class SolarSiteInspectionWizard(models.TransientModel):
    _name = 'solar.site.inspection.wizard'
    _description = 'Create Site Inspection Wizard'

    lead_id = fields.Many2one('crm.lead', string='Lead', required=True, readonly=True)
    inspection_type = fields.Selection([
        ('on_site', 'On-site'),
        ('remote', 'Remote')
    ], string='Inspection Type', default='on_site', required=True)
    survey_team_id = fields.Many2one('solar.survey.team', string='Survey Team', required=False)
    survey_manager_id = fields.Many2one('res.users', string='Manager', related='survey_team_id.manager_id', readonly=True)
    survey_team_member_ids = fields.Many2many(
        'res.users',
        string='Available Survey Members',
        related='survey_team_id.member_ids',
        readonly=True,
    )
    survey_member_id = fields.Many2one(
        'res.users',
        string='Survey Member',
    )
    survey_member_domain = fields.Char(compute='_compute_survey_member_domain', readonly=True)
    google_earth_url = fields.Char(string='Google Earth Link', compute='_compute_google_earth_url')
    inspection_date = fields.Date(string='Date of Inspection', default=fields.Date.context_today, required=True)

    @api.depends('inspection_type', 'survey_team_member_ids')
    def _compute_survey_member_domain(self):
        for rec in self:
            if rec.inspection_type == 'remote':
                group_tech = self.env.ref('sp_solar_management.group_solar_technician')
                rec.survey_member_domain = str([('id', 'in', group_tech.all_user_ids.ids)])
            else:
                rec.survey_member_domain = str([('id', 'in', rec.survey_team_member_ids.ids)])

    @api.depends('inspection_type', 'lead_id')
    def _compute_google_earth_url(self):
        for rec in self:
            if rec.inspection_type == 'remote' and rec.lead_id:
                lead = rec.lead_id
                lat = lead.renewable_site_latitude
                lng = lead.renewable_site_longitude
                if lat and lng:
                    rec.google_earth_url = f"https://earth.google.com/web/@{lat},{lng},150a,0d,35y,0h,0t,0r"
                else:
                    address_parts = [
                        lead.renewable_site_street,
                        lead.renewable_site_street2,
                        lead.renewable_site_city,
                        lead.renewable_site_state_id.name if lead.renewable_site_state_id else False,
                        lead.renewable_site_country_id.name if lead.renewable_site_country_id else False,
                    ]
                    address = ", ".join(part for part in address_parts if part)
                    if address:
                        import urllib.parse
                        encoded_address = urllib.parse.quote(address)
                        rec.google_earth_url = f"https://earth.google.com/web/search/{encoded_address}"
                    else:
                        rec.google_earth_url = False
            else:
                rec.google_earth_url = False

    @api.onchange('survey_team_id')
    def _onchange_survey_team_id(self):
        for rec in self:
            if rec.inspection_type != 'remote':
                if rec.survey_member_id and rec.survey_member_id not in rec.survey_team_member_ids:
                    rec.survey_member_id = False

    def action_create_site_inspection(self):
        self.ensure_one()
        lead = self.lead_id.sudo()
        lead._validate_required_documents_for_inspection()
        inspection = self.env['solar.site.inspection'].search(
            [('lead_id', '=', self.lead_id.id)],
            limit=1,
            order='id desc',
        )
        vals = {
            'lead_id': self.lead_id.id,
            'company_id': self.lead_id.company_id.id or self.env.company.id,
            'inspection_date': self.inspection_date,
            'survey_team_id': self.survey_team_id.id if self.inspection_type == 'on_site' else False,
            'survey_member_id': self.survey_member_id.id,
            'inspection_type': self.inspection_type,
        }
        if not inspection:
            inspection = self.env['solar.site.inspection'].create(vals)
        else:
            inspection.write(vals)
            lead._set_solar_crm_stage_proposition()
        return {
            'name': 'Site Inspection',
            'type': 'ir.actions.act_window',
            'res_model': 'solar.site.inspection',
            'view_mode': 'form',
            'res_id': inspection.id,
            'target': 'current',
        }
