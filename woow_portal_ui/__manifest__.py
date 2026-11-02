{
    "name": "Woow Portal UI",
    "version": "18.0.2.2.3",
    "category": "Website",
    "summary": "Clean, minimal Portal UI enhancements",
    "description": """
        Portal UI enhancements for Odoo 18:
        - White navbar background
        - Logo link to /my/home
        - Greeting card on home page
        - Footer hidden
        - Search bar on home page
        - Notification center
        - Hide zero-count module cards
        - Breadcrumb back button
        - Backend to Portal switch
    """,
    "author": "Woow Tech",
    "website": "https://www.woow.tw",
    "license": "LGPL-3",
    "depends": ["portal", "mail", "web"],
    "data": [
        "security/ir.model.access.csv",
        "views/portal_templates.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "woow_portal_ui/static/src/css/portal.css",
            "woow_portal_ui/static/src/css/woowtech_theme.css",
            "woow_portal_ui/static/src/css/detail_pages.css",
            "woow_portal_ui/static/src/js/portal.js",
            "woow_portal_ui/static/src/js/portal_counter_fix.js",
        ],
        "web.assets_backend": [
            "woow_portal_ui/static/src/js/switch_portal.js",
        ],
        "portal.assets_chatter_style": [
            "woow_portal_ui/static/src/css/chatter_theme.css",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
}
