from odoo import models


class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'

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
