from odoo import api, models


class ShSubscriptionSubscription(models.Model):
    _inherit = 'sh.subscription.subscription'

    @api.model
    def _wpn_portal_record_domain(self):
        """The user's own subscriptions, as on their page."""
        return [('sh_partner_id', '=', self.env.user.partner_id.id)]

    def _wpn_portal_url(self):
        """sh_subscription's customer page.  It lets the subscriber in by
        comparing partners, not through access rights, so check the same."""
        self.ensure_one()
        if self.sudo().sh_partner_id == self.env.user.partner_id:
            return '/my/sh_subscription/%d' % self.id
        return super()._wpn_portal_url()
