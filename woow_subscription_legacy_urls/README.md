# woow_subscription_legacy_urls

舊訂閱入口頁的網址，轉址到「我的帳戶」的訂閱頁（`/my/subscriptions`，由 woow_paas_platform 提供）。授權 LGPL-3。

| 舊網址 | 回應 |
|---|---|
| `/my/sh_subscription` | 301，`Location: /my/subscriptions` |
| `/my/sh_subscription/page/<n>` | 同上 |
| `/my/sh_subscription/<id>`（舊信與書籤裡的深連結） | 301，`Location: /my/subscriptions/<id>`（切換時保留了 id，所以是同一筆訂閱） |
| `/cancel-subscription`、`/renew-subscription` | 不轉址，404 |

- 只接 GET 與 HEAD，任何人都轉址：「我的帳戶」的頁面自己會要求登入，也只讓訂閱的客戶本人看到。這裡不查資料，也不儲存 session。
- 查詢字串一律丟掉。舊頁面的分頁、排序、`access_token` 等參數，新頁面都不讀；轉址也不把 token 往外帶。

## 安裝時機與保留期限

- **卸載舊引擎之後才安裝**。不設 auto_install，分類是 Hidden。
- manifest 宣告 `excludes: ['sh_subscription']`。舊引擎已安裝時，Odoo 拒絕安裝本模組（CLI 與 Apps 都一樣，發生在任何寫入之前）；本模組已安裝時，也不能把舊引擎裝回來。舊入口頁因此不會被搶走。
- 保留 6 個月（從切換當晚安裝起算），之後卸載並從映像移除。

更多行為與測試說明，見 repo 根目錄的 README.md。
