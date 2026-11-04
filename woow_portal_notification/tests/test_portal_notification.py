import re
from unittest.mock import patch

import lxml.html
from markupsafe import Markup

from odoo import Command
from odoo.tests import HttpCase, tagged
from odoo.tests.common import JsonRpcException


@tagged('post_install', '-at_install', 'woow_portal_notification')
class TestPortalNotification(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Users = cls.env['res.users'].with_context(no_reset_password=True)
        cls.portal_user = Users.create({
            'name': 'Wpn Customer', 'login': 'wpn_portal', 'password': 'wpn_portal_pw!',
            'email': 'wpn_portal@example.invalid',
            'groups_id': [Command.set([cls.env.ref('base.group_portal').id])],
        })
        cls.other_portal = Users.create({
            'name': 'Wpn Other', 'login': 'wpn_other', 'password': 'wpn_other_pw!',
            'email': 'wpn_other@example.invalid',
            'groups_id': [Command.set([cls.env.ref('base.group_portal').id])],
        })
        cls.internal_user = Users.create({
            'name': 'Wpn Staff', 'login': 'wpn_staff', 'password': 'wpn_staff_pw!',
            'email': 'wpn_staff@example.invalid', 'notification_type': 'email',
            'groups_id': [Command.set([cls.env.ref('base.group_user').id])],
        })
        # a document without a portal page of its own
        cls.thread = cls.env['res.partner'].create({'name': 'Wpn Thread'})
        cls.thread.message_subscribe([
            cls.portal_user.partner_id.id, cls.other_portal.partner_id.id,
            cls.internal_user.partner_id.id])

    def _post(self, body, author=None, record=None, **kwargs):
        """Post a message notifying the followers; by default from the system
        (the author of a message is not notified of it)."""
        if author:
            kwargs['author_id'] = author.partner_id.id
        return (record or self.thread).message_post(
            body=Markup(body), message_type='comment', subtype_xmlid='mail.mt_comment',
            **kwargs)

    def _notif(self, message, user=None):
        return self.env['mail.notification'].search([
            ('mail_message_id', '=', message.id),
            ('res_partner_id', '=', (user or self.portal_user).partner_id.id)])

    def _login_portal(self):
        self.authenticate('wpn_portal', 'wpn_portal_pw!')

    # --- unread mechanism -------------------------------------------------

    def test_portal_notification_starts_unread(self):
        message = self._post('<p>hello customer</p>')
        notif = self._notif(message)
        self.assertEqual(notif.notification_type, 'email')
        self.assertFalse(notif.is_read, "portal customers get their notifications unread")
        self.assertTrue(self._notif(message, self.internal_user).is_read,
                        "internal e-mail users keep Odoo's behaviour")
        self.assertEqual(self.portal_user._wpn_unread_count(), 1)
        self.assertEqual(self.internal_user._wpn_unread_count(), 0)

    def test_switch_off_keeps_odoo_default(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'woow_portal_notification.portal_unread', '0')
        message = self._post('<p>switched off</p>')
        self.assertTrue(self._notif(message).is_read)

    # --- /my --------------------------------------------------------------

    def _counters(self):
        return self.make_jsonrpc_request('/my/counters', {
            'counters': ['wpn_unread_count', 'wpn_notification_count']})

    def test_home_greeting_and_cards(self):
        for i in range(4):
            self._post('<p>wpn-home-%d</p>' % i)
        self._notif(self._post('<p>wpn-home-read</p>')).is_read = True
        self._login_portal()
        html = self.url_open('/my/home').text
        self.assertIn('o_wpn_greeting', html)
        self.assertIn('Wpn Customer', html)
        # Odoo's own cards, counted through /my/counters
        self.assertIn('data-placeholder_count="wpn_unread_count"', html)
        self.assertIn('data-placeholder_count="wpn_notification_count"', html)
        counters = self._counters()
        self.assertEqual(counters['wpn_unread_count'], 4)
        self.assertEqual(counters['wpn_notification_count'], 5)

    def test_home_cards_switch(self):
        self._post('<p>wpn-switch</p>')
        self.env['ir.config_parameter'].sudo().set_param(
            'woow_portal_notification.home_summary', '0')
        self._login_portal()
        counters = self._counters()
        self.assertEqual(counters['wpn_unread_count'], 0, "a card counting 0 stays hidden")
        self.assertEqual(counters['wpn_notification_count'], 0)
        self.assertIn('o_wpn_greeting', self.url_open('/my/home').text, "the greeting stays")

    def test_user_menu_entry_and_count(self):
        self._post('<p>count</p>')
        self._post('<p>count again</p>')
        self._login_portal()
        html = self.url_open('/my/home').text
        self.assertIn('href="/my/notifications"', html)
        self.assertRegex(html, r'o_wpn_unread_count"[^>]*>2<')
        if 'website' in self.env:
            self.assertRegex(self.url_open('/').text, r'o_wpn_unread_count"[^>]*>2<',
                             "the count is on website pages too")

    def test_user_menu_count_is_per_visitor(self):
        """Without website, Odoo caches the portal navbar per company
        (t-cache="res_company").  The user menu inside it is rendered for each
        visitor (t-nocache), and so must be the count and entry added to it."""
        for i in range(3):
            self._post('<p>wpn-visitor-%d</p>' % i)
        self.env['mail.notification'].search([
            ('res_partner_id', '=', self.other_portal.partner_id.id)])[:2].is_read = True
        self.assertEqual(self.portal_user._wpn_unread_count(), 3)
        self.assertEqual(self.other_portal._wpn_unread_count(), 1)
        visitors = {  # login, password, counts shown, menu entry shown
            'portal': ('wpn_portal', 'wpn_portal_pw!', {'3'}, True),
            'other': ('wpn_other', 'wpn_other_pw!', {'1'}, True),
            'staff': ('wpn_staff', 'wpn_staff_pw!', set(), False),
            'public': (None, None, set(), False),
        }
        names = {'portal': 'Wpn Customer', 'other': 'Wpn Other', 'staff': 'Wpn Staff'}
        website = 'website' in self.env
        Qweb = type(self.env['ir.qweb'])
        load_values = Qweb._load_values
        navbar = []

        def spy(qweb, cache_key, get_value, loaded_values=None):
            # whether the per-company navbar block came from the cache
            computed = []

            def compute():
                computed.append(True)
                return get_value()
            value = load_values(qweb, cache_key, compute, loaded_values)
            if "'res.company'" in str(cache_key):
                navbar.append(bool(computed))
            return value

        orders = [('portal', 'other', 'staff', 'public'), ('other', 'staff', 'public', 'portal'),
                  ('public', 'staff', 'other', 'portal'), ('staff', 'portal', 'public', 'other')]
        with patch.object(Qweb, '_load_values', spy):
            for order in orders:
                self.env.registry.clear_cache('templates')
                navbar.clear()
                for who in order:
                    login, password, counts, entry = visitors[who]
                    self.authenticate(login, password)
                    # the login page has no header; with website, the home page has one
                    url = '/my/home' if login else ('/' if website else '/web/login')
                    response = self.url_open(url)
                    self.assertEqual(response.status_code, 200, (order, who))
                    html = response.text
                    found = re.findall(r'o_wpn_unread_count"[^>]*>(\d+)<', html)
                    self.assertEqual(set(found), counts, (order, who))
                    self.assertEqual('href="/my/notifications" role="menuitem"' in html, entry,
                                     (order, who))
                    for other, name in names.items():
                        if other != who:
                            self.assertNotIn(name, html, (order, who))
                if not website:
                    self.assertEqual(navbar, [True, False, False],
                                     "after the first visitor the navbar comes from the cache")

    def test_internal_user_is_sent_to_the_backend_inbox(self):
        self._post('<p>for staff</p>')
        self.authenticate('wpn_staff', 'wpn_staff_pw!')
        response = self.url_open('/my/notifications', allow_redirects=False)
        self.assertEqual(response.status_code, 303)
        self.assertTrue(response.headers['Location'].endswith('/odoo/discuss'))
        html = self.url_open('/my/home').text
        self.assertNotIn('o_wpn_greeting', html)
        self.assertNotIn('href="/my/notifications" role="menuitem"', html)
        self.assertEqual(self._counters()['wpn_unread_count'], 0)

    # --- /my/notifications --------------------------------------------------

    def test_list_filter_search_and_order(self):
        unread = self._notif(self._post('<p>wpn-first-body</p>'))
        read_msg = self._post('<p>wpn-read-body</p>')
        self._post('<p>wpn-last-body</p>', author=self.internal_user)
        read = self._notif(read_msg)
        read.is_read = True
        self._login_portal()
        html = self.url_open('/my/notifications').text
        doc = lxml.html.fromstring(html)

        def classes(notif, part):
            return doc.xpath('//tr[@data-id="%d"]//*[contains(@class, "%s")]/@class'
                             % (notif.id, part))[0].split()
        # the read state shows through Bootstrap's d-none (some websites force
        # the display of .btn, which would show both buttons of the pair)
        self.assertIn('d-none', classes(read, 'o_wpn_unread_badge'))
        self.assertIn('d-none', classes(read, 'o_wpn_when_unread'))
        self.assertNotIn('d-none', classes(read, 'o_wpn_when_read'))
        self.assertNotIn('d-none', classes(unread, 'o_wpn_unread_badge'))
        self.assertNotIn('d-none', classes(unread, 'o_wpn_when_unread'))
        self.assertIn('d-none', classes(unread, 'o_wpn_when_read'))
        self.assertIn('wpn-read-body', html)
        self.assertIn('fa-comment-o', html, "a message written by someone shows a speech bubble")
        self.assertIn('Wpn Staff', html, "and its author")
        self.assertLess(html.index('wpn-last-body'), html.index('wpn-first-body'),
                        "newest first")
        self.assertIn('o_wpn_filters', html, "All / Unread / Read switch")
        html = self.url_open('/my/notifications?filterby=unread').text
        self.assertIn('wpn-first-body', html)
        self.assertNotIn('wpn-read-body', html)
        html = self.url_open('/my/notifications?filterby=read').text
        self.assertIn('wpn-read-body', html, "read notifications stay reachable")
        self.assertNotIn('wpn-first-body', html)
        html = self.url_open('/my/notifications?search=wpn-read').text
        self.assertIn('wpn-read-body', html)
        self.assertNotIn('wpn-first-body', html)

    def test_back_button_gets_fresh_pages(self):
        self._login_portal()
        for url in ('/my/home', '/my/notifications'):
            self.assertEqual(self.url_open(url).headers.get('Cache-Control'), 'no-store', url)

    def test_ordered_by_message_date(self):
        old = self._post('<p>wpn-backdated-body</p>')
        old.sudo().date = '2020-01-01 08:00:00'
        self._post('<p>wpn-recent-body</p>')
        self._post('<p>wpn-newest-body</p>')
        self._login_portal()
        html = self.url_open('/my/notifications').text
        self.assertLess(html.index('wpn-newest-body'), html.index('wpn-recent-body'))
        self.assertLess(html.index('wpn-recent-body'), html.index('wpn-backdated-body'),
                        "a back-dated message goes after newer ones, whatever its id")

    def test_open_without_page_shows_the_message(self):
        message = self._post('<p>wpn-modal-body</p>')
        notif = self._notif(message)
        self._login_portal()
        response = self.url_open('/my/notifications/%d/open' % notif.id, allow_redirects=False)
        self.assertEqual(response.status_code, 303)
        self.assertIn('/my/notifications?open=%d' % notif.id, response.headers['Location'])
        self.assertTrue(notif.is_read)
        html = self.url_open('/my/notifications?open=%d' % notif.id).text
        self.assertIn('data-open="%d"' % notif.id, html)
        self.assertIn('wpn-modal-body', html)
        self.assertRegex(html, r'<template [^>]*class="o_wpn_body_src"',
                         "kept inert until the dialog is opened")

    def test_page_lookup_bug_is_logged_and_shown_in_the_dialog(self):
        self._post('<p>wpn-broken-lookup</p>')
        self._login_portal()
        Partner = type(self.env['res.partner'])
        with patch.object(Partner, '_wpn_portal_url', side_effect=ValueError('bridge bug')), \
                self.assertLogs('odoo.addons.woow_portal_notification.controllers.portal',
                                'WARNING') as logs:
            html = self.url_open('/my/notifications').text
        self.assertIn('wpn-broken-lookup', html, "the list still shows")
        self.assertIn('o_wpn_body_src', html, "with the message in the dialog")
        self.assertTrue(any('no portal URL' in line for line in logs.output), logs.output)

    def test_open_with_portal_page_goes_to_the_document(self):
        if 'sale.order' not in self.env:
            self.skipTest('needs sale')
        order = self.env['sale.order'].create({'partner_id': self.portal_user.partner_id.id})
        order.message_subscribe([self.portal_user.partner_id.id])
        message = self._post('<p>about your order</p>', record=order)
        notif = self._notif(message)
        self._login_portal()
        response = self.url_open('/my/notifications/%d/open' % notif.id, allow_redirects=False)
        self.assertIn('/my/orders/%d' % order.id, response.headers['Location'])
        # opening the document page itself reads the notifications about it
        other = self._notif(self._post('<p>second</p>', record=order))
        self.assertFalse(other.is_read)
        self.url_open('/my/orders/%d' % order.id)
        self.assertTrue(other.is_read)

    def test_read_switch_and_ownership(self):
        mine = self._notif(self._post('<p>mine</p>'))
        theirs = self._notif(self._post('<p>theirs</p>'), self.other_portal)
        self._login_portal()
        result = self.make_jsonrpc_request('/my/notifications/read', {
            'notification_ids': [mine.id, theirs.id], 'read': True})
        self.assertEqual(result['updated'], [mine.id])
        self.assertTrue(mine.is_read)
        self.assertFalse(theirs.is_read, "someone else's notification is untouched")
        self.make_jsonrpc_request('/my/notifications/read', {
            'notification_ids': [mine.id], 'read': False})
        self.assertFalse(mine.is_read)
        response = self.url_open('/my/notifications/%d/open' % theirs.id, allow_redirects=False)
        self.assertTrue(response.headers['Location'].endswith('/my/notifications'))
        self.assertFalse(theirs.is_read)

    def test_read_flag_must_be_a_boolean(self):
        mine = self._notif(self._post('<p>mine</p>'))
        self._login_portal()
        with self.assertRaises(JsonRpcException):
            self.make_jsonrpc_request('/my/notifications/read', {
                'notification_ids': [mine.id], 'read': 'false'})
        self.assertFalse(mine.is_read, "the string 'false' is refused, not taken as true")

    def test_mark_all_read_follows_search(self):
        hit = self._notif(self._post('<p>wpn-alpha</p>'))
        miss = self._notif(self._post('<p>wpn-beta</p>'))
        self._login_portal()
        result = self.make_jsonrpc_request('/my/notifications/read_all', {'search': 'wpn-alpha'})
        self.assertEqual(result['updated'], 1)
        self.assertTrue(hit.is_read)
        self.assertFalse(miss.is_read)
        self.make_jsonrpc_request('/my/notifications/read_all', {})
        self.assertTrue(miss.is_read)
        self.assertEqual(self.portal_user._wpn_unread_count(), 0)

    # --- internal users of the centre's group -----------------------------

    def _make_member(self, notification_type='email'):
        self.internal_user.write({
            'notification_type': notification_type,
            'groups_id': [Command.link(self.env.ref('woow_portal_notification.group_internal_centre').id)],
        })
        return self.internal_user

    def _as_portal_document(self):
        """Let the test contact count as a document of the portal, as a
        portal.mixin document would (contacts have no portal page)."""
        return patch.object(type(self.env['res.partner']), '_wpn_portal_record_domain', lambda self: [])

    def _note(self, body, user):
        return self.thread.message_post(
            body=Markup(body), message_type='comment', subtype_xmlid='mail.mt_note',
            partner_ids=[user.partner_id.id])

    def test_internal_member_sees_the_portal_part_only(self):
        member = self._make_member('email')
        with self._as_portal_document():
            public = self._notif(self._post('<p>wpn-public-for-staff</p>'), member)
            note = self._notif(self._note('<p>wpn-internal-note</p>', member), member)
            self.assertEqual(public.notification_type, 'email')
            self.assertFalse(public.is_read, "handled by e-mail, kept unread for the centre")
            self.assertTrue(note.is_read, "an internal note stays as Odoo makes it")

            self.authenticate('wpn_staff', 'wpn_staff_pw!')
            response = self.url_open('/my/notifications', allow_redirects=False)
            self.assertEqual(response.status_code, 200)
            self.assertIn('wpn-public-for-staff', response.text)
            self.assertNotIn('wpn-internal-note', response.text)
            html = self.url_open('/my/home').text
            self.assertIn('o_wpn_greeting', html)
            self.assertIn('href="/my/notifications" role="menuitem"', html)
            self.assertRegex(html, r'o_wpn_unread_count"[^>]*>1<')
            self.assertEqual(self._counters()['wpn_unread_count'], 1)
            # out of the centre: not opened, not read
            response = self.url_open('/my/notifications/%d/open' % note.id, allow_redirects=False)
            self.assertTrue(response.headers['Location'].endswith('/my/notifications'))
            result = self.make_jsonrpc_request('/my/notifications/read', {
                'notification_ids': [note.id, public.id], 'read': True})
            self.assertEqual(result['updated'], [public.id])
            self.assertEqual(result['unread_count'], 0)

        # a document without a portal page is not part of their portal
        self.assertNotIn('wpn-public-for-staff', self.url_open('/my/notifications').text)
        self.assertEqual(member._wpn_unread_count(), 0)

    def test_internal_member_shares_the_inbox_read_state(self):
        member = self._make_member('inbox')
        with self._as_portal_document():
            message = self._post('<p>wpn-inbox-staff</p>')
            notif = self._notif(message, member)
            self.assertEqual(notif.notification_type, 'inbox')
            self.assertFalse(notif.is_read)
            self.assertTrue(message.with_user(member).needaction, "in the backend inbox")
            self.authenticate('wpn_staff', 'wpn_staff_pw!')
            self.make_jsonrpc_request('/my/notifications/read', {'notification_ids': [notif.id], 'read': True})
            self.env.invalidate_all()
            self.assertTrue(notif.is_read)
            self.assertFalse(message.with_user(member).needaction, "read in the backend inbox too")

    def test_internal_member_switch_off_keeps_odoo_default(self):
        member = self._make_member('email')
        self.env['ir.config_parameter'].sudo().set_param('woow_portal_notification.portal_unread', '0')
        with self._as_portal_document():
            notif = self._notif(self._post('<p>wpn-switched-off</p>'), member)
        self.assertTrue(notif.is_read)

