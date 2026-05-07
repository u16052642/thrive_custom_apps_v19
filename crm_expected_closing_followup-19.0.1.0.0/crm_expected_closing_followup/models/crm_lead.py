from thrive import api, fields,tools, models, _
import datetime
from thrive.exceptions import UserError, AccessError, ValidationError
from thrive.osv import expression
import re


class CrmLead(models.Model):
    _inherit = "crm.lead"
   

    # expected closing missing record based on previous_Date using cron
    def action_send_lead_followup_email(self):
        manager_group = self.env.ref('crm_expected_closing_followup.crm_followup_manager')
        email_data = {}
        email_list = [] 
        get_emails = manager_group.user_ids.partner_id.mapped('email')
        # get all the users email ids
        mails =  ', '.join(get_emails)
        previous_Date = (datetime.datetime.today() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        
        current_date = datetime.datetime.today().strftime('%Y-%m-%d')
        print(previous_Date,'uuuuuuuuuuuu',current_date)
        missed_closing_lead = self.env['crm.lead'].search([('date_deadline','>=',previous_Date),('date_deadline','<',current_date),('stage_id.is_won','!=',True),('stage_id.name','!=','Lost')],order='user_id desc')
        data_list = []             
        for lead in missed_closing_lead:
            data_dict = {};
            data_dict['customer_name'] = lead.partner_id.name if lead.partner_id else ''
            data_dict['sales_parson'] = lead.user_id.name
            data_dict['enquiry'] = lead.name
            data_dict['mobile_number'] = lead.phone
            data_dict['email'] = lead.email_from
            data_dict['status'] = lead.stage_id.name
            data_dict['expected_closing'] = lead.date_deadline
            data_list.append(data_dict)
        template_id = self.env.ref('crm_expected_closing_followup.lead_expected_closing_email_template')
        print(data_list,'1111111111111111111111111111111111')
        print(mails,'222222222222222222222222222222222')
        if data_list and mails:
            print(mails,'iiiiiiiiiii')
            # pass the datas to template using context
            print(mails,'mmmmmmmmmmmmmmmmmmmmmmmmm')
            template_id.with_context({'crm_data': data_list},email_to = mails).send_mail(lead.id,force_send=True)

