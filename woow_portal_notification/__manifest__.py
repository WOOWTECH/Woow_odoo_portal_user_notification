{
    "name": "Portal Notification Centre",
    "version": "18.0.1.2.1",
    "category": "Website",
    "summary": "An inbox for portal customers: unread notifications, "
               "Odoo's own cards on /my, and a notification list page",
    "description": """
Portal Notification Centre
==========================

Odoo e-mails portal customers about their documents but gives them no place in
the portal to see those notifications.  This module adds one, built only from
Odoo's own portal pieces (home cards and counters, search bar, table, pager),
so it looks like the rest of the portal and follows the website theme:

* portal users' e-mail notifications are kept unread (Odoo creates them read);
  opening the document, the notification or "Mark all as read" reads them;
* /my greets the customer in Odoo's header row and shows Odoo's alert card
  "N Unread notifications" and a "Notifications" card, counted like the
  other cards;
* /my/notifications lists the notifications like the orders list (filter
  all / unread, search, pages); a notification opens its document, or shows
  the message when the document has no page of its own;
* the user menu gets a "Notifications" entry, and the unread count shows next
  to the name, on every website page.

Portal customers see their notifications of public messages (no internal
note) and those Odoo sends them directly.  Internal users (all of them
by default) see the part their portal shows them: public messages (no
internal note) on the documents of their portal (orders, invoices, portal
projects and tasks, ...); their backend Inbox shares the read state.  Bridges (installed automatically) link subscriptions, assigned leads
and loyalty cards to their pages, and count unread conversations.

Settings (system parameters, "0" turns the feature off):

* ``woow_portal_notification.portal_unread``: keep portal notifications unread;
* ``woow_portal_notification.home_summary``: notification cards on /my;
* ``woow_portal_notification.internal_users``: "1" all internal users get the
  centre (default), "group" only the members of the group "Portal
  notification centre for internal users", "0" none (backend Inbox).
    """,
    "author": "Woow Tech",
    "website": "https://www.woow.tw",
    "license": "LGPL-3",
    "depends": ["portal", "mail"],
    "data": [
        "security/woow_portal_notification_groups.xml",
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
