# Copyright 2026 WoowTech
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).
{
    'name': "WOOW Subscriptions - Old Portal Addresses",
    'version': '18.0.1.0.0',
    'category': 'Hidden',
    'summary': "Permanent redirects from the retired subscription portal pages to the /woow app",
    # Kept short and plain on purpose: without it Odoo would render README.md as reStructuredText.
    'description': """
The subscription pages of the portal are retired with the switch to the WOOW
subscription engine. Their addresses, still found in e-mails already sent and
in bookmarks, answer with a permanent redirect (301) to the subscription list
of the /woow app. The module renders nothing and reads no data.

The previous engine served the same addresses, so the two cannot be installed
together: install this module after the previous engine is uninstalled. It is
meant to stay six months, then be removed. The module directory holds a
README.md with the details.
""",
    'author': "WoowTech",
    'license': 'LGPL-3',
    'depends': ['web'],
    # The previous engine served the same pages: never take them over from it.
    'excludes': ['sh_subscription'],
    'data': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}
