# Copyright 2026 WoowTech
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).
"""Permanent redirects from the addresses of the retired subscription portal.

Until the switch to woow_subscription, customers found their subscriptions on
the portal under ``/my/sh_subscription``: a list, its further pages and one
page per subscription. Those addresses live on in e-mails already sent, in
bookmarks and in browser history. "My account" shows subscriptions again,
under ``/my/subscriptions`` (pages of the woow_paas_platform module): the list
and its further pages lead to that list, and the page of one subscription to
the page of the same subscription, the switch having kept the ids.

The previous engine serves these very paths. The manifest therefore excludes
it: Odoo refuses to install this module while the previous engine is
installed, and the previous engine while this module is, so its pages are
never taken over. Install this module once the previous engine is
uninstalled.

What is answered, and how:

* GET and HEAD only, with ``301 Moved Permanently``. Other methods find no
  route; the previous engine's JSON endpoints (``/cancel-subscription``,
  ``/renew-subscription``) are not redirected and stay unknown (404).
* Anyone, signed in or not: the pages of "My account" ask for the sign-in
  themselves, and show a subscription only to its customer. Nothing is read or
  looked up here, so the answer says nothing about which subscriptions exist,
  and no session is started or saved for it.
* The query string is dropped. The old pages took paging, sorting and access
  token parameters; the new pages read none of them, and a redirect has no
  business carrying a token or any other input further.
* A small controller rather than ``website.rewrite`` records: it does not need the website module,
  ships and is tested with the module, also covers the per-subscription
  address (a rewrite rule matches one exact path), and answers in one hop.
"""
from odoo import http
from odoo.http import request

#: The subscription list of "My account".
SUBSCRIPTION_LIST = '/my/subscriptions'

#: The page of one subscription in "My account".
SUBSCRIPTION_PAGE = '/my/subscriptions/%d'

#: The retired addresses: the list, its further pages, one subscription.
LEGACY_ADDRESSES = [
    '/my/sh_subscription',
    '/my/sh_subscription/page/<int:page>',
    '/my/sh_subscription/<int:subscription_id>',
]


class LegacySubscriptionUrls(http.Controller):

    @http.route(LEGACY_ADDRESSES, type='http', auth='public', methods=['GET', 'HEAD'],
                readonly=True, save_session=False, sitemap=False)
    def legacy_subscription_pages(self, subscription_id=None, **_ignored):
        """Send the visitor to the same subscription, or to the list, in "My account"."""
        if subscription_id is not None:
            return request.redirect(SUBSCRIPTION_PAGE % subscription_id, code=301)
        return request.redirect(SUBSCRIPTION_LIST, code=301)
