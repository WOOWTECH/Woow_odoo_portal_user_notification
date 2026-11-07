# woow_portal_notification_subscription

入口通知中心（`woow_portal_notification`）和 WOOW 訂閱引擎（`woow_subscription`）之間的銜接。取代舊橋接 `woow_portal_notification_sh_subscription`。授權 LGPL-3。

## 行為

- 訂閱客戶本人從通知中心點開訂閱通知，導到 `/woow#/billing/subscriptions`。/woow 是 hash 路由，沒有每張訂閱的明細頁，所以每張訂閱都導到這個列表。
- 不是本人（例如只是追蹤者）：交回通知中心的預設，也就是沒有頁面、用對話框顯示訊息。
- 入口使用者對訂閱沒有任何權限。客戶比對用 superuser，只讀客戶欄位，所以點開不會 403。
- 內部使用者在通知中心只看到客戶是自己的訂閱（`_wpn_portal_record_domain`），這要有訂閱讀取權：引擎的操作人員、主管或開票人員。

## 安裝與休眠

- `auto_install`：`woow_portal_notification` 與 `woow_subscription` 都在時自動安裝。R1 安裝休眠引擎時，它會自動跟著裝。
- auto_install 只在安裝模組時觸發，`-u all` 不會。資料庫若在帶進本模組之前就已裝好引擎，要手動安裝。
- 只讀：沒有資料檔、掛鉤、排程，也沒有覆寫任何建立或寫入。休眠時不產生通知，也不寫入。

更多行為與測試說明，見 repo 根目錄的 README.md。
