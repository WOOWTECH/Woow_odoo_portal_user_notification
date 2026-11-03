from odoo import models


class ResUsers(models.Model):
    _inherit = 'res.users'

    def _wpn_unread_count(self):
        """Unread notifications of a portal customer (0 for anyone else).
        Called from the user menu on every website page."""
        self.ensure_one()
        if not self._is_portal():
            return 0
        return self.env['mail.notification'].sudo().search_count([
            ('res_partner_id', '=', self.partner_id.id),
            ('is_read', '=', False),
        ])
