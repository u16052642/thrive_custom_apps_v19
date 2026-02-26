from thrive import fields, models


class ResUser(models.Model):
    _inherit = "res.users"

    hide_stages = fields.Many2many("crm.stage", string="Hidden Stages in Pipeline")
    country_chart_filter = fields.Selection(
        [("country", "Country"), ("state", "State"), ("city", "City")],
        string="Country Chart Filter",
        default="country",
    )
    hidden_tags = fields.Many2many(
        "crm.tag",  # or 'crm.lead.tag' depending on your Odoo version
        string="Hidden Tags in Opportunities Chart",
    )
    hidden_source_ids = fields.Many2many("utm.source", string="Hidden Sources")
