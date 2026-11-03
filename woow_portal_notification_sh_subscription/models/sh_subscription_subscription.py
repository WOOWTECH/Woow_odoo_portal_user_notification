from odoo import models


class ShSubscriptionSubscription(models.Model):
    _inherit = 'sh.subscription.subscription'

    def _wpn_portal_url(self):
        """sh_subscription's customer page.  It lets the subscriber in by
        comparing partners, not through access rights, so check the same."""
        self.ensure_one()
        if self.sudo().sh_partner_id == self.env.user.partner_id:
            return '/my/sh_subscription/%d' % self.id
        return super()._wpn_portal_url()
