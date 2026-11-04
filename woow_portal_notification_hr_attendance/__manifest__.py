{
    "name": "Portal Notification Centre - Attendances",
    "version": "18.0.1.0.0",
    "category": "Website",
    "summary": "Attendance notifications open the office assistant page of the attendance",
    "description": """
Notifications about an attendance (woow_hr_portal_attendance) open the
employee's attendance page, /my/attendance/<id>, from the portal
notification centre.  Internal users of the centre see the notifications about their own attendances too.  Installed automatically when both modules are present.
    """,
    "author": "Woow Tech",
    "website": "https://www.woow.tw",
    "license": "LGPL-3",
    "depends": ["woow_portal_notification", "woow_hr_portal_attendance"],
    "data": [],
    "installable": True,
    "auto_install": True,
}
