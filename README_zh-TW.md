# Woow Portal 通知中心（Odoo 18）

Odoo 會寄 email 通知客戶訂單、發票、專案的消息，但 portal 裡沒有地方讓客戶看這些通知。這兩個模組只補上這件事；Odoo 原生的 portal 頁面、卡片與版面都維持原樣。

[English](README.md)

## 模組

| 模組 | 功能 | 依賴 |
|---|---|---|
| `woow_portal_notification` | portal 使用者的通知未讀機制、`/my` 的問候與通知摘要、`/my/notifications` 通知中心、使用者選單入口與頭像未讀小點 | `portal`、`mail` |
| `woow_portal_notification_discuss` | 給 `woow_odoo_portal_discuss` 用的「未讀對話」提醒卡與提示 | `woow_portal_notification`、`woow_odoo_portal_discuss` |
| `woow_portal_notification_sh_subscription` | 訂閱的通知直接打開 `/my/sh_subscription/<id>` | `woow_portal_notification`、`sh_subscription` |
| `woow_portal_notification_crm` | 指派給客戶的潛在商機／商機通知直接打開 `/my/lead/<id>` 或 `/my/opportunity/<id>` | `woow_portal_notification`、`website_crm_partner_assign` |
| `woow_portal_notification_loyalty` | 禮物卡、錢包點數的通知直接打開 `/my/loyalty_card/<id>/history` | `woow_portal_notification`、`loyalty` |

四個銜接模組在兩個依賴都安裝時自動安裝。

## 客戶看到的

畫面全部用 Odoo 原生的 portal 元件組成，所以和其他 portal 頁面一致，並跟著網站主題走。

**`/my`**
- Odoo 原生標題列那一行改成問候，例如「午安，王大明」。早安、午安、晚安用瀏覽器的時間判斷，使用者沒設時區也正確。
- 原生提醒卡「N 則未讀通知」（和「待審閱報價」並排），以及原生卡片「通知中心」。數量和其他卡片一樣經 `/my/counters` 取得，沒有可計數的內容時自動隱藏。

**`/my/notifications`**
- 和訂單、發票列表一樣的原生搜尋列（篩選全部／未讀、搜尋）與原生表格：最新的在前、每頁 20 則、原生分頁。未讀的標題粗體並加「未讀」標籤。
- 點一則通知會打開對應的單據，並標成已讀。單據沒有客戶頁面時（例如聯絡人、行事曆），改在對話視窗顯示訊息內容。
- 每則通知可以切換已讀／未讀。「全部標為已讀」只套用到目前的搜尋結果。

**每個網站頁面**
- 使用者選單有「通知中心」，名字旁邊顯示未讀數，樣式和購物車、願望清單的數字相同。

**整個 portal**
- 打開單據頁時，關於這張單據的通知會一起標成已讀。

不服務內部員工：員工打開 `/my/notifications` 會被帶到後台收件匣，`/my` 維持 Odoo 原樣。

## 運作方式

- **portal 未讀機制**：Odoo 因為 portal 使用者沒有收件匣，把他們的 email 通知建立成已讀。`mail.notification.create` 會把「使用者全是 portal 使用者」的聯絡人的通知改成未讀。內部員工的行為不變。
- **單據連結**：`mail.thread._wpn_portal_url()` 依序回傳：
  1. portal 頁（`portal.mixin` 的 `access_url`）
  2. 已發布的網站頁（`website_url`）
  3. `False`，此時改在對話視窗顯示訊息

  這個方法以客戶身分判斷，只連到他看得到的頁面。單據有其他客戶頁面的模組覆寫這個方法即可，訂閱、指派商機、禮物卡三個銜接模組就是這樣做。
- **額外提示**：通知清單上方的提示由 `PortalNotificationCenter._wpn_extra_entries()` 提供；首頁卡片用 Odoo 原生的計數（`_prepare_home_portal_values`）。討論區銜接模組兩者都用。
- **外觀**：只用 Bootstrap 的 SCSS 變數與工具類別，所以跟著網站主題走，不載入任何字型或品牌色。
- **資料表**：不新增任何欄位或資料表，卸載後 Odoo 的資料表維持原狀。

## 設定

在「設定 > 技術 > 系統參數」設定，值設為 `0` 即關閉該功能。

| 參數 | 預設 | 作用 |
|---|---|---|
| `woow_portal_notification.portal_unread` | `1` | portal 使用者的新通知以未讀建立 |
| `woow_portal_notification.home_summary` | `1` | `/my` 顯示通知卡片 |

## 測試

```
odoo -d <db> -i woow_portal_notification --test-enable \
     --test-tags /woow_portal_notification,/woow_portal_notification_discuss,/woow_portal_notification_sh_subscription,/woow_portal_notification_crm,/woow_portal_notification_loyalty \
     --stop-after-init
```

測試在四種資料庫上跑：
- 只有 `portal`、`mail` 和本模組；
- 先裝 `website` 再裝本模組（正式站的順序）；
- 加裝 `woow_odoo_portal_discuss`；
- 加裝 `sh_subscription`、`website_crm_partner_assign`、`loyalty`。

## 沿革

這兩個模組取代 `woow_portal_ui`（18.0.2.x）。舊模組除了通知中心，也改了所有 portal 列表與明細頁的版面，並改動全站行為：登入後導向、強制語言、隱藏頁尾、字型與配色。

舊程式保留在：
- git 歷史，tag `archive/woow_portal_ui-18.0.2.2.3`；
- 分支 `ux/portal-ui-sandbox-review-20261103`（18.0.2.3.0，未發版）。

## 授權

LGPL-3
