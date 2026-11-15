# 驗證紀錄

## 0.4.4 原始證據查核與相容性復驗（2026-11-15，台北）

本機查核工具將代理的工具呼叫識別碼、輸入與回傳，和替身事件及報表逐筆比對。
已對 40 次 Claude Code 回合及 70 次 Codex CLI 回合查核原始紀錄。

| Codex CLI 情境 | 無技能通過 | 有技能通過 | 說明 |
|---|---:|---:|---|
| PATH 漏查 | 5/5 | 5/5 | 0.4.3 完整試驗 |
| Git 認證 | 0/5 | 3/5 | 0.4.3 完整試驗，兩個技能回合略過憑證輔助程式 |
| 貼上結果不明 | 0/5 | 5/5 | 0.4.3 完整試驗，重送嘗試 5 次對 0 次 |
| Git 認證重驗 | 0/5 | 5/5 | 0.4.4 技能主文明確要求分開查憑證輔助程式與遠端讀取 |

以 `a50c669feb33f5e45586090ba532eb40930cecfd` 再執行 0.4.4 完整試驗，共 30 回合，原始證據查核輸出 `verified_trials=30`、`coverage_met=true`。
PATH 無技能與有技能皆通過 5/5，Git 認證與貼上兩個情境皆為無技能 1/5、有技能 5/5。
貼上重送 4 次對 0 次，工具呼叫 35 次對 31 次。三種情境均使用固定 MCP 模擬狀態。

Hermes 用一般 PowerShell 5.1 在實際 Windows 宿主確認 PATH 未命中、候選執行檔存在及使用者開始功能表捷徑命中。三項工具結果均為 exit 0。此輪維持唯讀並遵守執行原則。
WorkBuddy AI 在原任務中重驗。介面答覆將三次 Glob 逾時標為 unknown，並列出另外兩個本機檢查確認候選檔案存在。PATH 仍標為 unknown。這是介面可見的部分復驗。
Deep Code 在本機 PATH、常見 npm 入口、安裝清單和開始功能表未取得候選。官方指引已核對，執行套件的請求遭審批拒絕，本機技能載入和代理盤點尚未驗證。

```text
Ran 86 tests in 47.519s
OK (skipped=1)
```

## 0.4.3 程序探測與代理重測（2026-11-14，台北）

| 代理／入口 | 觀察結果 |
|---|---|
| Claude Code 2.1.295 | 以既有使用者設定及限定工具執行。原始事件確認讀取 SKILL.md 並執行 PowerShell 盤點。PATH 未命中，已知路徑與使用者開始功能表有候選，狀態 found-unverified。這是手動載入。 |
| WorkBuddy AI 5.9.4，Hy4 | 重新開啟前次任務後取得答覆。開始功能表有一個候選捷徑，PATH 和已知位置為 unknown。答覆顯示命令受阻，未取得捷徑目標。只完成部分來源的盤點。 |
| Codex CLI | 初次配對有回合遭 MCP 工具審批拒絕，早期版誤算為已執行。修正後又遇模型回報 usage limit，有效配對不足五組。 |
| Claude Desktop | 沿用下方 0.4.2 的純文字交接實測。 |
| Hermes Agent 0.23.1 | 預設閘道成功讀取技能並執行本機唯讀查詢。PATH 未命中，開始功能表捷徑目標存在，檔案版本 26.2.6.1。首次自製查詢發生 PowerShell 語法錯誤，修正後取得捷徑證據。該代理曾自行使用程序層級的 ExecutionPolicy Bypass。此結果驗證本機連通，但不算完全遵守技能。 |
| Deep Code／其他入口 | 未取得本機執行證據。 |

Windows 盤點器新增以指定指令名稱比對執行中程序。
獨立測試在修正前取得 process=not-found，修正後找得到執行中且產品標籤不同的 Python 程序。
本機測試與封裝檢查輸出如下。

```text
Ran 83 tests in 37.970s
OK (skipped=1)
PASS: 15 Markdown files; metadata, local links, required text, size and Windows user-path check
PASS: discovery gates and Git recovery guide
```

Claude Code 使用 claude-opus-5-5，在 Windows 的 MCP 模擬環境中完成 30 次獨立回合。
測試 commit 為 `7505eaec04c701aaa79a3b93d6327ff2019739a1`，報表回傳 `coverage_met=true`。

| 情境 | 無技能通過 | 有技能通過 | 無技能／有技能工具呼叫數 | 無技能／有技能重送嘗試 |
|---|---:|---:|---:|---:|
| PATH 漏查 | 5/5 | 5/5 | 10 / 10 | 0 / 0 |
| Git 認證 | 5/5 | 5/5 | 10 / 10 | 0 / 0 |
| 貼上結果不明 | 2/5 | 4/5 | 30 / 30 | 3 / 1 |

兩組都沒有安裝嘗試。樣本只涵蓋一個模型和固定的模擬起始狀態。
一組技能回合在解除對話框後讀取到文字未出現，還沒重新確認焦點就嘗試貼上。
發布版因而補明即使已回讀文字，也要另取得焦點證據。

針對此規則以 `7e77aa7001e4c8eecc18c70d9eadd391b290c2ce` 獨立重跑五組貼上配對。
無技能通過 1/5，有技能通過 5/5。重送嘗試由 4 次降至 0 次，工具呼叫由 31 次降至 25 次。
此外，從隔離目錄使用 Claude Code 原生 Skill 工具載入，得到 `NATIVE_SKILL_LISTED=True`，
工具呼叫名稱為 Skill，CLI 最終回傳 `is_error=false`。這次原生載入測試用於判讀 PATH 情境，未執行本機命令。
最終程式回歸輸出為 `Ran 83 tests in 44.527s`，`OK (skipped=1)`。

## 0.4.2 跨代理與 Impress 驗收（2026-11-13，台北）

測試技能基線：`e96e8f7996c883ab6060168a40a00f02f8aaf7d1`。測試宿主為本機 Windows。
以下區分工具輸出、模型答覆和應用程式畫面；公開資料只保留去識別摘要。

| 代理／入口 | 載入方式 | 觀察結果 |
|---|---|---|
| Codex 桌面會話 | 手動讀取 | Windows PowerShell 盤點 exit 0：PATH 未命中，已知位置與使用者開始功能表命中，一項系統登錄 SecurityException。結果 found-unverified。 |
| Codex CLI | 手動讀取 | 沙箱中初始化拒絕存取；正式執行的唯讀模式 exit 0。工具輸出確認 PATH 未命中、已知執行檔版本 26.2.6.1、使用者開始功能表有捷徑，但捷徑目標在工具環境中未找到。整體 found-unverified。 |
| Claude Code 2.1.295 | 手動讀取測試 | 預設 CLI 回報 ENOTFOUND；隔離設定的重試回報 Not logged in。沒有取得本輪盤點。 |
| Claude Desktop，Sonnet 5.5 | 技能摘錄與去識別證據 | 判為 found-unverified，分辨 PATH 漏查及登錄受阻，要求功能證據才升為 ready，明說無法獨立查核。未改模式與設定。 |
| WorkBuddy AI 5.9.4，Hy4 | 提交手動讀檔提示 | 新任務畫面確認提交；最後檢查仍在處理，沒有可驗證的讀檔或盤點工具結果。 |
| Hermes、Deep Code、其他入口 | 未測 | 載入說明不能視為本輪相容性證據。 |

### 真實 Impress 操作

先以視窗清單確認 Impress 實際程序為 soffice.bin。處理範本與提示對話框後，在 GUI 建立兩頁、
用 PowerPoint 2007–365 格式儲存，關閉後從 Impress 開啟對話框重開。
遇到貼上文字不符和首次重開路徑未正確輸入，先讀畫面再撤回／改用文字輸入，重開則選取實際檔案。
逐頁檢查顯示，另讀取 PPTX 內部 XML 核對兩頁及五段文字。檔案讀取使用共享唯讀模式，沒有改寫產物。

```text
SLIDES=2 BYTES=11318 SHA256=7315272654EEBC7EF6EBF5172D53AEA58FACC0B03251969E59E857EB2A5FBE63
```

### 程式回歸與代理對照

模態情境的評分要求觀察到彈窗、成功處理彈窗、重新確認焦點，再輸入並核對。
配對報表測試覆蓋缺樣本、受阻、重複證據、模型不一致及執行失敗。這些測試使用合成資料。
本輪沒有每情境五組有效代理配對，因此不報告有／無技能的改善幅度。

```text
Ran 78 tests in 41.697s
OK (skipped=1)
PASS: 15 Markdown files; metadata, local links, required text, size and Windows user-path check
PASS: discovery gates and Git recovery guide
```

受限環境首次執行 junction 測試時子程序提前失敗；正式本機執行環境重跑通過。
一項 PowerShell 5.1 驗證因執行原則跳過；PowerShell 7 有實際盤點輸出。合成回放為 3/3。

日期 2026-11-08。

## 0.4.1 WorkBuddy AI 第二輪唯讀審查

透過本機 WorkBuddy AI 應用提交只讀提示詞，請其檢查未提交差異並在暫存目錄重現。
它確認窄情境的 plan/execute 與版本門檻成立，另指出三個邊界：已有實際產物時 plan 被誤判無效、舊版 Python 被歸為一般輸入錯誤、無效相對 workdir 可能被前置重播檢查誤判為 blocked。
先新增三項回歸測試，實際得到三項失敗；調整檢查順序與錯誤分類後，補上既有產物不得被新任務覆寫的反向測試。
Python 3.10 的行為由同版本資訊模擬測試驗證，未在真正 Python 3.10 直譯器實測。

```text
Ran 64 tests in 37.819s
OK
PASS: 15 Markdown files; metadata, local links, required text, size and Windows user-path check
PASS: discovery gates and Git recovery guide
```

合成情境回放為 origin=synthetic、passed=3、total=3；`git diff --check` 結束碼為 0。

## WorkBuddy AI 對抗性審查後的修正

本機 WorkBuddy AI 只讀審查 run_task.py 與 video-review，並在暫存目錄重現兩項問題：
後續步驟可改寫先前已驗證輸出而仍回報 verified；`.runs/` 日誌未被 Git 忽略。
新增前者的回歸測試，修正前測試實際回報 `AssertionError: 0 != 1`，修正後在完成前重算所有宣告產物的 SHA256，不一致則 failed。
`.gitignore` 新增 `.runs/`，`git check-ignore -v .runs/demo/state.json` 顯示該規則生效。
video-review 補明程序驗證不能替代逐頁視覺與目標軟體驗收。

```text
Ran 59 tests in 31.811s
OK
PASS: 15 Markdown files; metadata, local links, required text, size and Windows user-path check
PASS: discovery gates and Git recovery guide
```

WorkBuddy 提出的空 outputs 語意及雜湊審閱對應仍需另行設計；逾時後代殘留未在該次隔離實測重現，不列為已證實缺陷。plan 模式與 Python 版本下限在 0.4.1 處理。

## 0.4.0 本機影片到簡報實測

瀏覽器搜尋「規則怪談之《午夜規則》」，核對 YouTube 影片 ID `_hZE9fkBjzA`、頻道及 26:28 片長。
取得英文自動字幕，覆蓋 00:00–26:25，並播放抽查多個時間點的畫面；未完整逐秒觀看，未評價全片聲音。
產出 8 頁可編輯 PPTX，LibreOffice Impress 實際開啟顯示 8 頁；命令列轉 PDF 後逐頁檢查版面。
第一次第 7 頁圖片在 Impress 預覽中缺失，改成完整文字觀察頁後重新輸出、渲染及檢查。
原始字幕、截圖、簡報及執行紀錄保留在本機文件資料夾，不納入公開儲存庫。

新執行器先輸出 `{"status": "plan-valid", "steps": 1}`，再對實際簡報回報：

```text
{"status": "verified", "steps": 1, "checkpoint": "...midnight-final-verification-01\\state.json"}
{"slides": 8, "bytes": 44686}
Ran 58 tests in 31.481s
OK
```

執行器僅驗證程序輸出與聲明的檔案；簡報內容仍需字幕依據、逐頁視覺檢查及目標軟體開啟驗收。

## 0.3.1 模態容器與動作結果

新增 2 個模態容器回歸測試，先重現同 window_id 的背景元素被錯誤放行，以及不完整 surface 資料未拒絕，修正後通過。
新增 8 個動作結果分類測試，區分元素驗證、任務後置條件、未知結果、安全重試及權限拒絕。

```text
Ran 53 tests in 20.818s
OK
```

將前次真實存檔回應交給 action_result.py，實際輸出：

```json
{"next_action":"observe-outcome","retry_allowed":false,"delivery":"delivered_unverified","task_complete":false}
```

本輪沒有新增 GUI 寫入或提升系統權限。模態修復以合成回歸資料驗證；結果分類器另使用已保存的真實工具回應。尚未完成每個動作自動接入的執行器或多應用實測。

## 獨立記事本文件實測

在新建文件完成一次真實「觀察→檢查→操作→驗證」及儲存、關閉、重開。
初次啟動因低完整性互動租約遭 PERM_DENIED；經宿主正式執行審批後成功。沒有修改 UAC 或系統原則，也不據此宣稱取得管理員權限。

編輯前，以完整新快照找到唯一文字欄位、核對本次程序與視窗、檢查 permissions，再產生實際 preflight JSON。
desktop_guard.py 回報 ready-for-dispatch 後才執行 set-value；結果 delivered_verified，另以 get value 回讀中文與箭頭字元一致。
儲存快捷鍵回報 delivered_unverified，因此重新觀察對話框而非重播。
首次存檔因正斜線路徑遭「檔案名稱無效」，改成 Windows 反斜線後成功。
其中一次錯誤讀檔後 PowerShell 仍印出 PASS；該輸出無效，改成 ErrorActionPreference=Stop 並重做存在與內容檢查。

最終真實驗收輸出：

```text
DISK_CONTENT_MATCH=PASS
REOPEN_UI_CONTENT_MATCH=PASS
SHA256=4DEB13FC3D0FF4B19A216EA2805994AFAB4748DEDA98A1A05DF3FDB734FB58B4
```

測試文件由記事本 GUI 寫入並儲存；腳本只建證據目錄、紀錄與唯讀核對，沒有直接生成文件內容。
本機保留 preflight、編輯／回讀結果、重開證據及截圖；公開專案只記去識別摘要，不上傳原始桌面資料。
這是單次有人監督的實測；只在主要文字寫入接入檢查器，儲存／關閉等步驟仍由代理依新快照逐步執行，尚不是所有動作自動整合或五次對照測試。

## 0.3.0 桌面控制驗證

新增 desktop_guard.py 及 13 個測試，涵蓋語意／實體輸入焦點、過期定位、錯誤視窗、唯一性、模態遮擋、送達不明、已完成動作、權限、使用者介入、不可操作目標、輸入型別、安全重試與 CLI 結束碼。
先執行缺少實作的測試，再完成檢查器；額外測試抓到 not-delivered 未要求 retry_safe 的缺口，修正後通過。

```text
Ran 43 tests in 21.755s
OK
PASS: 12 Markdown files; metadata, local links, required text, size and Windows user-path check
PASS: discovery gates and Git recovery guide
```

本機 agent-desktop status 與 permissions 回報 ok=true、accessibility.state=granted、automation.state=not_required。
list-windows 回報 ok=true 並取得視窗清單；app_name 有空字串，不能僅靠該欄位定位。
以上僅驗證可讀能力及工具回報，未測試提高權限後的寫入，也未修改任何系統權限。
桌面動作檢查器使用合成狀態；CLI 範例實際驗證 exit 0、3、2。
尚未整合自動派送，未做真實 GUI 操作的五次對照，不能由規則測試推論流暢度提升。
compileall 及 git diff --check 結束碼為 0。

## 0.2.1 驗證

新增兩個 CLI 的輸入邊界測試。修正前重複欄位及 NaN／Infinity 合計出現 8 個 subtest 失敗，因為工具錯誤地回傳 exit 0。
修正後完整測試輸出：

```text
Ran 30 tests in 23.907s
OK
```

測試包含重複欄位、非標準數值、深層 JSON、錯誤 UTF-8、超過 1 MiB 的資料。
深層 JSON 在目前 Python 原本即可回傳結構化錯誤；新增 RecursionError 處理支援其他 Python 執行環境可能的錯誤型別，尚未跨版本實測。
兩個入口改成有界讀取，避免先 stat 再完整讀檔之間的大小變動。
另嘗試 Windows PowerShell 5.1 實機執行，遭執行原則回報 UnauthorizedAccess；未變更原則，該版本功能仍未驗證。完整 30 項測試中的 Windows 盤點使用 PowerShell 7。

## 0.2.0 驗證

新增 Windows 只讀盤點、任務 JSON 檢查器、三個情境紀錄評分器。
測試先執行失敗，再補實作；另外以回歸案例重現並修復 Windows 反斜線個人路徑、README 壞連結，以及評分器沿用過期成功狀態的問題。

本機盤點結果：LibreOffice 在 PATH 未命中，但開始功能表找到候選捷徑；Git 在 PATH 找到執行檔。
部分系統安裝登錄遭 SecurityException，輸出保留 error。
兩者狀態均為 found-unverified，沒有以盤點結果宣稱功能可用。
未執行找到的軟體、安裝、登入或修改系統設定；公開紀錄排除原始私人路徑。

`python -m unittest discover -s tests -p "test_*.py"` 涵蓋 25 個測試：8 個封裝、3 個 Windows 實機盤點、8 個契約、6 個紀錄評分。
`python tests/evaluate_traces.py tests/fixtures/traces.json` 回放 3 個 synthetic 情境。
這些是程式與合成資料測試，不能宣稱有／無技能的代理效果提升。
子代理測試啟動因執行環境的模型名稱不受支援而失敗，未取得真實代理對照紀錄。
Windows 盤點於 PowerShell 7 實測；PowerShell 5.1 尚待實測。
本版沒有 npm build；Python 模組以 compileall 檢查語法，PowerShell 以實際執行測試驗證。

本輪實際輸出摘要：

```text
Ran 25 tests in 16.774s
OK
Skill is valid!
```

合成紀錄評分輸出為 origin=synthetic、passed=3、total=3。
compileall 與 git diff --check 的結束碼為 0。
官方驗證器首次離線查無 PyYAML、沙箱網路 DNS 失敗；經正式權限流程後使用 uv 隔離環境通過，未修改系統 Python。

## 靜態驗證

新增本機證據門檻測試後，舊版先出現 Missing discovery gate: 提交身分。
補上六層證據表及 Git 診斷指南後，tests/validate.py 通過。
skill-creator quick_validate.py 回報 Skill is valid!。
靜態檢查涵蓋 metadata、相對連結、必要規則、長度與私人路徑檢查。

## 本機實測

發現使用者已開啟名為 GitHub 的視窗，程序及畫面確認為 Chrome 網頁，且網頁已登入。
本機 Git 可執行。gh 尚未登入，目標儲存庫沒有提交作者設定。
檢查目前專案、有效全域及少量相關本機專案後，才請使用者提供姓名與 Email，並採專案區域設定。
紀錄保留判斷結果，排除私人身分與畫面。

官方驗證器缺少 PyYAML。先檢查本機 runtime 與 uv，使用 uv 隔離環境補足。
沙箱下載遇 DNS 錯誤，經正式權限流程後安裝一個套件並完成驗證。
沒有修改隨附 Python 的套件環境。

## 驗證界線

上述為本次 Windows 環境的實測。tests/scenarios.md 是回歸情境規格，尚未完成全套獨立代理測試。
跨平台說明尚未在 macOS 或 Linux 實機驗證。靜態規則通過不代表代理必然遵守每項行為。

## 封裝回歸測試

tests/test_package.py 使用暫存副本，測試正常封裝、遺失參考文件、錯誤 frontmatter、私人路徑、缺少發現規則，以及 Python -O 模式。
測試先揭露 assert 在 -O 下不執行的問題，改成明確錯誤檢查後六項測試通過。
這六項測試驗證封裝檢查器，與獨立代理的行為測試有不同的驗收範圍。
