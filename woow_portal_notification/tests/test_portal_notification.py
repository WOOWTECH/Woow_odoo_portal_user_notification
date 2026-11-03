from markupsafe import Markup

from odoo import Command
from odoo.tests import HttpCase, tagged


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

    def test_home_greeting_and_summary(self):
        for i in range(4):
            self._post('<p>wpn-summary-%d</p>' % i, subject='wpn-subject-%d' % i)
        self._login_portal()
        html = self.url_open('/my/home').text
        self.assertIn('o_wpn_greeting', html)
        self.assertIn('Wpn Customer', html)
        self.assertIn('o_wpn_summary', html)
        self.assertIn('wpn-subject-3', html, "newest unread first")
        self.assertNotIn('wpn-subject-0', html, "three items at most")
        self.assertIn('o_portal_docs', html, "Odoo's own cards stay")

    def test_home_summary_empty_and_switch(self):
        self._login_portal()
        html = self.url_open('/my/home').text
        self.assertIn('No new notifications', html)
        self.env['ir.config_parameter'].sudo().set_param(
            'woow_portal_notification.home_summary', '0')
        html = self.url_open('/my/home').text
        self.assertNotIn('o_wpn_summary', html)
        self.assertIn('o_wpn_greeting', html, "the greeting stays")

    def test_user_menu_entry_and_dot(self):
        self._post('<p>dot</p>')
        self._login_portal()
        html = self.url_open('/my/home').text
        self.assertIn('href="/my/notifications"', html)
        self.assertIn('o_wpn_dot', html)

    def test_internal_user_is_sent_to_the_backend_inbox(self):
        self.authenticate('wpn_staff', 'wpn_staff_pw!')
        response = self.url_open('/my/notifications', allow_redirects=False)
        self.assertEqual(response.status_code, 303)
        self.assertTrue(response.headers['Location'].endswith('/odoo/discuss'))
        html = self.url_open('/my/home').text
        self.assertNotIn('o_wpn_summary', html)
        self.assertNotIn('o_wpn_greeting', html)

    # --- /my/notifications --------------------------------------------------

    def test_list_filter_search_and_order(self):
        self._post('<p>wpn-first-body</p>')
        read_msg = self._post('<p>wpn-read-body</p>')
        self._post('<p>wpn-last-body</p>', author=self.internal_user)
        self._notif(read_msg).is_read = True
        self._login_portal()
        html = self.url_open('/my/notifications').text
        self.assertIn('wpn-read-body', html)
        self.assertIn('o_wpn_person', html, "a message written by someone shows their initial")
        self.assertLess(html.index('wpn-last-body'), html.index('wpn-first-body'),
                        "newest first")
        html = self.url_open('/my/notifications?filterby=unread').text
        self.assertIn('wpn-first-body', html)
        self.assertNotIn('wpn-read-body', html)
        html = self.url_open('/my/notifications?search=wpn-read').text
        self.assertIn('wpn-read-body', html)
        self.assertNotIn('wpn-first-body', html)

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
