# 驗證紀錄

日期 2026-11-08。

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
