# 驗證紀錄

日期 2026-11-08。

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
