# -- encoding: utf-8 --
###############################################################################
#
# Copyright (C) 2022-Present Speeduplight (https://speeduplight.com/)
#
###############################################################################
from thrive import _, api, fields, models
from thrive.exceptions import ValidationError


class SolarDesign(models.Model):
    _name = 'solar.design'
    _description = 'Solar Design Proposal'
    _order = 'id desc'
    _rec_name = 'design_number'
    _design_number_unique = models.Constraint(
        'UNIQUE(design_number)',
        'Design Number must be unique.'
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

    design_number = fields.Char(string='Design Number', required=True, copy=False, readonly=True, default='New')

    lead_id = fields.Many2one(
        'crm.lead',
        string='Lead',
        required=True,
        ondelete='cascade',
    )
    project_id = fields.Many2one(
        'project.project',
        string='Project',
        compute='_compute_project_id',
        store=True,
        readonly=False,
    )
    project_count = fields.Integer(compute='_compute_project_count')
    inspection_id = fields.Many2one(
        'solar.site.inspection',
        string='Site Inspection',
        ondelete='set null',
        domain="[('lead_id', '=', lead_id)]",
    )
    template_id = fields.Many2one(
        'solar.material.template',
        string='System Template',
        domain="[('expected_generation_kwh_month', '>=', current_electricity_consumption), ('system_size', '>=', contract_demand_kw)]",
    )
    system_size = fields.Float(string='System Size (kW)')
    expected_generation_kwh_month = fields.Float(string='Expected Generation (kWh/month)')
    current_electricity_consumption = fields.Float(
        related='lead_id.renewable_monthly_electricity_consumption',
        string='Current Electricity Consumption (kWh/month)',
        store=True,
        readonly=True,
    )
    contract_demand_kw = fields.Float(
        related='lead_id.renewable_contract_demand_kw',
        string='Contract Demand (kW)',
        store=True,
        readonly=True,
    )
    design_status = fields.Selection(
        [
            ('draft', 'Draft'),
            ('submitted', 'Submitted'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
        ],
        string='Design Status',
        default='draft',
        required=True,
    )
    system_type = fields.Selection(
        [
            ('on_grid', 'On-Grid'),
            ('off_grid', 'Off-Grid'),
            ('hybrid', 'Hybrid'),
        ],
        string='System Type',
    )
    solar_panel_type = fields.Selection(
        [
            ('mono', 'Monocrystalline Solar Panels (Mono-SI)'),
            ('poly', 'Polycrystalline Solar Panels (p-Si)'),
            ('thin_film', 'Thin-Film: Amorphous Silicon Solar Panels (A-SI)'),
            ('cvp', 'Concentrated PV Cell (CVP)'),
        ],
        string='Solar Panel Type',
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
    )
    currency_id = fields.Many2one(
        'res.currency',
        related='company_id.currency_id',
        readonly=True,
    )
    quotation_count = fields.Integer(compute='_compute_quotation_count')
    has_confirmed_quotation = fields.Boolean(compute='_compute_has_confirmed_quotation', string='Has Confirmed Quotation')
    installation_count = fields.Integer(compute='_compute_installation_count')
    line_ids = fields.One2many(
        'solar.design.line',
        compute='_compute_line_ids',
        string='Product Configuration',
    )
    document_ids = fields.One2many(
        'solar.design.document',
        'design_id',
        string='Design Plans ',
    )
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'solar_design_attachment_rel',
        'design_id',
        'attachment_id',
        string='Documents',
    )

    installation_cost = fields.Monetary(string='Installation Cost', currency_field='currency_id')
    transportation_distance_km = fields.Float(string='Transportation Distance (KM)')
    transport_cost = fields.Monetary(string='Transport Cost', currency_field='currency_id')
    task_ids = fields.One2many(
        'solar.design.task',
        'design_id',
        string='Project Tasks',
    )

    # ROI Fields
    total_system_cost = fields.Monetary(
        string='System Cost',
        currency_field='currency_id',
        compute='_compute_total_system_cost',
        store=True,
    )
    vat_percent = fields.Float(
        string='VAT (%)',
    )
    vat_amount = fields.Monetary(
        string='VAT',
        currency_field='currency_id',
        compute='_compute_vat_and_total',
    )
    total_cost = fields.Monetary(
        string='Total Cost',
        currency_field='currency_id',
        compute='_compute_vat_and_total',
    )
    electricity_rate = fields.Monetary(
        string='Electricity Rate (per kWh)',
        currency_field='currency_id',
        default=0.25,
        help="Cost of grid electricity per kWh to calculate savings."
    )
    monthly_savings_kwh = fields.Float(
        string='Monthly Savings (kWh)',
        compute='_compute_monthly_savings_kwh',
    )
    monthly_savings = fields.Monetary(
        string='Monthly Savings',
        currency_field='currency_id',
        compute='_compute_savings_amounts',
    )
    annual_savings = fields.Monetary(
        string='Annual Savings',
        currency_field='currency_id',
        compute='_compute_savings_amounts',
    )
    payback_period = fields.Float(
        string='Payback Period (Years)',
        compute='_compute_payback_and_roi',
    )
    roi_percent = fields.Float(
        string='ROI (%)',
        compute='_compute_payback_and_roi',
    )
    system_lifetime = fields.Integer(
        string='System Lifetime (Years)',
    )
    lifetime_savings = fields.Monetary(
        string='Savings',
        currency_field='currency_id',
        compute='_compute_lifetime_savings',
    )


    @api.depends('solar_panel_line_ids', 'battery_line_ids', 'inverter_line_ids', 'other_line_ids')
    def _compute_line_ids(self):
        for rec in self:
            rec.line_ids = rec.solar_panel_line_ids + rec.battery_line_ids + rec.inverter_line_ids + rec.other_line_ids

    solar_panel_line_ids = fields.One2many(
        'solar.design.line',
        'solar_panel_design_id',
        string='Solar Panels',
    )
    battery_line_ids = fields.One2many(
        'solar.design.line',
        'battery_design_id',
        string='Batteries',
    )
    inverter_line_ids = fields.One2many(
        'solar.design.line',
        'inverter_design_id',
        string='Inverters',
    )
    other_line_ids = fields.One2many(
        'solar.design.line',
        'other_design_id',
        string='Other Components',
    )



    @api.depends('solar_panel_line_ids.subtotal', 'battery_line_ids.subtotal', 'inverter_line_ids.subtotal', 'other_line_ids.subtotal', 'installation_cost', 'transport_cost')
    def _compute_total_system_cost(self):
        for rec in self:
            panels = sum(rec.solar_panel_line_ids.mapped('subtotal'))
            batteries = sum(rec.battery_line_ids.mapped('subtotal'))
            inverters = sum(rec.inverter_line_ids.mapped('subtotal'))
            others = sum(rec.other_line_ids.mapped('subtotal'))
            rec.total_system_cost = panels + batteries + inverters + others + rec.installation_cost + rec.transport_cost

    @api.depends('current_electricity_consumption', 'expected_generation_kwh_month')
    def _compute_monthly_savings_kwh(self):
        for rec in self:
            rec.monthly_savings_kwh = (rec.expected_generation_kwh_month or 0.0) - (rec.current_electricity_consumption or 0.0)

    @api.depends('total_system_cost', 'vat_percent')
    def _compute_vat_and_total(self):
        for rec in self:
            rec.vat_amount = rec.total_system_cost * (rec.vat_percent / 100.0)
            rec.total_cost = rec.total_system_cost + rec.vat_amount

    @api.depends('monthly_savings_kwh', 'electricity_rate')
    def _compute_savings_amounts(self):
        for rec in self:
            rec.monthly_savings = rec.monthly_savings_kwh * rec.electricity_rate
            rec.annual_savings = rec.monthly_savings * 12.0

    @api.depends('total_cost', 'annual_savings')
    def _compute_payback_and_roi(self):
        for rec in self:
            rec.payback_period = rec.total_cost / rec.annual_savings if rec.annual_savings > 0.0 else 0.0
            rec.roi_percent = (rec.annual_savings / rec.total_cost) * 100.0 if rec.total_cost > 0.0 else 0.0

    @api.depends('annual_savings', 'system_lifetime')
    def _compute_lifetime_savings(self):
        for rec in self:
            rec.lifetime_savings = rec.annual_savings * rec.system_lifetime



    @api.model
    def _get_generation_from_size(self, system_size):
        return (system_size or 0.0) * 4.0 * 30.0 * 0.8

    def _compute_installation_count(self):
        for design in self:
            design.installation_count = self.env['solar.installation'].sudo().search_count([
                ('design_id', '=', design.id)
            ])

    def _compute_quotation_count(self):
        for design in self:
            design.quotation_count = self.env['sale.order'].search_count([
                ('solar_design_id', '=', design.id)
            ])

    def _compute_has_confirmed_quotation(self):
        for design in self:
            confirmed_quotes = self.env['sale.order'].search_count([
                ('solar_design_id', '=', design.id),
                ('state', '=', 'sale'),
            ])
            design.has_confirmed_quotation = confirmed_quotes > 0

    @api.depends('lead_id.project_id')
    def _compute_project_id(self):
        for rec in self:
            rec.project_id = rec.lead_id.project_id or False

    @api.depends('project_id')
    def _compute_project_count(self):
        for rec in self:
            rec.project_count = 1 if rec.project_id else 0

    def action_view_project(self):
        self.ensure_one()
        if not self.project_id:
            if self.lead_id:
                if not self.lead_id.project_id:
                    self.lead_id._create_solar_projects()
                self.project_id = self.lead_id.project_id
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

    @api.onchange('template_id')
    def _onchange_template_id(self):
        for design in self:
            if not design.template_id:
                continue
            template = design.template_id
            design.system_size = template.system_size
            design.expected_generation_kwh_month = template.expected_generation_kwh_month
            design.system_type = template.system_type
            design.solar_panel_line_ids = [(5, 0, 0)] + [
                (0, 0, {
                    'sequence': line.sequence,
                    'product_id': line.product_id.id,
                    'name': line.name or line.product_id.display_name,
                    'quantity': line.quantity,
                    'uom_id': line.uom_id.id,
                    'unit_cost': line.unit_cost,
                    'line_type': 'solar_panel',
                })
                for line in template.solar_panel_line_ids.sorted(lambda rec: (rec.sequence, rec.id))
            ]
            design.battery_line_ids = [(5, 0, 0)] + [
                (0, 0, {
                    'sequence': line.sequence,
                    'product_id': line.product_id.id,
                    'name': line.name or line.product_id.display_name,
                    'quantity': line.quantity,
                    'uom_id': line.uom_id.id,
                    'unit_cost': line.unit_cost,
                    'line_type': 'battery',
                })
                for line in template.battery_line_ids.sorted(lambda rec: (rec.sequence, rec.id))
            ]
            design.inverter_line_ids = [(5, 0, 0)] + [
                (0, 0, {
                    'sequence': line.sequence,
                    'product_id': line.product_id.id,
                    'name': line.name or line.product_id.display_name,
                    'quantity': line.quantity,
                    'uom_id': line.uom_id.id,
                    'unit_cost': line.unit_cost,
                    'line_type': 'inverter',
                })
                for line in template.inverter_line_ids.sorted(lambda rec: (rec.sequence, rec.id))
            ]
            design.other_line_ids = [(5, 0, 0)] + [
                (0, 0, {
                    'sequence': line.sequence,
                    'product_id': line.product_id.id,
                    'name': line.name or line.product_id.display_name,
                    'quantity': line.quantity,
                    'uom_id': line.uom_id.id,
                    'unit_cost': line.unit_cost,
                    'line_type': 'other',
                })
                for line in template.other_line_ids.sorted(lambda rec: (rec.sequence, rec.id))
            ]
            design.task_ids = [(5, 0, 0)] + [
                (0, 0, {
                    'sequence': task.sequence,
                    'name': task.name,
                })
                for task in template.task_ids.sorted(lambda rec: (rec.sequence, rec.id))
            ]



    def _sync_lead_solar_stage(self):
        stage_sequence = [
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
        next_stage_index = stage_sequence.index('government_approval')
        for design in self.filtered(lambda rec: rec.design_status == 'approved' and rec.lead_id):
            lead_sudo = design.lead_id.sudo()
            current_stage_index = stage_sequence.index(lead_sudo.solar_stage or 'document_pending')
            if current_stage_index < next_stage_index:
                lead_sudo.write({'solar_stage': 'government_approval'})



    def action_submit_for_approval(self):
        for rec in self:
            if rec.design_status != 'draft':
                raise ValidationError(_('Only draft designs can be submitted for approval.'))
            rec.write({'design_status': 'submitted'})

    def action_approve(self):
        for rec in self:
            if rec.design_status != 'submitted':
                raise ValidationError(_('Only submitted designs can be approved.'))
            rec.with_context(allow_finalized_write=True).write({'design_status': 'approved'})
            rec._sync_lead_solar_stage()
            
            project = rec.project_id
            if not project and rec.lead_id:
                rec.lead_id._create_solar_projects()
                project = rec.lead_id.project_id
            if not project:
                project_name = rec.name or 'Solar Design Project'
                project = self.env['project.project'].sudo().create({
                    'name': project_name,
                    'partner_id': rec.partner_id.id or (rec.lead_id and rec.lead_id.partner_id.id),
                    'user_id': rec.user_id.id or self.env.user.id,
                })
                if rec.lead_id:
                    rec.lead_id.sudo().write({'project_id': project.id})
            
            if project:
                for task in rec.task_ids:
                    if not task.project_task_id:
                        project_task = self.env['project.task'].sudo().create({
                            'name': task.name,
                            'project_id': project.id,
                            'user_ids': [(6, 0, task.user_ids.ids)] if task.user_ids else False,
                            'sequence': task.sequence,
                        })
                        task.project_task_id = project_task.id

    def action_reject(self):
        for rec in self:
            if rec.design_status != 'submitted':
                raise ValidationError(_('Only submitted designs can be rejected.'))
            rec.write({'design_status': 'rejected'})

    def action_reset_to_draft(self):
        for rec in self:
            if rec.design_status == 'draft':
                continue
            rec.with_context(allow_finalized_write=True).write({'design_status': 'draft'})

    def action_create_quotation(self):
        self.ensure_one()
        if self.design_status != 'approved':
            raise ValidationError(_('Please approve the design before creating a quotation.'))
        order_lines = []
        sections = [
            ('solar_panel', _('Solar Panel')),
            ('battery', _('Battery')),
            ('inverter', _('Inverter')),
            ('other', _('Others Equipment')),
        ]
        for line_type, section_title in sections:
            lines = self.line_ids.filtered(lambda l: l.line_type == line_type)
            if lines:
                order_lines.append((0, 0, {
                    'display_type': 'line_section',
                    'name': section_title,
                }))
                for line in lines:
                    order_lines.append((0, 0, {
                        'product_id': line.product_id.id,
                        'name': line.name or line.product_id.display_name,
                        'product_uom_qty': line.quantity,
                        'product_uom_id': line.uom_id.id,
                        'price_unit': line.unit_cost,
                    }))

        # Add Services & Charges section if either cost is set
        if self.installation_cost > 0 or self.transport_cost > 0:
            order_lines.append((0, 0, {
                'display_type': 'line_section',
                'name': _('Installation & Transport Cost'),
            }))

            if self.installation_cost > 0:
                installation_product = self.env['product.product'].search([
                    ('default_code', '=', 'SOLAR_INSTALL_SERVICE')
                ], limit=1)
                if installation_product:
                    installation_product.write({
                        'name': _('Installation Cost'),
                        'default_code': False,
                    })
                else:
                    installation_product = self.env['product.product'].search([
                        ('name', '=', 'Installation Cost'),
                        ('type', '=', 'service')
                    ], limit=1)
                    if not installation_product:
                        installation_product = self.env['product.product'].create({
                            'name': _('Installation Cost'),
                            'type': 'service',
                            'invoice_policy': 'order',
                        })
                order_lines.append((0, 0, {
                    'product_id': installation_product.id,
                    'name': _('Installation Cost'),
                    'product_uom_qty': 1,
                    'price_unit': self.installation_cost,
                }))

            if self.transport_cost > 0:
                transport_product = self.env['product.product'].search([
                    ('default_code', '=', 'SOLAR_TRANSPORT_SERVICE')
                ], limit=1)
                if transport_product:
                    transport_product.write({
                        'name': _('Transport Cost'),
                        'default_code': False,
                    })
                else:
                    transport_product = self.env['product.product'].search([
                        ('name', '=', 'Transport Cost'),
                        ('type', '=', 'service')
                    ], limit=1)
                    if not transport_product:
                        transport_product = self.env['product.product'].create({
                            'name': _('Transport Cost'),
                            'type': 'service',
                            'invoice_policy': 'order',
                        })
                order_lines.append((0, 0, {
                    'product_id': transport_product.id,
                    'name': _('Transport Cost'),
                    'product_uom_qty': 1,
                    'price_unit': self.transport_cost,
                }))

        # Find or create a pricelist in the company's currency
        company_currency = self.company_id.currency_id or self.env.company.currency_id
        pricelist = self.env['product.pricelist'].search([
            ('currency_id', '=', company_currency.id)
        ], limit=1)
        if not pricelist:
            pricelist = self.env['product.pricelist'].create({
                'name': f'Default ({company_currency.name})',
                'currency_id': company_currency.id,
            })

        return {
            'name': _('Create Quotation'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_partner_id': self.lead_id.partner_id.id,
                'default_opportunity_id': self.lead_id.id,
                'default_solar_design_id': self.id,
                'default_pricelist_id': pricelist.id,
                'default_order_line': order_lines,
            },
        }

    def action_view_quotations(self):
        self.ensure_one()
        return {
            'name': _('Quotations'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'list,form',
            'domain': [('solar_design_id', '=', self.id)],
            'context': {
                'default_partner_id': self.lead_id.partner_id.id,
                'default_opportunity_id': self.lead_id.id,
                'default_solar_design_id': self.id,
            },
            'target': 'current',
        }

    def action_create_installation(self):
        self.ensure_one()
        if self.design_status != 'approved':
            raise ValidationError(_('Please approve the design before creating an installation.'))
        existing_installation = self.env['solar.installation'].search([
            ('design_id', '=', self.id)
        ], limit=1, order='id desc')
        if existing_installation:
            return self.action_view_installation()
        return {
            'name': _('Create Installation'),
            'type': 'ir.actions.act_window',
            'res_model': 'solar.installation.create.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_design_id': self.id,
            },
        }

    def action_view_installation(self):
        self.ensure_one()
        installation_records = self.env['solar.installation'].search([
            ('design_id', '=', self.id)
        ], order='id desc')
        if len(installation_records) == 1:
            return {
                'name': _('Installation'),
                'type': 'ir.actions.act_window',
                'res_model': 'solar.installation',
                'view_mode': 'form',
                'res_id': installation_records.id,
                'target': 'current',
            }
        return {
            'name': _('Installations'),
            'type': 'ir.actions.act_window',
            'res_model': 'solar.installation',
            'view_mode': 'list,form',
            'domain': [('design_id', '=', self.id)],
            'context': {
                'default_lead_id': self.lead_id.id,
                'default_design_id': self.id,
            },
            'target': 'current',
        }

    def action_view_documents(self):
        self.ensure_one()
        return {
            'name': _('Documents'),
            'type': 'ir.actions.act_window',
            'res_model': 'solar.design.document',
            'view_mode': 'list,form',
            'domain': [('design_id', '=', self.id)],
            'context': {
                'default_design_id': self.id,
            },
            'target': 'current',
        }



    def write(self, vals):
        if not self.env.context.get('allow_finalized_write'):
            if self.filtered(lambda design: design.design_status != 'draft'):
                raise ValidationError(_('Only designs in Draft state can be modified.'))
        return super().write(vals)

    def unlink(self):
        if self.filtered(lambda design: design.design_status != 'draft'):
            raise ValidationError(_('Only designs in Draft state can be deleted.'))
        return super().unlink()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('design_number', 'New') == 'New':
                vals['design_number'] = self.env['ir.sequence'].next_by_code('solar.design') or 'New'
        return super().create(vals_list)


class SolarDesignLine(models.Model):
    _name = 'solar.design.line'
    _description = 'Solar Design Product Line'
    _order = 'sequence, id'

    sequence = fields.Integer(default=10)
    design_id = fields.Many2one(
        'solar.design',
        string='Design',
        compute='_compute_design_id',
        store=True,
        readonly=False,
        ondelete='cascade',
    )
    solar_panel_design_id = fields.Many2one(
        'solar.design',
        string='Solar Panel Design',
        ondelete='cascade',
    )
    battery_design_id = fields.Many2one(
        'solar.design',
        string='Battery Design',
        ondelete='cascade',
    )
    inverter_design_id = fields.Many2one(
        'solar.design',
        string='Inverter Design',
        ondelete='cascade',
    )
    other_design_id = fields.Many2one(
        'solar.design',
        string='Other Design',
        ondelete='cascade',
    )

    @api.depends('solar_panel_design_id', 'battery_design_id', 'inverter_design_id', 'other_design_id')
    def _compute_design_id(self):
        for line in self:
            line.design_id = (
                line.solar_panel_design_id or
                line.battery_design_id or
                line.inverter_design_id or
                line.other_design_id
            )
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True,
    )
    line_type = fields.Selection(
        [
            ('solar_panel', 'Solar Panel'),
            ('battery', 'Battery'),
            ('inverter', 'Inverter'),
            ('other', 'Other'),
        ],
        string='Component Type',
        default='other',
        required=True,
    )
    name = fields.Char(
        string='Description',
        compute='_compute_name',
        store=True,
        readonly=False,
    )
    quantity = fields.Float(string='Quantity', default=1.0)
    uom_id = fields.Many2one(
        'uom.uom',
        string='Unit of Measure',
        compute='_compute_uom_id',
        store=True,
        readonly=False,
    )
    unit_cost = fields.Float(
        string='Unit Price',
        digits='Product Price',
        compute='_compute_unit_cost',
        store=True,
        readonly=False,
    )
    subtotal = fields.Monetary(
        string='Subtotal',
        currency_field='currency_id',
        compute='_compute_subtotal',
        store=True,
    )
    currency_id = fields.Many2one(
        'res.currency',
        related='design_id.currency_id',
        readonly=True,
    )

    @api.depends('product_id')
    def _compute_name(self):
        for line in self:
            if not line.name and line.product_id:
                line.name = line.product_id.display_name

    @api.depends('product_id')
    def _compute_uom_id(self):
        for line in self:
            if line.product_id:
                line.uom_id = line.product_id.uom_id

    @api.depends('product_id')
    def _compute_unit_cost(self):
        for line in self:
            if line.product_id:
                line.unit_cost = line.product_id.lst_price
            else:
                line.unit_cost = 0.0

    @api.depends('quantity', 'unit_cost')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = (line.quantity or 0.0) * (line.unit_cost or 0.0)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            design = self.env['solar.design'].browse(vals.get('design_id'))
            if design and design.design_status != 'draft':
                raise ValidationError(_('You cannot add product lines to a finalized design.'))
        return super().create(vals_list)

    def write(self, vals):
        if self.filtered(lambda line: line.design_id.design_status != 'draft'):
            raise ValidationError(_('You cannot modify product lines on a finalized design.'))
        return super().write(vals)

    def unlink(self):
        if self.filtered(lambda line: line.design_id.design_status != 'draft'):
            raise ValidationError(_('You cannot delete product lines from a finalized design.'))
        return super().unlink()


class SolarDesignDocument(models.Model):
    _name = 'solar.design.document'
    _description = 'Solar Design Document'
    _order = 'id'

    design_id = fields.Many2one(
        'solar.design',
        string='Design',
        required=True,
        ondelete='cascade',
        index=True,
    )
    name = fields.Char(string='Document Name', required=True)
    document_file = fields.Binary(string='Upload File', attachment=True, required=True)
    document_filename = fields.Char(string='Filename')

    def action_view_document(self):
        self.ensure_one()
        if not self.document_file:
            raise ValidationError(_('No file is uploaded for this document.'))
        return {
            'type': 'ir.actions.act_url',
            'url': (
                '/web/content?model=solar.design.document&id=%s&field=document_file&filename_field=document_filename&download=false'
                % self.id
            ),
            'target': 'new',
        }


class SolarDesignTask(models.Model):
    _name = 'solar.design.task'
    _description = 'Solar Design Task'
    _order = 'sequence, id'

    sequence = fields.Integer(default=10)
    design_id = fields.Many2one('solar.design', string='Design', ondelete='cascade')
    name = fields.Char(string='Title', required=True)
    user_ids = fields.Many2many('res.users', string='Assignees')
    project_task_id = fields.Many2one('project.task', string='Project Task', readonly=True, ondelete='set null')



