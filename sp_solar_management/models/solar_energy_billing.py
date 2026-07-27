# -- encoding: utf-8 --
###############################################################################
#
# Copyright (C) 2022-Present Speeduplight (https://speeduplight.com/)
#
###############################################################################
from thrive import _, api, fields, models
from thrive.exceptions import UserError

class SolarEnergyBilling(models.Model):
    _name = 'solar.energy.billing'
    _description = 'Solar Energy Billing'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(
        string='Billing Reference',
        required=True,
        copy=False,
        readonly=True,
        default='New',
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        tracking=True,
    )
    project_id = fields.Many2one(
        'project.project',
        string='Project',
        domain="[('partner_id', '=', partner_id)]",
        tracking=True,
    )
    installation_id = fields.Many2one(
        'solar.installation',
        string='Installation',
        domain="[('partner_id', '=', partner_id)]",
        tracking=True,
    )
    contract_id = fields.Many2one(
        'solar.contract',
        string='Contract',
        domain="[('partner_id', '=', partner_id)]",
        tracking=True,
    )
    billing_period = fields.Char(
        string='Billing Period',
        required=False,
        tracking=True,
    )
    billing_date = fields.Date(
        string='Billing Date',
        default=fields.Date.context_today,
        tracking=True,
    )
    period_start = fields.Date(
        string='Period Start',
        tracking=True,
    )
    period_end = fields.Date(
        string='Period End',
        tracking=True,
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
        required=True,
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('invoiced', 'Invoiced'),
        ('paid', 'Paid')
    ], string='Status', default='draft', required=True, tracking=True)

    # Energy Data Group
    energy_produced = fields.Float(string='Energy Produced (kWh)', tracking=True)
    energy_exported = fields.Float(string='Energy Exported (kWh)', tracking=True)
    energy_imported = fields.Float(string='Energy Imported (kWh)', tracking=True)
    energy_self_consumed = fields.Float(
        string='Self Consumed (kWh)',
        compute='_compute_energy_self_consumed',
        store=True,
        tracking=True,
    )
    performance_ratio = fields.Float(string='Performance %', tracking=True)

    # Rates Group
    export_rate = fields.Float(string='Export Rate (per kWh)', default=0.0, digits=(12, 4), tracking=True)
    import_rate = fields.Float(string='Import Rate (per kWh)', default=0.0, digits=(12, 4), tracking=True)
    net_metering_credit = fields.Float(string='Net Metering Credit', default=0.0, tracking=True)
    service_fee = fields.Monetary(string='Service Fee', currency_field='currency_id', default=0.0, tracking=True)

    # Amounts Group
    export_revenue = fields.Monetary(
        string='Export Revenue',
        compute='_compute_amounts',
        store=True,
        currency_field='currency_id',
        tracking=True,
    )
    import_cost = fields.Monetary(
        string='Import Cost',
        compute='_compute_amounts',
        store=True,
        currency_field='currency_id',
        tracking=True,
    )
    net_amount = fields.Monetary(
        string='Net Amount',
        compute='_compute_amounts',
        store=True,
        currency_field='currency_id',
        tracking=True,
    )
    invoice_id = fields.Many2one(
        'account.move',
        string='Invoice',
        tracking=True,
    )

    # Savings Analysis Tab
    cost_without_solar = fields.Monetary(
        string='Cost without Solar',
        compute='_compute_savings',
        store=True,
        currency_field='currency_id',
    )
    solar_savings = fields.Monetary(
        string='Solar Savings',
        compute='_compute_savings',
        store=True,
        currency_field='currency_id',
    )
    savings_percent = fields.Float(
        string='Savings %',
        compute='_compute_savings',
        store=True,
    )

    # Meter Readings Tab
    reading_ids = fields.One2many(
        'solar.energy.billing.reading',
        'billing_id',
        string='Meter Readings',
    )

    # Documents Tab
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'solar_energy_billing_attachment_rel',
        'billing_id',
        'attachment_id',
        string='Attachments',
    )

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            # Auto-select related project, installation, and contract if single match exists
            projects = self.env['project.project'].search([('partner_id', '=', self.partner_id.id)])
            installations = self.env['solar.installation'].search([('partner_id', '=', self.partner_id.id)])
            contracts = self.env['solar.contract'].search([('partner_id', '=', self.partner_id.id)])

            self.project_id = projects[0].id if len(projects) == 1 else False
            self.installation_id = installations[0].id if len(installations) == 1 else False
            self.contract_id = contracts[0].id if len(contracts) == 1 else False
        else:
            self.project_id = False
            self.installation_id = False
            self.contract_id = False

    @api.depends('energy_produced', 'energy_exported')
    def _compute_energy_self_consumed(self):
        for rec in self:
            rec.energy_self_consumed = max(0.0, rec.energy_produced - rec.energy_exported)

    @api.depends('energy_exported', 'energy_imported', 'export_rate', 'import_rate', 'service_fee', 'net_metering_credit')
    def _compute_amounts(self):
        for rec in self:
            rec.export_revenue = rec.energy_exported * rec.export_rate
            rec.import_cost = rec.energy_imported * rec.import_rate
            rec.net_amount = rec.export_revenue - rec.import_cost + rec.net_metering_credit - rec.service_fee

    @api.depends('energy_self_consumed', 'import_rate', 'export_revenue', 'service_fee', 'energy_imported')
    def _compute_savings(self):
        for rec in self:
            total_consumed = rec.energy_imported + rec.energy_self_consumed
            rec.cost_without_solar = total_consumed * rec.import_rate + rec.service_fee
            rec.solar_savings = rec.energy_self_consumed * rec.import_rate + rec.export_revenue
            if rec.cost_without_solar > 0:
                rec.savings_percent = (rec.solar_savings / rec.cost_without_solar) * 100.0
            else:
                rec.savings_percent = 0.0

    def action_confirm(self):
        for rec in self:
            rec.write({'state': 'confirmed'})

    def action_invoice(self):
        for rec in self:
            if not rec.partner_id:
                raise UserError("Please select a Customer before creating an invoice.")
            
            # Find or create a service product for Energy Billing
            product = self.env['product.product'].search([('name', '=', 'Energy Billing')], limit=1)
            if not product:
                product = self.env['product.product'].create({
                    'name': 'Energy Billing',
                    'type': 'service',
                })

            # Format dates to DD-MMM-YYYY
            start_date = rec.period_start.strftime('%d-%b-%Y') if rec.period_start else 'N/A'
            end_date = rec.period_end.strftime('%d-%b-%Y') if rec.period_end else 'N/A'
            
            # Format net amount with currency symbol
            currency = rec.currency_id or self.env.company.currency_id
            currency_symbol = currency.symbol or ''
            
            # Construct dynamic description name
            description = (
                "Energy Billing\n"
                f"Period: {start_date} to {end_date}\n\n"
                f"Energy Produced: {rec.energy_produced:.0f} kWh\n"
                f"Energy Exported: {rec.energy_exported:.0f} kWh\n"
                f"Net Amount: {currency_symbol} {rec.net_amount:,.2f}"
            )

            line_vals = {
                'product_id': product.id,
                'name': description,
                'quantity': 1.0,
                'price_unit': rec.net_amount,
            }

            invoice_vals = {
                'move_type': 'out_invoice',
                'partner_id': rec.partner_id.id,
                'invoice_date': rec.billing_date or fields.Date.context_today(self),
                'ref': rec.name,
                'invoice_origin': rec.name,
                'company_id': self.env.company.id,
                'invoice_line_ids': [(0, 0, line_vals)],
            }
            invoice = self.env['account.move'].create(invoice_vals)
            rec.write({
                'invoice_id': invoice.id,
                'state': 'invoiced',
            })
            
        if len(self) == 1:
            return {
                'name': 'Invoice',
                'type': 'ir.actions.act_window',
                'res_model': 'account.move',
                'view_mode': 'form',
                'res_id': self.invoice_id.id,
                'target': 'current',
            }

    def action_pay(self):
        for rec in self:
            rec.write({'state': 'paid'})

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('solar.energy.billing') or 'New'
        return super().create(vals_list)


class SolarEnergyBillingReading(models.Model):
    _name = 'solar.energy.billing.reading'
    _description = 'Solar Energy Billing Reading'
    _order = 'date desc, id desc'

    billing_id = fields.Many2one(
        'solar.energy.billing',
        string='Billing Reference',
        required=True,
        ondelete='cascade',
    )
    date = fields.Date(
        string='Date',
        required=True,
        default=fields.Date.context_today,
    )
    reading_type = fields.Selection([
        ('produced', 'Produced'),
        ('exported', 'Exported'),
        ('imported', 'Imported'),
    ], string='Type', required=True)
    value = fields.Float(string='Reading Value (kWh)', required=True)
    photo = fields.Binary(string='Meter Photo')
    photo_name = fields.Char(string='Photo Name')
