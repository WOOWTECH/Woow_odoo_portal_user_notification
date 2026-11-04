{
    "name": "Portal Notification Centre - Projects",
    "version": "18.0.1.0.0",
    "category": "Website",
    "summary": "Only projects and tasks shared on the portal count for internal users of the centre",
    "description": """
Internal users of the portal notification centre see the notifications about
the projects and tasks their portal shows: those of projects shared with
portal users ("Invited portal users and all internal users"), not of internal
projects.  Their portal pages (/my/projects/<id>, /my/tasks/<id>) come from
Odoo.  Installed automatically when both modules are present.
    """,
    "author": "Woow Tech",
    "website": "https://www.woow.tw",
    "license": "LGPL-3",
    "depends": ["woow_portal_notification", "project"],
    "data": [],
    "installable": True,
    "auto_install": True,
}
