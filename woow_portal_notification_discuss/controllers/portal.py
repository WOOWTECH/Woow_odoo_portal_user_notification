from odoo import _
from odoo.http import request

from odoo.addons.woow_portal_notification.controllers.portal import PortalNotificationCenter

DISCUSSIONS_URL = '/my/discussions'


class PortalNotificationDiscuss(PortalNotificationCenter):

    def _wpn_extra_entries(self):
        entries = super()._wpn_extra_entries()
        members = request.env['discuss.channel.member'].sudo().search([
            ('partner_id', '=', request.env.user.partner_id.id),
            ('channel_id.channel_type', 'in', ['chat', 'group', 'channel']),
        ])
        unread = sum(members.mapped('message_unread_counter'))
        if unread:
            entries.append({
                'icon': 'fa-comments-o',
                'title': _('Unread conversations'),
                'text': _('%(count)s unread messages in Discussions', count=unread),
                'url': DISCUSSIONS_URL,
            })
        return entries
