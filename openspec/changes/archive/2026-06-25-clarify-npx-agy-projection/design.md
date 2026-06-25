## Context

`migrate-gemini-cli-to-agy` 把使用者層級分發 target `gemini` → `agy`，但專案層級的 skills 來自外部工具 `npx skills`（vercel-labs/skills），其 agent 命名由該工具決定，與本專案內部 target 無關。`ai-dev` 在 `script/services/tools/update.py` 的 `_NPX_PROJECT_AGENTS` 顯式列出要安裝的 agent，避免 npx 預設 fanout 到 30+ 目錄。

### 調查證據（npx skills v1.5.1）

來源：已安裝套件 `~/.npm/_npx/.../node_modules/skills/README.md` 對照表 + `package.json` agent 清單 + 本專案 `update.py` docstring 實測註記。

- 支援的 agent：`claude-code`、`codex`、`opencode`、`antigravity`、`gemini-cli`、`kiro-cli`、`universal` 等；**無 `agy`／`antigravity-cli`**。
- 路徑對照：
  - `gemini-cli` → project `.agents/skills/`、global `~/.gemini/skills/`
  - `antigravity` → project `.agents/skills/`、global `~/.gemini/antigravity/skills/`
  - `universal` → project `.agents/skills/`、global `~/.config/agents/skills/`
- 實測（`update.py` docstring）：該 agent 列表在 project scope 只建立 `.agents/skills`、`.claude/skills`、`.kiro/skills`。

agy 的讀取路徑（已於前一變更實測 v1.0.12）：workspace `.agents/skills/`、global 共用 `~/.gemini/skills/`。

## Goals / Non-Goals

**Goals:**
- 明確記錄「npx 層不改名」的理由，並在程式碼留下澄清註解。

**Non-Goals:**
- 不改 `_NPX_PROJECT_AGENTS` 的內容（保留 `gemini-cli`）。
- 不改 `.gemini` 專案投影與 `project-template`。
- 不處理 `.gemini/commands/opsx/*.toml` 的內容遷移。

## Decisions

### 決策：保留 `gemini-cli` npx agent，僅加註解
- 理由：`gemini-cli` agent 的 project/global 路徑（`.agents/skills`、`~/.gemini/skills`）正是 agy 讀取處；保留即正確餵給 agy。npx skills 無 `agy` agent，改名會讓 `npx skills add -a ... agy` 失敗。
- 替代方案 A：改成 `antigravity` agent。其 global 路徑為 `~/.gemini/antigravity/skills`（IDE，agy 不讀的「無效」路徑），project 同為 `.agents/skills`。改了反而讓 global 落到 agy 不讀處。否決。
- 替代方案 B：移除 `gemini-cli`。project scope 其他 agent（codex/universal）也寫 `.agents/skills`，看似冗餘；但 global scope 下 `gemini-cli` 是唯一寫 `~/.gemini/skills`（agy 共用）的 agent，移除會讓 `-g` 全域安裝漏掉 agy。否決。

## Risks / Trade-offs

- [日後 npx skills 推出 `agy` agent，註解過期] → 註解明確標注「待 npx skills 推出 `agy` agent 前不得改名」，屆時另案處理。
- [`gemini-cli` 名稱看似遺漏未改] → 以註解說明係刻意保留，並指向本變更與 `migrate-gemini-cli-to-agy`。

## Open Questions

- `.gemini/commands/opsx/*.toml`（已退役 Gemini CLI 的 OpenSpec slash 指令投影）是否改用 agy 的 skill 機制？屬專案模板內容遷移，另案評估。
