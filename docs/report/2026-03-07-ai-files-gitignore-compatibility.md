# AI 文件 .gitignore 相容性調查報告

**日期：** 2026-03-07
**背景：** 評估將專案層級 AI 設定檔（rules、commands、skills 等）放入 .gitignore 或 .git/info/exclude 後，各 AI 工具是否能正常運作。

---

## 調查結論

### 總結矩陣

| 工具 | 設定載入 | Read（直接路徑） | Search/Grep | 整體結論 |
|------|:---:|:---:|:---:|------|
| **Claude Code** | OK | OK | Grep 跳過，Glob 可讀 | **可行** |
| **Codex CLI** | OK | OK | 搜尋跳過 | **可行** |
| **OpenCode** | OK | OK | 搜尋跳過 | **可行** |
| **Gemini CLI** | OK | read_file 拒絕 | 搜尋跳過 | **部分可行** |
| **Antigravity** | 不載入 | 不索引 | 不索引 | **不可行** |

### 關鍵發現

設定載入（config loading）和工具存取（tool access）是兩套獨立機制：

1. **設定載入**（CLAUDE.md、AGENTS.md、GEMINI.md）：除 Antigravity 外，所有工具都走 filesystem，不檢查 .gitignore
2. **工具存取**（Read、Grep、Glob）：大多數搜尋功能跳過 gitignored 檔案，但直接路徑讀取通常可行

### .git/info/exclude vs .gitignore

| 方式 | 效果 | 優點 | 缺點 |
|------|------|------|------|
| `.gitignore` | 所有人共享排除規則 | 團隊一致 | Antigravity 不載入設定、Gemini CLI read_file 拒絕 |
| `.git/info/exclude` | 僅本地排除 | 所有工具正常（不影響工具的 gitignore 檢查） | 每位開發者需自行設定 |

**建議：** 使用 `.git/info/exclude` 可避免所有工具相容性問題，因為工具檢查的是 `.gitignore` 檔案而非 git 實際追蹤狀態。`.git/info/exclude` 的排除效果等同但不被工具的 gitignore parser 讀取。

---

## 各工具詳細分析

### Claude Code

**設定載入：** CLAUDE.md 透過目錄樹向上搜尋載入，使用 filesystem walk，不檢查 git 狀態。`.claude/settings.json`、`.claude/commands/`、`.claude/skills/` 同理。

**工具存取：**
- Glob：使用 `rg --files --no-ignore --hidden`，**不尊重** .gitignore
- Grep：使用 ripgrep 預設模式，**尊重** .gitignore（會跳過）
- Read：直接路徑讀取，**不受影響**
- Bash：完全不受影響

**`respectGitignore` 設定：** 僅影響 `@` file picker 自動完成，不影響工具本身。

**來源：** Claude Code Memory Docs、GitHub issues #20609、#26286、#16043

### Codex CLI

**設定載入：** AGENTS.md 使用 `std::fs::symlink_metadata()` 和 `tokio::fs::File::open()` 發現與讀取，`discover_project_doc_paths` 函數中無任何 gitignore 檢查。

**工具存取：**
- File search（@ picker）：尊重 .gitignore（`respect_gitignore: true`）
- 直接檔案操作：可存取 gitignored 檔案

**來源：** codex-rs/core/src/project_doc.rs、GitHub issue #2952

### OpenCode

**設定載入：** AGENTS.md 透過目錄樹向上搜尋載入，文件未提及 gitignore 過濾。

**工具存取：**
- grep/glob/list：使用 ripgrep，尊重 .gitignore
- read：直接路徑讀取，可能不受影響

**來源：** opencode.ai/docs/rules/、opencode.ai/docs/tools/

### Gemini CLI

**設定載入：** GEMINI.md 使用 `fs.access()` filesystem walk 載入，`findUpwardGeminiFiles` 中無 gitignore 過濾。

**工具存取：**
- read_file：**強制尊重 .gitignore**，會拒絕讀取 gitignored 檔案（回傳 "File path is ignored by configured ignore patterns"）
- 設定 `respectGitIgnore: false` 有 bug，部分工具仍會拒絕
- `.geminiignore` 的 `!` 否定模式無法覆寫 .gitignore

**來源：** gemini-cli issues #16980、#20586、#3382

### Google Antigravity

**設定載入：** **完全尊重 .gitignore 進行設定發現**。將 `.agents/` 加入 .gitignore 會導致 workflows 和 commands 偵測全部失效。

**工具存取：** 同樣受 .gitignore 限制。

**解決方案：** 使用 `.git/info/exclude` 代替 `.gitignore`（本地排除，不被 Antigravity 的 gitignore parser 讀取）。

**來源：** rulesync issue #817、Antigravity Codelab

---

## 結合 rulesync 的可行方案

### 推薦方案

```
git-tracked:
  .rulesync/           <- 唯一真相來源（~50 檔）
  rulesync.jsonc       <- 設定檔

locally generated (via .git/info/exclude):
  .claude/             <- rulesync generate 產生
  .gemini/             <- rulesync generate 產生
  .codex/              <- rulesync generate 產生
  CLAUDE.md            <- rulesync generate 產生
  AGENTS.md            <- rulesync generate 產生
```

### 開發者工作流程

1. `git clone <project>`
2. `ai-dev project init` 或 `rulesync generate`（生成工具設定檔）
3. 生成的檔案自動加入 `.git/info/exclude`
4. AI 工具正常讀取設定
5. PR 只包含 `.rulesync/` 的變更

---

## 工具比較（Ruler vs rulesync vs ai-rules-sync）

### 推薦：rulesync

| 面向 | Ruler | rulesync | ai-rules-sync |
|------|-------|----------|---------------|
| Stars | 2,519 | 854 | 15 |
| 貢獻者 | ~10 | 30 | 1 |
| Skills 支援 | 實驗性 | 完整 | 有 |
| Commands 支援 | 無 | 完整 | 部分 |
| Hooks 支援 | 無 | 完整 | 無 |
| MCP 支援 | 有 | 有 | 無 |
| Per-agent 差異化 | 無 | 有 | 有 |
| 檔案可 git 追蹤 | 可選 | 預設可 | 不可（symlink） |
| Import 匯入 | 無 | 有 | 有 |
| CI 檢查 | 無 | 有 | 無 |

**選擇 rulesync 的理由：** 功能覆蓋最完整（7 項功能全支援 Claude Code）、生成檔案為普通檔案、有 import 命令可從現有設定遷移、社群健康（30 contributors）。
