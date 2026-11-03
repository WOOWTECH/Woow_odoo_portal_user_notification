from odoo import api, models

# System parameter: "0" keeps Odoo's default (portal users' e-mail
# notifications are created already read).
PARAM_PORTAL_UNREAD = 'woow_portal_notification.portal_unread'


class MailNotification(models.Model):
    _inherit = 'mail.notification'

    @api.model_create_multi
    def create(self, vals_list):
        """Portal users only ever get e-mail notifications, and Odoo creates
        those with ``is_read=True`` because they have no Inbox.  The portal
        notification centre is their inbox, so keep them unread there.
        Internal users are untouched."""
        candidates = {
            vals['res_partner_id'] for vals in vals_list
            if vals.get('notification_type') == 'email'
            and vals.get('is_read') and vals.get('res_partner_id')
        }
        if candidates and self._wpn_portal_unread_enabled():
            portal_ids = self._wpn_portal_only_partner_ids(candidates)
            for vals in vals_list:
                if (vals.get('notification_type') == 'email'
                        and vals.get('res_partner_id') in portal_ids):
                    vals['is_read'] = False
        return super().create(vals_list)

    @api.model
    def _wpn_portal_unread_enabled(self):
        value = self.env['ir.config_parameter'].sudo().get_param(
            PARAM_PORTAL_UNREAD, '1')
        return value not in ('0', 'False', 'false', '')

    @api.model
    def _wpn_portal_only_partner_ids(self, partner_ids):
        """Partners whose active users are all portal users."""
        users = self.env['res.users'].sudo().search(
            [('partner_id', 'in', list(partner_ids))])
        portal = set(users.filtered(lambda u: u._is_portal()).partner_id.ids)
        internal = set(users.filtered(lambda u: not u.share).partner_id.ids)
        return portal - internal
