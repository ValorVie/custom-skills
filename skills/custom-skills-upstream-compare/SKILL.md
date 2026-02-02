---
name: upstream-compare
description: |
  Generate AI-powered analysis reports from custom-skills-upstream-sync structured data.
  Use when: reviewing upstream changes, generating integration recommendations, preparing merge decisions, evaluating new repos.
  Triggers: "compare upstream", "analyze upstream report", "upstream compare", "generate recommendations", "upstream analysis", "上游比較", "分析上游報告".
---

# Upstream Compare | 上游比較

讀取 custom-skills-upstream-sync 生成的結構化報告，使用 AI 生成自然語言分析與整合建議。
支援分析已註冊 repo 的更新，或評估全新 repo 的整合價值。

## Quick Start

```bash
# 前置作業：先執行 custom-skills-upstream-sync 生成報告
python skills/custom-skills-upstream-sync/scripts/analyze_upstream.py

# 然後讓 AI 分析報告
/upstream-compare

# 評估新 repo（需先用 --new-repo 生成評估報告）
/upstream-compare --new-repo eval-awesome-skills-*.yaml
```

## Workflow

### 模式 1：分析已註冊 repo 更新

```
┌─────────────────────────────────────────────────────────────────┐
│                    Upstream Compare Workflow                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. [前置] custom-skills-upstream-sync                                         │
│     └── 生成 upstream/reports/structured/analysis-*.yaml        │
│                          ↓                                       │
│  2. AI 讀取結構化報告                                            │
│     ├── 解析 YAML 資料                                          │
│     ├── 理解各 repo 的變更內容                                   │
│     └── 評估整合建議等級                                         │
│                          ↓                                       │
│  3. AI 生成自然語言報告                                          │
│     ├── 執行摘要                                                 │
│     ├── 各 repo 詳細分析                                         │
│     ├── 整合建議與優先級                                         │
│     └── 實作步驟                                                 │
│                          ↓                                       │
│  4. [可選] 生成 OpenSpec proposal                                │
│     └── /openspec:proposal upstream-integration                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 模式 2：評估新 Repo

```
┌─────────────────────────────────────────────────────────────────┐
│                    New Repo Evaluation Workflow                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. [前置] custom-skills-upstream-sync --new-repo /path/to/repo               │
│     └── 生成 upstream/reports/new-repos/eval-*.yaml             │
│                          ↓                                       │
│  2. AI 讀取評估報告                                              │
│     ├── 分析 repo 結構與內容                                     │
│     ├── 檢視 skills/agents/commands 列表                        │
│     └── 評估內容品質與價值                                       │
│                          ↓                                       │
│  3. AI 生成詳細評估報告                                          │
│     ├── Repo 概覽                                                │
│     ├── 內容品質評估                                             │
│     ├── 與本專案的重疊/互補分析                                  │
│     ├── 整合建議（全部/部分/跳過）                               │
│     └── 推薦整合的具體項目                                       │
│                          ↓                                       │
│  4. [可選] 加入 sources.yaml 開始追蹤                            │
│     └── 或建立 proposal 整合特定內容                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## AI Analysis Guide

### 模式 1：分析已註冊 repo 更新

當執行 `/upstream-compare` 時，AI 會：

#### 1. 讀取最新報告

```yaml
# 讀取位置
upstream/reports/structured/analysis-YYYY-MM-DD.yaml
```

#### 2. 分析結構

報告包含以下關鍵資訊：

| 欄位 | 說明 | 分析重點 |
|------|------|----------|
| `recommendation` | High/Medium/Low/Skip | 判斷優先級 |
| `reasoning` | 建議原因 | 理解變更重要性 |
| `summary.by_type` | 變更類型分布 | feat/fix 數量 |
| `summary.by_category` | 檔案分類 | skills/agents/commands |
| `summary.novel_structures` | 新架構偵測 | **重要！新框架/結構** |
| `commits` | 近期 commit 列表 | 具體變更內容 |
| `file_changes` | 檔案變更清單 | 影響範圍 |

#### 3. 生成報告結構

```markdown
# 上游整合分析報告

## 執行摘要
- 分析了 N 個上游 repository
- M 個建議優先整合（High）
- K 個建議評估整合（Medium）
- N 個包含新框架/架構（需特別關注）

## 詳細分析

### [Repo Name]

**整合建議**: High/Medium/Low/Skip

**變更摘要**:
- X 個新功能
- Y 個修復
- Z 個 skill 變更

**新架構/框架**:（若有偵測到）
- [框架名稱]: [說明] - [是否採用]
- [特殊模式]: [說明] - [是否採用]

**重要變更**:
1. [commit subject] - [分析說明]
2. ...

**整合建議**:
- 建議整合原因
- 注意事項
- 實作步驟

## 整合路線圖

### 優先整合 (High)
1. ...

### 評估整合 (Medium)
1. ...

### 新架構採用建議
1. [框架名稱] - [採用建議與原因]

## 下一步行動
1. 建立 OpenSpec proposal
2. 執行整合
3. 更新 last-sync.yaml
```

### 模式 2：評估新 Repo

當執行 `/upstream-compare --new-repo <report>` 時，AI 會：

#### 1. 讀取評估報告

```yaml
# 讀取位置
upstream/reports/new-repos/eval-{repo-name}-{timestamp}.yaml
```

#### 2. 分析內容

評估報告包含：

| 欄位 | 說明 | 分析重點 |
|------|------|----------|
| `repo.name` | Repo 名稱 | 識別來源 |
| `repo.remote_url` | 遠端 URL | 確認來源可靠性 |
| `repo.recommendation` | Evaluate/Review/Skip | 初步建議 |
| `repo.file_structure.skills` | Skills 列表 | 核心整合目標 |
| `repo.file_structure.agents` | Agents 列表 | 代理擴充 |
| `repo.file_structure.commands` | Commands 列表 | 指令擴充 |
| `repo.recent_commits` | 近期 commits | 活躍度與品質 |
| `repo.summary.novel_structures` | 新架構偵測 | **重要！見下方說明** |
| `repo.overlap_analysis` | 重疊偵測結果 | **重要！見下方說明** |

#### 重疊偵測分析（重要）

報告中的 `overlap_analysis`（需使用 `--detect-overlaps` 參數）：

```yaml
overlap_analysis:
  # 名稱完全相同的項目
  exact_matches:
    - type: skills
      name: tdd-workflow
      local_name: tdd-workflow
      similarity: 1.0

  # 名稱相似的項目 (similarity > 0.7)
  similar_names:
    - type: skills
      name: test-assistant
      local_name: testing-guide
      similarity: 0.85

  # 功能關鍵字匹配
  functional_overlaps:
    - type: skills
      name: testing-helper
      category: tdd
      local_similar: [testing-guide, tdd-workflow]

  # 全新項目（無重疊）
  new_items:
    - type: skills
      name: unique-skill

  # 已在 overlaps.yaml 定義
  already_defined:
    - type: skills
      name: commit-standards
      note: 已在 overlaps.yaml 定義

  # 建議的群組分類
  suggested_groups:
    tdd:
      ecc:
        - type: skills
          name: testing-helper
```

**AI 分析時必須評估：**

1. **完全匹配** - 這些是同名項目，需決定使用哪個版本
2. **名稱相似** - 可能是功能相同但名稱不同，需比較內容
3. **功能重疊** - 同類功能，需決定是否合併或選擇
4. **全新項目** - 可直接整合，無衝突風險
5. **建議群組** - 參考 suggested_groups 更新 overlaps.yaml

#### 新架構/框架分析（重要）

報告中的 `novel_structures` 包含本專案沒有的新結構：

```yaml
novel_structures:
  # 新的框架/架構指標
  framework_indicators:
    - framework: "Claude Plugin System"
      description: "支援 Claude Code Plugin 架構"
      files: [...]
    - framework: "OpenCode Support"
      description: "支援 OpenCode 整合"
      files: [...]

  # 值得關注的特殊模式
  notable_patterns:
    - pattern: ".claude-plugin/"
      description: "Claude Plugin 架構"
      example_path: ".claude-plugin/plugin.json"

  # 本專案沒有的新目錄
  new_directories:
    - name: "prompts"
      example_files: [...]

  # 新的檔案類型
  new_file_types: [".codex", ".gitattributes"]
```

**AI 分析時必須評估：**

1. **框架指標** - 這些框架是否對本專案有價值？
   - Claude Plugin System：是否要支援作為獨立插件？
   - OpenCode Support：是否要支援 OpenCode？
   - Hook System：是否要採用其 hook 機制？

2. **特殊模式** - 這些配置/結構是否值得學習？
   - 配置檔案格式（hooks.json, plugin.json）
   - 腳本結構（run-hook.cmd, session-start.sh）
   - 目錄組織方式

3. **新目錄結構** - 是否有值得採用的組織方式？
   - prompts/ - 是否需要獨立的 prompt 目錄？
   - examples/ - 是否需要範例目錄？
   - lib/ - 是否需要共用函式庫？

#### 3. 生成評估報告

```markdown
# 新 Repo 評估報告：[Repo Name]

## Repo 概覽

- **名稱**: [name]
- **來源**: [remote_url]
- **總檔案數**: [count]
- **Skills 數量**: [count]
- **Agents 數量**: [count]
- **Commands 數量**: [count]

## 新架構/框架分析

### 偵測到的框架
[列出 framework_indicators 並評估是否採用]

| 框架 | 說明 | 建議 |
|------|------|------|
| Claude Plugin System | 支援作為獨立插件 | [採用/參考/跳過] |
| OpenCode Support | 支援 OpenCode 整合 | [採用/參考/跳過] |
| Hook System | 自動化 Hook 機制 | [採用/參考/跳過] |

### 特殊配置模式
[列出 notable_patterns 並評估]

- **hooks.json**: Hook 配置檔案 - [是否採用類似設計]
- **plugin.json**: Plugin 配置 - [是否需要]

### 新目錄結構
[列出 new_directories 並評估是否值得採用]

- **prompts/**: Prompt 目錄 - [是否需要]
- **examples/**: 範例目錄 - [是否需要]
- **lib/**: 共用函式庫 - [是否需要]

## 內容品質評估

### Skills 分析
[列出每個 skill 並簡短評估其價值]

1. **skill-name-1**: [功能描述] - [推薦/觀望/跳過]
2. **skill-name-2**: [功能描述] - [推薦/觀望/跳過]
...

### Agents 分析
[列出每個 agent 並評估]

### Commands 分析
[列出每個 command 並評估]

## 與本專案的關係

### 重疊內容
[列出已有類似功能的項目]

### 互補內容
[列出可以補充本專案的項目]

### 衝突風險
[列出可能造成衝突的項目]

## 整合建議

**總體建議**: [全部整合 / 部分整合 / 僅參考 / 跳過]

### 推薦整合項目

#### 框架/架構
1. [framework-1] - [原因]

#### Skills/Agents/Commands
1. [item-1] - [原因]
2. [item-2] - [原因]

### 不建議整合項目
1. [item-1] - [原因]

## 下一步行動

1. [具體行動項目]
2. 若決定整合：
   - 加入 sources.yaml 開始追蹤
   - 或建立 OpenSpec proposal
```

## Decision Criteria

### 已註冊 repo 更新

| 等級 | 條件 | 建議行動 |
|------|------|----------|
| **High** | 多個新功能、重要修復、核心 skill 變更、新框架支援 | 優先整合，盡快處理 |
| **Medium** | 有價值的改進、文件更新、新配置模式 | 評估後決定是否整合 |
| **Low** | 小幅調整、維護性變更 | 可選擇性整合 |
| **Skip** | 無變更或僅微調 | 無需處理 |

### 新 repo 評估

| 等級 | 條件 | 建議行動 |
|------|------|----------|
| **Evaluate (高價值)** | 包含新框架支援 + skills/agents/commands | 詳細評估，優先考慮 |
| **Evaluate** | 包含有價值的 skills/agents/commands | 詳細評估每個項目 |
| **Review** | 包含 hooks 或參考文件、有趣的配置模式 | 可參考部分內容 |
| **Skip** | 無可整合內容、無新架構 | 不適合整合 |

## Install Method Awareness（重要）

分析報告時，**必須先查看 `upstream/sources.yaml` 中每個 repo 的 `install_method`**，
避免建議錯誤的同步方式：

| install_method | 正確的同步動作 | 常見誤判 |
|---------------|--------------|---------|
| `plugin` | `claude plugin update <plugin_id>` + 重啟 | 不需手動複製檔案，報告顯示 High 不代表要手動操作 |
| `ai-dev` | `ai-dev clone` 已自動同步 | diff 可能已為零，僅需更新 last-sync.yaml |
| `standards` | diff `.standards/` 與上游，合併變更 | 需注意本地可能有超前版本或自訂修改 |
| `manual` | 手動比對差異，選擇性採用 | 本專案自訂版本可能比上游更完整（如 ecc-hooks） |

**分析報告撰寫時必須：**
1. 在每個 repo 分析段落標註其 `install_method`
2. 整合建議中說明正確的同步命令
3. 對 `manual` 類型，先比較本地 vs 上游功能完整度再建議

## Analysis Priorities

整合評估時優先考慮：

1. **新框架/架構** - 可能帶來全新能力（Plugin System, MCP, Hook System）
2. **Skills 變更** - 直接影響 AI 行為
3. **Agents 變更** - 影響子代理能力
4. **Commands 變更** - 影響使用者指令
5. **Hooks 變更** - 影響自動化流程
6. **配置模式** - 新的配置檔案格式或目錄結構
7. **Docs 變更** - 參考但通常不需整合

### 新架構評估指南

當發現 `novel_structures` 時，應評估：

| 框架類型 | 評估重點 | 整合難度 |
|----------|----------|----------|
| Claude Plugin System | 是否要作為獨立插件發布？ | 中 |
| OpenCode Support | 是否需要支援 OpenCode 用戶？ | 低 |
| Codex Support | 是否需要支援 Codex CLI？ | 低 |
| Hook System | 現有 hook 機制是否足夠？ | 中 |
| MCP Integration | 是否需要 MCP 配置支援？ | 高 |
| Test Framework | 是否需要採用其測試結構？ | 低 |

## Output Formats

### 1. 分析報告檔案（必須）

**AI 必須將分析報告儲存至檔案：**

```
upstream/reports/analysis/compare-YYYY-MM-DD.md
```

報告檔案包含：
- 執行摘要
- 各 repo 詳細分析
- 新框架採用建議
- 整合路線圖
- 下一步行動

**執行步驟：**
1. 讀取結構化報告（`upstream/reports/structured/analysis-*.yaml`）
2. 分析內容並生成 Markdown 報告
3. **使用 Write 工具儲存報告檔案**
4. 在對話中輸出摘要並告知報告位置

### 2. 對話摘要

在對話中輸出精簡摘要，包含：
- 關鍵發現
- 優先行動項目
- 報告檔案位置連結

### 3. OpenSpec Proposal（可選）

若決定整合，生成提案：

```yaml
title: "Upstream Integration: [repo-name]"
type: enhancement
priority: high|medium|low

background:
  source: upstream-compare analysis
  report_date: YYYY-MM-DD

changes:
  - category: skills
    items:
      - name: skill-name
        action: add|update|review
        source_commit: abc1234
        rationale: "..."

implementation:
  - step: 1
    description: "..."
  - step: 2
    description: "..."

risks:
  - risk: "..."
    mitigation: "..."
```

## Related Commands

- `/custom-skills-upstream-sync` - 生成結構化分析報告（前置步驟）
- `/custom-skills-upstream-sync --new-repo` - 評估新的本地 repo
- `/openspec:proposal` - 建立整合提案
- `ai-dev update` - 拉取上游最新內容
- `ai-dev clone` - 分發 skills 到各工具目錄

## References

- [Analysis Template](references/analysis-template.md) - 報告結構範本
- [Quality Criteria](references/quality-criteria.md) - 品質評估標準
