# conflict-diff-view Specification

## Purpose

提供衝突檔案的差異查看功能，讓使用者在分發前能比較來源與目標的差異。

## Requirements

### Requirement: FileRecord 記錄來源路徑

`FileRecord` dataclass SHALL 包含 `source_path: Path | None` 欄位（預設 `None`），記錄資源的來源檔案或目錄路徑。`ManifestTracker` 的 `record_skill`、`record_command`、`record_agent`、`record_workflow` 方法 SHALL 接受 `source_path` 參數並儲存至 `FileRecord`。`source_path` 不寫入 manifest 檔案（僅供執行時使用）。

#### Scenario: record_skill 儲存 source_path
- **WHEN** 呼叫 `tracker.record_skill("my-skill", source_path=Path("/src/skills/my-skill"))`
- **THEN** `tracker.skills["my-skill"].source_path` 為 `Path("/src/skills/my-skill")`

#### Scenario: source_path 不影響 manifest 輸出
- **WHEN** 呼叫 `tracker.to_manifest()` 且 FileRecord 有 source_path
- **THEN** 產生的 manifest dict 中不包含 `source_path` 欄位

### Requirement: ConflictInfo 攜帶來源與目標路徑

`ConflictInfo` dataclass SHALL 包含 `source_path: Path | None` 和 `target_path: Path | None` 欄位（預設 `None`）。

#### Scenario: detect_conflicts 填入路徑
- **WHEN** `detect_conflicts()` 偵測到衝突
- **THEN** 回傳的 `ConflictInfo` 包含 `source_path`（來源檔案/目錄路徑）和 `target_path`（目標檔案/目錄路徑）

### Requirement: 互動選單包含查看差異選項

`prompt_conflict_action()` SHALL 顯示 5 個選項，順序為：強制覆蓋（1）、跳過（2）、備份後覆蓋（3）、查看差異（4）、取消分發（5）。選擇「查看差異」時回傳 `"diff"`。

#### Scenario: 使用者選擇查看差異
- **WHEN** 使用者在衝突選單中輸入 `4`
- **THEN** 函式回傳 `"diff"`

#### Scenario: 選項順序正確
- **WHEN** 顯示衝突處理選單
- **THEN** 選項依序為：1=強制覆蓋、2=跳過、3=備份後覆蓋、4=查看差異、5=取消分發

### Requirement: 顯示衝突差異

系統 SHALL 提供 `show_conflict_diff(conflicts)` 函式，對每個衝突項目顯示來源與目標之間的 diff 輸出。

#### Scenario: 單檔資源（commands/agents/workflows）的 diff
- **WHEN** 衝突資源為 commands 類型且 source_path 和 target_path 皆存在
- **THEN** 使用 `diff -u source_path target_path` 顯示 unified diff

#### Scenario: 目錄資源（skills）的 diff
- **WHEN** 衝突資源為 skills 類型且 source_path 和 target_path 皆存在
- **THEN** 使用 `diff -ruN source_path target_path` 顯示遞迴 unified diff

#### Scenario: diff 工具不存在
- **WHEN** 系統無 `diff` 指令
- **THEN** 顯示提示訊息「diff 工具未安裝，無法顯示差異」，不拋出例外

#### Scenario: 路徑為 None
- **WHEN** 衝突的 source_path 或 target_path 為 None
- **THEN** 顯示提示「無法取得路徑，跳過此項差異」

### Requirement: 查看差異後重新顯示選單

在分發流程中，選擇「查看差異」後 SHALL 顯示 diff 輸出，然後重新顯示衝突清單與選單，讓使用者選擇實際的處理方式。

#### Scenario: diff 後回到選單
- **WHEN** 使用者在衝突選單中選擇「查看差異」
- **THEN** 顯示所有衝突的 diff 輸出後，重新顯示 `display_conflicts()` 和 `prompt_conflict_action()`

#### Scenario: diff 後選擇覆蓋
- **WHEN** 使用者先選擇「查看差異」，再選擇「強制覆蓋」
- **THEN** 系統執行強制覆蓋，流程正常完成
