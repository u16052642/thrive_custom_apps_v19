# -- encoding: utf-8 --
###############################################################################
#
# Copyright (C) 2022-Present Speeduplight (https://speeduplight.com/)
#
###############################################################################
from thrive import _, api, fields, models
from thrive.exceptions import ValidationError


class SolarMaterialTemplate(models.Model):
    _name = 'solar.material.template'
    _description = 'Solar Material Template'
    _order = 'name'

    name = fields.Char(string='Template Name', required=True)
    active = fields.Boolean(default=True)
    solar_company_id = fields.Many2one(
        'solar.company',
        string='Solar Company',
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
    system_type = fields.Selection(
        [
            ('on_grid', 'On-Grid'),
            ('off_grid', 'Off-Grid'),
            ('hybrid', 'Hybrid'),
        ],
        string='System Type',
    )
    system_size = fields.Float(string='System Size')
    expected_generation_kwh_month = fields.Float(string='Expected Generation (kWh/month)')
    line_ids = fields.One2many(
        'solar.material.template.line',
        'template_id',
        string='Products',
    )
    solar_panel_line_ids = fields.One2many(
        'solar.material.template.line',
        'solar_panel_template_id',
        string='Solar Panels',
    )
    battery_line_ids = fields.One2many(
        'solar.material.template.line',
        'battery_template_id',
        string='Batteries',
    )
    inverter_line_ids = fields.One2many(
        'solar.material.template.line',
        'inverter_template_id',
        string='Inverters',
    )
    other_line_ids = fields.One2many(
        'solar.material.template.line',
        'other_template_id',
        string='Other Components',
    )
    task_ids = fields.One2many(
        'solar.material.template.task',
        'template_id',
        string='Project Tasks',
    )


    @api.constrains('system_size')
    def _check_system_size(self):
        for template in self:
            if template.system_size <= 0:
                raise ValidationError(_('System Size (kW) must be greater than 0.'))


class SolarMaterialTemplateLine(models.Model):
    _name = 'solar.material.template.line'
    _description = 'Solar Material Template Line'
    _order = 'sequence, id'

    sequence = fields.Integer(default=10)
    template_id = fields.Many2one(
        'solar.material.template',
        string='Template',
        compute='_compute_template_id',
        store=True,
        readonly=False,
        ondelete='cascade',
    )
    solar_panel_template_id = fields.Many2one(
        'solar.material.template',
        string='Solar Panel Template',
        ondelete='cascade',
    )
    battery_template_id = fields.Many2one(
        'solar.material.template',
        string='Battery Template',
        ondelete='cascade',
    )
    inverter_template_id = fields.Many2one(
        'solar.material.template',
        string='Inverter Template',
        ondelete='cascade',
    )
    other_template_id = fields.Many2one(
        'solar.material.template',
        string='Other Template',
        ondelete='cascade',
    )

    @api.depends('solar_panel_template_id', 'battery_template_id', 'inverter_template_id', 'other_template_id')
    def _compute_template_id(self):
        for line in self:
            line.template_id = (
                line.solar_panel_template_id or
                line.battery_template_id or
                line.inverter_template_id or
                line.other_template_id
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
    product_id = fields.Many2one(
        'product.product',
        string='Product',
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
    currency_id = fields.Many2one(
        'res.currency',
        related='template_id.currency_id',
        readonly=True,
    )
    subtotal = fields.Monetary(
        string='Subtotal',
        currency_field='currency_id',
        compute='_compute_subtotal',
        store=True,
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


class SolarMaterialTemplateTask(models.Model):
    _name = 'solar.material.template.task'
    _description = 'Solar Material Template Task'
    _order = 'sequence, id'

    sequence = fields.Integer(default=10)
    template_id = fields.Many2one('solar.material.template', string='Template', ondelete='cascade')
    name = fields.Char(string='Title', required=True)
    user_ids = fields.Many2many('res.users', string='Assignees')
