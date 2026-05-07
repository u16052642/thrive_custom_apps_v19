# -*- coding: utf-8 -*-
from thrive.exceptions import ValidationError
from thrive import models, fields, exceptions, api, _
import tempfile
import binascii
import xlwt
import base64
from xlwt import easyxf
import io
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from thrive import models, fields, api, _
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
import xlwt
from io import BytesIO
import base64
from xlwt import easyxf
import datetime
from thrive.exceptions import UserError
from datetime import datetime
import pdb
import io


class CRMExcelReport(models.Model):
    _inherit = 'crm.lead'

    def lead_attachment_report_excel(self):
        workbook = xlwt.Workbook()
        worksheet1 = workbook.add_sheet('Leads Not Updated')

        design_7 = easyxf('align: horiz left;font: bold 1;')
        design_8 = easyxf('align: horiz left;')
        design_9 = easyxf('align: horiz right;')
        design_10 = easyxf('align: horiz right; pattern: pattern solid, fore_colour red;')
        design_11 = easyxf('align: horiz right; pattern: pattern solid, fore_colour green;')
        design_12 = easyxf('align: horiz right; pattern: pattern solid, fore_colour gray25;')
        design_14 = easyxf('align: horiz left; pattern: pattern solid, fore_colour yellow;')

        worksheet1.col(0).width = 2000
        worksheet1.col(1).width = 6000
        worksheet1.col(2).width = 14000
        worksheet1.col(3).width = 14000

        rows = 0
        cols = 0
        row_pq = 0

        worksheet1.set_panes_frozen(True)
        worksheet1.set_horz_split_pos(rows + 1)
        worksheet1.set_remove_splits(True)

        col_1 = 0

        worksheet1.write(rows, col_1, _('Sl.No'), design_7)
        col_1 += 1
        worksheet1.write(rows, col_1, _('Sales Person'), design_7)
        col_1 += 1
        worksheet1.write(rows, col_1, _('Lead Name'), design_7)
        col_1 += 1
        worksheet1.write(rows, col_1, _('Opportunity Name'), design_7)
        col_1 += 1

        s_no = 1
        row_pq += 1
        from datetime import datetime, date
        from dateutil.relativedelta import relativedelta
        today = datetime.today().date()
        delta = today - timedelta(days=2)
        active_lead_domain = [('stage_id.is_won', '!=', True), ('active', '=', True), ('active', '!=', False),
                              ('probability', '>=', 0), ('probability', '!=', 100)]
        active_lead_domain += [('write_date', '<=', delta)]
        lead_ids = self.search(active_lead_domain, order='user_id')
        # pdb.set_trace()
        cust_lead_name4 = ''
        cust_lead_name1 = ''
        cust_lead_name2 = ''
        cust_lead_name3 = ''
        cust_lead_name6 = ''
        cust_lead_name5 = ''
        my_list = []
        for i in range(len(lead_ids)):
            if lead_ids[i].user_id.id in my_list:
                continue
            worksheet1.write(row_pq, 0, s_no)
            worksheet1.write(row_pq, 1, lead_ids[i].user_id.name)
            new_1 = active_lead_domain
            new_1 += [('type', '=', 'lead'), ('user_id', '=', lead_ids[i].user_id.id)]
            len_lead = self.search(new_1)
            new_1 = list(set(new_1) - set([('type', '=', 'lead'), ('user_id', '=', lead_ids[i].user_id.id)]))
            active_lead_domain = list(
                set(active_lead_domain) - set([('type', '=', 'lead'), ('user_id', '=', lead_ids[i].user_id.id)]))
            new_2 = active_lead_domain
            new_2 += [('type', '=', 'opportunity'), ('user_id', '=', lead_ids[i].user_id.id)]
            len_opt = self.search(new_2)
            new_2 = list(set(new_2) - {('type', '=', 'opportunity'), ('user_id', '=', lead_ids[i].user_id.id)})
            active_lead_domain = list(
                set(active_lead_domain) - set([('type', '=', 'opportunity'), ('user_id', '=', lead_ids[i].user_id.id)]))
            sr = row_pq
            my_list.append(lead_ids[i].user_id.id)
            # pdb.set_trace()
            if len(len_lead) > len(len_opt):
                for m in range(len(len_opt)):
                    if len(len_opt) >= 1:
                        if len_opt[m].partner_id and not len_opt[m].partner_name:
                            cust_lead_name1 = str(len_opt[m].partner_id.name) + ' - ' + str(len_opt[m].name)
                        if len_opt[m].partner_name and not len_opt[m].partner_id:
                            cust_lead_name1 = str(len_opt[m].partner_name) + ' - ' + str(len_opt[m].name)
                    else:
                        cust_lead_name1 = ''
                    worksheet1.write(sr, 3, cust_lead_name1)
                    sr += 1
                sr = row_pq
                for m in range(len(len_lead)):
                    if len(len_lead) >= 1:
                        if len_lead[m].partner_id and not len_lead[m].partner_name:
                            cust_lead_name2 = str(len_lead[m].partner_id.name) + ' - ' + str(len_lead[m].name)
                        if len_lead[m].partner_name and not len_lead[m].partner_id:
                            cust_lead_name2 = str(len_lead[m].partner_name) + ' - ' + str(len_lead[m].name)
                    else:
                        cust_lead_name2 = ''
                    worksheet1.write(sr, 2, cust_lead_name2)
                    sr += 1
                row_pq = sr - 1
            elif len(len_opt) > len(len_lead):
                for m in range(len(len_lead)):
                    if len(len_lead) >= 1:
                        if len_lead[m].partner_id and not len_lead[m].partner_name:
                            cust_lead_name3 = str(len_lead[m].partner_id.name) + ' - ' + str(len_lead[m].name)
                        if len_lead[m].partner_name and not len_lead[m].partner_id:
                            cust_lead_name3 = str(len_lead[m].partner_id.name) + ' - ' + str(len_lead[m].name)
                    else:
                        cust_lead_name3 = ''
                    worksheet1.write(sr, 2, cust_lead_name3)
                    sr += 1
                sr = row_pq
                for m in range(len(len_opt)):
                    if len(len_opt) >= 1:
                        if len_opt[m].partner_id and not len_opt[m].partner_name:
                            cust_lead_name4 = str(len_opt[m].partner_id.name) + ' - ' + str(len_opt[m].name)
                        if len_opt[m].partner_name and not len_opt[m].partner_id:
                            cust_lead_name4 = str(len_opt[m].partner_name) + ' - ' + str(len_opt[m].name)
                    else:
                        cust_lead_name4 = ''
                    worksheet1.write(sr, 3, cust_lead_name4)
                    sr += 1
                row_pq = sr - 1
            elif len(len_opt) == len(len_lead):
                for m in range(len(len_lead)):
                    if len(len_lead) >= 1:
                        if len_lead[m].partner_id and not len_lead[m].partner_name:
                            cust_lead_name5 = str(len_lead[m].partner_id.name) + ' - ' + str(len_lead[m].name)
                        if len_lead[m].partner_name and not len_lead[m].partner_id:
                            cust_lead_name5 = str(len_lead[m].partner_name) + ' - ' + str(len_lead[m].name)
                    else:
                        cust_lead_name5 = ''
                    worksheet1.write(sr, 2, cust_lead_name5)
                    sr += 1
                sr = row_pq
                for m in range(len(len_opt)):
                    if len(len_opt) >= 1:
                        if len_opt[m].partner_id and not len_opt[m].partner_name:
                            cust_lead_name6 = str(len_opt[m].partner_id.name) + ' - ' + str(len_opt[m].name)
                        if len_opt[m].partner_name and not len_opt[m].partner_id:
                            cust_lead_name6 = str(len_opt[m].partner_name) + ' - ' + str(len_opt[m].name)
                    else:
                        cust_lead_name6 = ''
                    worksheet1.write(sr, 3, cust_lead_name6)
                    sr += 1
                row_pq = sr - 1
            row_pq += 1
            worksheet1.write_merge(row_pq, row_pq, 0, 3, '', design_14)
            s_no += 1
            row_pq += 2

        cols = 2
        s_no = 1

        worksheet2 = workbook.add_sheet('Leads Not Created')
        worksheet2.col(0).width = 2000
        worksheet2.col(1).width = 7500
        worksheet2.col(2).width = 5500

        rows = 0
        cols = 0
        row_pq = 0

        worksheet2.set_panes_frozen(True)
        worksheet2.set_horz_split_pos(rows + 1)
        worksheet2.set_remove_splits(True)

        col_1 = 0

        worksheet2.write(rows, col_1, _('Sl.No'), design_7)
        col_1 += 1
        worksheet2.write(rows, col_1, _('Sales Person'), design_7)
        col_1 += 1
        worksheet2.write(rows, col_1, _('Department'), design_7)
        col_1 += 1

        sno = 1
        row_pq = row_pq + 1

        sales_depart = self.env['hr.department'].search(['|', ('name', '=', 'Sales'), ('name', '=', 'Marketing')])
        for department in sales_depart:
            all_sales_users = self.env['hr.employee'].search([("department_id", "=", department.id)])
            for i in range(len(all_sales_users)):
                if not self.search([('create_date', '<=', delta), ('user_id', '=', all_sales_users[i].id)]):
                    worksheet2.write(row_pq, 0, sno)
                    worksheet2.write(row_pq, 1, all_sales_users[i].name)
                    worksheet2.write(row_pq, 2, all_sales_users[i].department_id.display_name)
                    sno += 1
                    row_pq += 1

        fp = io.BytesIO()
        workbook.save(fp)
        excel_file = base64.b64encode(fp.getvalue())
        fp.close()
        return excel_file
