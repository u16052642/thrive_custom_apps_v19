# -- encoding: utf-8 --
###############################################################################
#
# Copyright (C) 2022-Present Speeduplight (https://speeduplight.com/)
#
###############################################################################
from thrive import fields, models

class SolarSubcontractor(models.Model):
    _name = 'solar.subcontractor'
    _description = 'Solar Subcontractor Configuration'
    _order = 'name'

    name = fields.Char(string='Subcontractor Name', required=True)
    contact_person = fields.Char(string='Contact Person')
    phone = fields.Char(string='Phone')
