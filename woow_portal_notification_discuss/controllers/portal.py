from odoo import _
from odoo.http import request

from odoo.addons.woow_portal_notification.controllers.portal import (
    PARAM_HOME_SUMMARY, PortalNotificationCenter, _param_enabled)

DISCUSSIONS_URL = '/my/discussions'


class PortalNotificationDiscuss(PortalNotificationCenter):

    def _wpn_unread_conversations(self):
        """Unread messages in the customer's conversations (direct messages,
        groups, channels): they create no mail notification."""
        members = request.env['discuss.channel.member'].sudo().search([
            ('partner_id', '=', request.env.user.partner_id.id),
            ('channel_id.channel_type', 'in', ['chat', 'group', 'channel']),
        ])
        return sum(members.mapped('message_unread_counter'))

    def _wpn_extra_entries(self):
        entries = super()._wpn_extra_entries()
        if not request.env.user._is_portal():
            # internal users of the centre have Discuss in the backend
            return entries
        unread = self._wpn_unread_conversations()
        if unread:
            entries.append({
                'icon': 'fa-comments-o',
                'text': _('%(count)s unread messages in Discussions', count=unread),
                'url': DISCUSSIONS_URL,
                'link_label': _('Open Discussions'),
            })
        return entries

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'wpn_unread_conversation_count' in (counters or ()):
            user = request.env.user
            shown = user._is_portal() and _param_enabled(PARAM_HOME_SUMMARY)
            values['wpn_unread_conversation_count'] = self._wpn_unread_conversations() if shown else 0
        return values
