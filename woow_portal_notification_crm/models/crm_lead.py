from odoo import models


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    def _wpn_portal_url(self):
        """website_crm_partner_assign's pages for the leads and opportunities
        assigned to the customer's company; its access rules decide."""
        self.ensure_one()
        if self.type in ('lead', 'opportunity') and self.has_access('read'):
            return ('/my/opportunity/%d' if self.type == 'opportunity' else '/my/lead/%d') % self.id
        return super()._wpn_portal_url()
