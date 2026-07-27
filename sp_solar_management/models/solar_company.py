# -- encoding: utf-8 --
###############################################################################
#
# Copyright (C) 2022-Present Speeduplight (https://speeduplight.com/)
#
###############################################################################
from thrive import fields, models


class SolarCompany(models.Model):
    _name = 'solar.company'
    _description = 'Solar Company'
    _order = 'name'

    name = fields.Char(string='Solar Company', required=True)
    active = fields.Boolean(default=True)
