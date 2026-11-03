from markupsafe import Markup

from odoo import Command
from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install', 'woow_portal_notification')
class TestLoyaltyCardLink(HttpCase):

    def test_gift_card_notification_opens_its_history(self):
        Users = self.env['res.users'].with_context(no_reset_password=True)
        portal = self.env.ref('base.group_portal')
        customer = Users.create({'name': 'Wpn Card Holder', 'login': 'wpn_card', 'password': 'wpn_card_pw!',
                                 'email': 'wpn_card@example.invalid', 'groups_id': [Command.set([portal.id])]})
        other = Users.create({'name': 'Wpn Card Follower', 'login': 'wpn_card_other',
                              'password': 'wpn_card_other_pw!', 'email': 'wpn_card_other@example.invalid',
                              'groups_id': [Command.set([portal.id])]})
        program = self.env['loyalty.program'].create({
            'name': 'Wpn gift card', 'program_type': 'gift_card', 'applies_on': 'future', 'trigger': 'auto'})
        card = self.env['loyalty.card'].create({'program_id': program.id, 'partner_id': customer.partner_id.id,
                                                'points': 500, 'code': 'WPN-GIFT-500'})
        card.message_subscribe([customer.partner_id.id, other.partner_id.id])
        message = card.message_post(body=Markup('<p>topped up</p>'), message_type='comment',
                                    subtype_xmlid='mail.mt_comment')
        Notification = self.env['mail.notification']

        mine = Notification.search([('mail_message_id', '=', message.id),
                                    ('res_partner_id', '=', customer.partner_id.id)])
        self.authenticate('wpn_card', 'wpn_card_pw!')
        response = self.url_open('/my/notifications/%d/open' % mine.id, allow_redirects=False)
        self.assertTrue(response.headers['Location'].endswith('/my/loyalty_card/%d/history' % card.id))

        theirs = Notification.search([('mail_message_id', '=', message.id),
                                      ('res_partner_id', '=', other.partner_id.id)])
        self.authenticate('wpn_card_other', 'wpn_card_other_pw!')
        response = self.url_open('/my/notifications/%d/open' % theirs.id, allow_redirects=False)
        self.assertIn('/my/notifications?open=%d' % theirs.id, response.headers['Location'])
