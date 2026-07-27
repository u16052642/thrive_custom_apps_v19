/** @thrive-module **/

import { Component, useState, onWillStart, useRef, useEffect } from "@thrive/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { session } from "@web/session";
import { user } from "@web/core/user";

export class SolarDashboard extends Component {
    static template = "sp_solar_management.SolarDashboard";

    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.chartRef = useRef("salesChart");
        this.purchaseChartRef = useRef("purchaseChart");

        this.state = useState({
            data: null,
            loading: true,
            error: null,
            userName: user.name || "Admin",
        });

        onWillStart(async () => {
            await this.loadDashboardData();
        });

        useEffect(() => {
            if (this.state.data && this.chartRef.el) {
                this._renderChart();
            }
            if (this.state.data && this.purchaseChartRef.el) {
                this._renderPurchaseChart();
            }
        }, () => [this.state.data]);
    }


    async loadDashboardData() {
        this.state.loading = true;
        this.state.error = null;

        try {
            this.state.data = await this.orm.call(
                "solar.dashboard",
                "get_dashboard_data",
                []
            );
        } catch (e) {
            console.error("Solar Dashboard Error:", e);
            this.state.error = e.message || "Failed to load dashboard data.";
        } finally {
            this.state.loading = false;
        }
    }




    get pipelineSalesStyle() {
        const rights = this.state.data?.user_rights;
        if (!rights) return "grid-template-columns: 1fr !important;";
        const hasPipeline = rights.is_sales || rights.is_tech || rights.is_pm || rights.is_hr;
        const hasActivities = !!this.state.data?.recent_activities?.length;
        if (hasPipeline && hasActivities) {
            return "grid-template-columns: 60% 40% !important;";
        }
        return "grid-template-columns: 1fr !important;";
    }

    formatCurrency(amount) {
        if (amount === undefined || amount === null) amount = 0;
        const symbol = this.state.data?.currency_symbol || "₹";
        const position = this.state.data?.currency_position || "before";

        const formattedAmount = Number(amount).toLocaleString(undefined, {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });

        if (position === "after") {
            return `${formattedAmount} ${symbol}`;
        } else {
            return `${symbol} ${formattedAmount}`;
        }
    }

    formatNumber(num) {
        return num ?? "0";
    }

    getChangeClass(change) {
        if (change > 0) return "positive";
        if (change < 0) return "negative";
        return "";
    }

    getChangeIcon(change) {
        return change >= 0 ? "fa-arrow-up" : "fa-arrow-down";
    }

    absChange(change) {
        return Math.abs(change || 0);
    }

    getProgressClass(progress) {
        if (progress >= 80) return "high";
        if (progress >= 40) return "medium";
        return "low";
    }

    getStockBadgeClass(status) {
        if (status === "good") return "badge-good";
        if (status === "low") return "badge-low";
        return "badge-out";
    }

    getStockBadgeLabel(status) {
        if (status === "good") return "Good";
        if (status === "low") return "Low Stock";
        return "Out of Stock";
    }

    openLeads() {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Pipeline",
            res_model: "crm.lead",
            views: [[false, "kanban"], [false, "list"], [false, "form"]],
            domain: [["type", "=", "opportunity"]],
            context: { default_type: "opportunity" },
        });
    }

    openInspections() {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Ongoing Site Inspections",
            res_model: "solar.site.inspection",
            views: [[false, "list"], [false, "form"]],
            context: { search_default_filter_in_progress: 1 },
        });
    }

    openInstallations() {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Ongoing Installations",
            res_model: "solar.installation",
            views: [[false, "list"], [false, "form"]],
            context: { search_default_filter_in_progress: 1 },
        });
    }

    openCompletedProjects() {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Completed Projects",
            res_model: "solar.installation",
            views: [[false, "list"], [false, "form"]],
            context: { search_default_filter_completed: 1 },
        });
    }

    openMaintenanceRequests() {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Maintenance Requests",
            res_model: "maintenance.request",
            views: [[false, "list"], [false, "form"]],
        });
    }

    openOpenMaintenanceRequests() {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Open Maintenance Requests",
            res_model: "maintenance.request",
            views: [[false, "list"], [false, "form"]],
            domain: [["archive", "=", false], ["stage_id.name", "=", "New Request"]],
        });
    }

    openInProgressMaintenanceRequests() {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "In Progress Maintenance Requests",
            res_model: "maintenance.request",
            views: [[false, "list"], [false, "form"]],
            domain: [["archive", "=", false], ["stage_id.name", "=", "In Progress"]],
        });
    }

    openCompletedMaintenanceRequests() {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Completed Maintenance Requests",
            res_model: "maintenance.request",
            views: [[false, "list"], [false, "form"]],
            domain: [["archive", "=", false], ["stage_id.done", "=", true]],
        });
    }

    openOverdueMaintenanceRequests() {
        const now = new Date();
        const pad = (n) => n < 10 ? '0' + n : n;
        const dateStr = `${now.getUTCFullYear()}-${pad(now.getUTCMonth() + 1)}-${pad(now.getUTCDate())} ${pad(now.getUTCHours())}:${pad(now.getUTCMinutes())}:${pad(now.getUTCSeconds())}`;
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Overdue Maintenance Requests",
            res_model: "maintenance.request",
            views: [[false, "list"], [false, "form"]],
            domain: [["archive", "=", false], ["stage_id.done", "=", false], ["schedule_date", "<", dateStr]],
        });
    }

    openInvoices() {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Customer Invoices",
            res_model: "account.move",
            views: [[false, "list"], [false, "form"]],
            domain: [["move_type", "=", "out_invoice"]],
        });
    }

    openContracts() {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Active Service Contracts",
            res_model: "solar.contract",
            views: [[false, "list"], [false, "form"]],
            domain: [["status", "=", "active"]],
        });
    }

    openWarranties() {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Active Warranties",
            res_model: "solar.warranty.claim",
            views: [[false, "list"], [false, "form"]],
            domain: [["state", "=", "active"]],
        });
    }

    openEnergyBills() {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Energy Bills",
            res_model: "solar.energy.billing",
            views: [[false, "list"], [false, "form"]],
        });
    }

    openInventory(ev) {
        if(ev) ev.preventDefault();
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Inventory",
            res_model: "product.product",
            views: [[false, "list"], [false, "form"]],
            domain: [["type", "in", ["product", "consu"]]],
        });
    }

    openSaleOrders() {
        this.actionService.doAction("sale.action_orders", {
            additionalContext: { search_default_sales: 1 }
        });
    }

    openPendingOrders() {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Pending Orders",
            res_model: "sale.order",
            views: [[false, "list"], [false, "form"]],
            domain: [["state", "in", ["sale", "done"]], ["invoice_status", "=", "to invoice"]],
        });
    }

    openPendingPayments() {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Pending Payments",
            res_model: "account.move",
            views: [[false, "list"], [false, "form"]],
            domain: [["move_type", "=", "out_invoice"], ["state", "=", "posted"], ["payment_state", "in", ["not_paid", "partial"]]],
        });
    }

    openPipelineStage(stage) {
        const stageActions = {
            Lead: {
                name: "Leads",
                res_model: "crm.lead",
            },
            "Document Pending": {
                name: "Document Pending Leads",
                res_model: "crm.lead",
                domain: [["solar_stage", "=", "document_pending"]],
            },
            Inspection: {
                name: "Site Inspections",
                res_model: "solar.site.inspection",
            },
            "SSEG Application": {
                name: "SSEG Applications",
                res_model: "solar.government.approval",
            },
            Installation: {
                name: "Installations",
                res_model: "solar.installation",
            },
        };
        const action = stageActions[stage?.name];
        if (!action) {
            return;
        }
        this.actionService.doAction({
            type: "ir.actions.act_window",
            views: [[false, "list"], [false, "form"]],
            ...action,
        });
    }

    openQuotations() {
        this.actionService.doAction("sale.action_quotations", {
            additionalContext: { search_default_draft: 1 }
        });
    }

    openLateReceiving() {
        const now = new Date();
        const pad = (n) => n < 10 ? '0' + n : n;
        const dateStr = `${now.getUTCFullYear()}-${pad(now.getUTCMonth() + 1)}-${pad(now.getUTCDate())} ${pad(now.getUTCHours())}:${pad(now.getUTCMinutes())}:${pad(now.getUTCSeconds())}`;
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Late Receiving",
            res_model: "stock.picking",
            views: [[false, "list"], [false, "form"]],
            domain: [["picking_type_id.code", "=", "incoming"], ["state", "not in", ["done", "cancel"]], ["scheduled_date", "<", dateStr]],
        });
    }

    openToReceive() {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "To Receive",
            res_model: "stock.picking",
            views: [[false, "list"], [false, "form"]],
            domain: [["picking_type_id.code", "=", "incoming"], ["state", "not in", ["done", "cancel"]]],
        });
    }

    openReceived() {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Received",
            res_model: "stock.picking",
            views: [[false, "list"], [false, "form"]],
            domain: [["picking_type_id.code", "=", "incoming"], ["state", "=", "done"]],
        });
    }

    openActivity(act) {
        if (act.res_model && act.res_id) {
            this.actionService.doAction({
                type: "ir.actions.act_window",
                res_model: act.res_model,
                res_id: act.res_id,
                views: [[false, "form"]],
                target: "current",
            });
        }
    }

    openPipelineRecord(rec) {
        if (rec.res_model && rec.id) {
            this.actionService.doAction({
                type: "ir.actions.act_window",
                res_model: rec.res_model,
                res_id: rec.id,
                views: [[false, "form"]],
                target: "current",
            });
        }
    }

    _renderChart() {
        const canvas = this.chartRef.el;
        if (!canvas || !this.state.data) return;

        const data = this.state.data.sales_chart_data || {};
        if (!data.labels?.length) return;

        const ctx = canvas.getContext("2d");
        const W = canvas.parentElement?.clientWidth || 520;
        const H = 260;

        canvas.width = W;
        canvas.height = H;

        const pad = { top: 18, right: 42, bottom: 36, left: 52 };
        const chartW = W - pad.left - pad.right;
        const chartH = H - pad.top - pad.bottom;
        const maxBar = Math.max(
            Math.max(...data.quotations, 1),
            Math.max(...data.orders, 1)
        ) * 1.3;
        const maxLine = Math.max(...data.revenue, 1) * 1.3;
        const colW = chartW / data.labels.length;

        ctx.clearRect(0, 0, W, H);
        ctx.font = "12px Inter, sans-serif";

        ctx.strokeStyle = "#e5e7eb";
        ctx.lineWidth = 1;
        ctx.fillStyle = "#64748b";
        ctx.textAlign = "right";
        [0, 0.25, 0.5, 0.75, 1].forEach((step) => {
            const y = pad.top + chartH - chartH * step;
            ctx.beginPath();
            ctx.moveTo(pad.left, y);
            ctx.lineTo(pad.left + chartW, y);
            ctx.stroke();
            ctx.fillText(Math.round(maxBar * step), pad.left - 10, y + 4);
        });

        data.labels.forEach((label, i) => {
            const x = pad.left + i * colW;
            const bw = Math.min(colW * 0.24, 28);
            const qH = (data.quotations[i] / maxBar) * chartH;
            const oH = (data.orders[i] / maxBar) * chartH;

            ctx.fillStyle = "rgba(37, 99, 235, 0.38)";
            ctx.fillRect(x + colW * 0.16, pad.top + chartH - qH, bw, Math.max(qH, 1));
            ctx.fillStyle = "rgba(37, 99, 235, 0.74)";
            ctx.fillRect(x + colW * 0.48, pad.top + chartH - oH, bw, Math.max(oH, 1));

            ctx.fillStyle = "#64748b";
            ctx.textAlign = "center";
            ctx.fillText(label, x + colW / 2, pad.top + chartH + 24);
        });

        ctx.beginPath();
        ctx.strokeStyle = "#22c55e";
        ctx.lineWidth = 2.5;
        data.labels.forEach((_, i) => {
            const x = pad.left + i * colW + colW / 2;
            const y = pad.top + chartH - (data.revenue[i] / maxLine) * chartH;
            if (i === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        });
        ctx.stroke();

        data.labels.forEach((_, i) => {
            const x = pad.left + i * colW + colW / 2;
            const y = pad.top + chartH - (data.revenue[i] / maxLine) * chartH;
            ctx.beginPath();
            ctx.fillStyle = "#22c55e";
            ctx.arc(x, y, 4, 0, Math.PI * 2);
            ctx.fill();
        });
    }

    _renderPurchaseChart() {
        const canvas = this.purchaseChartRef.el;
        if (!canvas || !this.state.data) return;

        const data = this.state.data.purchase_chart_data || {};
        if (!data.labels?.length) return;

        const ctx = canvas.getContext("2d");
        const W = canvas.parentElement?.clientWidth || 520;
        const H = 260;

        canvas.width = W;
        canvas.height = H;

        const pad = { top: 18, right: 42, bottom: 36, left: 52 };
        const chartW = W - pad.left - pad.right;
        const chartH = H - pad.top - pad.bottom;
        const maxBar = Math.max(
            Math.max(...data.rfqs, 1),
            Math.max(...data.orders, 1)
        ) * 1.3;
        const maxLine = Math.max(...data.expenses, 1) * 1.3;
        const colW = chartW / data.labels.length;

        ctx.clearRect(0, 0, W, H);
        ctx.font = "12px Inter, sans-serif";

        ctx.strokeStyle = "#e5e7eb";
        ctx.lineWidth = 1;
        ctx.fillStyle = "#64748b";
        ctx.textAlign = "right";
        [0, 0.25, 0.5, 0.75, 1].forEach((step) => {
            const y = pad.top + chartH - chartH * step;
            ctx.beginPath();
            ctx.moveTo(pad.left, y);
            ctx.lineTo(pad.left + chartW, y);
            ctx.stroke();
            ctx.fillText(Math.round(maxBar * step), pad.left - 10, y + 4);
        });

        data.labels.forEach((label, i) => {
            const x = pad.left + i * colW;
            const bw = Math.min(colW * 0.24, 28);
            const rH = (data.rfqs[i] / maxBar) * chartH;
            const oH = (data.orders[i] / maxBar) * chartH;

            // Orange for RFQs
            ctx.fillStyle = "rgba(245, 158, 11, 0.4)";
            ctx.fillRect(x + colW * 0.16, pad.top + chartH - rH, bw, Math.max(rH, 1));
            // Green for Orders
            ctx.fillStyle = "rgba(16, 185, 129, 0.74)";
            ctx.fillRect(x + colW * 0.48, pad.top + chartH - oH, bw, Math.max(oH, 1));

            ctx.fillStyle = "#64748b";
            ctx.textAlign = "center";
            ctx.fillText(label, x + colW / 2, pad.top + chartH + 24);
        });

        // Expenses line (Red)
        ctx.beginPath();
        ctx.strokeStyle = "#ef4444";
        ctx.lineWidth = 2.5;
        data.labels.forEach((_, i) => {
            const x = pad.left + i * colW + colW / 2;
            const y = pad.top + chartH - (data.expenses[i] / maxLine) * chartH;
            if (i === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        });
        ctx.stroke();

        data.labels.forEach((_, i) => {
            const x = pad.left + i * colW + colW / 2;
            const y = pad.top + chartH - (data.expenses[i] / maxLine) * chartH;
            ctx.beginPath();
            ctx.fillStyle = "#ef4444";
            ctx.arc(x, y, 4, 0, Math.PI * 2);
            ctx.fill();
        });
    }
}

registry.category("actions").add("solar_dashboard", SolarDashboard);
