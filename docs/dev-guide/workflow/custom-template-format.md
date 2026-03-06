# 客製化模板與工具格式規範

本文件說明 `ai-dev` 支援的兩種客製化 repo 類型，以及各自的使用情境、目錄結構要求與工作流程。

---

## 概覽：兩種客製化 Repo

`ai-dev` 的資源管理分為兩條獨立管線：

| 類型 | 用途 | 指令 | 目標 |
|------|------|------|------|
| **客製化模板 repo** | 專案級 AI 配置（CLAUDE.md、.standards/ 等） | `init-from` | CWD（當前專案） |
| **客製化工具 repo** | 跨專案共用工具（skills/commands/agents） | `add-custom-repo` + `clone` | 全域目錄（~/.claude/ 等） |

---

## 客製化模板 Repo

### 用途

客製化模板 repo 包含特定專案類型（如 QDM、OpenCart）所需的 AI 輔助配置，直接放置到目標專案根目錄。

### 目錄結構

客製化模板 repo 的根目錄**應包含**以下類型的檔案：

```
qdm-ai-base/
├── CLAUDE.md              # AI 助理指令
├── GEMINI.md              # Gemini CLI 指令
├── AGENTS.md              # Agent 指令
├── .claude/
│   ├── commands/          # 專案專用指令
│   └── settings.json      # Claude Code 設定
├── .standards/            # 程式碼與開發規範
│   ├── commit-message.ai.yaml
│   └── ...
├── .editorconfig          # 編輯器設定
├── .gitattributes
└── .gitignore
```

### 限制

客製化模板 repo 的根目錄**不應包含** 5 個標準工具目錄：

```
agents/    ← 不應出現在模板根目錄
commands/  ← 不應出現在模板根目錄
hooks/     ← 不應出現在模板根目錄
plugins/   ← 不應出現在模板根目錄
skills/    ← 不應出現在模板根目錄
```

這些目錄屬於**客製化工具 repo**的職責，應透過 `add-custom-repo` 管理。

> **注意**：若模板 repo 包含上述目錄，`ai-dev init-from` 會顯示警告，但仍會繼續執行。

---

## 客製化工具 Repo

### 用途

客製化工具 repo 包含跨專案共用的 skills/commands/agents，透過 `ai-dev clone` 分發到全域目錄（`~/.claude/`、`~/.gemini/` 等）。

### 目錄結構

```
qdm-ai-tools/
├── agents/
│   └── <agent-name>/
├── commands/
│   └── <command-name>.md
├── hooks/
│   └── <hook-script>
├── plugins/
│   └── <plugin-name>/
└── skills/
    └── <skill-name>/
        └── SKILL.md
```

根目錄**必須包含**這 5 個目錄（可以是空目錄，但需有 `.gitkeep`）。

---

## 初始化工作流程

### 首次初始化

```bash
# 1. 在目標專案目錄執行
cd /path/to/my-project

# 2. 從模板 repo 初始化
ai-dev init-from ValorVie/qdm-ai-base
# 或使用完整 URL
ai-dev init-from https://github.com/ValorVie/qdm-ai-base

# 3. 智慧合併互動提示
#    [A] 附加到尾部  [I] 增量附加  [O] 覆蓋整份  [S] 跳過  [D] 顯示差異

# 4. 初始化完成後，.ai-dev-project.yaml 會記錄由模板管理的檔案
```

### 追蹤檔格式（.ai-dev-project.yaml）

```yaml
template:
  name: qdm-ai-base
  url: https://github.com/ValorVie/qdm-ai-base.git
  branch: main
  initialized_at: 2026-01-01T00:00:00+08:00
  last_updated: 2026-01-01T00:00:00+08:00

managed_files:
  - .claude/commands/tdd.md
  - .standards/commit-message.ai.yaml
  - CLAUDE.md
  - GEMINI.md
```

此檔案**應提交到 git**，讓團隊成員知道模板來源。

---

## 維護工作流程

### 更新模板到最新版本

```bash
# 在專案目錄執行
ai-dev init-from --update
```

此指令會：
1. 拉取模板 repo 的最新更新
2. 只對 `.ai-dev-project.yaml` 中 `managed_files` 列出的檔案重新走智慧合併
3. 更新 `.ai-dev-project.yaml` 的 `last_updated` 時間戳

### 更新所有模板 repo（不套用到專案）

```bash
# 更新所有 repos（含模板）但不修改專案檔案
ai-dev update
```

若模板 repo 有新 commit，`ai-dev update` 會提示：

```
模板 repo 有新更新：
  • qdm-ai-base
  在需要更新的專案目錄中執行：ai-dev init-from --update
```

---

## 與 clone 的互動

`ai-dev clone` 分發通用工具到全域目錄時，不受 `.ai-dev-project.yaml` 影響。

但若在有 `.ai-dev-project.yaml` 的專案目錄中執行 `ai-dev clone`，clone 會跳過已由模板管理的檔案，並顯示：

```
~ 跳過 .claude/commands/tdd.md（由 qdm-ai-base 管理）
```

---

## 如何建立新的客製化模板 Repo

1. 在 GitHub 建立新 repo（如 `my-org/ai-template`）
2. 加入專案配置檔（CLAUDE.md、.standards/ 等）
3. **不要**在根目錄加入 `agents/`、`commands/`、`skills/` 等標準工具目錄
4. 在目標專案執行：
   ```bash
   ai-dev init-from my-org/ai-template
   ```

---

## 相關資源

- `ai-dev init-from --help`：查看完整指令說明
- `ai-dev add-custom-repo --help`：客製化工具 repo 的管理
- [ai-dev-framework-architecture.md](./ai-dev-framework-architecture.md)：整體架構說明
