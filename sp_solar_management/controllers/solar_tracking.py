# -- encoding: utf-8 --
###############################################################################
#
# Copyright (C) 2022-Present Speeduplight (https://speeduplight.com/)
#
###############################################################################
import base64
import mimetypes

from markupsafe import escape

from thrive import http
from thrive.http import content_disposition, request


SOLAR_TIMELINE_STEPS = [
    ("document_pending", "Document Pending"),
    ("application_submitted", "Application Submitted"),
    ("site_survey_scheduled", "Site Survey & Technical Review"),
    ("design_approved", "Design Approved"),
    ("government_approval", "SSEG Application Process"),
    ("installation_in_progress", "Installation & Testing"),
    ("system_activated", "System Activated & Handover"),
]


class SolarTrackingController(http.Controller):
    def _get_lead_from_token(self, token):
        return request.env["crm.lead"].sudo().search(
            [("access_token", "=", token)],
            limit=1,
        )

    def _get_request_company(self):
        if "website" in request.env:
            website = request.env["website"].get_current_website()
            if website and website.company_id:
                return website.company_id
        return request.env.company

    def _get_latest_inspection(self, lead):
        return request.env["solar.site.inspection"].sudo().search(
            [("lead_id", "=", lead.id)],
            order="inspection_date desc, id desc",
            limit=1,
        )

    def _get_latest_design(self, lead, inspection=None):
        domain = [("lead_id", "=", lead.id)]
        if inspection:
            domain.append(("inspection_id", "=", inspection.id))
        design = request.env["solar.design"].sudo().search(
            domain + [("design_status", "=", "final")],
            order="id desc",
            limit=1,
        )
        if not design:
            design = request.env["solar.design"].sudo().search(
                domain,
                order="id desc",
                limit=1,
            )
        return design

    def _get_latest_installation(self, lead, design=None):
        domain = [("lead_id", "=", lead.id)]
        if design:
            domain.append(("design_id", "=", design.id))
        return request.env["solar.installation"].sudo().search(
            domain,
            order="actual_start_date desc, id desc",
            limit=1,
        )

    def _get_government_approval(self, lead):
        Approval = request.env["solar.government.approval"].sudo()
        approval = Approval.search([("lead_id", "=", lead.id)], limit=1)
        if not approval and lead.solar_reference:
            approval = Approval.search([("lead_reference", "=", lead.solar_reference)], limit=1)
        return approval

    def _get_effective_solar_stage(self, lead):
        stage = lead.solar_stage or "document_pending"
        installation = self._get_latest_installation(lead)
        if installation:
            if installation.installation_status == "completed":
                return "system_activated"
            return "installation_in_progress"

        approval = self._get_government_approval(lead)
        if approval:
            if approval.status == "approved":
                return "installation_in_progress"
            return "government_approval"

        design = self._get_latest_design(lead)
        if design and design.design_status == "final":
            return "government_approval"

        inspection = self._get_latest_inspection(lead)
        if inspection and inspection.state in ("approved", "completed"):
            return "site_survey_completed"
        if inspection:
            return "site_survey_scheduled"
        return stage

    def _get_solar_stage_label(self, lead):
        current_stage = self._get_effective_solar_stage(lead)
        labels = {
            "document_pending": "Documents Pending",
            "application_submitted": "Application Submitted",
            "site_survey_scheduled": "Survey in Progress",
            "site_survey_completed": "Site Survey Completed",
            "design_approved": "Design Approved",
            "government_approval": "SSEG Application Process",
            "installation_in_progress": "Installation in Progress",
            "inspection_testing": "Inspection & Testing",
            "system_activated": "System Activated",
        }
        return labels.get(current_stage) or dict(lead._fields["solar_stage"].selection).get(current_stage, "-")

    def _get_service_type_label(self, lead):
        return dict(lead._fields["renewable_service_type"].selection).get(lead.renewable_service_type, "-")

    def _get_formatted_address(self, lead):
        address_parts = [
            lead.renewable_site_street,
            lead.renewable_site_street2,
            lead.renewable_site_city,
            lead.renewable_site_state_id.name if lead.renewable_site_state_id else False,
            lead.renewable_site_zip,
            lead.renewable_site_country_id.name if lead.renewable_site_country_id else False,
        ]
        return ", ".join(part for part in address_parts if part) or "-"

    def _get_timeline_steps(self, lead):
        current_stage = self._get_effective_solar_stage(lead)
        current_index_map = {
            "document_pending": 0,
            "application_submitted": 1,
            "site_survey_scheduled": 2,
            "site_survey_completed": 3,
            "design_approved": 3,
            "government_approval": 4,
            "installation_in_progress": 5,
            "inspection_testing": 5,
            "system_activated": 6,
        }
        current_index = current_index_map.get(current_stage, 0)
        current_step_key = SOLAR_TIMELINE_STEPS[current_index][0]
        steps = []
        for index, (key, label) in enumerate(SOLAR_TIMELINE_STEPS):
            state = "pending"
            if index < current_index:
                state = "completed"
            elif key == current_step_key:
                state = "current"
            steps.append({
                "key": key,
                "label": label,
                "state": state,
                "description": self._get_timeline_step_description(lead, key),
            })
        return steps

    def _get_timeline_step_description(self, lead, key):
        if key == "government_approval":
            approval = self._get_government_approval(lead)
            status_messages = {
                "not_applied": "SSEG application is ready but not submitted yet.",
                "applied": "SSEG application has been submitted on the portal.",
                "under_process": "SSEG approval is under process with the authority.",
                "approved": "SSEG approval has been received.",
                "rejected": "SSEG approval was rejected. Our team will review the next steps.",
            }
            return status_messages.get(approval.status) if approval else "SSEG approval tracking will start after document verification."
        if key == "design_approved" and self._get_effective_solar_stage(lead) == "site_survey_completed":
            return "Site survey is approved. Our team is preparing the system design."
        return {
            "document_pending": "Customer documents are being collected and verified.",
            "application_submitted": "Your application has been submitted for processing.",
            "site_survey_scheduled": "Our survey team reviews the site and technical feasibility.",
            "site_survey_completed": "Site survey is approved. System design is now being prepared.",
            "design_approved": "System sizing and design are finalized for your project.",
            "installation_in_progress": "Material, installation work, and testing are underway.",
            "system_activated": "System commissioning is complete and the project is live.",
        }.get(key, "")

    def _get_document_statuses(self, lead):
        document_statuses = []
        document_lines = lead.solar_document_line_ids.filtered(lambda line: line.is_required)
        if not document_lines:
            return document_statuses
        for line in document_lines.sorted(lambda record: record.id):
            document_statuses.append(
                {
                    "key": str(line.id),
                    "label": line.name,
                    "status": "Uploaded" if line.document_file else "Missing",
                    "is_uploaded": bool(line.document_file),
                    "detail": line.document_filename or "-",
                    "filename": line.document_filename or line.name,
                    "url": "/solar/status/%s/document/line/%s" % (lead.access_token, line.id) if line.document_file else False,
                }
            )
        return document_statuses

    def _get_inspection_tracking_details(self, lead, inspection=None):
        inspection = inspection or self._get_latest_inspection(lead)
        if not inspection:
            return {
                "status": "Not Scheduled",
                "engineer_name": "-",
                "date": "-",
            }
        inspection_status = "Scheduled"
        if inspection.state in ("submitted", "approved", "rejected", "completed"):
            inspection_status = "Completed"
        return {
            "status": inspection_status,
            "engineer_name": inspection.survey_member_id.display_name or inspection.survey_manager_id.display_name or "-",
            "date": inspection.inspection_date or "-",
        }

    def _get_project_summary(self, lead):
        return [
            {"label": "Customer Name", "value": lead.contact_name or lead.partner_id.name or lead.name or "-"},
            {"label": "Application Number", "value": lead.solar_reference or lead.name or "-"},
            {"label": "Service Type", "value": self._get_service_type_label(lead)},
            {"label": "Address", "value": self._get_formatted_address(lead), "full": True},
        ]

    def _get_pending_documents(self, lead):
        document_lines = lead.solar_document_line_ids.filtered(lambda line: line.is_required)
        if document_lines:
            return [line.name for line in document_lines if not line._is_completed()]
        pending = []
        if not lead.electric_bill:
            pending.append("Electric Bill")
        if not lead.id_proof:
            pending.append("ID Proof")
        if not lead.ownership_proof:
            pending.append("Ownership Proof")
        return pending

    def _get_matching_design_lines(self, design, keywords):
        if not design:
            return request.env["solar.design.line"].sudo()
        return design.line_ids.filtered(
            lambda line: any(
                keyword in ("%s %s %s" % (
                    line.product_id.display_name or "",
                    line.product_id.default_code or "",
                    line.name or "",
                )).lower()
                for keyword in keywords
            )
        )

    def _get_product_summary(self, lines):
        names = []
        for line in lines:
            name = line.product_id.display_name or line.name
            if name and name not in names:
                names.append(name)
        return ", ".join(names) or "-"

    def _get_system_details(self, inspection, design=None):
        if design:
            system_type_label = dict(design._fields["system_type"].selection).get(design.system_type, "-")
            system_size = design.system_size or False
            estimated_generation = design.expected_generation_kwh_month or False
        elif inspection:
            system_type_label = dict(inspection._fields["system_type"].selection).get(inspection.system_type, "-")
            system_size = inspection.recommended_system_size_kw or inspection.max_installable_capacity_kw or False
            estimated_generation = inspection.expected_generation_kwh_month or False
        else:
            system_type_label = "-"
            system_size = False
            estimated_generation = False
        panel_lines = self._get_matching_design_lines(design, ("panel", "module", "pv"))
        inverter_lines = self._get_matching_design_lines(design, ("inverter",))
        number_of_panels = sum(panel_lines.mapped("quantity")) if panel_lines else False

        if design and design.solar_panel_type:
            panel_type_label = dict(design._fields["solar_panel_type"].selection).get(design.solar_panel_type, "-")
        else:
            panel_type_label = self._get_product_summary(panel_lines)

        return [
            {"label": "System Size (kW)", "value": system_size, "value_type": "number", "suffix": "kW"},
            {"label": "Panel Type", "value": panel_type_label},
            {"label": "Inverter", "value": self._get_product_summary(inverter_lines)},
            {"label": "Number of Panels", "value": number_of_panels, "value_type": "number"},
            {"label": "Estimated Generation", "value": estimated_generation, "value_type": "number", "suffix": "kWh/month"},
            {"label": "System Type", "value": system_type_label},
        ]

    def _get_payment_status(self, total_project_cost):
        return {"label": "Pending" if total_project_cost else "-", "state": "pending" if total_project_cost else "muted"}

    def _get_cost_details(self, inspection, design=None, installation=None):
        total_project_cost = False
        if installation and installation.sale_order_id:
            total_project_cost = installation.sale_order_id.amount_total
        elif design and design.line_ids:
            total_project_cost = sum(design.line_ids.mapped("subtotal"))
        if total_project_cost is False and inspection and inspection.estimated_project_cost:
            total_project_cost = inspection.estimated_project_cost
        customer_payable = total_project_cost
        payment_status = self._get_payment_status(total_project_cost)
        return {
            "total_project_cost": total_project_cost,
            "subsidy_amount": False,
            "customer_payable_amount": customer_payable,
            "payment_status": payment_status,
        }

    def _get_installation_details(self, inspection, installation=None):
        assigned_team = "-"
        engineer_name = "-"
        installation_date = "-"
        installation_status = "Not Started"
        if installation:
            installation_status = dict(installation._fields["installation_status"].selection).get(installation.installation_status, "-")
            installation_date = installation.actual_start_date or installation.planned_start_date or installation.installation_date or "-"
            assigned_team = installation.team_id.display_name or installation.subcontractor_id.display_name or assigned_team
            engineer_name = installation.assigned_engineer_id.display_name or installation.current_assigned_person or engineer_name
        if inspection and assigned_team == "-":
            assigned_team = inspection.survey_team_id.name or assigned_team
        if inspection and engineer_name == "-":
            engineer_name = inspection.survey_member_id.display_name or inspection.survey_manager_id.display_name or engineer_name
        return {
            "status": installation_status if installation else ("Scheduled" if inspection else "Not Started"),
            "date": installation_date,
            "assigned_team": assigned_team,
            "engineer_name": engineer_name,
        }

    def _get_completion_percentage(self, lead):
        current_stage = self._get_effective_solar_stage(lead)
        progress_map = {
            "document_pending": 20,
            "application_submitted": 30,
            "site_survey_scheduled": 40,
            "site_survey_completed": 45,
            "design_approved": 50,
            "government_approval": 60,
            "installation_in_progress": 80,
            "inspection_testing": 90,
            "system_activated": 100,
        }
        return progress_map.get(current_stage, 10)

    def _get_customer_action(self, lead):
        current_stage = self._get_effective_solar_stage(lead)
        pending_documents = self._get_pending_documents(lead)
        if current_stage == "document_pending" and pending_documents:
            return {
                "title": "Action Required",
                "message": "Please submit the pending documents so we can move your application forward.",
                "detail": ", ".join(pending_documents),
                "state": "attention",
            }
        if current_stage == "government_approval":
            return {
                "title": "Current Update",
                "message": self._get_timeline_step_description(lead, "government_approval"),
                "detail": "Our team will contact you if any additional document or clarification is required.",
                "state": "info",
            }
        if current_stage in ("installation_in_progress", "inspection_testing"):
            return {
                "title": "Upcoming Site Activity",
                "message": "Installation and quality checks are in progress.",
                "detail": "Please keep the site accessible for our installation or inspection team.",
                "state": "info",
            }
        if current_stage == "system_activated":
            return {
                "title": "Project Completed",
                "message": "Your solar project is active and handed over.",
                "detail": "Please contact support if you need post-installation assistance.",
                "state": "success",
            }
        return {
            "title": "Next Action",
            "message": "Our team is progressing your application through the next milestone.",
            "detail": "You can continue to track live updates from this dashboard.",
            "state": "info",
        }

    def _get_recent_updates(self, lead, inspection):
        updates = []
        if lead.create_date:
            updates.append({
                "title": "Application Registered",
                "date": lead.create_date.date(),
                "detail": "Your solar project request has been registered in our system.",
            })
        if inspection:
            updates.append({
                "title": "Site Survey Scheduled",
                "date": inspection.inspection_date or inspection.create_date.date(),
                "detail": "Survey team assigned: %s" % (inspection.survey_member_id.display_name or inspection.survey_manager_id.display_name or "Team to be assigned"),
            })
            if inspection.state in ("submitted", "approved", "completed"):
                updates.append({
                    "title": "Survey Report Submitted",
                    "date": (inspection.portal_submission_date.date() if inspection.portal_submission_date else inspection.inspection_date),
                    "detail": "Technical observations and recommendations have been recorded.",
                })
        updates = [update for update in updates if update["date"]]
        updates.sort(key=lambda item: item["date"], reverse=True)
        return updates[:5]

    def _get_dashboard_highlights(self, lead, inspection):
        pending_documents = self._get_pending_documents(lead)
        next_milestone = next((step["label"] for step in self._get_timeline_steps(lead) if step["state"] == "pending"), "Project Completion")
        last_update = "-"
        for candidate in (
            inspection.portal_submission_date.date() if inspection and inspection.portal_submission_date else False,
            inspection.inspection_date if inspection else False,
            lead.write_date.date() if lead.write_date else False,
        ):
            if candidate:
                last_update = candidate
                break
        return [
            {
                "label": "Project Progress",
                "value": "%s%%" % self._get_completion_percentage(lead),
                "detail": self._get_solar_stage_label(lead),
                "icon": "fa-line-chart",
            },
            {
                "label": "Pending Documents",
                "value": str(len(pending_documents)),
                "detail": ", ".join(pending_documents) if pending_documents else "All required documents received",
                "icon": "fa-file-text-o",
            },
            {
                "label": "Next Milestone",
                "value": next_milestone,
                "detail": "Upcoming stage in your solar project journey",
                "icon": "fa-flag-o",
            },
            {
                "label": "Last Update",
                "value": last_update,
                "detail": "Most recent milestone recorded in our system",
                "icon": "fa-refresh",
            },
        ]

    def _get_support_details(self, lead, company):
        contact_person = lead.user_id.partner_id.name or lead.user_id.name or company.name or "-"
        return {
            "contact_person": contact_person,
            "phone": company.phone or lead.user_id.partner_id.phone or "-",
            "email": company.email or lead.user_id.partner_id.email or "-",
        }

    def _get_next_step_message(self, lead):
        current_stage = self._get_effective_solar_stage(lead)
        messages = {
            "document_pending": "Please upload all pending documents so we can submit your solar application.",
            "application_submitted": "Your application has been submitted. Our team will review it and schedule the next activity shortly.",
            "site_survey_scheduled": "Our survey engineer will visit your site and validate technical feasibility.",
            "site_survey_completed": "Your site survey is approved. Our team is preparing the system design.",
            "design_approved": "The system design is approved. We are preparing the SSEG Application process.",
            "government_approval": self._get_timeline_step_description(lead, "government_approval"),
            "installation_in_progress": "Installation is underway. Our team is coordinating material delivery and site execution.",
            "inspection_testing": "Installation is complete and the system is currently under inspection and testing.",
            "system_activated": "Your solar system is active and ready. Our support team remains available for any help you need.",
        }
        return messages.get(
            current_stage,
            "Our team is reviewing your project and will update the next milestone soon.",
        )

    def _prepare_dashboard_values(self, lead, **kwargs):
        company = self._get_request_company()
        inspection = self._get_latest_inspection(lead)
        design = self._get_latest_design(lead, inspection=inspection)
        installation = self._get_latest_installation(lead, design=design)
        cost_details = self._get_cost_details(inspection, design=design, installation=installation)
        support_details = self._get_support_details(lead, company)
        return {
            "lead": lead,
            "project_summary": self._get_project_summary(lead),
            "dashboard_highlights": self._get_dashboard_highlights(lead, inspection),
            "customer_action": self._get_customer_action(lead),
            "recent_updates": self._get_recent_updates(lead, inspection),
            "service_type_label": self._get_service_type_label(lead),
            "formatted_address": self._get_formatted_address(lead),
            "solar_stage_label": self._get_solar_stage_label(lead),
            "timeline_steps": self._get_timeline_steps(lead),
            "document_statuses": self._get_document_statuses(lead),
            "inspection_details": self._get_inspection_tracking_details(lead, inspection=inspection),
            "system_details": self._get_system_details(inspection, design=design),
            "cost_details": cost_details,
            "installation_details": self._get_installation_details(inspection, installation=installation),
            "support_details": support_details,
            "display_currency": ((inspection and inspection.currency_id) or (design and design.currency_id) or company.currency_id),
        }

    @http.route(
        ["/solar/status/<string:token>"],
        type="http",
        auth="public",
        website=True,
    )
    def solar_status_page(self, token, **kwargs):
        lead = self._get_lead_from_token(token)
        values = {"lead": False}
        if lead.exists():
            values.update(self._prepare_dashboard_values(lead, **kwargs))
        return request.render("sp_solar_management.solar_tracking_status_page", values)

    @http.route(
        ["/solar/status/<string:token>/document/line/<int:line_id>"],
        type="http",
        auth="public",
        website=True,
    )
    def solar_status_document(self, token, line_id, **kwargs):
        lead = self._get_lead_from_token(token)
        if not lead:
            return request.not_found()
        document_line = lead.solar_document_line_ids.filtered(lambda line: line.id == line_id and line.document_file)[:1]
        if not document_line:
            return request.not_found()
        content = document_line.document_file
        filename = document_line.document_filename or document_line.name
        mimetype = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        return request.make_response(
            base64.b64decode(content),
            headers=[
                ("Content-Type", mimetype),
                ("Content-Disposition", content_disposition(filename, disposition_type="inline")),
            ],
        )

    @http.route(
        ["/solar/status/<string:token>/report-issue"],
        type="http",
        auth="public",
        methods=["POST"],
        website=True,
        csrf=True,
    )
    def solar_status_report_issue(self, token, **post):
        lead = self._get_lead_from_token(token)
        if not lead:
            return request.redirect("/solar/status/%s?issue_error=invalid" % token)
        issue_message = (post.get("issue_message") or "").strip()
        if not issue_message:
            return request.redirect("/solar/status/%s?issue_error=empty" % token)
        customer_name = lead.contact_name or lead.partner_id.name or lead.name or "Customer"
        customer_email = lead.email_from or lead.partner_id.email or "-"
        customer_phone = lead.phone or lead.partner_id.phone or "-"
        safe_customer_name = escape(customer_name)
        safe_customer_email = escape(customer_email)
        safe_customer_phone = escape(customer_phone)
        safe_issue_message = escape(issue_message).replace("\n", "<br/>")
        note_body = (
            "Customer issue reported from solar dashboard.<br/>"
            "<strong>Customer:</strong> %s<br/>"
            "<strong>Email:</strong> %s<br/>"
            "<strong>Phone:</strong> %s<br/>"
            "<strong>Message:</strong><br/>%s"
        ) % (safe_customer_name, safe_customer_email, safe_customer_phone, safe_issue_message)
        lead.sudo().message_post(
            body=note_body,
            message_type="comment",
            subtype_xmlid="mail.mt_note",
        )
        return request.redirect("/solar/status/%s?issue_reported=1" % token)
