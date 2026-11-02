/** @odoo-module **/

/**
 * Woow Portal UI — Frontend JS
 *
 * Handles:
 *  - Module search filter (client-side) on portal home
 *  - Notification page: swipe to mark-as-read / done
 *  - Notification detail modal (click card → fetch detail → show modal)
 *  - Logo link rewrite → /my/home on portal pages
 *  - Hide zero-count module cards on portal home
 *  - Notification searchbar (filter/sort/group/search panel)
 *  - Read toggle buttons + mark all read
 */

import { whenReady } from "@odoo/owl";
import { _t, translationIsReady } from "@web/core/l10n/translation";

whenReady(async () => {
    await translationIsReady;
    initFixedBars();
    initSearchFilter();
    initNotificationPage();
    initNotificationModal();
    initReadToggleButtons();
    initMarkAllRead();
    hideEmptyModuleCards();
    initNotifSearchbar();
    initMobileFilterSegments();
    initQuotationActions();
    initProjectEditorModals();
    initFieldChooser();
    initTaskEditor();
    initSubtasks();
    rewriteLogoLink();
});

// ------------------------------------------------------------------
// ⓪ Scroll-based sticky bars — elements fix below navbar on scroll
// ------------------------------------------------------------------

function initFixedBars() {
    // No-op: sticky behaviour removed per design decision.
    // Search bar and notification top bar now scroll naturally with the page.
}

// ------------------------------------------------------------------
// ① Search filter — client-side module name filtering
// ------------------------------------------------------------------

function initSearchFilter() {
    const input = document.getElementById("wpu_module_search");
    if (!input) return;

    input.placeholder = _t("Search modules or notifications...");

    input.addEventListener("keyup", function () {
        const query = this.value.trim().toLowerCase();

        // Filter module cards
        const cards = document.querySelectorAll(
            "#wpu_module_grid .o_portal_index_card"
        );
        cards.forEach(function (card) {
            const text = card.textContent.toLowerCase();
            if (!query || text.indexOf(query) !== -1) {
                card.classList.remove("wpu-hidden");
            } else {
                card.classList.add("wpu-hidden");
            }
        });

        // Hide/show empty categories
        const categories = document.querySelectorAll(
            "#wpu_module_grid .o_portal_category"
        );
        categories.forEach(function (cat) {
            const visibleCards = cat.querySelectorAll(
                ".o_portal_index_card:not(.wpu-hidden)"
            );
            if (visibleCards.length === 0 && query) {
                cat.classList.add("wpu-hidden");
            } else {
                cat.classList.remove("wpu-hidden");
            }
        });

        // Filter notification preview items
        var notifItems = document.querySelectorAll(
            ".wpu-notification-preview .wpu-notification-item"
        );
        notifItems.forEach(function (item) {
            var text = item.textContent.toLowerCase();
            if (!query || text.indexOf(query) !== -1) {
                item.classList.remove("wpu-hidden");
            } else {
                item.classList.add("wpu-hidden");
            }
        });

        // Hide group headers if all items in that group are hidden
        var groupHeaders = document.querySelectorAll(
            ".wpu-notification-preview .wpu-preview-group-header"
        );
        groupHeaders.forEach(function (header) {
            var items = [];
            var sibling = header.nextElementSibling;
            while (sibling && !sibling.classList.contains("wpu-preview-group-header")) {
                if (sibling.classList.contains("wpu-notification-item")) {
                    items.push(sibling);
                }
                sibling = sibling.nextElementSibling;
            }
            var visibleItems = items.filter(function (it) {
                return !it.classList.contains("wpu-hidden");
            });
            if (visibleItems.length === 0 && query) {
                header.classList.add("wpu-hidden");
            } else {
                header.classList.remove("wpu-hidden");
            }
        });
    });
}

// ------------------------------------------------------------------
// ② Notification Page — swipe + click
// ------------------------------------------------------------------

const SWIPE_THRESHOLD = 100;
const SWIPE_MAX = 200;

function initNotificationPage() {
    const list = document.getElementById("wpu_notif_list");
    if (!list) return;

    const wrappers = list.querySelectorAll(".wpu-notif-card-wrapper");
    wrappers.forEach(function (wrapper) {
        setupSwipe(wrapper);
        setupCardClick(wrapper);
    });

    // Hide hint after first swipe
    let hintHidden = false;
    list.addEventListener("touchstart", function () {
        if (!hintHidden) {
            const hint = document.getElementById("wpu_swipe_hint");
            if (hint) {
                hint.style.transition = "opacity 0.3s";
                hint.style.opacity = "0";
                setTimeout(function () { hint.remove(); }, 300);
            }
            hintHidden = true;
        }
    }, { once: true });
}

function setupCardClick(wrapper) {
    const card = wrapper.querySelector(".wpu-notif-card");
    if (!card) return;

    let didSwipe = false;

    card.addEventListener("touchstart", function () {
        didSwipe = false;
    }, { passive: true });

    card.addEventListener("touchmove", function () {
        didSwipe = true;
    }, { passive: true });

    card.addEventListener("click", function () {
        if (didSwipe || wrapper.classList.contains("wpu-removing")) return;

        const itemType = wrapper.getAttribute("data-item-type");
        const params = {};
        if (itemType === "activity") {
            params.activity_id = wrapper.getAttribute("data-activity-id");
        } else {
            params.notification_id = wrapper.getAttribute("data-notif-id");
        }
        openDetailModal(params, wrapper);
    });
}

function setupSwipe(wrapper) {
    const card = wrapper.querySelector(".wpu-notif-card");
    if (!card) return;

    let startX = 0;
    let startY = 0;
    let currentX = 0;
    let swiping = false;
    let locked = false;

    card.addEventListener("touchstart", function (e) {
        if (wrapper.classList.contains("wpu-removing")) return;
        const touch = e.touches[0];
        startX = touch.clientX;
        startY = touch.clientY;
        currentX = 0;
        swiping = true;
        locked = false;
        card.style.transition = "none";
    }, { passive: true });

    card.addEventListener("touchmove", function (e) {
        if (!swiping) return;
        const touch = e.touches[0];
        let diffX = touch.clientX - startX;
        const diffY = touch.clientY - startY;

        if (!locked) {
            if (Math.abs(diffX) > 10 || Math.abs(diffY) > 10) {
                if (Math.abs(diffY) > Math.abs(diffX)) {
                    swiping = false;
                    card.style.transform = "";
                    return;
                }
                locked = true;
            }
        }

        if (diffX < 0) diffX = 0;
        currentX = Math.min(diffX, SWIPE_MAX);
        card.style.transform = "translateX(" + currentX + "px)";

        const progress = Math.min(currentX / SWIPE_THRESHOLD, 1);
        const bg = wrapper.querySelector(".wpu-notif-swipe-bg");
        if (bg) bg.style.opacity = progress;

        if (currentX > 10) e.preventDefault();
    }, { passive: false });

    card.addEventListener("touchend", function () {
        if (!swiping) return;
        swiping = false;

        if (currentX >= SWIPE_THRESHOLD) {
            handleSwipeAction(wrapper);
        } else {
            snapBack(wrapper);
        }
    });

    // Mouse drag for desktop testing
    card.addEventListener("mousedown", function (e) {
        if (wrapper.classList.contains("wpu-removing")) return;
        startX = e.clientX;
        currentX = 0;
        swiping = true;
        card.style.transition = "none";

        function onMouseMove(ev) {
            if (!swiping) return;
            const diffX = Math.max(0, ev.clientX - startX);
            currentX = Math.min(diffX, SWIPE_MAX);
            card.style.transform = "translateX(" + currentX + "px)";
            const progress = Math.min(currentX / SWIPE_THRESHOLD, 1);
            const bg = wrapper.querySelector(".wpu-notif-swipe-bg");
            if (bg) bg.style.opacity = progress;
        }

        function onMouseUp() {
            document.removeEventListener("mousemove", onMouseMove);
            document.removeEventListener("mouseup", onMouseUp);
            if (!swiping) return;
            swiping = false;
            if (currentX >= SWIPE_THRESHOLD) {
                handleSwipeAction(wrapper);
            } else {
                snapBack(wrapper);
            }
        }

        document.addEventListener("mousemove", onMouseMove);
        document.addEventListener("mouseup", onMouseUp);
    });
}

function snapBack(wrapper) {
    const card = wrapper.querySelector(".wpu-notif-card");
    if (card) {
        card.style.transition = "transform 0.2s ease";
        card.style.transform = "translateX(0)";
    }
    const bg = wrapper.querySelector(".wpu-notif-swipe-bg");
    if (bg) {
        bg.style.transition = "opacity 0.2s ease";
        bg.style.opacity = "0";
    }
}

function handleSwipeAction(wrapper) {
    const itemType = wrapper.getAttribute("data-item-type");
    wrapper.classList.add("wpu-removing");

    const card = wrapper.querySelector(".wpu-notif-card");
    if (card) {
        card.style.transition = "transform 0.3s ease";
        card.style.transform = "translateX(110%)";
    }

    if (itemType === "activity") {
        const activityId = wrapper.getAttribute("data-activity-id");
        jsonRpc("/my/notifications/action", {
            activity_id: activityId,
            action: "done",
        }).then(function (data) {
            collapseAndRemove(wrapper);
            if (data && data.success) {
                updateActivityBadge(data.activity_count);
                updateBadgeCounts(data.unread_message_count, data.unread_notification_count, data.activity_count);
            } else {
                console.error("Failed to mark activity as done:", data);
            }
        });
    } else {
        var isAlreadyRead = wrapper.classList.contains("wpu-notif-read");

        if (isAlreadyRead) {
            // Already read — dismiss permanently via API so it won't reappear
            var dismissId = wrapper.getAttribute("data-notif-id");
            jsonRpc("/my/notifications/action", {
                notification_id: dismissId,
                action: "dismiss",
            }).then(function (data) {
                if (data && data.success) {
                    collapseAndRemove(wrapper);
                } else {
                    console.error("Failed to dismiss:", data);
                    wrapper.classList.remove("wpu-removing");
                    snapBack(wrapper);
                }
            });
            return;
        }

        const notifId = wrapper.getAttribute("data-notif-id");
        jsonRpc("/my/notifications/action", {
            notification_id: notifId,
            action: "mark_read",
        }).then(function (data) {
            if (!data || !data.success) {
                console.error("Failed to mark as read:", data);
                wrapper.classList.remove("wpu-removing");
                snapBack(wrapper);
                return;
            }

            const currentTab = getCurrentTab();
            const wasUnread = wrapper.classList.contains("wpu-notif-unread");
            if (currentTab === "all" && wasUnread) {
                // First swipe on unread: mark read, snap back
                wrapper.classList.remove("wpu-removing", "wpu-notif-unread");
                wrapper.classList.add("wpu-notif-read");
                if (card) {
                    card.style.transition = "transform 0.2s ease";
                    card.style.transform = "translateX(0)";
                }
                const dot = wrapper.querySelector(".wpu-unread-dot");
                if (dot) dot.remove();
            } else {
                // Already read or non-all tab: dismiss card
                collapseAndRemove(wrapper);
            }

            updateBadgeCounts(data.unread_message_count, data.unread_notification_count);
            updateMarkAllReadBtn(data.unread_message_count + data.unread_notification_count);
        });
    }
}

function collapseAndRemove(wrapper) {
    wrapper.style.transition =
        "max-height 0.3s ease, opacity 0.3s ease, margin 0.3s ease, padding 0.3s ease";
    wrapper.style.maxHeight = "0";
    wrapper.style.opacity = "0";
    wrapper.style.marginBottom = "0";
    wrapper.style.overflow = "hidden";

    setTimeout(function () {
        wrapper.remove();
        checkEmptyState();
    }, 300);
}

function checkEmptyState() {
    const remaining = document.querySelectorAll(".wpu-notif-card-wrapper");
    if (remaining.length === 0) {
        const list = document.getElementById("wpu_notif_list");
        if (list) {
            list.innerHTML =
                '<div class="wpu-notif-empty text-center text-muted py-5">' +
                '<i class="fa fa-check-circle fa-3x mb-3 d-block" style="opacity: 0.3;"></i>' +
                '<p class="mb-0">' + _t("No notifications") + '</p></div>';
        }
    }
}

function getCurrentTab() {
    const activeTab = document.querySelector(".wpu-notif-tab.active");
    if (!activeTab) return "all";
    const href = activeTab.getAttribute("href") || "";
    if (href.indexOf("tab=message") !== -1) return "message";
    if (href.indexOf("tab=notification") !== -1) return "notification";
    if (href.indexOf("tab=activity") !== -1) return "activity";
    return "all";
}

function updateBadgeCounts(msgCount, notifCount, activityCount) {
    // Update Messages tab badge
    var msgBadges = document.querySelectorAll('[data-unread-badge="message"]');
    msgBadges.forEach(function (b) {
        if (msgCount > 0) {
            b.textContent = msgCount;
            b.style.display = "";
        } else {
            b.style.display = "none";
        }
    });

    // Update Notifications tab badge
    var notifBadges = document.querySelectorAll('[data-unread-badge="notification"]');
    notifBadges.forEach(function (b) {
        if (notifCount > 0) {
            b.textContent = notifCount;
            b.style.display = "";
        } else {
            b.style.display = "none";
        }
    });

    // Update "All" tab badge = unread messages + unread notifications + pending activities
    var allBadge = document.querySelector('[data-unread-badge="all"]');
    if (allBadge) {
        var actCount = activityCount;
        if (actCount === undefined) {
            var actBadge = document.querySelector("[data-activity-badge]");
            actCount = actBadge ? (parseInt(actBadge.textContent, 10) || 0) : 0;
        }
        var total = (msgCount || 0) + (notifCount || 0) + actCount;
        if (total > 0) {
            allBadge.textContent = total;
            allBadge.style.display = "";
        } else {
            allBadge.style.display = "none";
        }
    }
}

function updateActivityBadge(activityCount) {
    var badges = document.querySelectorAll("[data-activity-badge]");
    badges.forEach(function (b) {
        if (activityCount > 0) {
            b.textContent = activityCount;
            b.style.display = "";
        } else {
            b.style.display = "none";
        }
    });
}

// ------------------------------------------------------------------
// ②-B Read toggle button (per notification)
// ------------------------------------------------------------------

function initReadToggleButtons() {
    var dots = document.querySelectorAll(".wpu-unread-dot[data-notif-id]");
    dots.forEach(function (dot) {
        dot.style.cursor = "pointer";
        dot.addEventListener("click", function (e) {
            e.stopPropagation();
            var notifId = dot.getAttribute("data-notif-id");
            if (!notifId) return;

            var wrapper = dot.closest(".wpu-notif-card-wrapper");
            var isRead = wrapper && wrapper.classList.contains("wpu-notif-read");
            var action = isRead ? "mark_unread" : "mark_read";

            dot.style.pointerEvents = "none";
            dot.style.opacity = "0.5";

            jsonRpc("/my/notifications/action", {
                notification_id: notifId,
                action: action,
            }).then(function (data) {
                dot.style.pointerEvents = "";
                dot.style.opacity = "";
                if (!data || !data.success) return;

                if (action === "mark_read") {
                    dot.classList.add("d-none");
                    if (wrapper) {
                        wrapper.classList.remove("wpu-notif-unread");
                        wrapper.classList.add("wpu-notif-read");
                    }
                } else {
                    dot.classList.remove("d-none");
                    if (wrapper) {
                        wrapper.classList.remove("wpu-notif-read");
                        wrapper.classList.add("wpu-notif-unread");
                    }
                }
                updateBadgeCounts(data.unread_message_count, data.unread_notification_count);
                updateMarkAllReadBtn(data.unread_message_count + data.unread_notification_count);
            });
        });
    });
}

// ------------------------------------------------------------------
// ②-C Mark all as read
// ------------------------------------------------------------------

function initMarkAllRead() {
    var btn = document.getElementById("wpu_mark_all_read");
    if (!btn) return;

    btn.addEventListener("click", function () {
        btn.disabled = true;
        btn.innerHTML = '<i class="fa fa-spinner fa-spin me-1"></i>' + _t("Processing...");

        var currentTab = getCurrentTab();
        jsonRpc("/my/notifications/mark_all_read", { tab: currentTab }).then(function (data) {
            if (data && data.success) {
                // Only affect notification cards, not activity cards
                var wrappers = document.querySelectorAll(
                    ".wpu-notif-card-wrapper.wpu-notif-unread[data-item-type='notification']"
                );
                wrappers.forEach(function (w) {
                    w.classList.remove("wpu-notif-unread");
                    w.classList.add("wpu-notif-read");
                    var dot = w.querySelector(".wpu-unread-dot");
                    if (dot) {
                        dot.classList.add("d-none");
                    }
                });
                updateBadgeCounts(data.unread_message_count, data.unread_notification_count, data.activity_count);
                btn.innerHTML = '<i class="fa fa-check me-1"></i>' + _t("Completed");
                setTimeout(function () { btn.style.display = "none"; }, 1000);
            } else {
                btn.disabled = false;
                btn.innerHTML = '<i class="fa fa-check-double me-1"></i>' + _t("Mark all read");
            }
        });
    });
}

function updateMarkAllReadBtn(unreadCount) {
    var btn = document.getElementById("wpu_mark_all_read");
    if (!btn) return;
    if (unreadCount <= 0) {
        btn.style.display = "none";
    }
}

// ------------------------------------------------------------------
// ③ Detail Modal
// ------------------------------------------------------------------

function initNotificationModal() {
    const overlay = document.getElementById("wpu_notif_modal_overlay");
    if (!overlay) return;

    overlay.addEventListener("click", function (e) {
        if (e.target === overlay) closeDetailModal();
    });

    const closeBtn = document.getElementById("wpu_modal_close");
    if (closeBtn) {
        closeBtn.addEventListener("click", closeDetailModal);
    }

    document.addEventListener("keydown", function (e) {
        if (e.key === "Escape") closeDetailModal();
    });
}

function openDetailModal(params, wrapper) {
    const overlay = document.getElementById("wpu_notif_modal_overlay");
    if (!overlay) return;

    overlay._currentParams = params;
    overlay._currentWrapper = wrapper;

    const body = document.getElementById("wpu_modal_body");
    body.innerHTML =
        '<div class="text-center py-4">' +
        '<i class="fa fa-spinner fa-spin fa-2x"></i></div>';

    const title = document.getElementById("wpu_modal_title");
    title.textContent = _t("Loading...");

    const docLink = document.getElementById("wpu_modal_doc_link");
    const actionBtn = document.getElementById("wpu_modal_action_btn");
    docLink.style.display = "none";
    actionBtn.style.display = "none";

    overlay.style.display = "flex";

    jsonRpc("/my/notifications/detail", params).then(function (data) {
        if (!data || !data.success) {
            body.innerHTML = '<p class="text-danger">' + _t("Failed to load") + '</p>';
            title.textContent = _t("Error");
            return;
        }
        renderModalContent(data);
    });
}

function renderModalContent(data) {
    const title = document.getElementById("wpu_modal_title");
    const body = document.getElementById("wpu_modal_body");
    const docLink = document.getElementById("wpu_modal_doc_link");
    const actionBtn = document.getElementById("wpu_modal_action_btn");
    const overlay = document.getElementById("wpu_notif_modal_overlay");

    const detail = data.detail;

    if (data.type === "notification") {
        renderNotificationDetail(detail, title, body, docLink, actionBtn, overlay);
    } else if (data.type === "activity") {
        renderActivityDetail(detail, title, body, docLink, actionBtn, overlay);
    }
}

function renderNotificationDetail(detail, title, body, docLink, actionBtn, overlay) {
    title.textContent = detail.subject;

    let html = '';

    html += '<div class="wpu-modal-meta mb-3">';
    if (detail.author_avatar_url) {
        html += '<img src="' + escapeAttr(detail.author_avatar_url) +
            '" class="wpu-modal-avatar me-2" alt=""/>';
    }
    html += '<span class="fw-semibold">' +
        escapeHtml(detail.author_name) + '</span>';
    html += '<span class="text-muted ms-2">' +
        escapeHtml(detail.date) + '</span>';
    if (detail.subtype_name) {
        html += '<span class="badge bg-light text-dark ms-2">' +
            escapeHtml(detail.subtype_name) + '</span>';
    }
    html += '</div>';

    if (detail.record_name) {
        html += '<div class="mb-3 small text-muted">';
        html += '<i class="fa fa-file-o me-1"></i>';
        html += escapeHtml(detail.record_name);
        html += '</div>';
    }

    if (detail.tracking_details && detail.tracking_details.length > 0) {
        html += '<div class="wpu-modal-tracking mb-3">';
        html += '<h6 class="fw-semibold mb-2">' +
            '<i class="fa fa-exchange me-1"></i>' + _t("Change History") + '</h6>';
        html += '<table class="table table-sm table-bordered">';
        html += '<thead><tr><th>' + _t("Field") + '</th><th>' + _t("Old Value") + '</th>' +
            '<th>' + _t("New Value") + '</th></tr></thead><tbody>';
        detail.tracking_details.forEach(function (td) {
            html += '<tr><td>' + escapeHtml(td.field_name) +
                '</td><td>' + escapeHtml(td.old_value) +
                '</td><td><strong>' + escapeHtml(td.new_value) +
                '</strong></td></tr>';
        });
        html += '</tbody></table></div>';
    }

    if (detail.body) {
        html += '<div class="wpu-modal-body-content">' +
            detail.body + '</div>';
    }

    body.innerHTML = html;

    if (detail.document_url && detail.document_url !== '#') {
        docLink.href = detail.document_url;
        docLink.style.display = '';
    } else {
        docLink.style.display = 'none';
    }

    actionBtn.style.display = '';
    if (detail.is_read) {
        actionBtn.disabled = true;
        actionBtn.innerHTML = '<i class="fa fa-check me-1"></i>' + _t("Read");
    } else {
        actionBtn.disabled = false;
        actionBtn.innerHTML = '<i class="fa fa-check me-1"></i>' + _t("Mark as read");
    }

    actionBtn.onclick = function () {
        const notifId = overlay._currentParams.notification_id;
        if (!notifId) return;
        actionBtn.disabled = true;
        actionBtn.innerHTML =
            '<i class="fa fa-spinner fa-spin me-1"></i>' + _t("Processing...");

        jsonRpc("/my/notifications/action", {
            notification_id: notifId,
            action: "mark_read",
        }).then(function (result) {
            if (result && result.success) {
                actionBtn.innerHTML =
                    '<i class="fa fa-check me-1"></i>' + _t("Read");

                const wrapper = overlay._currentWrapper;
                if (wrapper) {
                    wrapper.classList.remove("wpu-notif-unread");
                    wrapper.classList.add("wpu-notif-read");
                    const dot = wrapper.querySelector(".wpu-unread-dot");
                    if (dot) dot.remove();
                }
                updateBadgeCounts(result.unread_message_count, result.unread_notification_count);
            } else {
                actionBtn.disabled = false;
                actionBtn.innerHTML =
                    '<i class="fa fa-check me-1"></i>' + _t("Mark as read");
            }
        });
    };
}

function renderActivityDetail(detail, title, body, docLink, actionBtn, overlay) {
    title.textContent = detail.summary;

    let html = '';

    if (detail.activity_type) {
        html += '<div class="mb-3">';
        html += '<span class="badge bg-light text-dark">';
        html += '<i class="fa ' + escapeAttr(detail.icon) +
            ' me-1"></i>';
        html += escapeHtml(detail.activity_type);
        html += '</span>';
        if (detail.date_deadline) {
            html += '<span class="text-muted ms-3">';
            html += '<i class="fa fa-calendar-o me-1"></i>';
            html += escapeHtml(detail.date_deadline);
            html += '</span>';
        }
        html += '</div>';
    }

    if (detail.res_name) {
        html += '<div class="mb-3 small text-muted">';
        html += '<i class="fa fa-file-o me-1"></i>';
        html += escapeHtml(detail.res_name);
        html += '</div>';
    }

    if (detail.note) {
        html += '<div class="wpu-modal-body-content">' +
            detail.note + '</div>';
    } else {
        html += '<div class="text-muted small">' + _t("No description") + '</div>';
    }

    body.innerHTML = html;

    if (detail.document_url && detail.document_url !== '#') {
        docLink.href = detail.document_url;
        docLink.style.display = '';
    } else {
        docLink.style.display = 'none';
    }

    actionBtn.style.display = '';
    if (detail.can_approve) {
        actionBtn.innerHTML = '<i class="fa fa-check me-1"></i>' + _t("Approve");
    } else {
        actionBtn.innerHTML = '<i class="fa fa-check me-1"></i>' + _t("Done");
    }
    actionBtn.disabled = false;

    actionBtn.onclick = function () {
        const activityId = overlay._currentParams.activity_id;
        if (!activityId) return;
        actionBtn.disabled = true;
        actionBtn.innerHTML =
            '<i class="fa fa-spinner fa-spin me-1"></i>' + _t("Processing...");

        const action = detail.can_approve ? "approve" : "done";
        jsonRpc("/my/notifications/action", {
            activity_id: activityId,
            action: action,
        }).then(function (result) {
            if (result && result.success) {
                actionBtn.innerHTML =
                    '<i class="fa fa-check me-1"></i>' + _t("Completed");

                const wrapper = overlay._currentWrapper;
                if (wrapper) {
                    collapseAndRemove(wrapper);
                }

                updateActivityBadge(result.activity_count);
                updateBadgeCounts(result.unread_message_count, result.unread_notification_count, result.activity_count);

                setTimeout(closeDetailModal, 500);
            } else {
                actionBtn.disabled = false;
                actionBtn.innerHTML =
                    '<i class="fa fa-check me-1"></i>' +
                    (detail.can_approve ? _t("Approve") : _t("Done"));
            }
        });
    };
}

function closeDetailModal() {
    const overlay = document.getElementById("wpu_notif_modal_overlay");
    if (overlay) {
        overlay.style.display = "none";
        overlay._currentParams = null;
        overlay._currentWrapper = null;
    }
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function escapeAttr(text) {
    if (!text) return '';
    return text.replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

// ------------------------------------------------------------------
// ④ Notification Searchbar — toggle, sort, filter, group, search
// ------------------------------------------------------------------

function initNotifSearchbar() {
    var toggle = document.getElementById("wpu_notif_searchbar_toggle");
    var panel = document.getElementById("wpu_notif_searchbar");
    if (!toggle || !panel) return;

    toggle.addEventListener("click", function () {
        panel.classList.toggle("nc-filter-open");
        toggle.classList.toggle("active");
    });

    var list = document.getElementById("wpu_notif_list");
    if (!list) return;

    // Store original server-rendered order for stable sort
    Array.from(list.querySelectorAll(".wpu-notif-card-wrapper")).forEach(function (card, i) {
        card.dataset.origIndex = i;
    });

    // Sort By
    var sortBtns = panel.querySelectorAll(".wpu-notif-sort-btn");
    sortBtns.forEach(function (btn) {
        btn.addEventListener("click", function () {
            sortBtns.forEach(function (b) { b.classList.remove("active"); });
            btn.classList.add("active");
            _applyNotifFilters(list, panel);
        });
    });

    // Filter By
    var filterBtns = panel.querySelectorAll(".wpu-notif-filter-btn");
    filterBtns.forEach(function (btn) {
        btn.addEventListener("click", function () {
            filterBtns.forEach(function (b) { b.classList.remove("active"); });
            btn.classList.add("active");
            _applyNotifFilters(list, panel);
        });
    });

    // Group By
    var groupBtns = panel.querySelectorAll(".wpu-notif-group-btn");
    groupBtns.forEach(function (btn) {
        btn.addEventListener("click", function () {
            groupBtns.forEach(function (b) { b.classList.remove("active"); });
            btn.classList.add("active");
            _applyNotifFilters(list, panel);
        });
    });

    // Search
    var searchInput = document.getElementById("wpu_notif_search_input");
    var searchBtn = document.getElementById("wpu_notif_search_btn");
    if (searchInput) {
        searchInput.addEventListener("keyup", function (e) {
            if (e.key === "Enter") _applyNotifFilters(list, panel);
            clearTimeout(searchInput._debounce);
            searchInput._debounce = setTimeout(function () {
                _applyNotifFilters(list, panel);
            }, 300);
        });
    }
    if (searchBtn) {
        searchBtn.addEventListener("click", function () {
            _applyNotifFilters(list, panel);
        });
    }
}

function _applyNotifFilters(list, panel) {
    var cards = list.querySelectorAll(".wpu-notif-card-wrapper");
    if (!cards.length) return;

    var sortBtn = panel.querySelector(".wpu-notif-sort-btn.active");
    var sortVal = sortBtn ? sortBtn.dataset.sort : "newest";

    var filterBtn = panel.querySelector(".wpu-notif-filter-btn.active");
    var filterVal = filterBtn ? filterBtn.dataset.filter : "all";

    var groupBtn = panel.querySelector(".wpu-notif-group-btn.active");
    var groupVal = groupBtn ? groupBtn.dataset.group : "none";

    var searchInput = document.getElementById("wpu_notif_search_input");
    var query = searchInput ? searchInput.value.trim().toLowerCase() : "";

    // Remove existing group headers
    var existingHeaders = list.querySelectorAll(".wpu-notif-group-header");
    existingHeaders.forEach(function (h) { h.remove(); });

    // Filter cards
    var visibleCards = [];
    cards.forEach(function (card) {
        var show = true;
        var isActivity = card.dataset.itemType === "activity";

        if (filterVal === "unread") {
            // Show unread notifications + all pending activities
            if (!isActivity && card.classList.contains("wpu-notif-read")) show = false;
        }
        if (filterVal === "read") {
            // Show only read notifications — activities are never "read"
            if (isActivity) show = false;
            else if (card.classList.contains("wpu-notif-unread")) show = false;
        }

        if (show && query) {
            var text = card.textContent.toLowerCase();
            if (text.indexOf(query) === -1) show = false;
        }

        if (show) {
            card.classList.remove("wpu-filter-hidden");
            visibleCards.push(card);
        } else {
            card.classList.add("wpu-filter-hidden");
        }
    });

    // Sort by stored original index (stable across filter/sort switches)
    if (sortVal === "oldest") {
        visibleCards.sort(function (a, b) {
            return Number(b.dataset.origIndex) - Number(a.dataset.origIndex);
        });
    } else {
        visibleCards.sort(function (a, b) {
            return Number(a.dataset.origIndex) - Number(b.dataset.origIndex);
        });
    }

    // Re-append: sorted visible cards first, then hidden cards
    visibleCards.forEach(function (card) { list.appendChild(card); });
    Array.from(cards).forEach(function (card) {
        if (card.classList.contains("wpu-filter-hidden")) {
            list.appendChild(card);
        }
    });

    // Group
    if (groupVal !== "none" && visibleCards.length > 0) {
        var groups = {};
        visibleCards.forEach(function (card) {
            var groupKey;
            if (groupVal === "type") {
                groupKey = card.dataset.itemType === "activity" ? _t("To-Do") : _t("Notifications");
            } else if (groupVal === "source") {
                var sourceEl = card.querySelector(".wpu-notif-card-source");
                groupKey = sourceEl ? sourceEl.textContent.trim() : _t("Other");
            } else {
                groupKey = _t("All");
            }
            if (!groups[groupKey]) groups[groupKey] = [];
            groups[groupKey].push(card);
        });

        var parent = visibleCards[0].parentNode;
        Object.keys(groups).forEach(function (key) {
            var header = document.createElement("div");
            header.className = "wpu-notif-group-header fw-bold small text-muted py-2 px-1 border-bottom";
            header.textContent = key;
            parent.insertBefore(header, groups[key][0]);
        });
    }
}

// ------------------------------------------------------------------
// ⑤ Hide module cards with 0 records
// ------------------------------------------------------------------

function hideEmptyModuleCards() {
    var grid = document.getElementById("wpu_module_grid");
    if (!grid) return;

    var attempts = 0;
    var maxAttempts = 50; // 50 * 200ms = 10s max wait
    var timer = setInterval(function () {
        attempts++;
        var spinner = grid.querySelector(".o_portal_doc_spinner");
        if (!spinner || attempts >= maxAttempts) {
            clearInterval(timer);
            setTimeout(function () { _doHideEmpty(grid); }, 100);
        }
    }, 200);
}

function _doHideEmpty(grid) {
    var cards = grid.querySelectorAll(".o_portal_index_card");
    cards.forEach(function (card) {
        var counterEl = card.querySelector("[data-placeholder_count]");
        if (!counterEl) return;

        var countText = (counterEl.textContent || "").trim();
        if (countText === "0" || countText === "") {
            card.classList.add("d-none");
        }
    });

    var categories = grid.querySelectorAll(".o_portal_category");
    categories.forEach(function (cat) {
        var visibleCards = cat.querySelectorAll(".o_portal_index_card:not(.d-none)");
        if (visibleCards.length === 0) {
            cat.classList.add("d-none");
        }
    });
}

// ------------------------------------------------------------------
// ⑥ Logo link rewrite — on portal pages, logo clicks go to /my/home
// ------------------------------------------------------------------

function rewriteLogoLink() {
    if (!window.location.pathname.startsWith('/my')) return;

    var logos = document.querySelectorAll('a.navbar-brand');
    logos.forEach(function (el) {
        el.setAttribute('href', '/my/home');
    });
}

// ------------------------------------------------------------------
// JSON-RPC helper
// ------------------------------------------------------------------

function jsonRpc(url, params) {
    return fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            jsonrpc: "2.0",
            method: "call",
            params: params || {},
        }),
    })
        .then(function (response) { return response.json(); })
        .then(function (data) {
            if (data.error) {
                console.error("JSON-RPC error:", data.error);
                return null;
            }
            return data.result;
        })
        .catch(function (err) {
            console.error("Fetch error:", err);
            return null;
        });
}

// ------------------------------------------------------------------
// Project editor modals (Add Task / Add Stage)
// ------------------------------------------------------------------

function initProjectEditorModals() {
    var btnTask = document.getElementById("btnSubmitTask");
    var btnStage = document.getElementById("btnSubmitStage");
    if (!btnTask && !btnStage) return;

    // Add scoped class for always-collapsed navbar on this page
    var mainContent = document.querySelector(".o_portal");
    if (mainContent) mainContent.classList.add("wt-collapsed-nav");

    // Move editor bar into the navbar (same line as toggle button)
    var editorBar = document.getElementById("wtEditorBar");
    var nav = document.querySelector(".o_portal_navbar");
    var toggler = nav && nav.querySelector(".navbar-toggler");
    if (editorBar && toggler) {
        toggler.parentNode.insertBefore(editorBar, toggler);
    }

    // Extract project ID from the current URL: /my/projects/<id>
    var match = window.location.pathname.match(/\/my\/projects\/(\d+)/);
    if (!match) return;
    var projectId = parseInt(match[1], 10);

    if (btnTask) {
        btnTask.addEventListener("click", function () {
            var nameInput = document.getElementById("taskName");
            var stageSelect = document.getElementById("taskStage");
            var name = nameInput ? nameInput.value.trim() : "";
            if (!name) {
                nameInput.focus();
                return;
            }
            var params = { name: name };
            if (stageSelect && stageSelect.value) {
                params.stage_id = parseInt(stageSelect.value, 10);
            }
            btnTask.disabled = true;
            btnTask.textContent = _t("Creating...");
            jsonRpc("/my/projects/" + projectId + "/add_task", params).then(function (res) {
                if (res && res.success) {
                    window.location.reload();
                } else {
                    alert(res && res.error ? res.error : _t("Failed to create task."));
                    btnTask.disabled = false;
                    btnTask.textContent = _t("Create Task");
                }
            });
        });
    }

    if (btnStage) {
        btnStage.addEventListener("click", function () {
            var nameInput = document.getElementById("stageName");
            var name = nameInput ? nameInput.value.trim() : "";
            if (!name) {
                nameInput.focus();
                return;
            }
            btnStage.disabled = true;
            btnStage.textContent = _t("Creating...");
            jsonRpc("/my/projects/" + projectId + "/add_stage", { name: name }).then(function (res) {
                if (res && res.success) {
                    window.location.reload();
                } else {
                    alert(res && res.error ? res.error : _t("Failed to create stage."));
                    btnStage.disabled = false;
                    btnStage.textContent = _t("Create Stage");
                }
            });
        });
    }
}

// ------------------------------------------------------------------
// Field chooser — toggle card fields via localStorage
// ------------------------------------------------------------------

function initFieldChooser() {
    var chooser = document.getElementById("fieldChooser");
    if (!chooser) return;

    var match = window.location.pathname.match(/\/my\/projects\/(\d+)/);
    var storageKey = match ? "woow_project_" + match[1] + "_fields" : "woow_project_fields";

    // Load saved state
    var saved = null;
    try { saved = JSON.parse(localStorage.getItem(storageKey)); } catch (e) { /* ignore */ }

    var checkboxes = chooser.querySelectorAll("input[data-field]");

    // Apply saved state to checkboxes
    if (saved) {
        checkboxes.forEach(function (cb) {
            var field = cb.getAttribute("data-field");
            cb.checked = saved.indexOf(field) !== -1;
        });
    }

    function applyVisibility() {
        var visible = [];
        checkboxes.forEach(function (cb) {
            if (cb.checked) visible.push(cb.getAttribute("data-field"));
        });
        localStorage.setItem(storageKey, JSON.stringify(visible));

        // Toggle visibility of .wt-field-* rows on cards
        document.querySelectorAll(".wt-card-grid .wt-pc-meta [class*='wt-field-']").forEach(function (el) {
            var classes = el.className.split(" ");
            var fieldClass = classes.find(function (c) { return c.startsWith("wt-field-"); });
            if (fieldClass) {
                var field = fieldClass.replace("wt-field-", "");
                el.style.display = visible.indexOf(field) !== -1 ? "" : "none";
            }
        });
    }

    checkboxes.forEach(function (cb) {
        cb.addEventListener("change", applyVisibility);
    });

    // Apply on page load
    applyVisibility();
}

// ------------------------------------------------------------------
// Task detail editor — inline editing for project-addon fields
// ------------------------------------------------------------------

function initTaskEditor() {
    var btnSave = document.getElementById("btnSaveTask");
    if (!btnSave) return;

    var match = window.location.pathname.match(/\/my\/projects\/(\d+)\/task\/(\d+)/);
    if (!match) return;
    var projectId = parseInt(match[1], 10);
    var taskId = parseInt(match[2], 10);

    // Fix breadcrumb for sub-task pages
    var parentData = document.getElementById("wtParentTaskData");
    if (parentData) {
        var parentName = parentData.getAttribute("data-parent-name");
        var parentUrl = parentData.getAttribute("data-parent-url");
        var taskName = parentData.getAttribute("data-task-name");
        // Find the task name breadcrumb item (last active breadcrumb-item with task name)
        var bcItems = document.querySelectorAll(".breadcrumb-item");
        var lastActive = null;
        for (var i = bcItems.length - 1; i >= 0; i--) {
            if (bcItems[i].classList.contains("active")) { lastActive = bcItems[i]; break; }
        }
        if (lastActive) {
            // Replace the active item content with the parent task as a link
            lastActive.classList.remove("active");
            // Task names are user-editable: build the link with DOM APIs, never innerHTML.
            var parentLink = document.createElement("a");
            if (/^\/my\/projects\/\d+\/task\/\d+$/.test(parentUrl || "")) {
                parentLink.href = parentUrl;
            }
            parentLink.textContent = parentName || "";
            lastActive.replaceChildren(parentLink);
            // Add new active item for the sub-task name
            var newItem = document.createElement("li");
            newItem.className = "breadcrumb-item active text-break";
            newItem.textContent = taskName;
            lastActive.parentNode.insertBefore(newItem, lastActive.nextSibling);
        }
    }

    // Move description edit button next to "Description" heading
    var descBtn = document.querySelector(".wt-desc-edit-btn");
    if (descBtn) {
        var descField = document.querySelector("[data-oe-field='description']");
        var h5 = descField && descField.parentElement.querySelector("h5");
        if (h5) {
            h5.style.display = "flex";
            h5.style.alignItems = "center";
            h5.appendChild(descBtn);
        }
    }

    // Save all fields from the Edit Task modal
    btnSave.addEventListener("click", function () {
        var params = {};
        var nameInput = document.getElementById("editTaskName");
        var stageSelect = document.getElementById("editTaskStage");
        var deadlineInput = document.getElementById("editTaskDeadline");
        var descTextarea = document.getElementById("editTaskDescription");

        if (nameInput) params.name = nameInput.value;
        if (stageSelect) params.stage_id = parseInt(stageSelect.value, 10);
        if (deadlineInput) params.date_deadline = deadlineInput.value || false;
        if (descTextarea) params.description = descTextarea.value;

        btnSave.disabled = true;
        btnSave.textContent = _t("Saving...");
        jsonRpc("/my/projects/" + projectId + "/task/" + taskId + "/update", params).then(function (res) {
            if (res && res.success) {
                window.location.reload();
            } else {
                alert(res && res.error ? res.error : _t("Failed to update."));
                btnSave.disabled = false;
                btnSave.textContent = _t("Save Changes");
            }
        });
    });
}

// ------------------------------------------------------------------
// Sub-tasks — add / delete sub-tasks on task detail page
// ------------------------------------------------------------------

function initSubtasks() {
    var btnAdd = document.getElementById("btnAddSubtask");
    if (!btnAdd) return;

    var match = window.location.pathname.match(/\/my\/projects\/(\d+)\/task\/(\d+)/);
    if (!match) return;
    var projectId = parseInt(match[1], 10);
    var taskId = parseInt(match[2], 10);
    var baseUrl = "/my/projects/" + projectId + "/task/" + taskId;

    // Focus name input when modal opens
    var modal = document.getElementById("addSubtaskModal");
    if (modal) {
        modal.addEventListener("shown.bs.modal", function () {
            var nameInput = document.getElementById("subtaskName");
            if (nameInput) nameInput.focus();
        });
    }

    // Submit sub-task
    btnAdd.addEventListener("click", function () {
        var nameInput = document.getElementById("subtaskName");
        var name = nameInput ? nameInput.value.trim() : "";
        if (!name) {
            nameInput.focus();
            return;
        }
        var params = { name: name };
        var stageSelect = document.getElementById("subtaskStage");
        if (stageSelect && stageSelect.value) {
            params.stage_id = parseInt(stageSelect.value, 10);
        }
        var deadlineInput = document.getElementById("subtaskDeadline");
        if (deadlineInput && deadlineInput.value) {
            params.date_deadline = deadlineInput.value;
        }
        var descInput = document.getElementById("subtaskDescription");
        if (descInput && descInput.value.trim()) {
            params.description = descInput.value.trim();
        }
        btnAdd.disabled = true;
        btnAdd.textContent = _t("Creating...");
        jsonRpc(baseUrl + "/add_subtask", params).then(function (res) {
            if (res && res.success) {
                window.location.reload();
            } else {
                alert(res && res.error ? res.error : _t("Failed to add sub-task."));
                btnAdd.disabled = false;
                btnAdd.textContent = _t("Create Sub-task");
            }
        });
    });

    // Enter key on name input triggers submit
    var nameInput = document.getElementById("subtaskName");
    if (nameInput) {
        nameInput.addEventListener("keydown", function (e) {
            if (e.key === "Enter") {
                e.preventDefault();
                btnAdd.click();
            }
        });
    }

    // Delete sub-task buttons
    document.querySelectorAll(".wt-delete-subtask").forEach(function (btn) {
        btn.addEventListener("click", function () {
            var subtaskId = btn.getAttribute("data-subtask-id");
            if (!confirm(_t("Delete this sub-task?"))) return;
            btn.disabled = true;
            jsonRpc(baseUrl + "/delete_subtask", { subtask_id: parseInt(subtaskId, 10) }).then(function (res) {
                if (res && res.success) {
                    window.location.reload();
                } else {
                    alert(res && res.error ? res.error : _t("Failed to delete sub-task."));
                    btn.disabled = false;
                }
            });
        });
    });
}

// ------------------------------------------------------------------
// Mobile filter segments — transform dropdowns to NC-style buttons
// ------------------------------------------------------------------

function initMobileFilterSegments() {
    // On mobile (<= 991px) or on .wt-collapsed-nav pages, transform dropdowns to segments
    var isCollapsed = document.querySelector(".wt-collapsed-nav");
    if (window.innerWidth > 991 && !isCollapsed) return;

    var navContent = document.getElementById("o_portal_navbar_content");
    if (!navContent) return;

    var btnGroups = navContent.querySelectorAll(".nav .btn-group");
    btnGroups.forEach(function (group) {
        var toggle = group.querySelector(".dropdown-toggle");
        var menu = group.querySelector(".dropdown-menu");
        if (!toggle || !menu) return;

        // Dispose Bootstrap dropdown instance to prevent JS conflicts
        if (window.bootstrap && window.bootstrap.Dropdown) {
            var instance = bootstrap.Dropdown.getInstance(toggle);
            if (instance) instance.dispose();
        }
        toggle.removeAttribute("data-bs-toggle");
        toggle.style.display = "none";

        // Transform menu to inline segmented control
        menu.classList.remove("dropdown-menu", "dropdown-menu-end");
        menu.classList.add("ncf-seg");
        menu.style.position = "static";
        menu.style.display = "flex";
        menu.style.transform = "none";

        // Transform items to segment buttons
        menu.querySelectorAll("a").forEach(function (item) {
            var isActive = item.classList.contains("active");
            item.classList.remove("dropdown-item");
            item.classList.add("ncf-seg-btn");
            if (isActive) item.classList.add("active");
        });

        // Add arrow scroll hints when panel opens (dimensions are 0 while collapsed)
        var wrapper = group.parentElement;
        if (!wrapper) return;

        var hintsAdded = false;
        navContent.addEventListener("shown.bs.collapse", function () {
            if (hintsAdded) return;
            if (menu.scrollWidth <= menu.clientWidth) return;
            hintsAdded = true;

            var leftHint = document.createElement("span");
            leftHint.className = "ncf-scroll-hint ncf-scroll-hint-left";
            leftHint.innerHTML = '<i class="fa fa-chevron-left"></i>';

            var rightHint = document.createElement("span");
            rightHint.className = "ncf-scroll-hint ncf-scroll-hint-right visible";
            rightHint.innerHTML = '<i class="fa fa-chevron-right"></i>';

            wrapper.appendChild(leftHint);
            wrapper.appendChild(rightHint);

            menu.addEventListener("scroll", function () {
                leftHint.classList.toggle("visible", menu.scrollLeft > 4);
                rightHint.classList.toggle("visible",
                    menu.scrollLeft < menu.scrollWidth - menu.clientWidth - 4);
            });
        });
    });
}

// ------------------------------------------------------------------
// Quotation actions — add "Next Step" text block
// ------------------------------------------------------------------

function initQuotationActions() {
    var actions = document.querySelector('[name="sale_order_actions"]');
    if (!actions) return;

    // Detect action type by DOM structure (language-independent)
    var hasModalAccept = !!actions.querySelector('[data-bs-target="#modalaccept"]');
    var hasModalDecline = !!actions.querySelector('[data-bs-target="#modaldecline"]');
    var hasPayNow = !!actions.querySelector('#o_sale_portal_paynow');
    var hasSign = hasModalAccept && hasModalDecline;

    var title, desc;
    if (hasSign) {
        title = _t("Confirm this order to continue");
        desc = hasPayNow || actions.querySelector('[data-bs-target="#modalaccept"].btn-primary')
            ? _t("Sign & Pay to confirm. You can leave feedback or reject before signing.")
            : _t("Sign to confirm. You can leave feedback or reject before signing.");
    } else if (hasPayNow || hasModalAccept) {
        title = _t("Complete your payment");
        desc = _t("Pay now to finalize your order.");
    } else {
        title = _t("Actions available");
        desc = "";
    }

    var textBlock = document.createElement("div");
    textBlock.className = "wt-cta-text";
    textBlock.innerHTML =
        '<span class="wt-cta-label">' + _t("NEXT STEP") + '</span>' +
        '<span class="wt-cta-title">' + title + '</span>' +
        (desc ? '<span class="wt-cta-desc">' + desc + '</span>' : '');
    actions.prepend(textBlock);
}
