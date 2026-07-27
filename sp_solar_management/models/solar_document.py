# -- encoding: utf-8 --
###############################################################################
#
# Copyright (C) 2022-Present Speeduplight (https://speeduplight.com/)
#
###############################################################################
from thrive import _, api, fields, models
from thrive.exceptions import ValidationError


class SolarDocumentConfig(models.Model):
    _name = 'solar.document.config'
    _description = 'Solar Document Configuration'
    _order = 'id'

    name = fields.Char(required=True)
    is_required = fields.Boolean(string='Required Document', default=False)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        leads = self.env['crm.lead'].search([])
        leads._sync_dynamic_document_lines()
        leads._sync_solar_stage_from_documents()
        return records

    def write(self, vals):
        res = super().write(vals)
        leads = self.env['crm.lead'].search([])
        leads._sync_dynamic_document_lines()
        leads._sync_solar_stage_from_documents()
        return res

    def unlink(self):
        linked_lines = self.env['crm.lead.solar.document'].search([('document_config_id', 'in', self.ids)])
        if linked_lines.filtered(lambda line: line.document_file):
            raise ValidationError(_('You cannot delete a document configuration that already has uploaded files.'))
        res = super().unlink()
        leads = self.env['crm.lead'].search([])
        leads._sync_dynamic_document_lines()
        leads._sync_solar_stage_from_documents()
        return res


class CrmLeadSolarDocument(models.Model):
    _name = 'crm.lead.solar.document'
    _description = 'Lead Solar Document'
    _order = 'id'

    lead_id = fields.Many2one('crm.lead', string='Lead', required=True, ondelete='cascade', index=True)
    document_config_id = fields.Many2one('solar.document.config', string='Document', required=True, ondelete='cascade')
    name = fields.Char(related='document_config_id.name', store=True, readonly=True)
    is_required = fields.Boolean(related='document_config_id.is_required', store=True, readonly=True)
    document_file = fields.Binary(string='Upload File', attachment=True)
    document_filename = fields.Char(string='Filename')
    is_uploaded = fields.Boolean(string='Uploaded', compute='_compute_is_uploaded', store=True)

    _lead_document_config_unique = models.Constraint(
        'UNIQUE(lead_id, document_config_id)',
        'This document already exists on the lead.'
    )

    @api.depends('document_file')
    def _compute_is_uploaded(self):
        for rec in self:
            rec.is_uploaded = bool(rec.document_file)

    def _is_completed(self):
        self.ensure_one()
        return bool(self.document_file)

    def action_view_document(self):
        self.ensure_one()
        if not self.document_file:
            raise ValidationError(_('No file is uploaded for this document.'))
        return {
            'type': 'ir.actions.act_url',
            'url': (
                '/web/content?model=crm.lead.solar.document&id=%s&field=document_file&filename_field=document_filename&download=false'
                % self.id
            ),
            'target': 'new',
        }

    def action_download_document(self):
        self.ensure_one()
        if not self.document_file:
            raise ValidationError(_('No file is uploaded for this document.'))
        return {
            'type': 'ir.actions.act_url',
            'url': (
                '/web/content?model=crm.lead.solar.document&id=%s&field=document_file&filename_field=document_filename&download=true'
                % self.id
            ),
            'target': 'self',
        }

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records.mapped('lead_id')._sync_solar_stage_from_documents()
        return records

    def write(self, vals):
        res = super().write(vals)
        self.mapped('lead_id')._sync_solar_stage_from_documents()
        return res

    def unlink(self):
        leads = self.mapped('lead_id')
        res = super().unlink()
        leads._sync_solar_stage_from_documents()
        return res
