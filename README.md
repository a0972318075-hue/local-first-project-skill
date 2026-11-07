# Local-first Project Skill

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

本專案不含個人對話、私人路徑或憑證。發布前請執行 tests/validate.py，並參考 tests/scenarios.md 做行為驗收。
驗證器檢查封裝與必要規則，不能證明代理在所有桌面環境都會正確執行。
GitHub 發布步驟見 docs/PUBLISH.md。本專案採 MIT 授權，詳見 [LICENSE](LICENSE)。

## 檔案

- skills/local-first-project/SKILL.md 是技能入口。
- references/ 包含發現、補足、桌面操作與驗收指南。
- tests/ 包含靜態驗證器與行為測試情境。

執行封裝檢查與回歸測試（Python 3，僅使用標準函式庫）。

    python tests/validate.py
    python tests/test_package.py
