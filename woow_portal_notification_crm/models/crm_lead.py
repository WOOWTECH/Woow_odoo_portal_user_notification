from odoo import api, models


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    @api.model
    def _wpn_portal_record_domain(self):
        """The leads and opportunities the portal lists for the user: those
        assigned to their company (website_crm_partner_assign)."""
        return [('type', 'in', ('lead', 'opportunity')),
                ('partner_assigned_id', 'child_of', self.env.user.commercial_partner_id.id)]

    def _wpn_portal_url(self):
        """website_crm_partner_assign's pages for the leads and opportunities
        assigned to the customer's company; its access rules decide."""
        self.ensure_one()
        if self.type in ('lead', 'opportunity') and self.has_access('read'):
            return ('/my/opportunity/%d' if self.type == 'opportunity' else '/my/lead/%d') % self.id
        return super()._wpn_portal_url()
