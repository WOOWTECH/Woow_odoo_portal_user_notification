from odoo import models


class LoyaltyCard(models.Model):
    _inherit = 'loyalty.card'

    def _wpn_portal_url(self):
        """The card's history page of the loyalty portal.  It lets the card
        holder in by comparing partners, so check the same."""
        self.ensure_one()
        if self.sudo().partner_id == self.env.user.partner_id:
            return '/my/loyalty_card/%d/history' % self.id
        return super()._wpn_portal_url()
