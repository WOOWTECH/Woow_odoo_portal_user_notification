from odoo import api, models


class LoyaltyCard(models.Model):
    _inherit = 'loyalty.card'

    @api.model
    def _wpn_portal_record_domain(self):
        """The user's own cards, as on their history page."""
        return [('partner_id', '=', self.env.user.partner_id.id)]

    def _wpn_portal_url(self):
        """The card's history page of the loyalty portal.  It lets the card
        holder in by comparing partners, so check the same."""
        self.ensure_one()
        if self.sudo().partner_id == self.env.user.partner_id:
            return '/my/loyalty_card/%d/history' % self.id
        return super()._wpn_portal_url()
