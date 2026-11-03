{
    "name": "Portal Notification Centre",
    "version": "18.0.1.0.0",
    "category": "Website",
    "summary": "An inbox for portal customers: unread notifications, "
               "a greeting and summary on /my, and a notification centre page",
    "description": """
Portal Notification Centre
==========================

Odoo e-mails portal customers about their documents but gives them no place in
the portal to see those notifications.  This module adds one, and nothing else:

* portal users' e-mail notifications are kept unread (Odoo creates them read);
  opening the document, the notification or "Mark all as read" reads them;
* /my greets the customer and shows the unread count with the latest unread
  notifications above Odoo's own cards;
* /my/notifications lists every notification (all / unread, search, pages);
  a notification opens its document, or shows the message when the document
  has no page of its own;
* the user menu gets a "Notifications" entry with the count, and the avatar a
  dot, on every website page.

Only portal customers are served; internal users are sent to their backend
Inbox.  The look follows the website theme (Bootstrap variables only).

Settings (system parameters, "0" turns the feature off):

* ``woow_portal_notification.portal_unread``: keep portal notifications unread;
* ``woow_portal_notification.home_summary``: notification summary on /my.
    """,
    "author": "Woow Tech",
    "website": "https://www.woow.tw",
    "license": "LGPL-3",
    "depends": ["portal", "mail"],
    "data": [
        "views/portal_templates.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "woow_portal_notification/static/src/scss/portal_notification.scss",
            "woow_portal_notification/static/src/js/portal_notification.js",
        ],
    },
    "installable": True,
    "application": False,
}
