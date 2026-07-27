# -- encoding: utf-8 --
###############################################################################
#
# Copyright (C) 2022-Present Speeduplight (https://speeduplight.com/)
#
###############################################################################
from thrive import api, fields, models
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta


class SolarDashboard(models.AbstractModel):
    _name = 'solar.dashboard'
    _description = 'Solar Dashboard'

    @api.model
    def get_dashboard_data(self, date_from=None, date_to=None):
        try:
            today = fields.Date.today()
            this_month_start = today.replace(day=1)
            this_month_end = (today.replace(day=1) + relativedelta(months=1)) - timedelta(days=1)
            prev_from = this_month_start - relativedelta(months=1)
            prev_to = this_month_start - timedelta(days=1)

            # Use all-time for KPIs and Overview, but keep current month for financial comparison
            d1 = None
            d2 = None

            # Compute user rights
            is_admin = self.env.user.has_group('sp_solar_management.group_solar_manager')
            is_sales = self.env.user.has_group('sp_solar_management.group_solar_sales') or is_admin
            is_tech = self.env.user.has_group('sp_solar_management.group_solar_technician') or is_admin
            is_pm = self.env.user.has_group('sp_solar_management.group_solar_project_manager') or is_admin
            is_finance = self.env.user.has_group('sp_solar_management.group_solar_finance') or is_admin
            is_office = self.env.user.has_group('sp_solar_management.group_solar_office_manager') or is_admin

            user_rights = {
                'is_admin': is_admin,
                'is_sales': is_sales,
                'is_tech': is_tech,
                'is_pm': is_pm,
                'is_finance': is_finance,
                'is_office': is_office,
            }

            return {
                'currency_symbol': self.env.company.currency_id.symbol or '$',
                'currency_position': self.env.company.currency_id.position or 'before',
                'currency_name': self.env.company.currency_id.name or 'USD',
                'user_rights': user_rights,
                'kpi_cards': self._get_kpi_cards(d1, d2, prev_from, prev_to),
                'pipeline': self._get_pipeline(d1, d2),
                'sales_overview': self._get_sales(d1, d2),
                'sales_chart_data': self._get_chart(d1, d2),
                'installation_status': self._get_installations(),
                'inventory_status': self._get_inventory(),
                'purchase_overview': self._get_purchase(d1, d2),
                'purchase_chart_data': self._get_purchase_chart(d1, d2),
                'financial_overview': self._get_financial(this_month_start, this_month_end, prev_from, prev_to),
                'recent_activities': self._get_activities(),
                'alerts': self._get_alerts(),
                'maintenance_summary': self._get_maintenance_summary_data(),
                'revenue_summary': self._get_revenue_summary_data(None, None, prev_from, prev_to),
                'operations_overview': self._get_operations_overview(),
            }
        except Exception as e:
            return {
                'error': str(e),
                'currency_symbol': '$',
                'currency_position': 'before',
                'currency_name': 'USD',
                'user_rights': {
                    'is_admin': False, 'is_sales': False, 'is_tech': False,
                    'is_pm': False, 'is_finance': False, 'is_office': False
                },
                'kpi_cards': {
                    'total_leads': 0, 'leads_change': 0, 'ongoing_inspections': 0,
                    'ongoing_installations': 0, 'completed_projects': 0,
                    'total_revenue': 0, 'revenue_change': 0, 'pending_payments': 0,
                    'maintenance_requests': 0, 'maintenance_change': 0
                },
                'pipeline': [],
                'sales_overview': {'quotations': 0, 'sale_orders': 0, 'pending_orders': 0},
                'sales_chart_data': {'labels': [], 'quotations': [], 'orders': [], 'revenue': []},
                'installation_status': [],
                'inventory_status': [],
                'purchase_overview': {'pending_rfqs': 0, 'purchase_orders': 0, 'total_vendors': 0},
                'purchase_chart_data': {'labels': [], 'rfqs': [], 'orders': [], 'expenses': []},
                'financial_overview': {
                    'total_revenue': 0, 'revenue_change': 0, 'total_expenses': 0,
                    'expenses_change': 0, 'total_profit': 0, 'profit_change': 0,
                    'pending_payments': 0, 'pending_change': 0
                },
                'maintenance_summary': {'open_requests': 0, 'in_progress': 0, 'completed_this_month': 0, 'overdue': 0},
                'revenue_summary': {'total_revenue': 0, 'revenue_change': 0, 'installation_revenue': 0, 'maintenance_revenue': 0, 'contract_revenue': 0},
                'operations_overview': {'active_contracts': 0, 'active_warranties': 0, 'energy_bills': 0},
                'recent_activities': [],
                'alerts': [{
                    'type': 'danger', 'icon': 'fa-exclamation-triangle', 'color': '#ef4444',
                    'title': 'Data Load Error', 'detail': str(e)[:100], 'time': 'Now'
                }],
            }


    def _get_kpi_cards(self, d1, d2, p1, p2):
        Lead = self.env['crm.lead'].sudo()
        Install = self.env['solar.installation'].sudo()
        Sale = self.env['sale.order'].sudo()
        Purchase = self.env['purchase.order'].sudo()

        domain = []
        if d1 and d2:
            domain = [('create_date', '>=', d1), ('create_date', '<=', d2)]

        leads = Lead.search_count(domain)
        prev_leads = Lead.search_count([('create_date', '>=', p1), ('create_date', '<=', p2)])

        insp_domain = [('state', '=', 'in_progress')]
        if d1 and d2:
            insp_domain += [('create_date', '>=', d1), ('create_date', '<=', d2)]
        ongoing_inspections = self.env['solar.site.inspection'].sudo().search_count(insp_domain)
        prev_ongoing_inspections = self.env['solar.site.inspection'].sudo().search_count([('state', '=', 'in_progress'), ('create_date', '>=', p1), ('create_date', '<=', p2)])

        ongoing = Install.search_count([('installation_status', '=', 'in_progress')])
        completed = Install.search_count([('installation_status', '=', 'completed')])
        prev_ongoing = Install.search_count([
            ('installation_status', '=', 'in_progress'),
            ('create_date', '>=', p1),
            ('create_date', '<=', p2),
        ])
        prev_completed = Install.search_count([
            ('installation_status', '=', 'completed'),
            ('create_date', '>=', p1),
            ('create_date', '<=', p2),
        ])

        maintenance_requests = self.env['maintenance.request'].sudo().search_count([('archive', '=', False)])
        prev_maintenance = self.env['maintenance.request'].sudo().search_count([('archive', '=', False), ('create_date', '>=', p1), ('create_date', '<=', p2)])

        sale_domain = [('state', 'in', ['sale', 'done'])]
        if d1 and d2:
            sale_domain += [('date_order', '>=', d1), ('date_order', '<=', d2)]
            
        revenue = sum(Sale.search(sale_domain).mapped('amount_total'))
        prev_rev = sum(Sale.search([('state', 'in', ['sale', 'done']), ('date_order', '>=', p1), ('date_order', '<=', p2)]).mapped('amount_total')) or 1.0

        pending = sum(self.env['account.move'].sudo().search([
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('payment_state', 'in', ('not_paid', 'partial'))
        ]).mapped('amount_residual'))
        prev_pending = sum(self.env['account.move'].sudo().search([
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('payment_state', 'in', ('not_paid', 'partial')),
            ('invoice_date', '>=', p1),
            ('invoice_date', '<=', p2),
        ]).mapped('amount_residual'))

        return {
            'total_leads': leads,
            'leads_change': self._percent_change(leads, prev_leads),
            'ongoing_inspections': ongoing_inspections,
            'inspections_change': self._percent_change(ongoing_inspections, prev_ongoing_inspections),
            'ongoing_installations': ongoing,
            'ongoing_change': self._percent_change(ongoing, prev_ongoing),
            'completed_projects': completed,
            'completed_change': self._percent_change(completed, prev_completed),
            'total_revenue': revenue,
            'revenue_change': self._percent_change(revenue, prev_rev),
            'pending_payments': pending,
            'pending_change': self._percent_change(pending, prev_pending),
            'maintenance_requests': maintenance_requests,
            'maintenance_change': self._percent_change(maintenance_requests, prev_maintenance),
        }

    def _get_pipeline(self, d1, d2):
        Lead = self.env['crm.lead'].sudo()
        Inspection = self.env['solar.site.inspection'].sudo()
        Approval = self.env['solar.government.approval'].sudo()
        Install = self.env['solar.installation'].sudo()

        def _get_missing_docs_string(lead):
            required_lines = lead._get_active_required_document_lines()
            if required_lines:
                missing = [line.name for line in required_lines if not line._is_completed()]
            else:
                missing = []
                if not lead.electric_bill:
                    missing.append('Electric Bill')
                if not lead.id_proof:
                    missing.append('ID Proof')
            if missing:
                return ', '.join(missing)
            return 'Pending Documents'

        pipeline_data = [
            {
                'name': 'Lead', 
                'count': Lead.search_count([]),
                'records': [{'id': l.id, 'res_model': 'crm.lead', 'ref': l.solar_reference or '-', 'detail': l.name or '-'} for l in Lead.search([], limit=3, order='id desc')]
            },
            {
                'name': 'Document Pending', 
                'count': Lead.search_count([('solar_stage', '=', 'document_pending')]),
                'records': [{'id': l.id, 'res_model': 'crm.lead', 'ref': l.solar_reference or '-', 'detail': _get_missing_docs_string(l)} for l in Lead.search([('solar_stage', '=', 'document_pending')], limit=3, order='id desc')]
            },
            {
                'name': 'Inspection', 
                'count': Inspection.search_count([]),
                'records': [{'id': i.id, 'res_model': 'solar.site.inspection', 'ref': i.name, 'detail': i.lead_id.name or '-'} for i in Inspection.search([], limit=3, order='id desc')]
            },
            {
                'name': 'SSEG Application', 
                'count': Approval.search_count([]),
                'records': [{'id': a.id, 'res_model': 'solar.government.approval', 'ref': a.application_number or '-', 'detail': a.status or '-'} for a in Approval.search([], limit=3, order='id desc')]
            },
            {
                'name': 'Installation', 
                'count': Install.search_count([]),
                'records': [{'id': i.id, 'res_model': 'solar.installation', 'ref': i.installation_id, 'detail': i.lead_id.name or '-'} for i in Install.search([], limit=3, order='id desc')]
            },
        ]

        is_admin = self.env.user.has_group('sp_solar_management.group_solar_manager')
        is_sales = self.env.user.has_group('sp_solar_management.group_solar_sales') or is_admin
        is_tech = self.env.user.has_group('sp_solar_management.group_solar_technician') or is_admin
        is_pm = self.env.user.has_group('sp_solar_management.group_solar_project_manager') or is_admin

        if is_sales and not (is_tech or is_pm):
            pipeline_data = [stage for stage in pipeline_data if stage['name'] in ['Lead', 'Document Pending', 'SSEG Application']]

        return pipeline_data

    def _get_sales(self, d1, d2):
        domain_sale = [('state', 'in', ['sale', 'done'])]
        domain_quotation = [('state', 'in', ['draft', 'sent'])]
        domain_pending = [('state', '=', 'sale'), ('invoice_status', '=', 'to invoice')]

        if d1 and d2:
            domain_sale += [('date_order', '>=', d1), ('date_order', '<=', d2)]
            domain_quotation += [('date_order', '>=', d1), ('date_order', '<=', d2)]
            domain_pending += [('date_order', '>=', d1), ('date_order', '<=', d2)]
            
        return {
            'quotations': self.env['sale.order'].sudo().search_count(domain_quotation),
            'sale_orders': self.env['sale.order'].sudo().search_count(domain_sale),
            'pending_orders': self.env['sale.order'].sudo().search_count(domain_pending),
        }

    def _get_chart(self, d1, d2):
        labels, quotations, orders_data, revenue = [], [], [], []
        today = fields.Date.today()
        for i in range(5, -1, -1):
            m_start = (today - relativedelta(months=i)).replace(day=1)
            m_end = (m_start + relativedelta(months=1)) - timedelta(days=1)
            
            labels.append(m_start.strftime('%b'))
            quotations.append(self.env['sale.order'].sudo().search_count([('state', 'in', ['draft', 'sent']), ('date_order', '>=', m_start), ('date_order', '<=', m_end)]))
            
            m_orders = self.env['sale.order'].sudo().search([('state', 'in', ['sale', 'done']), ('date_order', '>=', m_start), ('date_order', '<=', m_end)])
            orders_data.append(len(m_orders))
            revenue.append(sum(m_orders.mapped('amount_total')))
            
        return {'labels': labels, 'quotations': quotations, 'orders': orders_data, 'revenue': revenue}

    def _get_purchase_chart(self, d1, d2):
        labels, rfqs, pos, expenses = [], [], [], []
        today = fields.Date.today()
        for i in range(5, -1, -1):
            m_start = (today - relativedelta(months=i)).replace(day=1)
            m_end = (m_start + relativedelta(months=1)) - timedelta(days=1)
            
            labels.append(m_start.strftime('%b'))
            rfqs.append(self.env['purchase.order'].sudo().search_count([('state', 'in', ['draft', 'sent']), ('date_order', '>=', m_start), ('date_order', '<=', m_end)]))
            
            m_pos = self.env['purchase.order'].sudo().search([('state', '=', 'purchase'), ('date_order', '>=', m_start), ('date_order', '<=', m_end)])
            pos.append(len(m_pos))
            expenses.append(sum(m_pos.mapped('amount_total')))
            
        return {'labels': labels, 'rfqs': rfqs, 'orders': pos, 'expenses': expenses}

    def _get_installations(self):
        installs = self.env['solar.installation'].sudo().search([('installation_status', 'in', ['planning', 'in_progress'])], limit=5, order='id desc')
        res = []
        for i in installs:
            progress = 0
            if i.installation_status == 'in_progress':
                checks = [i.panels_installed, i.inverter_installed, i.dc_wiring_done, i.ac_connection_done, i.earthing_done, i.testing_done, i.structure_installed]
                progress = int((sum(1 for c in checks if c) / max(len(checks), 1)) * 100)
            res.append({
                'id': i.id, 'ref': i.installation_id, 'project': i.lead_id.name or '-',
                'engineer': i.assigned_engineer_id.name or '-', 'progress': progress
            })
        return res

    def _get_inventory(self):
        # Find physical products
        products = self.env['product.product'].sudo().search([('type', 'in', ['product', 'consu'])], limit=8, order='id desc')
        if not products:
            # Fallback if none found
            products = self.env['product.product'].sudo().search([], limit=8, order='id desc')
            
        res = []
        for p in products:
            qty = p.qty_available
            uom = p.uom_id.name or 'Units'
            # E.g. "120 Nos"
            qty_str = f"{int(qty)} {uom}"
            
            status = 'Out of Stock' if qty <= 0 else ('Low Stock' if qty < 20 else 'Good')
            status_code = 'out' if qty <= 0 else ('low' if qty < 20 else 'good')

            res.append({
                'id': p.id, 
                'name': p.name, 
                'qty_str': qty_str,
                'status': status,
                'status_code': status_code
            })
        return res

    def _get_purchase(self, d1, d2):
        try:
            Picking = self.env['stock.picking'].sudo()
            incoming = [('picking_type_id.code', '=', 'incoming')]
            
            late = Picking.search_count(incoming + [('state', 'not in', ('done', 'cancel')), ('scheduled_date', '<', fields.Datetime.now())])
            to_receive = Picking.search_count(incoming + [('state', 'not in', ('done', 'cancel'))])
            received = Picking.search_count(incoming + [('state', '=', 'done')])
        except Exception:
            late = 0
            to_receive = 0
            received = 0
            
        return {
            'late_receiving': late,
            'to_receive': to_receive,
            'received': received,
        }

    def _get_financial(self, d1, d2, p1, p2):
        Move = self.env['account.move'].sudo()
        
        # Revenue from posted customer invoices in date range
        rev_domain = [('move_type', 'in', ['out_invoice', 'out_receipt']), ('state', '=', 'posted')]
        if d1 and d2:
            rev_domain += [('invoice_date', '>=', d1), ('invoice_date', '<=', d2)]
        rev = sum(Move.search(rev_domain).mapped('amount_untaxed_signed'))
        
        # Previous revenue
        prev_rev = sum(Move.search([
            ('move_type', 'in', ['out_invoice', 'out_receipt']), 
            ('state', '=', 'posted'), 
            ('invoice_date', '>=', p1), 
            ('invoice_date', '<=', p2)
        ]).mapped('amount_untaxed_signed')) or 1
        
        # Expenses from posted vendor bills in date range (amount is negative, so use abs)
        exp_domain = [('move_type', 'in', ['in_invoice', 'in_receipt']), ('state', '=', 'posted')]
        if d1 and d2:
            exp_domain += [('invoice_date', '>=', d1), ('invoice_date', '<=', d2)]
        exp = abs(sum(Move.search(exp_domain).mapped('amount_untaxed_signed')))
        
        # Previous expenses
        prev_exp = abs(sum(Move.search([
            ('move_type', 'in', ['in_invoice', 'in_receipt']), 
            ('state', '=', 'posted'), 
            ('invoice_date', '>=', p1), 
            ('invoice_date', '<=', p2)
        ]).mapped('amount_untaxed_signed'))) or 1

        # Pending payments (All time unpaid invoices)
        pending = sum(Move.search([
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('payment_state', 'in', ('not_paid', 'partial'))
        ]).mapped('amount_residual'))
        
        return {
            'total_revenue': rev, 'total_expenses': exp, 'total_profit': rev - exp,
            'pending_payments': pending, 
            'revenue_change': round((rev - prev_rev) / prev_rev * 100, 1),
            'expenses_change': round((exp - prev_exp) / prev_exp * 100, 1),
            'profit_change': round(((rev - exp) - (prev_rev - prev_exp)) / max(abs(prev_rev - prev_exp), 1) * 100, 1),
        }

    def _get_activities(self):
        acts = []
        is_admin = self.env.user.has_group('sp_solar_management.group_solar_manager')
        is_sales = self.env.user.has_group('sp_solar_management.group_solar_sales') or is_admin
        is_tech = self.env.user.has_group('sp_solar_management.group_solar_technician') or is_admin
        is_pm = self.env.user.has_group('sp_solar_management.group_solar_project_manager') or is_admin
        is_finance = self.env.user.has_group('sp_solar_management.group_solar_finance') or is_admin
        
        # New Leads
        if is_sales or is_pm:
            for l in self.env['crm.lead'].sudo().search([], limit=3, order='create_date desc'):
                acts.append({
                    'title': 'New Lead', 
                    'detail': f"{l.name} ({l.solar_reference or 'N/A'})", 
                    'time_dt': l.create_date,
                    'time': self._format_time(l.create_date), 
                    'icon': 'fa-user', 
                    'color': '#3b82f6',
                    'res_model': 'crm.lead',
                    'res_id': l.id
                })
            
        # Recent Inspections
        if is_tech or is_pm:
            for i in self.env['solar.site.inspection'].sudo().search([], limit=3, order='create_date desc'):
                acts.append({
                    'title': 'Site Inspection', 
                    'detail': f"{i.name} for {i.lead_id.name if i.lead_id else 'Project'}", 
                    'time_dt': i.create_date,
                    'time': self._format_time(i.create_date), 
                    'icon': 'fa-search', 
                    'color': '#f59e0b',
                    'res_model': 'solar.site.inspection',
                    'res_id': i.id
                })
            
        # Recent Installations
        if is_tech or is_pm:
            for inst in self.env['solar.installation'].sudo().search([], limit=3, order='create_date desc'):
                acts.append({
                    'title': 'Installation started', 
                    'detail': f"{inst.installation_id} assigned to {inst.assigned_engineer_id.name if inst.assigned_engineer_id else 'Engineer'}", 
                    'time_dt': inst.create_date,
                    'time': self._format_time(inst.create_date), 
                    'icon': 'fa-wrench', 
                    'color': '#10b981',
                    'res_model': 'solar.installation',
                    'res_id': inst.id
                })
            
        # Recent Sale Orders
        if is_sales or is_finance:
            for s in self.env['sale.order'].sudo().search([('state', 'in', ['sale', 'done'])], limit=3, order='date_order desc'):
                acts.append({
                    'title': 'Sale Order Confirmed', 
                    'detail': f"{s.name} for {s.partner_id.name}", 
                    'time_dt': s.date_order,
                    'time': self._format_time(s.date_order), 
                    'icon': 'fa-check-circle', 
                    'color': '#8b5cf6',
                    'res_model': 'sale.order',
                    'res_id': s.id
                })


        # Sort all by time_dt desc
        acts.sort(key=lambda x: x['time_dt'], reverse=True)
        
        # Take top 5 to fill the box nicely
        final_acts = acts[:5]
        
        # Remove time_dt before returning
        for act in final_acts:
            act.pop('time_dt', None)
            
        return final_acts

    def _get_alerts(self):
        alerts = []
        delayed = self.env['solar.installation'].sudo().search_count([('installation_status', '=', 'in_progress'), ('planned_end_date', '<', fields.Date.today())])
        if delayed:
            alerts.append({'title': 'Delayed Installations', 'detail': f'{delayed} installations delayed', 'time': 'Now', 'icon': 'fa-clock', 'color': '#ef4444'})
        return alerts

    def _format_time(self, dt):
        if not dt: return 'Just now'
        diff = fields.Datetime.now() - dt
        mins = int(diff.total_seconds() / 60)
        if mins < 60: return f"{mins} min ago" if mins > 0 else "Just now"
        return f"{mins // 60} hours ago"

    def _percent_change(self, current, previous):
        if not previous:
            return 100.0 if current else 0.0
        return round((current - previous) / previous * 100, 1)

    def _get_maintenance_summary_data(self):
        try:
            today = fields.Date.today()
            this_month_start = today.replace(day=1)
            
            # Find stages
            new_stage = self.env['maintenance.stage'].sudo().search([('name', '=', 'New Request')], limit=1)
            if not new_stage:
                new_stage = self.env['maintenance.stage'].sudo().search([], order='sequence, id', limit=1)
                
            ip_stage = self.env['maintenance.stage'].sudo().search([('name', '=', 'In Progress')], limit=1)
            if not ip_stage:
                ip_stage = self.env['maintenance.stage'].sudo().search([('done', '=', False), ('id', '!=', new_stage.id)], order='sequence, id', limit=1)
                
            open_count = self.env['maintenance.request'].sudo().search_count([
                ('archive', '=', False), 
                ('stage_id', '=', new_stage.id)
            ]) if new_stage else 0
            
            inprogress_count = self.env['maintenance.request'].sudo().search_count([
                ('archive', '=', False), 
                ('stage_id', '=', ip_stage.id)
            ]) if ip_stage else 0
            
            completed_count = self.env['maintenance.request'].sudo().search_count([
                ('archive', '=', False),
                ('stage_id.done', '=', True),
                ('close_date', '>=', this_month_start)
            ])
            
            overdue_count = self.env['maintenance.request'].sudo().search_count([
                ('archive', '=', False),
                ('stage_id.done', '=', False),
                ('schedule_date', '<', fields.Datetime.now())
            ])
            
            return {
                'open_requests': open_count,
                'in_progress': inprogress_count,
                'completed_this_month': completed_count,
                'overdue': overdue_count,
            }
        except Exception:
            return {
                'open_requests': 0,
                'in_progress': 0,
                'completed_this_month': 0,
                'overdue': 0,
            }

    def _get_revenue_summary_data(self, d1, d2, p1, p2):
        try:
            Sale = self.env['sale.order'].sudo()
            Move = self.env['account.move'].sudo()
            
            # Calculate total revenue from sale orders (all-time if d1 and d2 are None)
            sale_domain = [('state', 'in', ['sale', 'done'])]
            if d1 and d2:
                sale_domain += [('date_order', '>=', d1), ('date_order', '<=', d2)]
            total_rev = sum(Sale.search(sale_domain).mapped('amount_total'))
            
            # Find linked invoice IDs for current period
            maint_invoice_ids = self.env['maintenance.request'].sudo().search([('invoice_id', '!=', False)]).mapped('invoice_id').ids
            contract_invoice_ids = self.env['solar.energy.billing'].sudo().search([('invoice_id', '!=', False)]).mapped('invoice_id').ids
            
            rev_domain = [('move_type', 'in', ['out_invoice', 'out_receipt']), ('state', '=', 'posted')]
            if d1 and d2:
                rev_domain += [('invoice_date', '>=', d1), ('invoice_date', '<=', d2)]
            all_posted_invoices = Move.search(rev_domain)
            
            maint_rev = sum(all_posted_invoices.filtered(lambda m: m.id in maint_invoice_ids).mapped('amount_untaxed_signed'))
            contract_rev = sum(all_posted_invoices.filtered(lambda m: m.id in contract_invoice_ids).mapped('amount_untaxed_signed'))
            
            # Installation revenue is the remainder of the total revenue
            inst_rev = total_rev - maint_rev - contract_rev
            if inst_rev < 0:
                inst_rev = 0.0
                
            return {
                'total_revenue': total_rev,
                'revenue_change': 0.0,
                'installation_revenue': inst_rev,
                'maintenance_revenue': maint_rev,
                'contract_revenue': contract_rev,
            }
        except Exception:
            return {
                'total_revenue': 0,
                'revenue_change': 0,
                'installation_revenue': 0,
                'maintenance_revenue': 0,
                'contract_revenue': 0,
            }

    def _get_operations_overview(self):
        try:
            contracts = self.env['solar.contract'].sudo().search_count([('status', '=', 'active')])
            warranties = self.env['solar.warranty.claim'].sudo().search_count([('state', '=', 'active')])
            bills = self.env['solar.energy.billing'].sudo().search_count([])
            return {
                'active_contracts': contracts,
                'active_warranties': warranties,
                'energy_bills': bills,
            }
        except Exception:
            return {
                'active_contracts': 0,
                'active_warranties': 0,
                'energy_bills': 0,
            }
