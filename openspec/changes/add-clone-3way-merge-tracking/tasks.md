## 1. Manifest v2 schema 與 dataclass

- [ ] 1.1 在 `script/utils/manifest.py` 定義 `FileEntry` 與 `SkippedEntry` dataclass，欄位依 spec
- [ ] 1.2 擴充 `FileRecord`：新增 `files: dict[str, str]`（rel_path → sha256）與 `src_path: Path | None`、`src_commit: str | None` 欄位（src_path / src_commit 不寫 manifest）
- [ ] 1.3 擴充 `ManifestTracker.record_skill` / `record_command` / `record_agent` / `record_workflow`：新增 `src_path` 參數，蒐集 file-level hash map（依 `compute_dir_hash` 排除規則）
- [ ] 1.4 `to_manifest()` 寫出 v2 結構：root 加 `schema_version: 2` 與 `last_sync_commit_by_source`，`files.<resource>.<name>` 加 `files: { rel: ... }`、`commands/agents/workflows` 直接加 FileEntry 欄位

## 2. v1 → v2 Migration 與兼容 reader

- [ ] 2.1 實作 `migrate_to_v2(v1_manifest: dict, target: TargetType, sources_index: dict[str, Path]) -> dict`，依 spec 流程處理 dst==src 自動標 base
- [ ] 2.2 對每個 file 利用 `git -C <source-repo> rev-list -1 --before=<last_sync> HEAD -- <rel>` 推算 src_commit；無法取得時不寫 FileEntry
- [ ] 2.3 Migration 前備份原檔到 `~/.config/ai-dev/manifests/.backup-v1/<target>.yaml.<ISO-timestamp>`
- [ ] 2.4 確保 idempotent：對 `schema_version: 2` 的 manifest 為 no-op、不產新備份
- [ ] 2.5 `read_manifest()` 偵測缺 schema_version 時自動觸發 migration（懶觸發，僅在 v2 reader 被需要時）
- [ ] 2.6 提供 `v2_to_v1_view(m: dict) -> dict` helper：將 v2 manifest 投影回 v1 結構供舊 reader 用
- [ ] 2.7 unit test 覆蓋四種情境：dst==src、dst!=src、source repo 不存在、已是 v2

## 3. 3-way 分類函式與 skip 記憶

- [ ] 3.1 在 `manifest.py` 新增 `classify_file(file_entry: FileEntry | None, src_hash: str, dst_hash: str) -> Literal[...]`
- [ ] 3.2 新增 `record_file_decision(m, target, resource_type, name, rel, *, src_hash, src_commit, src_source, dst_hash, decision)`
- [ ] 3.3 新增 `record_skip(m, target, resource_type, name, rel, src_commit)` 與 `clear_skip(m, target, resource_type, name, rel)`
- [ ] 3.4 新增 `is_skipped(m, target, resource_type, name, rel, current_src_commit) -> bool`：命中 (rel, src_commit) 才回 True
- [ ] 3.5 新增 `update_last_sync_commit(m, source, commit)`
- [ ] 3.6 src_commit 不存在於來源 git 時清除 skipped 並視 base 失效（`is_base_valid()`）

## 4. Per-file prompt UI

- [ ] 4.1 在 `manifest.py` 新增 `prompt_file_decision(skill_name, rel_path, src_path, dst_path, base_blob_getter) -> Literal["overwrite","skip"]`
- [ ] 4.2 進 prompt 前印三段摘要（來源動 / 你動 / 重疊）；`+`/`-` 計數來自三組 `difflib.unified_diff`
- [ ] 4.3 互動指令 `[O] [S] [Ds] [Dl] [Dc]`，迴圈直到使用者輸入 O 或 S
- [ ] 4.4 `[Ds]` 用 base_blob_getter 抓 base bytes，與 src 文字內容做 unified diff 並印出
- [ ] 4.5 `[Dl]` 同上，base vs dst
- [ ] 4.6 `[Dc]` src vs dst（base 失效時仍可用）
- [ ] 4.7 base 取不到時 `[Ds]` `[Dl]` 印「無法取得 base 內容（commit 已失效）」、保留 prompt
- [ ] 4.8 unit test：mock stdin 與 base_blob_getter，覆蓋四個 diff 指令、O/S 回傳、base 失效

## 5. shared.copy_custom_skills_to_targets 重構

- [ ] 5.1 在 `script/utils/shared.py` 內 `copy_custom_skills_to_targets`：呼叫 `record_skill` 等時補傳 `src_path`（item，非 dst_item）
- [ ] 5.2 在 `detect_conflicts` 之後新增 `_classify_per_file(target, manifest, tracker) -> dict[(resource, name, rel), classification]`
- [ ] 5.3 將既有「整批 prompt_conflict_action」分支改為依分類分派：
  - clean：直接覆蓋、寫 base
  - local-only：跳過寫入、輸出 `=` 行
  - both-changed：呼叫 `prompt_file_decision`，O→覆蓋寫 base、S→寫 skip 記憶
  - no-base：保留現行 batch 路徑（force / skip_conflicts / batch UI）
- [ ] 5.4 `--force` 對所有分類覆蓋並寫 base
- [ ] 5.5 `--skip-conflicts` 對 both-changed 自動 skip；clean / local-only 不變
- [ ] 5.6 `--backup` 在覆蓋 both-changed 與 no-base 前備份；clean 不備份
- [ ] 5.7 整合 `is_skipped()`：分類前先查 skip 記憶
- [ ] 5.8 `_copy_with_log` 接受 file-level skip set（而非僅 skill-level `skip_names`）；對 skills 內個別 rel-path 跳過寫入
- [ ] 5.9 寫回 manifest：record_file_decision、update_last_sync_commit、save

## 6. Per-source update summary

- [ ] 6.1 在 `script/services/pipeline/clone_pipeline.py` 進入 `targets` phase 前蒐集 sources：custom-skills (`get_custom_skills_dir()`) + custom repos (`load_custom_repos()`) + ECC (`~/.config/everything-claude-code/`)
- [ ] 6.2 對每個 source 計算：`last_sync_commit_by_source[source]`（取任一 target manifest 內最新者）、當前 HEAD、`git diff --name-only`
- [ ] 6.3 預掃 file map（呼叫 `_prescan_*` 或新 helper）計算「影響本次 target」與「影響其他 target」檔數
- [ ] 6.4 用 rich Table 輸出 summary：未變來源「未變更」、首次同步「首次同步」、其他 target 影響數以 dim 樣式
- [ ] 6.5 summary 不受 `--target` 影響
- [ ] 6.6 dry-run 仍印 summary（不執行分發）

## 7. 兼容性與下游

- [ ] 7.1 `find_orphans` / `cleanup_orphans` 仍以 skill-level 名稱運作，`hash` 欄位保留
- [ ] 7.2 install / sync / update_custom_repo 等 reader 若期望 v1 結構，呼叫 `v2_to_v1_view()` 後使用
- [ ] 7.3 確保現有 `record_skill(item.name, dst_item, source)` 呼叫點補 `src_path=item`（搜尋並修正）

## 8. 文件與 changelog

- [ ] 8.1 `CHANGELOG.md` 新增 BREAKING 條目並指向本 change
- [ ] 8.2 `docs/dev-guide/workflow/copy-architecture.md`（如涉及）補充 3-way 流程圖
- [ ] 8.3 ADR `docs/adr/0001-...` 末段增註：實作對應 manifest.py + shared.py（不動 smart_merge.py）

## 9. 驗收（手動）

- [ ] 9.1 對既有 v1 manifest 執行 `ai-dev clone`：migration 觸發、備份生成、未動的 file 被自動標 base
- [ ] 9.2 改一個 dst 檔（skill 內單檔）後重跑 clone（src 未變）：local-only 行為、無 prompt
- [ ] 9.3 src 的同 skill 內其他檔有變動但 dst 未動該檔：clean 行為、自動套用、manifest 更新
- [ ] 9.4 src 與 dst 對同 file 同時動：both-changed prompt 顯示三段摘要與 [Ds]/[Dl]/[Dc] 切換
- [ ] 9.5 對 9.4 選 S 後再跑一次（src 未變）：不再出現 prompt
- [ ] 9.6 上游推新 commit 影響該檔：skip 記錄被清除、再次 prompt
- [ ] 9.7 `--target claude` 時 summary 仍列出 codex / gemini 來源變動
- [ ] 9.8 `--force` 與 `--skip-conflicts` 行為符合 spec
- [ ] 9.9 `.clonepolicy.json` 的 skill 行為不變（policy 自管，不報 3-way）
