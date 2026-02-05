---
tags:
  - ai
  - comparison
  - opencode
  - claude-code
  - dev-stack
date created: 2026-02-01T12:00:00+08:00
date modified: 2026-02-01T12:00:00+08:00
description: OpenCode 與 Claude Code AI 開發工具的完整比較分析
---

# OpenCode vs Claude Code 比較分析

本文比較 OpenCode 與 Claude Code 兩個 AI 輔助開發工具的優劣，分析各自特色功能，並提供選擇建議。

---

## 目錄

1. [架構與生態對比](#架構與生態對比)
2. [特色功能比較](#特色功能比較)
3. [相同模型下的效能比較](#相同模型下的效能比較)
4. [各擅長領域](#各擅長領域)
5. [結論與建議](#結論與建議)

---

## 架構與生態對比

| 維度 | Claude Code | OpenCode |
|------|-------------|----------|
| **開發商** | Anthropic (官方) | 社群開源 |
| **核心模型** | 專注 Claude 模型 | 多模型支援 (Claude/GPT/Gemini/GLM) |
| **Plugin 生態** | 官方 Marketplace + 社群市場 | Plugin 系統 (規模較小) |
| **Hooks 系統** | ✅ Python hooks (SessionStart/End 等) | ❌ 無原生 hooks |
| **Skills/Commands** | ✅ 完整支援 | ✅ 共用 `~/.claude/` 目錄 |
| **Agents** | ✅ 內建 + Plugin 擴展 | ✅ 可自訂 Agent |
| **Workflows** | ✅ YAML workflow | ❌ 無原生 workflow |
| **設定檔位置** | `~/.claude.json` | `~/.config/opencode/opencode.json` |
| **Skills 目錄** | `~/.claude/skills/` | `~/.claude/skills/` (共用) |

### 配置目錄結構

```
~/.claude/                    # Claude Code 主目錄
├── CLAUDE.md                 # 全域用戶指南
├── skills/                   # Skills (OpenCode 共用)
├── commands/                 # Commands (OpenCode 共用)
├── agents/                   # Agents
└── workflows/                # YAML Workflows

~/.config/opencode/           # OpenCode 主目錄
├── opencode.json             # 主設定檔
├── oh-my-opencode.json       # oh-my-opencode 設定
├── agent/                    # 自訂 Agents
└── plugin/                   # Plugins
```

---

## 特色功能比較

### Claude Code 獨有優勢

#### 1. 完整的 Hooks 系統

Claude Code 支援生命週期 Hooks，可在特定事件執行自訂邏輯：

| Hook 類型 | 觸發時機 |
|----------|----------|
| `SessionStart` | 對話開始時 |
| `SessionEnd` | 對話結束時 |
| `PromptSubmit` | 用戶提交提示前 |
| `ToolUse` | 工具呼叫前 |
| `ToolResult` | 工具結果返回後 |

**ECC (Everything Claude Code) 整合範例**：

```python
# memory-persistence hook
def session_start():
    load_conversation_history()

def session_end():
    save_conversation_history()
```

#### 2. 豐富的 Plugin 生態

```shell
# 官方插件
/plugin install code-simplifier
/plugin install ralph-loop
/plugin install php-lsp
/plugin install frontend-design

# 社群市場
/plugin marketplace add obra/superpowers-marketplace
/plugin marketplace add wshobson/agents  # 72+ 分類

# 查看已安裝
/plugin list
/agents
```

**常用 Plugin 分類**：

| 分類 | Plugin 數量 | 範例 |
|------|------------|------|
| Python 開發 | 3 agents + 5 skills | python-development, django-pro, fastapi-pro |
| K8s 運維 | 1 agent + 4 skills | kubernetes-operations |
| 測試 | 多個 | e2e-runner, test-specialist |
| 安全 | 1 agent | security-reviewer |

#### 3. Ralph Loop 批次任務

```shell
# 迭代執行直到完成
/ralph-loop:ralph-loop "根據目前變更跟計畫比對，review 是否有錯誤" --completion-promise "計畫驗證完畢"

# 設定最大迭代次數
/ralph-loop:ralph-loop "..." --max-iterations 20
```

適合需要多次嘗試才能完成的任務。

#### 4. YAML Workflows

```yaml
# feature-dev.workflow.yaml
name: Feature Development
steps:
  - name: Plan
    agent: code-architect
  - name: Implement
    agent: specialist
  - name: Test
    agent: test-specialist
  - name: Review
    agent: reviewer
```

#### 5. 官方 MCP 整合

```shell
claude mcp add context7 --scope user -- npx @upstash/context7-mcp
claude mcp list
claude mcp remove <name>
```

---

### OpenCode + oh-my-opencode 獨有優勢

#### 1. 多模型整合 (Sisyphus Agent)

同時整合多個 AI 提供者，彈性配置：

```json
{
  "$schema": "https://raw.githubusercontent.com/code-yeongyu/oh-my-opencode/master/assets/oh-my-opencode.schema.json",
  "agents": {
    "Sisyphus": {
      "model": "openai/gpt-5.2-codex"
    },
    "librarian": {
      "model": "opencode/glm-4.7-free"
    },
    "explore": {
      "model": "opencode/glm-4.7-free"
    },
    "frontend-ui-ux-engineer": {
      "model": "openai/gpt-5.2-codex"
    },
    "document-writer": {
      "model": "opencode/glm-4.7-free"
    },
    "multimodal-looker": {
      "model": "opencode/glm-4.7-free"
    }
  }
}
```

**支援的模型提供者**：

| 提供者 | 模型範例 | 用途 |
|--------|---------|------|
| OpenAI | gpt-5.2-codex | 核心開發 |
| Anthropic | claude-sonnet-4, claude-opus-4 | 推理任務 |
| Google | gemini-2.5-flash | 快速回應 |
| 智譜 AI | glm-4.7-free | 免費輔助 |

#### 2. ultrawork 模式

在提示詞中加入 `ultrawork` (或簡寫 `ulw`) 啟用所有增強功能：

```shell
# 啟用 ultrawork 模式
請幫我重構這個模組 ultrawork

# 簡寫
實作用戶登入功能 ulw
```

**ultrawork 功能**：

| 功能 | 說明 |
|------|------|
| **平行代理** | 自動將任務分配給多個 Agent 並行處理 |
| **深度探索** | 徹底分析程式碼庫結構 |
| **不間斷執行** | 持續執行直到任務完成 |
| **背景任務** | 長時間任務在背景執行 |

#### 3. 彈性的 Agent 設定

**全域 Agent** (`~/.config/opencode/agent/`)：

```markdown
---
description: Reviews code for quality and best practices
mode: subagent
model: anthropic/claude-sonnet-4-20250514
temperature: 0.1
tools:
  write: false
  edit: false
  bash: false
---

You are in code review mode. Focus on:
- Code quality and best practices
- Potential bugs and edge cases
- Performance implications
- Security considerations
```

**專案 Agent** (`.opencode/agent/`)：

專案級別的 Agent 設定會覆蓋全域設定。

#### 4. 認證管理

```shell
# 查看認證狀態
opencode auth list

# 新增認證
opencode auth login  # 選擇提供者

# 登出
opencode auth logout
```

#### 5. 共用 Claude Skills 生態

OpenCode 直接使用 `~/.claude/skills/` 和 `~/.claude/commands/`，無需重複設定：

```
~/.claude/skills/  ← Claude Code 和 OpenCode 共用
├── commit-standards/
├── code-review-assistant/
├── testing-guide/
└── ...
```

---

## 相同模型下的效能比較

**前提：使用相同模型 (例如 Claude Sonnet 4.5)**

| 任務類型 | Claude Code | OpenCode + oh-my-opencode | 說明 |
|----------|-------------|---------------------------|------|
| **單一複雜任務** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Claude Code 整合性更好 |
| **並行多任務** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | oh-my-opencode 平行處理強大 |
| **長時間執行** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Sisyphus 不間斷執行 |
| **程式碼探索** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | explore Agent 深度探索 |
| **Plugin 擴展** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | Claude Code 生態豐富 |
| **成本控制** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 免費模型整合優勢 |
| **推理品質** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 相同模型下相同 |
| **工作流自動化** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | YAML Workflows |
| **Hooks 整合** | ⭐⭐⭐⭐⭐ | ⭐ | Claude Code 獨有 |
| **企業級穩定性** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 官方支援優勢 |

---

## 各擅長領域

### Claude Code 更擅長

1. **深度推理任務**
   - Claude 模型推理能力最強
   - 適合複雜的邏輯分析

2. **需要 Plugin 生態**
   - 豐富的官方/社群插件
   - 72+ 分類的專業插件

3. **工作流自動化**
   - YAML Workflows 定義流程
   - Hooks 系統整合生命週期

4. **批次迭代任務**
   - Ralph Loop 機制
   - 適合需要多次嘗試的任務

5. **企業級使用**
   - 官方支援
   - 穩定性高
   - 文件完整

### OpenCode + oh-my-opencode 更擅長

1. **成本敏感專案**
   - 免費模型整合 (GLM-4.7-free)
   - 彈性配置付費/免費模型分工

2. **需要多模型協作**
   - GPT + Claude + Gemini 混合
   - 各取所長

3. **大型程式碼庫探索**
   - explore Agent + 平行處理
   - 深度分析

4. **長時間背景任務**
   - Sisyphus 不間斷執行
   - 直到完成為止

5. **彈性 Agent 配置**
   - 自訂 Agent 模型分工
   - 精細控制成本與效能

---

## 結論與建議

### 選擇 Claude Code 當

- 需要最佳推理品質
- 使用豐富的 Plugin 生態
- 需要官方支援與穩定性
- 以 Claude 模型為主
- 需要工作流自動化 (Workflows + Hooks)

### 選擇 OpenCode + oh-my-opencode 當

- 需要成本控制（免費模型）
- 需要多模型混合使用
- 大型程式碼庫深度探索
- 需要平行處理能力
- 想要彈性配置 Agent

### 最佳策略：兩者並用

```
┌─────────────────────────────────────────────────────────────┐
│                    ~/.config/custom-skills/                  │
│                    (統一 Skills 管理目錄)                     │
│  ├── skills/      # 共用 Skills                             │
│  ├── commands/    # 工具專屬 Commands                       │
│  └── agents/      # 工具專屬 Agents                         │
└─────────────────────────────────────────────────────────────┘
                              ↓
      ┌───────────┬───────────┐
      ↓           ↓           ↓
┌──────────┐ ┌──────────┐ ┌──────────┐
│~/.claude/│ │~/.config/│ │~/.gemini/│
│ Claude   │ │opencode/ │ │antigrav. │
│  Code    │ │OpenCode  │ │          │
└──────────┘ └──────────┘ └──────────┘
```

**使用建議**：

| 場景 | 使用工具 |
|------|----------|
| 深度推理、複雜邏輯 | Claude Code |
| 快速探索、成本敏感 | OpenCode + ultrawork |
| 需要 Plugin 功能 | Claude Code |
| 長時間背景任務 | OpenCode + Sisyphus |
| 程式碼審查 | Claude Code (reviewer agent) |
| 大型重構 | OpenCode (explore + parallel) |

**共用資源配置**：

兩者共用相同的 Skills 目錄 (`~/.claude/skills/`)，無需重複設定：

```bash
# 統一複製 Skills
cp -r ~/.config/custom-skills/skills/* ~/.claude/skills/

# Claude Code 自動使用
claude

# OpenCode 自動使用
opencode
```

---

## 相關文件

- [AI 開發環境設定指南](AI開發環境設定指南.md) - 完整安裝與設定流程
- [Skill-Command-Agent差異說明](Skill-Command-Agent差異說明.md) - 了解三者差異
- [copy-architecture](copy-architecture.md) - 複製架構與目錄結構
- [oh-my-opencode GitHub](https://github.com/code-yeongyu/oh-my-opencode) - oh-my-opencode 原始碼
- [Claude Code 官方文件](https://docs.anthropic.com/en/docs/claude-code/overview) - Claude Code 官方文件
