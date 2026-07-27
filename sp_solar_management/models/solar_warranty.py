# -- encoding: utf-8 --
###############################################################################
#
# Copyright (C) 2022-Present Speeduplight (https://speeduplight.com/)
#
###############################################################################
from thrive import models, fields, api
from datetime import date


class SolarWarrantyClaim(models.Model):
    _name = 'solar.warranty.claim'
    _description = 'Solar Warranty'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'start_date desc, id desc'

    name = fields.Char(
        string='Reference', required=True, copy=False,
        readonly=True, default='New', tracking=True,
    )
    # Left side fields
    partner_id = fields.Many2one('res.partner', string='Customer', tracking=True)
    project_id = fields.Many2one('project.project', string='Project', tracking=True)
    installation_id = fields.Many2one('solar.installation', string='Installation', tracking=True)
    product_id = fields.Many2one('product.product', string='Product', tracking=True)
    serial_number = fields.Char(string='Serial Number', tracking=True)
    warranty_type = fields.Selection([
        ('manufacturer', 'Manufacturer Warranty'),
        ('workmanship', 'Workmanship Warranty'),
        ('performance', 'Performance Warranty'),
        ('extended', 'Extended Warranty'),
    ], string='Warranty Type', tracking=True)

    # Right side fields
    start_date = fields.Date(string='Start Date', tracking=True)
    expiry_date = fields.Date(string='Expiry Date', tracking=True)
    days_left = fields.Integer(
        string='Days Left', compute='_compute_days_left', store=True,
    )

    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('expired', 'Expired'),
    ], string='Status', default='draft', tracking=True)

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', string='Responsible', default=lambda self: self.env.user, tracking=True)

    # Notes
    notes = fields.Text(string='Notes')

    @api.depends('expiry_date')
    def _compute_days_left(self):
        today = date.today()
        for rec in self:
            if rec.expiry_date:
                delta = (rec.expiry_date - today).days
                rec.days_left = delta
            else:
                rec.days_left = 0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('solar.warranty.claim') or 'New'
        return super().create(vals_list)

    def action_activate(self):
        self.write({'state': 'active'})

    def action_expire(self):
        self.write({'state': 'expired'})

    def action_reset_draft(self):
        self.write({'state': 'draft'})
