## 1. FileRecord 與 ConflictInfo 擴充 (manifest.py)

- [x] 1.1 `FileRecord` dataclass 新增 `source_path: Path | None = None` 欄位
- [x] 1.2 `ConflictInfo` dataclass 新增 `source_path: Path | None = None` 和 `target_path: Path | None = None` 欄位
- [x] 1.3 `ManifestTracker.record_skill()` 新增 `source_path` 參數，儲存至 `FileRecord`
- [x] 1.4 `ManifestTracker.record_command()` 新增 `source_path` 參數，儲存至 `FileRecord`
- [x] 1.5 `ManifestTracker.record_agent()` 新增 `source_path` 參數，儲存至 `FileRecord`
- [x] 1.6 `ManifestTracker.record_workflow()` 新增 `source_path` 參數，儲存至 `FileRecord`
- [x] 1.7 確認 `to_manifest()` 不輸出 `source_path` 欄位

## 2. detect_conflicts 填入路徑 (manifest.py)

- [x] 2.1 `detect_conflicts()` 建立 `ConflictInfo` 時，從 `new_tracker` 的 `FileRecord` 取得 `source_path`
- [x] 2.2 `detect_conflicts()` 建立 `ConflictInfo` 時，將已計算的 `target_path` 填入

## 3. 互動選單與 diff 顯示 (manifest.py)

- [x] 3.1 `prompt_conflict_action()` 新增參數 `conflicts: list[ConflictInfo] | None = None`
- [x] 3.2 修改選單順序：1=強制覆蓋、2=跳過、3=備份後覆蓋、4=查看差異、5=取消分發
- [x] 3.3 選項 4 回傳 `"diff"`，選項 5 回傳 `"abort"`（原選項 4）
- [x] 3.4 新增 `show_conflict_diff(conflicts: list[ConflictInfo])` 函式
- [x] 3.5 `show_conflict_diff` 中，skills 類型使用 `diff -ruN source target`
- [x] 3.6 `show_conflict_diff` 中，commands/agents/workflows 類型使用 `diff -u source target`
- [x] 3.7 `show_conflict_diff` 處理 `diff` 指令不存在的情況（捕獲 FileNotFoundError）
- [x] 3.8 `show_conflict_diff` 處理 source_path 或 target_path 為 None 的情況

## 4. 分發流程整合 (shared.py)

- [x] 4.1 `copy_custom_skills_to_targets()` 衝突處理段落：將 `prompt_conflict_action()` 呼叫改為傳入 `conflicts` 參數
- [x] 4.2 衝突處理段落新增 `"diff"` 動作：呼叫 `show_conflict_diff(conflicts)` 後重新顯示 `display_conflicts()` 和 `prompt_conflict_action()`（使用 while 迴圈）

## 5. 來源路徑傳遞 (shared.py)

- [x] 5.1 `_copy_with_log()` 中呼叫 `tracker.record_*` 時傳入 `source_path` 參數
- [x] 5.2 `_prescan_custom_repos()` 中呼叫 `record_*` 時傳入 `source_path` 參數
- [x] 5.3 確認預掃描階段（步驟 3 之前）的所有 `record_*` 呼叫都傳入 `source_path`

## 6. Shell Completion 自動安裝 (install.py)

- [x] 6.1 在 `install()` 函式的安裝流程結尾（步驟 7 後），新增 shell completion 安裝段落
- [x] 6.2 使用 `subprocess.run(["ai-dev", "--install-completion"])` 嘗試安裝
- [x] 6.3 捕獲例外，失敗時顯示手動安裝提示，不中斷流程

## 7. 驗證

- [ ] 7.1 手動修改一個已分發的 skill，執行 `ai-dev clone`，確認選單顯示 5 個選項
- [ ] 7.2 選擇「查看差異」，確認 diff 輸出正確顯示
- [ ] 7.3 查看差異後選擇其他選項，確認流程正常完成
- [ ] 7.4 執行 `ai-dev install`，確認 shell completion 自動安裝
- [ ] 7.5 新開 terminal，輸入 `ai-dev` + Tab，確認補全生效
