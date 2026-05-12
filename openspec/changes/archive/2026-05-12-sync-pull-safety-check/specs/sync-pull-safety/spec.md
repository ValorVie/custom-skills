## ADDED Requirements

### Requirement: 偵測本機未推送變更

系統 SHALL 提供 `detect_local_changes(config)` 函式，掃描所有同步目錄，回傳本機與 sync repo 之間的差異檔案清單。

- 對每個同步目錄比較本機路徑與 repo 子目錄
- 排除 ignore profile 中定義的檔案
- 回傳結構包含：每個目錄的變更檔案清單（新增、修改、刪除）與總變更數
- 變更類型：本機有但 repo 沒有（新增）、兩邊都有但內容不同（修改）、repo 有但本機沒有（刪除）

#### Scenario: 本機有未推送的修改

- **WHEN** 本機 `~/.claude/settings.json` 內容與 sync repo 中的 `claude/settings.json` 不同
- **THEN** 函式回傳的變更清單 SHALL 包含 `claude/settings.json` 且標記為 modified

#### Scenario: 本機有新增檔案

- **WHEN** 本機 `~/.claude/projects/new-project/CLAUDE.md` 存在但 sync repo 中不存在
- **THEN** 函式回傳的變更清單 SHALL 包含該檔案且標記為 added

#### Scenario: 本機與 repo 完全一致

- **WHEN** 所有同步目錄的檔案與 sync repo 完全一致
- **THEN** 函式回傳的總變更數 SHALL 為 0，變更清單為空

#### Scenario: 多目錄各有變更

- **WHEN** `~/.claude` 有 2 個修改檔案，`~/.claude-mem` 有 1 個修改檔案
- **THEN** 函式回傳的總變更數 SHALL 為 3，每個目錄的變更分別列出

---

### Requirement: 顯示變更摘要與互動式選項

系統 SHALL 在偵測到本機異動時，顯示變更檔案清單並提供三個選項。

- 顯示格式：「偵測到本機有 N 個檔案尚未推送」+ 檔案清單
- 檔案清單最多顯示 10 個，超過則顯示「...及其他 N 個檔案」
- 提供三個選項：
  1. 先 push 再 pull（推薦）
  2. 強制 pull（覆蓋本機變更）
  3. 取消
- 使用 `rich.prompt.Prompt` 或 `typer.prompt` 實作互動式輸入

#### Scenario: 少量變更時顯示完整清單

- **WHEN** 偵測到 3 個變更檔案
- **THEN** 系統 SHALL 顯示全部 3 個檔案路徑與三個選項

#### Scenario: 大量變更時截斷顯示

- **WHEN** 偵測到 15 個變更檔案
- **THEN** 系統 SHALL 顯示前 10 個檔案路徑，並附加「...及其他 5 個檔案」

#### Scenario: 使用者選擇先 push 再 pull

- **WHEN** 使用者選擇選項 1
- **THEN** 系統 SHALL 先執行完整的 push 流程（含 LFS 偵測、plugin manifest），push 成功後再執行 pull 流程

#### Scenario: 使用者選擇強制 pull

- **WHEN** 使用者選擇選項 2
- **THEN** 系統 SHALL 跳過安全檢查，直接執行原有的 pull 流程（覆蓋本機變更）

#### Scenario: 使用者選擇取消

- **WHEN** 使用者選擇選項 3
- **THEN** 系統 SHALL 顯示「已取消」並退出，不執行任何同步操作

---

### Requirement: push 失敗時中止 pull

當使用者選擇「先 push 再 pull」但 push 過程失敗時，系統 SHALL 中止整個操作。

- push 失敗時顯示錯誤訊息
- 不繼續執行 pull
- 提示使用者手動解決問題後重試

#### Scenario: push 因網路問題失敗

- **WHEN** 使用者選擇「先 push 再 pull」，但 `git push` 因網路問題失敗
- **THEN** 系統 SHALL 顯示 push 錯誤訊息並退出，不執行 pull

#### Scenario: push 因 rebase 衝突失敗

- **WHEN** 使用者選擇「先 push 再 pull」，但 `git pull --rebase` 產生衝突
- **THEN** 系統 SHALL 顯示衝突訊息並退出，提示使用者手動解決
