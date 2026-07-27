# -- encoding: utf-8 --
###############################################################################
#
# Copyright (C) 2022-Present Speeduplight (https://speeduplight.com/)
#
###############################################################################
from thrive import _, api, fields, models
from thrive.exceptions import ValidationError


class SolarGovernmentApproval(models.Model):
    _name = 'solar.government.approval'
    _description = 'SSEG Application'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc, id desc'

    # ── computed role flags (used for invisible= in views) ──────────────────
    user_is_admin = fields.Boolean(compute='_compute_user_roles')
    user_is_sales = fields.Boolean(compute='_compute_user_roles')
    user_is_tech = fields.Boolean(compute='_compute_user_roles')
    user_is_pm = fields.Boolean(compute='_compute_user_roles')
    user_is_finance = fields.Boolean(compute='_compute_user_roles')
    user_is_office = fields.Boolean(compute='_compute_user_roles')

    def _compute_user_roles(self):
        is_admin = self.env.user.has_group('sp_solar_management.group_solar_manager')
        is_sales = self.env.user.has_group('sp_solar_management.group_solar_sales')
        is_tech = self.env.user.has_group('sp_solar_management.group_solar_technician')
        is_pm = self.env.user.has_group('sp_solar_management.group_solar_project_manager')
        is_finance = self.env.user.has_group('sp_solar_management.group_solar_finance')
        is_office = self.env.user.has_group('sp_solar_management.group_solar_office_manager')
        for rec in self:
            rec.user_is_admin = is_admin
            rec.user_is_sales = is_sales or is_admin
            rec.user_is_tech = is_tech or is_admin
            rec.user_is_pm = is_pm or is_admin
            rec.user_is_finance = is_finance or is_admin
            rec.user_is_office = is_office or is_admin
    # ────────────────────────────────────────────────────────────────────────

    lead_id = fields.Many2one(
        'crm.lead',
        string='Lead',
        required=True,
        ondelete='cascade',
        index=True,
        tracking=True,
    )
    lead_reference = fields.Char(
        string='Lead ID',
        related='lead_id.solar_reference',
        store=True,
        readonly=True,
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        related='lead_id.partner_id',
        store=True,
        readonly=True,
    )
    project_id = fields.Many2one(
        'project.project',
        string='Project',
        related='lead_id.project_id',
        store=True,
        readonly=True,
    )
    status = fields.Selection(
        [
            ('not_applied', 'Not Applied'),
            ('applied', 'Applied'),
            ('under_process', 'Under Process'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
        ],
        string='Status',
        default='not_applied',
        required=True,
        tracking=True,
    )
    application_date = fields.Date(string='Application Date', tracking=True)
    application_number = fields.Char(string='SSEG Application Number', tracking=True)
    next_followup_date = fields.Date(string='Next Follow-up Date', tracking=True)
    followup_notes = fields.Text(string='Follow-up Notes')
    document_line_ids = fields.One2many(
        'crm.lead.solar.document',
        related='lead_id.solar_document_line_ids',
        string='Lead Documents',
        readonly=False,
    )
    installation_count = fields.Integer(compute='_compute_installation_count')

    @api.depends('application_number', 'lead_reference')
    def _compute_display_name(self):
        for approval in self:
            if approval.application_number:
                approval.display_name = f"SSEG Application - {approval.application_number}"
            elif approval.lead_reference:
                approval.display_name = f"SSEG Application - {approval.lead_reference}"
            else:
                approval.display_name = f"SSEG Application - #{approval.id}"

    _lead_unique = models.Constraint(
        'UNIQUE(lead_id)',
        'A government approval record already exists for this lead.'
    )

    @api.constrains('status', 'application_number')
    def _check_application_number(self):
        for approval in self:
            if approval.status == 'approved' and not approval.application_number:
                raise ValidationError(_('Please enter the SSEG Application Number before approving.'))

    def _sync_lead_solar_stage(self):
        stage_sequence = [
            'document_pending',
            'application_submitted',
            'site_survey_scheduled',
            'site_survey_completed',
            'design_approved',
            'government_approval',
            'installation_in_progress',
            'inspection_testing',
            'system_activated',
        ]
        for approval in self.filtered('lead_id'):
            # Only sync stage when approval is actively submitted/processed,
            # not when it is freshly created with status 'not_applied'
            if approval.status == 'not_applied':
                continue
            target_stage = 'installation_in_progress' if approval.status == 'approved' else 'government_approval'
            lead_sudo = approval.lead_id.sudo()
            current_stage = lead_sudo.solar_stage or 'document_pending'
            if current_stage not in stage_sequence:
                current_stage = 'document_pending'
            if stage_sequence.index(current_stage) < stage_sequence.index(target_stage):
                lead_sudo.write({'solar_stage': target_stage})

    def _sync_lead_application_number(self):
        for approval in self.filtered(lambda rec: rec.lead_id and rec.application_number):
            approval.lead_id.sudo().write({
                'renewable_gov_application_number': approval.application_number,
            })

    def _compute_installation_count(self):
        for approval in self:
            approval.installation_count = self.env['solar.installation'].sudo().search_count([
                ('lead_id', '=', approval.lead_id.id),
            ])

    def _get_installation_design(self):
        self.ensure_one()
        design = self.env['solar.design'].search([
            ('lead_id', '=', self.lead_id.id),
            ('design_status', '=', 'final'),
        ], limit=1, order='id desc')
        if not design:
            raise ValidationError(_('Please finalize the design before creating an installation.'))
        return design

    def action_create_installation(self):
        self.ensure_one()
        if self.status != 'approved':
            raise ValidationError(_('Government Approval must be approved before creating an installation.'))
        existing_installation = self.env['solar.installation'].search([
            ('lead_id', '=', self.lead_id.id),
        ], limit=1, order='id desc')
        if existing_installation:
            return self.action_view_installation()
        return self._get_installation_design().action_create_installation()

    def action_view_lead(self):
        self.ensure_one()
        if not self.lead_id:
            return False
        return {
            'name': _('Lead'),
            'type': 'ir.actions.act_window',
            'res_model': 'crm.lead',
            'view_mode': 'form',
            'res_id': self.lead_id.id,
            'target': 'current',
        }

    def action_view_project(self):
        self.ensure_one()
        if not self.project_id:
            return False
        return {
            'name': _('Project'),
            'type': 'ir.actions.act_window',
            'res_model': 'project.project',
            'view_mode': 'form',
            'res_id': self.project_id.id,
            'target': 'current',
        }

    def action_view_installation(self):
        self.ensure_one()
        installation_records = self.env['solar.installation'].search([
            ('lead_id', '=', self.lead_id.id),
        ], order='id desc')
        if len(installation_records) == 1:
            return {
                'name': _('Installation'),
                'type': 'ir.actions.act_window',
                'res_model': 'solar.installation',
                'view_mode': 'form',
                'res_id': installation_records.id,
                'target': 'current',
            }
        return {
            'name': _('Installations'),
            'type': 'ir.actions.act_window',
            'res_model': 'solar.installation',
            'view_mode': 'list,form',
            'domain': [('lead_id', '=', self.lead_id.id)],
            'context': {
                'default_lead_id': self.lead_id.id,
            },
            'target': 'current',
        }

    def action_open_lead_documents(self):
        self.ensure_one()
        return {
            'name': _('Lead Documents'),
            'type': 'ir.actions.act_window',
            'res_model': 'crm.lead.solar.document',
            'view_mode': 'list,form',
            'domain': [('lead_id', '=', self.lead_id.id)],
            'context': {
                'default_lead_id': self.lead_id.id,
            },
        }

    def action_mark_submitted(self):
        for approval in self:
            approval.write({
                'status': 'applied',
                'application_date': fields.Date.context_today(approval),
            })
            approval.message_post(body=_('Application submitted on government portal'))
        return True

    def action_mark_under_process(self):
        for approval in self:
            approval.write({'status': 'under_process'})
            approval.message_post(body=_('Government approval moved to under process'))
        return True

    def action_mark_approved(self):
        for approval in self:
            approval.write({'status': 'approved'})
            approval.message_post(body=_('Government approval approved'))
        return True

    def action_mark_rejected(self):
        for approval in self:
            approval.write({'status': 'rejected'})
            approval.message_post(body=_('Government approval rejected'))
        return True

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._sync_lead_application_number()
        # Do NOT call _sync_lead_solar_stage() on creation — the default status
        # is 'not_applied' and should not force the lead stage to 'government_approval'.
        # Stage will advance only when the user explicitly updates the status.
        return records

    def write(self, vals):
        res = super().write(vals)
        if vals.get('application_number'):
            self._sync_lead_application_number()
        if 'status' in vals or 'lead_id' in vals:
            self._sync_lead_solar_stage()
        return res
