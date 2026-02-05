# Skills CLI 指南

> 開放代理技能生態系統的命令列工具

## 概述

`skills` 是一個用於開放代理技能生態系統的 CLI 工具，支援多種 AI 代理，包括：

- OpenCode
- Claude Code
- Codex
- Cursor
- Windsurf
- Roo Code
- Cline
- Goose
- GitHub Copilot
- Gemini CLI
- 以及其他 30+ 種代理

**套件資訊：**
- **版本：** 1.2.0
- **授權：** MIT
- **儲存庫：** https://github.com/vercel-labs/skills

---

## 安裝與使用

### 安裝技能

使用 `npx` 直接執行，無需全域安裝：

```bash
npx skills add vercel-labs/agent-skills
```

### 支援的來源格式

| 格式 | 範例 |
|------|------|
| GitHub 簡寫 | `npx skills add vercel-labs/agent-skills` |
| 完整 GitHub URL | `npx skills add https://github.com/vercel-labs/agent-skills` |
| 直接路徑 | `npx skills add https://github.com/vercel-labs/agent-skills/tree/main/skills/web-design-guidelines` |
| GitLab URL | 支援任何 Git URL |
| 本地路徑 | 支援本地目錄路徑 |

---

## 命令參考

### `add` - 新增技能

安裝技能到專案或使用者目錄。

```bash
npx skills add <source> [選項]
```

**選項：**

| 選項 | 說明 |
|------|------|
| `-g, --global` | 安裝到使用者目錄而非專案目錄 |
| `-a, --agent <agents...>` | 指定目標代理（如 `claude-code`、`codex`） |
| `-s, --skill <skills...>` | 安裝指定名稱的技能 |
| `-l, --list` | 僅列出可用技能，不安裝 |
| `-y, --yes` | 跳過所有確認提示 |
| `--all` | 安裝所有技能到所有代理（無提示） |

**範例：**

```bash
# 列出儲存庫中的技能
npx skills add vercel-labs/agent-skills --list

# 安裝特定技能
npx skills add vercel-labs/agent-skills --skill frontend-design --skill skill-creator

# 安裝到特定代理
npx skills add vercel-labs/agent-skills -a claude-code -a opencode

# 非互動式安裝
npx skills add vercel-labs/agent-skills --skill frontend-design -g -a claude-code -y
```

---

### `list` (別名: `ls`) - 列出已安裝技能

```bash
npx skills list
npx skills ls
```

列出目前已安裝的所有技能。

---

### `find` - 搜尋技能

```bash
npx skills find [query]
```

互動式搜尋或按關鍵字搜尋技能。

---

### `remove` (別名: `rm`) - 移除技能

```bash
npx skills remove [skills]
npx skills rm [skills]
```

移除已安裝的技能。

---

### `check` - 檢查更新

```bash
npx skills check
```

檢查已安裝技能是否有可用更新。

---

### `update` - 更新技能

```bash
npx skills update
```

將所有已安裝技能更新至最新版本。

---

### `init` - 建立技能範本

```bash
npx skills init [name]
```

建立新的 `SKILL.md` 範本檔案。

---

### `generate-lock` - 產生鎖定檔

```bash
npx skills generate-lock
```

將已安裝的技能對應到來源，用於追蹤更新。

---

## 儲存庫快取位置

當執行 `npx skills add` 時，CLI 會將儲存庫 clone 到系統暫存目錄：

```
/var/folders/.../T/skills-<隨機ID>
```

### 快取特性

| 項目 | 說明 |
|------|------|
| **位置** | macOS: `/var/folders/.../T/`<br>Linux: `/tmp/`<br>Windows: `%TEMP%` |
| **命名格式** | `skills-<6位隨機字元>` (如 `skills-C621fE`) |
| **特性** | 每次執行產生新目錄，使用後可能被系統清理 |
| **Clone 深度** | `--depth 1` 淺層 clone（僅取最新 commit） |

> [!NOTE]
> 這是暫時性快取，僅用於讀取技能資訊。實際安裝後的技能會複製/symlink 到目標代理目錄。

---

## 建立技能

若要讓你的技能支援 `npx skills add`，需要遵守以下格式規範。

### 基本結構

技能是包含 `SKILL.md` 檔案的目錄，使用 YAML frontmatter 格式：

```markdown
---
name: my-skill
description: What this skill does and when to use it
---

# My Skill

Instructions for the agent to follow when this skill is activated.

## When to Use

Describe the scenarios where this skill should be used.

## Steps

1. First, do this
2. Then, do that
```

### 必要欄位

| 欄位 | 說明 | 範例 |
|------|------|------|
| `name` | 技能唯一識別符（小寫，可用連字號） | `my-skill`、`code-reviewer` |
| `description` | 簡短說明技能用途 | `Review code for best practices` |

### 選用欄位

| 欄位 | 說明 |
|------|------|
| `metadata.internal` | 設為 `true` 可隱藏技能，不被一般搜尋發現 |

**內部技能範例：**

```markdown
---
name: my-internal-skill
description: An internal skill not shown by default
metadata:
  internal: true
---
```

> [!TIP]
> 內部技能僅在設定 `INSTALL_INTERNAL_SKILLS=1` 時可見且可安裝。適用於開發中的技能或僅供內部工具使用的技能。

---

## 技能發現位置

CLI 會在儲存庫中的以下位置搜尋技能：

### 標準搜尋路徑

| 類型 | 路徑 |
|------|------|
| **根目錄** | `/`（若包含 `SKILL.md`） |
| **通用技能目錄** | `skills/`、`skills/.curated/`、`skills/.experimental/`、`skills/.system/` |
| **代理專屬目錄** | `.agents/skills/`、`.agent/skills/`、`./skills/` |

### 代理專屬搜尋路徑

CLI 會搜尋以下代理專屬目錄：

```
.claude/skills/      .codex/skills/       .cursor/skills/
.gemini/skills/      .github/skills/      .goose/skills/
.opencode/skills/    .windsurf/skills/    .roo/skills/
.cline/skills/       .continue/skills/    .kiro/skills/
.openhands/skills/   .qwen/skills/        .trae/skills/
```

> [!NOTE]
> 若標準位置中未找到技能，CLI 會執行遞迴搜尋。

### 建議的儲存庫結構

```
my-skills-repo/
├── README.md
└── skills/
    ├── code-reviewer/
    │   └── SKILL.md
    ├── test-writer/
    │   └── SKILL.md
    └── .experimental/
        └── new-feature/
            └── SKILL.md
```

---

## 代理安裝路徑

不同代理的技能安裝路徑各異：

| 代理 | 安裝路徑 |
|------|----------|
| Claude Code | `.claude/skills/` |
| OpenCode | `.agent/skills/` |
| 其他代理 | 依代理規格而定 |

---

## 環境變數

| 變數 | 說明 |
|------|------|
| `INSTALL_INTERNAL_SKILLS` | 設為 `1` 或 `true` 以安裝內部技能 |
| `DISABLE_TELEMETRY` | 停用匿名使用量遙測 |

---

## 相容性與疑難排解

### 相容性注意事項

- 技能遵循共享規格，但某些功能（如 `allowed-tools` 或 `Hooks`）可能是代理專屬
- 建議在目標代理上測試技能相容性

### 常見問題排解

1. **安裝失敗**
   - 確認 `SKILL.md` frontmatter 格式正確
   - 檢查寫入權限

2. **技能未被識別**
   - 確認技能目錄結構正確
   - 確認 `name` 和 `description` 欄位已填寫

3. **更新問題**
   - 執行 `npx skills generate-lock` 重新對應來源

---

## 相關資源

- **官方儲存庫：** https://github.com/vercel-labs/skills
- **技能範例：** https://github.com/vercel-labs/agent-skills

---

*此文件翻譯整理自 [skills NPM 套件](https://www.npmjs.com/package/skills)*
