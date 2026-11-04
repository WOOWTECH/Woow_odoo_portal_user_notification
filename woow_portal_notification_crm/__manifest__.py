{
    "name": "Portal Notification Centre - Assigned Leads",
    "version": "18.0.1.1.0",
    "category": "Website",
    "summary": "Notifications about assigned leads and opportunities open their portal page",
    "description": """
Notifications about a lead or an opportunity assigned to the customer's company
(website_crm_partner_assign) open /my/lead/<id> or /my/opportunity/<id> from the
portal notification centre.  Installed automatically when both modules are
present.
    """,
    "author": "Woow Tech",
    "website": "https://www.woow.tw",
    "license": "LGPL-3",
    "depends": ["woow_portal_notification", "website_crm_partner_assign"],
    "data": [],
    "installable": True,
    "auto_install": True,
}
