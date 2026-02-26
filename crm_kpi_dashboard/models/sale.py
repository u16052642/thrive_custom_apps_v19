import logging
from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta

from thrive import api, fields, models

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def get_period_date(self, period):
        # Compute date range based on `period`
        today = fields.Date.context_today(self)

        if period == "today":
            start_date = end_date = today
        elif period == "yesterday":
            start_date = end_date = today - timedelta(days=1)
        elif period == "week":
            start_date = today - timedelta(days=today.weekday())
            end_date = start_date + timedelta(days=6)
        elif period == "last_week":
            end_date = today - timedelta(days=today.weekday() + 1)
            start_date = end_date - timedelta(days=6)
        elif period == "month":
            start_date = today.replace(day=1)
            end_date = (start_date + relativedelta(months=1)) - timedelta(days=1)
        elif period == "last_month":
            start_date = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
            end_date = today.replace(day=1) - timedelta(days=1)
        elif period == "quarter":
            current_quarter = (today.month - 1) // 3 + 1
            start_date = today.replace(month=3 * current_quarter - 2, day=1)
            end_date = (start_date + relativedelta(months=3)) - timedelta(days=1)
        elif period == "last_quarter":
            current_quarter = (today.month - 1) // 3 + 1
            last_quarter = current_quarter - 1 if current_quarter > 1 else 4
            last_quarter_year = today.year if current_quarter > 1 else today.year - 1
            start_month = 3 * last_quarter - 2
            start_date = today.replace(year=last_quarter_year, month=start_month, day=1)
            end_date = (start_date + relativedelta(months=3)) - timedelta(days=1)
        elif period == "year":
            start_date = today.replace(month=1, day=1)
            end_date = today.replace(month=12, day=31)
        elif period == "last_year":
            start_date = today.replace(year=today.year - 1, month=1, day=1)
            end_date = today.replace(year=today.year - 1, month=12, day=31)
        else:
            # Default: last 30 days
            end_date = today
            start_date = today - timedelta(days=29)

        return start_date, end_date

    def get_result_data(
        self,
        data_map,
        start_date,
        end_date,
        salesperson_id,
        quotation_data,
        order_data,
        group_by,
    ):
        # Generate ordered result
        result = []
        if group_by == "day":
            current = start_date
            while current <= end_date:
                key = current.strftime("%Y-%m-%d")
                if key in data_map:
                    result.append(
                        {
                            "date": data_map[key]["date"],
                            "label": data_map[key]["label"],
                            "quotation_total": data_map[key]["quotation_total"],
                            "quotation_count": data_map[key]["quotation_count"],
                            "order_total": data_map[key]["order_total"],
                            "order_count": data_map[key]["order_count"],
                        }
                    )
                else:
                    result.append(
                        {
                            "date": current.strftime("%Y-%m-%d"),
                            "label": current.strftime("%d %b"),
                            "quotation_total": 0,
                            "quotation_count": 0,
                            "order_total": 0,
                            "order_count": 0,
                        }
                    )
                current += timedelta(days=1)

        elif group_by == "week":
            week_num = 1
            current = start_date
            while current <= end_date:
                # Calculate week range
                week_start = current
                week_end = min(current + timedelta(days=6), end_date)
                key = (
                    f"{week_start.strftime('%Y-%m-%d')}_{week_end.strftime('%Y-%m-%d')}"
                )

                if key in data_map:
                    result.append(
                        {
                            "date": week_start.strftime(
                                "%Y-%m-%d"
                            ),  # Use first day of week as date
                            "label": data_map[key]["label"],
                            "quotation_total": data_map[key]["quotation_total"],
                            "quotation_count": data_map[key]["quotation_count"],
                            "order_total": data_map[key]["order_total"],
                            "order_count": data_map[key]["order_count"],
                        }
                    )
                else:
                    result.append(
                        {
                            "date": week_start.strftime("%Y-%m-%d"),
                            "label": f"Week {week_num}",
                            "quotation_total": 0,
                            "quotation_count": 0,
                            "order_total": 0,
                            "order_count": 0,
                        }
                    )

                current = week_end + timedelta(days=1)
                week_num += 1

        elif group_by == "month":
            current = start_date.replace(day=1)
            while current <= end_date:
                key = current.strftime("%Y-%m")
                if key in data_map:
                    result.append(
                        {
                            "date": current.strftime(
                                "%Y-%m-%d"
                            ),  # Use first day of month as date
                            "label": data_map[key]["label"],
                            "quotation_total": data_map[key]["quotation_total"],
                            "quotation_count": data_map[key]["quotation_count"],
                            "order_total": data_map[key]["order_total"],
                            "order_count": data_map[key]["order_count"],
                        }
                    )
                else:
                    result.append(
                        {
                            "date": current.strftime("%Y-%m-%d"),
                            "label": current.strftime("%b %Y"),
                            "quotation_total": 0,
                            "quotation_count": 0,
                            "order_total": 0,
                            "order_count": 0,
                        }
                    )

                # Move to next month
                if current.month == 12:
                    current = current.replace(year=current.year + 1, month=1, day=1)
                else:
                    current = current.replace(month=current.month + 1, day=1)

        elif group_by == "quarter":
            current = start_date.replace(
                month=(((start_date.month - 1) // 3) * 3) + 1, day=1
            )
            while current <= end_date:
                quarter = (current.month - 1) // 3 + 1
                key = f"{current.year}-Q{quarter}"
                if key in data_map:
                    result.append(
                        {
                            "date": current.strftime("%Y-%m-%d"),
                            "label": data_map[key]["label"],
                            "quotation_total": data_map[key]["quotation_total"],
                            "quotation_count": data_map[key]["quotation_count"],
                            "order_total": data_map[key]["order_total"],
                            "order_count": data_map[key]["order_count"],
                        }
                    )
                else:
                    result.append(
                        {
                            "date": current.strftime("%Y-%m-%d"),
                            "label": f"Q{quarter} {current.year}",
                            "quotation_total": 0,
                            "quotation_count": 0,
                            "order_total": 0,
                            "order_count": 0,
                        }
                    )

                # Move to next quarter
                if quarter == 4:
                    current = current.replace(year=current.year + 1, month=1, day=1)
                else:
                    current = current.replace(month=3 * quarter + 1, day=1)

        return result

    @api.model
    def get_quotation_vs_order_data(self, period, salesperson_id=False):
        start_date, end_date = self.get_period_date(period)

        # Convert to datetime for domain
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())

        domain = [
            ("date_order", ">=", fields.Datetime.to_string(start_dt)),
            ("date_order", "<=", fields.Datetime.to_string(end_dt)),
            ("state", "!=", "cancel"),
        ]
        if salesperson_id and salesperson_id != 0:
            domain.append(("user_id", "=", salesperson_id))

        # Determine grouping based on period
        if period in ["today", "yesterday", "week", "last_week"]:
            group_by = "day"
        elif period in ["month", "last_month"]:
            group_by = "week"
        elif period in ["quarter", "last_quarter"]:
            group_by = "month"
        elif period in ["year", "last_year"]:
            group_by = "quarter"
        else:
            group_by = "day"

        # Quotation bucket - draft and sent states
        quotation_domain = domain + [("state", "in", ["draft", "sent"])]
        quotation_data = self._get_grouped_data(
            quotation_domain, group_by, start_date, end_date
        )

        # Sales Order bucket - confirmed sales
        order_domain = domain + [("state", "=", "sale")]
        order_data = self._get_grouped_data(
            order_domain, group_by, start_date, end_date
        )

        # Merge data by label
        data_map = {}
        for rec in quotation_data:
            data_map[rec["key"]] = {
                "quotation_total": rec["amount_total"],
                "quotation_count": rec["count"],
                "order_total": 0,
                "order_count": 0,
                "label": rec["label"],
                "date": rec["date"],
            }

        for rec in order_data:
            if rec["key"] in data_map:
                data_map[rec["key"]].update(
                    {
                        "order_total": rec["amount_total"],
                        "order_count": rec["count"],
                    }
                )
            else:
                data_map[rec["key"]] = {
                    "quotation_total": 0,
                    "quotation_count": 0,
                    "order_total": rec["amount_total"],
                    "order_count": rec["count"],
                    "label": rec["label"],
                    "date": rec["date"],
                }

        result = self.get_result_data(
            data_map,
            start_date,
            end_date,
            salesperson_id,
            quotation_data,
            order_data,
            group_by,
        )

        # Get the company currency symbol
        company = self.env.company
        currency_symbol = company.currency_id.symbol

        MailMessage = self.env["mail.message"]

        subtype = self.env.ref("sale.mt_order_confirmed")
        messages = MailMessage.search(
            [
                ("model", "=", "sale.order"),
                ("subtype_id", "=", subtype.id),
                ("date", ">=", fields.Datetime.to_string(start_dt)),
                ("date", "<=", fields.Datetime.to_string(end_dt)),
            ]
        )
        converted_order_ids = self.browse(set(messages.mapped("res_id")))
        if salesperson_id and salesperson_id != 0:
            converted_order_ids = converted_order_ids.filtered(
                lambda o: o.user_id.id == salesperson_id
            )

        total_orders = sum(
            data["amount_total"] for data in order_data if data["amount_total"] > 0
        )

        open_quotations = sum(
            data["amount_total"] for data in quotation_data if data["amount_total"] > 0
        )

        total_quotations = open_quotations + total_orders

        conversion_percent = (
            (sum(converted_order_ids.mapped("amount_total")) / total_quotations) * 100
            if total_quotations > 0
            else 0
        )

        return {
            "data": result,
            "currency_symbol": currency_symbol,
            "conversion_percent": round(conversion_percent, 2),
            "open_quotations": open_quotations,
            "total_quotations": total_quotations,
            "total_orders": total_orders,
        }

    def _get_grouped_data(self, domain, group_by, start_date, end_date):
        """
        Get data grouped by the specified time period
        """
        orders = self.search(domain)
        grouped_data = {}
        company_currency = self.env.company.currency_id

        for order in orders:
            if not order.date_order:
                continue
            dt = order.date_order.date()

            if group_by == "day":
                key = dt.strftime("%Y-%m-%d")
                label = dt.strftime("%d %b")
                date_str = dt.strftime("%Y-%m-%d")

            elif group_by == "week":
                week_start = dt - timedelta(days=dt.weekday())
                week_end = week_start + timedelta(days=6)
                key = (
                    f"{week_start.strftime('%Y-%m-%d')}_{week_end.strftime('%Y-%m-%d')}"
                )
                label = f"Week {(dt - start_date).days // 7 + 1}"
                date_str = week_start.strftime("%Y-%m-%d")

            elif group_by == "month":
                key = dt.strftime("%Y-%m")
                label = dt.strftime("%b %Y")
                date_str = dt.replace(day=1).strftime("%Y-%m-%d")

            elif group_by == "quarter":
                quarter = (dt.month - 1) // 3 + 1
                key = f"{dt.year}-Q{quarter}"
                label = f"Q{quarter} {dt.year}"
                # first day of that quarter
                start_month = 3 * quarter - 2
                date_str = dt.replace(month=start_month, day=1).strftime("%Y-%m-%d")

            else:
                continue  # safety fallback

            if key not in grouped_data:
                grouped_data[key] = {
                    "amount_total": 0,
                    "count": 0,
                    "label": label,
                    "date": date_str,
                    "key": key,
                }

            # ✅ Convert order.amount_total into company currency
            amount = order.currency_id._convert(
                order.amount_total,
                company_currency,
                order.company_id,
                order.date_order or fields.Date.context_today(self),
            )

            grouped_data[key]["amount_total"] += round(amount) or 0
            grouped_data[key]["count"] += 1

        return list(grouped_data.values())
