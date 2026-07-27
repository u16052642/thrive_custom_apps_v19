# -- encoding: utf-8 --
###############################################################################
#
# Copyright (C) 2022-Present Speeduplight (https://speeduplight.com/)
#
###############################################################################
from thrive import fields, models

class SolarInstallationPhoto(models.Model):
    _name = 'solar.installation.photo'
    _description = 'Solar Installation Photo'
    _order = 'create_date desc'

    installation_id = fields.Many2one('solar.installation', string='Installation', required=True, ondelete='cascade')
    image = fields.Binary(string='Image', attachment=True, required=True)
    stage = fields.Selection([
        ('planning', 'Planning'),
        ('digging', 'Digging'),
        ('structure', 'Structure'),
        ('panel', 'Panel'),
        ('electrical', 'Electrical'),
        ('testing', 'Testing'),
        ('completed', 'Completed'),
    ], string='Stage')
    photo_type = fields.Selection([
        ('before', 'Before'),
        ('during', 'During'),
        ('after', 'After'),
    ], string='Type', required=True, default='during')
    name = fields.Char(string='Description')
