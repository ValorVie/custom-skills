## 1. OpenCode Commands 目錄

- [x] 1.1 建立 `commands/opencode/` 目錄，從 `commands/claude/` 複製所有 .md 檔案（排除 README.md）
- [x] 1.2 移除所有檔案的 `allowed-tools` 和 `argument-hint` frontmatter 欄位，保留 `description`
- [x] 1.3 建立 `commands/opencode/README.md` 說明此目錄用途

## 2. OpenCode ecc-hooks Plugin

- [x] 2.1 建立 `plugins/ecc-hooks-opencode/` 目錄結構（plugin.ts、package.json）
- [x] 2.2 實作 `plugin.ts`：tool.execute.before hook（dev server 攔截、strategic compact 建議）
- [x] 2.3 實作 `plugin.ts`：tool.execute.after hook（code quality 腳本觸發，依副檔名分派）
- [x] 2.4 實作 `plugin.ts`：event hook（session.created → session-start.py、session.deleted → session-end.py + evaluate-session.py）
- [x] 2.5 實作 `plugin.ts`：experimental.session.compacting hook（pre-compact.py）
- [x] 2.6 複製 `plugins/ecc-hooks/scripts/` 到 `plugins/ecc-hooks-opencode/scripts/`（或建立同步機制）

## 3. CLI 分發邏輯更新

- [x] 3.1 在 `script/utils/paths.py` 新增 `get_opencode_plugin_dir()` 函式
- [x] 3.2 在 `script/utils/shared.py` 的 `COPY_TARGETS["opencode"]` 新增 `"plugins"` 項目
- [x] 3.3 更新 `copy_custom_skills_to_targets()` 中 opencode 平台的分發配置，加入 plugins 資源
- [x] 3.4 更新 `DEFAULT_TOGGLE_CONFIG["opencode"]` 加入 plugins 資源類型

## 4. 驗證

- [x] 4.1 確認 `commands/opencode/` 檔案數量與 `commands/claude/` 一致
- [x] 4.2 確認所有 opencode commands 不含 Claude 特有 frontmatter
- [x] 4.3 確認 plugin.ts 語法正確（TypeScript 型別檢查）
- [x] 4.4 確認 `ai-dev clone` 可正常分發 commands 和 plugin 到 OpenCode 目錄
