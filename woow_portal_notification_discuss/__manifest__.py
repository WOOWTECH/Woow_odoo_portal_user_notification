{
    "name": "Portal Notification Centre - Discussions",
    "version": "18.0.1.0.0",
    "category": "Website",
    "summary": "Unread conversations of woow_odoo_portal_discuss on the portal notification centre",
    "description": """
Conversations (direct messages, groups, channels) create no mail notifications,
so the notification centre cannot list them.  With woow_odoo_portal_discuss
installed, this bridge adds an "Unread conversations" line, linking to
/my/discussions, on /my and on /my/notifications.  Installed automatically.
    """,
    "author": "Woow Tech",
    "website": "https://www.woow.tw",
    "license": "LGPL-3",
    "depends": ["woow_portal_notification", "woow_odoo_portal_discuss"],
    "data": [],
    "installable": True,
    "auto_install": True,
}
