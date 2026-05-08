## 1. Manifest v2 schema 與讀寫 API

- [ ] 1.1 在 `script/utils/manifest.py` 定義 `FileEntry` 與 `SkippedEntry` dataclass，欄位依 spec
- [ ] 1.2 新增 `load_manifest(target) -> ManifestV2` 與 `save_manifest(target, m)`，內部依 `schema_version` 分派 v1 / v2 reader
- [ ] 1.3 提供 `get_file_entry(m, source, rel_path)` / `record_file_decision(m, source, rel_path, decision, ...)` / `record_skip(m, source, rel_path, src_commit)` / `clear_skip(m, source, rel_path)` API
- [ ] 1.4 提供 `update_last_sync_commit(m, source, commit)` 並於 save 時保證 `last_sync_commit_by_source` 為當前各來源 HEAD

## 2. v1 → v2 Migration

- [ ] 2.1 實作 `migrate_to_v2(v1_manifest, *, target, sources_index) -> ManifestV2`，dst==src 自動標 base、其他留白
- [ ] 2.2 對每筆 entry 利用 `git rev-list -1 --before=<last_sync> <branch>` 推算 src_commit；無法取得時留白
- [ ] 2.3 Migration 前備份原檔到 `~/.config/ai-dev/manifests/.backup-v1/<target>.yaml.<timestamp>`
- [ ] 2.4 確保 idempotent：對已是 v2 的 manifest 執行 migration 為 no-op、不產新備份
- [ ] 2.5 寫 unit test 覆蓋四種情境（dst==src、dst!=src、無 last_sync、已是 v2）

## 3. 3-way 衝突分類

- [ ] 3.1 在 `script/utils/smart_merge.py` 新增 `classify_conflict(src_hash, dst_hash, base_entry) -> Literal["clean","local-only","both-changed","no-base"]`
- [ ] 3.2 重構 `merge_file()` 接受 `base_entry` 與 `src_commit` 參數，依分類分派
- [ ] 3.3 `clean` 分類：直接覆蓋並回傳新 `FileEntry` 給 caller 寫回 manifest
- [ ] 3.4 `local-only` 分類：不寫 dst、輸出 `=` 提示行
- [ ] 3.5 `both-changed` 分類：呼叫新版 prompt（含 skip 記憶查詢）
- [ ] 3.6 `no-base` 分類：保留 v1 行為（force / skip_conflicts / 互動 prompt），但 prompt 結束後仍寫入 `FileEntry` 確立 base
- [ ] 3.7 `--force` 與 `--skip-conflicts` 與分類的互動依 spec：force 全部覆蓋並寫 base、skip_conflicts 僅影響 both-changed

## 4. Skip 記憶

- [ ] 4.1 prompt 回傳 `skip` 時呼叫 `record_skip(m, source, rel_path, current_src_commit)`
- [ ] 4.2 `merge_file()` 進分類前先查詢 skip 記憶：命中 (file, src_commit) → 視為 local-only 不 prompt
- [ ] 4.3 src_commit 與 skip 記錄不同時 `clear_skip()` 並繼續分類
- [ ] 4.4 src_commit 不存在於來源 git 時（`git cat-file -e` 失敗）視 base 失效 → no-base，並清除對應 skip 記錄

## 5. 三向 diff UI

- [ ] 5.1 在 `_prompt_conflict()` 進入 both-changed 前印出三段摘要（來源動 / 你動 / 重疊）
- [ ] 5.2 拆 `[D]` 為 `[Ds]` `[Dl]` `[Dc]` 三個指令，分別用 `git cat-file blob` 取得 base 內容後與 src / dst 做 unified diff
- [ ] 5.3 更新 `_prompt_hint()` 文字為「Diff: [Ds]/[Dl]/[Dc] | Action: [A]/[I]/[O]/[S]」
- [ ] 5.4 base 取不到時 `[Ds]` `[Dl]` 顯示「無法取得 base 內容（commit 已失效）」、保留 prompt 不退出
- [ ] 5.5 `_prompt_conflict()` 全套互動寫測試（mock stdin）

## 6. Per-source update summary

- [ ] 6.1 在 `script/services/pipeline/clone_pipeline.py` 進入分發迴圈前蒐集所有來源 `(source, local_path)`
- [ ] 6.2 對每個來源計算：`last_sync_commit_by_source[source]`、當前 HEAD、`git diff --name-only` 變動清單
- [ ] 6.3 預掃 file map，計算「影響本次 target」與「影響其他 target」檔數
- [ ] 6.4 用 rich Table 輸出 summary，未變來源顯示「未變更」、首次同步顯示「首次同步」、其他 target 影響數以 dim 樣式顯示
- [ ] 6.5 summary 不受 `--target` 影響（永遠列所有來源）

## 7. clone pipeline 整合

- [ ] 7.1 `clone_pipeline.execute_clone_plan()` 接 manifest 讀寫 API，每個檔案分發前後讀寫 base
- [ ] 7.2 分發完成時更新 `last_sync_commit_by_source` 為各來源當前 HEAD
- [ ] 7.3 分發過程出錯（例如寫入失敗）時不更新 manifest，避免 base 漂移
- [ ] 7.4 `script/commands/clone.py` 不變動 CLI 介面，僅確保旗標正確傳遞

## 8. 兼容性 fallback

- [ ] 8.1 在 `manifest.py` 提供 v1 reader：偵測 `schema_version: 2` 但呼叫端期望 v1 結構時，從 `files.skills.<skill>.files.<rel>.src_hash` 折算回 skill-level hash
- [ ] 8.2 確保 install / sync / update_custom_repo 路徑沒有因 schema 變更而崩潰（read 不寫）

## 9. 文件與 changelog

- [ ] 9.1 更新 `docs/dev-guide/workflow/copy-architecture.md`（如涉及）
- [ ] 9.2 在 `CHANGELOG.md` 新增 BREAKING 條目並指向本 change
- [ ] 9.3 補充 `docs/adr/0001-ai-dev-clone-file-level-3way-merge.md` 連結到本 change

## 10. 驗收

- [ ] 10.1 對既有 v1 manifest 執行 clone：migration 觸發、備份生成、未動的檔案被自動標 base
- [ ] 10.2 改一個 dst 檔後重跑 clone（src 未變）：local-only 行為、無 prompt
- [ ] 10.3 src 動但 dst 未動：clean 行為、自動套用、manifest 更新
- [ ] 10.4 src 與 dst 同時動：both-changed prompt 顯示三段摘要與三向 diff 切換
- [ ] 10.5 同情境選 skip 後再跑一次（src 未變）：不再出現 prompt
- [ ] 10.6 上游推新 commit 影響該檔：skip 記錄被清除、再次出現 prompt
- [ ] 10.7 `--target claude` 時 summary 仍列出 codex / gemini 來源變動
- [ ] 10.8 `--force` 與 `--skip-conflicts` 行為符合 spec
