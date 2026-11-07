# Copyright 2026 WoowTech
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).
"""The addresses of the retired subscription portal.

Each kind of old address answers 301 with the /woow subscription list as
Location; the query string is dropped; nothing else is redirected: no other
method, no other address, and not the previous engine's JSON endpoints.
"""
from urllib.parse import urlsplit

from odoo.tests import HttpCase, new_test_user, tagged

SUBSCRIPTION_LIST = '/woow#/billing/subscriptions'

#: One address of each kind the old portal had: the list, a further page of it, one subscription.
OLD_ADDRESSES = ('/my/sh_subscription', '/my/sh_subscription/page/2', '/my/sh_subscription/42')

#: The routes behind them.
OLD_ROUTES = ('/my/sh_subscription', '/my/sh_subscription/page/<int:page>',
              '/my/sh_subscription/<int:subscription_id>')

#: JSON endpoints of the previous engine: they changed subscriptions, so they are not redirected.
OLD_ENDPOINTS = ('/cancel-subscription', '/renew-subscription')

#: Addresses under the old prefix that the old portal did not have.
NOT_OLD_ADDRESSES = ('/my/sh_subscription/abc', '/my/sh_subscription/page/abc', '/my/sh_subscription/42/extra')


@tagged('post_install', '-at_install', 'woow_subscription_legacy_urls')
class TestLegacySubscriptionAddresses(HttpCase):

    def assertMovedToTheList(self, response):
        """301 to the /woow subscription list: no query string, the part after '#' kept."""
        self.assertEqual(response.status_code, 301, response.url)
        location = response.headers.get('Location')
        self.assertTrue(location, "a redirect without a Location header")
        parts = urlsplit(location)
        self.assertIn(parts.netloc, ('', urlsplit(self.base_url()).netloc))
        self.assertEqual((parts.path, parts.query, parts.fragment), ('/woow', '', '/billing/subscriptions'))

    def assertNotLeadingToWoow(self, response):
        """The final answer is a 404 and no hop on the way led to /woow.

        A database with the website module and a second language may first
        move an unknown address to its language-prefixed twin, so redirects
        are followed."""
        self.assertEqual(response.status_code, 404, response.url)
        hops = [hop.headers.get('Location', '') for hop in response.history]
        self.assertFalse([hop for hop in hops if '/woow' in hop], hops)

    def test_each_kind_of_old_address(self):
        for address in OLD_ADDRESSES:
            with self.subTest(address=address):
                self.assertMovedToTheList(self.url_open(address, allow_redirects=False))

    def test_location_header_as_sent(self):
        """A path on the same site, including its fragment."""
        for address in OLD_ADDRESSES:
            with self.subTest(address=address):
                response = self.url_open(address, allow_redirects=False)
                self.assertEqual(response.headers.get('Location'), SUBSCRIPTION_LIST)

    def test_query_string_is_dropped(self):
        """Paging, sorting or an access token mean nothing to /woow, and a token travels no further."""
        for address in OLD_ADDRESSES:
            with self.subTest(address=address):
                response = self.url_open(address + '?access_token=wpns-token-1&sortby=date&page=3',
                                         allow_redirects=False)
                self.assertMovedToTheList(response)
                self.assertNotIn('wpns-token-1', response.headers['Location'])

    def test_head_is_answered_like_get(self):
        for address in OLD_ADDRESSES:
            with self.subTest(address=address):
                self.assertMovedToTheList(self.url_open(address, head=True))

    def test_trailing_slash(self):
        for address in OLD_ADDRESSES:
            with self.subTest(address=address):
                self.assertMovedToTheList(self.url_open(address + '/', allow_redirects=False))

    def test_signed_in_customer(self):
        customer = new_test_user(self.env, login='wpns_legacy_customer', groups='base.group_portal')
        self.authenticate(customer.login, customer.login)
        for address in OLD_ADDRESSES:
            with self.subTest(address=address):
                self.assertMovedToTheList(self.url_open(address, allow_redirects=False))

    def test_visitor_gets_no_session(self):
        """Nothing is remembered about an anonymous visitor following an old link."""
        response = self.url_open('/my/sh_subscription/42', allow_redirects=False)
        self.assertMovedToTheList(response)
        self.assertNotIn('session_id', response.cookies)

    def test_other_methods_are_not_redirected(self):
        for address in OLD_ADDRESSES:
            with self.subTest(address=address):
                response = self.opener.post(self.base_url() + address, data={'csrf_token': 'x'},
                                            timeout=12, allow_redirects=False)
                self.assertEqual(response.status_code, 405)
                self.assertFalse(response.headers.get('Location'))

    def test_old_json_endpoints_stay_unknown(self):
        for address in OLD_ENDPOINTS:
            with self.subTest(address=address):
                response = self.opener.post(
                    self.base_url() + address, timeout=12, allow_redirects=False,
                    json={'jsonrpc': '2.0', 'method': 'call', 'id': 1, 'params': {'subscription_id': 42}})
                self.assertEqual(response.status_code, 404)
                self.assertFalse(response.headers.get('Location'))
                self.assertNotLeadingToWoow(self.url_open(address))

    def test_other_addresses_under_the_old_prefix_stay_unknown(self):
        for address in NOT_OLD_ADDRESSES:
            with self.subTest(address=address):
                self.assertNotLeadingToWoow(self.url_open(address))

    def test_only_the_three_routes(self):
        """No page is back: the only routes under the old prefix are the redirects, for GET and HEAD."""
        rules = [rule for rule in self.env['ir.http'].routing_map().iter_rules()
                 if rule.rule.startswith('/my/sh_subscription')]
        self.assertCountEqual([rule.rule for rule in rules], OLD_ROUTES)
        for rule in rules:
            self.assertLessEqual(rule.methods, {'GET', 'HEAD', 'OPTIONS'}, rule.rule)
        self.assertFalse([rule.rule for rule in self.env['ir.http'].routing_map().iter_rules()
                          if rule.rule in OLD_ENDPOINTS])
