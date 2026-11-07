# GitHub 發布

1. 執行 python tests/validate.py。
2. 檢查所有待提交檔案與差異，確認沒有機密或本機日誌。
3. 本專案已採 MIT，發布時包含 LICENSE。
4. 建立 GitHub 儲存庫，決定名稱及公開／私人可見性。
5. 在此專案目錄執行 git init，提交已審查檔案，設定自己的 remote 並推送。
6. 確認 GitHub 顯示 SKILL.md、相對連結與安裝說明。

範例命令，OWNER 與 REPO 需替換成實際目標。

```sh
git init
git add README.md LICENSE skills tests docs .gitignore
git commit -m "Add local-first project execution skill"
git remote add origin https://github.com/OWNER/REPO.git
git push -u origin HEAD
```

如已加入 LICENSE，將它一同提交。若已有 Git 儲存庫，沿用既有分支及 remote，先檢查狀態。

發布遇到作者或認證錯誤時，先依 skills/local-first-project/references/git.md 診斷。
本機提交身分、瀏覽器 session 與 gh 認證分開驗證。缺少一項時繼續完成不依賴該項的工作。
