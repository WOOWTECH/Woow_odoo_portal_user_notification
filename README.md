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
| `woow_portal_notification_discuss` | "Unread conversations" card and notice for `woow_odoo_portal_discuss` | `woow_portal_notification`, `woow_odoo_portal_discuss` |
| `woow_portal_notification_sh_subscription` | Subscription notifications open `/my/sh_subscription/<id>` | `woow_portal_notification`, `sh_subscription` |
| `woow_portal_notification_crm` | Notifications about assigned leads and opportunities open `/my/lead/<id>` or `/my/opportunity/<id>` | `woow_portal_notification`, `website_crm_partner_assign` |
| `woow_portal_notification_loyalty` | Gift card and eWallet notifications open `/my/loyalty_card/<id>/history` | `woow_portal_notification`, `loyalty` |
| `woow_portal_notification_project` | For internal users, only projects and tasks shared on the portal count | `woow_portal_notification`, `project` |
| `woow_portal_notification_hr_expense` | Expense and expense report notifications open the office assistant's `/my/expenses/<id>` | `woow_portal_notification`, `woow_hr_portal_expense` |
| `woow_portal_notification_hr_leave` | Time off notifications open `/my/leaves/<id>` | `woow_portal_notification`, `woow_hr_portal_leave` |
| `woow_portal_notification_hr_attendance` | Attendance notifications open `/my/attendance/<id>` | `woow_portal_notification`, `woow_hr_portal_attendance` |

The bridges install automatically when their two dependencies are present.

## What a portal customer sees

Everything is built from Odoo's own portal pieces, so it looks like the rest
of the portal and follows the website theme.

**`/my`**
- A greeting in Odoo's header row, for example "Good afternoon, Daming Wang". The browser's clock picks the part of the day, so it is right even when the user has no time zone set.
- Odoo's alert card "N Unread notifications", next to "Quotations to review", and a "Notifications" card among Odoo's cards. Both are counted through `/my/counters` like every other card, and stay hidden when there is nothing to count.

**`/my/notifications`**
- Odoo's portal search bar (filter All / Unread, search) and portal table, like the orders or invoices list: newest message first, 20 per page, Odoo's pager. Unread notifications are bold with an "Unread" badge.
- A notification opens its document and becomes read. When the document has no customer page (a contact card, a calendar event), the message opens in a dialog instead.
- Each notification can be switched between read and unread. "Mark all as read" applies to the current search.

**On every website page**
- The user menu has a "Notifications" entry, and the unread count shows next to the name like the cart and wishlist counters.

**Everywhere in the portal**
- Opening a document reads the notifications about it.

Internal notes are not listed for a portal customer, including those left over from before the account was an internal one; notifications Odoo sends to the customer directly (such as follower invitations) are listed as usual.

## Internal users

All internal users get the centre by default (the system parameter
`woow_portal_notification.internal_users` below can limit it to the group
**Portal notification centre for internal users**, or turn it off). They see
what their portal shows them, not their backend Inbox:

- public messages only: internal notes, activities and assignments stay out;
- about documents of their portal: orders and invoices they follow, projects
  and tasks shared on the portal, their own expenses, time off and
  attendances (office assistant), published website content;
- the read state is the one of the backend Inbox: reading a notification in
  one place reads it in the other. For a user who handles notifications by
  e-mail, the new notifications the centre shows are kept unread, so they
  also appear in the backend Inbox; everything else stays as Odoo makes it.

Internal users without the centre are sent to the backend Inbox by
`/my/notifications`, and `/my` stays as Odoo renders it for them.

## How it works

- **Unread for portal users.** Odoo creates a portal user's e-mail notifications already read, because portal users have no Inbox. `mail.notification.create` keeps them unread for partners whose users are all portal users, and, for internal users of the group, keeps unread those the centre shows them.
- **Portal scope of internal users.** `res.users._wpn_notification_domain()` is what the centre shows. For an internal user it keeps public messages on records given by `mail.thread._wpn_portal_record_domain()`: every `portal.mixin` document, published website content, and what the bridges declare (shared projects, own expenses, time off, attendances, subscriptions, cards, assigned leads). Opening a document page reads only these notifications, so internal notes stay unread in the backend Inbox.
- **Document links.** `mail.thread._wpn_portal_url()` returns, in this order:
  1. the portal page (`access_url` of `portal.mixin`);
  2. the published website page (`website_url`);
  3. `False`, and the message is then shown in a dialog.

  It is evaluated as the user, so only pages they can read are linked. A module whose records have another page overrides this method; the subscription, assigned lead, loyalty and office assistant bridges do.
- **Notices** above the notification list come from `PortalNotificationCenter._wpn_extra_entries()`; home cards use Odoo's counters (`_prepare_home_portal_values`). The discussions bridge uses both.
- **Look.** Only Bootstrap SCSS variables and utility classes are used, so the pages follow the website theme. No fonts or brand colours are loaded.
- **Schema.** Nothing is added to the database schema. Uninstalling leaves Odoo's tables as they were.

## Settings

System parameters (Settings > Technical > System Parameters). Set a value to
`0` to turn a feature off.

| Key | Default | Effect |
|---|---|---|
| `woow_portal_notification.portal_unread` | `1` | Keep portal users' new notifications unread |
| `woow_portal_notification.home_summary` | `1` | Show the notification cards on `/my` |
| `woow_portal_notification.internal_users` | `1` | Internal users who get the centre: `1` all, `group` only the members of the group above, `0` none |

## Tests

```
odoo -d <db> -i woow_portal_notification --test-enable \
     --test-tags woow_portal_notification \
     --stop-after-init
```

The suite runs on a database with only `portal`, `mail` and this module; with
`website` installed first and this module after (the order of a live site);
with `woow_odoo_portal_discuss`; with `sh_subscription`,
`website_crm_partner_assign` and `loyalty`; and with `project` and the office
assistant (`woow_hr_portal_expense`, `woow_hr_portal_leave`,
`woow_hr_portal_attendance`).

## History

These modules replace `woow_portal_ui` (18.0.2.x). That module also restyled
every portal list and detail page and changed site-wide behaviour: login
redirect, forced language, hidden footer, fonts and colours. Its code is kept
in the git history (tag `archive/woow_portal_ui-18.0.2.2.3`) and on branch
`ux/portal-ui-sandbox-review-20261103` (18.0.2.3.0, never released).

## License

LGPL-3
