# Copyright 2026 WoowTech
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).
"""Opening a subscription notification from the portal notification centre.

The customer of the subscription lands on the subscription list of the /woow
app, ``/woow#/billing/subscriptions``
(the app has no page per subscription). Anyone else gets what the centre does
for a document without a page of its own: the message, in a dialog. Portal
customers have no access rights on subscriptions; opening the notification
must not end in a 403 for them.
"""
from urllib.parse import urlsplit

import lxml.html
from markupsafe import Markup

from odoo import Command
from odoo.tests import HttpCase, tagged

SUBSCRIPTION_LIST = '/woow#/billing/subscriptions'


@tagged('post_install', '-at_install', 'woow_portal_notification_subscription')
class TestSubscriptionNotificationLink(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.customer = cls._user('wpns_customer', 'base.group_portal')
        cls.follower = cls._user('wpns_follower', 'base.group_portal')
        cls.plan = cls.env['woow.subscription.plan'].create({'name': 'Wpns hosting', 'price': 250.0})
        cls.env['product.product'].create({
            'name': 'Wpns hosting service', 'type': 'service',
            'woow_is_subscription': True, 'woow_subscription_plan_id': cls.plan.id,
        })
        cls.subscription = cls._subscription_of(cls.customer, cls.follower)

    @classmethod
    def _user(cls, login, *groups):
        return cls.env['res.users'].with_context(no_reset_password=True).create({
            'name': login, 'login': login, 'password': login + '_pw!',
            'email': login + '@example.invalid', 'notification_type': 'email',
            'groups_id': [Command.set([cls.env.ref(group).id for group in groups])],
        })

    @classmethod
    def _subscription_of(cls, customer, *followers):
        """A draft subscription of ``customer``, followed by them and by ``followers``."""
        subscription = cls.env['woow.subscription'].create_for_plan(customer.partner_id, cls.plan)
        subscription.message_subscribe([user.partner_id.id for user in (customer, *followers)])
        return subscription

    def _post(self, subscription, body):
        """A public message on the subscription from the system, notifying its followers."""
        return subscription.message_post(
            body=Markup(body), message_type='comment', subtype_xmlid='mail.mt_comment')

    def _notification(self, message, user):
        return self.env['mail.notification'].search([
            ('mail_message_id', '=', message.id), ('res_partner_id', '=', user.partner_id.id)])

    def _login(self, user):
        self.authenticate(user.login, user.login + '_pw!')

    def _open(self, notification):
        """Open the notification as the signed-in user: (status, where the centre sends them)."""
        response = self.url_open('/my/notifications/%d/open' % notification.id, allow_redirects=False)
        location = urlsplit(response.headers.get('Location', ''))
        target = location.path + ('?' + location.query if location.query else '') \
            + ('#' + location.fragment if location.fragment else '')
        return response.status_code, target

    def _title_links(self, html):
        """href of every notification title in the list page, by notification id."""
        document = lxml.html.fromstring(html)
        rows = document.xpath('//tr[contains(concat(" ", @class, " "), " o_wpn_item ")]')
        return {
            int(row.get('data-id')): row.xpath('.//a[contains(concat(" ", @class, " "), " o_wpn_title ")]/@href')[0]
            for row in rows
        }

    def test_customer_opens_the_subscription_list(self):
        mine = self._notification(self._post(self.subscription, '<p>wpns-your-plan</p>'), self.customer)
        self.assertFalse(mine.is_read, "the centre keeps it unread")
        self._login(self.customer)
        self.assertEqual(self._open(mine), (303, SUBSCRIPTION_LIST))
        self.env.invalidate_all()
        self.assertTrue(mine.is_read, "opening it reads it")

    def test_customer_list_links_the_notification_to_its_page(self):
        mine = self._notification(self._post(self.subscription, '<p>wpns-in-the-list</p>'), self.customer)
        self._login(self.customer)
        response = self.url_open('/my/notifications')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._title_links(response.text).get(mine.id), '/my/notifications/%d/open' % mine.id,
                         "a link to the page, not the dialog")

    def test_someone_elses_subscription_gets_the_default(self):
        """A follower who is not the customer: the subscription is no page of theirs."""
        message = self._post(self.subscription, '<p>wpns-not-yours</p>')
        theirs = self._notification(message, self.follower)
        self._login(self.follower)
        self.assertEqual(self._open(theirs), (303, '/my/notifications?open=%d' % theirs.id))
        response = self.url_open('/my/notifications?open=%d' % theirs.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._title_links(response.text).get(theirs.id), '#', "the message opens in the dialog")
        self.assertIn('wpns-not-yours', response.text)

    def test_internal_user_sees_their_own_subscription_only(self):
        """Internal users of the centre see the part their portal shows them: subscriptions billed to them."""
        accountant = self._user('wpns_accountant', 'base.group_user', 'account.group_account_invoice')
        own = self._subscription_of(accountant)
        self.subscription.message_subscribe([accountant.partner_id.id])
        on_own = self._notification(self._post(own, '<p>wpns-staff-own</p>'), accountant)
        on_other = self._notification(self._post(self.subscription, '<p>wpns-staff-other</p>'), accountant)
        self.assertFalse(on_own.is_read, "shown in the centre, so kept unread")
        self.assertTrue(on_other.is_read, "not part of their portal: left as Odoo made it")
        self._login(accountant)
        response = self.url_open('/my/notifications')
        self.assertEqual(response.status_code, 200)
        links = self._title_links(response.text)
        self.assertEqual(links.get(on_own.id), '/my/notifications/%d/open' % on_own.id)
        self.assertNotIn(on_other.id, links, "another customer's subscription is not part of their portal")
        self.assertEqual(self._open(on_own), (303, SUBSCRIPTION_LIST))

    def test_internal_user_without_subscription_rights(self):
        """The centre leaves out what the user may not read; their list still opens."""
        staff = self._user('wpns_staff', 'base.group_user')
        own = self._subscription_of(staff)
        notification = self._notification(self._post(own, '<p>wpns-staff-no-rights</p>'), staff)
        self.assertTrue(notification.is_read)
        self._login(staff)
        response = self.url_open('/my/notifications')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(notification.id, self._title_links(response.text))
