import logging
from datetime import datetime

import pytz
from babel.dates import format_skeleton

from odoo import _, http
from odoo.fields import Datetime as FieldDatetime
from odoo.http import request
from odoo.tools import SQL, format_amount
from odoo.tools.mail import html_to_inner_content
from odoo.tools.misc import babel_locale_parse, format_date, format_datetime
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.portal.controllers.portal import pager as portal_pager

_logger = logging.getLogger(__name__)

PAGE_SIZE = 20
PREVIEW_CHARS = 140
SEARCH_CHARS = 100
# System parameter: "0" hides the notification cards on /my.
PARAM_HOME_SUMMARY = 'woow_portal_notification.home_summary'
# Internal users read their notifications in the backend Inbox.
BACKEND_INBOX = '/odoo/discuss'
# message types written by a person (a reply, an e-mail); the rest are
# system notifications (tracking, automatic messages, assignments)
_PEOPLE_TYPES = ('comment', 'email')


def _param_enabled(key):
    value = request.env['ir.config_parameter'].sudo().get_param(key, '1')
    return value not in ('0', 'False', 'false', '')


class PortalNotificationCenter(CustomerPortal):
    """Notification centre for portal customers, built from Odoo's own
    portal pieces: home cards and counters, the portal search bar, the
    portal table and pager."""

    # ------------------------------------------------------------------
    # Extension points
    # ------------------------------------------------------------------

    def _wpn_extra_entries(self):
        """Notices shown above the notification list for things that are not
        mail notifications (e.g. unread conversations).
        Each entry: {icon, text, url, link_label}."""
        return []

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    @staticmethod
    def _wpn_domain(partner, filterby='all', search=None):
        domain = [('res_partner_id', '=', partner.id)]
        if filterby == 'unread':
            domain.append(('is_read', '=', False))
        if search:
            # one subquery on this partner's messages
            domain.append(('mail_message_id', 'any', [
                '|', '|', '|',
                ('subject', 'ilike', search),
                ('record_name', 'ilike', search),
                ('body', 'ilike', search),
                ('author_id.name', 'ilike', search),
            ]))
        return domain

    @staticmethod
    def _wpn_search(domain, limit=None, offset=0):
        """Notifications matching the domain, newest message first.  Ordered
        on the message date, not on the notification id: imported or
        back-dated messages keep their place in time."""
        Notification = request.env['mail.notification'].sudo()
        query = Notification._search(domain)
        message = query.join(Notification._table, 'mail_message_id',
                             'mail_message', 'id', 'mail_message_id')
        query.order = SQL('%s DESC, %s DESC', SQL.identifier(message, 'date'),
                          SQL.identifier(Notification._table, 'id'))
        query.limit = limit
        query.offset = offset
        return Notification.browse(query.get_result_ids())

    @staticmethod
    def _wpn_mark_read(notifications, read=True):
        todo = notifications.filtered(lambda n: n.is_read != read)
        if todo:
            todo.write({
                'is_read': read,
                'read_date': FieldDatetime.now() if read else False,
            })
        return todo

    # ------------------------------------------------------------------
    # Display helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _wpn_user_tz():
        try:
            return pytz.timezone(request.env.user.tz or 'UTC')
        except pytz.UnknownTimeZoneError:
            return pytz.UTC

    def _wpn_local(self, dt):
        return pytz.UTC.localize(dt).astimezone(self._wpn_user_tz())

    def _wpn_local_datetime(self, dt):
        if not dt:
            return ''
        return format_datetime(request.env, dt, tz=self._wpn_user_tz().zone,
                               dt_format='short')

    def _wpn_format_tracking_value(self, value, field_type, currency_id=None):
        """One side of a tracked change, readable whatever the field type."""
        if value is None or (value is False and field_type != 'boolean'):
            return ''
        if field_type == 'boolean':
            return _('Yes') if value else _('No')
        if field_type == 'datetime':
            try:
                dt = datetime.strptime(str(value).rstrip('Z')[:19],
                                       '%Y-%m-%d %H:%M:%S')
            except ValueError:
                return str(value)
            return self._wpn_local_datetime(dt)
        if field_type == 'date':
            try:
                return format_date(request.env, str(value)[:10])
            except ValueError:
                return str(value)
        if field_type == 'monetary' and currency_id:
            currency = request.env['res.currency'].sudo().browse(currency_id)
            if currency.exists():
                return format_amount(request.env, value or 0.0, currency)
        if field_type in ('float', 'monetary'):
            return ('%.2f' % value).rstrip('0').rstrip('.') if value else '0'
        return str(value)

    def _wpn_tracking_rows(self, message):
        """[{field, old, new}] of a message's tracked changes, without the
        fields the reader has no access to (same rule as the chatter)."""
        tracking = message.sudo().tracking_value_ids
        if not tracking:
            return []
        try:
            visible = tracking._filter_has_field_access(request.env)
            formatted = visible._tracking_value_format()
        except Exception:  # noqa: BLE001 - tracked model uninstalled, etc.
            _logger.debug('tracking values of message %s not shown', message.id,
                          exc_info=True)
            return []
        rows = []
        for info in formatted:
            ftype = info.get('fieldType') or 'char'
            old = info.get('oldValue') or {}
            new = info.get('newValue') or {}
            rows.append({
                'field': info.get('changedField') or '',
                'old': self._wpn_format_tracking_value(
                    old.get('value'), ftype, old.get('currencyId')),
                'new': self._wpn_format_tracking_value(
                    new.get('value'), ftype, new.get('currencyId')),
            })
        return rows

    @staticmethod
    def _wpn_tracking_summary(rows):
        parts = []
        for row in rows:
            if row['old'] and row['new']:
                parts.append('%s: %s → %s' % (row['field'], row['old'], row['new']))
            elif row['new']:
                parts.append('%s: %s' % (row['field'], row['new']))
            elif row['old']:
                parts.append('%s: %s → —' % (row['field'], row['old']))
        return '; '.join(parts)

    def _wpn_document_url(self, message):
        """The customer's page for the message's document, or False."""
        if not message.model or not message.res_id or message.model not in request.env:
            return False
        record = request.env[message.model].browse(message.res_id)
        if not hasattr(record, '_wpn_portal_url'):
            return False
        try:
            record = record.exists()
            return record._wpn_portal_url() if record else False
        except Exception:  # noqa: BLE001 - never break the list for one record
            _logger.debug('no portal URL for %s,%s', message.model, message.res_id,
                          exc_info=True)
            return False

    @staticmethod
    def _wpn_model_label(model, cache):
        if model not in cache:
            cache[model] = (request.env['ir.model']._get(model).name or '') if model else ''
        return cache[model]

    def _wpn_item(self, notification, cache, with_body=None):
        """Display values of one notification.  ``with_body``: True, False,
        or None for "only when the document has no page of its own" (the
        message is then shown in a dialog)."""
        message = notification.mail_message_id
        author = message.author_id
        if 'odoobot' not in cache:
            cache['odoobot'] = request.env.ref('base.partner_root', raise_if_not_found=False)
        is_person = (message.message_type in _PEOPLE_TYPES and bool(author)
                     and author != cache['odoobot'])
        title = message.subject or message.record_name or _('Notification')
        source = [self._wpn_model_label(message.model, cache)]
        if message.record_name and message.record_name != title:
            source.append(message.record_name)
        rows = self._wpn_tracking_rows(message)
        preview = self._wpn_tracking_summary(rows) or html_to_inner_content(message.body or '')
        if not preview and message.subtype_id:
            preview = message.subtype_id.name or ''
        preview = ' '.join(preview.split())
        if len(preview) > PREVIEW_CHARS:
            preview = preview[:PREVIEW_CHARS].rstrip() + '…'
        url = self._wpn_document_url(message)
        if with_body is None:
            with_body = not url
        local = self._wpn_local(message.date) if message.date else None
        if local and 'locale' not in cache:
            cache['locale'] = babel_locale_parse(request.env.lang or 'en_US')
            cache['year'] = self._wpn_local(FieldDatetime.now()).year
        return {
            'id': notification.id,
            'is_read': notification.is_read,
            'is_person': is_person,
            'author': (author.name or '') if is_person else '',
            'title': title,
            'source': ' · '.join(part for part in source if part),
            'preview': preview,
            'day': format_date(request.env, local.date()) if local else '',
            # short form for phones: "11月3日" / "Nov 3", with the year when not this year
            'day_short': format_skeleton('MMMd' if local.year == cache['year'] else 'yMMMd',
                                         local, locale=cache['locale']) if local else '',
            'time': local.strftime('%H:%M') if local else '',
            'date': self._wpn_local_datetime(message.date),
            'url': url,
            'open_url': '/my/notifications/%d/open' % notification.id,
            'body': message.body if with_body else False,
            'tracking': rows if with_body else [],
        }

    def _wpn_greetings(self):
        """The greeting in each part of the day; the browser picks one with
        its own clock (the user's time zone is often not set)."""
        name = request.env.user.partner_id.name or request.env.user.name or ''
        return {
            'default': _('Hello, %s', name),
            'morning': _('Good morning, %s', name),
            'afternoon': _('Good afternoon, %s', name),
            'evening': _('Good evening, %s', name),
        }

    # ------------------------------------------------------------------
    # /my: greeting, and Odoo's own cards (counted like every other card)
    # ------------------------------------------------------------------

    @staticmethod
    def _wpn_no_store(response):
        """Unread counts and states change while the customer reads documents:
        make the back button fetch the page again instead of showing the copy
        the browser kept (HTTP cache, back/forward cache)."""
        response.headers['Cache-Control'] = 'no-store'
        return response

    @http.route()
    def home(self, **kw):
        response = super().home(**kw)
        if request.env.user._is_portal() and getattr(response, 'qcontext', None) is not None:
            response.qcontext['wpn_greetings'] = self._wpn_greetings()
            self._wpn_no_store(response)
        return response

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        wanted = {'wpn_unread_count', 'wpn_notification_count'} & set(counters or ())
        if wanted:
            user = request.env.user
            shown = user._is_portal() and _param_enabled(PARAM_HOME_SUMMARY)
            if 'wpn_unread_count' in wanted:
                values['wpn_unread_count'] = user._wpn_unread_count() if shown else 0
            if 'wpn_notification_count' in wanted:
                values['wpn_notification_count'] = request.env['mail.notification'].sudo().search_count(
                    self._wpn_domain(user.partner_id)) if shown else 0
        return values

    # ------------------------------------------------------------------
    # Opening a document reads its notifications
    # ------------------------------------------------------------------

    def _get_page_view_values(self, document, access_token, values,
                              session_history, no_breadcrumbs, **kwargs):
        values = super()._get_page_view_values(
            document, access_token, values, session_history, no_breadcrumbs,
            **kwargs)
        user = request.env.user
        if document and len(document) == 1 and user._is_portal():
            self._wpn_mark_read(request.env['mail.notification'].sudo().search([
                ('res_partner_id', '=', user.partner_id.id),
                ('is_read', '=', False),
                ('mail_message_id.model', '=', document._name),
                ('mail_message_id.res_id', '=', document.id),
            ]))
        return values

    # ------------------------------------------------------------------
    # The notification centre
    # ------------------------------------------------------------------

    @http.route(['/my/notifications', '/my/notifications/page/<int:page>'],
                type='http', auth='user', website=True, methods=['GET'])
    def wpn_notifications(self, page=1, filterby='all', search=None, open=None, **kw):
        user = request.env.user
        if not user._is_portal():
            return request.redirect(BACKEND_INBOX)
        partner = user.partner_id
        filterby = filterby if filterby in ('all', 'unread') else 'all'
        search = (search or '').strip()[:SEARCH_CHARS]
        Notification = request.env['mail.notification'].sudo()
        domain = self._wpn_domain(partner, filterby, search)
        url_args = {}
        if filterby != 'all':
            url_args['filterby'] = filterby
        if search:
            url_args['search'] = search
        pager = portal_pager(url='/my/notifications', url_args=url_args,
                             total=Notification.search_count(domain),
                             page=page, step=PAGE_SIZE)
        notifications = self._wpn_search(domain, limit=PAGE_SIZE, offset=pager['offset'])
        cache = {}
        items = [self._wpn_item(n, cache) for n in notifications]

        # ?open=<id>: show that notification's message on arrival (one whose
        # document has no customer page)
        modal_items = [item for item in items if not item['url']]
        open_id = False
        try:
            wanted = int(open or 0)
        except ValueError:
            wanted = 0
        if wanted:
            target = Notification.browse(wanted).exists()
            if target and target.res_partner_id == partner:
                open_id = target.id
                if open_id not in {item['id'] for item in modal_items}:
                    modal_items.append(self._wpn_item(target, cache, with_body=True))

        unread_count = user._wpn_unread_count()
        values = self._prepare_portal_layout_values()
        values.update({
            'page_name': 'wpn_notifications',
            'default_url': '/my/notifications',
            # Odoo's portal search bar
            'searchbar_filters': {
                'all': {'label': _('All')},
                'unread': {'label': _('Unread (%s)', unread_count)},
            },
            'filterby': filterby,
            'searchbar_inputs': {
                'all': {'input': 'all', 'label': _('Search in notifications')},
            },
            'search_in': 'all',
            'search': search,
            'pager': pager,
            'items': items,
            'modal_items': modal_items,
            'open_id': open_id,
            'unread_count': unread_count,
            'extras': self._wpn_extra_entries(),
        })
        return self._wpn_no_store(
            request.render('woow_portal_notification.portal_my_notifications', values))

    @http.route('/my/notifications/<int:notification_id>/open', type='http',
                auth='user', website=True, methods=['GET'])
    def wpn_open(self, notification_id, **kw):
        """Read the notification and go to its document, or show the message
        in the centre when the document has no page of its own."""
        user = request.env.user
        if not user._is_portal():
            return request.redirect(BACKEND_INBOX)
        notification = request.env['mail.notification'].sudo().browse(notification_id).exists()
        if not notification or notification.res_partner_id != user.partner_id:
            return request.redirect('/my/notifications')
        self._wpn_mark_read(notification)
        url = self._wpn_document_url(notification.mail_message_id)
        return request.redirect(url or '/my/notifications?open=%d' % notification.id)

    @http.route('/my/notifications/read', type='json', auth='user', methods=['POST'])
    def wpn_read(self, notification_ids=None, read=True, **kw):
        """Mark the given notifications of the signed-in customer read or
        unread.  Returns the ids changed and the new unread count."""
        user = request.env.user
        if not user._is_portal():
            return {'updated': [], 'unread_count': 0}
        if not isinstance(notification_ids, (list, tuple)):
            notification_ids = [notification_ids]
        ids = []
        for value in notification_ids[:200]:
            try:
                ids.append(int(value))
            except (TypeError, ValueError):
                continue
        notifications = request.env['mail.notification'].sudo().search([
            ('id', 'in', ids), ('res_partner_id', '=', user.partner_id.id)])
        self._wpn_mark_read(notifications, bool(read))
        return {'updated': notifications.ids, 'unread_count': user._wpn_unread_count()}

    @http.route('/my/notifications/read_all', type='json', auth='user', methods=['POST'])
    def wpn_read_all(self, search=None, **kw):
        """Mark every unread notification read, limited to the search the
        list is showing."""
        user = request.env.user
        if not user._is_portal():
            return {'updated': 0, 'unread_count': 0}
        search = (search or '').strip()[:SEARCH_CHARS]
        notifications = request.env['mail.notification'].sudo().search(
            self._wpn_domain(user.partner_id, 'unread', search))
        self._wpn_mark_read(notifications)
        return {'updated': len(notifications), 'unread_count': user._wpn_unread_count()}
