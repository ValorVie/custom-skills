## Context

`ai-dev clone` 的實際呼叫鏈：

```
script/commands/clone.py:clone()
  → script/services/pipeline/clone_pipeline.py:execute_clone_plan()
    → script/services/targets/distribute.py:run_targets_phase()
      → script/utils/shared.py:copy_custom_skills_to_targets()  (line 1095-1351)
        → script/utils/manifest.py:detect_conflicts() / prompt_conflict_action()
        → script/utils/shared.py:_copy_with_log()  (line 962, 真正的複製)
```

現行衝突模型：

- `manifest.py:ManifestTracker.record_skill()` 用 `compute_dir_hash()` 對整個 skill 目錄取 hash，**顆粒度為 skill / command / agent / workflow**。
- `detect_conflicts()` 比對 `tracker.skills[name].hash`（整目錄 hash）與 manifest 上次寫入的 hash。
- `prompt_conflict_action()` 是 **batch UI**：對所有衝突 **一次** 詢問 `1) force / 2) skip / 3) backup / 4) diff / 5) abort`。
- `[4] diff` 用 `diff -ruN` / `diff -u` 顯示來源 vs 目標。

**痛點**：使用者改了一個 skill 的某個檔案 → 整個 skill 被當衝突。下次來源更新（即使更新的是同 skill 內的其他檔），仍報衝突；使用者無從判斷是否該 skip。

注意：`script/utils/smart_merge.py` 提供 `merge_file()` 與 `[A]/[I]/[O]/[S]/[D]` per-file UI，**只給 `script/commands/project.py`（專案模板同步）使用，與 clone 無關**。本 change 不動 smart_merge。

來源 repos：

- `~/.config/custom-skills/`（git，主來源）
- `~/.config/qdm-ai-tools/`（git，列於 `~/.config/ai-dev/repos.yaml`）
- `~/.config/everything-claude-code/`（git，ECC selective dist）

三者皆可 `git rev-parse HEAD` / `git log` 取 commit。

ADR `docs/adr/0001-ai-dev-clone-file-level-3way-merge.md` 已 Accepted，本設計對齊其決議並對應實際呼叫鏈展開。

## Goals / Non-Goals

**Goals:**

- 在 `~/.config/ai-dev/manifests/<target>.yaml` 內以 file 為單位紀錄 base hash + src commit + decision，使 `clean / local-only / both-changed / no-base` 分類成立。
- 將 `copy_custom_skills_to_targets` 的「整批 5-option prompt」流程升級為「先依分類自動處理、僅 both-changed 進 per-file prompt」。
- 保留既有 `--force` / `--skip-conflicts` / `--backup` 旗標語意（force/skip 改為作用於 both-changed；backup 在覆蓋前備份）。
- clone 啟動時於 `clone_pipeline` 印 per-source summary。
- 既有孤兒清理、tracker、record_method、`detect_conflicts` 對 commands/agents/workflows 的行為保持兼容。

**Non-Goals:**

- 不動 `smart_merge.py`（不在 clone 路徑上）。
- 不變更 `clone.py` 的 CLI 旗標表面。
- 不引入新指令（如 `--untrack`），下一輪再評估。
- 不重寫整個 `copy_custom_skills_to_targets`，僅替換衝突處理段。
- 不改變 skill 子目錄結構或扁平化邏輯。
- 不引入 sqlite 等新依賴；manifest 仍是 YAML。

## Decisions

### 1. 顆粒度：在 manifest 內並存 skill-level hash 與 file-level entries

避免破壞 `record_skill` / 孤兒清理 / commands 等下游：

- `files.skills.<skill-name>.hash`：保留現行 dir hash（孤兒判斷、向下相容）。
- `files.skills.<skill-name>.files.<rel-path>`：v2 新增，每筆是 `FileEntry`。
- `files.commands.<name>.hash`：commands/agents/workflows 是單檔，本身就是 file-level；新增同層的 `src_commit` / `dst_hash_at_sync` / `decision` / `decided_at`。
- 若 v2 reader 讀到沒有 `files.<...>.files` 的 entry，視為 v1 → 對該 entry 走 migration 或退回 no-base。

**Alternatives**：純 file-level（廢棄 dir hash）會讓孤兒清理重寫；雙層只多幾 KB YAML，是務實取捨。

### 2. ManifestTracker 擴充：file-level 蒐集

`record_skill(name, source_path, source)` 內部改為：

1. 仍計算 dir hash（`hash` 欄位）。
2. 額外迭代 `source_path.rglob('*')`（套用既有 pycache / pyc 排除規則），對每個檔案計算 file hash 並暫存於 `FileRecord.files: dict[str, FileHash]`（`rel_path` → hash）。
3. `record_command` / `record_agent` / `record_workflow` 已是單檔，直接記。
4. `to_manifest()` 寫出時將 file-level 資訊放到 `files.skills.<skill>.files.<rel>` 結構。

`source_path` 必須能用 `git -C <repo_root> log -1 --format=%H -- <rel-to-repo>` 取得對應檔案最後一次 commit；shared.py 的 `record_skill(item.name, dst_item, ...)` 傳的是 dst（為了多源合併準確），需要額外保存「真正的 src path」以供 commit 查詢。`record_skill` 增加 `src_path: Path | None` 參數（不寫 manifest）。

### 3. 3-way 衝突分類函式

新增 `manifest.classify_file(file_entry, src_hash, dst_hash) -> Literal["clean","local-only","both-changed","no-base"]`：

| 條件 | 分類 |
|------|------|
| `file_entry is None` 或缺 `src_hash` / `dst_hash_at_sync` | `no-base` |
| `dst_hash == file_entry.dst_hash_at_sync` 且 `src_hash != file_entry.src_hash` | `clean` |
| `src_hash == file_entry.src_hash` 且 `dst_hash != file_entry.dst_hash_at_sync` | `local-only` |
| 其他 | `both-changed` |

### 4. 衝突 dispatch 改寫

`copy_custom_skills_to_targets` 在 `detect_conflicts` 後新增 `_classify_conflicts(target, conflicts, old_manifest)` 階段：

- 將 batch `ConflictInfo`（skill-level）展開為 `FileConflict`（file-level），分類為 4 類。
- `clean`：直接覆蓋（在 `_copy_with_log` 階段以 file-level skip set 控制；對 skills 而言意味「該 file 寫入但無 prompt」）。
- `local-only`：將 `(skill, rel)` 加入「保留本地」集合，在 `_copy_with_log` 內遇到該 file 不覆蓋，console 輸出 `=` 行。
- `no-base`：第一次同步、或 base 失效；維持現行行為（force / skip_conflicts / 互動）。
- `both-changed`：進入新的 per-file prompt（見 5）。

`--force`：所有 file 一律覆蓋並更新 base。
`--skip-conflicts`：對 `both-changed` 自動寫 skip 記憶並跳過；clean / local-only 不受影響。
`--backup`：對 `both-changed` 與 `no-base` 在覆蓋前備份檔案；clean 不備份（不會破壞使用者修改）。

### 5. Per-file prompt UI

新增 `manifest.prompt_file_decision(skill_name, rel_path, src_path, dst_path, base_blob_getter) -> Literal["overwrite","skip"]`：

- 開頭印三行摘要：`來源動 +N -M`、`你動 +P -Q`、`重疊改動 +R -S`（行數從 unified diff 的 `+`/`-` 計算）。
- 提示文字：`Diff: [Ds]/[Dl]/[Dc] | Action: [O] overwrite / [S] skip`。
- 僅兩個 action（overwrite / skip）：append / incremental 是 smart_merge 的特化用途，clone 不適用（會破壞檔案結構）。
- `[Ds]` 用 `git -C <src_repo> show <src_commit>:<rel>` 抓 base，與 src 做 unified diff。
- `[Dl]` base vs dst。
- `[Dc]` src vs dst（與既有 batch diff 一致）。
- 若 base 拿不到（`git cat-file -e` 失敗），`[Ds]/[Dl]` 顯示「無法取得 base 內容」、保留 prompt；`[Dc]` 仍可用。

選 `O` → 覆蓋並更新 base、寫 `decision: overwritten`。
選 `S` → 不覆蓋、寫 `skipped` 記憶到 `files.skills.<skill>.skipped[<rel>] = { src_commit, decided_at }`、保留舊 base 不更新。

### 6. Skip 記憶查詢

進分類前先查 `files.skills.<skill>.skipped[<rel>]`：

- 命中 `(rel, current_src_commit)` → 視為 `local-only`、不 prompt。
- 不命中（src_commit 變了或無記憶）→ 移除舊 skipped（如果有）、走分類邏輯。

### 7. Per-source update summary

於 `clone_pipeline.execute_clone_plan()` 進入 `targets` phase 前：

1. 蒐集 source 清單：`(name, local_path)`。Custom-skills 路徑由 `get_custom_skills_dir()`，custom repos 從 `repos.yaml`，ECC 從 `~/.config/everything-claude-code/`（若存在）。
2. 對每個 source：讀「任一 target manifest」的 `last_sync_commit_by_source[source]`（取最新者），與當前 `git rev-parse HEAD` 比對。
3. 若有差異：`git diff --name-only <last>..<head>` 取變動檔清單。
4. 預掃影響檔數：對 `selected_targets` 的 platform_configs 估算，與「其他 target」估算分開。
5. rich Table 輸出，未變顯示「未變更」、首次同步顯示「首次同步」、其他 target 影響數以 dim 顯示。

`last_sync_commit_by_source` 在 manifest root，每個 target manifest 各自有；以「任一 target 的紀錄都代表使用者上次同步該 source 到任意 target 的 commit」為近似（更精確需要 per-(source,target) 紀錄；此 change 內取簡化方案，open question 列出）。

### 8. v1 → v2 Migration

`read_manifest()` 偵測缺 `schema_version` 或值非 2 → 呼叫 `migrate_to_v2(m, target)`：

1. 對每筆 `files.skills.<skill>.hash`：
   - 找 dst 路徑（`_get_target_resource_path`）。
   - 對 dst 計算 `compute_dir_hash`。若等於 v1 的 `hash`：
     - 進入該 skill 內部，對每個檔案計算 file hash，並查 source repo（依 `source` 欄位）取對應 file 的 `git log -1 --format=%H -- <rel>` 在 `last_sync` 之前的 commit。
     - 寫入 `FileEntry`：`src_hash = dst_hash`、`dst_hash_at_sync = dst_hash`、`src_commit = <commit>`、`decision = accepted`、`decided_at = <last_sync>`。
   - 若不等於：留空，視為 no-base。
2. 對 commands / agents / workflows 同邏輯（單檔比對較直接）。
3. 寫入 `schema_version: 2`、保留原 `version`、`last_sync`、`target`。
4. 備份原檔到 `~/.config/ai-dev/manifests/.backup-v1/<target>.yaml.<ISO-timestamp>`。
5. Idempotent：`schema_version: 2` 已存在則 no-op。

**Alternatives**：A（全當 no-base）糟糕體驗、B（一律 accepted）危險、C 安全 — 已在 ADR 中收斂。

### 9. 既有 batch UI 處置

`prompt_conflict_action()` / `display_conflicts()` / `show_conflict_diff()` 函式 **保留**，但 `copy_custom_skills_to_targets` 不再呼叫。理由：

- 移除可能影響第三方未知呼叫者（保守）。
- 函式簽章不變，後續可作為 no-base / 全 force / 全 skip 的 fallback 路徑（目前 `--force` / `--skip-conflicts` 都不呼叫互動）。
- spec 上以 MODIFIED 標示：clone 路徑改採新 per-file UI，舊 batch UI 在 clone 流程內被取代但函式保留。

## Risks / Trade-offs

- [Manifest 體積] → 假設平均每 skill 10 檔，膨脹約 5–10×。實測前以 50KB 為警戒線；超過再考慮拆檔。
- [`record_skill(item.name, dst_item, ...)` 傳 dst path] → file commit 查詢需要 src path；新增可選 `src_path` 參數，舊呼叫者不傳即無 commit 紀錄（退回 no-base 行為）。
- [Source repo git history 重寫] → `src_commit` 失效時 entry 視為 `no-base`，並清除對應 skipped。
- [Clone policy skill] → 含 `.clonepolicy.json` 的 skill 在 prescan 階段被跳過，現行就走檔案層級處理。本 change 暫不擴及 clonepolicy 路徑（policy 自有 force/skip 邏輯）。Open question 列出。
- [Custom repos / ECC source 沒紀錄到 last_sync_commit_by_source] → 第一次跑 v2 時 summary 顯示「首次同步」、`git diff` 不執行；migration 不寫該 source 的 commit，下次 clone 才開始追蹤。
- [Per-file prompt 數量] → 若 src 與 dst 都改了多檔，prompt 變密集。提供 `--force` / `--skip-conflicts` 為應急手段；prompt 內可考慮加 `[A]ccept all remaining` / `[X] skip all remaining`，本 change 暫不做、列入 open question。

## Migration Plan

1. v2 reader / writer 上線：`read_manifest()` 自動 migration；migration 失敗則保留 v1 檔不寫 v2，下次 clone 重試。
2. v1 reader fallback：若使用者降級 ai-dev，舊版讀 v2 時取不到 `files.skills.<skill>.hash` 結構 → 既有 reader 已用 `.get("hash", "")` 兜底，不會崩潰；但會把所有 skill 視為「無 hash」→ 全部報衝突。本 change 提供 `_v2_to_v1_view(m)` helper，install / sync 等其他指令呼叫 `read_manifest()` 時若需要 v1 結構，先過 helper。
3. Rollback：複製 `~/.config/ai-dev/manifests/.backup-v1/<target>.yaml.<timestamp>` 回原位。

## Open Questions

- `last_sync_commit_by_source` 是否要進化為 per-(source, target)？目前以單一 target 的紀錄涵蓋全 source，若使用者跨 target 跑 clone 頻率不同會略不準，但對 summary 用途夠用。
- Per-file prompt 是否提供 `[A]ccept all remaining` / `[X] skip all remaining` 加速？此 change 不做，等實測再評估。
- `.clonepolicy.json` 的 skill 是否納入 file-level tracking？目前由 policy 自管，先不接管；若使用者該 skill 內既有 file 與 src 不一致仍會走 policy 路徑，不報 3-way 衝突。
