## 1. 路徑與分發核心調整

- [x] 1.1 將 `script/utils/paths.py` 的 `get_opencode_plugin_dir()` 由 `plugin` 改為 `plugins`
- [x] 1.2 將 `script/utils/shared.py` 的 `COPY_TARGETS["opencode"]["plugins"]` 目標改為 `~/.config/opencode/plugins/`
- [x] 1.3 調整 OpenCode plugin 分發格式，確保 `plugins/` 第一層產生明確 entry 檔（`*.ts` 或 `*.js`）

## 2. 相容遷移策略

- [x] 2.1 新增 legacy 路徑 `~/.config/opencode/plugin/...` 偵測邏輯
- [x] 2.2 實作一次性搬遷或 fallback 相容流程，避免既有安裝中斷
- [x] 2.3 增加遷移過程的使用者提示訊息（新路徑/舊路徑狀態與處理結果）

## 3. 規格與文件對齊

- [x] 3.1 更新 `openspec/specs/clone-command/spec.md` 中 OpenCode plugin 路徑與分發格式描述
- [x] 3.2 更新 `openspec/specs/opencode-plugin/spec.md` 中 plugin 分發目標與載入契約描述
- [x] 3.3 更新專案文件中所有 `~/.config/opencode/plugin` 舊路徑為 `~/.config/opencode/plugins`

## 4. 測試與驗證

- [x] 4.1 新增或更新測試，覆蓋 `plugin` → `plugins` 路徑遷移行為
- [x] 4.2 新增或更新測試，覆蓋 `plugins/` 第一層 entry 檔存在與可載入契約
- [x] 4.3 新增或更新測試，覆蓋 legacy 路徑偵測與相容遷移流程
- [x] 4.4 執行相關測試與手動驗證，確認 OpenCode plugin 分發與載入行為符合規格
