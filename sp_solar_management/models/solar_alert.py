# -- encoding: utf-8 --
###############################################################################
#
# Copyright (C) 2022-Present Speeduplight (https://speeduplight.com/)
#
###############################################################################
from thrive import models, fields, api, _
from datetime import datetime


class SolarInstallationAlert(models.Model):
    _name = 'solar.installation.alert'
    _description = 'Solar Installation Alert'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc, id desc'

    name = fields.Char(string='Alert Title', required=True, tracking=True)
    installation_id = fields.Many2one('solar.installation', string='Installation', required=True, tracking=True)
    equipment_id = fields.Many2one('maintenance.equipment', string='Equipment', tracking=True)
    
    alert_type = fields.Selection([
        ('low_production', 'Low Production'),
        ('offline', 'Inverter Offline'),
        ('hardware_fault', 'Hardware Fault'),
        ('communication_error', 'Communication Error'),
        ('other', 'Other')
    ], string='Alert Type', default='low_production', tracking=True)
    
    severity = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')
    ], string='Severity', default='medium', tracking=True)
    
    state = fields.Selection([
        ('new', 'New'),
        ('acknowledged', 'Acknowledged'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved')
    ], string='Status', default='new', tracking=True, group_expand='_read_group_states')

    acknowledged_by_id = fields.Many2one('res.users', string='Acknowledged By', tracking=True, readonly=True)
    acknowledged_date = fields.Datetime(string='Acknowledged Date', tracking=True, readonly=True)
    resolved_date = fields.Datetime(string='Resolved Date', tracking=True, readonly=True)
    
    maintenance_request_id = fields.Many2one('maintenance.request', string='Maintenance Request', tracking=True)
    description = fields.Html(string='Description')

    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company
    )

    def _read_group_states(self, stages, domain, order):
        return ['new', 'acknowledged', 'in_progress', 'resolved']

    @api.model
    def create(self, vals):
        # Auto-acknowledge if created manually by user, or let it stay 'new'
        return super(SolarInstallationAlert, self).create(vals)

    def action_acknowledge(self):
        for rec in self:
            if rec.state == 'new':
                rec.write({
                    'state': 'acknowledged',
                    'acknowledged_by_id': self.env.user.id,
                    'acknowledged_date': datetime.now(),
                })

    def action_resolve(self):
        for rec in self:
            rec.write({
                'state': 'resolved',
                'resolved_date': datetime.now(),
            })


    def action_create_maintenance(self):
        self.ensure_one()
        if self.maintenance_request_id:
            # Already created, just open it
            return self.action_view_maintenance()

        # Create maintenance request
        vals = {
            'name': self.name,
            'installation_id': self.installation_id.id,
            'project_id': self.installation_id.project_id.id if self.installation_id.project_id else False,
            'partner_id': self.installation_id.partner_id.id if self.installation_id.partner_id else False,
            'equipment_id': self.equipment_id.id if self.equipment_id else False,
            'description': self.description,
            'user_id': self.env.user.id,
        }
        maintenance = self.env['maintenance.request'].create(vals)
        
        self.write({
            'maintenance_request_id': maintenance.id,
            'state': 'in_progress',
        })
        
        return self.action_view_maintenance()

    def action_view_maintenance(self):
        self.ensure_one()
        if not self.maintenance_request_id:
            return {}
        return {
            'name': _('Maintenance Request'),
            'type': 'ir.actions.act_window',
            'res_model': 'maintenance.request',
            'view_mode': 'form',
            'res_id': self.maintenance_request_id.id,
            'target': 'current',
        }
