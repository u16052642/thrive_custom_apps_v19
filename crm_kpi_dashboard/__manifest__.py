{
    "name": "CRM Dashboard",
    "version": "19.0.1.0.0",
    "summary": """CRM Dashboard""",
    "description": """CRM Dashboard""",
    "category": "Generic Modules/Lead and Opportunity Management",
    "author": "7Span",
    "company": "7Span",
    "maintainer": "7Span",
    "website": "https://apps.thrive.com/apps/modules/19.0/crm_kpi_dashboard",
    "depends": ["crm", "sale"],
    "external_dependencies": {
        "python": ["pandas"],
    },
    "data": [
        "views/crm_dashboard_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            # # highcharts
            "https://code.highcharts.com/stock/highstock.js",
            "https://code.highcharts.com/modules/funnel.js",
            "https://code.highcharts.com/modules/exporting.js",
            "https://code.highcharts.com/modules/export-data.js",
            "https://code.highcharts.com/modules/accessibility.js",
            "https://code.highcharts.com/themes/adaptive.js",
            "https://code.highcharts.com/modules/pattern-fill.js",
            # Local assets
            "crm_kpi_dashboard/static/src/css/dashboard.css",
            "crm_kpi_dashboard/static/src/js/dashboard.js",
            "crm_kpi_dashboard/static/src/xml/dashboard.xml",
        ],
    },
    'images': ['static/description/thumbnail.png'],
    "license": "LGPL-3",
    "installable": True,
    "application": True,
}
