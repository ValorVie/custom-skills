# Oh My OpenCode 使用指南

## 簡介

**Oh My OpenCode** 是 OpenCode 的增強插件，被稱為「最佳 Agent Harness（代理框架）」。它將 OpenCode 轉變為一個強大的、開箱即用的 AI 開發環境，提供多模型協調、專業化代理團隊、背景任務並行執行等進階功能。

---

## 核心概念

### 主要特色

| 特色 | 說明 |
|------|------|
| **多模型協調** | 自動整合 Claude、GPT、Gemini 等多個 AI 模型，每個代理使用最適合的模型 |
| **專業化代理團隊** | 提供 11 個專門的 AI 代理，每個代理針對特定任務優化 |
| **背景任務並行** | 多個代理可以同時工作，像真實的開發團隊一樣 |
| **完整工具生態** | LSP/AST 重構工具、MCP 伺服器、瀏覽器自動化等 |
| **Claude Code 相容** | 完整支援 Commands、Skills、Agents、MCPs、Hooks |

### 代理團隊架構

#### 核心代理（6 個）

| 代理 | 預設模型 | 角色 | 工具權限 |
|-----|---------|------|----------|
| **Sisyphus** | Claude Opus 4.5 | 主要編排者，使用專業子代理進行並行執行 | 全部權限 |
| **Hephaestus** | GPT 5.2 Codex | 自治深度工作者，目標導向執行 | 全部權限 |
| **Oracle** | GPT 5.2 | 架構決策、程式碼審查、除錯 | 唯讀 |
| **Librarian** | GLM-4.7 | 多倉庫分析、文件查詢、開源實作範例 | 唯讀 |
| **Explore** | Claude Haiku 4.5 | 快速程式碼庫探索 | 唯讀 |
| **Multimodal-Looker** | Gemini 3 Flash | 視覺內容專家（PDF、圖片、圖表） | 白名單 |

#### 規劃代理（3 個）

- **Prometheus (Planner)**：策略規劃者，透過面試建立詳細工作計劃
- **Metis (Plan Consultant)**：規劃前分析，識別隱藏意圖和歧義
- **Momus (Plan Reviewer)**：驗證計劃是否符合清晰度、可驗證性和完整性標準

---

## 安裝設定

### 前置條件

- **OpenCode** 已安裝（v1.0.150 或更新）
- 支援平台：macOS (ARM64, x64)、Linux (x64, ARM64)、Windows (x64)

### 推薦安裝方式

將以下提示詞貼上給 LLM 代理：

```
Install and configure oh-my-opencode by following the instructions here:
https://raw.githubusercontent.com/code-yeongyu/oh-my-opencode/refs/heads/master/docs/guide/installation.md
```

### 手動安裝

```bash
# 推薦使用 Bun
bunx oh-my-opencode install

# 或使用 npx
npx oh-my-opencode install
```

安裝時會自動：
1. 註冊插件到 `~/.config/opencode/opencode.json`
2. 根據訂閱旗標配置代理模型
3. 顯示需要哪些認證步驟

### 提供者配置

安裝時會詢問以下問題：

| 問題 | 選項 | 用途 |
|------|------|------|
| Claude Pro/Max 訂閱？ | `--claude=<yes|no|max20>` | Sisyphus 主代理 |
| OpenAI/ChatGPT Plus 訂閱？ | `--openai=<yes|no>` | Oracle 代理 |
| Gemini 整合？ | `--gemini=<yes|no>` | Frontend UI/UX 工程師代理 |
| GitHub Copilot 訂閱？ | `--copilot=<yes|no>` | 後援提供者 |
| OpenCode Zen 存取？ | `--opencode-zen=<yes|no>` | opencode/ 模型 |
| Z.ai Coding Plan 訂閱？ | `--zai-coding-plan=<yes|no>` | GLM-4.7 模型（Librarian） |

### 認證設定

#### Anthropic (Claude)

```bash
opencode auth login
# 選擇 Provider: Anthropic
# 選擇 Login method: Claude Pro/Max
```

#### Google Gemini（推薦使用 opencode-antigravity-auth）

1. 新增插件：

```json
{
  "plugin": [
    "oh-my-opencode",
    "opencode-antigravity-auth@latest"
  ]
}
```

2. 配置代理模型覆蓋：

```json
{
  "agents": {
    "multimodal-looker": { "model": "google/antigravity-gemini-3-flash" }
  }
}
```

3. 認證：

```bash
opencode auth login
# Provider: Google
# Login method: OAuth with Google (Antigravity)
```

**注意**：支援最多 10 個 Google 帳號做負載平衡

---

## 使用方法

### 工作模式

#### 模式 1：Ultrawork 模式（快速工作）

在提示詞中加入 `ultrawork` 或 `ulw`：

```bash
ulw add authentication to my Next.js app
```

代理會自動：
1. 探索程式碼庫以了解現有模式
2. 透過專業代理研究最佳實踐
3. 遵循慣例實作功能
4. 使用診斷工具和測試驗證
5. 持續工作直到完成

#### 模式 2：Prometheus 模式（精密工作）

對於複雜或關鍵任務，按 **Tab** 切換到 Prometheus（Planner）模式：

```
1. 按 Tab → 進入 Prometheus 模式
2. 描述工作 → Prometheus 面試你
3. 確認計劃 → 審閱 .sisyphus/plans/*.md
4. 執行 /start-work → Atlas 接手執行
```

### 常用斜槓命令

| 命令 | 描述 |
|------|------|
| `/init-deep` | 初始化階層式 AGENTS.md 知識庫 |
| `/ralph-loop` | 啟動自我參照開發循環直到完成 |
| `/ulw-loop` | 啟動 ultrawork 循環 |
| `/refactor` | 智慧重構（LSP、AST-grep、架構分析） |
| `/start-work` | 從 Prometheus 計劃啟動 Sisyphus 工作階段 |

### 委派給專業代理

```typescript
// 明確指定代理
Ask @oracle to review this design
Ask @librarian how this is implemented
Ask @explore for the policy on this feature

// 透過 delegate_task 工具
delegate_task(agent="oracle", prompt="Review this architecture")
delegate_task(subagent_type="explore", prompt="Find auth implementations", run_in_background=true)
```

### 背景任務並行處理

```typescript
// 發動多個背景代理同時工作
delegate_task(
  subagent_type="explore",
  load_skills=[],
  prompt="Find auth implementations",
  run_in_background=true
)

delegate_task(
  subagent_type="librarian",
  load_skills=[],
  prompt="Search documentation",
  run_in_background=true
)

// 繼續實作...

// 當需要時獲取結果
background_output(task_id="bg_abc123")
background_output(task_id="bg_def456")
```

---

## 最佳實踐

### 1. 分類模型配置

**⚠️ 關鍵**：分類不會使用其內建預設，除非你進行配置。

#### 如何觸發分類

分類是透過 `delegate_task()` 的 `category` 參數自動觸發：

```typescript
// 視覺工程任務 → 自動使用 visual-engineering 配置的模型
delegate_task(
  category="visual-engineering",
  load_skills=["frontend-ui-ux"],
  prompt="Create a responsive navbar with animations"
)

// 複雜邏輯任務 → 自動使用 ultrabrain 配置的模型
delegate_task(
  category="ultrabrain",
  load_skills=[],
  prompt="Design a distributed consensus algorithm"
)

// 簡單任務 → 自動使用 quick 配置的模型
delegate_task(
  category="quick",
  load_skills=["git-master"],
  prompt="Fix the typo in README"
)
```

**系統會根據 `category` 自動選擇對應的模型**，無需手動指定。

#### 可用分類與使用時機

| 分類 | 使用時機 | 推薦模型 |
|------|----------|----------|
| `visual-engineering` | 前端、UI/UX、設計、樣式、動畫 | Gemini 3 Pro |
| `ultrabrain` | 複雜邏輯、演算法、架構設計 | GPT 5.2 Codex |
| `artistry` | 非傳統問題、創意解法 | Gemini 3 Pro |
| `quick` | 簡單修改、單檔案變更、錯字修正 | Claude Haiku |
| `unspecified-low` | 未分類的低複雜度任務 | Claude Sonnet |
| `unspecified-high` | 未分類的高複雜度任務 | Claude Opus |
| `writing` | 文件撰寫、技術寫作 | Gemini 3 Flash |

#### 自然語言使用方式

**分類不是由使用者直接觸發，而是由 Sisyphus 根據任務類型自動分配**：

```
使用者：幫我設計一個響應式導航列
Sisyphus：→ 自動識別為 visual-engineering 任務
       → 委派給使用 Gemini 3 Pro 的代理

使用者：我需要實作一個分散式共識演算法
Sisyphus：→ 自動識別為 ultrabrain 任務
       → 委派給使用 GPT 5.2 的代理

使用者：修復 README 裡的錯字
Sisyphus：→ 自動識別為 quick 任務
       → 委派給使用 Claude Haiku 的代理
```

**你也可以明確指定分類**：

```
這是一個前端設計問題，請用 visual-engineering 方式處理
這個演算法很複雜，需要 ultrabrain 來解決
這只是個小修改，用 quick 模式就好
```

**注意**：`ultrawork` / `ulw` 關鍵字觸發的是**工作模式**（啟動完整代理團隊），不是單一的分類。在 Ultrawork 模式下，Sisyphus 會自動根據子任務類型選擇適合的分類。

**推薦配置**（`~/.config/opencode/oh-my-opencode.json`）：

```jsonc
{
  "$schema": "https://raw.githubusercontent.com/code-yeongyu/oh-my-opencode/master/assets/oh-my-opencode.schema.json",
  "categories": {
    "visual-engineering": { 
      "model": "google/gemini-3-pro-preview"
    },
    "ultrabrain": { 
      "model": "openai/gpt-5.2-codex",
      "variant": "xhigh"
    },
    "artistry": { 
      "model": "google/gemini-3-pro-preview",
      "variant": "max"
    },
    "quick": { 
      "model": "anthropic/claude-haiku-4-5"
    },
    "unspecified-low": { 
      "model": "anthropic/claude-sonnet-4-5"
    },
    "unspecified-high": { 
      "model": "anthropic/claude-opus-4-5",
      "variant": "max"
    },
    "writing": { 
      "model": "google/gemini-3-flash-preview"
    }
  }
}
```

### 2. 使用 Prometheus + Orchestrator

**❌ 不要**直接使用 `atlas` 而不使用 `/start-work`。

**正確工作流程**：
```
1. 按 Tab → 進入 Prometheus 模式
2. 描述工作 → Prometheus 面試你
3. 確認計劃 → 審閱 .sisyphus/plans/*.md
4. 執行 /start-work → Atlas 執行
```

### 3. Tmux 整合

啟動 Tmux 整合以查看背景代理：

```json
{
  "tmux": {
    "enabled": true,
    "layout": "main-vertical",
    "main_pane_size": 60,
    "main_pane_min_width": 120,
    "agent_pane_min_width": 40
  }
}
```

**布局選項**：
- `main-vertical`：主 pane 左側，代理 pane 堆疊在右側（預設）
- `main-horizontal`：主 pane 上方，代理 pane 堆疊在下方
- `tiled`：所有 pane 等大小網格

### 4. Ollama 提供者設定

**⚠️ 重要**：使用 Ollama 時必須停用串流：

```json
{
  "agents": {
    "explore": {
      "model": "ollama/qwen3-coder",
      "stream": false
    }
  }
}
```

### 5. 背景任務最佳實踐

- 使用快速/便宜的模型進行背景搜尋
- 使用昂貴/智慧模型進行主要實作
- 避免在背景任務中進行寫入操作

---

## 內建工具

### Skills

#### Playwright（瀏覽器自動化）

```bash
/playwright Navigate to example.com and take a screenshot
```

支援：導航、截圖、填寫表單、點擊元素、等待網路請求

#### Git Master

```bash
/git-master commit these changes
/git-master rebase onto main
/git-master who wrote this code?
```

功能：原子性提交、歷史重寫、分支清理、尋找特定變更

### MCP 伺服器

- **websearch (Exa AI)**：即時網頁搜尋
- **context7**：官方文件查詢
- **grep.app**：公開 GitHub 倉庫的超快速程式碼搜尋

---

## 常見使用場景

### 快速功能實作

```bash
ulw add authentication to my Next.js app
```

### 程式碼庫理解和除錯

```bash
Ask @librarian how this authentication works
Ask @explore for the policy on this feature
```

### 視覺化工程任務

```bash
delegate_task(category="visual-engineering", prompt="Create a responsive dashboard")
```

### Git 工作流程

```bash
/git-master commit these changes
```

自動將大型變更分割成多個小提交

### 多天專案規劃

```
1. 按 Tab → Prometheus 模式
2. 描述工作 → Prometheus 面試你
3. 確認計劃 → 審閱 .sisyphus/plans/*.md
4. 執行 /start-work → Atlas 分發任務
```

---

## 參考資源

- **GitHub**: https://github.com/code-yeongyu/oh-my-opencode
- **安裝指南**: https://github.com/code-yeongyu/oh-my-opencode/blob/master/docs/guide/installation.md
- **功能文件**: https://github.com/code-yeongyu/oh-my-opencode/blob/master/docs/features.md
- **配置說明**: https://github.com/code-yeongyu/oh-my-opencode/blob/master/docs/configurations.md
