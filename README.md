# Woow Portal Notification Centre (Odoo 18)

An inbox for portal customers. Odoo e-mails customers about their orders,
invoices and projects, but the portal has no place where they can see those
notifications. These modules add that place and nothing else: Odoo's own
portal pages, cards and layout stay as they are.

[中文說明](README_zh-TW.md)

## Modules

| Module | What it does | Depends on |
|---|---|---|
| `woow_portal_notification` | Unread notifications for portal users, greeting and summary on `/my`, the `/my/notifications` page, user-menu entry and unread dot | `portal`, `mail` |
| `woow_portal_notification_discuss` | "Unread conversations" line for `woow_odoo_portal_discuss`. Installed automatically when both are present | `woow_portal_notification`, `woow_odoo_portal_discuss` |

## What a portal customer sees

**`/my`**
- A greeting in Odoo's header row, for example "Good afternoon, Daming Wang". The browser's clock picks the part of the day, so it is right even when the user has no time zone set.
- A summary card above Odoo's cards: the unread count, the three latest unread notifications and "View all". When nothing is unread it is one line, "No new notifications".

**`/my/notifications`**
- One list, newest first, with an All / Unread switch, search, and 20 notifications per page. Unread notifications are marked.
- A notification opens its document and becomes read. When the document has no customer page (a contact card, a calendar event), the message opens in a dialog instead.
- Each notification can be switched between read and unread. "Mark all as read" applies to the current search.

**On every website page**
- The user menu has a "Notifications" entry with the unread count, and the avatar shows a dot.

**Everywhere in the portal**
- Opening a document reads the notifications about it.

Internal users are not served. `/my/notifications` sends them to the backend
Inbox, and `/my` stays as Odoo renders it for them.

## How it works

- **Unread for portal users.** Odoo creates a portal user's e-mail notifications already read, because portal users have no Inbox. `mail.notification.create` keeps them unread for partners whose users are all portal users. Internal users keep Odoo's behaviour.
- **Document links.** `mail.thread._wpn_portal_url()` returns, in this order:
  1. the portal page (`access_url` of `portal.mixin`);
  2. the published website page (`website_url`);
  3. `False`, and the message is then shown in a dialog.

  It is evaluated as the customer, so only pages they can read are linked. A module whose records have another customer page overrides this method.
- **Extra lines** above the notifications come from `PortalNotificationCenter._wpn_extra_entries()`. The discussions bridge uses it.
- **Look.** Only Bootstrap SCSS variables and utility classes are used, so the pages follow the website theme. No fonts or brand colours are loaded.
- **Schema.** Nothing is added to the database schema. Uninstalling leaves Odoo's tables as they were.

## Settings

System parameters (Settings > Technical > System Parameters). Set a value to
`0` to turn a feature off.

| Key | Default | Effect |
|---|---|---|
| `woow_portal_notification.portal_unread` | `1` | Keep portal users' new notifications unread |
| `woow_portal_notification.home_summary` | `1` | Show the notification summary on `/my` |

## Tests

```
odoo -d <db> -i woow_portal_notification --test-enable \
     --test-tags /woow_portal_notification,/woow_portal_notification_discuss --stop-after-init
```

The suite runs both on a database with only `portal`, `mail` and this module,
and on one with `website`, `sale_management` and `woow_odoo_portal_discuss`.

## History

These modules replace `woow_portal_ui` (18.0.2.x). That module also restyled
every portal list and detail page and changed site-wide behaviour: login
redirect, forced language, hidden footer, fonts and colours. Its code is kept
in the git history (tag `archive/woow_portal_ui-18.0.2.2.3`) and on branch
`ux/portal-ui-sandbox-review-20261103` (18.0.2.3.0, never released).

## License

LGPL-3
