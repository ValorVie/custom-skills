## ADDED Requirements

### Requirement: SessionEnd 記錄 git 變更摘要
session-end.py 在會話結束時，SHALL 執行 `git diff --stat HEAD` 並將結果寫入 .tmp 檔的「Git 變更摘要」區塊。

#### Scenario: 有未提交的變更
- **WHEN** 工作目錄有未提交的變更
- **THEN** .tmp 檔包含 `## Git 變更摘要` 區塊，內容為 diff stat 輸出（最多 50 行）

#### Scenario: 工作目錄乾淨
- **WHEN** 工作目錄沒有未提交的變更
- **THEN** .tmp 檔的 `## Git 變更摘要` 區塊顯示「clean」

### Requirement: SessionEnd 記錄修改的檔案清單
session-end.py SHALL 執行 `git diff --name-status HEAD` 並將結果寫入 .tmp 檔的「修改的檔案」區塊。

#### Scenario: 有修改的檔案
- **WHEN** 工作目錄有修改、新增或刪除的檔案
- **THEN** .tmp 檔包含 `## 修改的檔案` 區塊，每行格式為 `- <檔案路徑> (<狀態>)`，狀態為新增/修改/刪除

#### Scenario: 無修改檔案
- **WHEN** 工作目錄沒有變更
- **THEN** `## 修改的檔案` 區塊顯示「無」

### Requirement: SessionEnd 記錄 commit 歷史
session-end.py SHALL 記錄本次會話期間產生的 commit，寫入 .tmp 檔的「Commit 記錄」區塊。

#### Scenario: 會話中有產生 commit
- **WHEN** 會話期間（從 Started 時間到現在）有新的 commit
- **THEN** .tmp 檔包含 `## Commit 記錄` 區塊，每行格式為 `- <hash> <message>`，最多 20 筆

#### Scenario: 會話中無 commit
- **WHEN** 會話期間沒有新的 commit
- **THEN** `## Commit 記錄` 區塊顯示「無」

### Requirement: SessionEnd 記錄專案名稱
session-end.py SHALL 透過 `git rev-parse --show-toplevel` 或目錄名稱取得專案名稱，寫入 .tmp 檔標頭。

#### Scenario: 在 git 專案中
- **WHEN** 當前目錄是 git 倉庫
- **THEN** .tmp 檔標頭包含 `**Project:** <專案名稱>`

#### Scenario: 非 git 專案
- **WHEN** 當前目錄不是 git 倉庫
- **THEN** .tmp 檔標頭包含 `**Project:** (非 git 專案)`，git 相關區塊顯示「不適用」

### Requirement: SessionEnd 記錄工作目錄狀態
session-end.py SHALL 執行 `git status --porcelain` 並將結果寫入 .tmp 檔的「工作目錄狀態」區塊。

#### Scenario: 乾淨的工作目錄
- **WHEN** `git status --porcelain` 輸出為空
- **THEN** `## 工作目錄狀態` 區塊顯示「clean」

#### Scenario: 有未追蹤或未暫存的變更
- **WHEN** `git status --porcelain` 有輸出
- **THEN** `## 工作目錄狀態` 區塊列出每個檔案的狀態

### Requirement: SessionEnd 錯誤處理
每個 git 指令的執行 SHALL 獨立用 try/except 包裹，單一指令失敗不影響其他區塊的記錄。腳本整體失敗時 SHALL 以 exit code 0 結束，不阻擋 Claude Code。

#### Scenario: git 指令超時
- **WHEN** 某個 git 指令執行超過 5 秒
- **THEN** 該區塊顯示「[超時]」，其他區塊正常記錄

#### Scenario: git 未安裝
- **WHEN** 系統中沒有 git 指令
- **THEN** 所有 git 相關區塊顯示「[git 未安裝]」，腳本仍以 exit code 0 結束
