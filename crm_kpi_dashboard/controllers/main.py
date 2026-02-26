from thrive import http
from thrive.http import request


class CrmController(http.Controller):
    @http.route("/crm_kpi_dashboard/toggle_stage_visibility", type="json", auth="user")
    def toggle_stage_visibility(self, stage_name, is_visible):
        """Toggle stage visibility for current user"""
        try:
            user = request.env.user
            stage_record = request.env["crm.stage"].search(
                [("name", "=", stage_name)], limit=1
            )

            if is_visible:
                # Remove from hidden stages (show the stage)
                user.write({"hide_stages": [(3, stage_record.id)]})
            else:
                # Add to hidden stages (hide the stage)
                user.write({"hide_stages": [(4, stage_record.id)]})

            return {"success": True, "message": "Stage visibility updated"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    @http.route("/crm_kpi_dashboard/get_country_wise_revenue", type="json", auth="user")
    def get_country_wise_revenue_controller(
        self, period, salesperson_id=False, location_filter="country"
    ):
        """Controller to call the get_country_wise_revenue model method"""
        try:
            result = request.env["crm.lead"].get_country_wise_revenue(
                period=period,
                salesperson_id=salesperson_id,
                location_filter=location_filter,
            )
            return result
        except Exception as e:
            return {"error": str(e), "data": [], "kpis": {}}

    @http.route(
        "/crm_kpi_dashboard/save_country_chart_filter", type="json", auth="user"
    )
    def save_country_chart_filter(self, filter_type):
        """Save country chart filter preference for current user"""
        try:
            user = request.env.user
            user.write({"country_chart_filter": filter_type})
            return {"success": True, "message": "Filter preference saved"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    @http.route("/crm_kpi_dashboard/get_country_chart_filter", type="json", auth="user")
    def get_country_chart_filter(self):
        """Get country chart filter preference for current user"""
        user = request.env.user
        return {"filter_type": user.country_chart_filter or "country"}

    @http.route("/crm_kpi_dashboard/save_hidden_tags", type="json", auth="user")
    def save_hidden_tags(self, **kwargs):
        """Save hidden tags for current user using tag IDs"""
        try:
            # Get hidden_tag_ids from kwargs
            hidden_tag_ids = kwargs.get("hidden_tag_ids", [])

            user = request.env.user
            user.write({"hidden_tags": [(6, 0, hidden_tag_ids)]})
            return {"success": True, "message": "Tags updated"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    @http.route("/crm_kpi_dashboard/get_hidden_tags", type="json", auth="user")
    def get_hidden_tags(self):
        """Get hidden tags for current user"""
        user = request.env.user
        hidden_tags = (
            user.hidden_tags.mapped("name") if hasattr(user, "hidden_tags") else []
        )
        return {"hidden_tags": hidden_tags}

    @http.route("/crm_kpi_dashboard/toggle_tag_visibility", type="json", auth="user")
    def toggle_tag_visibility(self, **kwargs):
        """Toggle tag visibility for current user"""
        try:
            user = request.env.user
            tag_id = kwargs.get("tag_id")
            is_visible = kwargs.get("is_visible")

            # Handle untagged (tag_id = 0)
            if tag_id == 0:
                # For untagged, we need a different approach since there's no tag record
                return {"success": True, "message": "Untagged visibility updated"}

            tag_record = request.env["crm.tag"].browse(tag_id)

            if is_visible:
                # Remove from hidden tags (show the tag)
                user.write({"hidden_tags": [(3, tag_record.id)]})
            else:
                # Add to hidden tags (hide the tag)
                user.write({"hidden_tags": [(4, tag_record.id)]})

            return {"success": True, "message": "Tag visibility updated"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    @http.route("/crm_kpi_dashboard/get_hidden_sources", type="json", auth="user")
    def get_hidden_sources(self):
        user = request.env.user
        hidden_sources = (
            user.hidden_source_ids.mapped("id")
            if hasattr(user, "hidden_source_ids")
            else []
        )
        return {"hidden_sources": hidden_sources}

    @http.route("/crm_kpi_dashboard/toggle_source_visibility", type="json", auth="user")
    def toggle_source_visibility(self, **kwargs):
        try:
            user = request.env.user
            source_id = kwargs.get("source_id")
            is_visible = kwargs.get("is_visible")

            source_record = request.env["utm.source"].browse(source_id)

            if is_visible:
                user.write({"hidden_source_ids": [(3, source_record.id)]})
            else:
                user.write({"hidden_source_ids": [(4, source_record.id)]})
            return {"success": True, "message": "Source visibility updated"}
        except Exception as e:
            return {"success": False, "message": str(e)}
