## ADDED Requirements

### Requirement: PreCompact 保存 git status 快照
pre-compact.py SHALL 在上下文壓縮前，將 `git status --porcelain` 和 `git diff --stat` 的結果追加到當前 .tmp 檔。

#### Scenario: 有進行中的變更
- **WHEN** 壓縮觸發時工作目錄有未提交的變更
- **THEN** .tmp 檔追加一個壓縮快照區塊，包含時間戳、git status 和 diff stat

#### Scenario: 工作目錄乾淨
- **WHEN** 壓縮觸發時工作目錄乾淨
- **THEN** .tmp 檔追加壓縮快照區塊，標記「工作目錄 clean」

### Requirement: PreCompact 快照格式
追加的快照區塊 SHALL 使用以下格式，方便後續閱讀和解析：

#### Scenario: 快照格式
- **WHEN** 壓縮觸發
- **THEN** 追加內容格式為：
  ```
  ---
  **[Compaction at <HH:MM>]**
  工作目錄: <clean 或 N 個檔案有變更>
  <git diff --stat 輸出，最多 20 行>
  ```

### Requirement: PreCompact 保留 compaction-log.txt
pre-compact.py SHALL 繼續將壓縮事件記錄到 `compaction-log.txt`，維持現有行為。

#### Scenario: 寫入 compaction-log.txt
- **WHEN** 壓縮觸發
- **THEN** `~/.claude/sessions/compaction-log.txt` 追加一行 `[<datetime>] Context compaction triggered`

### Requirement: PreCompact 錯誤處理
git 指令失敗時 SHALL 靜默降級，不阻擋壓縮流程。

#### Scenario: git 指令失敗
- **WHEN** git status 或 git diff 執行失敗
- **THEN** 快照區塊中該部分顯示「[無法取得]」，壓縮正常進行
