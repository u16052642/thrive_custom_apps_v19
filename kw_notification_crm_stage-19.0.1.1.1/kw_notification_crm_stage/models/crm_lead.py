import logging

from thrive import models, fields, api
from thrive.addons.generic_mixin import post_write

_logger = logging.getLogger(__name__)


class CrmLead(models.Model):
    _name = 'crm.lead'
    _inherit = ['generic.mixin.track.changes', 'crm.lead']

    kw_send_message = fields.Boolean(default=False)

    @api.model_create_multi
    def create(self, vals_list):
        records = super(CrmLead, self).create(vals_list)
        records.post_write_stage_id_sms('sms')
        records.post_write_stage_id_email('email')
        return records

    @post_write('stage_id')
    def post_write_stage_id_sms(self, changes):
        filtered_records = self.filtered_domain([
            ('stage_id.kw_sms_template_id', '!=', False),
            ('kw_send_message', '=', False)])

        for obj in filtered_records:
            tmpl = obj.stage_id.kw_sms_template_id
            render = tmpl._render_template

            values = {
                'number': obj.phone or obj.partner_id.phone,
                'partner_id': obj.partner_id.id,
                'body': render(tmpl.body, 'crm.lead', [obj.id])[obj.id], }

            sms = self.env['sms.sms'].sudo().create(values)
            sms.sudo().send()
            if obj.stage_id.kw_sms_mass_keep_log:
                self.message_post(body=values['body'])
            obj.kw_send_message = True

    @post_write('stage_id')
    def post_write_stage_id_email(self, changes):
        filtered_records = self.filtered_domain([
            ('stage_id.kw_email_template_id', '!=', False),
            ('kw_send_message', '=', False)])

        for obj in filtered_records:
            tmpl = obj.stage_id.kw_email_template_id
            render = tmpl._render_template

            values = {
                'subject': render(tmpl.subject, 'crm.lead', [obj.id])[obj.id],
                'body_html': render(
                    tmpl.body_html, 'crm.lead', [obj.id])[obj.id],
                'email_to': obj.email_from or obj.partner_id.email, }

            email = self.env['mail.mail'].sudo().create(values)
            email.sudo().send()
            if obj.stage_id.kw_sms_mass_keep_log:
                self.message_post(body=values['body_html'])
            obj.kw_send_message = True
