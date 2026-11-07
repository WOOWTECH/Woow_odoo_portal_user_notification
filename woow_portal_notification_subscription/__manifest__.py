# Copyright 2026 WoowTech
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).
{
    'name': "Portal Notification Centre - WOOW Subscriptions",
    'version': '18.0.1.0.0',
    'category': 'Website',
    'summary': "Notifications about a subscription open the subscription list of the /woow app",
    # Kept short and plain on purpose: without it Odoo would render README.md as reStructuredText.
    'description': """
Links the portal notification centre (woow_portal_notification) to the WOOW
subscription engine (woow_subscription). A customer who opens a notification
about one of their subscriptions lands on the subscription list of the /woow
app. Anyone else gets what the centre does for a document without a page of
its own. Read-only: the module brings no data and writes nothing.

Installed automatically when both modules are present. The module directory
holds a README.md with the details.
""",
    'author': "WoowTech",
    'license': 'LGPL-3',
    'depends': ['woow_portal_notification', 'woow_subscription'],
    'data': [],
    'installable': True,
    'auto_install': True,
    'application': False,
}
