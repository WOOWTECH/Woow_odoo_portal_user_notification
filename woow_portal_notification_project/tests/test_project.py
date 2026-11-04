from markupsafe import Markup

from odoo import Command
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
class TestProjectScope(HttpCase):

    def _notif(self, message, user):
        return self.env['mail.notification'].search([
            ('mail_message_id', '=', message.id), ('res_partner_id', '=', user.partner_id.id)])

    def test_internal_member_sees_shared_projects_only(self):
        member = _member(self.env, 'wpn_pj_staff', 'Wpn Project Staff', 'inbox', ['project.group_project_user'])
        shared = self.env['project.project'].create({'name': 'Wpn shared', 'privacy_visibility': 'portal'})
        internal = self.env['project.project'].create({'name': 'Wpn internal', 'privacy_visibility': 'followers'})
        task = self.env['project.task'].create({'name': 'Wpn shared task', 'project_id': shared.id})
        internal_task = self.env['project.task'].create({'name': 'Wpn internal task', 'project_id': internal.id})
        for record in (task, internal_task):
            record.message_subscribe([member.partner_id.id])
        public = _post(task, '<p>wpn-shared-msg</p>')
        _post(internal_task, '<p>wpn-internal-project-msg</p>')
        note = _post(task, '<p>wpn-task-note</p>', note_for=member)

        self.authenticate('wpn_pj_staff', 'wpn_pj_staff_pw!')
        html = self.url_open('/my/notifications').text
        self.assertIn('wpn-shared-msg', html)
        self.assertNotIn('wpn-internal-project-msg', html, "an internal project is not on the portal")
        self.assertNotIn('wpn-task-note', html, "internal notes stay in the backend inbox")
        response = self.url_open('/my/notifications/%d/open' % self._notif(public, member).id, allow_redirects=False)
        self.assertIn('/my/tasks/%d' % task.id, response.headers['Location'])

        # opening the task page reads its public notifications only
        second = self._notif(_post(task, '<p>wpn-shared-second</p>'), member)
        self.assertFalse(second.is_read)
        self.assertEqual(self.url_open('/my/tasks/%d' % task.id).status_code, 200)
        self.env.invalidate_all()
        self.assertTrue(second.is_read)
        self.assertFalse(self._notif(note, member).is_read, "the backend inbox keeps the note unread")
