# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
import re
from thrive import api, fields, models, tools, SUPERUSER_ID
from thrive.tools.translate import _
from thrive.tools import email_split
from thrive.exceptions import UserError, ValidationError
from thrive.addons.crm.models import crm_stage
import logging
import pdb
from io import BytesIO
import base64
import io

logger = logging.getLogger(__name__)


class Lead(models.Model):
    _inherit = "crm.lead"
    _description = "Lead/Opportunity"

    def crm_lead_auto_generate_mail_for_no_update_since_n_days(self):
        from datetime import datetime, date
        from dateutil.relativedelta import relativedelta
        today = datetime.today().date()
        import datetime
        today_print = today.strftime("%d/%m/%Y")
        data = self.lead_attachment_report_excel()
        ir_values = {
            'name': "Lead Report_%s.xls" % today_print,
            'type': 'binary',
            'datas': data,
            'store_fname': data,
            # 'mimetype': 'text/csv',
        }
        data_id = self.env['ir.attachment'].create(ir_values)
        body = """
            Dear Team,
            <br/>
            <br/>
            Enquiries are not updated since 2 days by sales persons as listed in the attached report. Please find the attachment.
                <br/>
                <br/>
            Regards,<br/>
            Administrator
            <p align="center">----------------------------------This is a system generated email----------------------------------------------</p>"""
        import datetime
        today_print = today.strftime("%d/%m/%Y")
        # MENTION YOUR EMAIL FROM, TO, CC EMAIL ADDRESS BEFORE INSTALLATION
        mail_value = {
            'subject': 'Leads Not Updated since Last 2 Days (%s)' % today_print,
            'body_html': body,
            'email_cc': "xxx.gmail.com",
            'email_to': "yyy.gmail.com",
            'email_from': "zzz.gmail.com",
            'attachment_ids': [(6, 0, [data_id.id])],
        }
        self.env['mail.mail'].create(mail_value).send()
