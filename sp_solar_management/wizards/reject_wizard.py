# -- encoding: utf-8 --
###############################################################################
#
# Copyright (C) 2022-Present Speeduplight (https://speeduplight.com/)
#
###############################################################################
from thrive import fields, models


class SolarSiteInspectionRejectWizard(models.TransientModel):
    _name = 'solar.site.inspection.reject.wizard'
    _description = 'Reject Site Inspection Wizard'

    inspection_id = fields.Many2one('solar.site.inspection', string='Inspection', required=True, readonly=True)
    rejection_reason = fields.Text(string='Rejection Reason', required=True)

    def action_confirm_reject(self):
        self.ensure_one()
        inspection = self.inspection_id
        inspection.write({'rejection_reason': self.rejection_reason})
        inspection.action_reject()
        return {'type': 'ir.actions.act_window_close'}
