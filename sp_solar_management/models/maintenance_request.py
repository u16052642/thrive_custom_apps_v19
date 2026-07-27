# -- encoding: utf-8 --
###############################################################################
#
# Copyright (C) 2022-Present Speeduplight (https://speeduplight.com/)
#
###############################################################################
from thrive import models, fields, api
from thrive.exceptions import UserError

class SolarMaintenanceIssueCategory(models.Model):
    _name = 'solar.maintenance.issue.category'
    _description = 'Solar Maintenance Issue Category'
    _order = 'sequence, id'

    name = fields.Char(string='Name', required=True)
    sequence = fields.Integer(string='Sequence', default=10)

class SolarMaintenanceVisitType(models.Model):
    _name = 'solar.maintenance.visit.type'
    _description = 'Solar Maintenance Visit Type'
    _order = 'sequence, id'

    name = fields.Char(string='Name', required=True)
    sequence = fields.Integer(string='Sequence', default=10)

class MaintenanceRequestPartLine(models.Model):
    _name = 'maintenance.request.part.line'
    _description = 'Maintenance Request Part Line'

    request_id = fields.Many2one('maintenance.request', string='Maintenance Request', ondelete='cascade', required=True)
    product_id = fields.Many2one('product.product', string='Product', required=True)
    qty = fields.Float(string='Qty', default=1.0, required=True)
    cost = fields.Monetary(string='Cost', currency_field='currency_id')
    subtotal = fields.Monetary(string='Subtotal', compute='_compute_subtotal', store=True, currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string='Currency', related='request_id.currency_id')

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.cost = self.product_id.standard_price or self.product_id.lst_price or 0.0

    @api.depends('qty', 'cost')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.qty * line.cost

class MaintenanceRequest(models.Model):
    _inherit = 'maintenance.request'

    partner_id = fields.Many2one('res.partner', string='Customer', tracking=True)
    project_id = fields.Many2one('project.project', string='Solar Project', tracking=True)
    installation_id = fields.Many2one('solar.installation', string='Installation', tracking=True)
    contract_id = fields.Many2one('solar.contract', string='Service Contract', tracking=True)
    solar_issue_category_id = fields.Many2one('solar.maintenance.issue.category', string='Issue Category', tracking=True)
    solar_visit_type_id = fields.Many2one('solar.maintenance.visit.type', string='Visit Type', tracking=True)

    currency_id = fields.Many2one('res.currency', string='Currency', related='company_id.currency_id')
    is_chargeable = fields.Boolean(string='Chargeable', default=False)
    service_charge = fields.Monetary(string='Service Charge', currency_field='currency_id')
    transport_charge = fields.Monetary(string='Transportation Charge', currency_field='currency_id')
    part_line_ids = fields.One2many('maintenance.request.part.line', 'request_id', string='Parts Cost')
    parts_total = fields.Monetary(string='Total Parts Cost', compute='_compute_parts_total', store=True, currency_field='currency_id')
    total_cost = fields.Monetary(string='Total Cost', compute='_compute_total_cost', store=True, currency_field='currency_id')
    invoice_id = fields.Many2one('account.move', string='Invoice', copy=False, readonly=True)

    # Service Report fields
    problem_found = fields.Text(string='Problem Found')
    root_cause = fields.Text(string='Root Cause')
    action_taken = fields.Text(string='Action Taken')

    # Photos fields
    image_ids = fields.One2many('maintenance.request.image', 'request_id', string='Images')

    def action_open_photo_wizard(self):
        self.ensure_one()
        return {
            'name': 'Upload Photo',
            'type': 'ir.actions.act_window',
            'res_model': 'maintenance.request.photo.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_request_id': self.id,
            }
        }

    def action_create_invoice(self):
        self.ensure_one()
        if not self.partner_id:
            raise UserError("Please select a Customer before creating an invoice.")
        
        invoice_vals = {
            'move_type': 'out_invoice',
            'partner_id': self.partner_id.id,
            'invoice_origin': self.name,
            'company_id': self.company_id.id or self.env.company.id,
            'invoice_line_ids': [],
        }

        # Find a default income account for lines without product
        account = self.env['account.account'].search([
            ('account_type', '=', 'income'),
            ('company_ids', 'in', [self.company_id.id or self.env.company.id])
        ], limit=1)
        account_id = account.id if account else False

        # 1. Service Charge Line
        if self.service_charge > 0:
            line_vals = {
                'name': f"Service Charge - {self.name}",
                'quantity': 1.0,
                'price_unit': self.service_charge,
            }
            if account_id:
                line_vals['account_id'] = account_id
            invoice_vals['invoice_line_ids'].append((0, 0, line_vals))

        # 2. Transportation Charge Line
        if self.transport_charge > 0:
            line_vals = {
                'name': f"Transportation Charge - {self.name}",
                'quantity': 1.0,
                'price_unit': self.transport_charge,
            }
            if account_id:
                line_vals['account_id'] = account_id
            invoice_vals['invoice_line_ids'].append((0, 0, line_vals))

        # 3. Parts Cost Lines
        for line in self.part_line_ids:
            if line.qty > 0:
                invoice_vals['invoice_line_ids'].append((0, 0, {
                    'product_id': line.product_id.id,
                    'name': line.product_id.display_name,
                    'quantity': line.qty,
                    'price_unit': line.cost,
                }))

        if not invoice_vals['invoice_line_ids']:
            raise UserError("There are no chargeable amounts to invoice.")

        invoice = self.env['account.move'].create(invoice_vals)
        self.invoice_id = invoice.id

        # Return action to open the newly created invoice
        return {
            'name': 'Invoice',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': invoice.id,
            'target': 'current',
        }

    def action_view_invoice(self):
        self.ensure_one()
        if self.invoice_id:
            return {
                'name': 'Invoice',
                'type': 'ir.actions.act_window',
                'res_model': 'account.move',
                'view_mode': 'form',
                'res_id': self.invoice_id.id,
                'target': 'current',
            }

    @api.depends('part_line_ids.subtotal')
    def _compute_parts_total(self):
        for rec in self:
            rec.parts_total = sum(rec.part_line_ids.mapped('subtotal'))

    @api.depends('service_charge', 'transport_charge', 'parts_total')
    def _compute_total_cost(self):
        for rec in self:
            rec.total_cost = rec.service_charge + rec.transport_charge + rec.parts_total

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            # If current values do not belong to the selected partner, clear them
            if self.project_id and self.project_id.partner_id != self.partner_id:
                self.project_id = False
            if self.installation_id and self.installation_id.partner_id != self.partner_id:
                self.installation_id = False
            if self.contract_id and self.contract_id.partner_id != self.partner_id:
                self.contract_id = False
        else:
            self.project_id = False
            self.installation_id = False
            self.contract_id = False

    @api.onchange('project_id')
    def _onchange_project_id(self):
        if self.project_id:
            if not self.partner_id and self.project_id.partner_id:
                self.partner_id = self.project_id.partner_id
            if self.installation_id and self.installation_id.project_id != self.project_id:
                self.installation_id = False
            if self.contract_id and self.contract_id.project_id != self.project_id:
                self.contract_id = False

    @api.onchange('installation_id')
    def _onchange_installation_id(self):
        if self.installation_id:
            if not self.project_id and self.installation_id.project_id:
                self.project_id = self.installation_id.project_id
            if not self.partner_id and self.installation_id.partner_id:
                self.partner_id = self.installation_id.partner_id

    @api.onchange('contract_id')
    def _onchange_contract_id(self):
        if self.contract_id:
            if not self.project_id and self.contract_id.project_id:
                self.project_id = self.contract_id.project_id
            if not self.partner_id and self.contract_id.partner_id:
                self.partner_id = self.contract_id.partner_id
class MaintenanceRequestPhotoWizard(models.TransientModel):
    _name = 'maintenance.request.photo.wizard'
    _description = 'Upload Maintenance Photos'

    request_id = fields.Many2one('maintenance.request', string='Maintenance Request', required=True)
    photo_type = fields.Selection([
        ('before', 'Before'),
        ('after', 'After'),
    ], string='Type', required=True, default='before')
    photo = fields.Binary(string='Image', required=True)
    photo_name = fields.Char(string='Photo Name')

    def action_save(self):
        self.ensure_one()
        self.env['maintenance.request.image'].create({
            'request_id': self.request_id.id,
            'image': self.photo,
            'image_name': self.photo_name,
            'image_type': self.photo_type,
        })


class MaintenanceRequestImage(models.Model):
    _name = 'maintenance.request.image'
    _description = 'Maintenance Request Image'

    request_id = fields.Many2one('maintenance.request', string='Maintenance Request', ondelete='cascade', required=True)
    image = fields.Binary(string='Image', required=True)
    image_name = fields.Char(string='Image Name')
    image_type = fields.Selection([
        ('before', 'Before'),
        ('after', 'After'),
    ], string='Type', required=True)

    def action_delete(self):
        self.ensure_one()
        self.unlink()
        return True
