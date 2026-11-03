from markupsafe import Markup

from odoo import Command
from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install', 'woow_portal_notification')
class TestAssignedLeadLink(HttpCase):

    def test_assigned_lead_and_opportunity_open_their_page(self):
        Users = self.env['res.users'].with_context(no_reset_password=True)
        portal = self.env.ref('base.group_portal')
        customer = Users.create({'name': 'Wpn Reseller', 'login': 'wpn_crm', 'password': 'wpn_crm_pw!',
                                 'email': 'wpn_crm@example.invalid', 'groups_id': [Command.set([portal.id])]})
        partner = customer.partner_id
        Lead = self.env['crm.lead']
        lead = Lead.create({'name': 'Wpn lead', 'type': 'lead', 'partner_assigned_id': partner.id})
        opportunity = Lead.create({'name': 'Wpn opportunity', 'type': 'opportunity',
                                   'partner_assigned_id': partner.id})
        not_assigned = Lead.create({'name': 'Wpn other', 'type': 'opportunity'})
        Notification = self.env['mail.notification']
        notifs = {}
        for record in (lead, opportunity, not_assigned):
            record.message_subscribe([partner.id])
            message = record.message_post(body=Markup('<p>update</p>'), message_type='comment',
                                          subtype_xmlid='mail.mt_comment')
            notifs[record] = Notification.search([('mail_message_id', '=', message.id),
                                                  ('res_partner_id', '=', partner.id)])
        self.authenticate('wpn_crm', 'wpn_crm_pw!')

        def location(record):
            return self.url_open('/my/notifications/%d/open' % notifs[record].id,
                                 allow_redirects=False).headers['Location']

        self.assertTrue(location(lead).endswith('/my/lead/%d' % lead.id))
        self.assertTrue(location(opportunity).endswith('/my/opportunity/%d' % opportunity.id))
        self.assertIn('/my/notifications?open=', location(not_assigned),
                      "not assigned to the customer: no page they could open")
