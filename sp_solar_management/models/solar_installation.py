# -- encoding: utf-8 --
###############################################################################
#
# Copyright (C) 2022-Present Speeduplight (https://speeduplight.com/)
#
###############################################################################
from thrive import _, api, fields, models
from thrive.exceptions import ValidationError

class SolarInstallation(models.Model):
    _name = 'solar.installation'
    _description = 'Manage installation process for solar projects'
    _order = 'actual_start_date desc, id desc'
    _rec_name = 'installation_id'
    _installation_id_unique = models.Constraint(
        'UNIQUE(installation_id)',
        'Installation ID must be unique.'
    )

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

    # Section 1: Project Information
    installation_id = fields.Char(string='Installation ID', required=True, copy=False, readonly=True, default='New')
    lead_id = fields.Many2one('crm.lead', string='Application / Project', required=True, ondelete='cascade')
    partner_id = fields.Many2one('res.partner', string='Customer', related='lead_id.partner_id', store=True, readonly=True)
    design_id = fields.Many2one('solar.design', string='Design', ondelete='set null')
    sale_order_id = fields.Many2one('sale.order', string='Sales Order', compute='_compute_sale_order_id', store=True, readonly=False)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)
    location = fields.Char(string='Location', compute='_compute_location', store=True, readonly=False)
    project_id = fields.Many2one('project.project', string='Project')
    project_count = fields.Integer(compute='_compute_project_count', string='Project Count')
    contract_count = fields.Integer(compute='_compute_contract_count', string='Contract Count')
    maintenance_count = fields.Integer(compute='_compute_maintenance_count', string='Maintenance Count')
    document_count = fields.Integer(compute='_compute_document_count', string='Document Count')
    alert_count = fields.Integer(compute='_compute_alert_count', string='Alert Count')
    installation_task_id = fields.Many2one('project.task', string='Installation Task', readonly=True, copy=False)



    def _get_default_location(self):
        self.ensure_one()
        lead = self.design_id.inspection_id.lead_id or self.design_id.lead_id or self.lead_id
        return lead._get_solar_contact_address() if lead else False

    @api.depends(
        'lead_id',
        'lead_id.renewable_site_street',
        'lead_id.renewable_site_street2',
        'lead_id.renewable_site_city',
        'lead_id.renewable_site_state_id',
        'lead_id.renewable_site_zip',
        'lead_id.renewable_site_country_id',
        'lead_id.partner_id',
        'design_id',
        'design_id.lead_id',
        'design_id.inspection_id',
        'design_id.inspection_id.lead_id',
    )
    def _compute_location(self):
        for rec in self:
            if not rec.location:
                rec.location = rec._get_default_location()

    @api.onchange('lead_id', 'design_id')
    def _onchange_location_source(self):
        for rec in self:
            if not rec.location:
                rec.location = rec._get_default_location()

    @api.depends('lead_id')
    def _compute_sale_order_id(self):
        for rec in self:
            if rec.lead_id and not rec.sale_order_id:
                sale_order = self.env['sale.order'].search([('opportunity_id', '=', rec.lead_id.id)], limit=1, order='id desc')
                if sale_order:
                    rec.sale_order_id = sale_order.id

    salesperson_id = fields.Many2one('res.users', string='Salesperson', related='lead_id.user_id', store=True, readonly=True)
    system_size_kw = fields.Float(related='design_id.system_size', string='System Size (kW)', store=True, readonly=True)
    expected_generation_kwh_month = fields.Float(
        related='design_id.expected_generation_kwh_month',
        string='Expected Generation (kWh/month)',
        store=True,
        readonly=True,
    )
    
    installation_status = fields.Selection([
        ('planning', 'Draft'),
        ('in_progress', 'In Process'),
        ('completed', 'Completed'),
    ], string='Installation Status', default='planning', tracking=True)

    dashboard_status = fields.Selection([
        ('planning', 'Planning'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ], string='Status', compute='_compute_dashboard_status', store=True)


    # Section 3: Material Status
    material_readiness = fields.Selection([
        ('not_ready', 'Not Ready'),
        ('partially_ready', 'Partially Ready'),
        ('ready', 'Ready'),
    ], string='Material Readiness', default='not_ready', tracking=True)
    panel_availability = fields.Selection([('yes', 'Yes'), ('no', 'No'), ('partial', 'Partial')], string='Panel Availability', default='no')
    inverter_availability = fields.Selection([('yes', 'Yes'), ('no', 'No'), ('partial', 'Partial')], string='Inverter Availability', default='no')
    structure_availability = fields.Selection([('yes', 'Yes'), ('no', 'No'), ('partial', 'Partial')], string='Structure Availability', default='no')

    # Legacy material fields (kept to avoid errors if used elsewhere, hide in view)
    panels_delivered = fields.Boolean(string='Panels Delivered')
    inverter_delivered = fields.Boolean(string='Inverter Delivered')
    structure_delivered = fields.Boolean(string='Structure Delivered')
    cables_delivered = fields.Boolean(string='Cables Delivered')
    structure_installed = fields.Boolean(string='Structure Installed')
    panels_installed = fields.Boolean(string='Panels Installed')
    dc_wiring_done = fields.Boolean(string='DC Wiring Done')
    inverter_installed = fields.Boolean(string='Inverter Installed')
    ac_connection_done = fields.Boolean(string='AC Connection Done')
    earthing_done = fields.Boolean(string='Earthing Done')
    testing_done = fields.Boolean(string='Testing Done')

    # Section 4: Execution Type
    installation_type = fields.Selection([
        ('in_house', 'Internal Team'),
        ('subcontracted', 'Subcontractor'),
    ], string='Execution Type')

    team_id = fields.Many2one('solar.installation.team', string='Team')
    project_manager_id = fields.Many2one(
        'res.users',
        string='Project Manager',
        related='team_id.manager_id',
        store=True,
        readonly=True,
    )
    coordinator_id = fields.Many2one(
        'res.users',
        string='Coordinator',
        related='team_id.coordinator_id',
        store=True,
        readonly=True,
    )
    team_engineer_ids = fields.Many2many(
        'res.users',
        string='Team Members',
        related='team_id.engineer_ids',
        readonly=True,
    )
    assigned_engineer_id = fields.Many2one('res.users', string='Assigned Engineer', compute='_compute_assigned_engineer', store=True)
    team_leader = fields.Char(related='team_id.team_leader_id.name', string='Team Leader', store=True, readonly=True)
    technician_count = fields.Integer(related='team_id.technician_count', string='Technician Count', store=True, readonly=True)
    team_contact = fields.Char(string='Team Contact')

    subcontractor_id = fields.Many2one(
        'solar.subcontractor',
        string='Subcontractor Name',
    )
    contact_person = fields.Char(string='Contact Person')
    phone = fields.Char(string='Phone')
    current_assigned_person = fields.Char(string='Assigned Person', compute='_compute_current_assigned_person')

    # Section 6: Schedule
    planned_start_date = fields.Date(string='Planned Start Date')
    planned_end_date = fields.Date(string='Planned End Date')
    actual_start_date = fields.Date(string='Actual Start Date')
    actual_end_date = fields.Date(string='Actual End Date')
    
    # Legacy schedule fields
    installation_date = fields.Date(string='Installation Date')
    start_time = fields.Float(string='Start Time')
    expected_completion_date = fields.Date(string='Expected Completion Date')
    completion_date = fields.Date(string='Completion Date')

    # Section 7: Issues / Blockers
    issue_description = fields.Text(string='Issue Description')
    issue_type = fields.Selection([
        ('material', 'Material'),
        ('approval', 'Approval'),
        ('site', 'Site'),
        ('weather', 'Weather'),
    ], string='Issue Type')
    issue_status = fields.Selection([
        ('open', 'Open'),
        ('resolved', 'Resolved'),
    ], string='Issue Status', default='open')

    # Section 8: Work Notes
    internal_notes = fields.Text(string='Notes')
    last_update_date = fields.Datetime(string='Last Update Date', compute='_compute_last_update_date', store=True)

    # Section 9: Work Photos
    photo_ids = fields.One2many('solar.installation.photo', 'installation_id', string='Work Photos')

    # Legacy photo fields
    before_photos = fields.Binary(string='Before Photos', attachment=True)
    before_photos_filename = fields.Char(string='Before Photos Filename')
    during_photos = fields.Binary(string='During Photos', attachment=True)
    during_photos_filename = fields.Char(string='During Photos Filename')
    after_photos = fields.Binary(string='After Photos', attachment=True)
    after_photos_filename = fields.Char(string='After Photos Filename')
    
    subcontractor_notes = fields.Text(string='Subcontractor Notes')
    manager_verified = fields.Boolean(string='Manager Verified')
    customer_confirmed = fields.Boolean(string='Customer Confirmed')

    @api.depends('internal_notes')
    def _compute_last_update_date(self):
        for rec in self:
            if rec.internal_notes:
                rec.last_update_date = fields.Datetime.now()

    @api.depends('project_id')
    def _compute_project_count(self):
        for rec in self:
            rec.project_count = 1 if rec.project_id else 0

    @api.depends('lead_id')
    def _compute_contract_count(self):
        for rec in self:
            rec.contract_count = self.env['solar.contract'].sudo().search_count([
                ('installation_id', '=', rec.id)
            ])

    def _compute_maintenance_count(self):
        for rec in self:
            rec.maintenance_count = self.env['maintenance.request'].sudo().search_count([
                ('installation_id', '=', rec.id)
            ])

    def _compute_document_count(self):
        for rec in self:
            rec.document_count = self.env['solar.installation.document'].sudo().search_count([
                ('installation_id', '=', rec.id)
            ])

    def _compute_alert_count(self):
        for rec in self:
            rec.alert_count = self.env['solar.installation.alert'].sudo().search_count([
                ('installation_id', '=', rec.id)
            ])



    def action_view_project(self):
        self.ensure_one()
        if not self.project_id:
            self.project_id = self.lead_id.project_id or self._get_default_installation_project()
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

    @api.depends('installation_status')
    def _compute_dashboard_status(self):
        for rec in self:
            if rec.installation_status == 'completed':
                rec.dashboard_status = 'completed'
            elif rec.installation_status == 'planning':
                rec.dashboard_status = 'planning'
            else:
                rec.dashboard_status = 'in_progress'

    @api.depends('installation_type', 'team_id', 'team_leader', 'subcontractor_id', 'contact_person')
    def _compute_current_assigned_person(self):
        for rec in self:
            if rec.installation_type == 'subcontracted':
                rec.current_assigned_person = rec.subcontractor_id.display_name or rec.contact_person or False
            else:
                rec.current_assigned_person = rec.team_id.display_name or rec.team_leader or False

    @api.depends('team_id', 'team_id.engineer_ids', 'team_id.team_leader_id')
    def _compute_assigned_engineer(self):
        for rec in self:
            rec.assigned_engineer_id = rec.team_id.team_leader_id or rec.team_id.engineer_ids[:1] or False

    @api.onchange('subcontractor_id')
    def _onchange_subcontractor_id(self):
        for rec in self:
            if rec.subcontractor_id:
                rec.contact_person = rec.subcontractor_id.contact_person
                rec.phone = rec.subcontractor_id.phone

    @api.onchange('installation_type')
    def _onchange_installation_type(self):
        for rec in self:
            if rec.installation_type != 'subcontracted':
                rec.subcontractor_id = False
                rec.contact_person = False
                rec.phone = False
                rec.subcontractor_notes = False
            else:
                rec.team_id = False

    @api.constrains('installation_type', 'team_id', 'subcontractor_id', 'contact_person', 'phone', 'installation_status')
    def _check_execution_assignment(self):
        for rec in self:
            if rec.installation_status == 'planning':
                continue
            if not rec.installation_type:
                raise ValidationError(_('Please select an Execution Type.'))
            if rec.installation_type == 'in_house' and not rec.team_id:
                raise ValidationError(_('Please select a team for internal execution.'))
            if rec.installation_type == 'subcontracted':
                if not rec.subcontractor_id:
                    raise ValidationError(_('Please select a subcontractor for subcontracted execution.'))
                if not rec.contact_person or not rec.phone:
                    raise ValidationError(_('Please complete the subcontractor contact person and phone number.'))

    def _notification_action(self, message, title=None):
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': title or _('Solar Installation'),
                'message': message,
                'type': 'success',
                'sticky': False,
            }
        }

    def action_update_progress(self):
        self.ensure_one()
        if not self.installation_type:
            raise ValidationError(_('Please select an Execution Type before starting the installation.'))
        if self.installation_type == 'in_house' and not self.team_id:
            raise ValidationError(_('Please select a team for internal execution before starting the installation.'))
        if self.installation_type == 'subcontracted':
            if not self.subcontractor_id:
                raise ValidationError(_('Please select a subcontractor for subcontracted execution before starting the installation.'))
            if not self.contact_person or not self.phone:
                raise ValidationError(_('Please complete the subcontractor contact person and phone number before starting the installation.'))

        if self.installation_status == 'completed':
            return {'type': 'ir.actions.client', 'tag': 'reload'}
        if self.installation_status == 'in_progress':
            return {'type': 'ir.actions.client', 'tag': 'reload'}
        self.write({'installation_status': 'in_progress'})
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def action_mark_stage_complete(self):
        self.ensure_one()
        if self.installation_status == 'completed':
            return {'type': 'ir.actions.client', 'tag': 'reload'}
        if self.installation_status != 'in_progress':
            raise ValidationError(_('You can only complete an installation that is in process.'))
        vals = {
            'installation_status': 'completed',
            'actual_end_date': fields.Date.context_today(self),
        }
        self.write(vals)
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def action_view_contracts(self):
        self.ensure_one()
        return {
            'name': _('Contracts'),
            'type': 'ir.actions.act_window',
            'res_model': 'solar.contract',
            'view_mode': 'list,form',
            'domain': [('installation_id', '=', self.id)],
            'context': {
                'default_lead_id': self.lead_id.id,
                'default_installation_id': self.id,
            },
        }

    def action_view_maintenance(self):
        self.ensure_one()
        return {
            'name': _('Maintenance Requests'),
            'type': 'ir.actions.act_window',
            'res_model': 'maintenance.request',
            'view_mode': 'kanban,list,form',
            'domain': [('installation_id', '=', self.id)],
            'context': {
                'default_installation_id': self.id,
                'default_partner_id': self.partner_id.id,
                'default_project_id': self.project_id.id,
            },
        }

    def action_view_documents(self):
        self.ensure_one()
        return {
            'name': _('Documents'),
            'type': 'ir.actions.act_window',
            'res_model': 'solar.installation.document',
            'view_mode': 'list,form',
            'domain': [('installation_id', '=', self.id)],
            'context': {
                'default_installation_id': self.id,
            },
        }

    def action_view_alerts(self):
        self.ensure_one()
        return {
            'name': _('Alerts'),
            'type': 'ir.actions.act_window',
            'res_model': 'solar.installation.alert',
            'view_mode': 'list,form',
            'domain': [('installation_id', '=', self.id)],
            'context': {
                'default_installation_id': self.id,
            },
        }



    def action_create_maintenance(self):
        self.ensure_one()
        return {
            'name': _('Create Maintenance Request'),
            'type': 'ir.actions.act_window',
            'res_model': 'maintenance.request',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_installation_id': self.id,
                'default_partner_id': self.partner_id.id,
                'default_project_id': self.project_id.id,
            }
        }

    def action_create_contract(self):
        self.ensure_one()
        existing_contract = self.env['solar.contract'].search([
            ('installation_id', '=', self.id)
        ], limit=1)
        if existing_contract:
            return {
                'name': _('Contract'),
                'type': 'ir.actions.act_window',
                'res_model': 'solar.contract',
                'view_mode': 'form',
                'res_id': existing_contract.id,
                'target': 'current',
            }
        contract = self.env['solar.contract'].create({
            'partner_id': self.partner_id.id if self.partner_id else False,
            'project_id': self.project_id.id if self.project_id else False,
            'lead_id': self.lead_id.id if self.lead_id else False,
            'installation_id': self.id,
            'start_date': fields.Date.context_today(self),
            'status': 'draft',
        })
        return {
            'name': _('Contract'),
            'type': 'ir.actions.act_window',
            'res_model': 'solar.contract',
            'view_mode': 'form',
            'res_id': contract.id,
            'target': 'current',
        }

    def action_upload_photo(self):
        self.ensure_one()
        return {
            'name': _('Site Work Photos'),
            'type': 'ir.actions.act_window',
            'res_model': 'solar.installation.photo',
            'view_mode': 'list,form',
            'target': 'current',
            'domain': [
                ('installation_id', '=', self.id),
            ],
            'context': {
                'default_installation_id': self.id,
            },
        }

    def _sync_lead_solar_stage(self):
        for rec in self.filtered('lead_id'):
            if rec.installation_status == 'completed':
                rec.lead_id.sudo().write({'solar_stage': 'system_activated'})
            else:
                rec.lead_id.sudo().write({'solar_stage': 'installation_in_progress'})

    def _prepare_completion_vals(self, vals):
        vals = dict(vals)
        if vals.get('installation_status') == 'completed' and not vals.get('actual_end_date'):
            vals['actual_end_date'] = fields.Date.context_today(self)
        return vals

    def _get_default_installation_project(self):
        project_name = self.lead_id.name or 'Solar Project'
        project = self.env['project.project'].sudo().search([
            ('name', '=', project_name), ('partner_id', '=', self.partner_id.id)
        ], limit=1)
        if not project:
            project = self.env['project.project'].sudo().create({
                'name': project_name,
                'partner_id': self.partner_id.id,
                'lead_id': self.lead_id.id if self.lead_id else False,
            })
            if self.lead_id:
                self.lead_id.sudo().write({'project_id': project.id})
        return project

    def _prepare_installation_task_vals(self):
        self.ensure_one()
        member_ids = []
        if self.assigned_engineer_id:
            member_ids.append(self.assigned_engineer_id.id)
        if self.project_manager_id:
            member_ids.append(self.project_manager_id.id)
        if self.coordinator_id:
            member_ids.append(self.coordinator_id.id)
        if self.team_id:
            member_ids.extend(self.team_id.engineer_ids.ids)
            if self.team_id.manager_id:
                member_ids.append(self.team_id.manager_id.id)
        unique_member_ids = list(dict.fromkeys([m for m in member_ids if m]))

        project = self.project_id or self.lead_id.project_id or self._get_default_installation_project()
        return {
            'name': "Installation",
            'project_id': project.id,
            'date_deadline': self.planned_end_date or self.installation_date,
            'partner_id': self.partner_id.id,
            'user_ids': [(6, 0, unique_member_ids)],
            'team_type': 'installation',
            'installation_id': self.id,
            'lead_id': self.lead_id.id,
        }

    def _sync_task_stage(self, task, status=None):
        self.ensure_one()
        status = status or self.installation_status
        stage_model = self.env['project.task.type'].sudo()
        if status == 'planning':
            stage_name = 'New'
        elif status == 'in_progress':
            stage_name = 'In Progress'
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

    def _sync_installation_task(self):
        for rec in self:
            if not rec.project_id:
                proj = rec.lead_id.project_id or rec._get_default_installation_project()
                rec.sudo().write({'project_id': proj.id})
            task = rec.installation_task_id
            vals = rec._prepare_installation_task_vals()
            if task:
                task.sudo().write(vals)
            else:
                task = self.env['project.task'].sudo().create(vals)
                rec.sudo().write({'installation_task_id': task.id})
            rec._sync_task_stage(task, rec.installation_status)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('installation_id', 'New') == 'New':
                vals['installation_id'] = self.env['ir.sequence'].next_by_code('solar.installation') or 'New'
            if vals.get('lead_id') and not vals.get('project_id'):
                lead = self.env['crm.lead'].browse(vals['lead_id'])
                if lead.project_id:
                    vals['project_id'] = lead.project_id.id
            if not vals.get('location'):
                design = self.env['solar.design'].browse(vals.get('design_id')) if vals.get('design_id') else self.env['solar.design']
                lead = self.env['crm.lead'].browse(vals.get('lead_id')) if vals.get('lead_id') else design.lead_id
                location_lead = design.inspection_id.lead_id or design.lead_id or lead
                if location_lead:
                    vals['location'] = location_lead._get_solar_contact_address()
        vals_list = [self._prepare_completion_vals(vals) for vals in vals_list]
        records = super().create(vals_list)
        records._sync_lead_solar_stage()
        records._sync_installation_task()
        return records

    def write(self, vals):
        vals = self._prepare_completion_vals(vals)
        res = super().write(vals)
        if not self.env.context.get('skip_location_sync') and any(key in vals for key in ('lead_id', 'design_id')):
            for rec in self.filtered(lambda installation: not installation.location):
                location = rec._get_default_location()
                if location:
                    rec.with_context(skip_location_sync=True).write({'location': location})
        if 'installation_status' in vals or 'lead_id' in vals:
            self._sync_lead_solar_stage()
        if any(key in vals for key in ('team_id', 'subcontractor_id', 'installation_type', 'planned_end_date', 'installation_date', 'project_id', 'lead_id', 'installation_status', 'assigned_engineer_id')):
            self._sync_installation_task()
        return res

    def unlink(self):
        tasks_to_delete = self.mapped('installation_task_id')
        res = super(SolarInstallation, self).unlink()
        if tasks_to_delete:
            tasks_to_delete.sudo().unlink()
        return res
