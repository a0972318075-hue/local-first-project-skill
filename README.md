# Local-first Project Skill

目前版本：**0.4.2**。

讓 AI 代理先認識本機環境，主動補足缺少的軟體與依賴，再完成並驗證專案。

核心流程為「確認任務 → 本機發現 → 判斷缺口 → 授權內補足 → 真實功能測試 → 執行 → 驗收」。

## 適用範圍

需要本機應用、開發 runtime、桌面操作或外掛的專案。技能包含跨平台發現指南與 Windows 桌面注意事項。它是一套代理指令與檢查規則，安裝由代理依環境選擇官方工具執行。

## 安裝

使用完整的 [local-first-project 技能目錄](skills/local-first-project)，保留其中的 scripts/ 與 references/。若目的地已有同名技能，先比較版本與自訂修改。

| 代理 | 載入方式 |
| --- | --- |
| Codex | 使用本機技能目錄。下方提供 Windows 範例。 |
| Claude Code | 放入專案的 `.claude/skills/local-first-project/`，在新會話使用 `/local-first-project`。[官方文件](https://code.claude.com/docs/en/skills) |
| Hermes Agent | 放入目前 Hermes 設定檔的技能目錄，預設為 `~/.hermes/skills/`，再開新會話呼叫技能。[官方文件](https://hermes-agent.nousresearch.com/docs/guides/work-with-skills) |
| Deep Code | 放入專案的 `.deepcode/skills/local-first-project/`，從斜線選單選取。[官方文件](https://api-docs.deepseek.com/quick_start/agent_integrations/deepcode/) |
| WorkBuddy AI、DeepSeek Harness 與其他有工作區的代理 | 開啟包含技能的專案，明確要求讀取 `skills/local-first-project/SKILL.md`，再依任務讀取其相對路徑下的參考與腳本。 |
| Claude Desktop 預設對話與其他純聊天代理 | 將 [SKILL.md](skills/local-first-project/SKILL.md) 內容貼入對話。可用來規劃或判讀你提供的證據。若對話缺少本機工具，請在可執行的代理完成操作並帶回結果。 |

Codex 的 Windows 範例：

```powershell
New-Item -ItemType Directory -Path "$env:USERPROFILE\.codex\skills" -Force | Out-Null
Copy-Item -LiteralPath .\skills\local-first-project -Destination "$env:USERPROFILE\.codex\skills\local-first-project" -Recurse
```

## 使用

「使用 local-first-project，先確認這台電腦有沒有 LibreOffice。如果缺少，找官方方式補足，再在 Impress 裡逐步製作和儲存簡報。」

「使用 local-first-project，盤點專案 runtime 與依賴，修復缺口並執行既有測試。」

各代理可用同一個提示詞驗收：

> 使用 local-first-project 唯讀盤點 LibreOffice。先說明技能從哪裡載入，以及檔案和終端工具是否連到我的 Windows。分別列出 PATH、已知位置和開始功能表的查詢結果。未能檢查的來源標為尚未檢查。找到候選回報 found-unverified，沒有足夠證據回報 unknown。請附工具輸出或具體阻礙，這次只做唯讀盤點。

驗收時分別記錄技能是否載入、工具是否在目標電腦執行，以及結果是否有證據。各代理的原生載入與本機操作需在各自環境實測。
記錄格式、配對比較與跨代理證據見 [驗收情境](tests/scenarios.md) 和 [驗證紀錄](tests/RESULTS.md)。

## 發布與驗證

發布前請執行 tests/validate.py，並參考 tests/scenarios.md 做行為驗收。
自動檢查涵蓋文件中的 Windows 使用者路徑與相對連結，不是完整個資或秘密掃描；原始盤點輸出與代理紀錄仍需人工審查後才可發布。
驗證器檢查封裝與必要規則，不能證明代理在所有桌面環境都會正確執行。
GitHub 發布步驟見 docs/PUBLISH.md。本專案採 MIT 授權，詳見 [LICENSE](LICENSE)。

## 檔案

- skills/local-first-project/SKILL.md 是技能入口。
- references/ 包含發現、補足、桌面操作與驗收指南。
- tests/ 包含靜態驗證器與行為測試情境。

執行封裝檢查與回歸測試（Python 3.11 或更新版本，僅使用標準函式庫）。

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

## 0.4.0 有界執行與影片整理

- [程序執行器](skills/local-first-project/references/runner.md)：明確命令清單、逐步檢查點、逾時停止、輸出驗證與拒絕自動重播。不是作業系統沙箱或 GUI 全自動控制器。
- [video-review 技能](skills/video-review/SKILL.md)：處理影片身分、字幕取得、抽樣觀看、來源時間戳及簡報證據；可獨立複製到技能目錄。
- 本機案例：YouTube 搜尋與字幕／畫面核對後，由執行器派送簡報生成及驗證。影片內容與私人原始紀錄不放入公開儲存庫。

## 0.4.1 執行器檢查順序

純計畫檢查可重驗已有執行紀錄和產物的清單；實際執行仍拒絕重播或覆寫既有產物。
無效工作目錄回報輸入錯誤；不支援的 Python 版本有獨立狀態與結束碼。

## 0.4.2 跨代理驗收與 Impress 實測

固定測試版本、代理、工具宿主、載入方式和原始證據；比較工具區分已執行、受阻與缺樣本。
以 LibreOffice Impress 介面建立、儲存、關閉及重開兩頁 PPTX；另核對檔案文字與雜湊。
桌面證據只適用於已測試的 Windows 宿主與應用，不代表所有代理都能操作同一台電腦。
