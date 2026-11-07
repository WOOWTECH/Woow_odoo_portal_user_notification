# Copyright 2026 WoowTech
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).
"""Where the portal notification centre sends a customer for a subscription.

The customers' subscription screen is the /woow app. It routes in the
browser, on the part of the address after ``#``, and has one list of the
customer's subscriptions with no page per subscription, so every subscription
leads to that list.

Both methods only read. The bridge brings no data and has no hook, so it is
inert while the engine is held dormant (R1): a dormant engine has no
subscriptions, hence no notification about one, and nothing here writes.
"""
from odoo import api, models

#: The subscription list of the /woow app, the same for every subscription.
SUBSCRIPTION_LIST = '/woow#/billing/subscriptions'


class WoowSubscription(models.Model):
    _inherit = 'woow.subscription'

    @api.model
    def _wpn_portal_record_domain(self):
        """Subscriptions the centre counts as the current user's own.

        The ones billed to the user's own contact: the subscriptions the /woow
        list shows them. The centre applies this to internal users, with their
        access rights (portal customers see all their notifications anyway).
        """
        return [('partner_id', '=', self.env.user.partner_id.id)]

    def _wpn_portal_url(self):
        """The /woow subscription list for the subscription's customer; the default for anyone else.

        Customers have no access rights on subscriptions (the engine has no
        portal pages), and /woow lets them in by comparing their contact with
        the customer of the subscription. The comparison is made the same way,
        as superuser, so a customer opening the notification never meets an
        access error; nothing else is read on their behalf.
        """
        self.ensure_one()
        if self.sudo().partner_id == self.env.user.partner_id:
            return SUBSCRIPTION_LIST
        return super()._wpn_portal_url()
