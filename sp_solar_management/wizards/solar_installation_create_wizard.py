# -- encoding: utf-8 --
###############################################################################
#
# Copyright (C) 2022-Present Speeduplight (https://speeduplight.com/)
#
###############################################################################
from thrive import _, api, fields, models
from thrive.exceptions import ValidationError


class SolarInstallationCreateWizard(models.TransientModel):
    _name = 'solar.installation.create.wizard'
    _description = 'Create Solar Installation'

    design_id = fields.Many2one('solar.design', string='Design', required=True, readonly=True)
    installation_type = fields.Selection([
        ('in_house', 'Internal Team'),
        ('subcontracted', 'Subcontractor'),
    ], string='Execution Type', default='in_house', required=True)
    team_id = fields.Many2one('solar.installation.team', string='Team')
    project_manager_id = fields.Many2one(
        'res.users',
        string='Project Manager',
        related='team_id.manager_id',
        readonly=True,
    )
    team_engineer_ids = fields.Many2many(
        'res.users',
        string='Team Members',
        related='team_id.engineer_ids',
        readonly=True,
    )
    subcontractor_id = fields.Many2one('solar.subcontractor', string='Subcontractor Name')
    contact_person = fields.Char(string='Contact Person')
    phone = fields.Char(string='Phone')

    def _get_existing_installation_action(self):
        self.ensure_one()
        return self.design_id.action_view_installation()

    def _prepare_installation_vals(self):
        self.ensure_one()
        vals = {
            'lead_id': self.design_id.lead_id.id,
            'design_id': self.design_id.id,
            'installation_type': self.installation_type,
        }
        if self.installation_type == 'in_house':
            if not self.team_id:
                raise ValidationError(_('Please select a team for internal execution.'))
            vals['team_id'] = self.team_id.id
        else:
            if not self.subcontractor_id:
                raise ValidationError(_('Please select a subcontractor for subcontracted execution.'))
            if not self.contact_person or not self.phone:
                raise ValidationError(_('Please complete the subcontractor contact person and phone number.'))
            vals.update({
                'subcontractor_id': self.subcontractor_id.id,
                'contact_person': self.contact_person,
                'phone': self.phone,
            })
        return vals

    def action_create_installation(self):
        self.ensure_one()
        existing_installation = self.env['solar.installation'].search([
            ('design_id', '=', self.design_id.id),
        ], limit=1, order='id desc')
        if existing_installation:
            return self._get_existing_installation_action()
        installation = self.env['solar.installation'].create(self._prepare_installation_vals())
        return {
            'name': _('Installation'),
            'type': 'ir.actions.act_window',
            'res_model': 'solar.installation',
            'view_mode': 'form',
            'res_id': installation.id,
            'target': 'current',
        }

    def action_cancel(self):
        return {'type': 'ir.actions.act_window_close'}

    def _clear_internal_team_values(self):
        self.team_id = False

    def _clear_subcontractor_values(self):
        self.subcontractor_id = False
        self.contact_person = False
        self.phone = False

    def _set_subcontractor_contact(self):
        if self.subcontractor_id:
            self.contact_person = self.subcontractor_id.contact_person
            self.phone = self.subcontractor_id.phone
        else:
            self.contact_person = False
            self.phone = False

    @api.onchange('installation_type')
    def _onchange_installation_type(self):
        for wizard in self:
            if wizard.installation_type == 'in_house':
                wizard._clear_subcontractor_values()
            else:
                wizard._clear_internal_team_values()

    @api.onchange('subcontractor_id')
    def _onchange_subcontractor_id(self):
        for wizard in self:
            wizard._set_subcontractor_contact()
