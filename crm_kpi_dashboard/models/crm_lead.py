from datetime import datetime, time, timedelta

from thrive import api, fields, models


def get_period_start_date_and_end_date(period):
    """
    Returns (start_date, end_date) for the given period.
    Period options: week, last_week, month, last_month, quarter,
    last_quarter, year, last_year, today, yesterday
    """
    today = datetime.now().date()

    if period == "week":
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)

    elif period == "last_week":
        end_date = today - timedelta(days=today.weekday() + 1)
        start_date = end_date - timedelta(days=6)

    elif period == "month":
        start_date = today.replace(day=1)
        next_month = (start_date + timedelta(days=32)).replace(day=1)
        end_date = next_month - timedelta(days=1)

    elif period == "last_month":
        first_of_this_month = today.replace(day=1)
        end_date = first_of_this_month - timedelta(days=1)
        start_date = end_date.replace(day=1)

    elif period == "quarter":
        start_month = ((today.month - 1) // 3) * 3 + 1
        start_date = today.replace(month=start_month, day=1)
        next_quarter = (start_date + timedelta(days=92)).replace(day=1)
        end_date = next_quarter - timedelta(days=1)

    elif period == "last_quarter":
        start_month = ((today.month - 1) // 3) * 3 + 1
        start_of_current_quarter = today.replace(month=start_month, day=1)
        end_date = start_of_current_quarter - timedelta(days=1)
        start_month_last_q = ((end_date.month - 1) // 3) * 3 + 1
        start_date = end_date.replace(month=start_month_last_q, day=1)

    elif period == "year":
        start_date = today.replace(month=1, day=1)
        end_date = today.replace(month=12, day=31)

    elif period == "last_year":
        start_date = today.replace(year=today.year - 1, month=1, day=1)
        end_date = today.replace(year=today.year - 1, month=12, day=31)

    elif period == "today":
        start_date = end_date = today

    elif period == "yesterday":
        yesterday = today - timedelta(days=1)
        start_date = end_date = yesterday

    else:
        raise ValueError("Invalid period specified")

    return start_date, end_date


class CrmLead(models.Model):
    _inherit = "crm.lead"

    # -------------------------------------------------------------------------
    # Internal Helpers
    # -------------------------------------------------------------------------
    @api.model
    def get_current_user_info(self):
        """Get current logged-in user information"""
        user = self.env.user
        return {
            "name": user.name,
            "id": user.id,
            "email": user.email,
        }

    def _get_stage_names(self):
        """Centralize stage name mapping."""
        return {
            "qualified": ["Qualified"],
            "presales": ["Pre-Sales"],
            "proposed": ["Proposed", "Negotiation"],
            "onhold": ["On Hold"],
        }

    def _build_domains(self, period, salesperson_id):
        """Return domain filters for created and closed opportunities."""
        start_date, end_date = get_period_start_date_and_end_date(period)

        # Convert dates to datetime for proper comparison with create_date
        start_datetime = datetime.combine(start_date, time.min)
        end_datetime = datetime.combine(end_date, time.max)

        creation_domain = [
            ("type", "=", "opportunity"),
            ("create_date", ">=", start_datetime),
            ("create_date", "<=", end_datetime),
            ("active", "=", True),
            ("stage_id.is_won", "=", False),
        ]

        close_domain = [
            ("type", "=", "opportunity"),
            ("date_closed", ">=", start_datetime),
            ("date_closed", "<=", end_datetime),
            "|",
            "&",
            ("active", "=", True),
            ("stage_id.is_won", "=", True),
            "&",
            ("active", "=", False),
            ("probability", "=", 0),
        ]

        if salesperson_id and int(salesperson_id):
            creation_domain.append(("user_id", "=", int(salesperson_id)))
            close_domain.append(("user_id", "=", int(salesperson_id)))
        return creation_domain, close_domain

    def get_all_data(self, period, salesperson_id):
        """Fetch opportunities created and closed in the given period."""
        creation_domain, close_domain = self._build_domains(period, salesperson_id)

        created_opps = self.search(creation_domain)
        closed_opps = self.search(close_domain)

        return created_opps, closed_opps

    # -------------------------------------------------------------------------
    # Dashboard Data Fetchers
    # -------------------------------------------------------------------------
    @api.model
    def get_salespersons_performance(self, period, salesperson_id=False):
        created_opps, closed_opps = self.get_all_data(period, salesperson_id)
        stage_map = self._get_stage_names()
        salesperson_data = {}

        def _init_user_data(user, currency):
            return {
                "id": user.id,
                "name": user.name.split(" ")[0] if user.name else "Unknown",
                "qualified": 0,
                "presales": 0,
                "proposed": 0,
                "onhold": 0,
                "won": 0,
                "lost": 0,
                "expected_revenue": 0.0,  # Required for chart
                "won_revenue": 0.0,  # Required for chart
                "won_leads_quantity": 0,  # Count of won opportunities
                "currency": currency,  # Required for chart
                # Optional fields for detailed analysis (not used in chart)
                "avg_deal_size": 0.0,
                "conversion_rate": 0.0,
                "total_opp": 0,
            }

        all_opps = []
        # Process created opportunities
        for opp in created_opps:
            if not opp.user_id:
                continue
            uid = opp.user_id.id
            currency = opp.company_id.currency_id.symbol or "$"
            salesperson_data.setdefault(uid, _init_user_data(opp.user_id, currency))

            # Count opportunities by stage
            stage = opp.stage_id.name if opp.stage_id else "No Stage"
            for key, names in stage_map.items():
                if stage in names:
                    salesperson_data[uid][key] += 1

            # Add expected revenue for all opportunities (required for chart)
            salesperson_data[uid]["expected_revenue"] += opp.expected_revenue
            all_opps.append(opp)

        # Process closed opportunities
        for opp in closed_opps:
            if not opp.user_id:
                continue
            uid = opp.user_id.id
            currency = opp.company_id.currency_id.symbol or "$"
            salesperson_data.setdefault(uid, _init_user_data(opp.user_id, currency))

            # Calculate won revenue from related sale orders (sale/done)
            won_revenue = 0.0
            for order in opp.order_ids.filtered(lambda o: o.state in ("sale", "done")):
                order_currency = order.pricelist_id.currency_id
                company_currency = order.company_id.currency_id
                amount = order.amount_total or 0.0

                # Convert order amount to company currency if different
                if order_currency != company_currency:
                    amount = order_currency._convert(
                        amount,
                        company_currency,
                        order.company_id,
                        order.date_order or fields.Date.today(),
                    )

                won_revenue += amount

            if opp.stage_id.is_won and opp.active:
                salesperson_data[uid]["won"] += 1
                salesperson_data[uid]["won_leads_quantity"] += 1
                salesperson_data[uid]["won_revenue"] += (
                    won_revenue  # Converted total revenue
                )

                # Add expected revenue if not already part of created_opps
                if opp not in created_opps:
                    salesperson_data[uid]["expected_revenue"] += opp.expected_revenue
                    all_opps.append(opp)

            elif not opp.active and opp.probability == 0:
                salesperson_data[uid]["lost"] += 1

        overview = []
        total_won_revenue = 0.0
        total_expected_revenue = 0.0

        # Process each salesperson's data
        for _uid, data in salesperson_data.items():
            # Basic calculations for optional fields
            total_opportunities = sum(
                [
                    data["qualified"],
                    data["presales"],
                    data["proposed"],
                    data["onhold"],
                    data["won"],
                    data["lost"],
                ]
            )

            data["total_opp"] = total_opportunities
            data["ongoing"] = data["qualified"] + data["presales"] + data["proposed"]

            # Round the main values needed for chart display
            data["expected_revenue"] = round(data["expected_revenue"], 2)
            data["won_revenue"] = round(data["won_revenue"], 2)
            # Optional calculations (can be removed if not needed elsewhere)
            data["conversion_rate"] = (
                round((data["won"] / total_opportunities) * 100, 2)
                if total_opportunities
                else 0
            )
            data["avg_deal_size"] = (
                round(data["won_revenue"] / data["won_leads_quantity"], 2)
                if data["won_leads_quantity"]
                else 0
            )

            # Add to global totals (needed for dashboard summary)
            total_won_revenue += data["won_revenue"]
            total_expected_revenue += data["expected_revenue"]
            overview.append(data)

            # Clean up zero values for display (required by original logic)
            for field in ["qualified", "presales", "proposed", "onhold", "won", "lost"]:
                data[field] = data[field] or ""
        # Calculate summary metrics needed for dashboard display
        number_of_salespersons = len(salesperson_data) if salesperson_data else 0

        # Main metrics used in the chart's document.getElementById updates
        avg_won_revenue_per_salesperson = (
            round(total_won_revenue / number_of_salespersons, 2)
            if number_of_salespersons
            else 0
        )

        avg_opportunity_count = (
            round(len(all_opps) / number_of_salespersons, 2)
            if number_of_salespersons
            else 0
        )

        # Get currency symbol for display (used in JS)
        currency_symbol = (
            salesperson_data[list(salesperson_data.keys())[0]]["currency"]
            if salesperson_data
            else "$"
        )

        max_revenue = max((r["won_revenue"] for r in overview), default=0.0)
        dynamic_interval = self.get_dynamic_interval(max_revenue)

        # Return only the data actually used by the frontend
        performance_dict = {
            "performance_overview": overview,  # Main data for chart
            "total_opportunity_count": len(all_opps),  # Used in getElementById
            "avg_opp_count": avg_opportunity_count,  # Used in getElementById
            "avg_won_revenue_per_salesperson": avg_won_revenue_per_salesperson,
            "currency_symbol": currency_symbol,  # Used for display formatting
            # Additional metrics (optional, for other dashboard components)
            "total_won_revenue": round(total_won_revenue, 2),
            "total_expected_revenue": round(total_expected_revenue, 2),
            "total_won_leads_quantity": sum(
                data.get("won_leads_quantity", 0) for data in salesperson_data.values()
            ),
            "number_of_salespersons": number_of_salespersons,
            "dynamic_interval": dynamic_interval,
        }
        return performance_dict

    def get_dynamic_interval(self, max_revenue):
        dynamic_interval = 0
        if max_revenue <= 5_000_000:  # up to 5M
            dynamic_interval = 1_000_000
        elif max_revenue <= 20_000_000:  # up to 20M
            dynamic_interval = 5_000_000
        else:  # 80M or more
            dynamic_interval = 20_000_000
        return dynamic_interval

    @api.model
    def get_lost_reason_data(self, period, salesperson_id=False):
        """Aggregate leads lost reasons for chart display."""
        start_date, end_date = get_period_start_date_and_end_date(period)

        domain = [
            ("active", "=", False),
            ("probability", "=", 0),
            # ("lost_reason_id", "!=", False),
            ("date_closed", ">=", start_date),
            ("date_closed", "<=", end_date),
            ("type", "=", "opportunity"),
        ]

        if salesperson_id and int(salesperson_id):
            domain.append(("user_id", "=", int(salesperson_id)))

        # Get opportunities WITH lost reasons
        domain_with_reason = domain + [("lost_reason_id", "!=", False)]
        data_with_reason = self.read_group(
            domain=domain_with_reason,
            fields=["lost_reason_id", "expected_revenue:sum", "id:count"],
            groupby=["lost_reason_id"],
        )

        # Get opportunities WITHOUT lost reasons
        domain_without_reason = domain + [("lost_reason_id", "=", False)]
        data_without_reason = self.read_group(
            domain=domain_without_reason,
            fields=["expected_revenue:sum", "id:count"],
            groupby=[],
        )

        lost_reasons = [
            {
                "reason": d["lost_reason_id"][1],
                "count": d.get("id", 0),
                "revenue": d.get("expected_revenue", 0),
            }
            for d in data_with_reason
        ]
        # Add "No Reason Specified" if there are opportunities without reasons
        if data_without_reason and data_without_reason[0].get("id", 0) > 0:
            lost_reasons.append(
                {
                    "reason": "No Reason Specified",
                    "count": data_without_reason[0].get("id", 0),
                    "revenue": data_without_reason[0].get("expected_revenue", 0),
                }
            )
        # Calculate totals
        total_lost_revenue = sum(d.get("expected_revenue", 0) for d in data_with_reason)
        total_lost_opportunities = sum(d.get("id", 0) for d in data_with_reason)

        if data_without_reason:
            total_lost_revenue += data_without_reason[0].get("expected_revenue", 0)
            total_lost_opportunities += data_without_reason[0].get("id", 0)

        company = self.env.company
        currency_symbol = company.currency_id.symbol or "$"

        # Return both the chart data and KPIs
        return {
            "data": lost_reasons,
            "kpis": {
                "total_lost_revenue": total_lost_revenue,
                "total_lost_opportunities": total_lost_opportunities,
                "currency_symbol": currency_symbol,
            },
        }

    @api.model
    def get_funnel_stage_data(self, salesperson_id=None):
        """Return data for Funnel Chart, excluding hidden stages."""
        domain = [("probability", ">", 0), ("type", "=", "opportunity")]

        if salesperson_id:
            domain.append(("user_id", "=", int(salesperson_id)))

        # Get current user's hidden stages
        current_user = self.env.user
        hidden_stage_ids = (
            current_user.hide_stages.ids if hasattr(current_user, "hide_stages") else []
        )

        # Get ALL stages (including hidden ones) for the dropdown
        all_stages = self.env["crm.stage"].search([])
        all_stage_names = all_stages.mapped("name")

        # Add filter to exclude hidden stages from the data
        if hidden_stage_ids:
            domain.append(("stage_id", "not in", hidden_stage_ids))

        # Aggregate expected revenue and counts
        leads = self.read_group(
            domain,
            fields=["stage_id", "expected_revenue:sum", "id:count"],
            groupby=["stage_id"],
            orderby="stage_id",
        )

        total_opportunities = sum(rec["id"] for rec in leads)
        total_expected_revenue = sum(rec["expected_revenue"] or 0.0 for rec in leads)
        avg_expected_revenue = (
            total_expected_revenue / total_opportunities if total_opportunities else 0
        )

        won_deals = self.read_group(
            domain + [("stage_id.is_won", "=", True)],
            fields=["stage_id", "expected_revenue:sum", "id:count"],
            groupby=["stage_id"],
            orderby="stage_id",
        )

        total_won_deals = sum(rec["id"] for rec in won_deals)
        avg_deal_size = (
            sum(rec["expected_revenue"] or 0.0 for rec in won_deals) / total_won_deals
            if total_won_deals
            else 0
        )

        data = []
        for rec in leads:
            stage_name = rec["stage_id"][1]
            expected_revenue = rec.get("expected_revenue") or 0.0
            count = rec.get("id") or 0
            percentage = (
                (count / total_opportunities * 100) if total_opportunities else 0
            )
            if expected_revenue > 0:
                data.append([stage_name, expected_revenue, count, percentage])

        # Get the company currency symbol
        company = self.env.company
        currency_symbol = company.currency_id.symbol

        return {
            "data": data,
            "total_opportunities": total_opportunities,
            "avg_expected_revenue": avg_expected_revenue,
            "avg_deal_size": avg_deal_size,
            "all_stages": all_stage_names,  # Send all stages for dropdown
            "hidden_stages": current_user.hide_stages.mapped("name")
            if hidden_stage_ids
            else [],
            "currency_symbol": currency_symbol,
        }

    @api.model
    def get_top_salespersons_data(self, period, limit=10, salesperson_id=False):
        """Get top salespersons by revenue for the dashboard"""
        start_date, end_date = get_period_start_date_and_end_date(period)

        domain = [
            ("type", "=", "opportunity"),
            ("active", "=", True),
            ("stage_id.is_won", "=", True),
            ("date_closed", ">=", start_date),
            ("date_closed", "<=", end_date),
        ]

        # If specific salesperson is selected, filter for that person only
        if salesperson_id and int(salesperson_id):
            domain.append(("user_id", "=", int(salesperson_id)))

        # Use read_group for better performance
        results = self.read_group(
            domain=domain,
            fields=["user_id", "expected_revenue:sum"],
            groupby=["user_id"],
            orderby="expected_revenue desc",
            limit=limit,
            lazy=False,
        )

        top_salespersons = []
        for res in results:
            if res.get("user_id"):
                user_id = res["user_id"][0]
                user_name = res["user_id"][1]
                revenue = res.get("expected_revenue", 0.0)
                count = res.get("__count", 0)

                top_salespersons.append(
                    {
                        "user_id": user_id,
                        "user_name": user_name,
                        "revenue": revenue,
                        "count": count,
                    }
                )

        return top_salespersons

    @api.model
    def get_opportunities_by_source_data(self, period, salesperson_id=False, limit=10):
        """Get opportunities grouped by source for donut chart"""
        start_date, end_date = get_period_start_date_and_end_date(period)

        # --- Hidden sources for current user ---
        user_hidden_source_ids = (
            self.env.user.hidden_source_ids.ids
            if hasattr(self.env.user, "hidden_source_ids")
            else []
        )

        # Base domain WITHOUT source filtering for chart data
        base_domain = [
            ("type", "=", "opportunity"),
            ("active", "=", True),
            ("create_date", ">=", start_date),
            ("create_date", "<=", end_date),
        ]

        if salesperson_id and int(salesperson_id):
            base_domain.append(("user_id", "=", int(salesperson_id)))

        # --- Domain for chart (EXCLUDE hidden sources) ---
        chart_domain = base_domain.copy()
        if user_hidden_source_ids:
            chart_domain.append(("source_id", "not in", user_hidden_source_ids))

        # Use read_group for chart data (visible sources only)
        chart_results = self.read_group(
            domain=chart_domain,
            fields=["source_id", "expected_revenue:sum"],
            groupby=["source_id"],
            orderby="expected_revenue desc",
            lazy=False,
        )

        # --- Get ALL sources for dropdown (including hidden ones) ---
        all_results = self.read_group(
            domain=base_domain,  # No source filtering
            fields=["source_id"],
            groupby=["source_id"],
            lazy=False,
        )

        source_data = []
        total_revenue = 0
        total_count = 0
        all_source_info = []

        # Build all_source_info from ALL results
        all_source_info.append({"id": 0, "name": "Unspecified"})

        for res in all_results:
            if res.get("source_id"):
                source_id = res["source_id"][0]
                source_name = res["source_id"][1]
                if not any(t["id"] == source_id for t in all_source_info):
                    all_source_info.append({"id": source_id, "name": source_name})
        # Build chart data from visible results only
        for res in chart_results:
            revenue = res.get("expected_revenue", 0.0)
            count = res.get("__count", 0)
            total_revenue += revenue
            total_count += count

            if res.get("source_id"):
                source_id = res["source_id"][0]
                source_name = res["source_id"][1]
            else:
                source_id = 0
                source_name = "Unspecified"

            source_data.append(
                {
                    "source_id": source_id,
                    "source_name": source_name,
                    "revenue": revenue,
                    "count": count,
                    "percentage": 0,
                }
            )

        # Calculate percentages and apply limit
        if source_data:
            source_data.sort(key=lambda x: x["revenue"], reverse=True)

            for data in source_data:
                if total_revenue > 0:
                    data["percentage"] = (data["revenue"] / total_revenue) * 100

            if len(source_data) > limit:
                top_sources = source_data[:limit]
                others_revenue = sum(item["revenue"] for item in source_data[limit:])
                others_count = sum(item["count"] for item in source_data[limit:])

                if others_revenue > 0:
                    others_percentage = (others_revenue / total_revenue) * 100
                    top_sources.append(
                        {
                            "source_id": -1,
                            "source_name": "Others",
                            "revenue": others_revenue,
                            "count": others_count,
                            "percentage": others_percentage,
                        }
                    )
                source_data = top_sources

        company_id = self.env.company
        currency_symbol = company_id.currency_id.symbol or "$"

        return {
            "source_data": source_data,  # Only visible sources for chart
            "all_sources": all_source_info,  # ALL sources for dropdown
            "hidden_source_ids": user_hidden_source_ids,
            "totals": {
                "total_opportunities": total_count,
                "total_revenue": total_revenue,
                "top_source": source_data[0]["source_name"] if source_data else "N/A",
                "currency_symbol": currency_symbol,
            },
        }

    @api.model
    def get_opportunities_by_tag_data(self, period, salesperson_id=False, limit=10):
        """Get opportunities grouped by tag for column chart with won revenue"""
        start_date, end_date = get_period_start_date_and_end_date(period)

        domain = [
            ("type", "=", "opportunity"),
            ("active", "=", True),
            ("create_date", ">=", start_date),
            ("create_date", "<=", end_date),
        ]

        if salesperson_id and int(salesperson_id):
            domain.append(("user_id", "=", int(salesperson_id)))

        # Get current user's hidden tags
        current_user = self.env.user
        hidden_tag_ids = (
            current_user.hidden_tags.ids if hasattr(current_user, "hidden_tags") else []
        )
        company_id = self.env.company
        currency_symbol = company_id.currency_id.symbol or "$"

        # Fetch opportunities with their tags
        opportunities = self.search(domain)
        # Manual aggregation by tags
        tag_data = {}
        expected_revenue_by_tags = 0
        won_revenue_by_tags = 0
        all_tags_info = []  # Track all available tags with IDs for dropdown

        # Add untagged option to all tags
        all_tags_info.append({"id": 0, "name": "Untagged"})

        for opp in opportunities:
            expected_revenue = opp.expected_revenue or 0

            # Calculate won revenue
            won_revenue = 0
            if opp.stage_id and opp.stage_id.is_won:
                if hasattr(opp, "order_ids"):
                    won_revenue = sum(
                        order.amount_total
                        for order in opp.order_ids
                        if order.state in ["sale", "done"]
                    )
                elif hasattr(opp, "sale_order_count") and opp.sale_order_count > 0:
                    sale_orders = self.env["sale.order"].search(
                        [
                            ("opportunity_id", "=", opp.id),
                            ("state", "in", ["sale", "done"]),
                        ]
                    )
                    won_revenue = sum(order.amount_total for order in sale_orders)

                expected_revenue_by_tags += expected_revenue
                won_revenue_by_tags += won_revenue

            # If opportunity has no tags, add to "Untagged" category
            if not opp.tag_ids:
                # Check if untagged is hidden (we'll handle this differently)
                # For now, we'll always include untagged in the data
                if "untagged" not in tag_data:
                    tag_data["untagged"] = {
                        "tag_id": 0,  # Use 0 for untagged
                        "tag_name": "Untagged",
                        "revenue": 0,
                        "expected_revenue": expected_revenue,
                        "won_revenue": won_revenue,
                        "count": 0,
                    }

                tag_data["untagged"]["revenue"] += expected_revenue
                tag_data["untagged"]["expected_revenue"] += expected_revenue
                tag_data["untagged"]["won_revenue"] += won_revenue
                tag_data["untagged"]["count"] += 1

            else:
                # If opportunity has multiple tags, count it for each tag
                for tag in opp.tag_ids:
                    # Add tag to all tags list if not already added
                    if not any(t["id"] == tag.id for t in all_tags_info):
                        all_tags_info.append({"id": tag.id, "name": tag.name})
                    # Skip if tag is hidden
                    if tag.id in hidden_tag_ids:
                        continue

                    tag_key = f"tag_{tag.id}"
                    if tag_key not in tag_data:
                        tag_data[tag_key] = {
                            "tag_id": tag.id,
                            "tag_name": tag.name,
                            "revenue": 0,
                            "expected_revenue": 0,
                            "won_revenue": 0,
                            "count": 0,
                        }
                    tag_data[tag_key]["revenue"] += expected_revenue
                    tag_data[tag_key]["expected_revenue"] += expected_revenue
                    tag_data[tag_key]["won_revenue"] += won_revenue
                    tag_data[tag_key]["count"] += 1

        # Convert to list and sort by expected revenue descending
        result = list(tag_data.values())
        result.sort(key=lambda x: x["expected_revenue"], reverse=True)

        max_revenue = max((r["revenue"] for r in result), default=0.0)
        dynamic_interval = self.get_dynamic_interval(max_revenue)

        # Apply limit
        if len(result) > limit:
            result = result[:limit]
        return {
            "result": result,
            "total_expected_revenue_by_tags": expected_revenue_by_tags,
            "total_won_revenue_by_tags": won_revenue_by_tags,
            "all_tags": all_tags_info,
            "hidden_tags": current_user.hidden_tags.mapped("name")
            if hidden_tag_ids
            else [],
            "currency_symbol": currency_symbol,
            "dynamic_interval": dynamic_interval,
        }

    @api.model
    def get_country_wise_revenue(
        self, period, salesperson_id=False, location_filter="country"
    ):
        """Get won deals and won revenue by location using confirmed sale orders."""

        start_date, end_date = get_period_start_date_and_end_date(period)
        SaleOrder = self.env["sale.order"]
        company_currency = self.env.company.currency_id

        # Base domain: confirmed sale orders in the period
        domain = [
            ("state", "in", ["sale", "done"]),
            ("date_order", ">=", start_date),
            ("date_order", "<=", end_date),
            ("partner_id", "!=", False),
            ("partner_id.active", "=", True),
        ]

        if salesperson_id and int(salesperson_id):
            domain.append(("user_id", "=", int(salesperson_id)))

        orders = SaleOrder.search(domain)

        # Aggregate by location
        location_map = {}
        for order in orders:
            # Determine key and name based on filter
            if location_filter == "country":
                key = (
                    order.partner_id.country_id.id
                    if order.partner_id.country_id
                    else False
                )
                name = (
                    order.partner_id.country_id.name
                    if order.partner_id.country_id
                    else "Unknown"
                )
            elif location_filter == "state":
                key = (
                    order.partner_id.state_id.id if order.partner_id.state_id else False
                )
                name = (
                    order.partner_id.state_id.name
                    if order.partner_id.state_id
                    else "Unknown"
                )
            elif location_filter == "city":
                key = order.partner_id.city or "Unknown"
                name = order.partner_id.city or "Unknown"
            else:
                key = (
                    order.partner_id.country_id.id
                    if order.partner_id.country_id
                    else False
                )
                name = (
                    order.partner_id.country_id.name
                    if order.partner_id.country_id
                    else "Unknown"
                )

            # Convert order total to company currency if needed
            order_currency = order.pricelist_id.currency_id or company_currency
            amount = order.amount_total or 0.0
            if order_currency != company_currency:
                amount = order_currency._convert(
                    amount,
                    company_currency,
                    order.company_id,
                    order.date_order or fields.Date.today(),
                )

            if key not in location_map:
                location_map[key] = {
                    "location": name,
                    "won_deals": 0,
                    "revenue": 0.0,
                }

            location_map[key]["won_deals"] += 1
            location_map[key]["revenue"] += amount

        # Build result
        result = list(location_map.values())

        # Filter only positive revenue/deals
        result = [r for r in result if r["won_deals"] > 0 and r["revenue"] > 0]

        # Sort and limit top 10
        result = sorted(result, key=lambda x: x["revenue"], reverse=True)[:10]

        # KPI calculations
        total_won_deals = sum(r["won_deals"] for r in result)
        total_won_revenue = sum(r["revenue"] for r in result)
        geographies_with_won_deals = len(result)
        # Compute total revenue from all orders (before filtering top 10)
        total_won_revenue_all = sum(
            amount_currency
            for amount_currency in [order.amount_total for order in orders]
        )
        # Or, to include currency conversion correctly:
        total_won_revenue_all = sum(
            order.pricelist_id.currency_id._convert(
                order.amount_total or 0.0,
                company_currency,
                order.company_id,
                order.date_order or fields.Date.today(),
            )
            if order.pricelist_id.currency_id != company_currency
            else order.amount_total or 0.0
            for order in orders
        )

        # Filter and sort top 10 locations
        result = [
            r for r in location_map.values() if r["won_deals"] > 0 and r["revenue"] > 0
        ]
        result = sorted(result, key=lambda x: x["revenue"], reverse=True)[:10]

        # Top 3 revenue share
        top_3_revenue = sum(r["revenue"] for r in result[:3])
        top_3_percentage_share = (
            (top_3_revenue / total_won_revenue_all * 100)
            if total_won_revenue_all > 0
            else 0
        )
        company_id = self.env.company
        currency_symbol = company_id.currency_id.symbol or "$"
        # 🧠 Dynamic interval calculation
        max_revenue = max((r["revenue"] for r in result), default=0.0)
        dynamic_interval = self.get_dynamic_interval(max_revenue)

        kpis = {
            "total_won_deals": total_won_deals,
            "total_won_revenue": round(total_won_revenue, 2),
            "top_location": result[0]["location"] if result else "None",
            "locations_count": len(result),
            "geographies_with_won_deals": geographies_with_won_deals,
            "top_3_percentage_share": round(top_3_percentage_share, 2),
            # "currency_symbol": company_currency.symbol or "$",
            "currency_symbol": currency_symbol,
            "dynamic_interval": dynamic_interval,
        }
        return {"data": result, "kpis": kpis}

    @api.model
    def get_top_customers_data(self, period, salesperson_id=False, limit=7):
        """Get top customers by revenue from confirmed sales orders (currency-aware)"""
        start_date, end_date = get_period_start_date_and_end_date(period)

        # Domain for confirmed sales orders
        domain = [
            ("state", "in", ["sale", "done"]),  # Confirmed/processed orders
            ("date_order", ">=", start_date),
            ("date_order", "<=", end_date),
            ("partner_id", "!=", False),
            ("partner_id.active", "=", True),
        ]

        if salesperson_id and int(salesperson_id):
            domain.append(("user_id", "=", int(salesperson_id)))

        SaleOrder = self.env["sale.order"]
        company_currency = self.env.company.currency_id

        orders = SaleOrder.search(domain)

        # Aggregate per customer (in company currency)
        customer_data = {}
        for order in orders:
            partner = order.partner_id
            if not partner:
                continue

            order_currency = order.pricelist_id.currency_id
            amount = order.amount_total or 0.0

            # Convert to company currency if needed
            if order_currency != company_currency:
                amount = order_currency._convert(
                    amount,
                    company_currency,
                    order.company_id,
                    order.date_order or fields.Date.today(),
                )

            if partner.id not in customer_data:
                customer_data[partner.id] = {
                    "partner": partner,
                    "revenue": 0.0,
                    "order_count": 0,
                }

            customer_data[partner.id]["revenue"] += amount
            customer_data[partner.id]["order_count"] += 1

        # Sort by total revenue (descending)
        sorted_customers = sorted(
            customer_data.values(), key=lambda x: x["revenue"], reverse=True
        )[:limit]

        # Compute global metrics
        total_revenue = sum(c["revenue"] for c in customer_data.values())
        total_orders = sum(c["order_count"] for c in customer_data.values())

        top_customers_total_revenue = sum(c["revenue"] for c in sorted_customers)
        top_customers_total_orders = sum(c["order_count"] for c in sorted_customers)

        # Prepare customer data for dashboard
        customers_data = []
        for c in sorted_customers:
            revenue = c["revenue"]
            order_count = c["order_count"]
            customers_data.append(
                {
                    "customer_id": c["partner"].id,
                    "customer_name": c["partner"].name,
                    "revenue": round(revenue, 2),
                    "order_count": order_count,
                    "average_order_value": (
                        round(revenue / order_count, 2) if order_count > 0 else 0
                    ),
                }
            )

        # KPI calculations
        top_customers_avg_order_value = (
            top_customers_total_revenue / top_customers_total_orders
            if top_customers_total_orders > 0
            else 0
        )

        overall_avg_order_value = (
            total_revenue / total_orders if total_orders > 0 else 0
        )

        percentage_share = (
            (top_customers_total_revenue / total_revenue * 100)
            if total_revenue > 0
            else 0
        )

        currency_symbol = company_currency.symbol or "$"
        max_revenue = max((r["revenue"] for r in customer_data.values()), default=0.0)
        dynamic_interval = self.get_dynamic_interval(max_revenue)

        kpis = {
            "total_revenue": round(total_revenue, 2),
            "top_customers_revenue": round(top_customers_total_revenue, 2),
            "top_customers_order_count": top_customers_total_orders,
            "top_customers_avg_order_value": round(top_customers_avg_order_value, 2),
            "overall_avg_order_value": round(overall_avg_order_value, 2),
            "percentage_share": round(percentage_share, 2),
            "total_orders": total_orders,
            "currency_symbol": currency_symbol,
            "dynamic_interval": dynamic_interval,
        }

        return {"data": customers_data, "kpis": kpis}

    @api.model
    def get_dashboard_stats(self, period, salesperson_id=False):
        """
        Get core dashboard statistics for the top 6 cards.
        Based on opportunities created/closed in the period, filtered by salesperson.
        """
        creation_domain, close_domain = self._build_domains(period, salesperson_id)

        # Total Opportunities: All created in period (active, non-won)
        total_opportunities = self.search_count(creation_domain)

        # Won Opportunities: Closed as won in period
        won_domain = close_domain + [
            ("stage_id.is_won", "=", True),
            ("active", "=", True),
        ]
        won_opportunities = self.search_count(won_domain)

        # Pipeline Value: Sum of expected_revenue for open
        # (non-won) opportunities created in period
        pipeline_opps = self.search(creation_domain)
        pipeline_value = sum(opp.expected_revenue for opp in pipeline_opps)

        start_date, end_date = get_period_start_date_and_end_date(period)
        sale_order_domain = [
            ("state", "in", ["sale", "done"]),
            ("date_order", ">=", start_date),
            ("date_order", "<=", end_date),
        ]
        if salesperson_id and int(salesperson_id):
            sale_order_domain.append(("user_id", "=", int(salesperson_id)))
        sale_orders = self.env["sale.order"].search(sale_order_domain)
        company_currency = self.env.company.currency_id

        # Convert amount_total to company currency if needed
        total_sales = 0.0
        for order in sale_orders:
            order_currency = order.pricelist_id.currency_id or company_currency
            amount = order.amount_total or 0.0
            if order_currency != company_currency:
                amount = order_currency._convert(
                    amount,
                    company_currency,
                    order.company_id,
                    order.date_order or fields.Date.today(),
                )
            total_sales += amount

        # Average Deal Size: Total Sales / Sale Order Count
        sale_order_count = len(sale_orders)
        average_deal_size = (
            total_sales / sale_order_count if sale_order_count > 0 else 0.0
        )

        open_quotation_domain = [
            ("state", "=", "draft"),
            ("date_order", ">=", start_date),
            ("date_order", "<=", end_date),
        ]
        if salesperson_id and int(salesperson_id):
            open_quotation_domain.append(("user_id", "=", int(salesperson_id)))
        open_quotations_orders = self.env["sale.order"].search(open_quotation_domain)

        # Convert amount_total to company currency if needed for open quotations
        open_quotations = 0.0
        for order in open_quotations_orders:
            order_currency = order.pricelist_id.currency_id or company_currency
            amount = order.amount_total or 0.0
            if order_currency != company_currency:
                amount = order_currency._convert(
                    amount,
                    company_currency,
                    order.company_id,
                    order.date_order or fields.Date.today(),
                )
            open_quotations += amount

        # Currency symbol
        currency_symbol = company_currency.symbol or "$"

        return {
            "total_opportunities": total_opportunities + won_opportunities,
            "won_opportunities": won_opportunities,
            "pipeline_value": pipeline_value,
            "total_sales": total_sales,
            "average_deal_size": average_deal_size,
            "open_quotations": open_quotations,
            "currency_symbol": currency_symbol,
        }
