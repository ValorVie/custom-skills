## ADDED Requirements

### Requirement: clone 啟動時輸出 per-source update summary

`ai-dev clone` 進入檔案分發迴圈前 SHALL 對每個來源 repo（custom-skills、qdm-ai-tools、ecc）逐一輸出一行摘要，內容包含：上次 sync commit、本次 commit、來源變動檔數、影響本次 target 檔數、影響其他 target 檔數。Summary SHALL 不受 `--target` 旗標限制，永遠列出所有來源。

#### Scenario: 來源未變
- **GIVEN** 某來源 repo 的 `last_sync_commit_by_source[source]` 等於當前 `git rev-parse HEAD`
- **WHEN** 執行 `ai-dev clone`
- **THEN** summary 對應該來源的行 SHALL 顯示 `未變更`、不顯示變動檔數

#### Scenario: 來源已更新且影響本次 target
- **GIVEN** 來源 commit 從 `abc1234` 變為 `def5678`，期間有 12 個檔案變動
- **AND** 其中 3 個檔案會被分發到本次 target（如 claude）
- **AND** 9 個檔案會被分發到其他 target
- **WHEN** 執行 `ai-dev clone --target claude`
- **THEN** summary 對應該來源的行 SHALL 包含「abc1234 → def5678」、檔案變動「12」、影響本次 target「3」、影響其他 target「9」（後者以 dim 樣式顯示）

#### Scenario: --target 不縮減 summary 範圍
- **WHEN** 執行 `ai-dev clone --target claude` 而非 codex 來源仍有變動
- **THEN** summary SHALL 仍列出 codex 相關來源資訊；只有實際分發迴圈受 `--target` 限制

#### Scenario: 來源 commit 不存在 last_sync 紀錄
- **GIVEN** 某來源從未被 ai-dev 同步過（last_sync_commit_by_source 內無此 source）
- **WHEN** 執行 `ai-dev clone`
- **THEN** summary 該行 SHALL 顯示「首次同步」、不嘗試計算變動檔數

### Requirement: clone 採用 3-way 衝突分類分派

`ai-dev clone` 對每個 dst 檔案 SHALL 依以下分類處理：

| 條件 | 分類 | 行為 |
|------|------|------|
| manifest 無對應 entry | `no-base` | 退回現行 `merge_file()` 行為（force / skip_conflicts / 互動 prompt） |
| `dst_hash == base.dst_hash_at_sync` 且 `src_hash != base.src_hash` | `clean` | 自動以 src 覆蓋 dst、更新 base、不顯示 prompt |
| `src_hash == base.src_hash` 且 `dst_hash != base.dst_hash_at_sync` | `local-only` | 不寫入 dst、輸出一行 `=` 提示、保留現有 base |
| 其他（兩邊皆動） | `both-changed` | 進入互動 prompt（含三向 diff UI） |

`--force` 旗標 SHALL 覆蓋上述分類為一律覆蓋，但仍 MUST 寫入 base 紀錄；`--skip-conflicts` 旗標 SHALL 將 `both-changed` 轉為 skip 行為，但 `clean` / `local-only` 不受影響。

#### Scenario: clean 自動套用
- **GIVEN** dst_hash 等於 base.dst_hash_at_sync、src_hash 與 base.src_hash 不同
- **WHEN** 執行 `ai-dev clone`
- **THEN** 系統 SHALL 將 src 寫入 dst、不顯示 prompt、manifest 該 entry 的 src_hash / src_commit / dst_hash_at_sync 同步更新

#### Scenario: local-only 靜默保留
- **GIVEN** src_hash 等於 base.src_hash、dst_hash 與 base.dst_hash_at_sync 不同
- **WHEN** 執行 `ai-dev clone`
- **THEN** dst 不被改寫、console SHALL 輸出 `= <relative-path> (本地已修改、來源未變)` 一行、manifest 不變

#### Scenario: both-changed 進 prompt
- **GIVEN** src_hash != base.src_hash 且 dst_hash != base.dst_hash_at_sync
- **WHEN** 執行 `ai-dev clone`
- **THEN** 系統 SHALL 進入互動 prompt 並顯示三向 diff 摘要

#### Scenario: no-base 退回原行為
- **GIVEN** manifest 不含對應 entry
- **WHEN** 執行 `ai-dev clone` 且 src 與 dst 不同
- **THEN** 系統 SHALL 走 v1 邏輯（`force` / `skip_conflicts` / 互動 prompt）

#### Scenario: --force 覆蓋分類
- **GIVEN** 任意分類
- **WHEN** 執行 `ai-dev clone --force`
- **THEN** 系統 SHALL 覆蓋 dst 並寫入 base，無互動 prompt

#### Scenario: --skip-conflicts 僅影響 both-changed
- **GIVEN** 一個 `clean` 檔案與一個 `both-changed` 檔案
- **WHEN** 執行 `ai-dev clone --skip-conflicts`
- **THEN** `clean` 檔案 SHALL 自動套用、`both-changed` 檔案 SHALL 被跳過並寫入 skip 記憶

### Requirement: clone 在分發後寫回 manifest

每次 clone 結束時，系統 SHALL 將本輪所有 `accepted` / `overwritten` / `appended` / `incremental` 結果寫入 manifest 對應 `FileEntry`，並更新 root 的 `last_sync_commit_by_source[source]` 為各來源當前 `git rev-parse HEAD`。

#### Scenario: 寫回 file entry
- **WHEN** 一個 dst 檔案被覆蓋（無論分類為 `clean` 或 prompt 後 `overwrite`）
- **THEN** manifest 對應 `FileEntry` 的 `src_hash`、`src_commit`、`dst_hash_at_sync`、`decision`、`decided_at` 應為本輪實際值

#### Scenario: 更新 last_sync_commit_by_source
- **WHEN** clone 結束（無論是否所有檔案都被處理）
- **THEN** `last_sync_commit_by_source[source]` SHALL 等於該 source 當前 `git rev-parse HEAD`
