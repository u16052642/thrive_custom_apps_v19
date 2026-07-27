# -- encoding: utf-8 --
###############################################################################
#
# Copyright (C) 2022-Present Speeduplight (https://speeduplight.com/)
#
###############################################################################
from thrive import models, fields, api
from datetime import date


class SolarDocumentType(models.Model):
    _name = 'solar.document.type'
    _description = 'Solar Document Type'
    _order = 'sequence, name'

    name = fields.Char(string='Document Type', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(default=True)


class SolarInstallationDocument(models.Model):
    _name = 'solar.installation.document'
    _description = 'Solar Installation Document'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'issue_date desc, id desc'

    name = fields.Char(string='Document Name', required=True, tracking=True)
    installation_id = fields.Many2one('solar.installation', string='Installation', required=True, tracking=True)
    document_type_id = fields.Many2one(
        'solar.document.type', string='Document Type',
        required=True, tracking=True,
    )
    document_number = fields.Char(string='Document Number', tracking=True)
    issued_by = fields.Char(string='Issued By', tracking=True)

    # Right side
    issue_date = fields.Date(string='Issue Date', tracking=True)
    expiry_date = fields.Date(string='Expiry Date', tracking=True)
    is_expired = fields.Boolean(
        string='Expired', compute='_compute_expiry_status', store=True,
    )
    days_to_expiry = fields.Integer(
        string='Days to Expiry', compute='_compute_expiry_status', store=True,
    )

    # Attachments & Notes
    attachment_ids = fields.Many2many(
        'ir.attachment', 'solar_installation_document_attachment_rel',
        'document_id', 'attachment_id',
        string='Attachments',
    )
    notes = fields.Text(string='Notes')

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

    @api.depends('expiry_date')
    def _compute_expiry_status(self):
        today = date.today()
        for rec in self:
            if rec.expiry_date:
                delta = (rec.expiry_date - today).days
                rec.days_to_expiry = delta
                rec.is_expired = delta < 0
            else:
                rec.days_to_expiry = 0
                rec.is_expired = False
