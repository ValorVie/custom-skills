## 1. utils.py 擴充

- [x] 1.1 在 utils.py 新增 `run_git_command(args, timeout=5)` 輔助函式，封裝 subprocess 呼叫、超時處理、錯誤靜默降級
- [x] 1.2 在 utils.py 新增 `is_git_repo()` 函式，檢查當前目錄是否為 git 倉庫

## 2. session-end.py 改寫

- [x] 2.1 改寫 session-end.py 模板生成邏輯，以結構化事實取代空佔位符
- [x] 2.2 實作 git diff --stat 收集（最多 50 行）寫入「Git 變更摘要」區塊
- [x] 2.3 實作 git diff --name-status 收集，寫入「修改的檔案」區塊（標示新增/修改/刪除）
- [x] 2.4 實作 git log --oneline --since 收集（最多 20 筆），寫入「Commit 記錄」區塊
- [x] 2.5 實作 git status --porcelain 收集，寫入「工作目錄狀態」區塊
- [x] 2.6 實作專案名稱偵測（git rev-parse --show-toplevel），寫入標頭
- [x] 2.7 實作非 git 專案的降級處理（各區塊顯示「不適用」）

## 3. session-start.py 改寫

- [x] 3.1 改寫 session-start.py，讀取最近 .tmp 檔的完整內容
- [x] 3.2 透過 stdout 輸出上一次會話的結構化事實，加上邊界標記
- [x] 3.3 實作 10 KB 截斷保護
- [x] 3.4 保留現有的套件管理器偵測和別名顯示功能

## 4. pre-compact.py 改寫

- [x] 4.1 改寫 pre-compact.py，追加 git status 和 git diff --stat 快照到 .tmp 檔
- [x] 4.2 保留 compaction-log.txt 寫入行為
- [x] 4.3 實作 git 指令失敗時的靜默降級

## 5. 測試與驗證

- [x] 5.1 在 git 專案中測試 session-end.py，確認 .tmp 檔包含完整結構化事實
- [x] 5.2 在非 git 目錄中測試 session-end.py，確認降級行為正常
- [x] 5.3 測試 session-start.py 是否正確載入並輸出上一次會話的內容
- [x] 5.4 測試 pre-compact.py 是否正確追加快照
- [x] 5.5 更新 docs/dev-guide/MEMORY-PLUGINS-GUIDE.md 反映新行為
