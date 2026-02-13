## ADDED Requirements

### Requirement: sync init 子指令初始化同步環境

系統 SHALL 提供 `ai-dev sync init --remote <git-url>` 子指令，建立本機同步 repo 並連接遠端。

- 接受 `--remote` 參數指定 Git remote URL（必填）
- 在 `~/.config/ai-dev/sync-repo/` 建立或 clone Git repo
- 為每個預設同步目錄（`~/.claude`、`~/.claude-mem`）建立 repo 內子目錄
- 根據 ignore profiles 產生 `.gitignore` 和 `.gitattributes`
- 執行首次檔案同步（本機 → repo）
- 執行首次 commit 並 push 到遠端
- 儲存設定到 `~/.config/ai-dev/sync.yaml`
- 若遠端已有內容，SHALL clone 並合併本機檔案

#### Scenario: 全新初始化

- **WHEN** 使用者執行 `ai-dev sync init --remote git@github.com:user/sync.git`，且本機尚無 sync-repo
- **THEN** 系統建立 `~/.config/ai-dev/sync-repo/`，初始化 Git repo，建立 `claude/` 和 `claude-mem/` 子目錄，同步本機檔案，commit 並 push

#### Scenario: 從既有遠端初始化

- **WHEN** 使用者執行 `ai-dev sync init --remote <url>`，且遠端 repo 已有內容
- **THEN** 系統 clone 遠端 repo 到 `~/.config/ai-dev/sync-repo/`，並將 repo 內容同步到本機目錄

#### Scenario: 已初始化時重複執行

- **WHEN** 使用者執行 `ai-dev sync init`，但 `sync.yaml` 已存在
- **THEN** 系統提示已初始化，詢問是否重新初始化（覆蓋設定）

#### Scenario: Git 不可用

- **WHEN** 使用者執行 `ai-dev sync init`，但系統未安裝 Git
- **THEN** 系統顯示錯誤訊息並提示安裝 Git

---

### Requirement: sync push 子指令推送本機變更

系統 SHALL 提供 `ai-dev sync push` 子指令，將本機變更推送到遠端 repo。

- 讀取 `sync.yaml` 取得同步目錄清單
- 對每個目錄執行檔案同步（本機 → repo 子目錄）
- 排除 ignore profile 中定義的檔案
- 執行 `git add -A`、`git commit`、`git pull --rebase`、`git push`
- Commit message 格式：`sync: <hostname> <timestamp>`
- 顯示同步結果摘要（新增/修改/刪除檔案數）

#### Scenario: 正常推送

- **WHEN** 使用者執行 `ai-dev sync push`，且本機有變更
- **THEN** 系統將變更同步到 repo，commit 並 push，顯示變更摘要

#### Scenario: 無變更時推送

- **WHEN** 使用者執行 `ai-dev sync push`，但本機與 repo 內容一致
- **THEN** 系統顯示「無變更需要同步」

#### Scenario: 遠端有新 commit

- **WHEN** 使用者執行 `ai-dev sync push`，且遠端有本機未拉取的 commit
- **THEN** 系統先執行 `git pull --rebase`，再 push 本機變更

#### Scenario: 未初始化時推送

- **WHEN** 使用者執行 `ai-dev sync push`，但尚未執行 `sync init`
- **THEN** 系統顯示錯誤訊息並提示先執行 `ai-dev sync init`

---

### Requirement: sync pull 子指令拉取遠端變更

系統 SHALL 提供 `ai-dev sync pull` 子指令，從遠端 repo 拉取變更到本機。

- 執行 `git pull --rebase`
- 對每個目錄執行檔案同步（repo 子目錄 → 本機）
- 提供 `--no-delete` 選項，防止刪除本機有但 repo 沒有的檔案
- 顯示同步結果摘要

#### Scenario: 正常拉取

- **WHEN** 使用者執行 `ai-dev sync pull`，且遠端有新變更
- **THEN** 系統拉取遠端變更並同步到本機目錄，顯示變更摘要

#### Scenario: 無遠端變更

- **WHEN** 使用者執行 `ai-dev sync pull`，但遠端無新 commit
- **THEN** 系統顯示「已是最新狀態」

#### Scenario: 使用 --no-delete 選項

- **WHEN** 使用者執行 `ai-dev sync pull --no-delete`
- **THEN** 系統拉取遠端變更但不刪除本機多出的檔案

---

### Requirement: sync status 子指令顯示同步狀態

系統 SHALL 提供 `ai-dev sync status` 子指令，以 Rich 表格顯示各同步目錄的狀態。

- 顯示每個目錄的：本機變更檔案數、遠端狀態（最新/落後 N commits）、最後同步時間
- 使用 Rich Table 格式化輸出

#### Scenario: 顯示同步狀態

- **WHEN** 使用者執行 `ai-dev sync status`
- **THEN** 系統以表格顯示所有同步目錄的本機變更數、遠端狀態和最後同步時間

#### Scenario: 未初始化時查看狀態

- **WHEN** 使用者執行 `ai-dev sync status`，但尚未初始化
- **THEN** 系統顯示「尚未初始化，請先執行 ai-dev sync init」

---

### Requirement: sync add 子指令新增同步目錄

系統 SHALL 提供 `ai-dev sync add <path>` 子指令，將新目錄加入同步清單。

- 接受目錄路徑作為參數
- 提供 `--profile` 選項指定 ignore profile（預設為 `custom`）
- 提供 `--ignore` 選項指定自訂排除模式（可多次使用）
- 驗證路徑存在且為目錄
- 新增到 `sync.yaml`
- 在 sync-repo 中建立對應子目錄
- 更新 `.gitignore`

#### Scenario: 新增自訂目錄

- **WHEN** 使用者執行 `ai-dev sync add ~/.gemini --ignore "cache/" --ignore "*.log"`
- **THEN** 系統將 `~/.gemini` 加入同步清單，建立 repo 子目錄，更新 `.gitignore`

#### Scenario: 路徑不存在

- **WHEN** 使用者執行 `ai-dev sync add /nonexistent`
- **THEN** 系統顯示錯誤「目錄不存在」

#### Scenario: 重複新增

- **WHEN** 使用者執行 `ai-dev sync add ~/.claude`，但該目錄已在同步清單中
- **THEN** 系統顯示提示「該目錄已在同步清單中」

---

### Requirement: sync remove 子指令移除同步目錄

系統 SHALL 提供 `ai-dev sync remove <path>` 子指令，從同步清單移除目錄。

- 從 `sync.yaml` 移除該目錄
- 詢問是否也從 repo 中刪除對應子目錄
- 更新 `.gitignore`
- 不可移除最後一個目錄

#### Scenario: 移除自訂目錄

- **WHEN** 使用者執行 `ai-dev sync remove ~/.gemini`
- **THEN** 系統從設定中移除，詢問是否刪除 repo 中的 `gemini/` 子目錄

#### Scenario: 移除不存在的目錄

- **WHEN** 使用者執行 `ai-dev sync remove /not-tracked`
- **THEN** 系統顯示錯誤「該目錄不在同步清單中」
