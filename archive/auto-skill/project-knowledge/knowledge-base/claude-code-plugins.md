## 🔧 Claude Code Plugin 架構與目錄結構
**日期：** 2026-02-26
**情境：** 建立新的 Claude Code plugin 時需要了解正確的目錄結構
**最佳實踐：**
- Plugin 目錄結構必須遵循：
  ```
  plugin-name/
  ├── .claude-plugin/
  │   └── plugin.json       # 只有 plugin.json 放這裡
  ├── skills/               # Agent Skills（SKILL.md）
  ├── commands/              # 指令（markdown）
  ├── agents/                # 自訂 agent
  ├── hooks/
  │   └── hooks.json         # Hook 事件設定
  ├── scripts/               # Hook 腳本（放 plugin 內，不跨目錄引用）
  ├── .mcp.json              # MCP server 設定
  ├── .lsp.json              # LSP server 設定
  └── settings.json          # 預設 settings
  ```
- **不要**把 commands/agents/skills/hooks 放進 `.claude-plugin/` 目錄
- Hook 腳本路徑用 `${CLAUDE_PLUGIN_ROOT}/scripts/xxx.js`，不要用 `../` 跨目錄引用
- Plugin 中的 skill 會自動加上 namespace 前綴：`/plugin-name:skill-name`

## 🔧 Marketplace 註冊與 Plugin 安裝流程
**日期：** 2026-02-26
**情境：** 新建的 plugin 無法在 `/plugins` 或 `/plugin install` 中找到
**最佳實踐：**
- **Source of truth** 是 repo 根目錄的 `.claude-plugin/marketplace.json`（不是 `~/.claude/` 裡的副本）
- 新 plugin 必須在此檔案的 `plugins` 陣列中註冊：
  ```json
  {
    "name": "plugin-name",
    "source": "./plugins/plugin-name",
    "description": "描述",
    "version": "1.0.0",
    "author": { "name": "custom-skills" }
  }
  ```
- 安裝指令：`/plugin install plugin-name@marketplace-name`
- `~/.claude/plugins/marketplaces/` 是 clone/sync 的副本，更新流程：
  1. 修改 repo 的 `.claude-plugin/marketplace.json`
  2. 同步到 `~/.claude/plugins/marketplaces/custom-skills/`（syncthing 或手動）
  3. 重啟 Claude Code
  4. `/plugin install custom-skills-notify@custom-skills`
- Plugin 啟用後會寫入 `~/.claude/settings.json` 的 `enabledPlugins`，格式為 `"plugin-name@marketplace-name": true`

## 🔧 Hook 腳本最佳實踐
**日期：** 2026-02-26
**情境：** 撰寫 Claude Code hook 腳本時的關鍵注意事項
**最佳實踐：**
- Hook 從 **stdin** 接收 JSON（不是環境變數），共用欄位：`session_id`, `transcript_path`, `cwd`, `hook_event_name`
- `async: true` 讓 hook 在背景執行，不阻塞 Claude
- 失敗時總是 `exit 0`（通知/日誌類 hook 不應中斷 Claude）
- hooks.json 中每個 hook group 需要 `"matcher": "*"`（即使要匹配所有事件）
- 發送 Telegram 訊息不要用 `parse_mode: "HTML"`，因為 hook payload 中的錯誤訊息可能包含 `<>`，會破壞 HTML 解析

## 🔧 Skill 的 Frontmatter 欄位
**日期：** 2026-02-26
**情境：** 設定 skill 的觸發方式和權限
**最佳實踐：**
- `name` — skill 名稱
- `description` — 描述，讓 Claude 知道何時使用
- `disable-model-invocation: true` — 只有使用者可透過 `/skill-name` 觸發，Claude 不會自動呼叫
- `allowed-tools` — 限制 skill 可使用的工具
- 沒有 `user_invocable` 這個欄位（不存在）
- 不設定 `disable-model-invocation` 時，Claude 會根據 description 自動判斷何時使用
