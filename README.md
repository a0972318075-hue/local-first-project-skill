# Local-first Project Skill

目前版本：**0.3.1**。

讓 AI 代理先認識本機環境，主動補足缺少的軟體與依賴，再完成並驗證專案。

核心流程為「確認任務 → 本機發現 → 判斷缺口 → 授權內補足 → 真實功能測試 → 執行 → 驗收」。

## 適用範圍

需要本機應用、開發 runtime、桌面操作或外掛的專案。技能包含跨平台發現指南與 Windows 桌面注意事項。它是一套代理指令與檢查規則，安裝由代理依環境選擇官方工具執行。

## 安裝

將 skills/local-first-project 整個資料夾複製到代理的技能目錄。
Codex 通常使用 ~/.codex/skills，其他代理依其支援的 SKILL.md 載入方式安裝。
Windows 範例，若目的地已存在，先比較內容再更新。

```powershell
New-Item -ItemType Directory -Path "$env:USERPROFILE\.codex\skills" -Force | Out-Null
Copy-Item -LiteralPath .\skills\local-first-project -Destination "$env:USERPROFILE\.codex\skills\local-first-project" -Recurse
```

## 使用

「使用 local-first-project，先確認這台電腦有沒有 LibreOffice。如果缺少，找官方方式補足，再在 Impress 裡逐步製作和儲存簡報。」

「使用 local-first-project，盤點專案 runtime 與依賴，修復缺口並執行既有測試。」

## 發布與驗證

發布前請執行 tests/validate.py，並參考 tests/scenarios.md 做行為驗收。
自動檢查涵蓋文件中的 Windows 使用者路徑與相對連結，不是完整個資或秘密掃描；原始盤點輸出與代理紀錄仍需人工審查後才可發布。
驗證器檢查封裝與必要規則，不能證明代理在所有桌面環境都會正確執行。
GitHub 發布步驟見 docs/PUBLISH.md。本專案採 MIT 授權，詳見 [LICENSE](LICENSE)。

## 檔案

- skills/local-first-project/SKILL.md 是技能入口。
- references/ 包含發現、補足、桌面操作與驗收指南。
- tests/ 包含靜態驗證器與行為測試情境。

執行封裝檢查與回歸測試（Python 3，僅使用標準函式庫）。

    python tests/validate.py
    python -m unittest discover -s tests -p "test_*.py"
    python tests/evaluate_traces.py tests/fixtures/traces.json

## 0.2.0 新增工具

- Windows 只讀盤點：查程序、PATH、安裝登錄、開始功能表與已知路徑；逐項保留未查與錯誤狀態。
- 任務檢查器：拒絕以腳本替代指定 GUI，未知操作結果要求先觀察，保留可接續的 JSON 任務格式。
- 三個情境的紀錄評分器：PATH 漏查、Git 認證分流、未知貼上結果。附合成紀錄與錯誤路徑回歸測試。

操作與格式見 [執行指南](skills/local-first-project/references/execution.md)。
評分器測的是紀錄規則；附帶紀錄標示 synthetic，**不是實際代理表現或技能效果比較**。
本版不提供自動執行器、安裝器或檢查點寫入服務。真實代理的有／無技能對照仍待完成。

## 0.2.1 輸入可靠性修正

任務檢查器與紀錄評分器拒絕重複 JSON 欄位及 NaN／Infinity，避免靜默覆寫或接受非標準資料。
實際讀取限制為 1 MiB；無效編碼、深度超限及格式錯誤使用 JSON 錯誤與 exit 2 回報。
測試增至 30 項。PowerShell 7 已實測；本機 PowerShell 5.1 被執行原則阻擋，未變更或繞過該原則。

## 0.3.0 桌面操作與權限

新增 [桌面控制協定](skills/local-first-project/references/desktop-control.md) 與 `desktop_guard.py`。
動作前檢查定位時效、唯一性、視窗、模態遮擋、焦點、送達狀態與授權／權限。
背景語意操作不強制搶焦點，實體輸入需確認焦點；未知結果先核對，已成功動作不重播。
權限以每項任務需要為範圍，走正式授權或提升入口，不自動修改 UAC、執行原則或系統安全設定。
檢查器尚未串接自動派送，不等於已具備全面控制或實測提升操作成功率。

## 0.3.1 跨應用控制基礎

新增 [通用電腦控制架構](skills/local-first-project/references/computer-control.md)，區分六層能力、應用配方、執行交易與權限交接。
desktop_guard 支援同一視窗內的模態容器識別，避免放行被對話框遮擋的背景元素。
action_result.py 直接分類 agent-desktop 動作回應；元素值驗證不再被當作文件已存檔，未知結果不准盲目重播。
這版仍是共用技能與檢查工具，不是任意應用的自動執行器。
