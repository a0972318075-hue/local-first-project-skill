# 桌面控制協定與權限（0.3.0）

目標是提高已授權任務的完成率、定位精準度與恢復速度。
技能是決策與驗證規則；真正控制來自宿主工具、應用介面及作業系統權限。
不能承諾任何軟體、任何安全桌面或任何權限層級都可完全控制。

## 操作路由與流暢度

| 工作條件 | 優先方式 | 驗收 |
|---|---|---|
| 使用者指定可見 GUI | 指定程式的桌面操作 | 建立、編輯、儲存均有 UI 證據 |
| 未指定方式，應用有正式 API／CLI | 正式介面 | 產物內容及重開結果 |
| 可唯一識別 UI 控制項 | 語意動作、可讀值回查 | 新值或狀態符合預期 |
| 自繪畫布或無可用語意控制 | 新截圖、視窗內座標、縮放與焦點確認 | 圖像與內容核對 |
| 權限或政策拒絕 | 停止該操作，分類並走正式授權 | 授權後重新檢查能力 |

已經可用的工具不重裝；背景語意操作不無故搶前景。
GUI 有新增視窗、模態對話框、滾動、清單更新、縮放或使用者輸入時，立即刷新相關定位。
固定等待改為有上限的條件等待；僅查目標視窗與需要的子樹。
只有不跨越未知狀態、可逐項驗證的動作才批次執行。不要批次串接「開啟對話框→猜座標→送出」。
同一桌面一次只允許一個輸入者；多代理可並行分析，不能同時爭用鍵鼠。

## 認識權限，而非一律提升

分別記錄：使用者是否授權本動作、工具政策是否允許、OS 是否可存取目標、應用帳號是否有權限。
其中任一未知都不能用另一層的成功代替。

| 層級 | 如何處理 |
|---|---|
| 一般使用者的文件、同權限程式 | 沿既有授權直接工作，完成能力測試 |
| 工具允許的鍵鼠／截圖能力尚未啟用 | 檢查工具說明，透過宿主互動授權啟用需要的能力 |
| 確有需要操作較高權限目標 | 準備具體操作、目標、理由、影響、恢復方法及結束條件，使用正式提升入口 |
| UAC 安全桌面、登入、MFA、受管理政策拒絕 | 使用者完成必要互動；政策拒絕則停止該路徑，不改用其他工具繞過 |

「使用者允許」不等於「OS 已提升」；「管理員終端」不等於「應用帳號已登入」。
不要把整個 AI 助理設成永久管理員。若任務確需提升，只讓指定工作與有限期間具備必要權限。
不關閉 UAC、不停用防護、不擷取權杖或 Cookie、不建立 SYSTEM 常駐服務來迴避互動授權。
已授權且仍在同一範圍的操作不重複詢問；增加權限或擴大目標才重新確認。

## agent-desktop 本機對接

以安裝版本的說明為準，先執行 `agent-desktop status`、`agent-desktop permissions`。
再讀 `agent-desktop skills get desktop` 與 `agent-desktop skills get platform`。
有 elevation 問題時讀 `agent-desktop skills get agent-desktop-windows references/permissions-and-elevation.md`。

已驗證可讀的入口：

```text
agent-desktop list-windows --timeout-ms 5000
agent-desktop snapshot --window-id <本次清單的ID> --skeleton --compact --timeout-ms 5000
```

視窗 app_name 可能空白；以 pid、程序路徑、視窗及文件內容交叉確認，不能只靠標題。
引用需沿用同一 session 並包含 snapshot ID；PowerShell 中以單引號包住 `@ref`。
`--headed` 是輸入方式選擇，不是管理員提升或政策豁免。
讀取每次結果的 ok、disposition.delivery、disposition.retry。
delivered_unverified 與送達後回查失敗都先觀察，不直接重播。

## 動作前檢查器

從技能目錄執行 `python scripts/desktop_guard.py observation.json`。
輸入是宿主整理過的觀察資料，**不是 agent-desktop 原始回應格式**：

```json
{
  "snapshot_id": "s-current",
  "target_snapshot_id": "s-current",
  "age_ms": 100,
  "window_id": "w-current",
  "target_window_id": "w-current",
  "matches": 1,
  "visible": true,
  "enabled": true,
  "focused": true,
  "modal_window_id": null,
  "delivery": "semantic",
  "permission": "granted",
  "authorized": true,
  "previous_outcome": "none",
  "retry_safe": false,
  "user_intervened": false
}
```

上述為示例，不是實機成功證據。呼叫端應從真實工具與對話授權建立資料：

- age_ms 使用同一宿主的單調時計算，不能猜測；超過 5 秒重新觀察。5 秒是保守門檻，不保證期間內畫面不變。
- snapshot_id 是目前觀察；target_snapshot_id 是目標定位來源，兩者須一致。
- window_id 是目前被觀察視窗；target_window_id 是本次動作的視窗。
- matches 必須是整個目標視窗的唯一性檢查結果，不是截斷子樹的數量。
- focused 對實體輸入表示前景視窗及正確輸入焦點均已確認。
- modal_window_id 無遮擋才填 null；不知道時先觀察，不填假值。
- permission：granted、not-required、denied、unknown；僅代表本次目標能力。
- previous_outcome 是**同一動作**的狀態：none、not-delivered、unknown、delivered-unverified、verified。
- 工具回傳 not-delivered 也不代表可以重試；只有工具明確回報 retry=safe 才填 retry_safe=true，否則檢查器回傳 diagnose。呼叫端仍需確認錯誤原因已處理。

exit 0 / ready-for-dispatch：可交給受政策約束的 adapter 再檢查並執行。
exit 3：有待處理項目，包括 observe、reconcile、diagnose、resolve-modal、focus-and-observe、needs-authorization、inspect-permission、blocked-permission、already-complete。
exit 2：輸入無效。檢查器不發送鍵鼠、不取得權限、不認證輸入真實性，也不消除檢查與執行間的競態。
必須由宿主接入才能影響實際派送；目前提供獨立檢查器，尚未整合 agent-desktop 自動執行。

## 可重複驗收

使用新建的測試文件，先記錄基線，再使用技能，各重複至少五次。
案例：背景文字框、同名按鈕、模態遮擋、焦點被使用者切換、過期定位、未知貼上結果、權限拒絕。
保存工具呼叫、輸出及最終文件；公開前去除私人資料。
比較完成率、錯誤輸入次數、未知結果重播次數、非必要焦點切換、重複詢問、耗時中位數。
規則測試不等於操作成功率；沒有實測數據，不宣稱流暢度或精準度已提升多少。
