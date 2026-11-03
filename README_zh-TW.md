# Woow Portal 通知中心（Odoo 18）

Odoo 會寄 email 通知客戶訂單、發票、專案的消息，但 portal 裡沒有地方讓客戶看這些通知。這兩個模組只補上這件事；Odoo 原生的 portal 頁面、卡片與版面都維持原樣。

[English](README.md)

## 模組

| 模組 | 功能 | 依賴 |
|---|---|---|
| `woow_portal_notification` | portal 使用者的通知未讀機制、`/my` 的問候與通知摘要、`/my/notifications` 通知中心、使用者選單入口與頭像未讀小點 | `portal`、`mail` |
| `woow_portal_notification_discuss` | 給 `woow_odoo_portal_discuss` 用的「未讀對話」一行；兩者都裝了就自動安裝 | `woow_portal_notification`、`woow_odoo_portal_discuss` |

## 客戶看到的

**`/my`**
- Odoo 原生標題列那一行改成問候，例如「午安，王大明」。早安、午安、晚安用瀏覽器的時間判斷，使用者沒設時區也正確。
- 原生卡片上方有一張摘要卡：未讀數、最新 3 則未讀、「查看全部」。沒有未讀時只剩一行「沒有新通知」。

**`/my/notifications`**
- 一個清單，最新的在前。可以切換「全部／未讀」、搜尋，每頁 20 則，未讀的有標示。
- 點一則通知會打開對應的單據，並標成已讀。單據沒有客戶頁面時（例如聯絡人、行事曆），改在對話視窗顯示訊息內容。
- 每則通知可以切換已讀／未讀。「全部標為已讀」只套用到目前的搜尋結果。

**每個網站頁面**
- 使用者選單有「通知中心」和未讀數，頭像旁邊有未讀小點。

**整個 portal**
- 打開單據頁時，關於這張單據的通知會一起標成已讀。

不服務內部員工：員工打開 `/my/notifications` 會被帶到後台收件匣，`/my` 維持 Odoo 原樣。

## 運作方式

- **portal 未讀機制**：Odoo 因為 portal 使用者沒有收件匣，把他們的 email 通知建立成已讀。`mail.notification.create` 會把「使用者全是 portal 使用者」的聯絡人的通知改成未讀。內部員工的行為不變。
- **單據連結**：`mail.thread._wpn_portal_url()` 依序回傳：
  1. portal 頁（`portal.mixin` 的 `access_url`）
  2. 已發布的網站頁（`website_url`）
  3. `False`，此時改在對話視窗顯示訊息

  這個方法以客戶身分判斷，只連到他看得到的頁面。單據有其他客戶頁面的模組，覆寫這個方法即可。
- **額外項目**：通知上方的額外項目由 `PortalNotificationCenter._wpn_extra_entries()` 提供，討論區銜接模組就是用這個方法。
- **外觀**：只用 Bootstrap 的 SCSS 變數與工具類別，所以跟著網站主題走，不載入任何字型或品牌色。
- **資料表**：不新增任何欄位或資料表，卸載後 Odoo 的資料表維持原狀。

## 設定

在「設定 > 技術 > 系統參數」設定，值設為 `0` 即關閉該功能。

| 參數 | 預設 | 作用 |
|---|---|---|
| `woow_portal_notification.portal_unread` | `1` | portal 使用者的新通知以未讀建立 |
| `woow_portal_notification.home_summary` | `1` | `/my` 顯示通知摘要 |

## 測試

```
odoo -d <db> -i woow_portal_notification --test-enable \
     --test-tags /woow_portal_notification,/woow_portal_notification_discuss --stop-after-init
```

測試在兩種資料庫上跑：
- 只有 `portal`、`mail` 和本模組；
- 另外加裝 `website`、`sale_management`、`woow_odoo_portal_discuss`。

## 沿革

這兩個模組取代 `woow_portal_ui`（18.0.2.x）。舊模組除了通知中心，也改了所有 portal 列表與明細頁的版面，並改動全站行為：登入後導向、強制語言、隱藏頁尾、字型與配色。

舊程式保留在：
- git 歷史，tag `archive/woow_portal_ui-18.0.2.2.3`；
- 分支 `ux/portal-ui-sandbox-review-20261103`（18.0.2.3.0，未發版）。

## 授權

LGPL-3
