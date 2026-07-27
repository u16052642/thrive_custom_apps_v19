# -- encoding: utf-8 --
###############################################################################
#
# Copyright (C) 2022-Present Speeduplight (https://speeduplight.com/)
#
###############################################################################
from thrive import http
from thrive.fields import Domain
from thrive.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from thrive.http import request
from werkzeug.exceptions import NotFound

INSPECTION_PAGE_SIZE = 20


class SolarInspectionPortal(CustomerPortal):
    def _get_inspection_model(self):
        return request.env["solar.site.inspection"].sudo()

    def _get_portal_sortings(self):
        return {
            "date": {"label": "Inspection Date", "order": "inspection_date desc, id desc"},
            "name": {"label": "Reference", "order": "name asc"},
            "state": {"label": "Status", "order": "state asc, inspection_date desc"},
        }

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        values.setdefault("inspection_count", 0)
        if "inspection_count" in counters:
            values["inspection_count"] = self._get_inspection_model().search_count(self._inspection_domain())
        return values

    def _inspection_domain(self):
        user_id = request.env.user.id
        return Domain("state", "in", ["in_progress", "submitted", "approved", "rejected", "completed"]) & (
            Domain("survey_manager_id", "=", user_id) | Domain("survey_member_id", "=", user_id)
        )

    def _get_portal_inspection(self, inspection_id):
        inspection = self._get_inspection_model().browse(inspection_id)
        if not inspection.exists():
            raise NotFound()
        inspection.check_portal_manager_access(user=request.env.user)
        return inspection

    @http.route(["/my/inspections", "/my/inspections/page/<int:page>"], type="http", auth="user", website=True)
    def portal_my_inspections(self, page=1, sortby="date"):
        values = self._prepare_portal_layout_values()
        domain = self._inspection_domain()
        searchbar_sortings = self._get_portal_sortings()
        sortby = sortby if sortby in searchbar_sortings else "date"
        inspection_model = self._get_inspection_model()
        inspection_count = inspection_model.search_count(domain)
        pager = portal_pager(
            url="/my/inspections",
            url_args={"sortby": sortby},
            total=inspection_count,
            page=page,
            step=INSPECTION_PAGE_SIZE,
        )
        inspections = inspection_model.search(
            domain,
            order=searchbar_sortings[sortby]["order"],
            limit=INSPECTION_PAGE_SIZE,
            offset=pager["offset"],
        )
        values.update(
            {
                "page_name": "inspection",
                "default_url": "/my/inspections",
                "pager": pager,
                "sortby": sortby,
                "searchbar_sortings": searchbar_sortings,
                "inspections": inspections,
            }
        )
        return request.render("sp_solar_management.portal_my_inspections", values)

    @http.route(["/my/inspections/<int:inspection_id>"], type="http", auth="user", website=True)
    def portal_inspection_page(self, inspection_id):
        inspection = self._get_portal_inspection(inspection_id)
        values = self._prepare_portal_layout_values()
        values.update(inspection.portal_prepare_page_values())
        values["page_name"] = "inspection"
        return request.render("sp_solar_management.portal_inspection_page", values)

    @http.route(
        ["/my/inspections/<int:inspection_id>/submit"],
        type="http",
        auth="user",
        website=True,
        methods=["POST"],
        csrf=True,
    )
    def portal_submit_inspection(self, inspection_id, **post):
        inspection = self._get_portal_inspection(inspection_id)
        if inspection.state in ("approved", "completed", "cancelled"):
            return request.redirect(f"/my/inspections/{inspection.id}?locked=1")
        inspection.portal_submit_inspection(
            post=request.httprequest.form,
            files=request.httprequest.files,
            user=request.env.user,
        )
        return request.redirect(f"/my/inspections/{inspection.id}?submitted=1")

    @http.route(
        ["/my/inspections/<int:inspection_id>/images/<int:image_id>/delete"],
        type="http",
        auth="user",
        website=True,
        methods=["POST"],
        csrf=True,
    )
    def portal_delete_inspection_image(self, inspection_id, image_id):
        inspection = self._get_portal_inspection(inspection_id)
        inspection.portal_delete_image(image_id=image_id, user=request.env.user)
        return request.redirect(f"/my/inspections/{inspection.id}")
