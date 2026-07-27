# -- encoding: utf-8 --
###############################################################################
#
# Copyright (C) 2022-Present Speeduplight (https://speeduplight.com/)
#
###############################################################################
import base64

from thrive import _, api, fields, models
from thrive.exceptions import AccessError, ValidationError


class SolarSiteInspection(models.Model):
    _name = 'solar.site.inspection'
    _description = 'Solar Site Inspection'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'inspection_date desc, id desc'

    # ── computed role flags (used for invisible= in views) ──────────────────
    user_is_admin = fields.Boolean(compute='_compute_user_roles')
    user_is_sales = fields.Boolean(compute='_compute_user_roles')
    user_is_tech = fields.Boolean(compute='_compute_user_roles')
    user_is_pm = fields.Boolean(compute='_compute_user_roles')
    user_is_finance = fields.Boolean(compute='_compute_user_roles')
    user_is_office = fields.Boolean(compute='_compute_user_roles')

    def _compute_user_roles(self):
        is_admin = self.env.user.has_group('sp_solar_management.group_solar_manager')
        is_sales = self.env.user.has_group('sp_solar_management.group_solar_sales')
        is_tech = self.env.user.has_group('sp_solar_management.group_solar_technician')
        is_pm = self.env.user.has_group('sp_solar_management.group_solar_project_manager')
        is_finance = self.env.user.has_group('sp_solar_management.group_solar_finance')
        is_office = self.env.user.has_group('sp_solar_management.group_solar_office_manager')
        for rec in self:
            rec.user_is_admin = is_admin
            rec.user_is_sales = is_sales or is_admin
            rec.user_is_tech = is_tech or is_admin
            rec.user_is_pm = is_pm or is_admin
            rec.user_is_finance = is_finance or is_admin
            rec.user_is_office = is_office or is_admin
    # ────────────────────────────────────────────────────────────────────────

    name = fields.Char(string='Inspection Reference', required=True, copy=False, default='New')
    lead_id = fields.Many2one('crm.lead', string='Lead', required=True, ondelete='cascade')
    partner_id = fields.Many2one('res.partner', string='Customer', related='lead_id.partner_id', store=True, readonly=True)
    customer_name = fields.Char(string='Customer', compute='_compute_customer_contact_details', readonly=True)
    customer_email = fields.Char(string='Email', compute='_compute_customer_contact_details', readonly=True)
    customer_phone = fields.Char(string='Phone', compute='_compute_customer_contact_details', readonly=True)
    salesperson_id = fields.Many2one('res.users', string='Salesperson', related='lead_id.user_id', store=True, readonly=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Currency', readonly=True)
    state = fields.Selection([
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='new', tracking=True)
    inspection_date = fields.Date(string='Date of Inspection', default=fields.Date.context_today)
    inspection_type = fields.Selection([
        ('on_site', 'On-site'),
        ('remote', 'Remote')
    ], string='Inspection Type', default='on_site', required=True)
    project_id = fields.Many2one('project.project', string='Project')
    project_count = fields.Integer(compute='_compute_project_count', string='Project Count')
    survey_team_id = fields.Many2one('solar.survey.team', string='Survey Team')
    survey_manager_id = fields.Many2one('res.users', string='Manager', related='survey_team_id.manager_id', store=True, readonly=True)
    survey_member_id = fields.Many2one('res.users', string='Survey Member')
    survey_member_domain = fields.Char(compute='_compute_survey_member_domain', readonly=True)
    google_earth_url = fields.Char(string='Google Earth Link', compute='_compute_google_earth_url')
    survey_team_member_ids = fields.Many2many('res.users', string='Available Survey Members', related='survey_team_id.member_ids', readonly=True)
    survey_task_id = fields.Many2one('project.task', string='Survey Task', readonly=True, copy=False)
    service_type = fields.Selection(related='lead_id.renewable_service_type', string='Service Type', store=True, readonly=True)
    connection_type = fields.Selection(related='lead_id.renewable_connection_type', string='Connection Type', store=True, readonly=True)
    customer_category = fields.Selection(related='lead_id.renewable_site_usage', string='Customer Category', store=True, readonly=True)
    contract_demand_kw = fields.Float(related='lead_id.renewable_contract_demand_kw', string='Contract Demand (kW)', store=True, readonly=True)
    consumer_no = fields.Char(related='lead_id.renewable_consumer_no', string='Consumer No', store=True, readonly=True)
    monthly_electric_bill = fields.Monetary(related='lead_id.renewable_monthly_electric_bill', string='Monthly Electric Bill', currency_field='currency_id', store=True, readonly=True)
    monthly_electricity_consumption = fields.Float(related='lead_id.renewable_monthly_electricity_consumption', string='Monthly Electricity Consumption (kWh)', store=True, readonly=True)
    existing_connection = fields.Selection(related='lead_id.renewable_existing_connection', string='Existing Connection', store=True, readonly=True)
    existing_supply_volts = fields.Float(related='lead_id.renewable_existing_supply_volts', string='Existing Supply Volts', store=True, readonly=True)
    property_type = fields.Selection(related='lead_id.renewable_property_type', string='Type of Property', store=True, readonly=True)
    property_age_years = fields.Integer(related='lead_id.renewable_property_age_years', string='Age of Property (Years)', store=True, readonly=True)
    roof_type = fields.Selection(related='lead_id.renewable_roof_type', string='Roof Type', store=True, readonly=True)
    roof_area_sqft = fields.Float(related='lead_id.renewable_roof_area_sqft', string='Roof Area (Sq. Ft.)', store=True, readonly=True)
    site_street = fields.Char(related='lead_id.renewable_site_street', string='Street', store=True, readonly=True)
    site_street2 = fields.Char(related='lead_id.renewable_site_street2', string='Street 2', store=True, readonly=True)
    site_city = fields.Char(related='lead_id.renewable_site_city', string='City', store=True, readonly=True)
    site_state_id = fields.Many2one('res.country.state', related='lead_id.renewable_site_state_id', string='State', store=True, readonly=True)
    site_zip = fields.Char(related='lead_id.renewable_site_zip', string='ZIP', store=True, readonly=True)
    site_country_id = fields.Many2one('res.country', related='lead_id.renewable_site_country_id', string='Country', store=True, readonly=True)
    site_latitude = fields.Float(related='lead_id.renewable_site_latitude', string='Latitude', digits=(16, 6), store=True, readonly=True)
    site_longitude = fields.Float(related='lead_id.renewable_site_longitude', string='Longitude', digits=(16, 6), store=True, readonly=True)
    site_remarks = fields.Text(string='Site Remarks')
    site_checklist = fields.Text(string='Site Checklist')
    max_installable_capacity_kw = fields.Float(string='Max Installable Capacity (kW)')
    recommended_system_size_kw = fields.Float(string='Recommended System Size (kW)')
    expected_generation_kwh_month = fields.Float(string='Expected Generation (kWh/month)')
    system_type = fields.Selection([('on_grid', 'On-Grid'), ('off_grid', 'Off-Grid'), ('hybrid', 'Hybrid')], string='System Type')
    installation_feasible = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Installation Feasible')
    feasibility_reason = fields.Selection([
        ('roof_weak', 'Roof weak'),
        ('shadow_issue', 'Shadow issue'),
        ('space_insufficient', 'Space insufficient'),
        ('electrical_limitation', 'Electrical limitation'),
        ('other', 'Other'),
    ], string='If No, Reason')
    shadow_present = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Shadow Present')
    shadow_percentage = fields.Float(string='Shadow Percentage (%)')
    obstruction_type = fields.Selection([('tree', 'Tree'), ('building', 'Building'), ('water_tank', 'Water Tank'), ('other', 'Other')], string='Obstruction Type')
    orientation = fields.Selection([('north', 'North'), ('south', 'South'), ('east', 'East'), ('west', 'West')], string='Orientation')
    peak_load_kw = fields.Float(string='Current Peak Load (kW)')
    backup_requirement = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Backup Requirement')
    battery_required = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Battery Required')
    dg_integration = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='DG Integration')
    roof_load_capacity_ok = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Roof Load Capacity OK')
    structure_reinforcement_required = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Structure Reinforcement Required')
    mounting_structure_type = fields.Selection([('fixed_tilt', 'Fixed Tilt'), ('elevated', 'Elevated'), ('tracking', 'Tracking')], string='Mounting Structure Type')
    estimated_project_cost = fields.Monetary(string='Estimated Project Cost', currency_field='currency_id')
    payback_period_years = fields.Float(string='Payback Period (Years)')
    installation_risk_level = fields.Selection([('low', 'Low'), ('medium', 'Medium'), ('high', 'High')], string='Installation Risk Level')
    safety_notes = fields.Text(string='Safety Notes')
    electricity_bill_pdf = fields.Binary(string='Electricity Bill PDF', attachment=True)
    electricity_bill_pdf_filename = fields.Char(string='Electricity Bill PDF Filename')
    site_layout_plan = fields.Binary(string='Site Layout Plan', attachment=True)
    site_layout_plan_filename = fields.Char(string='Site Layout Plan Filename')
    government_approval_docs = fields.Binary(string='SSEG Application Docs', attachment=True)
    government_approval_docs_filename = fields.Char(string='SSEG Application Docs Filename')
    approved_by_id = fields.Many2one('res.users', string='Approved By', readonly=True, copy=False, ondelete='set null')
    approved_date = fields.Datetime(string='Approved Date', readonly=True, copy=False)
    rejected_by_id = fields.Many2one('res.users', string='Rejected By', readonly=True, copy=False, ondelete='set null')
    rejected_date = fields.Datetime(string='Rejected Date', readonly=True, copy=False)
    rejection_reason = fields.Text(string='Rejection Reason')
    image_ids = fields.One2many('solar.site.inspection.image', 'inspection_id', string='Site Survey Images')
    checklist_line_ids = fields.One2many('solar.site.inspection.checklist', 'inspection_id', string='Site Checklist')
    google_map_url = fields.Char(string='Google Map Link', compute='_compute_google_map_url')
    portal_submission_date = fields.Datetime(string='Submission Date', readonly=True, copy=False)
    portal_submitted_by_id = fields.Many2one('res.users', string='Submitted By', readonly=True, copy=False, ondelete='set null')
    design_count = fields.Integer(compute='_compute_design_count', string='Design Count')

    def _compute_design_count(self):
        for rec in self:
            rec.design_count = self.env['solar.design'].search_count([('inspection_id', '=', rec.id)])

    @api.depends('project_id')
    def _compute_project_count(self):
        for rec in self:
            rec.project_count = 1 if rec.project_id else 0

    def action_view_project(self):
        self.ensure_one()
        if not self.project_id:
            self.project_id = self.lead_id.project_id or self._get_default_survey_project()
        if self.project_id:
            return {
                'name': _('Project'),
                'type': 'ir.actions.act_window',
                'res_model': 'project.project',
                'view_mode': 'form',
                'res_id': self.project_id.id,
                'target': 'current',
            }
        return {}

    @api.depends('lead_id.contact_name', 'lead_id.email_from', 'lead_id.phone', 'partner_id.name', 'partner_id.email', 'partner_id.phone')
    def _compute_customer_contact_details(self):
        for rec in self:
            rec.customer_name = rec.lead_id.contact_name or rec.partner_id.name or False
            rec.customer_email = rec.lead_id.email_from or rec.partner_id.email or False
            rec.customer_phone = rec.lead_id.phone or rec.partner_id.phone or False

    @api.depends('site_latitude', 'site_longitude')
    def _compute_google_map_url(self):
        for rec in self:
            rec.google_map_url = f"https://www.google.com/maps?q={rec.site_latitude},{rec.site_longitude}" if rec.site_latitude and rec.site_longitude else False

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

    def _get_max_installable_capacity_kw(self, roof_area_sqft):
        return round((roof_area_sqft or 0.0) / 100.0, 2)

    def _get_bill_based_capacity_kw(self, monthly_electric_bill):
        return round((monthly_electric_bill or 0.0) / 500.0, 2)

    def _get_expected_generation_kwh_month(self, recommended_system_size_kw):
        return round((recommended_system_size_kw or 0.0) * 120.0, 2)

    def _get_recommendation_values(self, vals=None):
        self.ensure_one()
        vals = vals or {}
        roof_area_sqft = vals.get('roof_area_sqft', self.roof_area_sqft)
        monthly_electric_bill = vals.get('monthly_electric_bill', self.monthly_electric_bill)
        contract_demand_kw = vals.get('contract_demand_kw', self.contract_demand_kw)
        max_installable_capacity_kw = self._get_max_installable_capacity_kw(roof_area_sqft)
        bill_based_capacity_kw = self._get_bill_based_capacity_kw(monthly_electric_bill)
        recommended_system_size_kw = max(contract_demand_kw or 0.0, bill_based_capacity_kw)
        if not recommended_system_size_kw:
            recommended_system_size_kw = max_installable_capacity_kw
        elif max_installable_capacity_kw:
            recommended_system_size_kw = min(recommended_system_size_kw, max_installable_capacity_kw)
        return {
            'max_installable_capacity_kw': max_installable_capacity_kw,
            'recommended_system_size_kw': recommended_system_size_kw,
        }

    def _sync_recommendation_values(self):
        for rec in self:
            recommendation_vals = rec._get_recommendation_values()
            if any(rec[field] != value for field, value in recommendation_vals.items()):
                super(SolarSiteInspection, rec.with_context(skip_recommendation_sync=True)).write(recommendation_vals)

    def _sync_task_stage(self, task, inspection_state=None):
        self.ensure_one()
        inspection_state = inspection_state or self.state
        stage_model = self.env['project.task.type'].sudo()
        if inspection_state == 'new':
            stage_name = 'New'
        elif inspection_state == 'in_progress':
            stage_name = 'In Progress'
        elif inspection_state == 'cancelled':
            stage_name = 'Cancelled'
        else:
            stage_name = 'Done'
        stage = stage_model.search([('name', '=', stage_name)], limit=1)
        if not stage:
            stage = stage_model.create({'name': stage_name})
        if task:
            project = task.project_id
            if project and project.id not in stage.project_ids.ids:
                stage.write({'project_ids': [(4, project.id)]})
            task_sudo = task.sudo()
            if task_sudo.stage_id != stage:
                task_sudo.stage_id = stage.id

    def action_start(self):
        for inspection in self:
            inspection._sync_survey_task()
            inspection.state = 'in_progress'
            if inspection.survey_task_id:
                inspection._sync_task_stage(inspection.survey_task_id, inspection.state)

    def action_complete(self):
        self.action_submit_for_approval()

    def action_submit_for_approval(self):
        for inspection in self:
            vals = {
                'state': 'submitted',
                'portal_submission_date': inspection.portal_submission_date or fields.Datetime.now(),
                'portal_submitted_by_id': inspection.portal_submitted_by_id.id or self.env.user.id,
                'approved_by_id': False,
                'approved_date': False,
                'rejected_by_id': False,
                'rejected_date': False,
                'rejection_reason': False,
            }
            inspection.write(vals)
            if inspection.survey_task_id:
                inspection._sync_task_stage(inspection.survey_task_id, inspection.state)

    def action_approve(self):
        for inspection in self:
            inspection.write({'state': 'approved', 'approved_by_id': self.env.user.id, 'approved_date': fields.Datetime.now()})
            if inspection.lead_id and inspection.lead_id.sudo().solar_stage == 'site_survey_scheduled':
                inspection.lead_id.sudo().write({'solar_stage': 'site_survey_completed'})
            if inspection.survey_task_id:
                inspection._sync_task_stage(inspection.survey_task_id, inspection.state)

    def action_create_design(self):
        self.ensure_one()
        if self.state != 'approved':
            raise ValidationError(_('You can create a design only after approving the site inspection.'))
        design = self.env['solar.design'].search([
            ('inspection_id', '=', self.id),
        ], limit=1, order='id desc')
        if not design:
            design = self.env['solar.design'].create({
                'lead_id': self.lead_id.id,
                'inspection_id': self.id,
                'company_id': self.company_id.id,
            })
        return {
            'name': _('Solar Design'),
            'type': 'ir.actions.act_window',
            'res_model': 'solar.design',
            'view_mode': 'form',
            'res_id': design.id,
            'target': 'current',
        }

    def action_view_design(self):
        self.ensure_one()
        return {
            'name': _('Solar Design'),
            'type': 'ir.actions.act_window',
            'res_model': 'solar.design',
            'view_mode': 'list,form',
            'domain': [('inspection_id', '=', self.id)],
            'target': 'current',
        }

    def action_open_reject_wizard(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Reject Inspection',
            'res_model': 'solar.site.inspection.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_inspection_id': self.id},
        }

    def action_reject(self):
        for inspection in self:
            if not inspection.rejection_reason:
                raise ValidationError('Please enter a rejection reason before rejecting the inspection.')
            inspection.write({'state': 'rejected', 'rejected_by_id': self.env.user.id, 'rejected_date': fields.Datetime.now()})
            if inspection.survey_task_id:
                inspection._sync_task_stage(inspection.survey_task_id, inspection.state)

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_open_google_map(self):
        self.ensure_one()
        if not self.google_map_url:
            raise ValidationError(_('No Google Map URL is available for this inspection.'))
        return {'type': 'ir.actions.act_url', 'url': self.google_map_url, 'target': 'new'}

    def action_send_mail(self):
        self.ensure_one()
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        portal_link = f"{base_url}/my/inspections/{self.id}"
        
        body = _(
            "Hello,<br/><br/>"
            "Please find the link to the Solar Site Inspection form for <strong>{name}</strong> below:<br/><br/>"
            "<div style='margin: 16px 0;'>"
            "  <a href='{link}' style='background-color:#875A7B;padding:10px 18px;text-decoration:none;color:#fff;border-radius:5px;font-weight:bold;'>View Site Inspection</a>"
            "</div>"
            "You can use this link to fill in the site details, upload survey images, and submit the inspection report.<br/><br/>"
            "Thank you."
        ).format(name=self.name, link=portal_link)
        
        ctx = {
            'default_model': 'solar.site.inspection',
            'default_res_ids': [self.id],
            'default_body': body,
            'default_subject': _('Solar Site Inspection Reference: %s') % self.name,
            'default_partner_ids': [self.partner_id.id] if self.partner_id else [],
            'force_email': True,
        }
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }

    def check_portal_manager_access(self, user=None):
        self.ensure_one()
        user = user or self.env.user
        if user.has_group('base.group_user'):
            return True
        if user != self.survey_manager_id and user != self.survey_member_id:
            raise AccessError(_('You do not have access to this inspection.'))
        return True

    def _portal_get_sorted_checklist_lines(self):
        self.ensure_one()
        return self.checklist_line_ids.sorted(lambda line: (line.sequence, line.id))

    def _sync_master_checklist_lines(self):
        point_model = self.env['solar.site.inspection.checklist.point']
        for inspection in self:
            existing_ids = inspection.checklist_line_ids.mapped('checklist_point_id').ids
            for checklist_point in point_model.search([('active', '=', True)], order='sequence, id'):
                if checklist_point.id not in existing_ids:
                    self.env['solar.site.inspection.checklist'].create({
                        'inspection_id': inspection.id,
                        'checklist_point_id': checklist_point.id,
                        'name': checklist_point.name,
                        'sequence': checklist_point.sequence,
                    })

    def _sync_existing_inspections_for_checklist_point(self, checklist_points):
        inspections = self.search([])
        for inspection in inspections:
            for checklist_point in checklist_points:
                if checklist_point.active and checklist_point.id not in inspection.checklist_line_ids.mapped('checklist_point_id').ids:
                    self.env['solar.site.inspection.checklist'].create({
                        'inspection_id': inspection.id,
                        'checklist_point_id': checklist_point.id,
                        'name': checklist_point.name,
                        'sequence': checklist_point.sequence,
                    })

    def _portal_get_sorted_image_lines(self):
        self.ensure_one()
        return self.image_ids.sorted(lambda image: (image.sequence, image.id))

    def portal_prepare_page_values(self):
        self.ensure_one()

        def _selection_options(field_name):
            field_info = self.env['crm.lead'].fields_get([field_name])[field_name]
            return field_info.get('selection') or []

        return {
            'inspection': self,
            'checklist_lines': self._portal_get_sorted_checklist_lines(),
            'image_lines': self._portal_get_sorted_image_lines(),
            'system_type_options': self._fields['system_type'].selection,
            'feasibility_reason_options': self._fields['feasibility_reason'].selection,
            'yes_no_options': self._fields['installation_feasible'].selection,
            'shadow_present_options': self._fields['shadow_present'].selection,
            'obstruction_type_options': self._fields['obstruction_type'].selection,
            'orientation_options': self._fields['orientation'].selection,
            'backup_requirement_options': self._fields['backup_requirement'].selection,
            'battery_required_options': self._fields['battery_required'].selection,
            'roof_load_capacity_options': self._fields['roof_load_capacity_ok'].selection,
            'mounting_structure_type_options': self._fields['mounting_structure_type'].selection,
            'risk_level_options': self._fields['installation_risk_level'].selection,
            'connection_type_options': _selection_options('renewable_connection_type'),
            'existing_connection_options': _selection_options('renewable_existing_connection'),
            'customer_category_options': _selection_options('renewable_site_usage'),
            'service_type_options': _selection_options('renewable_service_type'),
            'property_type_options': _selection_options('renewable_property_type'),
            'roof_type_options': _selection_options('renewable_roof_type'),
        }

    def portal_delete_image(self, image_id, user=None):
        self.ensure_one()
        user = user or self.env.user
        self.check_portal_manager_access(user=user)
        image = self.image_ids.filtered(lambda line: line.id == image_id)
        if not image:
            raise AccessError(_('The requested image was not found for this inspection.'))
        image.sudo().unlink()
        return True

    @staticmethod
    def _portal_extract_post_list(post, key):
        values = post.getlist(key) if hasattr(post, 'getlist') else post.get(key, [])
        if isinstance(values, str):
            return [values]
        return values or []

    def _portal_build_checklist_commands(self, post):
        checklist_commands = []
        checklist_keys = self._portal_extract_post_list(post, 'checklist_keys')
        delete_keys = {str(key) for key in self._portal_extract_post_list(post, 'checklist_delete_ids')}
        valid_lines = {str(line.id): line for line in self.checklist_line_ids}
        next_sequence = max(self.checklist_line_ids.mapped('sequence') or [0]) + 10
        for key in delete_keys:
            line = valid_lines.get(key)
            if line:
                checklist_commands.append((2, line.id, 0))
        for key in checklist_keys:
            if str(key) in delete_keys:
                continue
            line = valid_lines.get(str(key))
            name = (post.get('checklist_name_%s' % key) or '').strip()
            description = (post.get('checklist_description_%s' % key) or '').strip()
            if line:
                checklist_commands.append((1, line.id, {'name': name or line.name, 'description': description}))
            elif name or description:
                checklist_commands.append((0, 0, {'name': name or _('Checklist Point'), 'description': description, 'sequence': next_sequence}))
                next_sequence += 10
        return checklist_commands

    def _portal_build_image_commands(self, post, files):
        image_commands = []
        next_sequence = max(self.image_ids.mapped('sequence') or [0]) + 10
        for key in self._portal_extract_post_list(post, 'image_keys'):
            upload = files.get('inspection_image_%s' % key)
            image_tag = (post.get('inspection_image_tag_%s' % key) or '').strip()
            image_title = (post.get('inspection_image_title_%s' % key) or '').strip()
            if not upload:
                continue
            content = upload.read()
            if not content:
                continue
            image_commands.append((0, 0, {'name': image_title or upload.filename or _('Inspection Image'), 'image_tag': image_tag, 'image': base64.b64encode(content), 'sequence': next_sequence}))
            next_sequence += 10
        return image_commands

    def portal_submit_inspection(self, post, files=None, user=None):
        self.ensure_one()
        user = user or self.env.user
        self.check_portal_manager_access(user=user)
        if self.state in ('approved', 'completed', 'cancelled'):
            raise AccessError(_('Approved inspections cannot be modified .'))
        files = files or {}

        def _clean_value(key):
            return (post.get(key) or '').strip()

        def _clean_float(key, default=False):
            value = _clean_value(key)
            if value == '':
                return default
            try:
                return float(value)
            except (TypeError, ValueError):
                return default

        def _clean_int(key, default=False):
            value = _clean_value(key)
            if value == '':
                return default
            try:
                return int(float(value))
            except (TypeError, ValueError):
                return default

        def _clean_date(key):
            value = _clean_value(key)
            if not value:
                return False
            try:
                return fields.Date.to_date(value)
            except (TypeError, ValueError):
                return False

        inspection_vals = {
            'inspection_date': _clean_date('inspection_date') or self.inspection_date,
            'max_installable_capacity_kw': _clean_float('max_installable_capacity_kw', 0.0),
            'recommended_system_size_kw': _clean_float('recommended_system_size_kw', 0.0),
            'expected_generation_kwh_month': _clean_float('expected_generation_kwh_month', 0.0),
            'system_type': _clean_value('system_type') or False,
            'installation_feasible': _clean_value('installation_feasible') or False,
            'feasibility_reason': _clean_value('feasibility_reason') or False,
            'shadow_present': _clean_value('shadow_present') or False,
            'shadow_percentage': _clean_float('shadow_percentage', 0.0),
            'obstruction_type': _clean_value('obstruction_type') or False,
            'orientation': _clean_value('orientation') or False,
            'peak_load_kw': _clean_float('peak_load_kw', 0.0),
            'backup_requirement': _clean_value('backup_requirement') or False,
            'battery_required': _clean_value('battery_required') or False,
            'roof_load_capacity_ok': _clean_value('roof_load_capacity_ok') or False,
            'structure_reinforcement_required': _clean_value('structure_reinforcement_required') or False,
            'mounting_structure_type': _clean_value('mounting_structure_type') or False,
            'estimated_project_cost': _clean_float('estimated_project_cost', 0.0),
            'payback_period_years': _clean_float('payback_period_years', 0.0),
            'installation_risk_level': _clean_value('installation_risk_level') or False,
            'safety_notes': _clean_value('safety_notes') or False,
            'site_remarks': _clean_value('site_remarks') or False,
            'checklist_line_ids': self._portal_build_checklist_commands(post),
            'portal_submission_date': fields.Datetime.now(),
            'portal_submitted_by_id': user.id,
            'state': 'submitted',
            'approved_by_id': False,
            'approved_date': False,
            'rejected_by_id': False,
            'rejected_date': False,
            'rejection_reason': False,
        }
        lead_vals = {
            'renewable_connection_type': _clean_value('connection_type') or False,
            'renewable_existing_connection': _clean_value('existing_connection') or False,
            'renewable_existing_supply_volts': _clean_float('existing_supply_volts', 0.0),
            'renewable_site_usage': _clean_value('customer_category') or False,
            'renewable_service_type': _clean_value('service_type') or False,
            'renewable_contract_demand_kw': _clean_float('contract_demand_kw', 0.0),
            'renewable_property_type': _clean_value('property_type') or False,
            'renewable_property_age_years': _clean_int('property_age_years', 0),
            'renewable_roof_type': _clean_value('roof_type') or False,
            'renewable_roof_area_sqft': _clean_float('roof_area_sqft', 0.0),
            'renewable_consumer_no': _clean_value('consumer_no') or False,
            'renewable_monthly_electric_bill': _clean_float('monthly_electric_bill', 0.0),
            'renewable_monthly_electricity_consumption': _clean_float('monthly_electricity_consumption', 0.0),
        }

        electricity_bill_pdf = files.get('electricity_bill_pdf')
        if electricity_bill_pdf:
            content = electricity_bill_pdf.read()
            if content:
                inspection_vals['electricity_bill_pdf'] = base64.b64encode(content)
                inspection_vals['electricity_bill_pdf_filename'] = electricity_bill_pdf.filename or 'electricity_bill.pdf'
        site_layout_plan = files.get('site_layout_plan')
        if site_layout_plan:
            content = site_layout_plan.read()
            if content:
                inspection_vals['site_layout_plan'] = base64.b64encode(content)
                inspection_vals['site_layout_plan_filename'] = site_layout_plan.filename or 'site_layout_plan'
        government_approval_docs = files.get('government_approval_docs')
        if government_approval_docs:
            content = government_approval_docs.read()
            if content:
                inspection_vals['government_approval_docs'] = base64.b64encode(content)
                inspection_vals['government_approval_docs_filename'] = government_approval_docs.filename or 'government_approval_docs'
        image_commands = self._portal_build_image_commands(post, files)
        if image_commands:
            inspection_vals['image_ids'] = image_commands
        inspection_vals.update(self._get_recommendation_values(inspection_vals))
        self.lead_id.sudo().write(lead_vals)
        self.sudo().write(inspection_vals)
        if self.survey_task_id:
            self._sync_task_stage(self.survey_task_id, self.state)
        return True

    def _get_default_survey_project(self):
        project_name = self.lead_id.name or 'Solar Project'
        project = self.env['project.project'].sudo().search([
            ('name', '=', project_name), ('partner_id', '=', self.partner_id.id)
        ], limit=1)
        if not project:
            project = self.env['project.project'].sudo().create({
                'name': project_name,
                'partner_id': self.partner_id.id,
                'lead_id': self.lead_id.id,
            })
        return project

    def _prepare_survey_task_vals(self):
        self.ensure_one()
        member_ids = []
        if self.survey_member_id:
            member_ids.append(self.survey_member_id.id)
        if self.survey_manager_id:
            member_ids.append(self.survey_manager_id.id)
        if self.survey_team_id:
            member_ids.extend(self.survey_team_id.member_ids.ids)
            if self.survey_team_id.manager_id:
                member_ids.append(self.survey_team_id.manager_id.id)
        unique_member_ids = list(dict.fromkeys([m for m in member_ids if m]))

        project = self.project_id or self.lead_id.project_id or self._get_default_survey_project()
        return {
            'name': "Site Inspection",
            'project_id': project.id,
            'date_deadline': self.inspection_date,
            'partner_id': self.partner_id.id,
            'user_ids': [(6, 0, unique_member_ids)],
            'team_type': 'survey',
            'site_inspection_id': self.id,
            'lead_id': self.lead_id.id,
            'survey_team_id': self.survey_team_id.id if self.survey_team_id else False,
        }

    def _sync_survey_task(self):
        for inspection in self:
            if not inspection.project_id:
                proj = inspection.lead_id.project_id or inspection._get_default_survey_project()
                inspection.sudo().write({'project_id': proj.id})
            task = inspection.survey_task_id
            vals = inspection._prepare_survey_task_vals()
            if task:
                task.sudo().write(vals)
            else:
                task = self.env['project.task'].sudo().create(vals)
            inspection.sudo().write({'survey_task_id': task.id})
            inspection._sync_task_stage(task, inspection.state)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('solar.site.inspection') or 'New'
            if vals.get('lead_id') and not vals.get('project_id'):
                lead = self.env['crm.lead'].browse(vals['lead_id'])
                if lead.project_id:
                    vals['project_id'] = lead.project_id.id
        inspections = super().create(vals_list)
        leads = inspections.mapped('lead_id').filtered(lambda lead: lead)
        leads.write({
            'solar_stage': 'site_survey_scheduled',
        })
        leads._set_solar_crm_stage_proposition()
        inspections._sync_master_checklist_lines()
        inspections._sync_recommendation_values()
        inspections._sync_survey_task()
        return inspections

    def write(self, vals):
        res = super().write(vals)
        if any(key in vals for key in ('survey_team_id', 'survey_member_id', 'inspection_date', 'project_id', 'lead_id', 'state')):
            self._sync_survey_task()
        if any(key in vals for key in ('checklist_line_ids',)):
            self._sync_master_checklist_lines()
        if not self.env.context.get('skip_recommendation_sync'):
            self._sync_recommendation_values()
        return res


class SolarSiteInspectionImage(models.Model):
    _name = 'solar.site.inspection.image'
    _description = 'Solar Site Inspection Image'
    _order = 'sequence, id'

    sequence = fields.Integer(default=10)
    name = fields.Char(string='Title', required=True, default='Site Image')
    image_tag = fields.Char(string='Tag')
    inspection_id = fields.Many2one('solar.site.inspection', string='Site Inspection', required=True, ondelete='cascade')
    image = fields.Image(string='Image', required=True)
    image_128 = fields.Image(string='Thumbnail', related='image', max_width=128, max_height=128)


class SolarSiteInspectionChecklistPoint(models.Model):
    _name = 'solar.site.inspection.checklist.point'
    _description = 'Site Inspection Checklist Point'
    _order = 'sequence, id'

    sequence = fields.Integer(default=10)
    name = fields.Char(string='Checklist Point', required=True)
    active = fields.Boolean(default=True)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        self.env['solar.site.inspection']._sync_existing_inspections_for_checklist_point(records)
        return records

    def write(self, vals):
        res = super().write(vals)
        for rec in self:
            linked_lines = self.env['solar.site.inspection.checklist'].search([('checklist_point_id', '=', rec.id)])
            line_vals = {}
            if 'name' in vals:
                line_vals['name'] = rec.name
            if 'sequence' in vals:
                line_vals['sequence'] = rec.sequence
            if line_vals and linked_lines:
                linked_lines.write(line_vals)
            if vals.get('active'):
                self.env['solar.site.inspection']._sync_existing_inspections_for_checklist_point(rec)
        return res


class SolarSiteInspectionChecklist(models.Model):
    _name = 'solar.site.inspection.checklist'
    _description = 'Solar Site Inspection Checklist'
    _order = 'sequence, id'

    sequence = fields.Integer(default=10)
    inspection_id = fields.Many2one('solar.site.inspection', string='Site Inspection', required=True, ondelete='cascade')
    checklist_point_id = fields.Many2one('solar.site.inspection.checklist.point', string='Checklist Point', ondelete='set null')
    is_ok = fields.Boolean(string='OK', default=True)
    name = fields.Char(string='Check Name', required=True)
    description = fields.Char(string='Description')
