/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";

/**
 * Greeting on /my: the server renders the greeting for each part of the
 * day; pick the one matching the browser's clock (the customer's time zone
 * is often not set in Odoo).
 */
publicWidget.registry.WoowPortalGreeting = publicWidget.Widget.extend({
    selector: ".o_wpn_greeting",

    start() {
        const hour = new Date().getHours();
        const part = hour >= 5 && hour < 12 ? "morning" : hour >= 12 && hour < 18 ? "afternoon" : "evening";
        const text = this.el.dataset[part];
        if (text) {
            this.el.textContent = text;
        }
        // back from a document: the browser shows /my from its back/forward
        // cache, with the counts of before; reload them
        this._onPageShow = (ev) => ev.persisted && window.location.reload();
        window.addEventListener("pageshow", this._onPageShow);
        return this._super(...arguments);
    },

    destroy() {
        window.removeEventListener("pageshow", this._onPageShow);
        this._super(...arguments);
    },
});

/**
 * Notification centre (Odoo's portal search bar and table): read / unread
 * switch per row, "Mark all as read", and the dialog showing the message of
 * a notification whose document has no page.
 */
publicWidget.registry.WoowPortalNotifications = publicWidget.Widget.extend({
    selector: ".o_wpn_page",
    events: {
        "click .o_wpn_toggle": "_onToggleClick",
        "click .o_wpn_read_all": "_onReadAllClick",
        "click a.o_wpn_title:not([data-bs-toggle])": "_onOpenClick",
    },

    start() {
        this.modalEl = this.el.querySelector("#o_wpn_modal");
        if (this.modalEl) {
            this._onShowModal = this._onShowModal.bind(this);
            this.modalEl.addEventListener("show.bs.modal", this._onShowModal);
        }
        // back from a document: the list comes from the back/forward cache,
        // as it was before the notification was read; reload it
        this._onPageShow = (ev) => ev.persisted && window.location.reload();
        window.addEventListener("pageshow", this._onPageShow);
        const openId = this.el.dataset.open;
        if (openId) {
            this.el.querySelector(`[data-bs-toggle="modal"][data-id="${openId}"]`)?.click();
        }
        return this._super(...arguments);
    },

    destroy() {
        this.modalEl?.removeEventListener("show.bs.modal", this._onShowModal);
        window.removeEventListener("pageshow", this._onPageShow);
        this._super(...arguments);
    },

    async _setRead(ids, read) {
        const result = await rpc("/my/notifications/read", { notification_ids: ids, read });
        for (const id of result.updated || []) {
            this.el.querySelector(`.o_wpn_item[data-id="${id}"]`)?.classList.toggle("o_wpn_unread", !read);
        }
        this._showUnreadCount(result.unread_count || 0);
    },

    _showUnreadCount(count) {
        // the counters in the user menu (next to the name and on the entry)
        for (const el of document.querySelectorAll(".o_wpn_unread_count")) {
            el.textContent = count;
            el.classList.toggle("d-none", !count);
        }
        this.el.querySelector(".o_wpn_read_all_wrap")?.classList.toggle("d-none", !count);
    },

    async _onToggleClick(ev) {
        ev.preventDefault();
        ev.stopPropagation();
        const item = ev.currentTarget.closest(".o_wpn_item");
        if (!item) {
            return;
        }
        const hadFocus = document.activeElement === ev.currentTarget;
        await this._setRead([parseInt(item.dataset.id, 10)], item.classList.contains("o_wpn_unread"));
        if (hadFocus) {
            // the other button of the pair is the visible one now
            item.querySelector(item.classList.contains("o_wpn_unread") ? ".o_wpn_when_unread" : ".o_wpn_when_read")?.focus();
        }
    },

    /**
     * The link goes through /my/notifications/<id>/open, which reads the
     * notification before showing the document: show the row read now,
     * while the document loads.
     */
    _onOpenClick(ev) {
        this._showRead(ev.currentTarget.closest(".o_wpn_item"));
    },

    _showRead(item) {
        if (item?.classList.contains("o_wpn_unread")) {
            item.classList.remove("o_wpn_unread");
            for (const el of document.querySelectorAll(".o_wpn_unread_count")) {
                const count = Math.max((parseInt(el.textContent, 10) || 0) - 1, 0);
                el.textContent = count;
                el.classList.toggle("d-none", !count);
            }
        }
    },

    async _onReadAllClick(ev) {
        ev.preventDefault();
        const button = ev.currentTarget;
        button.disabled = true;
        try {
            await rpc("/my/notifications/read_all", { search: button.dataset.search || "" });
        } finally {
            window.location.reload();
        }
    },

    _onShowModal(ev) {
        const id = ev.relatedTarget?.dataset.id;
        const source = id && this.el.querySelector(`.o_wpn_body_src[data-id="${id}"]`);
        if (!source) {
            return;
        }
        this.modalEl.querySelector(".modal-title").textContent = source.dataset.title || "";
        // server-rendered, sanitised message HTML kept in a <template>
        // (see portal_my_notifications): copy its nodes, never re-parse markup
        this.modalEl.querySelector(".o_wpn_modal_body").replaceChildren(source.content.cloneNode(true));
        const item = this.el.querySelector(`.o_wpn_item[data-id="${id}"]`);
        if (item?.classList.contains("o_wpn_unread")) {
            this._showRead(item);
            this._setRead([parseInt(id, 10)], true);
        }
    },
});
