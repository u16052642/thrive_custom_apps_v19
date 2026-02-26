/** @thrive-module **/
/* global $ */
import {registry} from "@web/core/registry";
import {Component, useState, onMounted, onWillStart} from "@thrive/owl";
import {useService} from "@web/core/utils/hooks";
import {rpc} from "@web/core/network/rpc";
import { Tooltip } from "@web/core/tooltip/tooltip";


// Add the Highcharts animation extension (paste this at the top of your JS file)
const addDonutAnimation = (H) => {
    H.seriesTypes.pie.prototype.animate = function (init) {
        const series = this,
            chart = series.chart,
            points = series.points,
            {animation} = series.options,
            {startAngleRad} = series;

        function fanAnimate(point, startAngleRad) {
            const graphic = point.graphic,
                args = point.shapeArgs;

            if (graphic && args) {
                graphic
                    // Set inital animation values
                    .attr({
                        start: startAngleRad,
                        end: startAngleRad,
                        opacity: 1,
                    })
                    // Animate to the final position
                    .animate(
                        {
                            start: args.start,
                            end: args.end,
                        },
                        {
                            duration: animation.duration / points.length,
                        },
                        function () {
                            // On complete, start animating the next point
                            if (points[point.index + 1]) {
                                fanAnimate(points[point.index + 1], args.end);
                            }
                            // On the last point, fade in the data labels, then
                            // apply the inner size
                            if (point.index === series.points.length - 1) {
                                series.dataLabelsGroup.animate(
                                    {
                                        opacity: 1,
                                    },
                                    void 0,
                                    function () {
                                        points.forEach((point) => {
                                            point.opacity = 1;
                                        });
                                        series.update(
                                            {
                                                enableMouseTracking: true,
                                            },
                                            false
                                        );
                                        chart.update({
                                            plotOptions: {
                                                pie: {
                                                    innerSize: "50%",
                                                    borderRadius: 0,
                                                },
                                            },
                                        });
                                    }
                                );
                            }
                        }
                    );
            }
        }

        if (init) {
            // Hide points on init
            points.forEach((point) => {
                point.opacity = 0;
            });
        } else {
            fanAnimate(points[0], startAngleRad);
        }
    };
};
// Mouse Wheel Scroll Helper for Highcharts
const addMouseWheelScroll = (chartConfig, options = {}) => {
    const {
        scrollSpeed = 1, // 10% of visible range per scroll
        invertScroll = false, // Reverse scroll direction
    } = options;

    // Deep clone to avoid mutating original config
    // const config = JSON.parse(JSON.stringify(chartConfig));
    const config = {...chartConfig};
    // Store original events
    const originalEvents = config.chart?.events || {};

    // Add/merge load event
    config.chart = config.chart || {};
    config.chart.events = {
        ...originalEvents,
        load: function () {
            // Call original load handler if exists
            // if (originalEvents.load) {
            //     originalEvents.load.call(this);
            // }
            if (originalEvents.load && typeof originalEvents.load === "function") {
                originalEvents.load.call(this);
            }

            const chart = this;

            // Detect which axis has categories
            // const xHasCategories = config.xAxis?.categories && config.xAxis.categories.length > 0;
            // const yHasCategories = config.yAxis?.categories && config.yAxis.categories.length > 0;
            const xHasCategories =
                (config.xAxis?.categories && config.xAxis.categories.length > 0) ||
                config.xAxis?.type === "category";
            const yHasCategories =
                (config.yAxis?.categories && config.yAxis.categories.length > 0) ||
                config.yAxis?.type === "category";
            let targetAxis;

            if (xHasCategories) {
                targetAxis = chart.xAxis[0];
            } else if (yHasCategories) {
                targetAxis = chart.yAxis[0];
            } else {
                console.warn("No categorical axis found for scrolling");
                return;
            }

            // Only add scroll if axis has min/max set (indicating scrollable content)
            const extremes = targetAxis.getExtremes();
            if (
                extremes.max === extremes.dataMax &&
                extremes.min === extremes.dataMin
            ) {
                // No scrolling needed - all data is visible
                return;
            }

            // Add mouse wheel scroll listener
            chart.container.addEventListener("wheel", function (e) {
                e.preventDefault();

                const extremes = targetAxis.getExtremes();
                const range = extremes.max - extremes.min;
                const step = range * scrollSpeed;

                let newMin, newMax;
                const scrollDirection = invertScroll ? -1 : 1;

                if (e.deltaY > 0) {
                    // Scroll forward (right for X-axis, down for Y-axis)
                    newMin = extremes.min + step * scrollDirection;
                    newMax = extremes.max + step * scrollDirection;
                } else {
                    // Scroll backward (left for X-axis, up for Y-axis)
                    newMin = extremes.min - step * scrollDirection;
                    newMax = extremes.max - step * scrollDirection;
                }

                // Keep within data bounds
                if (newMin < extremes.dataMin) {
                    newMin = extremes.dataMin;
                    newMax = extremes.dataMin + range;
                } else if (newMax > extremes.dataMax) {
                    newMax = extremes.dataMax;
                    newMin = extremes.dataMax - range;
                }

                targetAxis.setExtremes(newMin, newMax);
            });
        },
    };
    return config;
};

// Call the animation function
addDonutAnimation(Highcharts);

export class CRMGraphDashboard extends Component {
    static template = "CRMDashboardMain";

    setup() {
        this.orm = useService("orm");
        this.state = useState({
            currentUser: {name: ""},
            performance_overview: [],
            lost_reason_data: [],
            selectedStages: null,
            funnel_data: {},
            quotation_vs_order_data: [],
            period: "month",
            salesperson_id: 0, // Default to "All Sales Persons"
            salesPersons: [],
            top_salespersons_data: [],
            opportunities_by_source_data: [],
            country_revenue: [], // Add this
            country_kpis: {},
            top_customers_data: [], // Add this
            top_customers_kpis: {}, // Add this
            country_chart_filter: "country",
            opportunities_by_tag_data: {
                result: [],
                all_tags: [], // Initialize with empty array
                total_expected_revenue_by_tags: 0,
                total_won_revenue_by_tags: 0,
                hidden_tags: [],
            },
            hiddenTagIds: [], // Track hidden tag IDs
            dashboard_stats: {},
        });

        onWillStart(async () => {
            const url = new URL(window.location.href);
            const period = url.searchParams.get("period");
            const salespersonId = url.searchParams.get("salesperson_id");

            if (period) {
                this.state.period = period;
            }
            if (salespersonId !== null) {
                this.state.salesperson_id = parseInt(salespersonId);
            }
            this.state.currentUser = await this.orm.call(
                "crm.lead",
                "get_current_user_info",
                []
            );

            await this.fetchAllData();
            await this.fetchSalesPersons();
        });

        onMounted(() => {
            this.renderAllCharts();
            this.updateDashboardStats();
            this.initTooltip();
        });
    }

    initTooltip() {
        // Safety check
        if (!this.tooltipCleanups) {
            console.warn('tooltipCleanups not initialized');
            this.tooltipCleanups = [];
        }

        const tooltipElements = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        
        tooltipElements.forEach(el => {
            const tooltipText = el.getAttribute('title') || 
                            el.getAttribute('data-bs-original-title') ||
                            el.getAttribute('data-original-title');
            
            if (tooltipText) {
                // Store original title and remove it
                el.setAttribute('data-tooltip-text', tooltipText);
                el.removeAttribute('title');
                
                const showTooltip = () => {
                    // Remove any existing tooltip first
                    if (el._tooltip) {
                        el._tooltip.remove();
                    }
                    
                    const tooltip = document.createElement('div');
                    tooltip.className = 'custom-tooltip-wrapper';
                    
                    const tooltipInner = document.createElement('div');
                    tooltipInner.className = 'tooltip-inner';
                    tooltipInner.textContent = tooltipText;
                    
                    Object.assign(tooltipInner.style, {
                        maxWidth: '400px',           // limit width
                    });

                    tooltip.appendChild(tooltipInner);
                    
                    // Base styles for wrapper
                    Object.assign(tooltip.style, {
                        position: 'fixed',
                        zIndex: '9999',
                        pointerEvents: 'none',
                    });
                    
                    document.body.appendChild(tooltip);
                    
                    // Calculate position
                    const rect = el.getBoundingClientRect();
                    const tooltipRect = tooltip.getBoundingClientRect();
                    const placement = el.getAttribute('data-bs-placement') || 'right';
                    
                    let left, top;
                    
                    switch(placement) {
                        case 'right':
                            left = rect.right + 10;
                            top = rect.top + (rect.height / 2) - (tooltipRect.height / 2);
                            break;
                        case 'left':
                            left = rect.left - tooltipRect.width - 10;
                            top = rect.top + (rect.height / 2) - (tooltipRect.height / 2);
                            break;
                        case 'bottom':
                            left = rect.left + (rect.width / 2) - (tooltipRect.width / 2);
                            top = rect.bottom + 10;
                            break;
                        case 'top':
                            left = rect.left + (rect.width / 2) - (tooltipRect.width / 2);
                            top = rect.top - tooltipRect.height - 10;
                            break;
                        default: // right
                            left = rect.right + 10;
                            top = rect.top + (rect.height / 2) - (tooltipRect.height / 2);
                            break;
                    }
                    
                    // Keep tooltip within viewport
                    const padding = 10;
                    left = Math.max(padding, Math.min(left, window.innerWidth - tooltipRect.width - padding));
                    top = Math.max(padding, Math.min(top, window.innerHeight - tooltipRect.height - padding));
                    
                    tooltip.style.left = left + 'px';
                    tooltip.style.top = top + 'px';
                    
                    // Add fade-in animation
                    tooltip.style.opacity = '0';
                    tooltip.style.transition = 'opacity 0.2s ease-in-out';
                    setTimeout(() => {
                        tooltip.style.opacity = '1';
                    }, 10);
                    
                    el._tooltip = tooltip;
                };
                
                const hideTooltip = () => {
                    if (el._tooltip) {
                        // Fade out animation
                        el._tooltip.style.opacity = '0';
                        setTimeout(() => {
                            if (el._tooltip) {
                                el._tooltip.remove();
                                el._tooltip = null;
                            }
                        }, 200);
                    }
                };
                
                // Add event listeners
                el.addEventListener('mouseenter', showTooltip);
                el.addEventListener('mouseleave', hideTooltip);
                el.addEventListener('click', hideTooltip);
                
                // Store cleanup function
                this.tooltipCleanups.push(() => {
                    hideTooltip();
                    el.removeEventListener('mouseenter', showTooltip);
                    el.removeEventListener('mouseleave', hideTooltip);
                    el.removeEventListener('click', hideTooltip);
                });
            }
        });
    }

    cleanupTooltips() {
        this.tooltipCleanups.forEach(cleanup => {
            if (typeof cleanup === 'function') {
                cleanup();
            }
        });
        this.tooltipCleanups = [];
    }

    // Helper function to format numbers in K/M format
    formatCurrency(
        value,
        currencySymbol = "$",
        showSymbol = true,
        showDecimals = true
    ) {
        if (!value || value === 0) return showSymbol ? currencySymbol + " 0" : "0";

        const absValue = Math.abs(value);
        let formattedValue = "";

        if (absValue >= 1000000) {
            formattedValue = (value / 1000000).toFixed(showDecimals ? 1 : 0) + "M";
        } else if (absValue >= 1000) {
            formattedValue = (value / 1000).toFixed(showDecimals ? 1 : 0) + "k";
        } else {
            formattedValue = value.toString();
        }
        return showSymbol ? currencySymbol + formattedValue : formattedValue;
    }

    async fetchAllData() {
        await Promise.all([
            this.fetchDashboardStats(),
            this.fetchQuotationVsOrderData(),
            this.fetchPerformanceOverview(),
            this.fetchFunneOpportunityPipeline(),
            this.fetchTopSalespersonsData(),
            this.fetchOpportunitiesBySourceData(),
            this.fetchOpportunitiesByTagData(),
            this.fetchTopCustomersData(),
            this.fetchCountryWiseRevenue(),
            this.fetchLostReasonData(),
            this.loadCountryChartFilter(),
            this.loadHiddenTags(),
            this.loadHiddenSources(),
        ]);
    }
    // New method to fetch dashboard stats
    async fetchDashboardStats() {
        try {
            const result = await this.orm.call("crm.lead", "get_dashboard_stats", [
                this.state.period,
                this.state.salesperson_id,
            ]);
            this.state.dashboard_stats = result || {};
        } catch (error) {
            console.error("Error fetching dashboard stats:", error);
            this.state.dashboard_stats = {
                total_opportunities: 0,
                won_opportunities: 0,
                pipeline_value: 0,
                total_sales: 0,
                average_deal_size: 0,
                open_quotations: 0,
                currency_symbol: "$",
            };
        }
    }

    updateDashboardStats() {
        const stats = this.state.dashboard_stats || {};
        const currencySymbol = stats.currency_symbol || "$";

        // Update Total Opportunities (stats ID)
        const totalOppEl = document.getElementById("total_opportunities_stats");
        if (totalOppEl) totalOppEl.innerText = stats.total_opportunities || 0;

        // Update Won Opportunities (stats ID)
        const wonOppEl = document.getElementById("won_opportunities_stats");
        if (wonOppEl) wonOppEl.innerText = stats.won_opportunities || 0;

        // Update Pipeline Value (stats ID)
        const pipelineEl = document.getElementById("pipeline_value_stats");
        if (pipelineEl)
            pipelineEl.innerText = this.formatCurrency(
                stats.pipeline_value || 0,
                currencySymbol
            );

        // Update Total Sales (stats ID)
        const totalSalesEl = document.getElementById("total_sales_stats");
        if (totalSalesEl)
            totalSalesEl.innerText = this.formatCurrency(
                stats.total_sales || 0,
                currencySymbol
            );

        // Update Average Deal Size (stats ID)
        const avgSizeEl = document.getElementById("average_deal_size_stats");
        if (avgSizeEl)
            avgSizeEl.innerText = this.formatCurrency(
                stats.average_deal_size || 0,
                currencySymbol
            );

        // Update Open Quotations (stats ID)
        const openQuotesEl = document.getElementById("open_quotations_stats");
        if (openQuotesEl)
            openQuotesEl.innerText = this.formatCurrency(
                stats.open_quotations || 0,
                currencySymbol
            );
    }

    async OnChangePeriods() {
        this.state.salesperson_id = parseInt(this.state.salesperson_id) || 0;
        await this.fetchAllData();
        this.renderAllCharts();
        this.updateDashboardStats();
    }

    async OnChangePeriodFromDropdown(ev) {
        ev.preventDefault();
        const selectedPeriod = ev.currentTarget.dataset.value;
        this.state.period = selectedPeriod;
        await this.fetchAllData();
        this.renderAllCharts();
        this.updateDashboardStats();
    }

    getPeriodLabel2(period) {
        const periodLabels = {
            today: "Today",
            yesterday: "Yesterday",
            week: "This Week",
            last_week: "Last Week",
            month: "This Month",
            last_month: "Last Month",
            quarter: "This Quarter",
            last_quarter: "Last Quarter",
            year: "This Year",
            last_year: "Last Year",
        };
        return periodLabels[period] || "This Month";
    }

    async OnChangeSalesPerson() {
        this.state.salesperson_id = parseInt(this.state.salesperson_id) || 0;
        await this.fetchAllData();
        this.renderAllCharts();
        this.updateDashboardStats();
    }

    getSelectedSalespersonName() {
        const selected = this.state.salesPersons.find(
            (sp) => sp.id === this.state.salesperson_id
        );
        return selected ? selected.name : "Select Salesperson";
    }

    async OnSalespersonSelect(ev) {
        ev.preventDefault();
        const selectedId = parseInt(ev.currentTarget.dataset.id);
        this.state.salesperson_id = selectedId;
        await this.fetchAllData();
        this.renderAllCharts();
        this.updateDashboardStats();
    }

    loadHiddenTags() {
        rpc("/crm_kpi_dashboard/get_hidden_tags", {}).then(
            function (result) {
                this.state.hiddenTags = result.hidden_tags || [];
            }.bind(this)
        );
    }

    loadHiddenSources() {
        rpc("/crm_kpi_dashboard/get_hidden_sources", {}).then(
            function (result) {
                this.state.hiddenSources = result.hidden_sources || [];
            }.bind(this)
        );
    }

    async loadCountryChartFilter() {
        rpc("/crm_kpi_dashboard/get_country_chart_filter", {}).then(
            function (result) {
                this.state.country_chart_filter = result.filter_type;
            }.bind(this)
        );
    }

    saveCountryChartFilter(filterType) {
        rpc("/crm_kpi_dashboard/save_country_chart_filter", {
            filter_type: filterType,
        }).then(function () {}.bind(this));
    }

    async fetchCountryWiseRevenue() {
        try {
            const result = await this.orm.call(
                "crm.lead",
                "get_country_wise_revenue",
                [
                    this.state.period,
                    this.state.salesperson_id,
                    this.state.country_chart_filter,
                ] // Add location_filter parameter
            );
            this.state.country_revenue = result.data || [];
            this.state.country_kpis = result.kpis || {};
        } catch (error) {
            console.error("Error fetching country-wise revenue:", error);
            this.state.country_revenue = [];
            this.state.country_kpis = {};
        }
    }

    async fetchTopCustomersData() {
        try {
            const result = await this.orm.call("crm.lead", "get_top_customers_data", [
                this.state.period,
                this.state.salesperson_id,
                7, // Top 10 customers
            ]);
            this.state.top_customers_data = result.data || [];
            this.state.top_customers_kpis = result.kpis || {};
        } catch (error) {
            console.error("Error fetching top customers data:", error);
            this.state.top_customers_data = [];
            this.state.top_customers_kpis = {};
        }
    }

    async fetchOpportunitiesByTagData() {
        try {
            const result = await this.orm.call(
                "crm.lead",
                "get_opportunities_by_tag_data",
                [
                    this.state.period,
                    this.state.salesperson_id,
                    10, // Top 10 by default
                ]
            );
            // Ensure all_tags is always an array
            this.state.opportunities_by_tag_data = {
                result: result.result || [],
                all_tags: result.all_tags || [],
                total_expected_revenue_by_tags:
                    result.total_expected_revenue_by_tags || 0,
                total_won_revenue_by_tags: result.total_won_revenue_by_tags || 0,
                hidden_tags: result.hidden_tags || [],
                currency_symbol: result.currency_symbol || "$",
            };
        } catch (error) {
            console.error("Error fetching opportunities by tag:", error);
            this.state.opportunities_by_tag_data = {
                result: [],
                all_tags: [],
                total_expected_revenue_by_tags: 0,
                total_won_revenue_by_tags: 0,
                hidden_tags: [],
            };
        }
    }

    async fetchTopSalespersonsData() {
        const result = await this.orm.call("crm.lead", "get_top_salespersons_data", [
            this.state.period,
            10, // Top 10 by default
            this.state.salesperson_id,
        ]);
        this.state.top_salespersons_data = result || [];
    }

    async fetchQuotationVsOrderData() {
        const result = await this.orm.call(
            "sale.order",
            "get_quotation_vs_order_data",
            [this.state.period, this.state.salesperson_id]
        );
        this.state.quotation_vs_order_data = result || [];
    }

    async fetchSalesPersons() {
        const result = await this.orm.call("res.users", "search_read", [
            [
                ["share", "=", false],
                ["sale_team_id", "!=", false],
            ],
            ["id", "name", "sale_team_id"],
        ]);

        this.state.salesPersons = [{id: 0, name: "Sales Person"}].concat(result);
    }

    async fetchPerformanceOverview() {
        const result = await this.orm.call("crm.lead", "get_salespersons_performance", [
            this.state.period,
            this.state.salesperson_id,
        ]);
        this.state.performance_overview = result || [];
    }

    async fetchLostReasonData() {
        const result = await this.orm.call("crm.lead", "get_lost_reason_data", [
            this.state.period,
            this.state.salesperson_id,
        ]);
        this.state.lost_reason_data = result || [];
    }

    async fetchFunneOpportunityPipeline() {
        const salespersonId = this.state.salesperson_id
            ? parseInt(this.state.salesperson_id)
            : 0;
        const result = await this.orm.call("crm.lead", "get_funnel_stage_data", [
            salespersonId,
        ]);
        this.state.funnel_data = result || [];
    }

    async fetchOpportunitiesBySourceData() {
        const result = await this.orm.call(
            "crm.lead",
            "get_opportunities_by_source_data",
            [this.state.period, this.state.salesperson_id, 10]
        );
        this.state.opportunities_by_source_data = result || {};
        this.state.hiddenSourceIds = result.hidden_source_ids || []; // FIX: Store IDs
        console.log("Hidden source IDs:", this.state.hiddenSourceIds);
    }
    // Helper method to get period label for x-axis
    getPeriodLabel() {
        const {period} = this.state;
        switch (period) {
            case "today":
                return "Time (Today)";
            case "yesterday":
                return "Time (Yesterday)";
            case "week":
                return "Days of Week";
            case "last_week":
                return "Days of Last Week";
            case "month":
                return "Weeks of Month";
            case "last_month":
                return "Weeks of Last Month";
            case "quarter":
                return "Months of Quarter";
            case "last_quarter":
                return "Months of Last Quarter";
            case "year":
                return "Months of Year";
            case "last_year":
                return "Months of Last Year";
            default:
                return "Days";
        }
    }

    renderAllCharts() {
        this.renderQuotationVsOrderChart();
        this.renderPerformanceOverviewChart();
        this.renderFunnelOpportunityPipeline();
        // this.renderTopSalespersonsChart();
        this.renderOpportunitiesBySourceChart();
        this.renderOpportunitiesByTagChart();
        this.renderTopCustomersChart();
        this.renderCountryWiseRevenueChart();
        this.renderLostReasonChart();
    }

    renderQuotationVsOrderChart() {
        let response = this.state.quotation_vs_order_data || {};
        let data = response.data || [];
        const currencySymbol = response.currency_symbol || "$";
        const formatCurrency = this.formatCurrency.bind(this);

        if (!data.length) {
            const today = new Date().toISOString().split("T")[0];
            data = [
                {
                    date: today,
                    quotation_total: 0,
                    quotation_count: 0,
                    order_total: 0,
                    order_count: 0,
                },
            ];
        }

        const categories = data.map((d) => d.label);
        const quotationTotals = data.map((d) => d.quotation_total);
        const orderTotals = data.map((d) => d.order_total);

        // Update the totals in the divs with formatted currency
        document.getElementById("total_quotations").innerText = this.formatCurrency(
            response.total_quotations || 0,
            currencySymbol
        );
        document.getElementById("total_orders").innerText = this.formatCurrency(
            response.total_orders || 0,
            currencySymbol
        );
        document.getElementById("total_conversion").innerText =
            response.conversion_percent ? response.conversion_percent + " %" : "0 %";

        Highcharts.chart("quotation_order_chart", {
            chart: {type: "column", backgroundColor: "transparent"},
            title: {text: ""},
            xAxis: {
                categories,
                crosshair: false,
                title: {text: this.getPeriodLabel()},
            },
            yAxis: {
                min: 0,
                title: {text: ""},
                gridLineDashStyle: "dash",
                labels: {
                    formatter: function () {
                        return formatCurrency(this.value, currencySymbol, true, false);
                    },
                },
            },
            tooltip: {
                headerFormat:
                    '<span class="tooltip-header">{point.key}</span><table style="margin-top:12px">',
                pointFormatter: function () {
                    // Show color square or pattern preview before value
                    let colorSquare = "";
                    if (this.color && this.color.pattern) {
                        // Show a small SVG pattern preview (12x12 square)
                        const pattern = this.color.pattern;
                        colorSquare =
                            '<svg width="12" height="12" style="vertical-align:middle;"><rect width="12" height="12" fill="' +
                            (pattern.backgroundColor || "#fff") +
                            '"/><path d="' +
                            (pattern.path?.d || pattern.path || "") +
                            '" stroke="' +
                            (pattern.color || "#CBD8E2") +
                            '" stroke-width="1"/></svg>';
                    } else {
                        // Use SVG for solid color as well, to match pattern size
                        colorSquare =
                            '<svg width="12" height="12" style="vertical-align:middle;"><rect width="12" height="12" fill="' +
                            (this.color || "#DBE5EC") +
                            '"/></svg>';
                    }
                    return (
                        '<tr class="tooltip-row"><td style="padding-right:10px;padding-bottom:5px">' +
                        colorSquare +
                        " " +
                        this.series.name +
                        '</td><td style="padding-bottom:5px"><b> ' +
                        currencySymbol +
                        " " +
                        Highcharts.numberFormat(this.y, 2) +
                        "</b></td></tr>"
                    );
                },
                footerFormat: "</table>",
                shared: true,
                useHTML: true,
            },
            plotOptions: {
                column: {
                    pointPadding: 0.03,
                    borderWidth: 0,
                    grouping: true,
                    groupPadding: 0.2,
                    dataLabels: {enabled: false},
                },
                series: {
                    states: {
                        inactive: {opacity: 1}, // Prevent dimming of non-hovered series
                    },
                },
            },
            series: [
                {
                    name: "Quotations",
                    data: quotationTotals.map((value) => value),
                    color: "#DBE5EC", // Solid color
                    states: {
                        hover: {
                            color: "#D8C1FB", // Hover color
                            brightness: 0,
                        },
                    },
                },
                {
                    name: "Orders",
                    data: orderTotals.map((value) => value),
                    color: {
                        pattern: {
                            path: "M 5 0 L 0 5 M -0.5 0.5 L 0.5 -0.5 M 4.5 5.5 L 5.5 4.5",
                            width: 5,
                            height: 5,
                            opacity: 0.7,
                            color: "#CBD8E2",
                        },
                    },
                    states: {
                        hover: {
                            color: {
                                pattern: {
                                    path: {
                                        d: "M 5 0 L 0 5 M -0.5 0.5 L 0.5 -0.5 M 4.5 5.5 L 5.5 4.5",
                                        stroke: "#D8C1FB",
                                        strokeWidth: 1,
                                    },
                                    backgroundColor: "#F1E9FE",
                                    width: 5,
                                    height: 5,
                                    opacity: 1,
                                },
                            },
                            brightness: 0,
                        },
                    },
                },
            ],
            legend: {
                enabled: true,
                align: "center",
                verticalAlign: "bottom",
                layout: "horizontal",
                itemStyle: {
                    fontStyle: "italic", // ← makes legend text italic
                    color: "#6E6E6E",
                    fontSize: "12px",
                    fontWeight: "400",
                },
                symbolHeight: 12,
                symbolWidth: 12,
                symbolRadius: 4, // ← makes legend shape square instead of round
            },
        });
    }

    renderFunnelOpportunityPipeline() {
        const funnelDataObj = this.state.funnel_data || {};
        const funnelData = funnelDataObj.data || []; // <-- ensure this is an array

        // Handle no data case AFTER updating KPIs
        if (!funnelData.length) {
            Highcharts.chart("opportunity_pipeline", {
                chart: {
                    type: "funnel",
                    backgroundColor: "transparent",
                    height: 400,
                },
                title: {
                    text: "Opportunity Pipeline",
                    style: {fontSize: "16px", fontWeight: "bold"},
                },
                subtitle: {
                    text: "No opportunities found for selected filters",
                    style: {fontSize: "12px", color: "#666"},
                },
                series: [
                    {
                        name: "Expected Revenue",
                        data: [],
                    },
                ],
                credits: {enabled: false},
            });
            return;
        }

        Highcharts.chart("opportunity_pipeline", {
            chart: {type: "funnel", backgroundColor: "transparent"},
            title: {text: ""},
            plotOptions: {
                series: {
                    borderColor: "#fff",
                    borderWidth: 2,
                    pointPadding: 5,
                    states: {
                        hover: {
                            brightness: 0, // prevents default brightening
                            color: {
                                pattern: {
                                    path: {
                                        d: "M 0 0 L 14 14 M 13 -1 L 15 1 M -1 13 L 1 15",
                                        stroke: "#E6D7FD",
                                        strokeWidth: 3,
                                    },
                                    backgroundColor: "#D8C1FB", // hover background
                                    width: 14,
                                    height: 14,
                                    opacity: 1,
                                },
                            },
                        },
                    },
                    dataLabels:
                        {
                            enabled: true,
                            useHTML: true,
                            align: "right",
                            inside: false,
                            connectorPadding: 0,
                            formatter: function () {
                                const stageName = this.point.name;
                                const stagewiseCount = Highcharts.numberFormat(
                                    this.point.options.stagewiseCount,
                                    0
                                );
                                const expectedRevenue = Highcharts.numberFormat(
                                    this.point.expectedRevenue,
                                    0
                                );
                                const currencySymbol =
                                    funnelDataObj.currency_symbol || "$";
                                return `
                        <div class="dashboard-graph-text" style="display:flex; justify-content:space-between; width:100%;">
                            <p style="text-align:right">
                                <span style="flex:1;font-size:14px;font-weight:600;">${stageName} (${stagewiseCount}) </span><br/>
                                <span style="font-weight:400">${currencySymbol} ${expectedRevenue}</span>
                            </p>
                        </div>`;
                            },
                            softConnector: true,
                        },
                    center: ["40%", "50%"],
                    neckWidth: "30%",
                    neckHeight: "10%",
                    width: "75%",
                },
            },
            legend: {enabled: false},
            tooltip: {enabled: false},
            series: [
                {
                    name: "Expected Revenue",
                    data: funnelData.map((d) => ({
                        name: d[0],
                        y: d[3],
                        expectedRevenue: d[1],
                        stagewiseCount: d[2],
                        percentage: d[3],
                        color: {
                            pattern: {
                                path: {
                                    d: "M 0 0 L 14 14 M 13 -1 L 15 1 M -1 13 L 1 15",
                                    stroke: "#E6D7FD",
                                    strokeWidth: 3,
                                },
                                backgroundColor: "#F1E9FE", // default background
                                width: 14,
                                height: 14,
                                opacity: 1,
                            },
                        },
                    })),
                },
            ],
        });
    }

    renderOpportunitiesBySourceChart() {
        const response = this.state.opportunities_by_source_data || {};
        const data = response.source_data || [];
        const totals = response.totals || {};
        const currencySymbol = totals.currency_symbol || "$";

        // Color palette (solid + pattern)
        const colorPalette = [{solid: "#D8C1FB", pattern: "#E6D7FD"}];

        // Build chart data with pattern fill
        const chartData = data.length
            ? data.map((item, index) => {
                  const colorIndex = index % colorPalette.length;
                  const colors = colorPalette[colorIndex];

                  return {
                      name: item.source_name,
                      y: item.percentage, // use percentage for pie slices
                      count: item.count,
                      revenue: item.revenue,
                      color: {
                          pattern: {
                              path: "M 0 0 L 10 10 M 9 -1 L 11 1 M -1 9 L 1 11",
                              width: 10,
                              height: 10,
                              color: colors.pattern,
                              backgroundColor: colors.solid,
                          },
                      },
                      solidColor: colors.solid,
                  };
              })
            : [
                  {
                      name: "No Data",
                      y: 100,
                      count: 0,
                      revenue: 0,
                      color: "#cccccc",
                      solidColor: "#cccccc",
                  },
              ];

        const dataCount = chartData.length;
        let labelFontSize = 16; // default
        if (dataCount > 15) {
            labelFontSize = 10;
        } else if (dataCount > 5) {
            labelFontSize = 12;
        }
        // Update summary totals above chart
        document.getElementById("total_expected_revenue_source").innerHTML =
            this.formatCurrency(totals.total_revenue || 0, currencySymbol);
        document.getElementById("top_source").innerHTML = totals.top_source || "N/A";

        Highcharts.chart("opportunities_by_source_chart", {
            chart: {type: "pie", backgroundColor: "transparent"},
            title: {text: ""},
            tooltip: {
                headerFormat: "<table>",
                pointFormatter: function () {
                    // Use 12x12 SVG for color square
                    return (
                        '<tr class="tooltip-row">' +
                        "<td><b>" +
                        this.point.name +
                        "</b></td></tr>" +
                        '<tr class="tooltip-row"><td style="padding-right:40px;padding-bottom:5px">Revenue</td><td><b>' +
                        currencySymbol +
                        " " +
                        Highcharts.numberFormat(this.point.revenue, 0) +
                        "</b></td></tr>" +
                        '<tr class="tooltip-row"><td>Opportunities</td><td><b>' +
                        this.point.count +
                        "</b></td></tr>" +
                        '<tr class="tooltip-row"><td>Share</td><td><b>' +
                        Highcharts.numberFormat(this.point.percentage, 1) +
                        "%</b></td></tr>"
                    );
                },
                footerFormat: "</table>",
                useHTML: true,
                shared: true,
            },
            plotOptions: {
                pie: {
                    allowPointSelect: true,
                    borderWidth: 2,
                    cursor: "pointer",
                    dataLabels: {
                        enabled: true,
                        format: "<b>{point.name}</b><br>{point.percentage:.1f}%",
                        distance: 20,
                        style: {
                            fontSize: `${labelFontSize}px`,
                            textOutline: "none",
                            color: "#000",
                        },
                    },
                    size: "80%",
                    showInLegend: true,
                    // Enable custom states for hover
                    states: {
                        hover: {
                            color: {
                                pattern: {
                                    path: {
                                        d: "M 0 0 L 14 14 M 13 -1 L 15 1 M -1 13 L 1 15",
                                        stroke: "#E6D7FD",
                                        strokeWidth: 3,
                                    },
                                    backgroundColor: "#D8C1FB", // hover background
                                    width: 14,
                                    height: 14,
                                    opacity: 1,
                                },
                            },
                        },
                    },
                },
            },
            series: [
                {
                    enableMouseTracking: false,
                    animation: {duration: 2000},
                    colorByPoint: true,
                    data: chartData.map((d) => ({
                        ...d,
                        color: {
                            pattern: {
                                path: {
                                    d: "M 0 0 L 14 14 M 13 -1 L 15 1 M -1 13 L 1 15",
                                    stroke: "#E6D7FD",
                                    strokeWidth: 3,
                                },
                                backgroundColor: "#F1E9FE", // default background
                                width: 14,
                                height: 14,
                                opacity: 1,
                            },
                        },
                        states: {
                            hover: {
                                color: {
                                    pattern: {
                                        path: {
                                            d: "M 0 0 L 14 14 M 13 -1 L 15 1 M -1 13 L 1 15",
                                            stroke: "#E6D7FD",
                                            strokeWidth: 3,
                                        },
                                        backgroundColor: "#D8C1FB",
                                        width: 14,
                                        height: 14,
                                        opacity: 1,
                                    },
                                },
                            },
                        },
                    })),
                    events: {
                        afterAnimate: function () {
                            this.update({enableMouseTracking: true}, false);
                        },
                    },
                },
            ],
            credits: {enabled: false},
            legend: {enabled: false},
        });
    }

    renderPerformanceOverviewChart() {
        const selectedSalespersonId = parseInt(this.state.salesperson_id);
        const performanceMap = {};

        this.state.performance_overview.performance_overview.forEach((d) => {
            if (d.id) {
                // Only include entries with an id (exclude summary rows)
                performanceMap[d.id] = d;
            }
        });

        let categories = [];
        let expectedRevenue = [];
        let wonRevenue = [];

        if (!selectedSalespersonId || selectedSalespersonId === 0) {
            // Show all salespersons
            const salespersons = this.state.salesPersons.filter(
                (sp) =>
                    sp.id !== 0 &&
                    (performanceMap[sp.id]?.expected_revenue || 0) > 0 &&
                    (performanceMap[sp.id]?.won_revenue || 0) > 0
            );
            categories = salespersons.map((sp) => sp.name.split(" ")[0]);
            expectedRevenue = salespersons.map(
                (sp) => performanceMap[sp.id]?.expected_revenue || 0
            );
            wonRevenue = salespersons.map(
                (sp) => performanceMap[sp.id]?.won_revenue || 0
            );
        } else {
            // Show only selected salesperson
            const selectedSp = this.state.salesPersons.find(
                (sp) => sp.id === selectedSalespersonId
            );
            const data = performanceMap[selectedSalespersonId] || {};
            categories = [selectedSp?.name ? selectedSp.name.split(" ")[0] : "Unknown"];
            expectedRevenue = [data.expected_revenue || 0];
            wonRevenue = [data.won_revenue || 0];
        }

        const currency =
            this.state.performance_overview.performance_overview.find((d) => d.currency)
                ?.currency || "$";

        let response = this.state.performance_overview || {};
        const currencySymbol = response.currency_symbol || "$";

        // Update the totals in the divs with formatted values
        document.getElementById("avg_opportunity_count").innerText =
            Highcharts.numberFormat(response.avg_opp_count, 0);
        document.getElementById("avg_revenue_per_salesperson").innerText =
            this.formatCurrency(
                response.avg_won_revenue_per_salesperson,
                currencySymbol
            );
        console.log(
            "Rendering Performance Overview Chart with categories:",
            categories
        );
        let dynamic_interval = response.dynamic_interval;
        const chartConfig = {
            chart: {
                type: "column",
                backgroundColor: "transparent",
            },
            title: {
                text: "",
            },
            xAxis: {
                categories: categories,
                labels: {rotation: 0, style: {fontSize: "11px"}},
                min: 0,
                max: Math.min(categories.length - 1, 4),
                scrollbar: {
                    enabled: true,
                },
                tickLength: 0,
            },
            yAxis: {
                title: {text: ""},
                min: 0,
                gridLineDashStyle: "dash",
                tickInterval: dynamic_interval,
            },
            tooltip: {
                headerFormat:
                    '<span class="tooltip-header">{point.key}</span><table style="margin-top:12px">',
                pointFormatter: function () {
                    // Show pattern preview if pattern exists, else show color square
                    let colorSquare = "";
                    if (this.color && this.color.pattern) {
                        // Show a small SVG pattern preview
                        const pattern = this.color.pattern;
                        colorSquare =
                            '<svg width="12" height="12" style="vertical-align:middle;"><rect width="12" height="12" fill="' +
                            (pattern.backgroundColor || "#fff") +
                            '"/><path d="' +
                            (pattern.path?.d || pattern.path || "") +
                            '" stroke="' +
                            (pattern.color || "#CBD8E2") +
                            '" stroke-width="1"/></svg>';
                    } else {
                        colorSquare =
                            '<svg width="12" height="12" style="vertical-align:middle;"><rect width="12" height="12" fill="' +
                            (this.color || "#CBD8E2") +
                            '">\u25A0</svg>';
                    }
                    return (
                        '<tr class="tooltip-row"><td style="padding-right:10px;padding-bottom:5px">' +
                        colorSquare +
                        " " +
                        this.series.name +
                        " </td>" +
                        '<td style="padding-bottom:5px"><b>' +
                        currency +
                        " " +
                        Highcharts.numberFormat(this.y, 0) +
                        "</b></td></tr>"
                    );
                },
                footerFormat: "</table>",
                shared: true,
                useHTML: true,
            },
            plotOptions: {
                column: {
                    pointPadding: 0.03,
                    borderWidth: 0,
                    dataLabels: {
                        enabled: false, // Disabled data labels - amounts will only show on hover
                    },
                    grouping: true,
                    groupPadding: 0.2,
                },
                series: {
                    states: {
                        inactive: {
                            opacity: 1, // Prevent dimming of non-hovered series
                        },
                    },
                },
            },
            series: [
                {
                    name: "Expected Revenue",
                    data: expectedRevenue,
                    color: "#DBE5EC", // Solid color for expected revenue
                    states: {
                        hover: {
                            color: "#D8C1FB", // Custom hover color for Expected Revenue
                            brightness: 0,
                        },
                    },
                },
                {
                    name: "Won Revenue",
                    data: wonRevenue,
                    color: {
                        pattern: {
                            path: "M 5 0 L 0 5 M -0.5 0.5 L 0.5 -0.5 M 4.5 5.5 L 5.5 4.5",
                            width: 5,
                            height: 5,
                            opacity: 0.7,
                            color: "#CBD8E2", // Green color for sales orders
                        },
                    },
                    states: {
                        hover: {
                            color: {
                                pattern: {
                                    path: {
                                        d: "M 5 0 L 0 5 M -0.5 0.5 L 0.5 -0.5 M 4.5 5.5 L 5.5 4.5",
                                        stroke: "#D8C1FB",
                                        strokeWidth: 1,
                                    },
                                    backgroundColor: "#F1E9FE",
                                    width: 5,
                                    height: 5,
                                    opacity: 1,
                                },
                            },
                            brightness: 0,
                        },
                    },
                },
            ],
            legend: {
                enabled: true,
                align: "center",
                verticalAlign: "bottom",
                layout: "horizontal",
                itemStyle: {
                    fontStyle: "italic", // ← makes legend text italic
                    color: "#6E6E6E",
                    fontSize: "12px",
                    fontWeight: "400",
                },
                symbolHeight: 12,
                symbolWidth: 12,
                symbolRadius: 4, // ← makes legend shape square instead of round
            },
        };
        Highcharts.chart(
            "salesperson_performance_overview",
            addMouseWheelScroll(chartConfig, {scrollSpeed: 0.2})
        );
    }

    renderOpportunitiesByTagChart() {
        const data = this.state.opportunities_by_tag_data.result || [];
        const currencySymbol =
            this.state.opportunities_by_tag_data.currency_symbol || "$";
        const formatCurrency = this.formatCurrency.bind(this);

        const categories = data.map((item) => {
            const name = item.tag_name || "";
            return name.length > 10 ? name.substring(0, 10) + "..." : name;
        });
        const expectedRevenueData = data.map(
            (item) => item.expected_revenue ?? item.revenue ?? 0
        );
        const wonRevenueData = data.map((item) => item.won_revenue ?? 0);

        document.getElementById("expected_revenue_by_tags").innerText =
            this.formatCurrency(
                this.state.opportunities_by_tag_data.total_expected_revenue_by_tags ||
                    0,
                currencySymbol
            );
        document.getElementById("won_revenue_by_tags").innerText = this.formatCurrency(
            this.state.opportunities_by_tag_data.total_won_revenue_by_tags || 0,
            currencySymbol
        );
        let dynamic_interval = this.state.opportunities_by_tag_data.dynamic_interval;

        const chartConfig = {
            chart: {type: "column", backgroundColor: "transparent"},
            title: {text: ""},
            subtitle: {text: ""},
            xAxis: {
                categories,
                crosshair: false,
                title: {text: ""},
                labels: {rotation: 0, style: {fontSize: "11px"}},
                min: 0,
                max: 4,
                scrollbar: {
                    enabled: true,
                },
                tickLength: 0,
            },
            yAxis: {
                min: 0,
                title: {text: ""},
                labels: {
                    formatter: function () {
                        return formatCurrency(this.value, currencySymbol, true, false);
                    },
                },
                gridLineDashStyle: "dash",
                tickInterval: dynamic_interval,
            },
            tooltip: {
                // headerFormat:
                //     '<span class="tooltip-header":style="padding-bottom:20px"><b>{point.key}</b></span><table>',
                headerFormat:
                    '<span class="tooltip-header">{point.key}</span><table style="margin-top:12px">',
                pointFormatter: function () {
                    // Show color square before value, like in salesperson performance overview
                    let colorSquare = "";
                    if (this.color && this.color.pattern) {
                        // Show a small SVG pattern preview
                        const pattern = this.color.pattern;
                        colorSquare =
                            '<svg width="12" height="12" style="vertical-align:middle;"><rect width="12" height="12" fill="' +
                            (pattern.backgroundColor || "#fff") +
                            '"/><path d="' +
                            (pattern.path?.d || pattern.path || "") +
                            '" stroke="' +
                            (pattern.color || "#CBD8E2") +
                            '" stroke-width="1"/></svg>';
                    } else {
                        colorSquare =
                            '<svg width="12" height="12" style="vertical-align:middle;"><rect width="12" height="12" fill="' +
                            (this.color || "#CBD8E2") +
                            '">\u25A0</svg>';
                    }
                    // Add currency symbol and Highcharts number format for revenues
                    const currency = currencySymbol || "$";
                    return (
                        '<tr class="tooltip-row"><td style="padding-right:10px;padding-bottom:5px">' +
                        colorSquare +
                        " " +
                        this.series.name +
                        " </td>" +
                        '<td style="padding-right:10px;padding-bottom:5px"><b>' +
                        currency +
                        " " +
                        Highcharts.numberFormat(this.y, 0) +
                        "</b></td></tr>" +
                        '<tr class="tooltip-row" ><td style="padding-right:10px;padding-bottom:5px;padding-left:16px;">Opportunities</td>' +
                        '<td style="padding-right:10px;padding-bottom:5px"><b>' +
                        (this.count !== undefined
                            ? this.count
                            : (this.point?.count ?? "")) +
                        "</b></td></tr>"
                    );
                },
                footerFormat: "</table>",
                shared: true,
                useHTML: true,
                padding: 12,
                borderRadius: 4,
                overflow: "hidden",
            },
            plotOptions: {
                column: {
                    pointPadding: 0.03,
                    borderWidth: 0,
                    borderRadius: 3,
                    grouping: true,
                    states: {hover: {brightness: 0}}, // Disable group hover background
                },
                series: {
                    states: {inactive: {opacity: 1}}, // Prevent dimming
                },
            },
            series: [
                {
                    name: "Expected Revenue",
                    color: "#DBE5EC", // Add this for legend
                    data: data.map((item, index) => ({
                        name: item.tag_name,
                        y: expectedRevenueData[index],
                        count: item.count,
                        color: "#DBE5EC",
                        states: {
                            hover: {
                                color: "#D8C1FB",
                                brightness: 0,
                            },
                        },
                    })),
                },
                {
                    name: "Won Revenue",
                    color: {
                        pattern: {
                            path: "M 5 0 L 0 5 M -0.5 0.5 L 0.5 -0.5 M 4.5 5.5 L 5.5 4.5",
                            width: 5,
                            height: 5,
                            opacity: 0.7,
                            color: "#CBD8E2", // Green color for sales orders
                        },
                    },
                    data: data.map((item, index) => ({
                        name: item.tag_name,
                        y: wonRevenueData[index],
                        count: item.count,
                        color: {
                            pattern: {
                                path: "M 5 0 L 0 5 M -0.5 0.5 L 0.5 -0.5 M 4.5 5.5 L 5.5 4.5",
                                width: 5,
                                height: 5,
                                opacity: 0.7,
                                color: "#CBD8E2",
                            },
                        },
                    })),
                    states: {
                        hover: {
                            color: {
                                pattern: {
                                    path: {
                                        d: "M 5 0 L 0 5 M -0.5 0.5 L 0.5 -0.5 M 4.5 5.5 L 5.5 4.5",
                                        stroke: "#D8C1FB",
                                        strokeWidth: 1,
                                    },
                                    backgroundColor: "#F1E9FE",
                                    width: 5,
                                    height: 5,
                                    opacity: 1,
                                },
                            },
                            brightness: 0,
                        },
                    },
                },
            ],
            credits: {enabled: false},
            legend: {
                enabled: true,
                align: "center",
                verticalAlign: "bottom",
                layout: "horizontal",
                itemStyle: {
                    fontStyle: "italic", // ← makes legend text italic
                    color: "#6E6E6E",
                    fontSize: "12px",
                    fontWeight: "400",
                },
                symbolHeight: 12,
                symbolWidth: 12,
                symbolRadius: 4, // ← makes legend shape square instead of round
            },
        };
        Highcharts.chart(
            "opportunities_by_tag_chart",
            addMouseWheelScroll(chartConfig, {scrollSpeed: 0.1})
        );
    }

    renderCountryWiseRevenueChart() {
        const data = this.state.country_revenue || [];
        const kpis = this.state.country_kpis || {};
        const filterType = this.state.country_chart_filter;
        const formatCurrency = this.formatCurrency.bind(this);
        const currencySymbol = kpis.currency_symbol || "$";

        // Update KPI boxes
        document.getElementById("geographies_with_won_deals").innerText =
            kpis.geographies_with_won_deals || 0;

        document.getElementById("percentage_share_top_geographies").innerText =
            kpis.top_3_percentage_share ? kpis.top_3_percentage_share + "%" : "0%";

        // Use item.location instead of item.country/state/city
        const categories = data.map((item) => {
            const name = item.location || "Unknown";
            return name.length > 10 ? name.substring(0, 10) + "..." : name;
        });
        const chartData = data.map((item) => ({
            y: item.revenue,
            custom: {
                count: item.won_deals,
            },
            name: item.location || "Unknown",
        }));

        // Dynamic axis titles based on filter
        const xAxisTitle = filterType.charAt(0).toUpperCase() + filterType.slice(1);
        const chartTitle = `${xAxisTitle} Wise Revenue`;

        let dynamic_interval = kpis.dynamic_interval;

        const chartConfig = {
            chart: {
                type: "bar",
                backgroundColor: "transparent",
                marginLeft: 80, // Reserve fixed space for y-axis labels
                spacingLeft: 10,
                marginBottom: 50,
            },
            title: {
                text: chartTitle,
                align: "left",
                style: {fontSize: "16px", fontWeight: "bold"},
            },
            xAxis: {
                categories: categories,
                title: {
                    text: "",
                },
                labels: {
                    rotation: 0,
                    style: {fontSize: "11px"},
                },
                gridLineWidth: 1,
                gridLineDashStyle: "dash",
                lineWidth: 0,
                min: 0,
                max: 4,
                scrollbar: {
                    enabled: true,
                    showFull: false, // Add this
                },
            },
            yAxis: {
                min: 0,
                title: {
                    text: "",
                },
                labels: {
                    formatter: function () {
                        return formatCurrency(this.value, currencySymbol, true, false);
                    },
                },
                gridLineWidth: 0,
                lineWidth: 1,
                tickInterval: dynamic_interval,
            },
            legend: {enabled: false},
            tooltip: {
                headerFormat:
                    '<span class="tooltip-header">{point.key}</span><table style="margin-top:12px">',
                pointFormatter: function () {
                    // Show color square before value, add currency symbol, and use Highcharts number format
                    let colorSquare = "";
                    if (this.color && typeof this.color === "string") {
                        colorSquare =
                            '<span style="color:' + this.color + '">\u25A0</span>';
                    } else {
                        colorSquare = '<span style="color:#DBE5EC">\u25A0</span>';
                    }
                    return (
                        '<tr class="tooltip-row"><td style="padding-right:40px;padding-bottom:5px">' +
                        colorSquare +
                        " Revenue </td>" +
                        "<td><b>" +
                        currencySymbol +
                        " " +
                        Highcharts.numberFormat(this.y, 0) +
                        "</b></td></tr>" +
                        '<tr class="tooltip-row"><td style="padding-bottom:5px">' +
                        colorSquare +
                        " Opportunities  </td>" +
                        '<td style="padding-bottom:5px"><b>' +
                        (this.custom && this.custom.count !== undefined
                            ? this.custom.count
                            : (this.point?.custom?.count ?? "")) +
                        "</b></td></tr>"
                    );
                },
                footerFormat: "</table>",
                shared: true,
                useHTML: true,
            },
            plotOptions: {
                series: {
                    borderRadius: 3,
                    dataLabels: {
                        enabled: true,
                        formatter: function () {
                            return this.point.custom.count;
                        },
                        style: {
                            fontSize: "11px",
                            fontWeight: "bold",
                        },
                    },
                },
            },
            series: [
                {
                    name: "",
                    data: chartData,
                    color: "#DBE5EC",
                    states: {
                        hover: {
                            color: "#D8C1FB",
                            brightness: 0,
                        },
                    },
                },
            ],
            credits: {enabled: false},
        };
        Highcharts.chart(
            "country_wise_revenue_chart",
            addMouseWheelScroll(chartConfig, {scrollSpeed: 0.1})
        );
    }

    renderTopCustomersChart() {
        const data = this.state.top_customers_data || [];
        const kpis = this.state.top_customers_kpis || {};
        const formatCurrency = this.formatCurrency.bind(this);

        const currencySymbol = kpis.currency_symbol || "$";

        // Update KPI elements
        if (document.getElementById("total_won_revenue_top_customers")) {
            document.getElementById("total_won_revenue_top_customers").innerText =
                this.formatCurrency(kpis.top_customers_revenue || 0, currencySymbol);
        }

        if (document.getElementById("average_deal_size_top_customers")) {
            document.getElementById("average_deal_size_top_customers").innerText =
                this.formatCurrency(
                    kpis.top_customers_avg_order_value || 0,
                    currencySymbol
                );
        }

        if (document.getElementById("percentage_share_top_customers")) {
            document.getElementById("percentage_share_top_customers").innerText =
                kpis.percentage_share ? kpis.percentage_share + " %" : "0 %";
        }

        if (document.getElementById("top_customers_opportunity_count")) {
            document.getElementById("top_customers_opportunity_count").innerText =
                kpis.top_customers_order_count || 0;
        }

        const containerId = "top_seven_customers";

        // Create enhanced data array with both revenue and opportunity count
        const chartData = data.map((item) => ({
            y: item.revenue,
            custom: {
                count: item.order_count,
                avgDealSize: item.average_order_value,
            },
            name: item.customer_name,
        }));

        const categories = data.map((item) => {
            const name = item.customer_name || "";
            return name.length > 10 ? name.substring(0, 10) + "..." : name;
        });
        let dynamic_interval = kpis.dynamic_interval;

        const chartConfig = {
            chart: {
                type: "bar",
                backgroundColor: "transparent",
                marginLeft: 80, // Reserve fixed space for y-axis labels
                spacingLeft: 10,
                marginBottom: 50,
            },
            title: {
                text: "",
                align: "left",
                style: {fontSize: "16px", fontWeight: "bold"},
            },
            xAxis: {
                categories: categories,
                title: {
                    text: "",
                    style: {fontWeight: "bold"},
                },
                labels: {
                    rotation: 0,
                    style: {
                        fontSize: "11px",
                    },
                },
                gridLineWidth: 1,
                lineWidth: 0,
                gridLineDashStyle: "dash",
                min: 0,
                max: 4,
                scrollbar: {
                    enabled: true,
                    showFull: false, // Add this
                },
                tickLength: 0,
            },
            yAxis: {
                min: 0,
                title: {
                    text: "",
                    style: {fontWeight: "bold"},
                },
                labels: {
                    formatter: function () {
                        return formatCurrency(this.value, currencySymbol, true, false);
                    },
                },
                gridLineWidth: 0,
                lineWidth: 1,
                tickInterval: dynamic_interval,
            },
            legend: {
                enabled: false,
            },
            tooltip: {
                // headerFormat:
                //     '<span class="tooltip-header"><b>{point.name}</b></span><table>',
                headerFormat:
                    '<span class="tooltip-header">{point.key}</span><table style="margin-top:12px">',
                pointFormatter: function () {
                    // Add color square before label, currency symbol, and Highcharts number format
                    let colorSquare = "";
                    if (this.color && typeof this.color === "string") {
                        colorSquare =
                            '<span style="color:' + this.color + '">\u25A0</span>';
                    } else {
                        colorSquare = '<span style="color:#DBE5EC">\u25A0</span>';
                    }
                    const currency = currencySymbol || "$";
                    return `
            <tr class="tooltip-row"><td style="padding-right:10px;padding-bottom:5px">${colorSquare} Revenue </td><td style="padding-bottom:5px"><b>${currency} ${Highcharts.numberFormat(this.y, 0)}</b></td></tr>
            <tr class="tooltip-row"><td style="padding-right:10px;padding-bottom:5px">${colorSquare} Opportunities </td><td style="padding-bottom:5px"><b>${Highcharts.numberFormat(this.custom.count, 0)}</b></td></tr>
            <tr class="tooltip-row"><td style="padding-right:10px;padding-bottom:5px">${colorSquare} Avg Deal Size </td><td style="padding-bottom:5px"><b>${currency} ${Highcharts.numberFormat(this.custom.avgDealSize, 0)}</b></td></tr>
        `;
                },
                footerFormat: "</table>",
                shared: true,
                useHTML: true,
            },
            plotOptions: {
                bar: {
                    dataLabels: {
                        enabled: true,
                        formatter: function () {
                            // Display revenue amount with opportunity count in parentheses
                            return this.point.custom.count;
                        },
                        style: {
                            fontSize: "11px",
                            fontWeight: "bold",
                        },
                    },
                    borderRadius: 3,
                },
            },
            series: [
                {
                    name: "",
                    data: chartData,
                    color: "#DBE5EC",
                    states: {
                        hover: {
                            color: "#D8C1FB",
                            brightness: 0,
                        },
                    },
                },
            ],
            credits: {
                enabled: false,
            },
        };
        Highcharts.chart(
            containerId,
            addMouseWheelScroll(chartConfig, {scrollSpeed: 0.1})
        );
    }

    renderLostReasonChart() {
        const lostData = this.state.lost_reason_data || {};
        const reasonsData = lostData.data || [];
        const kpis = lostData.kpis || {};
        const currencySymbol = kpis.currency_symbol || "$";
        const formatCurrency = this.formatCurrency.bind(this);

        // Update KPI boxes (unchanged)
        if (document.getElementById("total_lost_opportunities")) {
            document.getElementById("total_lost_opportunities").innerText =
                Highcharts.numberFormat(kpis.total_lost_opportunities || 0, 0);
        }
        if (document.getElementById("total_lost_revenue")) {
            document.getElementById("total_lost_revenue").innerText =
                this.formatCurrency(kpis.total_lost_revenue || 0, currencySymbol, true);
        }

        // Use count as y-value, revenue as custom property
        const chartData = reasonsData.map((item) => ({
            y: item.count, // Show count as main value
            custom: {
                revenue: item.revenue,
            },
            name: item.reason,
        }));

        // Sort data by count (descending) - most common reasons at top
        const sortedData = [...reasonsData].sort((a, b) => b.count - a.count);

        // Extract categories
        const categories = reasonsData.map((item) => {
            const name = item.reason || "";
            return name.length > 10 ? name.substring(0, 10) + "..." : name;
        });

        let dynamic_interval = 10; // default

        if (this.state.period) {
            const longRangePeriods = ["year", "last_year", "quarter", "last_quarter"];
            if (longRangePeriods.includes(this.state.period)) {
                dynamic_interval = 50; // 10M
            }
        }

        // Highcharts.chart("crm_lost_reason_chart", {
        const chartConfig = {
            chart: {
                type: "bar",
                backgroundColor: "transparent",
                marginLeft: 80, // Reserve fixed space for y-axis labels
                spacingLeft: 10,
                marginBottom: 50,
            },
            title: {
                text: "",
                align: "left",
                style: {fontSize: "16px", fontWeight: "bold"},
            },
            xAxis: {
                categories: categories,
                title: {
                    text: null,
                },
                lineWidth: 0,
                gridLineWidth: 1,
                lineWidth: 0,
                gridLineDashStyle: "dash",
                min: 0,
                max: 4,
                scrollbar: {
                    enabled: true,
                },
                tickLength: 0,
            },
            yAxis: {
                min: 0,
                max: Math.ceil(Math.max(...sortedData.map((d) => d.count)) / 10) * 10,
                tickInterval: dynamic_interval,
                allowDecimals: false,
                title: {
                    text: "",
                },
                labels: {
                    formatter: function () {
                        return Highcharts.numberFormat(this.value, 0);
                    },
                },
                gridLineWidth: 0,
                lineWidth: 1,
            },
            legend: {enabled: false},
            tooltip: {
                // headerFormat:
                //     '<span class="tooltip-header"><b>{point.key}</b></span><table>',
                headerFormat:
                    '<span class="tooltip-header">{point.key}</span><table style="margin-top:12px">',
                pointFormatter: function () {
                    // Add color square before label, currency symbol, and Highcharts number format
                    let colorSquare = "";
                    if (this.color && typeof this.color === "string") {
                        colorSquare =
                            '<span style="color:' + this.color + '">\u25A0</span>';
                    } else {
                        colorSquare = '<span style="color:#DBE5EC">\u25A0</span>';
                    }
                    return `
                        <tr class="tooltip-row">
                            <td style="padding-right:10px;padding-bottom:5px">${colorSquare} Opportunities </td>
                            <td style="padding-right:10px;padding-bottom:5px"><b>${Highcharts.numberFormat(this.y, 0)}</b></td>
                        </tr>
                        <tr class="tooltip-row">
                            <td style="padding-right:10px;padding-bottom:5px">${colorSquare} Revenue </td>
                            <td style="padding-right:10px;padding-bottom:5px"><b>${currencySymbol} ${Highcharts.numberFormat(this.custom.revenue, 0)}</b></td>
                        </tr>
                    `;
                },
                footerFormat: "</table>",
                shared: true,
                useHTML: true,
            },
            plotOptions: {
                series: {
                    dataLabels: {
                        enabled: true,
                        formatter: function () {
                            // Show count and revenue in parentheses: count (revenue $)
                            return formatCurrency(
                                this.point.custom.revenue,
                                currencySymbol,
                                true,
                                false
                            );
                        },
                    },
                    borderRadius: 3,
                },
            },
            series: [
                {
                    name: "Lost Opportunities",
                    data: chartData,
                    color: "#DBE5EC",
                    states: {
                        hover: {color: "#D8C1FB", brightness: 0},
                    },
                },
            ],
            credits: {enabled: false},
        };
        Highcharts.chart(
            "crm_lost_reason_chart",
            addMouseWheelScroll(chartConfig, {scrollSpeed: 0.1})
        );
    }

    onStageToggle = function (ev) {
        const stageName = ev.target.value;
        const isChecked = ev.target.checked;

        // Save to server
        this.saveHiddenStages(stageName, isChecked);
    };

    saveHiddenStages = function (stageName, isChecked) {
        rpc("/crm_kpi_dashboard/toggle_stage_visibility", {
            stage_name: stageName,
            is_visible: isChecked, // true = show, false = hide
        }).then(
            function () {
                // Refresh funnel data to update the graph and dropdown
                this.fetchFunneOpportunityPipeline().then(() => {
                    this.renderFunnelOpportunityPipeline();
                });
            }.bind(this)
        );
    };

    onCountryChartFilterChange(ev) {
        const filterType = ev.target.value;

        // Update state
        this.state.country_chart_filter = filterType;
        // Save to server
        this.saveCountryChartFilter(filterType);

        // Refresh country revenue data
        this.fetchCountryWiseRevenue().then(() => {
            this.renderCountryWiseRevenueChart();
        });
    }

    onTagToggle(ev) {
        const tagId = parseInt(ev.target.value);
        const isChecked = ev.target.checked;

        // Save to server using toggle logic
        this.toggleTagVisibility(tagId, isChecked);
    }

    toggleTagVisibility(tagId, isVisible) {
        rpc("/crm_kpi_dashboard/toggle_tag_visibility", {
            tag_id: tagId,
            is_visible: isVisible,
        })
            .then(
                function () {
                    // Refresh tag data
                    this.fetchOpportunitiesByTagData().then(() => {
                        this.renderOpportunitiesByTagChart();
                    });
                }.bind(this)
            )
            .catch(function (error) {
                console.error("Error toggling tag visibility:", error);
            });
    }

    toggleSourceVisibility(sourceId, isVisible) {
        rpc("/crm_kpi_dashboard/toggle_source_visibility", {
            source_id: sourceId,
            is_visible: isVisible,
        })
            .then(
                function () {
                    // Refresh source data
                    this.fetchOpportunitiesBySourceData().then(() => {
                        this.renderOpportunitiesBySourceChart();
                    });
                }.bind(this)
            )
            .catch(function (error) {
                console.error("Error toggling source visibility:", error);
            });
    }

    onSourceToggle(ev) {
        const sourceId = ev.target.value === "0" ? 0 : parseInt(ev.target.value);
        const isChecked = ev.target.checked;
        this.toggleSourceVisibility(sourceId, isChecked);
    }
}

registry.category("actions").add("crm_graph_dashboard", CRMGraphDashboard);
