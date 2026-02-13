## 1. 本機變更偵測函式

- [x] 1.1 在 `sync_config.py` 新增 `detect_local_changes(config)` 函式，回傳各同步目錄的差異檔案清單（added/modified/deleted）與總變更數
- [x] 1.2 重用現有 `_collect_files()` 和 `_files_equal()` 比較檔案差異
- [x] 1.3 排除 ignore profile 中定義的檔案

## 2. 互動式安全檢查

- [x] 2.1 在 `sync.py` 新增 `_prompt_pull_safety(changes)` 函式，顯示變更清單與三個選項
- [x] 2.2 變更清單最多顯示 10 個檔案，超過顯示「...及其他 N 個檔案」
- [x] 2.3 選項 1（先 push 再 pull）：呼叫現有 push 流程，成功後繼續 pull
- [x] 2.4 選項 2（強制覆蓋）：跳過安全檢查，執行原有 pull 流程
- [x] 2.5 選項 3（取消）：顯示「已取消」並退出

## 3. Pull 指令修改

- [x] 3.1 修改 `pull()` 指令，新增 `--force` flag（預設 False）
- [x] 3.2 無 `--force` 時：先呼叫 `detect_local_changes()`，有異動則進入互動式選項
- [x] 3.3 有 `--force` 時：跳過偵測，直接執行原有 pull 流程
- [x] 3.4 push 失敗時中止整個操作，顯示錯誤訊息

## 4. 測試

- [x] 4.1 測試 `detect_local_changes()` — 無變更回傳空清單
- [x] 4.2 測試 `detect_local_changes()` — 有修改/新增/刪除時正確回傳
- [x] 4.3 測試 `--force` flag 跳過偵測
- [x] 4.4 測試互動選項：選擇取消時不執行 pull
- [x] 4.5 測試互動選項：選擇強制覆蓋時執行 pull

## 5. 文件更新

- [x] 5.1 更新 `AI-DEV-SYNC-GUIDE.md` 的 pull 章節，說明安全檢查行為
- [x] 5.2 更新指令總覽表格，加入 `--force` 說明
