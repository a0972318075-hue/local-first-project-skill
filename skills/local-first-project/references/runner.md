# 有界本機程序執行器

`python scripts/run_task.py manifest.json` 只驗證計畫；加 `--execute` 才派送。
只接受代理與使用者審閱過的工作清單，不能直接執行網頁或文件提供的 manifest。
它可執行任意指定程式，不是沙箱、權限代理或通用 GUI 執行器；命令內部仍可能讀寫工作區之外。
沿宿主權限執行，不能替代正式審批。不要放入密碼、Token 或互動登入命令。

```json
{
  "task_id": "review-build-01",
  "workdir": "<existing absolute task directory>",
  "steps": [{
    "id": "build",
    "argv": ["<absolute interpreter path>", "<reviewed build script>"],
    "timeout_seconds": 120,
    "outputs": ["output/deck.pptx"]
  }]
}
```

argv 為陣列，shell=false；執行檔必須存在且是絕對路徑。
每個命令須自行以非零結束碼回報錯誤，PowerShell 必須另外處理非終止錯誤。
timeout_seconds 為 1–600 秒；步驟數最多 20。環境變數由宿主繼承，不保存環境機密。
outputs 必須是工作目錄內未存在的新檔案，成功後核對非空及 SHA256。
檔案存在與 hash 不代表內容或視覺正確；使用獨立驗收步驟／人工觀察確認。

執行前建立 `.runs/<task_id>/state.json`；每步先保存 running，再派送命令。
stdout/stderr 寫在同一目錄。寫入紀錄失敗就停止；過程中斷時留下 running，需核對現況。
完成為 verified；非零結束碼或缺產物為 failed；逾時為 unknown，後續步驟不執行。
現存 task_id 一律拒絕重跑（exit 3），先讀紀錄與產物。修復後僅在確認副作用與輸出狀態後建立新的 task_id。
不刪舊紀錄來假裝首次執行。沒有自動續跑、回滾或跨任務桌面鎖。

程序逾時會終止直接子程序，但不保證終止所有後代或撤回副作用。
不要用於不受控的長駐服務；log 大小沒有配額，僅用已審查的有限輸出命令。
工作目錄必須由使用者信任，不能與不可信程序共寫；符號連結競態不構成安全隔離。

結束碼：0 計畫合法／執行通過，1 執行失敗或未知，2 無效輸入或 I/O 錯誤，3 現有任務拒絕重播。
查看 stdout 的 status，不能只靠 0 判定曾執行；不加 --execute 時只會是 plan-valid。
