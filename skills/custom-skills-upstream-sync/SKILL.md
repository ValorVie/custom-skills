---
name: custom-skills-upstream-sync
description: |
  Sync upstream third-party repositories and generate diff reports for review.
  Use when: checking for upstream updates, syncing third-party resources, reviewing changes before merging.
  Triggers: "sync upstream", "check upstream updates", "upstream sync", "sync repos", "上游同步", "同步上游".
---

# Upstream Sync | 上游同步

分析上游 repository 的 commit 變更，生成結構化報告供後續分析使用。
支援分析已註冊的上游 repo，或評估全新的本地 repo。

## Quick Start

```bash
# 分析所有上游 repo，生成報告
python skills/custom-skills-upstream-sync/scripts/analyze_upstream.py

# 只分析特定 repo
python skills/custom-skills-upstream-sync/scripts/analyze_upstream.py --source superpowers

# 分析並更新同步狀態
python skills/custom-skills-upstream-sync/scripts/analyze_upstream.py --update-sync

# 評估新的本地 repo（全量分析）
python skills/custom-skills-upstream-sync/scripts/analyze_upstream.py --new-repo ~/.config/some-new-repo
```

## 功能

### 1. Commit 差異分析（已註冊 repo）
- 比較上次同步 commit 與目前 HEAD
- 解析每個 commit 的類型（feat, fix, refactor, docs 等）
- 統計變更檔案數、新增/刪除行數

### 2. 新 Repo 評估（--new-repo）
- 全量分析本地 repo 內容
- 掃描 skills/agents/commands/hooks 等目錄
- 評估是否適合整合進專案
- 生成評估報告到 `upstream/reports/new-repos/`

### 3. 檔案變更分類
自動將變更檔案分類為：
- `skills` - Skill 相關
- `agents` - Agent 相關
- `commands` - Command 相關
- `rules` - Rules 相關
- `hooks` - Hooks 相關
- `contexts` - Contexts 相關
- `docs` - 文件
- `other` - 其他

### 4. 整合建議

**已註冊 repo：**

| 等級 | 條件 | 說明 |
|------|------|------|
| 🔴 **High** | 多個新功能/重要變更 | 建議優先整合 |
| 🟡 **Medium** | 有價值的變更 | 建議評估整合 |
| 🟢 **Low** | 小幅變更 | 可選擇性整合 |
| ⚪ **Skip** | 無變更或僅文件 | 可跳過 |

**新 repo 評估：**

| 等級 | 條件 | 說明 |
|------|------|------|
| 🔵 **Evaluate** | 包含 skills/agents/commands | 建議詳細評估 |
| 🟡 **Review** | 包含 hooks 或大量文件 | 可參考部分內容 |
| ⚪ **Skip** | 無可整合內容 | 不適合整合 |

### 5. 報告輸出

**已註冊 repo 報告：**
```
upstream/reports/structured/analysis-YYYY-MM-DD.yaml
```

**新 repo 評估報告：**
```
upstream/reports/new-repos/eval-{repo-name}-{timestamp}.yaml
```

## 工作流程

### 日常同步流程

```
┌─────────────────────────────────────────────────────────────┐
│                   UPSTREAM ANALYSIS WORKFLOW                 │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. 載入配置                                                 │
│     ├── 讀取 upstream/sources.yaml                          │
│     └── 讀取 upstream/last-sync.yaml                        │
│                        ↓                                     │
│  2. 分析每個 Repo                                            │
│     ├── 比較 last_synced_commit 與 HEAD                     │
│     ├── 解析 commit 列表與類型                               │
│     ├── 分類變更檔案                                         │
│     └── 計算統計數據                                         │
│                        ↓                                     │
│  3. 生成建議                                                 │
│     ├── 根據變更內容評分                                     │
│     └── 輸出 High/Medium/Low/Skip                           │
│                        ↓                                     │
│  4. 輸出結構化報告 (YAML)                                    │
│                        ↓                                     │
│  5. [可選] 更新同步狀態                                      │
│     └── 更新 upstream/last-sync.yaml                        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 新 Repo 評估流程

```
┌─────────────────────────────────────────────────────────────┐
│                   NEW REPO EVALUATION WORKFLOW               │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. --new-repo /path/to/repo                                 │
│     └── 驗證是 git repository                               │
│                        ↓                                     │
│  2. 全量分析                                                 │
│     ├── 掃描所有檔案                                         │
│     ├── 分類 skills/agents/commands/hooks                   │
│     └── 取得近期 commit 歷史                                 │
│                        ↓                                     │
│  3. 生成評估報告                                             │
│     └── upstream/reports/new-repos/eval-{name}-{ts}.yaml    │
│                        ↓                                     │
│  4. 下一步：/upstream-compare --new-repo                     │
│     └── AI 分析報告，給出整合建議                            │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## 目錄結構

```
upstream/
├── sources.yaml              # 上游 repo 註冊表
├── last-sync.yaml            # 上次同步狀態
└── reports/
    ├── structured/
    │   └── analysis-YYYY-MM-DD.yaml
    └── new-repos/
        └── eval-{repo-name}-{timestamp}.yaml
```

## 使用範例

### 日常檢查

```bash
# 1. 先拉取最新
ai-dev update --skip-npm

# 2. 分析變更
python skills/custom-skills-upstream-sync/scripts/analyze_upstream.py

# 3. AI 分析報告
/upstream-compare
```

### 評估新 Repo

```bash
# 1. Clone 新 repo 到本地
git clone https://github.com/someone/awesome-skills ~/.config/awesome-skills

# 2. 執行評估
python skills/custom-skills-upstream-sync/scripts/analyze_upstream.py --new-repo ~/.config/awesome-skills

# 3. AI 分析評估報告
/upstream-compare --new-repo eval-awesome-skills-*.yaml

# 4. 若決定整合，加入 sources.yaml 並建立 proposal
```

### 整合流程

```bash
# 1. 分析特定 repo
python skills/custom-skills-upstream-sync/scripts/analyze_upstream.py --source superpowers

# 2. 使用 /upstream-compare 生成 AI 分析報告

# 3. 若要整合，建立 proposal
/openspec:proposal integrate-superpowers-skills

# 4. 完成後更新同步狀態
python skills/custom-skills-upstream-sync/scripts/analyze_upstream.py --update-sync
```

## 相關指令

- `ai-dev update` - 拉取上游 repo 最新內容
- `ai-dev clone` - 分發 skills 到各工具目錄
- `/upstream-compare` - 使用 AI 分析結構化報告，生成自然語言建議
- `/openspec:proposal` - 建立整合提案

## 安裝方式與同步策略

每個上游 repo 在 `upstream/sources.yaml` 中定義了 `install_method`，決定正確的同步方式：

| install_method | 同步動作 | 範例來源 |
|---------------|---------|---------|
| `plugin` | 執行 `claude plugin update <plugin_id>` | superpowers |
| `ai-dev` | `ai-dev clone` 已自動同步檔案到 `skills/` | obsidian-skills, anthropic-skills |
| `standards` | `ai-dev clone` 同步到 `.standards/`，需 diff 合併 | universal-dev-standards |
| `manual` | 本專案有自訂版本，需手動比對差異 | everything-claude-code |

### 同步判斷流程

```
分析報告顯示有更新
        │
        ▼
  檢查 install_method
        │
   ┌────┼─────┬──────────┐
   ▼    ▼     ▼          ▼
plugin ai-dev standards manual
   │    │     │          │
   │    │     │          ▼
   │    │     │    手動 diff 比對
   │    │     │    決定是否採用
   │    │     ▼
   │    │   diff .standards/ 與上游
   │    │   合併變更內容
   │    ▼
   │  確認 ai-dev clone 已同步
   │  若已一致，僅更新 last-sync
   ▼
 claude plugin update <id>
 重啟 Claude Code 生效
        │
        ▼
  更新 last-sync.yaml
```

### 常見誤判

- **plugin 類型報告 High** → 不需手動複製檔案，只需 `claude plugin update`
- **ai-dev 類型報告有變更** → 先確認 `ai-dev clone` 是否已同步，可能 diff 已為零
- **manual 類型** → 本專案有深度自訂（如 ecc-hooks），上游簡化版可能不如本地版完整

## 配置

上游 repo 定義在 `upstream/sources.yaml`：

```yaml
sources:
  superpowers:
    repo: obra/superpowers
    branch: main
    local_path: ~/.config/superpowers/
    format: claude-code-native
    install_method: plugin
    plugin_id: superpowers@superpowers-marketplace
```
