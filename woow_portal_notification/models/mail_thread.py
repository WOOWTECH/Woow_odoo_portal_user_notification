from odoo import api, models


class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    @api.model
    def _wpn_portal_record_domain(self):
        """Records of this model that the current user's portal shows them,
        as a domain, or None when the model has no portal page.

        Decides which notifications an internal user of the centre sees (a
        portal customer sees all of theirs).  Default: documents with a
        portal page (portal.mixin ``access_url``).  Modules whose records
        have another portal page, or whose portal shows only some records,
        override this method together with _wpn_portal_url().
        Published website content (courses, events, ...) counts too, as it
        does for customers who follow it; contacts do not (customer records,
        not portal content)."""
        if 'access_url' in self._fields:
            return []
        if 'website_url' in self._fields and 'is_published' in self._fields and self._name != 'res.partner':
            return [('is_published', '=', True)]
        return None

    def _wpn_portal_url(self):
        """Page a portal customer opens from the notification centre for this
        record, or False when it has none (the centre then shows the message
        itself).  Called as the customer, so only pages they may read.

        Default: the portal page (portal.mixin ``access_url``), else the
        published website page (``website_url``).  Modules whose records have
        another customer page override this method."""
        self.ensure_one()
        if not self.has_access('read'):
            return False
        url = self['access_url'] if 'access_url' in self._fields else False
        if url and url != '#':
            return url
        if 'website_url' in self._fields:
            published = self['is_published'] if 'is_published' in self._fields else True
            url = self['website_url']
            if published and url and url != '#':
                return url
        return False
