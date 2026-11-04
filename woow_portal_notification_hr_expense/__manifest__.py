{
    "name": "Portal Notification Centre - Expenses",
    "version": "18.0.1.0.0",
    "category": "Website",
    "summary": "Expense notifications open the office assistant page of the expense",
    "description": """
Notifications about an expense or an expense report (woow_hr_portal_expense)
open the employee's expense page, /my/expenses/<id>, from the portal
notification centre.  Internal users of the centre see the notifications about their own expenses too.  Installed automatically when both modules are present.
    """,
    "author": "Woow Tech",
    "website": "https://www.woow.tw",
    "license": "LGPL-3",
    "depends": ["woow_portal_notification", "woow_hr_portal_expense"],
    "data": [],
    "installable": True,
    "auto_install": True,
}
