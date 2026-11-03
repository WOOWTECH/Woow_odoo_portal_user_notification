from datetime import timedelta

from markupsafe import Markup

from odoo import Command, fields
from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install', 'woow_portal_notification')
class TestSubscriptionLink(HttpCase):

    def test_subscription_notification_opens_its_page(self):
        Users = self.env['res.users'].with_context(no_reset_password=True)
        portal = self.env.ref('base.group_portal')
        customer = Users.create({'name': 'Wpn Subscriber', 'login': 'wpn_sub', 'password': 'wpn_sub_pw!',
                                 'email': 'wpn_sub@example.invalid', 'groups_id': [Command.set([portal.id])]})
        other = Users.create({'name': 'Wpn Follower', 'login': 'wpn_sub_other', 'password': 'wpn_sub_other_pw!',
                              'email': 'wpn_sub_other@example.invalid', 'groups_id': [Command.set([portal.id])]})
        plan = self.env['sh.subscription.plan'].create({
            'name': 'Wpn plan', 'sh_duration': 1, 'sh_unit': 'month', 'sh_plan_price': 100,
            'sh_no_of_billing_cycle': 1})
        product = self.env['product.product'].create({'name': 'Wpn subscription', 'list_price': 100})
        today = fields.Date.today()
        partner = customer.partner_id
        subscription = self.env['sh.subscription.subscription'].create({
            'sh_partner_id': partner.id, 'sh_partner_invoice_id': partner.id, 'product_id': product.id,
            'sh_qty': 1, 'sh_subscription_plan_id': plan.id, 'sh_plan_price': 100, 'sh_recurrency': 1,
            'sh_unit': 'month', 'sh_start_date': today, 'sh_end_date': today + timedelta(days=29),
            'sh_no_of_billing_cycle': 1, 'sh_source': 'manual', 'sh_date_of_next_payment': today})
        subscription.message_subscribe([partner.id, other.partner_id.id])
        message = subscription.message_post(body=Markup('<p>renewal soon</p>'), message_type='comment',
                                            subtype_xmlid='mail.mt_comment')
        Notification = self.env['mail.notification']

        mine = Notification.search([('mail_message_id', '=', message.id), ('res_partner_id', '=', partner.id)])
        self.authenticate('wpn_sub', 'wpn_sub_pw!')
        response = self.url_open('/my/notifications/%d/open' % mine.id, allow_redirects=False)
        self.assertTrue(response.headers['Location'].endswith('/my/sh_subscription/%d' % subscription.id))

        # a follower who is not the subscriber: the page would turn them away
        theirs = Notification.search([('mail_message_id', '=', message.id),
                                      ('res_partner_id', '=', other.partner_id.id)])
        self.authenticate('wpn_sub_other', 'wpn_sub_other_pw!')
        response = self.url_open('/my/notifications/%d/open' % theirs.id, allow_redirects=False)
        self.assertIn('/my/notifications?open=%d' % theirs.id, response.headers['Location'])
