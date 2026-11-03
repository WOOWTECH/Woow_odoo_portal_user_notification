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
        return this._super(...arguments);
    },
});

/**
 * Notification centre: read / unread switch, "Mark all as read", and the
 * dialog showing the message of a notification whose document has no page.
 */
publicWidget.registry.WoowPortalNotifications = publicWidget.Widget.extend({
    selector: ".o_wpn_page",
    events: {
        "click .o_wpn_toggle": "_onToggleClick",
        "click .o_wpn_read_all": "_onReadAllClick",
    },

    start() {
        this.modalEl = this.el.querySelector("#o_wpn_modal");
        if (this.modalEl) {
            this._onShowModal = this._onShowModal.bind(this);
            this.modalEl.addEventListener("show.bs.modal", this._onShowModal);
        }
        const openId = this.el.dataset.open;
        if (openId) {
            this.el.querySelector(`[data-bs-toggle="modal"][data-id="${openId}"]`)?.click();
        }
        return this._super(...arguments);
    },

    destroy() {
        this.modalEl?.removeEventListener("show.bs.modal", this._onShowModal);
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
        for (const el of document.querySelectorAll(".o_wpn_unread_count")) {
            el.textContent = count;
            el.classList.toggle("d-none", !count);
        }
        for (const el of document.querySelectorAll(".o_wpn_dot")) {
            el.classList.toggle("d-none", !count);
        }
        this.el.querySelector(".o_wpn_read_all")?.classList.toggle("d-none", !count);
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
        // server-rendered, sanitised message HTML (see portal_my_notifications)
        this.modalEl.querySelector(".o_wpn_modal_body").innerHTML = source.innerHTML;
        const item = this.el.querySelector(`.o_wpn_item[data-id="${id}"]`);
        if (item?.classList.contains("o_wpn_unread")) {
            this._setRead([parseInt(id, 10)], true);
        }
    },
});
