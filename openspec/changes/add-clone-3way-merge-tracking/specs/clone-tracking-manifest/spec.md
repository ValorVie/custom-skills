## ADDED Requirements

### Requirement: Manifest Schema v2 結構

`~/.config/ai-dev/manifests/<target>.yaml` SHALL 支援 `schema_version: 2`。當 `schema_version` 為 `2` 時：

- Manifest root SHALL 額外包含 `last_sync_commit_by_source: { <source-name>: <40-hex> }`。
- 既有 `files.<resource_type>.<name>.hash` 欄位 SHALL 保留（用於孤兒清理與向下相容）。
- `files.skills.<skill-name>` SHALL 額外包含 `files: { <relative-path>: <FileEntry> }` 與選填 `skipped: { <relative-path>: <SkippedEntry> }`。
- `files.commands.<name>` / `files.agents.<name>` / `files.workflows.<name>` SHALL 額外包含 `FileEntry` 欄位（直接放在該 entry 同層，因為這些資源原本就是單檔）。

`FileEntry` 結構：

```yaml
src_hash: sha256:<64-hex>
src_commit: <40-hex git commit>
src_source: custom-skills | qdm-ai-tools | ecc | <repo-name>
dst_hash_at_sync: sha256:<64-hex>
decision: accepted | overwritten | skipped
decided_at: <ISO 8601 timestamp>
```

`SkippedEntry` 結構：

```yaml
src_commit: <40-hex>
decided_at: <ISO 8601 timestamp>
```

#### Scenario: schema_version 缺失視為 v1
- **WHEN** 讀取的 manifest 不含 `schema_version` 欄位
- **THEN** 系統 MUST 視為 v1 並觸發 migration 流程

#### Scenario: schema_version 為 2 時讀取 file-level entry
- **WHEN** `schema_version: 2` 且呼叫 `get_file_entry(m, "claude", "skills", "auto-skill", "SKILL.md")`
- **THEN** 系統 SHALL 回傳對應 `FileEntry`，欄位齊全

#### Scenario: 寫入 file entry 後 schema_version 保持為 2
- **WHEN** 呼叫 `record_file_decision(m, "claude", "skills", "auto-skill", "SKILL.md", decision="accepted", ...)` 寫入新紀錄
- **THEN** manifest root 的 `schema_version` 維持 `2`、目標 entry 內的 `files.<rel>` 內含寫入的欄位、`last_sync_commit_by_source[source]` 同步更新為當前 src_commit

#### Scenario: skill-level dir hash 仍存在
- **WHEN** v2 manifest 內某 skill 同時有 `hash` 與 `files.<rel>`
- **THEN** 既有 `find_orphans` / `detect_conflicts` 對 skill 名稱的孤兒判斷 SHALL 仍可用 `hash` 欄位運作

### Requirement: ManifestTracker 蒐集 file-level 內容

`ManifestTracker.record_skill(name, source_path, source, src_path=None)` SHALL 在計算 dir hash 之外，迭代 `source_path` 內所有非排除檔案、計算每檔 sha256，存入 `FileRecord.files: dict[str, str]`（key 為相對於 skill 根目錄的路徑、value 為 `sha256:<hex>`）。`record_command` / `record_agent` / `record_workflow` SHALL 在 `FileRecord` 內新增 `src_commit` 與 `src_path` 欄位（不寫 manifest，僅供查 commit 用）。

`to_manifest()` 寫出 v2 結構時 SHALL 將 `FileRecord.files` 對應到 `files.skills.<skill>.files`。

#### Scenario: record_skill 蒐集 file map
- **WHEN** 呼叫 `tracker.record_skill("auto-skill", Path("/src/skills/auto-skill"), src_path=Path("/src/skills/auto-skill"))`
- **THEN** `tracker.skills["auto-skill"].files` 為 `{ "SKILL.md": "sha256:...", "knowledge-base/...": "sha256:..." }`，包含所有非排除檔案

#### Scenario: file map 排除 __pycache__ 與 .pyc
- **WHEN** 來源目錄包含 `__pycache__/foo.pyc`
- **THEN** `FileRecord.files` 不包含該檔案

#### Scenario: src_path 不寫入 manifest
- **WHEN** 呼叫 `tracker.to_manifest()`
- **THEN** 輸出 dict 內不含 `src_path` 欄位

### Requirement: 3-way 分類函式

系統 SHALL 提供 `classify_file(file_entry, src_hash, dst_hash) -> Literal["clean","local-only","both-changed","no-base"]`：

| 條件 | 結果 |
|------|------|
| `file_entry is None` 或缺 `src_hash` / `dst_hash_at_sync` | `no-base` |
| `dst_hash == file_entry.dst_hash_at_sync` 且 `src_hash != file_entry.src_hash` | `clean` |
| `src_hash == file_entry.src_hash` 且 `dst_hash != file_entry.dst_hash_at_sync` | `local-only` |
| 其他（兩邊皆動） | `both-changed` |

若 `src_hash == file_entry.src_hash` 且 `dst_hash == file_entry.dst_hash_at_sync`，回傳 `clean`（無變動視同 clean，呼叫端判斷不需動作）。

#### Scenario: clean
- **GIVEN** file_entry 存在、src_hash 與 base.src_hash 不同、dst_hash 等於 base.dst_hash_at_sync
- **WHEN** 呼叫 classify_file
- **THEN** 回傳 `"clean"`

#### Scenario: local-only
- **GIVEN** src_hash 等於 base.src_hash、dst_hash 與 base.dst_hash_at_sync 不同
- **WHEN** 呼叫 classify_file
- **THEN** 回傳 `"local-only"`

#### Scenario: both-changed
- **GIVEN** src_hash 與 base.src_hash 不同、dst_hash 與 base.dst_hash_at_sync 不同
- **WHEN** 呼叫 classify_file
- **THEN** 回傳 `"both-changed"`

#### Scenario: no-base 為 None
- **GIVEN** file_entry 為 None
- **WHEN** 呼叫 classify_file
- **THEN** 回傳 `"no-base"`

### Requirement: v1 → v2 Migration（保守標 base）

系統 SHALL 提供 `migrate_to_v2(v1_manifest, target) -> dict`：

1. 對每個 v1 `files.<resource>.<name>.hash`，找對應 dst 路徑：
   - skills：`compute_dir_hash(dst_path)` 與 v1 `hash` 相同 → 進入該目錄迭代每個 file，計算 file hash 並查 `git -C <source-repo> rev-list -1 --before=<last_sync> HEAD -- <rel>` 取對應 commit；寫入 `FileEntry`，`src_hash = file_hash`、`dst_hash_at_sync = file_hash`、`decision = accepted`、`decided_at = last_sync`。
   - commands / agents / workflows：file hash 與 v1 `hash` 相同 → 寫 `FileEntry`。
2. 若 dst 內容已不等於 v1 hash → 不寫 `FileEntry`，留待下次 clone 走 `no-base`。
3. Migration 結束後 SHALL 寫 `schema_version: 2`、保留 `version`、`last_sync`、`target`，並 SHALL 將原 v1 manifest 備份到 `~/.config/ai-dev/manifests/.backup-v1/<target>.yaml.<ISO-timestamp>`。
4. Migration SHALL idempotent：對 `schema_version: 2` 的 manifest 為 no-op、不產新備份。

#### Scenario: dst==src 自動標 base（skill 內單檔）
- **GIVEN** v1 manifest 中 `<skill>.hash` 等於當前 `compute_dir_hash(dst)`
- **WHEN** 觸發 migration
- **THEN** 該 skill 內每個檔案 SHALL 在 v2 manifest 有對應 `FileEntry`，`decision = accepted`、`src_hash = dst_hash`

#### Scenario: dst!=src 不自動標 base
- **GIVEN** v1 manifest 中 `<skill>.hash` 不等於當前 `compute_dir_hash(dst)`
- **WHEN** 觸發 migration
- **THEN** 該 skill 在 v2 manifest 不應有 `files.<rel>` entries，視為 `no-base`

#### Scenario: 備份成功
- **WHEN** Migration 結束
- **THEN** `~/.config/ai-dev/manifests/.backup-v1/` 下存在帶 ISO 時間戳的 v1 副本

#### Scenario: Migration idempotent
- **WHEN** 對 `schema_version: 2` 的 manifest 再次執行 migration
- **THEN** manifest 內容不變、不產生新備份檔

#### Scenario: 找不到 source repo 時略過 commit
- **GIVEN** `<source>` 對應的本地 git repo 不存在
- **WHEN** Migration 處理該 source 的 entries
- **THEN** 系統 SHALL 不寫該 source 的 `FileEntry`，留待 no-base

### Requirement: Skip 記憶以 (file, src_commit) 為 key

當 per-file prompt 回傳 `skip` 時，系統 SHALL 寫入 `files.skills.<skill>.skipped[<rel-path>] = { src_commit: <current-src-commit>, decided_at: <now> }`（commands / agents / workflows 同邏輯，路徑為 `files.<resource>.<name>.skipped`）。

於下一輪 clone 進入分類前，系統 MUST 先比對：

- 若 `(rel-path, current-src-commit)` 命中既有 skipped 紀錄 → 視為 `local-only`、不進 prompt。
- 若 src_commit 與 skipped 紀錄不同 → 系統 SHALL 移除該筆 skipped，依分類邏輯處理。
- 若 src_commit 不存在於來源 git history（`git cat-file -e <commit>^{commit}` 失敗）→ 系統 SHALL 視 base 失效、移除 skipped、走 `no-base`。

#### Scenario: 寫入 skip 記憶
- **WHEN** 使用者於 per-file prompt 選擇 `S`
- **THEN** manifest 對應 `skipped[<rel>].src_commit` 等於當前 src_commit、`decided_at` 為當前時間

#### Scenario: 同一 src_commit 不再提示
- **GIVEN** skipped 紀錄存在，src_commit 為 `abc`
- **WHEN** 下一輪 clone 偵測到該 file、src_commit 仍為 `abc`
- **THEN** 系統 SHALL 不顯示 prompt、行為視同 `local-only`

#### Scenario: src_commit 變動清除 skip
- **GIVEN** skipped 紀錄存在，src_commit 為 `abc`
- **WHEN** 下一輪 clone 該 file 的 src_commit 變為 `def`
- **THEN** 系統 SHALL 移除該 skipped 紀錄、依分類邏輯重新處理

#### Scenario: src_commit 失效時移除 skip
- **GIVEN** skipped 紀錄的 src_commit 已不存在於來源 git
- **WHEN** 下一輪 clone 評估該 file
- **THEN** 系統 SHALL 移除該 skipped、視為 `no-base`
