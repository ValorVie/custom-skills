## Why

`ai-dev clone` 目前只做 src ↔ dst 二路 hash 比對。使用者一旦改過 dst，每次 update + clone 都會被重複追問同一個檔案；且使用者無法判斷「本次來源是否真的更新了、更新了什麼」。需要一份「使用者上次接受了哪個版本」的反向紀錄，才能把無謂的提示濾掉、把真正的衝突浮上來。

## What Changes

- **新增 file-level base 紀錄**：在 `~/.config/ai-dev/manifests/<target>.yaml` 內以 `(target, source, file rel-path)` 為 key，記錄 `src_hash` / `src_commit` / `src_source` / `dst_hash_at_sync` / `decision` / `decided_at`。
- **3-way 衝突分類**：依 base / src / dst 三向比對分為 `clean`（自動套用）、`local-only`（靜默保留）、`both-changed`（prompt）、`no-base`（退回現行行為）。
- **per-source update summary**：clone 開始時對每個來源 repo（custom-skills / qdm-ai-tools / ecc）逐一輸出上次與本次 commit、變動檔數、影響本次 target 數、影響其他 target 數。
- **三向 diff UI**：原 `[D]` 拆為 `[Ds]` src vs base、`[Dl]` dst vs base、`[Dc]` src vs dst；prompt 預設先列三行摘要（來源動 / 你動 / 重疊改動）。
- **Skip 記憶**：使用者選 skip 時記到 `(file, src_commit)`；同 src_commit 不再提示，src_commit 一變立刻重評估為 both-changed。
- **Manifest schema v2**：新增 `schema_version: 2` 欄位區分版本；既有 `version: 1.2.8` 欄位忽略。
- **v1 → v2 migration**：第一次跑 v2 時，只對 `dst hash == src hash` 的檔案自動標 base；其餘 entry 退回 no-base。
- **BREAKING**：v1 manifest 結構由 `files.skills.<skill>.hash` 升為 `files.skills.<skill>.files.<rel-path>.{...}`。讀寫舊欄位的程式必須升級；migration 路徑見上一條。

## Capabilities

### New Capabilities

- `clone-tracking-manifest`：file-level base-hash 與 decision history 的儲存格式、讀寫 API、v1→v2 migration 邏輯。

### Modified Capabilities

- `clone-command`：clone 啟動時新增 per-source update summary；3-way 分類影響 dispatch 邏輯。
- `conflict-diff-view`：原 `[D]` 升為 `[Ds] / [Dl] / [Dc]` 三向視角，prompt 預設先列三行摘要。

## Impact

- 程式碼：`script/utils/smart_merge.py`（3-way 比對、prompt UI）、`script/utils/manifest.py`（v2 schema 讀寫、migration）、`script/services/pipeline/clone_pipeline.py`（summary、3-way dispatch）、`script/commands/clone.py`（無重大改動，傳遞旗標）。
- 資料檔：`~/.config/ai-dev/manifests/<target>.yaml` schema 升級；首次 clone 觸發 migration。
- 使用者體驗：來源未變時不再被反覆追問；衝突更精確；多來源狀況一目了然。
- 文件：`docs/adr/0001-ai-dev-clone-file-level-3way-merge.md`（已 Accepted）為設計依據。
- 不在範圍：`--untrack` 反向指令、其他 sync / install 指令的 manifest 改寫（視後續再評估）。
