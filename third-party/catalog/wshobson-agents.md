# Claude Code Agents (wshobson/agents)

> **最後更新**: 2026-01-25
> **來源版本**: 最新 main 分支
> **評估者**: custom-skills 專案團隊

## 基本資訊

| 項目 | 內容 |
|------|------|
| **GitHub** | [wshobson/agents](https://github.com/wshobson/agents) |
| **授權** | MIT |
| **維護狀態** | 🟢 活躍維護 |
| **主要語言** | Markdown (配置型專案) |
| **適用工具** | Claude Code CLI |

## 專案概述

Claude Code Agents 是一個為 Claude Code 設計的**生產就緒系統**,整合了 108 個專門 AI 代理、15 個多代理工作流協調器、129 個代理技能,以及 72 個開發工具。該專案實現「智能自動化和多代理編排」,讓開發者能透過模組化方式擴展 Claude 的能力。

### 主要特色

- **大規模代理庫**: 108 個涵蓋架構、語言、基礎設施、品質保證、AI/ML、文檔和營運的專業代理
- **Plugin 市場機制**: 採用「安裝僅需之物」設計,避免不必要的上下文污染
- **多層次模型配置**: 針對不同任務複雜度使用 Opus 4.5 / Sonnet / Haiku 模型
- **漸進式揭露**: Skills 按需載入,優化 token 使用
- **工作流編排**: 15 個協調器可組合多個代理完成複雜任務

### 功能規模

| 類別 | 數量 | 說明 |
|------|------|------|
| **Agents** | 108 個 | 專業領域專家 (架構師、語言專家、DevOps 等) |
| **Skills** | 129 個 | 可複用的行為規範與知識包 |
| **Commands** | 72 個 | 實用工具 (專案搭建、安全掃描、測試自動化) |
| **Workflows** | 15 個 | 多代理工作流協調器 |
| **Languages** | 7 個 | 編程語言插件 (Python, JavaScript, TypeScript 等) |
| **Infrastructure** | 5 個 | 雲端和 DevOps 相關插件 (K8s, Docker, Terraform 等) |

## 功能分類

### 類別 1: 專業代理 (Agents)

| 功能名稱 | 說明 | 模型 |
|----------|------|------|
| `solution-architect` | 系統架構設計專家 | Opus 4.5 |
| `python-expert` | Python 開發專家 | Sonnet |
| `kubernetes-expert` | K8s 營運專家 | Sonnet |
| `security-auditor` | 安全審查專家 | Opus 4.5 |
| `documentation-writer` | 技術文件撰寫專家 | Haiku |
| ... | 共 108 個代理 | - |

### 類別 2: 技能包 (Skills)

| 功能名稱 | 說明 | 類型 |
|----------|------|------|
| `python-best-practices` | Python 最佳實踐指引 | Skill |
| `kubernetes-deployment` | K8s 部署流程 | Skill |
| `api-design-patterns` | API 設計模式 | Skill |
| `testing-strategies` | 測試策略指南 | Skill |
| ... | 共 129 個技能 | - |

### 類別 3: 命令工具 (Commands)

| 功能名稱 | 說明 | 類型 |
|----------|------|------|
| `scaffold-project` | 專案腳手架工具 | Command |
| `security-scan` | 安全漏洞掃描 | Command |
| `test-automation` | 測試自動化執行 | Command |
| ... | 共 72 個命令 | - |

### 類別 4: 工作流編排 (Workflows)

| 功能名稱 | 說明 | 協調代理數 |
|----------|------|------------|
| `full-stack-orchestration` | 全端開發工作流 | 7+ 代理 |
| `deployment-pipeline` | 部署流水線編排 | 5+ 代理 |
| `code-review-workflow` | 程式碼審查流程 | 3+ 代理 |
| ... | 共 15 個工作流 | - |

## 適用場景

### 目標使用者

- [x] **全端開發者** - 提供完整的開發到部署工作流
- [x] **後端開發者** - 涵蓋多種後端語言和框架的專家代理
- [x] **DevOps 工程師** - 包含 K8s、Docker、Terraform 等基礎設施工具
- [x] **技術架構師** - 提供架構設計和決策支援代理
- [x] **團隊領導** - 多代理協調可模擬團隊協作模式

### 典型使用情境

1. **情境 1: 快速啟動新專案**
   - 使用功能: `scaffold-project` 命令 + 語言專家代理
   - 預期效益: 依最佳實踐快速建立專案結構和配置

2. **情境 2: 複雜功能開發**
   - 使用功能: `full-stack-orchestration` 工作流
   - 預期效益: 自動協調前端、後端、資料庫、測試等多個代理完成端到端開發

3. **情境 3: 程式碼審查與品質控制**
   - 使用功能: `code-review-workflow` + `security-auditor`
   - 預期效益: 自動化程式碼審查、安全掃描、測試覆蓋率檢查

4. **情境 4: 基礎設施即程式碼**
   - 使用功能: `kubernetes-expert` + `terraform-specialist`
   - 預期效益: 使用 AI 協助撰寫和審查基礎設施配置

## 手動安裝指南

### 前置需求

- [x] Claude Code CLI 已安裝
- [x] Git 已安裝
- [x] 熟悉 Claude Code 的基本操作

### 安裝步驟

#### 方法 1: 使用 Plugin 市場 (推薦)

```bash
# 1. 新增 wshobson/agents 市場
/plugin marketplace add wshobson/agents

# 2. 瀏覽可用插件 (共 72 個分類)
/plugin list

# 3. 安裝特定插件 (例如: Python 開發)
/plugin install python-development
# 這會自動載入 3 個代理 + 5 個技能

# 4. 安裝 K8s 相關功能
/plugin install kubernetes-operations
# 這會載入 K8s 專家代理 + 4 個技能

# 5. 驗證安裝
/agents  # 查看已載入的代理
```

#### 方法 2: 手動 Clone 與配置

```bash
# 1. Clone 專案到本地
git clone https://github.com/wshobson/agents.git ~/.config/wshobson-agents

# 2. 瀏覽專案結構
cd ~/.config/wshobson-agents
ls plugins/  # 查看 72 個插件分類

# 3. 選擇性複製需要的插件
# 例如: 複製 Python 開發相關功能
cp -r plugins/python-development/* ~/.claude/

# 4. 或僅複製特定代理
cp plugins/python-development/agents/python-expert.md ~/.claude/agents/

# 5. 或僅複製特定技能
cp plugins/python-development/skills/python-best-practices.md ~/.claude/skills/
```

#### 方法 3: 漸進式探索

```bash
# 1. 先安裝單一小型插件測試
/plugin install documentation-writer  # 較小的插件

# 2. 測試功能
/doc-writer  # 觸發文件撰寫代理

# 3. 若滿意,再逐步安裝其他插件
/plugin install python-development
/plugin install kubernetes-operations
# ... 依需求安裝
```

### 驗證安裝

```bash
# 1. 檢查已安裝的插件
/plugin list --installed

# 2. 檢查可用的代理
/agents

# 3. 檢查可用的技能
/skills

# 4. 測試特定工作流 (若已安裝)
/full-stack-orchestration:full-stack-feature
# 這會協調 7+ 代理完成端到端開發
```

## 與 custom-skills 的整合建議

### 功能對照表

| wshobson/agents 功能 | custom-skills 對應 | 建議整合方式 |
|----------------------|-------------------|--------------|
| `python-development` 插件 | ❌ 無完整對應 | ✅ 建議選擇性新增 |
| `kubernetes-operations` | ❌ 無完整對應 | ✅ 建議選擇性新增 |
| `security-auditor` 代理 | `security-review` Skill | 🔀 互補使用 |
| `documentation-writer` | `doc-writer` Agent (ECC) | 🔄 可替換使用 |
| `full-stack-orchestration` | ❌ 無對應 | ✅ 建議新增 (需評估) |
| Plugin 市場機制 | ❌ 無對應 | 💡 可學習設計理念 |

### 整合建議

#### 1. 建議完全整合的功能 (可提議加入 `upstream/`)

**不建議完全整合**。理由:
- wshobson/agents 規模龐大 (108 代理 + 129 技能)
- 與 custom-skills 的設計理念有差異 (plugin 市場 vs 統一整合)
- 完全整合會造成資源重複和維護負擔

#### 2. 建議選擇性採用 (個人環境使用)

推薦以下插件供使用者手動安裝:

**高度推薦**:
- `python-development` - Python 專家代理和最佳實踐技能
- `kubernetes-operations` - K8s 專家和部署技能
- `security-auditor` - 安全審查代理 (與現有 security-review 互補)

**中度推薦**:
- `documentation-writer` - 文件撰寫專家 (可替代 ECC 的 doc-writer)
- `full-stack-orchestration` - 全端開發工作流 (適合大型專案)

**低度推薦**:
- 語言特定插件 - 根據個人使用的程式語言選擇

#### 3. 建議僅作參考

以下功能與 custom-skills 高度重複,建議僅作學習參考:
- 通用 TDD 工作流 (custom-skills 已有 `tdd-workflow`)
- Git 相關功能 (custom-skills 已有完整 Git workflow)
- 測試覆蓋率分析 (custom-skills 已有 `test-coverage`)

### 已知相容性問題

- [ ] **問題 1: Plugin 市場需要網路連線**
  - 描述: `/plugin marketplace add` 需要存取 GitHub API
  - 解決方案: 使用方法 2 手動 Clone 與配置

- [ ] **問題 2: 部分代理使用 Opus 4.5 模型**
  - 描述: 42 個關鍵代理配置為使用 Opus 4.5,成本較高
  - 解決方案: 可手動修改代理配置改用 Sonnet

- [ ] **問題 3: 大量載入會增加上下文消耗**
  - 描述: 同時安裝多個插件可能導致 token 使用量大增
  - 解決方案: 採用漸進式安裝,僅載入當前需要的功能

## 替代方案

如果 wshobson/agents 不適合您的需求,可考慮以下替代方案:

| 專案名稱 | GitHub | 主要差異 |
|----------|--------|----------|
| superpowers (obra) | [obra/superpowers](https://github.com/obra/superpowers) | 更輕量,專注於核心工作流而非大量代理 |
| everything-claude-code | [affaan-m/everything-claude-code](https://github.com/affaan-m/everything-claude-code) | 提供 Hooks 系統和記憶持久化,功能互補 |
| anthropic-skills | [anthropics/skills](https://github.com/anthropics/skills) | Anthropic 官方技能庫,更穩定但功能較少 |

## 學習資源

- 📖 [專案 README](https://github.com/wshobson/agents/blob/main/README.md)
- 📂 [Plugin 清單](https://github.com/wshobson/agents/blob/main/docs/plugins.md)
- 🤖 [代理說明](https://github.com/wshobson/agents/blob/main/docs/agents.md)
- 🎓 [技能文件](https://github.com/wshobson/agents/blob/main/docs/agent-skills.md)

## 評估結論

### 優點

- ✅ **規模龐大**: 108 代理 + 129 技能涵蓋極廣範圍
- ✅ **模組化設計**: Plugin 機制讓使用者按需安裝
- ✅ **多層次模型配置**: 針對任務複雜度優化成本
- ✅ **工作流編排**: 15 個協調器可組合複雜任務
- ✅ **活躍維護**: MIT 授權,持續更新

### 缺點

- ❌ **規模過大**: 對多數使用者來說功能過於豐富
- ❌ **學習曲線陡峭**: 需要時間理解 72 個插件的差異
- ❌ **成本考量**: 部分代理使用 Opus 4.5 模型,成本較高
- ❌ **與 custom-skills 理念不同**: Plugin 市場 vs 統一整合

### 推薦度

- **整體評分**: ⭐⭐⭐⭐ (4/5)
- **學習曲線**: 🟡 中等 (需時間探索 72 個插件)
- **維護負擔**: 🟡 中 (Plugin 機制降低維護成本,但需選擇)

### 推薦給

**適合**以下開發者使用:
- 需要**大量專業代理**支援多領域開發
- 希望透過**多代理協調**模擬團隊協作
- 願意花時間**探索和選擇**適合的插件
- 有**成本預算**使用 Opus 4.5 模型的關鍵任務

**不適合**以下情況:
- 希望輕量化、開箱即用的解決方案
- 僅需少數核心功能
- 成本敏感,主要使用 Haiku/Sonnet 模型

---

**貢獻者**: 如發現資訊過時或有誤,歡迎提交 PR 更新本文件。
