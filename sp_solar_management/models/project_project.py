# -- encoding: utf-8 --
###############################################################################
#
# Copyright (C) 2022-Present Speeduplight (https://speeduplight.com/)
#
###############################################################################
from thrive import models, fields, api

class ProjectProject(models.Model):
    _inherit = 'project.project'

    project_reference = fields.Char(
        string='Project ID',
        copy=False,
        readonly=True,
        index=True,
        default='New',
    )

    _project_reference_unique = models.Constraint(
        'UNIQUE(project_reference)',
        'Project ID must be unique.'
    )

    lead_id = fields.Many2one(
        'crm.lead',
        string='Lead/Opportunity',
        help="The CRM lead associated with this project."
    )

    # Related fields from Lead for Solar Requirements
    renewable_service_type = fields.Selection(
        related='lead_id.renewable_service_type',
        readonly=False,
    )
    renewable_solar_company_id = fields.Many2one(
        'solar.company',
        related='lead_id.renewable_solar_company_id',
        readonly=False,
    )
    renewable_contract_demand_kw = fields.Float(
        related='lead_id.renewable_contract_demand_kw',
        readonly=False,
    )
    renewable_connection_type = fields.Selection(
        related='lead_id.renewable_connection_type',
        readonly=False,
    )
    renewable_existing_connection = fields.Selection(
        related='lead_id.renewable_existing_connection',
        readonly=False,
    )
    renewable_existing_supply_volts = fields.Float(
        related='lead_id.renewable_existing_supply_volts',
        readonly=False,
    )
    renewable_consumer_no = fields.Char(
        related='lead_id.renewable_consumer_no',
        readonly=False,
    )
    company_currency = fields.Many2one(
        'res.currency',
        string='Currency',
        related='company_id.currency_id',
        readonly=True,
    )
    renewable_monthly_electric_bill = fields.Monetary(
        related='lead_id.renewable_monthly_electric_bill',
        currency_field='company_currency',
        readonly=False,
    )
    renewable_monthly_electricity_consumption = fields.Float(
        related='lead_id.renewable_monthly_electricity_consumption',
        readonly=False,
    )
    renewable_roof_type = fields.Selection(
        related='lead_id.renewable_roof_type',
        readonly=False,
    )
    renewable_roof_area_sqft = fields.Float(
        related='lead_id.renewable_roof_area_sqft',
        readonly=False,
    )
    renewable_site_usage = fields.Selection(
        related='lead_id.renewable_site_usage',
        readonly=False,
    )
    renewable_property_type = fields.Selection(
        related='lead_id.renewable_property_type',
        readonly=False,
    )
    renewable_property_age_years = fields.Integer(
        related='lead_id.renewable_property_age_years',
        readonly=False,
    )
    renewable_site_street = fields.Char(
        related='lead_id.renewable_site_street',
        readonly=False,
    )
    renewable_site_street2 = fields.Char(
        related='lead_id.renewable_site_street2',
        readonly=False,
    )
    renewable_site_city = fields.Char(
        related='lead_id.renewable_site_city',
        readonly=False,
    )
    renewable_site_state_id = fields.Many2one(
        'res.country.state',
        related='lead_id.renewable_site_state_id',
        readonly=False,
    )
    renewable_site_zip = fields.Char(
        related='lead_id.renewable_site_zip',
        readonly=False,
    )
    renewable_site_country_id = fields.Many2one(
        'res.country',
        related='lead_id.renewable_site_country_id',
        readonly=False,
    )
    renewable_site_latitude = fields.Float(
        related='lead_id.renewable_site_latitude',
        readonly=False,
    )
    renewable_site_longitude = fields.Float(
        related='lead_id.renewable_site_longitude',
        readonly=False,
    )

    sseg_application_number = fields.Char(
        string='SSEG Application Number',
        compute='_compute_sseg_application_number',
    )

    lead_count = fields.Integer(
        string='Lead',
        compute='_compute_lead_count',
    )

    inspection_count = fields.Integer(
        string='Site Inspections',
        compute='_compute_inspection_count',
    )

    design_count = fields.Integer(
        string='Designs',
        compute='_compute_design_count',
    )

    government_approval_count = fields.Integer(
        string='SSEG Applications',
        compute='_compute_government_approval_count',
    )

    installation_count = fields.Integer(
        string='Installations',
        compute='_compute_installation_count',
    )

    contract_count = fields.Integer(
        string='Contracts',
        compute='_compute_contract_count',
    )

    document_count = fields.Integer(
        string='Documents',
        compute='_compute_document_count',
    )

    maintenance_count = fields.Integer(
        string='Maintenance Requests',
        compute='_compute_maintenance_count',
    )


    @api.depends('lead_id')
    def _compute_lead_count(self):
        for project in self:
            project.lead_count = 1 if project.lead_id else 0

    @api.depends('lead_id')
    def _compute_inspection_count(self):
        for project in self:
            domain = []
            if project.lead_id:
                domain = ['|', ('project_id', '=', project.id), ('lead_id', '=', project.lead_id.id)]
            else:
                domain = [('project_id', '=', project.id)]
            project.inspection_count = self.env['solar.site.inspection'].search_count(domain)

    @api.depends('lead_id')
    def _compute_design_count(self):
        for project in self:
            if project.lead_id:
                project.design_count = self.env['solar.design'].search_count([('lead_id', '=', project.lead_id.id)])
            else:
                project.design_count = 0

    @api.depends('lead_id')
    def _compute_government_approval_count(self):
        for project in self:
            if project.lead_id:
                project.government_approval_count = self.env['solar.government.approval'].search_count([('lead_id', '=', project.lead_id.id)])
            else:
                project.government_approval_count = 0

    @api.depends('lead_id')
    def _compute_installation_count(self):
        for project in self:
            domain = []
            if project.lead_id:
                domain = ['|', ('project_id', '=', project.id), ('lead_id', '=', project.lead_id.id)]
            else:
                domain = [('project_id', '=', project.id)]
            project.installation_count = self.env['solar.installation'].search_count(domain)

    @api.depends('lead_id')
    def _compute_contract_count(self):
        for project in self:
            if project.lead_id:
                project.contract_count = self.env['solar.contract'].search_count([('lead_id', '=', project.lead_id.id)])
            else:
                project.contract_count = 0

    @api.depends('lead_id')
    def _compute_document_count(self):
        for project in self:
            domain = []
            if project.lead_id:
                domain = ['|', ('installation_id.project_id', '=', project.id), ('installation_id.lead_id', '=', project.lead_id.id)]
            else:
                domain = [('installation_id.project_id', '=', project.id)]
            project.document_count = self.env['solar.installation.document'].search_count(domain)

    @api.depends('lead_id')
    def _compute_maintenance_count(self):
        for project in self:
            domain = []
            if project.lead_id:
                domain = ['|', ('project_id', '=', project.id), ('installation_id.lead_id', '=', project.lead_id.id)]
            else:
                domain = [('project_id', '=', project.id)]
            project.maintenance_count = self.env['maintenance.request'].search_count(domain)


    solar_stage = fields.Selection(
        [
            ('document_pending', 'Document Pending'),
            ('application_submitted', 'Application Submitted'),
            ('site_survey_scheduled', 'Site Survey Scheduled'),
            ('site_survey_completed', 'Site Survey Completed'),
            ('design_approved', 'Design Approved'),
            ('government_approval', 'SSEG Application'),
            ('installation_in_progress', 'Installation in Progress'),
            ('inspection_testing', 'Inspection & Testing'),
            ('system_activated', 'System Activated'),
        ],
        string='Project Progress',
        compute='_compute_solar_stage',
        store=True,
        default='document_pending',
        tracking=True,
        help="The current stage/process of the solar project."
    )

    @api.depends('lead_id.solar_stage')
    def _compute_solar_stage(self):
        for project in self:
            if project.lead_id:
                project.solar_stage = project.lead_id.solar_stage
            elif not project.solar_stage:
                project.solar_stage = 'document_pending'

    def _compute_sseg_application_number(self):
        for project in self:
            if project.lead_id:
                approval = self.env['solar.government.approval'].search([
                    ('lead_id', '=', project.lead_id.id)
                ], limit=1)
                project.sseg_application_number = approval.application_number if approval else False
            else:
                project.sseg_application_number = False

    @api.depends('project_reference', 'name')
    def _compute_display_name(self):
        for project in self:
            if project.project_reference and project.project_reference != 'New':
                project.display_name = f"[{project.project_reference}] {project.name}"
            else:
                project.display_name = project.name

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('project_reference') or vals.get('project_reference') == 'New':
                vals['project_reference'] = self.env['ir.sequence'].next_by_code('project.project.solar') or 'New'
        return super().create(vals_list)

    def action_view_lead(self):
        self.ensure_one()
        if not self.lead_id:
            return {}
        view_id = self.env.ref('crm.crm_lead_view_form').id
        action_name = 'Opportunity' if self.lead_id.type == 'opportunity' else 'Lead'
        return {
            'name': action_name,
            'type': 'ir.actions.act_window',
            'res_model': 'crm.lead',
            'view_mode': 'form',
            'view_id': view_id,
            'res_id': self.lead_id.id,
            'target': 'current',
        }

    def action_view_site_inspections(self):
        self.ensure_one()
        return {
            'name': 'Site Inspections',
            'type': 'ir.actions.act_window',
            'res_model': 'solar.site.inspection',
            'view_mode': 'list,form',
            'domain': [('project_id', '=', self.id)] if not self.lead_id else ['|', ('project_id', '=', self.id), ('lead_id', '=', self.lead_id.id)],
            'context': {
                'default_project_id': self.id,
                'default_lead_id': self.lead_id.id if self.lead_id else False,
                'default_partner_id': self.partner_id.id if self.partner_id else False,
            },
        }

    def action_view_designs(self):
        self.ensure_one()
        return {
            'name': 'Solar Designs',
            'type': 'ir.actions.act_window',
            'res_model': 'solar.design',
            'view_mode': 'list,form',
            'domain': [('lead_id', '=', self.lead_id.id)] if self.lead_id else [('id', '=', 0)],
            'context': {
                'default_lead_id': self.lead_id.id if self.lead_id else False,
                'default_partner_id': self.partner_id.id if self.partner_id else False,
            },
        }

    def action_view_government_approval(self):
        self.ensure_one()
        approval = self.env['solar.government.approval'].search([
            ('lead_id', '=', self.lead_id.id),
        ], limit=1) if self.lead_id else False
        action = {
            'name': 'SSEG Application',
            'type': 'ir.actions.act_window',
            'res_model': 'solar.government.approval',
            'view_mode': 'list,form',
            'domain': [('lead_id', '=', self.lead_id.id)] if self.lead_id else [('id', '=', 0)],
            'context': {
                'default_lead_id': self.lead_id.id if self.lead_id else False,
            },
        }
        if approval:
            action.update({
                'view_mode': 'form',
                'res_id': approval.id,
            })
        return action

    def action_view_installations(self):
        self.ensure_one()
        return {
            'name': 'Installations',
            'type': 'ir.actions.act_window',
            'res_model': 'solar.installation',
            'view_mode': 'list,form',
            'domain': [('project_id', '=', self.id)] if not self.lead_id else ['|', ('project_id', '=', self.id), ('lead_id', '=', self.lead_id.id)],
            'context': {
                'default_project_id': self.id,
                'default_lead_id': self.lead_id.id if self.lead_id else False,
                'default_project_manager_id': self.env.user.id,
            },
        }

    def action_view_contracts(self):
        self.ensure_one()
        return {
            'name': 'Contracts',
            'type': 'ir.actions.act_window',
            'res_model': 'solar.contract',
            'view_mode': 'list,form',
            'domain': [('lead_id', '=', self.lead_id.id)] if self.lead_id else [('id', '=', 0)],
            'context': {
                'default_lead_id': self.lead_id.id if self.lead_id else False,
            },
        }

    def action_view_documents(self):
        self.ensure_one()
        domain = [('installation_id.project_id', '=', self.id)] if not self.lead_id else ['|', ('installation_id.project_id', '=', self.id), ('installation_id.lead_id', '=', self.lead_id.id)]
        installation = self.env['solar.installation'].search([
            '|', ('project_id', '=', self.id), ('lead_id', '=', self.lead_id.id)
        ], limit=1) if self.lead_id or self.id else False
        return {
            'name': 'Documents',
            'type': 'ir.actions.act_window',
            'res_model': 'solar.installation.document',
            'view_mode': 'list,form',
            'domain': domain,
            'context': {
                'default_installation_id': installation.id if installation else False,
            },
        }

    def action_view_maintenance(self):
        self.ensure_one()
        domain = [('project_id', '=', self.id)] if not self.lead_id else ['|', ('project_id', '=', self.id), ('installation_id.lead_id', '=', self.lead_id.id)]
        installation = self.env['solar.installation'].search([
            '|', ('project_id', '=', self.id), ('lead_id', '=', self.lead_id.id)
        ], limit=1) if self.lead_id or self.id else False
        return {
            'name': 'Maintenance Requests',
            'type': 'ir.actions.act_window',
            'res_model': 'maintenance.request',
            'view_mode': 'list,form',
            'domain': domain,
            'context': {
                'default_project_id': self.id,
                'default_installation_id': installation.id if installation else False,
                'default_partner_id': self.partner_id.id if self.partner_id else False,
            },
        }

