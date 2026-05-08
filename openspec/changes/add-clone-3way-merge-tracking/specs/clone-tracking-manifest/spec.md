## ADDED Requirements

### Requirement: Manifest Schema v2 結構

`~/.config/ai-dev/manifests/<target>.yaml` SHALL 支援 `schema_version: 2`。當 `schema_version` 為 `2` 時，`files.skills.<skill-name>` 的結構 SHALL 為：

```yaml
files.skills.<skill-name>:
  files:
    <relative-path>:
      src_hash: sha256:<64-hex>
      src_commit: <40-hex git commit>
      src_source: custom-skills | qdm-ai-tools | ecc
      dst_hash_at_sync: sha256:<64-hex>
      decision: accepted | skipped | overwritten | appended | incremental
      decided_at: <ISO 8601 timestamp>
  skipped:
    <relative-path>:
      src_commit: <40-hex>
      decided_at: <ISO 8601 timestamp>
```

Manifest root SHALL 額外包含 `last_sync_commit_by_source: { <source-name>: <40-hex> }`。

#### Scenario: schema_version 缺失視為 v1
- **WHEN** 讀取的 manifest 不含 `schema_version` 欄位
- **THEN** 系統 MUST 視為 v1 並觸發 migration 流程

#### Scenario: schema_version 為 2 時讀取 file-level entry
- **WHEN** `schema_version: 2` 且呼叫 `get_file_entry(target, source, rel_path)`
- **THEN** 系統 SHALL 回傳對應 `FileEntry` dataclass，欄位齊全

#### Scenario: 寫入 file entry 後 schema_version 保持為 2
- **WHEN** 呼叫 `record_file_decision(target, source, rel_path, decision)` 寫入新紀錄
- **THEN** manifest root 的 `schema_version` 維持 `2`、`files.skills.<skill>.files.<rel_path>` 內含寫入的欄位、`last_sync_commit_by_source[source]` 同步更新為當前 src_commit

### Requirement: v1 → v2 Migration（保守標 base）

當讀取到 v1 manifest 時，系統 SHALL 執行 migration：

1. 對每個既有 `<skill>.hash` 對應的 dst 檔案，計算當前 `dst_hash`。
2. 若 `dst_hash == <skill>.hash` 中對應的內容（即 dst 與 v1 紀錄的 src 內容相同），系統 SHALL 寫入 `FileEntry` 將 `src_hash`、`dst_hash_at_sync` 設為 `dst_hash`，`src_commit` 取自對應 source repo 在 `last_sync` 時間點的 `git rev-list -1 --before=<last_sync> <branch>`，`decision = accepted`。
3. 若不一致或無法取得 commit，該 entry SHALL 留白（不寫入 `FileEntry`），下次比對視為 `no-base`。
4. Migration 結束後 SHALL 寫入 `schema_version: 2`，並 SHALL 將原 v1 manifest 備份到 `~/.config/ai-dev/manifests/.backup-v1/<target>.yaml.<ISO-timestamp>`。
5. Migration SHALL idempotent：對已是 v2 的 manifest 執行 migration MUST 為 no-op。

#### Scenario: dst==src 自動標 base
- **GIVEN** v1 manifest 中 `<skill>.hash` 為 `sha256:abc`
- **AND** 對應 dst 檔案的 sha256 也是 `sha256:abc`
- **WHEN** 觸發 migration
- **THEN** v2 manifest 該 entry 的 `decision` SHALL 為 `accepted`、`src_hash` 與 `dst_hash_at_sync` 皆為 `sha256:abc`

#### Scenario: dst!=src 不自動標 base
- **GIVEN** v1 manifest 中 `<skill>.hash` 為 `sha256:abc`
- **AND** 對應 dst 檔案的 sha256 為 `sha256:xyz`
- **WHEN** 觸發 migration
- **THEN** v2 manifest 該 rel_path 不應有 `FileEntry`，視為 `no-base`

#### Scenario: 備份成功
- **WHEN** Migration 結束
- **THEN** `~/.config/ai-dev/manifests/.backup-v1/` 下存在帶時間戳的 v1 副本

#### Scenario: Migration idempotent
- **WHEN** 對 schema_version 已為 2 的 manifest 再次執行 migration
- **THEN** manifest 內容不變、不產生新備份檔

### Requirement: Skip 記憶以 (file, src_commit) 為 key

當使用者於 prompt 選擇 skip 時，系統 SHALL 寫入 `files.skills.<skill>.skipped[<rel-path>] = { src_commit: <current-src-commit>, decided_at: <now> }`。

於下一輪 clone 進入分類前，系統 MUST 先比對：

- 若 `(rel-path, current-src-commit)` 命中既有 skipped 紀錄 → 視為 `local-only`、不進 prompt。
- 若 src_commit 與 skipped 紀錄不同 → 系統 SHALL 移除該筆 skipped，依分類邏輯處理（多半為 `both-changed`）。

#### Scenario: 寫入 skip 記憶
- **WHEN** 使用者於 prompt 選擇 `S`
- **THEN** manifest 的 `files.skills.<skill>.skipped[<rel-path>].src_commit` 等於當前 src_commit、`decided_at` 為當前時間

#### Scenario: 同一 src_commit 不再提示
- **GIVEN** skipped 紀錄存在，src_commit 為 `abc`
- **WHEN** 下一輪 clone 偵測到同一檔案、src_commit 仍為 `abc`
- **THEN** 系統 SHALL 不顯示 prompt、行為視同 `local-only`

#### Scenario: src_commit 變動清除 skip
- **GIVEN** skipped 紀錄存在，src_commit 為 `abc`
- **WHEN** 下一輪 clone 該檔案 src_commit 變為 `def`
- **THEN** 系統 SHALL 移除該 skipped 紀錄、依分類邏輯重新處理

### Requirement: 來源 commit 失效時退回 no-base

當系統使用 `src_commit` 查詢來源 git history 而 commit 已不存在時，該筆 entry SHALL 視為失效並退回 `no-base` 處理。

#### Scenario: src_commit 不存在於來源 git
- **GIVEN** v2 entry 的 src_commit 為 `obsolete`
- **AND** 來源 repo 內 `git cat-file -e obsolete^{commit}` 失敗
- **WHEN** 進行衝突分類
- **THEN** 系統 SHALL 視該 entry 為失效、分類結果為 `no-base`、退回現行 prompt 行為
