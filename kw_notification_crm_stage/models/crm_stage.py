import logging

from thrive import models, fields

_logger = logging.getLogger(__name__)


class CrmStage(models.Model):
    _inherit = 'crm.stage'

    kw_sms_template_id = fields.Many2one(
        comodel_name='sms.template', string='SMS | Viber Template')
    kw_email_template_id = fields.Many2one(
        comodel_name='mail.template', string='Email Template')
    kw_sms_mass_keep_log = fields.Boolean('Log as Note', default=True)
