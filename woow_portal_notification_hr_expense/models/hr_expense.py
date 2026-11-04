from odoo import api, models


def _portal_employee(env):
    """The employee whose office assistant pages the current user sees."""
    return env['hr.employee'].sudo()._get_portal_employee(env.user)


class HrExpense(models.Model):
    _inherit = 'hr.expense'

    @api.model
    def _wpn_portal_record_domain(self):
        employee = _portal_employee(self.env)
        return [('employee_id', '=', employee.id)] if employee else None

    def _wpn_portal_url(self):
        """The office assistant's expense page.  It lets the employee in by
        comparing employees, not through access rights, so check the same."""
        self.ensure_one()
        employee = _portal_employee(self.env)
        if employee and self.sudo().employee_id == employee:
            return '/my/expenses/%d' % self.id
        return super()._wpn_portal_url()


class HrExpenseSheet(models.Model):
    _inherit = 'hr.expense.sheet'

    @api.model
    def _wpn_portal_record_domain(self):
        employee = _portal_employee(self.env)
        return [('employee_id', '=', employee.id)] if employee else None

    def _wpn_portal_url(self):
        """A report has no page of its own: the page of its expense (the
        office assistant submits one expense per report), or the list."""
        self.ensure_one()
        employee = _portal_employee(self.env)
        sheet = self.sudo()
        if employee and sheet.employee_id == employee:
            expenses = sheet.expense_line_ids
            return '/my/expenses/%d' % expenses.id if len(expenses) == 1 else '/my/expenses'
        return super()._wpn_portal_url()
