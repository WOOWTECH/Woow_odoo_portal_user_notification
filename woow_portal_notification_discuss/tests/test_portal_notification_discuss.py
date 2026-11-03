from markupsafe import Markup

from odoo import Command
from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install', 'woow_portal_notification')
class TestPortalNotificationDiscuss(HttpCase):

    def test_unread_conversations_line(self):
        Users = self.env['res.users'].with_context(no_reset_password=True)
        customer = Users.create({
            'name': 'Wpn Chat Customer', 'login': 'wpn_chat', 'password': 'wpn_chat_pw!',
            'email': 'wpn_chat@example.invalid',
            'groups_id': [Command.set([self.env.ref('base.group_portal').id])],
        })
        staff = Users.create({
            'name': 'Wpn Chat Staff', 'login': 'wpn_chat_staff', 'password': 'wpn_chat_staff_pw!',
            'email': 'wpn_chat_staff@example.invalid',
            'groups_id': [Command.set([self.env.ref('base.group_user').id])],
        })
        self.authenticate('wpn_chat', 'wpn_chat_pw!')
        self.assertNotIn('Unread conversations', self.url_open('/my/home').text)

        channel = self.env['discuss.channel'].create({
            'name': 'Wpn chat', 'channel_type': 'group',
            'channel_member_ids': [Command.create({'partner_id': customer.partner_id.id}),
                                   Command.create({'partner_id': staff.partner_id.id})],
        })
        channel.with_user(staff).message_post(
            body=Markup('<p>hi</p>'), message_type='comment', subtype_xmlid='mail.mt_comment')
        html = self.url_open('/my/home').text
        self.assertIn('Unread conversations', html)
        self.assertIn('/my/discussions', html)
        self.assertIn('Unread conversations', self.url_open('/my/notifications').text)
