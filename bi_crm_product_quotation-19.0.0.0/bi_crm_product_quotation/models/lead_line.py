# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from thrive import api, fields, models, _

class LeadLine(models.Model):
    _name = 'lead.line'
    _description = "Lead Line"

    lead_line_id = fields.Many2one('crm.lead', string="crm")
    product_id = fields.Many2one(
        'product.product', string='Product', required=True)
    name = fields.Text(string='Description', required=True)
    product_uom_quantity = fields.Float(
        string='Order Quantity', digits='Product Unit of Measure', required=True, default=1.0)
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure' )

    price_unit = fields.Float('Unit Price', default=0.0)
    tax_id = fields.Many2many('account.tax', string='Taxes')

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.write({
                'name': self.product_id.name,
                'price_unit': self.product_id.lst_price,
                'product_uom': self.product_id.uom_id.id
            })
