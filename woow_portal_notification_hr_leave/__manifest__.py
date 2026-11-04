{
    "name": "Portal Notification Centre - Time Off",
    "version": "18.0.1.0.0",
    "category": "Website",
    "summary": "Time off notifications open the office assistant page of the request",
    "description": """
Notifications about a time off request (woow_hr_portal_leave) open the
employee's request page, /my/leaves/<id>, from the portal notification
centre.  Internal users of the centre see the notifications about their own time off requests too.  Installed automatically when both modules are present.
    """,
    "author": "Woow Tech",
    "website": "https://www.woow.tw",
    "license": "LGPL-3",
    "depends": ["woow_portal_notification", "woow_hr_portal_leave"],
    "data": [],
    "installable": True,
    "auto_install": True,
}
