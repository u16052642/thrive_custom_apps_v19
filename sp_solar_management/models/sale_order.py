# -- encoding: utf-8 --
###############################################################################
#
# Copyright (C) 2022-Present Speeduplight (https://speeduplight.com/)
#
###############################################################################
from thrive import models, fields

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    solar_design_id = fields.Many2one('solar.design', string='Solar Design', copy=False)

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for order in self:
            if order.solar_design_id:
                design = order.solar_design_id
                
                # Ensure Project is created/assigned
                project = design.project_id
                if not project and design.lead_id:
                    design.lead_id._create_solar_projects()
                    project = design.lead_id.project_id
                if not project:
                    project_name = design.name or 'Solar Design Project'
                    project = self.env['project.project'].sudo().create({
                        'name': project_name,
                        'partner_id': design.partner_id.id or (design.lead_id and design.lead_id.partner_id.id),
                        'user_id': design.user_id.id or self.env.user.id,
                    })
                    if design.lead_id:
                        design.lead_id.sudo().write({'project_id': project.id})
                
                # Ensure Design Tasks are created in the Project
                if project:
                    for task in design.task_ids:
                        if not task.project_task_id:
                            project_task = self.env['project.task'].sudo().create({
                                'name': task.name,
                                'project_id': project.id,
                                'user_ids': [(6, 0, task.user_ids.ids)] if task.user_ids else False,
                                'sequence': task.sequence,
                            })
                            task.project_task_id = project_task.id
                
                # Create Installation if not exists
                existing = self.env['solar.installation'].search([
                    ('design_id', '=', design.id)
                ], limit=1)
                
                # Cancel other quotations for this design/project
                other_quotations = self.env['sale.order'].search([
                    ('solar_design_id', '=', design.id),
                    ('id', '!=', order.id),
                    ('state', 'not in', ['sale', 'cancel'])
                ])
                if other_quotations:
                    other_quotations.action_cancel()
                if not existing:
                    self.env['solar.installation'].create({
                        'lead_id': design.lead_id.id,
                        'design_id': design.id,
                        'installation_type': False,
                        'team_id': False,
                    })
        return res

    def action_cancel(self):
        res = super(SaleOrder, self).action_cancel()
        for order in self:
            if order.solar_design_id:
                installations = self.env['solar.installation'].search([
                    ('design_id', '=', order.solar_design_id.id)
                ])
                if installations:
                    installations.unlink()
        return res
