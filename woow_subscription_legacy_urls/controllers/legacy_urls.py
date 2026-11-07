# Copyright 2026 WoowTech
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).
"""Permanent redirects from the addresses of the retired subscription portal.

Until the switch to woow_subscription, customers found their subscriptions on
the portal under ``/my/sh_subscription``: a list, its further pages and one
page per subscription. Those addresses live on in e-mails already sent, in
bookmarks and in browser history. Subscriptions are shown by the /woow app now. It routes in the
browser on the part after ``#`` and has a single subscription list with no
page per subscription, so all three addresses lead to that list.

The previous engine serves these very paths. The manifest therefore excludes
it: Odoo refuses to install this module while the previous engine is
installed, and the previous engine while this module is, so its pages are
never taken over. Install this module once the previous engine is
uninstalled.

What is answered, and how:

* GET and HEAD only, with ``301 Moved Permanently``. Other methods find no
  route; the previous engine's JSON endpoints (``/cancel-subscription``,
  ``/renew-subscription``) are not redirected and stay unknown (404).
* Anyone, signed in or not: /woow asks for the sign-in itself. Nothing is
  read or looked up, so the answer says nothing about which subscriptions
  exist, and no session is started or saved for it.
* The query string is dropped. The old pages took paging, sorting and access
  token parameters; /woow reads none of them, and a redirect has no business
  carrying a token or any other input further.
* A small controller rather than ``website.rewrite`` records: it does not need the website module,
  ships and is tested with the module, also covers the per-subscription
  address (a rewrite rule matches one exact path), and answers in one hop.
"""
from odoo import http
from odoo.http import request

#: The subscription list of the /woow app.
SUBSCRIPTION_LIST = '/woow#/billing/subscriptions'

#: The retired addresses: the list, its further pages, one subscription.
LEGACY_ADDRESSES = [
    '/my/sh_subscription',
    '/my/sh_subscription/page/<int:page>',
    '/my/sh_subscription/<int:subscription_id>',
]


class LegacySubscriptionUrls(http.Controller):

    @http.route(LEGACY_ADDRESSES, type='http', auth='public', methods=['GET', 'HEAD'],
                readonly=True, save_session=False, sitemap=False)
    def legacy_subscription_pages(self, **_ignored):
        """Send the visitor to the subscription list of /woow, whatever the old address said."""
        return request.redirect(SUBSCRIPTION_LIST, code=301)
