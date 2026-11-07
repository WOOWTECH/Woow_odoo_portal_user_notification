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
| `woow_portal_notification_subscription` | Subscription notifications open the subscription list of the `/woow` app, for the `woow_subscription` engine | `woow_portal_notification`, `woow_subscription` |
| `woow_portal_notification_crm` | Notifications about assigned leads and opportunities open `/my/lead/<id>` or `/my/opportunity/<id>` | `woow_portal_notification`, `website_crm_partner_assign` |
| `woow_portal_notification_loyalty` | Gift card and eWallet notifications open `/my/loyalty_card/<id>/history` | `woow_portal_notification`, `loyalty` |
| `woow_portal_notification_project` | For internal users, only projects and tasks shared on the portal count | `woow_portal_notification`, `project` |
| `woow_portal_notification_hr_expense` | Expense and expense report notifications open the office assistant's `/my/expenses/<id>` | `woow_portal_notification`, `woow_hr_portal_expense` |
| `woow_portal_notification_hr_leave` | Time off notifications open `/my/leaves/<id>` | `woow_portal_notification`, `woow_hr_portal_leave` |
| `woow_portal_notification_hr_attendance` | Attendance notifications open `/my/attendance/<id>` | `woow_portal_notification`, `woow_hr_portal_attendance` |
| `woow_subscription_legacy_urls` | The addresses of the old subscription pages (`/my/sh_subscription…`) move permanently to the same subscription list. Not a bridge | `web` |

The bridges install automatically when their two dependencies are present.
`woow_subscription_legacy_urls` is the exception: it is installed by hand and
only for a while (see *Subscription modules* below).

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

## Subscription modules

Two modules go with `woow_subscription`, the WOOW subscription engine that
takes over from `sh_subscription`. The engine is a separate module and not part
of this repository. It has no portal pages: customers see their subscriptions
in the `/woow` app, which routes in the browser (the part of the address after
`#`) and has one list of the customer's subscriptions, with no page per
subscription.

**`woow_portal_notification_subscription`** links the centre to the engine.
- A customer who opens a notification about one of their subscriptions lands on that list, `/woow#/billing/subscriptions`. Anyone else (a follower who is not the customer, say) gets the centre's default: no page, the message opens in a dialog.
- Portal users have no access rights on subscriptions, so the customer is compared with the user's contact as superuser. Only that field is read, and opening a notification never ends in a 403.
- For internal users the centre counts the subscriptions billed to their own contact (`_wpn_portal_record_domain`), the set their `/woow` list shows. It needs read access on subscriptions: without it the centre lists no subscription notification.
- Read-only: no data file, hook or scheduled action, and no override of `create` or `write`.
- Installed automatically when `woow_portal_notification` and `woow_subscription` are both present. Odoo does that when a module is installed, not on `-u all`: a database that already had the engine before this module reached it needs `-i woow_portal_notification_subscription`.

**`woow_subscription_legacy_urls`** is a temporary companion, not a bridge. The addresses of the old subscription pages live on in e-mails already sent and in bookmarks:

| Old address | Answer |
|---|---|
| `/my/sh_subscription`, `/my/sh_subscription/page/<n>`, `/my/sh_subscription/<id>` | `301`, `Location: /woow#/billing/subscriptions` |
| `/cancel-subscription`, `/renew-subscription` (JSON endpoints of the old module) | not redirected, `404` |
| any other address under `/my/sh_subscription/` | not redirected, `404` |

- GET and HEAD only (other methods get `405`); a trailing slash is accepted. Everyone is redirected, signed in or not: `/woow` asks for the sign-in itself. Nothing is looked up and no session is started or saved.
- The query string is dropped. `/woow` reads none of the old paging, sorting or `access_token` parameters, and a redirect has no business carrying a token any further.
- It is a small controller rather than `website.rewrite` records: it does not need `website`, it ships and is tested with the module, it covers the address of each subscription (a rewrite rule matches one exact path), and it answers in one hop without the query string.
- The old module serves these very addresses, so the manifest `excludes` it: Odoo refuses to install the two together, in either order, before anything is written. Install this module by hand once `sh_subscription` is uninstalled. It is in the category *Hidden* and never installs itself.
- It is meant to stay six months after the switch, then be removed.

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

The two subscription modules have their own tests.
`woow_portal_notification_subscription` needs `woow_subscription` on the addons
path, and this centre in version 18.0.1.2.0 or later (one of its tests relies on
the centre being on for all internal users, the default from that version on);
`woow_subscription_legacy_urls` needs only `web`:

```
odoo -d <db> -i woow_portal_notification_subscription,woow_subscription_legacy_urls \
     --test-enable \
     --test-tags woow_portal_notification_subscription,woow_subscription_legacy_urls \
     --stop-after-init
```

They run on a database with the dependencies only and on one with `website`
installed first.

## History

These modules replace `woow_portal_ui` (18.0.2.x). That module also restyled
every portal list and detail page and changed site-wide behaviour: login
redirect, forced language, hidden footer, fonts and colours. Its code is kept
in the git history (tag `archive/woow_portal_ui-18.0.2.2.3`) and on branch
`ux/portal-ui-sandbox-review-20261103` (18.0.2.3.0, never released).

## License

LGPL-3
