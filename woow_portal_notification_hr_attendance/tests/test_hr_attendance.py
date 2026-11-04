from datetime import timedelta

from markupsafe import Markup

from odoo import Command, fields
from odoo.tests import HttpCase, tagged


def _post(record, body, note_for=None):
    """A public message to the followers, or an internal note for one user."""
    if note_for:
        return record.message_post(body=Markup(body), message_type='comment', subtype_xmlid='mail.mt_note',
                                   partner_ids=[note_for.partner_id.id])
    return record.message_post(body=Markup(body), message_type='comment', subtype_xmlid='mail.mt_comment')


def _member(env, login, name, notification_type='email', extra_groups=()):
    groups = [env.ref('base.group_user'), env.ref('woow_portal_notification.group_internal_centre')]
    groups += [env.ref(xmlid) for xmlid in extra_groups]
    return env['res.users'].with_context(no_reset_password=True).create({
        'name': name, 'login': login, 'password': login + '_pw!', 'email': login + '@example.invalid',
        'notification_type': notification_type, 'groups_id': [Command.set([g.id for g in groups])]})


@tagged('post_install', '-at_install', 'woow_portal_notification')
class TestAttendanceLink(HttpCase):

    def _notif(self, message, user):
        return self.env['mail.notification'].search([
            ('mail_message_id', '=', message.id), ('res_partner_id', '=', user.partner_id.id)])

    def _open(self, login, notification):
        self.authenticate(login, login + '_pw!')
        return self.url_open('/my/notifications/%d/open' % notification.id, allow_redirects=False).headers['Location']

    def test_notifications_open_the_office_assistant(self):
        member = _member(self.env, 'wpn_at_staff', 'Wpn Attendance Staff')
        employee = self.env['hr.employee'].create({'name': 'Wpn Attendance Staff', 'user_id': member.id})
        other = self.env['hr.employee'].create({'name': 'Wpn Attendance Other'})
        mine = self._record(employee)
        theirs = self._record(other)
        for record in (mine, theirs):
            record.message_subscribe([member.partner_id.id])
        notif = self._notif(_post(mine, '<p>wpn-at-mine</p>'), member)
        self.assertFalse(notif.is_read, "handled by e-mail, kept unread for the centre")
        hidden = self._notif(_post(theirs, '<p>wpn-at-theirs</p>'), member)
        self.assertTrue(hidden.is_read, "not on their portal: as Odoo makes it")

        self.assertTrue(self._open('wpn_at_staff', notif).endswith('/my/attendance/%d' % mine.id))
        html = self.url_open('/my/notifications').text
        self.assertNotIn('wpn-at-theirs', html, "another employee's record is not on their portal")

        # a portal user who is an employee (linked by their contact) gets the page too
        portal = self.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Wpn Attendance Portal', 'login': 'wpn_at_portal', 'password': 'wpn_at_portal_pw!',
            'email': 'wpn_at_portal@example.invalid',
            'groups_id': [Command.set([self.env.ref('base.group_portal').id])]})
        portal_employee = self.env['hr.employee'].create({
            'name': 'Wpn Attendance Portal', 'work_contact_id': portal.partner_id.id})
        record = self._record(portal_employee)
        record.message_subscribe([portal.partner_id.id])
        portal_notif = self._notif(_post(record, '<p>wpn-at-portal</p>'), portal)
        self.assertTrue(self._open('wpn_at_portal', portal_notif).endswith('/my/attendance/%d' % record.id))

    def _record(self, employee):
        now = fields.Datetime.now()
        return self.env['hr.attendance'].create({
            'employee_id': employee.id, 'check_in': now - timedelta(hours=3), 'check_out': now - timedelta(hours=2)})
