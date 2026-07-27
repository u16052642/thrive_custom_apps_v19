# -- encoding: utf-8 --
###############################################################################
#
# Copyright (C) 2022-Present Speeduplight (https://speeduplight.com/)
#
###############################################################################
import secrets
import string

from thrive import _, api, fields, models
from thrive.exceptions import ValidationError
from markupsafe import Markup, escape


class CrmLead(models.Model):
    _inherit = 'crm.lead'
    _rec_name = 'solar_reference'
    _rec_names_search = ['solar_reference', 'name']

    _solar_reference_unique = models.Constraint(
        'UNIQUE(solar_reference)',
        'Solar Tracking ID must be unique.'
    )
    _access_token_unique = models.Constraint(
        'UNIQUE(access_token)',
        'Access Token must be unique.'
    )

    solar_reference = fields.Char(
        string='Solar Tracking ID',
        copy=False,
        readonly=True,
        index=True,
        default='New',
    )
    access_token = fields.Char(
        string='Access Token',
        copy=False,
        readonly=True,
        index=True,
    )
    project_id = fields.Many2one(
        'project.project',
        string='Project',
        copy=False,
    )

    project_count = fields.Integer(
        string='Project',
        compute='_compute_project_count',
    )

    @api.depends('project_id')
    def _compute_project_count(self):
        for lead in self:
            lead.project_count = 1 if lead.project_id else 0

    renewable_service_type = fields.Selection(
        [
            ('power_backup', 'Power Backup'),
            ('on_grid', 'On Grid'),
            ('off_grid', 'Off Grid'),
            ('hybrid', 'Hybrid'),
        ],
        string='Service Type',
    )

    renewable_solar_company_id = fields.Many2one(
        'solar.company',
        string='Solar Company',
    )
    renewable_system_template_id = fields.Many2one(
        'solar.material.template',
        string='System Required',
    )
    renewable_gov_application_number = fields.Char(string='SSEG Approval Number')
    renewable_approx_amount = fields.Monetary(
        string='Approx Amount',
        currency_field='company_currency',
    )
    renewable_max_timeline = fields.Selection(
        [
            ('7_days', '7 Days'),
            ('15_days', '15 Days'),
            ('1_month', '1 Month'),
            ('2_months', '2 Months'),
            ('3_months', '3 Months'),
            ('6_months', '6 Months'),
        ],
        string='Max Timeline',
    )

    renewable_contract_demand_kw = fields.Float(string='Contract Demand (kW)')

    renewable_connection_type = fields.Selection(
        [
            ('single_phase', 'Single Phase'),
            ('three_phase', 'Three Phase'),
            ('other', 'Other'),
        ],
        string='Connection Type',
    )

    renewable_existing_connection = fields.Selection(
        [
            ('single_phase', 'Single Phase'),
            ('three_phase', 'Three Phase'),
        ],
        string='Existing Connection',
    )

    renewable_existing_supply_volts = fields.Float(string='Existing Supply Volts')

    renewable_consumer_no = fields.Char(string='Consumer No')

    renewable_monthly_electric_bill = fields.Monetary(
        string='Monthly Electric Bill',
        currency_field='company_currency',
    )

    renewable_monthly_electricity_consumption = fields.Float(
        string='Monthly Electricity Consumption (kWh)',
    )

    renewable_site_usage = fields.Selection(
        [
            ('residential', 'Residential'),
            ('commercial', 'Commercial'),
            ('industrial', 'Industrial'),
            ('agriculture', 'Agriculture'),
        ],
        string='Site Usage',
    )

    renewable_property_type = fields.Selection(
        [
            ('house', 'House'),
            ('semi', 'Semi'),
            ('villa', 'Villa'),
            ('apartment', 'Apartment'),
            ('factory', 'Factory'),
            ('warehouse', 'Warehouse'),
            ('office', 'Office'),
        ],
        string='Type of Property',
    )

    renewable_property_age_years = fields.Integer(string='Age of Property (Years)')

    renewable_roof_type = fields.Selection(
        [
            ('rcc', 'RCC Roof'),
            ('sheet', 'Sheet Roof'),
            ('tile', 'Tile Roof'),
            ('ground', 'Ground Mount'),
        ],
        string='Roof Type',
    )

    renewable_roof_area_sqft = fields.Float(string='Roof Area (Sq. Ft.)')

    # -------------------------
    # Site Address
    # -------------------------
    renewable_site_street = fields.Char(string='Site Street')
    renewable_site_street2 = fields.Char(string='Site Street 2')
    renewable_site_city = fields.Char(string='Site City')
    renewable_site_state_id = fields.Many2one(
        'res.country.state',
        string='Site State',
        domain="[('country_id', '=?', renewable_site_country_id)]",
    )
    renewable_site_zip = fields.Char(string='Site ZIP')
    renewable_site_country_id = fields.Many2one('res.country', string='Site Country')

    renewable_site_latitude = fields.Float(string='Latitude', digits=(16, 6))
    renewable_site_longitude = fields.Float(string='Longitude', digits=(16, 6))

    renewable_solar_requirement = fields.Text(string='Solar Requirement')
    solar_document_line_ids = fields.One2many('crm.lead.solar.document', 'lead_id', string='Solar Documents')
    required_solar_document_line_ids = fields.One2many(
        'crm.lead.solar.document',
        'lead_id',
        domain=[('is_required', '=', True)],
        string='Required Solar Documents',
    )
    optional_solar_document_line_ids = fields.One2many(
        'crm.lead.solar.document',
        'lead_id',
        domain=[('is_required', '=', False)],
        string='Optional Solar Documents',
    )
    renewable_has_required_documents = fields.Boolean(
        string='Has Required Documents',
        compute='_compute_renewable_has_required_documents',
    )

    electric_bill = fields.Binary(string='Electric Bill', attachment=True)
    electric_bill_filename = fields.Char(string='Electric Bill Filename')
    id_proof_type = fields.Selection(
        [
            ('aadhar_card', 'Aadhar Card'),
            ('pan_card', 'PAN Card'),
            ('passport', 'Passport'),
        ],
        string='ID Proof Type',
        help='Select the type of identity document',
    )
    id_proof = fields.Binary(
        string='ID Proof',
        attachment=True,
        help='Upload clear and valid document',
    )
    id_proof_filename = fields.Char(string='ID Proof Filename')
    ownership_proof = fields.Binary(string='Ownership Proof', attachment=True)
    ownership_proof_filename = fields.Char(string='Ownership Proof Filename')
    bank_cancel_cheque = fields.Binary(string='Bank Cancel Cheque', attachment=True)
    bank_cancel_cheque_filename = fields.Char(string='Bank Cancel Cheque Filename')
    passport_size_photo = fields.Binary(string='Passport Size Photo', attachment=True)
    passport_size_photo_filename = fields.Char(string='Passport Size Photo Filename')

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
        string='Solar Project Status',
        default='document_pending',
        tracking=True,
    )

    # -------------------------
    # Site Inspection
    # -------------------------
    site_inspection_count = fields.Integer(compute='_compute_site_inspection_count')
    installation_count = fields.Integer(compute='_compute_installation_count')
    government_approval_count = fields.Integer(compute='_compute_government_approval_count')
    design_count = fields.Integer(compute='_compute_design_count')


    @api.depends(
        'solar_document_line_ids.document_file',
        'solar_document_line_ids.is_required',
        'electric_bill',
        'id_proof',
    )
    def _compute_renewable_has_required_documents(self):
        for lead in self:
            lead.renewable_has_required_documents = lead._has_required_documents()

    def _compute_site_inspection_count(self):
        for lead in self:
            lead.site_inspection_count = self.env['solar.site.inspection'].sudo().search_count([
                ('lead_id', '=', lead.id)
            ])

    def _compute_installation_count(self):
        for lead in self:
            lead.installation_count = self.env['solar.installation'].sudo().search_count([
                ('lead_id', '=', lead.id)
            ])

    def _compute_government_approval_count(self):
        for lead in self:
            lead.government_approval_count = self.env['solar.government.approval'].sudo().search_count([
                ('lead_id', '=', lead.id)
            ])

    def _compute_design_count(self):
        for lead in self:
            lead.design_count = self.env['solar.design'].sudo().search_count([
                ('lead_id', '=', lead.id)
            ])

    def _get_active_required_document_lines(self):
        self.ensure_one()
        return self.solar_document_line_ids.filtered(lambda line: line.is_required)

    def _sync_dynamic_document_lines(self):
        document_configs = self.env['solar.document.config'].sudo().search([])
        for lead in self:
            existing_lines = {line.document_config_id.id: line for line in lead.solar_document_line_ids}
            missing_commands = []
            for config in document_configs:
                if config.id not in existing_lines:
                    missing_commands.append((0, 0, {'document_config_id': config.id}))
            if missing_commands:
                lead.write({'solar_document_line_ids': missing_commands})
        return True

    def _has_required_documents(self):
        self.ensure_one()
        required_lines = self._get_active_required_document_lines()
        if required_lines:
            return all(line._is_completed() for line in required_lines)
        return bool(self.electric_bill and self.id_proof)

    def _has_government_required_documents(self):
        self.ensure_one()
        return self._has_required_documents()

    def _create_government_approval_if_ready(self):
        Approval = self.env['solar.government.approval'].sudo()
        for lead in self:
            if not lead._has_government_required_documents():
                continue
            if Approval.search_count([('lead_id', '=', lead.id)]):
                continue
            approval = Approval.create({'lead_id': lead.id})
            message = _('Required documents uploaded for government application')
            lead.sudo().message_post(body=message)
            approval.message_post(body=message)

    def _validate_required_documents_for_inspection(self):
        pass

    def _get_solar_contact_address(self):
        self.ensure_one()
        address_parts = [
            self.renewable_site_street,
            self.renewable_site_street2,
            self.renewable_site_city,
            self.renewable_site_state_id.name if self.renewable_site_state_id else False,
            self.renewable_site_zip,
            self.renewable_site_country_id.name if self.renewable_site_country_id else False,
        ]
        address = ', '.join(part for part in address_parts if part)
        return address or self.partner_id.contact_address or '-'

    def _sync_solar_stage_from_documents(self):
        # Stages ordered from least to most advanced
        _stage_sequence = [
            'document_pending',
            'application_submitted',
            'site_survey_scheduled',
            'site_survey_completed',
            'design_approved',
            'government_approval',
            'installation_in_progress',
            'inspection_testing',
            'system_activated',
        ]
        for lead in self:
            current = lead.solar_stage or 'document_pending'
            current_idx = _stage_sequence.index(current) if current in _stage_sequence else 0
            if lead._has_required_documents():
                # Only advance if still at document_pending
                if current == 'document_pending':
                    lead.solar_stage = 'application_submitted'
            else:
                # Only revert if stage has not progressed past application_submitted
                if current_idx <= _stage_sequence.index('application_submitted'):
                    lead.solar_stage = 'document_pending'
        self._create_government_approval_if_ready()

    def _get_solar_crm_stage(self, stage_xmlid):
        return self.env.ref(stage_xmlid, raise_if_not_found=False)

    def _set_solar_crm_stage(self, stage_xmlid):
        stage = self._get_solar_crm_stage(stage_xmlid)
        if not stage:
            return False
        for lead in self:
            if lead.stage_id == stage:
                continue
            if lead.stage_id.is_won and not stage.is_won:
                continue
            lead.sudo().write({'stage_id': stage.id})
        return True

    def _set_solar_crm_stage_new(self):
        return self._set_solar_crm_stage('crm.stage_lead1')

    def _set_solar_crm_stage_qualified(self):
        return self.filtered(lambda lead: lead.type == 'opportunity')._set_solar_crm_stage('crm.stage_lead2')

    def _set_solar_crm_stage_proposition(self):
        return self.filtered(lambda lead: lead.type == 'opportunity')._set_solar_crm_stage('crm.stage_lead3')

    def _set_solar_crm_stage_won(self):
        leads = self.filtered(lambda lead: lead.type == 'opportunity' and lead.won_status != 'won')
        if leads:
            leads.sudo().action_set_won()
        return True

    def _action_view_document(self, field_name, filename_field):
        self.ensure_one()
        if not self[field_name]:
            raise ValidationError(_('No document is uploaded for this field.'))
        return {
            'type': 'ir.actions.act_url',
            'url': (
                '/web/content?model=crm.lead&id=%s&field=%s&filename_field=%s&download=false'
                % (self.id, field_name, filename_field)
            ),
            'target': 'new',
        }

    def action_view_electric_bill(self):
        return self._action_view_document('electric_bill', 'electric_bill_filename')

    def action_view_id_proof(self):
        return self._action_view_document('id_proof', 'id_proof_filename')

    def action_view_ownership_proof(self):
        return self._action_view_document('ownership_proof', 'ownership_proof_filename')

    def action_view_bank_cancel_cheque(self):
        return self._action_view_document('bank_cancel_cheque', 'bank_cancel_cheque_filename')

    def action_view_passport_size_photo(self):
        return self._action_view_document('passport_size_photo', 'passport_size_photo_filename')

    def action_send_solar_application_mail(self):
        self.ensure_one()
        email_to = self.email_from or self.partner_id.email or ''
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url', '').rstrip('/')
        tracking_url = f"{base_url}/solar/status/{self.access_token}" if base_url and self.access_token else ''
        customer_name = self.partner_name or self.contact_name or self.partner_id.name or self.name or _('Customer')
        application_no = self.solar_reference or self.name or '-'
        customer_phone = self.phone or self.partner_id.phone or '-'
        customer_address = self._get_solar_contact_address()
        safe_customer_name = escape(customer_name)
        safe_application_no = escape(application_no)
        safe_customer_phone = escape(customer_phone)
        safe_customer_address = escape(customer_address)
        safe_tracking_url = escape(tracking_url)
        body = Markup("""
            <p>Dear %s,</p>
            <p>Thank you for choosing our solar service.</p>
            <p>Your application has been successfully registered.</p>
            <p><strong>Application Details:</strong></p>
            <ul>
                <li><strong>Application No:</strong> %s</li>
                <li><strong>Customer Name:</strong> %s</li>
                <li><strong>Phone:</strong> %s</li>
                <li><strong>Address:</strong> %s</li>
            </ul>
            <p><strong>Track Your Application:</strong><br/>
                Click below to view full project details and progress:
            </p>
            <p><a href="%s" target="_blank">%s</a></p>
            <p>If you find any issue, you can report it to our team.</p>
            <p>Thank you,<br/>Solar Team</p>
        """) % (
            safe_customer_name,
            safe_application_no,
            safe_customer_name,
            safe_customer_phone,
            safe_customer_address,
            safe_tracking_url,
            safe_tracking_url,
        )
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'res_model': 'mail.compose.message',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_model': 'crm.lead',
                'default_res_ids': [self.id],
                'default_composition_mode': 'comment',
                'default_email_to': email_to,
                'default_subject': _('Solar Application Registered - %s') % application_no,
                'default_body': body,
            },
        }

    def action_view_site_inspections(self):
        self.ensure_one()
        return {
            'name': 'Site Inspections',
            'type': 'ir.actions.act_window',
            'res_model': 'solar.site.inspection',
            'view_mode': 'list,form',
            'domain': [('lead_id', '=', self.id)],
            'context': {
                'default_lead_id': self.id,
                'default_partner_id': self.partner_id.id
            },
        }

    def action_create_site_inspection(self):
        self.ensure_one()
        self._validate_required_documents_for_inspection()
        inspection = self.env['solar.site.inspection'].search(
            [('lead_id', '=', self.id)],
            limit=1,
            order='id desc',
        )

        if inspection:
            self._set_solar_crm_stage_proposition()
            return {
                'name': 'Site Inspection',
                'type': 'ir.actions.act_window',
                'res_model': 'solar.site.inspection',
                'view_mode': 'form',
                'res_id': inspection.id,
                'target': 'current',
            }

        return {
            'name': 'Create Site Inspection',
            'type': 'ir.actions.act_window',
            'res_model': 'solar.site.inspection.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_lead_id': self.id,
                'default_inspection_date': fields.Date.context_today(self),
            },
        }

    def action_view_installations(self):
        self.ensure_one()
        return {
            'name': 'Installations',
            'type': 'ir.actions.act_window',
            'res_model': 'solar.installation',
            'view_mode': 'list,form',
            'domain': [('lead_id', '=', self.id)],
            'context': {
                'default_lead_id': self.id,
                'default_project_manager_id': self.env.user.id,
            },
        }

    def action_view_government_approval(self):
        self.ensure_one()
        approval = self.env['solar.government.approval'].search([
            ('lead_id', '=', self.id),
        ], limit=1)
        action = {
            'name': 'SSEG Application',
            'type': 'ir.actions.act_window',
            'res_model': 'solar.government.approval',
            'view_mode': 'list,form',
            'domain': [('lead_id', '=', self.id)],
            'context': {
                'default_lead_id': self.id,
            },
        }
        if approval:
            action.update({
                'view_mode': 'form',
                'res_id': approval.id,
            })
        return action

    def action_view_designs(self):
        self.ensure_one()
        return {
            'name': 'Solar Designs',
            'type': 'ir.actions.act_window',
            'res_model': 'solar.design',
            'view_mode': 'list,form',
            'domain': [('lead_id', '=', self.id)],
            'context': {
                'default_lead_id': self.id,
                'default_partner_id': self.partner_id.id,
            },
        }

    def action_view_project(self):
        self.ensure_one()
        if not self.project_id:
            self._create_solar_projects()
        if self.project_id:
            return {
                'name': 'Project',
                'type': 'ir.actions.act_window',
                'res_model': 'project.project',
                'view_mode': 'form',
                'res_id': self.project_id.id,
                'target': 'current',
            }
        return {}

    def action_create_installation(self):
        self.ensure_one()
        return {
            'name': 'Create Installation',
            'type': 'ir.actions.act_window',
            'res_model': 'solar.installation',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_lead_id': self.id,
                'default_project_manager_id': self.env.user.id,
            },
        }

    def name_get(self):
        result = []
        for lead in self:
            if lead.solar_reference and lead.solar_reference != 'New':
                display_name = lead.solar_reference
            else:
                display_name = lead.name or ''
            result.append((lead.id, display_name))
        return result

    @api.depends('solar_reference', 'name')
    def _compute_display_name(self):
        for lead in self:
            if lead.solar_reference and lead.solar_reference != 'New':
                lead.display_name = lead.solar_reference
            else:
                lead.display_name = lead.name or ''

    # -------------------------
    # Sequence Generate
    # -------------------------
    @api.model
    def _generate_access_token(self, length=10):
        alphabet = string.ascii_lowercase + string.digits
        while True:
            token = ''.join(secrets.choice(alphabet) for _ in range(length))
            if not self.sudo().search_count([('access_token', '=', token)]):
                return token

    def _assign_access_token_if_needed(self):
        for lead in self:
            if lead.type == 'opportunity' and not lead.access_token:
                lead.access_token = self._generate_access_token()

    def _create_solar_projects(self):
        for lead in self:
            if lead.type == 'opportunity' and not lead.project_id:
                project_name = lead.name or 'Solar Project'
                project = self.env['project.project'].sudo().search([
                    ('name', '=', project_name), ('partner_id', '=', lead.partner_id.id)
                ], limit=1)
                if not project:
                    project = self.env['project.project'].sudo().create({
                        'name': project_name,
                        'partner_id': lead.partner_id.id,
                        'user_id': lead.user_id.id or self.env.user.id,
                        'lead_id': lead.id,
                    })
                lead.sudo().write({'project_id': project.id})

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('renewable_reference') and not vals.get('solar_reference'):
                vals['solar_reference'] = vals['renewable_reference']

            if not vals.get('solar_reference') or vals.get('solar_reference') == 'New':
                vals['solar_reference'] = self.env['ir.sequence'].next_by_code(
                    'crm.lead.renewable'
                ) or 'New'

        leads = super().create(vals_list)
        leads._assign_access_token_if_needed()
        leads.filtered(lambda lead: lead.type == 'lead')._set_solar_crm_stage_new()
        leads._sync_dynamic_document_lines()
        leads._sync_solar_stage_from_documents()
        return leads

    def write(self, vals):
        res = super().write(vals)
        if 'type' in vals and vals.get('type') == 'opportunity':
            self._assign_access_token_if_needed()
            self._sync_dynamic_document_lines()
            # Sync stage so already-uploaded docs are reflected after conversion
            self._sync_solar_stage_from_documents()
        if vals.get('renewable_gov_application_number'):
            self._set_solar_crm_stage_won()
        if 'solar_document_line_ids' in vals:
            self._sync_solar_stage_from_documents()
        if any(field in vals for field in (
            'electric_bill',
            'id_proof_type',
            'id_proof',
            'ownership_proof',
            'bank_cancel_cheque',
            'passport_size_photo',
        )):
            self._sync_dynamic_document_lines()
            self._sync_solar_stage_from_documents()
        return res
