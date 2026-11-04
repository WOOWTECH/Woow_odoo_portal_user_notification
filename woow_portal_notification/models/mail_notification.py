from odoo import api, models
from odoo.osv import expression

from .res_users import GROUP_INTERNAL

# System parameter: "0" keeps Odoo's default (e-mail notifications are
# created already read).
PARAM_PORTAL_UNREAD = 'woow_portal_notification.portal_unread'


class MailNotification(models.Model):
    _inherit = 'mail.notification'

    @api.model_create_multi
    def create(self, vals_list):
        """Odoo creates e-mail notifications with ``is_read=True``: their
        reader has no Inbox (portal users) or chose "Handle by Emails".  The
        portal notification centre is an inbox, so keep them unread:

        - portal customers: all of them;
        - internal users of the centre's group: only those the centre shows
          them (public messages on records of their portal).  Their backend
          inbox shares the read state, so those appear there unread too;
          the rest stays as Odoo made it.
        """
        enabled = None
        candidates = {
            vals['res_partner_id'] for vals in vals_list
            if vals.get('notification_type') == 'email'
            and vals.get('is_read') and vals.get('res_partner_id')
        }
        members = self.env['res.users']
        if candidates:
            enabled = self._wpn_portal_unread_enabled()
        if candidates and enabled:
            portal_ids, members = self._wpn_centre_partners(candidates)
            for vals in vals_list:
                if (vals.get('notification_type') == 'email'
                        and vals.get('res_partner_id') in portal_ids):
                    vals['is_read'] = False
        records = super().create(vals_list)
        for user in members:
            emailed = records.filtered(
                lambda n: n.res_partner_id == user.partner_id
                and n.notification_type == 'email' and n.is_read)
            if emailed:
                self.sudo().search(expression.AND([
                    [('id', 'in', emailed.ids)], user._wpn_portal_scope_domain(),
                ])).write({'is_read': False})
        return records

    @api.model
    def _wpn_portal_unread_enabled(self):
        value = self.env['ir.config_parameter'].sudo().get_param(
            PARAM_PORTAL_UNREAD, '1')
        return value not in ('0', 'False', 'false', '')

    @api.model
    def _wpn_centre_partners(self, partner_ids):
        """(partners whose active users are all portal users,
            internal users of the centre's group among those partners)"""
        users = self.env['res.users'].sudo().search(
            [('partner_id', 'in', list(partner_ids))])
        portal = set(users.filtered(lambda u: u._is_portal()).partner_id.ids)
        internal_users = users.filtered(lambda u: not u.share)
        internal = set(internal_users.partner_id.ids)
        members = internal_users.filtered(lambda u: u.has_group(GROUP_INTERNAL))
        return portal - internal, members
