## Context

`script/utils/smart_merge.py:merge_file()` 為現行衝突處理核心。流程：

1. 計算 `src` 與 `dst` 的 sha256。
2. 相同 → `identical`。不同 → 進入 `force` / `skip_conflicts` / 互動 prompt。
3. 互動 prompt 提供 `[A] [I] [O] [S] [D]`，`[D]` 用 `difflib.unified_diff`。

`~/.config/ai-dev/manifests/<target>.yaml` 是 v1 schema，已有：

```yaml
managed_by: ai-dev
version: 1.2.8
last_sync: '2026-05-08T08:57:55+08:00'
target: claude
files:
  skills:
    <skill-name>:
      hash: sha256:<src-hash-at-last-sync>
      source: custom-skills
```

來源 repo（custom-skills、qdm-ai-tools、ecc）皆為 `~/.config/<repo>/` 下的 git working copy，可直接 `git rev-parse HEAD`、`git log` 取得 commit 與時間。

ADR `docs/adr/0001-ai-dev-clone-file-level-3way-merge.md` 已 Accepted，本設計依其決議展開實作層細節。

## Goals / Non-Goals

**Goals:**

- 在不破壞 manifests/ 既有讀者的前提下，原地擴充至 v2，承載 file-level base hash 與 decision history。
- 衝突分類能正確區分「使用者沒動 / 來源沒動 / 兩邊都動」，把不需 prompt 的情境靜默處理。
- clone 啟動時提供 per-source summary，使用者一眼看出來源是否真的更新。
- Skip 決定以 `(file, src_commit)` 為粒度，避免反覆追問同一個版本，又不至於永久封死。

**Non-Goals:**

- 不提供 `--untrack` 或反向解鎖指令（後續再評估）。
- 不修改 `ai-dev install` / `ai-dev sync` / `ai-dev update_custom_repo` 的 manifest 路徑（本輪僅 clone pipeline）。
- 不替換 `difflib.unified_diff`；視覺化升級限於三向視角切換與摘要列。
- 不變更 `force` / `skip_conflicts` / `--target` 旗標的 CLI 介面。
- 不引入新的設定檔或 daemon。

## Decisions

### 1. Manifest schema v2 採原地擴充

- 新欄位 `schema_version: 2` 放在 root，獨立於既有 `version` 欄位（後者忽略，與檔案實際狀態以 schema_version 為準）。
- `files.skills.<skill-name>.hash` 改為 `files.skills.<skill-name>.files: { <rel-path>: <FileEntry> }`，每筆 `FileEntry`：
  ```yaml
  src_hash: sha256:...
  src_commit: <40-char-commit>
  src_source: custom-skills
  dst_hash_at_sync: sha256:...
  decision: accepted | skipped | overwritten | appended | incremental
  decided_at: 2026-05-08T08:57:55+08:00
  ```
- 額外維護 `files.skills.<skill-name>.skipped: { <rel-path>: { src_commit: ..., decided_at: ... } }`，存放 skip 記憶；當下一輪 src_commit 不同即無視該記憶。
- 為什麼不開新檔：manifests/ 已被 install / sync / clone 多處讀取，新檔會分散事實來源。原地擴充由 `manifest.py` 統一處理 schema 升級，呼叫者無感。

**Alternatives considered**：

- 新開 `tracking/<target>.yaml` 平行檔：拒。三個 evaluation 觸點分散、易不一致。
- 廢棄 manifests/ 全新表：拒。改名成本高、收益等於原地擴充。
- dst 端 sidecar `.ai-dev-base`：拒。污染使用者目錄、難以集中查詢。

### 2. 3-way 衝突分類

於 `merge_file()` 之前先取出 manifest entry，進入分類函式 `_classify_conflict(src_hash, dst_hash, base_entry) -> Literal["clean","local-only","both-changed","no-base"]`：

| 條件 | 分類 | 行為 |
|------|------|------|
| `base_entry is None` | `no-base` | 退回現行 prompt（force / skip / 互動） |
| `dst_hash == base.dst_hash_at_sync` 且 `src_hash != base.src_hash` | `clean` | 自動覆蓋並更新 base |
| `src_hash == base.src_hash` 且 `dst_hash != base.dst_hash_at_sync` | `local-only` | 不寫入，輸出 `=` 行 |
| 其他 | `both-changed` | 進 prompt |

`base.dst_hash_at_sync` 是「ai-dev 上次寫入 dst 後的 hash」，能偵測使用者外部編輯。

### 3. Skip 記憶實作

- prompt 回傳 `skip` 時：寫入 `files.skills.<skill>.skipped[<rel-path>] = { src_commit, decided_at }`。
- 下一輪 clone 進入分類前：若 `(rel-path, current-src-commit)` 命中 skipped 記憶，視為 `local-only`（靜默保留），不進 prompt。
- 若 `current-src-commit` 與記憶不同：清除該筆 skipped、走標準分類，多半是 `both-changed`。
- 不持久化 src_commit 變更前的舊 skip 記憶，避免膨脹。

### 4. Per-source update summary

於 `clone_pipeline.py` 進入 file 分發迴圈前：

1. 從 `repos.yaml` + 內建 source 列表取出 `(source_name, local_path)` 清單。
2. 對每個 source：讀 `manifest.<target>.last_sync_commit_by_source[source]` 取得上次 commit；以 `git rev-parse HEAD` 取得本次。
3. 計算來源變動檔數 = `git diff --name-only <last>..<head>` 的長度。
4. 預掃 file map，分別計算「影響本次 target」「影響其他 target」的檔數。
5. 用 rich Table 輸出，未變來源以 `未變更` 顯示、其他 target 影響數以 dim 顯示。

`last_sync_commit_by_source` 是 manifest v2 的 root 欄位，於 sync 完成時寫入。

### 5. 三向 diff UI

- prompt 第一行先列三段摘要：「來源動 +N -M」「你動 +P -Q」「兩邊重疊 +R -S」。摘要由三組 unified diff 的 `+/-` 計數推算。
- 互動指令由 `[D]` 拆為 `[Ds]` src vs base、`[Dl]` dst vs base、`[Dc]` src vs dst；保留 `[A] [I] [O] [S]`。
- `_prompt_hint()` 文字同步更新。
- 若 `base_entry` 不存在（理論上 `both-changed` 一定有 base），UI 退回原 `[D]`（src vs dst）。

### 6. v1 → v2 migration

- `manifest.py` 在讀取時若偵測 `schema_version` 缺失，啟動 migration：
  1. 對每個 `<skill>` 與其下的 file（透過 `clone_pipeline` 的 file iterator 解析），檢查當前 dst 是否存在。
  2. 計算 `dst_hash`；若等於 v1 的 `<skill>.hash` 對應檔案 hash → 寫入 `FileEntry`，`src_hash = dst_hash`，`src_commit` 取 manifest 的 `last_sync` 對應到 source repo 的 commit（以 `git rev-list -1 --before=<last_sync>` 推算），`decision = accepted`。
  3. 若不一致或無法判斷 → 留白，視為 `no-base`。
  4. 結束後寫入 `schema_version: 2` 並備份原檔到 `manifests/.backup-v1/<target>.yaml.<timestamp>`。
- Migration 全程 idempotent，可重跑。

**Alternatives considered**：

- 全部視為 no-base（A）：使用者首次升級被淹沒在 prompt 裡，差體驗。
- 全部視為已接受（B）：會把使用者明明改過、與 src 不同的 dst 誤標 base，下次 src 動就靜默覆蓋本地修改。否決。
- 採 C：dst==src 自動標 base 是物理事實等價（hash 一致代表內容相同），唯一安全選項。

### 7. `--target X` 時 summary 範圍

- summary 永遠列所有 source 的變動，與 `--target` 無關。
- 每個 source row 顯示「影響本次 target N」與「影響其他 target M」（dim）。
- 理由：summary 是來源層資訊；多 target 使用者輪流跑時資訊應一致；`--target` 仍只控制實際分發。

## Risks / Trade-offs

- [Manifest 體積膨脹] → 從 skill-level 到 file-level 約 5–10× 大小。仍是 KB 級 YAML，可接受；之後若超 500KB 再評估改 sqlite。
- [v1 manifest 已被使用者手改過] → migration 備份原檔，並在 console 提示備份位置；若 migration 失敗，保留 v1 檔不寫 v2，下次 clone 重試。
- [`dst_hash_at_sync` 漂移] → 使用者用外部工具改 dst 後 dst_hash 會變動；`clean` / `local-only` 分類仍正確（因為比對的是 `dst == base.dst_hash_at_sync`）。若使用者改回與 base 同的內容，本系統視為未動，預期行為。
- [`--force` 與 manifest 互動] → `--force` 維持「不問直接覆蓋」，但仍要在覆蓋後更新 base。否則下次比對會錯亂。
- [來源 git history 重寫] → 若使用者 `git reset --hard` 來源 repo，舊的 `src_commit` 可能已不存在。讀取時 `git cat-file -e <commit>^{commit}` 不通過時，視 base 為失效，退回 `no-base`。
- [三向 diff prompt 變複雜] → 需要清楚的 hint。`_prompt_hint()` 文字更新並包含分組：「Diff: [Ds]/[Dl]/[Dc] | Action: [A]/[I]/[O]/[S]」。
- [skipped 記憶膨脹] → 每個 src_commit 變更時清除舊記憶；理論上每 file 同時最多一筆。

## Migration Plan

1. `manifest.py` 加入 `load_manifest(target)` / `save_manifest(target, m)` 與 `migrate_to_v2(m)`；既有讀者改用新 API。
2. 第一次跑 v2 程式時自動備份並升級 manifest。CLI 不需要新指令。
3. 若使用者降級 ai-dev 版本，舊版讀到 `schema_version: 2` 會找不到 `files.skills.<skill>.hash` 這個 key；舊版讀者需檢查 `schema_version`，遇到 v2 時 fallback 到 v1 兼容 reader（讀 `files.skills.<skill>.files.<rel>.src_hash` 折算）。本輪變更包含此 fallback，以避免「先升級後降級」造成資料損毀。
4. 若需 rollback：執行 `cp manifests/.backup-v1/<target>.yaml.<timestamp> manifests/<target>.yaml`，重啟 clone 即可。

## Open Questions

- skipped 記憶在 `git rebase` / `git reset` 後的失效時機是否需要更激進（例如 src_commit 不存在於來源 git history 時自動清除整筆 skipped）？預設「下次 src_commit 變動時重評估」就會自然清除。先不做更主動的清除，待實際發現問題再加。
- 是否需要 `ai-dev clone --show-summary-only`（只看 summary 不執行）？此問題不阻塞本輪，作為後續優化。
