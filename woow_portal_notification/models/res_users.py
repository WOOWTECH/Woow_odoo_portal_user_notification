from odoo import models
from odoo.exceptions import AccessError
from odoo.osv import expression
from odoo.tools import SQL

GROUP_INTERNAL = 'woow_portal_notification.group_internal_centre'


class ResUsers(models.Model):
    _inherit = 'res.users'

    def _wpn_uses_centre(self):
        """Portal customers, and the internal users of the group "Portal
        notification centre for internal users"."""
        self.ensure_one()
        if self._is_public():
            return False
        return self._is_portal() or self.has_group(GROUP_INTERNAL)

    def _wpn_notification_domain(self):
        """mail.notification domain of what the centre shows this user.

        A portal customer sees all their notifications: Odoo only notifies
        them of public messages.  An internal user sees the part their portal
        shows them too (see _wpn_portal_scope_domain), not their backend
        inbox."""
        self.ensure_one()
        domain = [('res_partner_id', '=', self.partner_id.id)]
        if self._is_portal():
            return domain
        return expression.AND([domain, self._wpn_portal_scope_domain()])

    def _wpn_portal_scope_domain(self):
        """Notifications of an internal user that belong in their portal:
        public messages (no internal note or internal subtype) on records the
        portal shows them, as each model declares with
        mail.thread._wpn_portal_record_domain()."""
        self.ensure_one()
        self.env.cr.execute(SQL(
            """SELECT DISTINCT m.model
                 FROM mail_notification n
                 JOIN mail_message m ON m.id = n.mail_message_id
                WHERE n.res_partner_id = %s AND m.model IS NOT NULL""",
            self.partner_id.id))
        clauses = []
        for (model_name,) in self.env.cr.fetchall():
            if model_name not in self.env or not hasattr(self.env[model_name], '_wpn_portal_record_domain'):
                continue
            Model = self.env[model_name].with_user(self)
            record_domain = Model._wpn_portal_record_domain()
            if record_domain is None:
                continue
            try:
                records = Model._search(record_domain)
            except AccessError:
                continue
            clauses.append(['&', ('model', '=', model_name), ('res_id', 'in', records)])
        if not clauses:
            return expression.FALSE_DOMAIN
        return [('mail_message_id', 'any', expression.AND([
            [('is_internal', '=', False), '|', ('subtype_id', '=', False), ('subtype_id.internal', '=', False)],
            expression.OR(clauses),
        ]))]

    def _wpn_unread_count(self):
        """Unread notifications shown by the centre to this user (0 for
        anyone who does not use it).  Called from the user menu on every
        website page."""
        self.ensure_one()
        if not self._wpn_uses_centre():
            return 0
        return self.env['mail.notification'].sudo().search_count(
            expression.AND([self._wpn_notification_domain(), [('is_read', '=', False)]]))
