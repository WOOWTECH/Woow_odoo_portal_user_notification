from odoo import api, models


class HrLeave(models.Model):
    _inherit = 'hr.leave'

    @api.model
    def _wpn_portal_record_domain(self):
        employee = self.env['hr.employee'].sudo()._get_portal_employee(self.env.user)
        return [('employee_id', '=', employee.id)] if employee else None

    def _wpn_portal_url(self):
        """The office assistant's time off page.  It lets the employee in by
        comparing employees, not through access rights, so check the same."""
        self.ensure_one()
        employee = self.env['hr.employee'].sudo()._get_portal_employee(self.env.user)
        if employee and self.sudo().employee_id == employee:
            return '/my/leaves/%d' % self.id
        return super()._wpn_portal_url()
