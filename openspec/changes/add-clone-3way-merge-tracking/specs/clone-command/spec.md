## ADDED Requirements

### Requirement: clone 啟動時輸出 per-source update summary

`ai-dev clone` 進入檔案分發前 SHALL 對每個來源 repo（custom-skills、qdm-ai-tools 與 `repos.yaml` 內其他 custom repos、ECC）逐一輸出一行摘要，內容包含：上次 sync commit、本次 commit、來源變動檔數、影響本次 target 檔數、影響其他 target 檔數。

Summary SHALL **不**受 `--target` 旗標限制，永遠列出所有來源。

#### Scenario: 來源未變
- **GIVEN** 某來源 repo 任一 target manifest 中 `last_sync_commit_by_source[source]` 等於當前 `git rev-parse HEAD`
- **WHEN** 執行 `ai-dev clone`
- **THEN** summary 對應該來源的行 SHALL 顯示「未變更」、不顯示變動檔數

#### Scenario: 來源已更新且影響本次 target
- **GIVEN** 某來源 commit 從 `abc1234` 變為 `def5678`，期間 12 個檔案變動
- **AND** 其中 3 個檔案會被分發到本次 target、9 個會被分發到其他 target
- **WHEN** 執行 `ai-dev clone --target claude`
- **THEN** summary 對應該來源的行 SHALL 包含 commit 變動「abc1234 → def5678」、檔案變動「12」、影響本次 target「3」、影響其他 target「9」（後者以 dim 樣式顯示）

#### Scenario: --target 不縮減 summary 範圍
- **WHEN** 執行 `ai-dev clone --target claude` 而其他 target 對應的來源仍有變動
- **THEN** summary SHALL 仍列出該來源；`--target` 僅縮減實際分發迴圈

#### Scenario: 首次同步
- **GIVEN** 某 source 在所有 target manifest 內皆無 `last_sync_commit_by_source` 紀錄
- **WHEN** 執行 `ai-dev clone`
- **THEN** summary 該行 SHALL 顯示「首次同步」、不嘗試計算變動檔數

### Requirement: clone 採用 file-level 3-way 衝突分派

`copy_custom_skills_to_targets` 對每個 (resource_type, name, rel-path) SHALL 依以下分類處理：

| 條件 | 分類 | 行為 |
|------|------|------|
| manifest 無對應 `FileEntry` 或 base 失效 | `no-base` | 退回 v1 batch 行為（force / skip_conflicts / `prompt_conflict_action` 互動） |
| `dst_hash == file_entry.dst_hash_at_sync` 且 `src_hash != file_entry.src_hash` | `clean` | 自動以 src 覆蓋、更新 base、無 prompt |
| `src_hash == file_entry.src_hash` 且 `dst_hash != file_entry.dst_hash_at_sync` | `local-only` | 不寫 dst、輸出一行 `=` 提示、保留現有 base、被 `skipped` 記憶命中時行為相同 |
| 其他（兩邊皆動，且不在 skipped 記憶內） | `both-changed` | 進入 per-file prompt（spec：conflict-diff-view） |

`--force` SHALL 將所有分類視同 `clean` 處理（覆蓋並更新 base），不顯示 prompt。
`--skip-conflicts` SHALL 對 `both-changed` 自動寫 skip 記憶並跳過；`clean` / `local-only` 不受影響。
`--backup` SHALL 在覆蓋 `both-changed` 與 `no-base` 前備份原 dst；`clean` 不備份。

#### Scenario: clean 自動套用
- **GIVEN** 某 dst file hash 等於 base.dst_hash_at_sync、src hash 與 base.src_hash 不同
- **WHEN** 執行 `ai-dev clone`
- **THEN** 系統 SHALL 將 src 寫入 dst、不顯示 prompt、manifest 對應 `FileEntry` 的 src_hash / src_commit / dst_hash_at_sync / decision 同步更新為本輪實際值

#### Scenario: local-only 靜默保留
- **GIVEN** 某 file 的 src hash 等於 base.src_hash、dst hash 與 base.dst_hash_at_sync 不同
- **WHEN** 執行 `ai-dev clone`
- **THEN** dst 不被改寫、console SHALL 輸出 `= <skill>/<rel>（本地已修改、來源未變）` 一行、manifest 不變

#### Scenario: both-changed 進 per-file prompt
- **GIVEN** 某 file src 與 dst 皆與 base 不同、(rel, src_commit) 未命中 skipped 記憶
- **WHEN** 執行 `ai-dev clone`
- **THEN** 系統 SHALL 呼叫 `prompt_file_decision()` 進入 per-file 互動

#### Scenario: skipped 記憶命中視同 local-only
- **GIVEN** `files.skills.<skill>.skipped[<rel>].src_commit` 等於當前 src_commit
- **WHEN** 執行 `ai-dev clone`
- **THEN** 系統 SHALL 不 prompt、不寫 dst、行為視同 local-only

#### Scenario: no-base 退回 batch 行為
- **GIVEN** 某 file 在 manifest 內無 FileEntry（如全新檔案、首次跑 v2 後尚未標 base）
- **WHEN** 執行 `ai-dev clone` 且 src 與 dst 不同
- **THEN** 系統 SHALL 走 v1 batch 路徑（依 `--force` / `--skip-conflicts` / 互動 `prompt_conflict_action`）

#### Scenario: --force 全部覆蓋並寫 base
- **WHEN** 執行 `ai-dev clone --force`
- **THEN** 所有 file 不論分類 SHALL 被 src 覆蓋、manifest FileEntry 同步更新、無互動 prompt

#### Scenario: --skip-conflicts 僅影響 both-changed
- **GIVEN** 一個 `clean` file 與一個 `both-changed` file
- **WHEN** 執行 `ai-dev clone --skip-conflicts`
- **THEN** `clean` file SHALL 自動套用、`both-changed` file SHALL 被跳過並寫 skip 記憶

### Requirement: clone 在分發後寫回 manifest

每次 clone 結束時，系統 SHALL 將本輪每筆寫入或保留的決定同步到 manifest：

- 對 `clean` / `overwritten` / `accepted`：寫入 `FileEntry`，欄位反映本輪實際值。
- 對 `local-only`：保留既有 `FileEntry` 不變。
- 對 `skipped`：寫 `skipped[<rel>] = { src_commit, decided_at }`，保留既有 `FileEntry` 不變。
- Manifest root 的 `last_sync_commit_by_source[source]` SHALL 更新為該 source 當前 `git rev-parse HEAD`（即使所有 file 皆 local-only）。
- Manifest 寫入失敗 SHALL 不影響 dst（dst 已寫入），並在 console 印錯誤。

#### Scenario: 寫回 file entry
- **WHEN** 一個 dst 檔案被覆蓋（無論分類為 `clean` 或 prompt 後 `O`）
- **THEN** manifest 對應 `FileEntry` 的 `src_hash`、`src_commit`、`dst_hash_at_sync`、`decision`、`decided_at` 為本輪實際值

#### Scenario: 更新 last_sync_commit_by_source
- **WHEN** clone 結束
- **THEN** `last_sync_commit_by_source[source]` SHALL 等於該 source 當前 `git rev-parse HEAD`

### Requirement: 兼容 v1 reader fallback

`read_manifest()` 讀取 `schema_version: 2` 時，仍 SHALL 提供使呼叫端能取得 v1 結構的 helper（`v2_to_v1_view(m)`），以維持 install / sync / update_custom_repo 等指令的 reader 不需立即改寫。

#### Scenario: v2 manifest 提供 v1 view
- **GIVEN** `schema_version: 2` 的 manifest
- **WHEN** 呼叫 `v2_to_v1_view(m)`
- **THEN** 回傳 dict 結構與 v1 相同（`files.<resource>.<name>.hash` / `source`），其他 v2 專屬欄位不出現
