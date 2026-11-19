# Copyright 2026 WoowTech
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).
"""Where the portal notification centre sends a customer for a subscription.

A customer's subscription has a page of its own in "My account",
``/my/subscriptions/<id>`` (added by the woow_paas_platform module, which shows
it only to the subscription's customer), so a notification about a
subscription leads to that page.

Both methods only read. The bridge brings no data and has no hook, so it is
inert while the engine is held dormant (R1): a dormant engine has no
subscriptions, hence no notification about one, and nothing here writes.
"""
from odoo import api, models

#: The page of one subscription in "My account".
SUBSCRIPTION_PAGE = '/my/subscriptions/%d'


class WoowSubscription(models.Model):
    _inherit = 'woow.subscription'

    @api.model
    def _wpn_portal_record_domain(self):
        """Subscriptions the centre counts as the current user's own.

        The ones billed to the user's own contact: the subscriptions "My
        account" shows them. The centre applies this to internal users, with their
        access rights (portal customers see all their notifications anyway).
        """
        return [('partner_id', '=', self.env.user.partner_id.id)]

    def _wpn_portal_url(self):
        """The subscription's page in "My account" for its customer; the default for anyone else.

        Customers have no access rights on subscriptions, and the page lets them
        in by comparing their contact with the customer of the subscription. The
        comparison is made the same way, as superuser, so a customer opening the
        notification never meets an access error; nothing else is read on their
        behalf.
        """
        self.ensure_one()
        if self.sudo().partner_id == self.env.user.partner_id:
            return SUBSCRIPTION_PAGE % self.id
        return super()._wpn_portal_url()
