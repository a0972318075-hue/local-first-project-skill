# 可執行輔助工具（0.2.1）

這些工具支援既有流程；不替代理授權、不操作桌面、不自動安裝軟體。

## Windows 只讀盤點

從技能目錄執行，已實測 PowerShell 7，無第三方套件：

```powershell
pwsh -NoProfile -File scripts/discover_windows.ps1 -Product LibreOffice -Command soffice
pwsh -NoProfile -File scripts/discover_windows.ps1 -Product Git -Command git
```

已知執行檔可用 `-KnownPath` 傳入完整路徑。產品名稱是字面比對，不支援萬用字元。
PowerShell 5.1 尚未完成功能驗證。若腳本被執行原則阻擋，記錄 blocked，遵循環境授權流程；不要自動調整或繞過原則。
輸出 JSON 包含 schema_version、observed_at、product、status、evidence、limitations。
每筆 evidence 有 source、status（found / not-found / unchecked / error）及 details。
來源是程序、PATH、三個登錄安裝位置、開始功能表捷徑、指定路徑。
不讀視窗標題、私人文件、憑證，不執行找到的程式，不連網。

候選命中只代表 found-unverified；未命中維持 unknown。
程序名稱可能與品牌不同、檔案可能不是所稱產品、登錄可能過期。
因此這份輸出不能自動宣告 ready 或 missing-after-search。
GUI、套件管理器、自訂目錄及產品真實功能仍依任務另查。
代理為整體呼叫設定 45 秒上限；逾時視為 unknown，不採部分輸出推斷不存在。
輸出可能包含本機路徑，保存在專案私人執行紀錄，不直接提交或發布。

## 任務契約與檢查點

以 JSON 記錄下列格式（例子是未執行任務，不是成功證據）：

```json
{
  "schema_version": 1,
  "task_id": "slides-demo",
  "contract": {
    "goal": "製作簡報",
    "application": "LibreOffice Impress",
    "gui_required": true,
    "output": "slides.pptx"
  },
  "steps": [{
    "id": "save-slides",
    "operation": "save",
    "status": "planned",
    "channel": "gui",
    "application": "LibreOffice Impress",
    "retry_safe": false,
    "evidence": []
  }]
}
```

`application` 是本次任務固定名稱；工具別名先由代理核實並統一。
`operation`：inspect、create、edit、save、install、publish。
`status`：planned、running、unknown、verified、failed。
`channel`：gui、script、api。`retry_safe` 必須為布林值，但不會自動准許重播。
`evidence` 是已觀察工具輸出／截圖／檔案檢驗的參照，不能用預期結果填入。

由執行端在動作前保存 running，動作後保存核對結果。
先寫同目錄暫存檔，再原子替換正式檢查點；同一任務只使用一個寫入者。
這版不包含執行器或自動保存功能，代理或宿主負責持久化。
中斷後 running 與 unknown 均先重新觀察；舊紀錄不代表目前狀態。

```text
python scripts/workflow.py path/to/checkpoint.json
```

exit 0 表示資料合法；exit 2 表示無效，並輸出原因。
輸入採 UTF-8（可有 BOM），上限 1 MiB；拒絕任何層級的重複欄位及 NaN／Infinity。
錯誤輸入回傳 JSON error，外部執行端仍需設定逾時並檢查結束碼。
合法資料仍需讀取 decision：

| decision | 接續工作 |
|---|---|
| continue | 檢查授權、前置條件，再處理下一步 |
| observe | 核對未知／進行中動作；不能直接重播 |
| diagnose | 依錯誤類別診斷，再決定修復 |
| review-delivery | 核對完整契約、產物與重開結果，不代表自動完成 |

檢查器會拒絕指定 GUI 卻用 script/api 建立、編輯、儲存，或使用不同應用程式。
verified 必須附非空證據，但檢查器無法驗證證據真實性、權限或範圍是否完整。
它是輔助檢查，不是安全邊界，宿主仍須強制權限與工具政策。

## 失敗分類

| 實際證據 | 處理 |
|---|---|
| PATH 未命中 | 查程序、捷徑、安裝清單與已知位置 |
| 權限拒絕 | 記錄 blocked，依正式審批流程處理 |
| 功能／設定錯誤 | 確認設定來源，最小修復後重新測試 |
| 認證錯誤 | 區分瀏覽器、gh、Git credential helper，不重新安裝 Git |
| 逾時／動作送達不明 | 記錄 unknown，讀取現況後決定是否可重試 |
| 格式或內容不符 | 修復產物並重開驗收，不能只以存在或 hash 判定成功 |
