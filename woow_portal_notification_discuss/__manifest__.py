{
    "name": "Portal Notification Centre - Discussions",
    "version": "18.0.1.1.0",
    "category": "Website",
    "summary": "Unread conversations of woow_odoo_portal_discuss on the portal notification centre",
    "description": """
Conversations (direct messages, groups, channels) create no mail notifications,
so the notification centre cannot list them.  With woow_odoo_portal_discuss
installed, this bridge adds Odoo's alert card "N unread conversations" on /my
and a notice on /my/notifications, both linking to /my/discussions.  Installed
automatically.
    """,
    "author": "Woow Tech",
    "website": "https://www.woow.tw",
    "license": "LGPL-3",
    "depends": ["woow_portal_notification", "woow_odoo_portal_discuss"],
    "data": [
        "views/portal_templates.xml",
    ],
    "installable": True,
    "auto_install": True,
}
