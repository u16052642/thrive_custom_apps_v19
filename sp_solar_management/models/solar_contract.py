# -- encoding: utf-8 --
###############################################################################
#
# Copyright (C) 2022-Present Speeduplight (https://speeduplight.com/)
#
###############################################################################
from thrive import _, api, fields, models
from dateutil.relativedelta import relativedelta

class SolarContract(models.Model):
    _name = 'solar.contract'
    _description = 'Solar Contract Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'start_date desc, id desc'
    _rec_name = 'contract_id'

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

    contract_id = fields.Char(
        string='Contract ID',
        required=True,
        copy=False,
        readonly=True,
        default='New',
    )
    lead_id = fields.Many2one(
        'crm.lead',
        string='Application / Project',
        required=False,
        ondelete='cascade',
        index=True,
        tracking=True,
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        tracking=True,
    )
    contract_type_id = fields.Many2one(
        'solar.contract.type',
        string='Contract Type',
        tracking=True,
    )
    project_id = fields.Many2one(
        'project.project',
        string='Project',
        tracking=True,
    )
    installation_id = fields.Many2one(
        'solar.installation',
        string='Installation',
        domain="[('partner_id', '=', partner_id)]",
        tracking=True,
    )
    sale_order_id = fields.Many2one(
        'sale.order',
        string='Sales Order',
        tracking=True,
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
    )
    start_date = fields.Date(string='Start Date', tracking=True)
    end_date = fields.Date(string='Expiration Date', tracking=True)
    days_left = fields.Integer(
        string='Days Left',
        compute='_compute_days_left',
    )
    contract_amount = fields.Float(
        string='Contract Amount',
        tracking=True,
    )
    cost_frequency = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annually', 'Annually'),
    ], string='Cost Frequency', default='monthly', tracking=True)
    auto_renew = fields.Boolean(string='Auto Renew', default=False, tracking=True)
    status = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('expired', 'Expired'),
    ], string='Status', default='draft', required=True, tracking=True)

    service_ids = fields.Many2many(
        'solar.contract.service',
        string='Included Services',
    )
    terms_and_conditions = fields.Html(string='Terms & Conditions')
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'solar_contract_attachment_rel',
        'contract_id',
        'attachment_id',
        string='Attachments',
    )
    notes = fields.Text(string='Notes')

    _contract_id_unique = models.Constraint(
        'UNIQUE(contract_id)',
        'Contract ID must be unique.'
    )

    @api.onchange('lead_id')
    def _onchange_lead_id(self):
        if self.lead_id:
            if self.lead_id.partner_id:
                self.partner_id = self.lead_id.partner_id.id
            if self.lead_id.project_id:
                self.project_id = self.lead_id.project_id.id

    @api.onchange('project_id')
    def _onchange_project_id(self):
        if self.project_id and self.project_id.partner_id:
            self.partner_id = self.project_id.partner_id.id

    @api.onchange('installation_id')
    def _onchange_installation_id(self):
        if self.installation_id:
            if self.installation_id.partner_id:
                self.partner_id = self.installation_id.partner_id.id
            if self.installation_id.project_id:
                self.project_id = self.installation_id.project_id.id

    @api.depends('end_date', 'status', 'auto_renew', 'cost_frequency')
    def _compute_days_left(self):
        today = fields.Date.today()
        for rec in self:
            if rec.end_date:
                if rec.status == 'active' and rec.end_date < today:
                    if not rec.auto_renew:
                        rec.status = 'expired'
                        rec.days_left = (rec.end_date - today).days
                    else:
                        new_start = rec.end_date + relativedelta(days=1)
                        if rec.cost_frequency == 'monthly':
                            new_end = new_start + relativedelta(months=1) - relativedelta(days=1)
                        elif rec.cost_frequency == 'quarterly':
                            new_end = new_start + relativedelta(months=3) - relativedelta(days=1)
                        elif rec.cost_frequency == 'annually':
                            new_end = new_start + relativedelta(years=1) - relativedelta(days=1)
                        else:
                            new_end = new_start
                        
                        rec.start_date = new_start
                        rec.end_date = new_end
                        rec.days_left = (new_end - today).days
                else:
                    rec.days_left = (rec.end_date - today).days
            else:
                rec.days_left = 0

    @api.model
    def _cron_check_contract_expiry(self):
        today = fields.Date.today()
        contracts = self.search([('status', '=', 'active'), ('end_date', '<', today)])
        for rec in contracts:
            if not rec.auto_renew:
                rec.write({'status': 'expired'})
            else:
                new_start = rec.end_date + relativedelta(days=1)
                if rec.cost_frequency == 'monthly':
                    new_end = new_start + relativedelta(months=1) - relativedelta(days=1)
                elif rec.cost_frequency == 'quarterly':
                    new_end = new_start + relativedelta(months=3) - relativedelta(days=1)
                elif rec.cost_frequency == 'annually':
                    new_end = new_start + relativedelta(years=1) - relativedelta(days=1)
                else:
                    new_end = new_start
                
                rec.write({
                    'start_date': new_start,
                    'end_date': new_end,
                })

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('contract_id', 'New') == 'New':
                vals['contract_id'] = self.env['ir.sequence'].next_by_code('solar.contract') or 'New'
        return super().create(vals_list)

    def action_activate(self):
        for rec in self:
            rec.write({'status': 'active'})
        return True

    def action_renew(self):
        for rec in self:
            if rec.status == 'expired':
                new_start = (rec.end_date or fields.Date.today()) + relativedelta(days=1)
                if rec.cost_frequency == 'monthly':
                    new_end = new_start + relativedelta(months=1) - relativedelta(days=1)
                elif rec.cost_frequency == 'quarterly':
                    new_end = new_start + relativedelta(months=3) - relativedelta(days=1)
                elif rec.cost_frequency == 'annually':
                    new_end = new_start + relativedelta(years=1) - relativedelta(days=1)
                else:
                    new_end = new_start
                
                rec.write({
                    'start_date': new_start,
                    'end_date': new_end,
                    'status': 'active',
                })
        return True

    def action_expire(self):
        for rec in self:
            rec.write({'status': 'expired'})
        return True

    def action_view_lead(self):
        self.ensure_one()
        if not self.lead_id:
            return {}
        return {
            'name': _('Lead'),
            'type': 'ir.actions.act_window',
            'res_model': 'crm.lead',
            'view_mode': 'form',
            'res_id': self.lead_id.id,
            'target': 'current',
        }

    def action_view_project(self):
        self.ensure_one()
        if not self.project_id:
            return {}
        return {
            'name': _('Project'),
            'type': 'ir.actions.act_window',
            'res_model': 'project.project',
            'view_mode': 'form',
            'res_id': self.project_id.id,
            'target': 'current',
        }

    def action_view_installation(self):
        self.ensure_one()
        if not self.installation_id:
            return {}
        return {
            'name': _('Installation'),
            'type': 'ir.actions.act_window',
            'res_model': 'solar.installation',
            'view_mode': 'form',
            'res_id': self.installation_id.id,
            'target': 'current',
        }


class SolarContractType(models.Model):
    _name = 'solar.contract.type'
    _description = 'Solar Contract Type'
    _order = 'sequence, id'

    name = fields.Char(string='Name', required=True, translate=True)
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)


class SolarContractService(models.Model):
    _name = 'solar.contract.service'
    _description = 'Solar Contract Service'
    _order = 'sequence, id'

    name = fields.Char(string='Name', required=True, translate=True)
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)
