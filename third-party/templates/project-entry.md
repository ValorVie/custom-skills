# [專案名稱]

> **最後更新**: YYYY-MM-DD
> **來源版本**: [GitHub Release/Tag/Commit]
> **評估者**: [您的名稱]

## 基本資訊

| 項目 | 內容 |
|------|------|
| **GitHub** | [owner/repo](https://github.com/owner/repo) |
| **授權** | [MIT / Apache 2.0 / 其他] |
| **維護狀態** | 🟢 活躍維護 / 🟡 偶爾更新 / 🔴 已停止維護 |
| **最後提交** | YYYY-MM-DD |
| **Stars** | ~X.XK |
| **主要語言** | [JavaScript / Python / Shell / 其他] |

## 專案概述

> 用 2-3 句話描述這個專案的核心價值和主要目標。

### 主要特色

- **特色 1**: 簡短說明
- **特色 2**: 簡短說明
- **特色 3**: 簡短說明

### 功能規模

| 類別 | 數量 | 說明 |
|------|------|------|
| **Agents** | X 個 | 專業化 AI 代理 |
| **Skills** | X 個 | 可複用的行為規範 |
| **Commands** | X 個 | 手動觸發的工作流 |
| **Workflows** | X 個 | 多代理協調系統 |
| **其他** | X 個 | [工具/插件/配置等] |

## 功能分類

### 類別 1: [例如: 開發工作流]

| 功能名稱 | 說明 | 類型 |
|----------|------|------|
| `feature-1` | 簡短描述 | Agent / Skill / Command |
| `feature-2` | 簡短描述 | Agent / Skill / Command |

### 類別 2: [例如: 測試與品質]

| 功能名稱 | 說明 | 類型 |
|----------|------|------|
| `feature-3` | 簡短描述 | Agent / Skill / Command |

## 適用場景

### 目標使用者

- [ ] **前端開發者** - 說明為何適合
- [ ] **後端開發者** - 說明為何適合
- [ ] **全端開發者** - 說明為何適合
- [ ] **DevOps 工程師** - 說明為何適合
- [ ] **AI 研究者** - 說明為何適合

### 典型使用情境

1. **情境 1**: [例如: 需要快速搭建多代理系統]
   - 使用功能: [列出相關功能]
   - 預期效益: [說明能解決什麼問題]

2. **情境 2**: [例如: 需要標準化團隊開發流程]
   - 使用功能: [列出相關功能]
   - 預期效益: [說明能解決什麼問題]

## 手動安裝指南

### 前置需求

- [ ] Claude Code CLI 已安裝
- [ ] Git 已安裝
- [ ] [其他必要工具]

### 安裝步驟

#### 方法 1: 使用 Plugin 市場 (推薦)

```bash
# 1. 新增市場來源
/plugin marketplace add owner/repo

# 2. 瀏覽可用插件
/plugin list

# 3. 安裝特定插件
/plugin install plugin-name
```

#### 方法 2: 手動 Clone 與配置

```bash
# 1. Clone 專案到本地
git clone https://github.com/owner/repo.git ~/.config/third-party-name

# 2. 複製需要的檔案到 Claude Code 目錄
# (根據實際需求調整路徑)
cp -r ~/.config/third-party-name/skills/* ~/.claude/skills/
cp -r ~/.config/third-party-name/commands/* ~/.claude/commands/
cp -r ~/.config/third-party-name/agents/* ~/.claude/agents/

# 3. (可選) 複製配置檔案
cp ~/.config/third-party-name/.claude.json ~/.claude/.claude.json.example
```

#### 方法 3: 選擇性整合

```bash
# 僅整合特定 Skill 或 Command
cp ~/.config/third-party-name/skills/specific-skill.md ~/.claude/skills/

# 或手動複製內容到自己的檔案中
cat ~/.config/third-party-name/skills/specific-skill.md
```

### 驗證安裝

```bash
# 檢查 Skill 是否載入
/skills

# 檢查 Command 是否可用
/help

# 測試特定功能
/command-name --help
```

## 與 custom-skills 的整合建議

### 功能對照表

| 第三方功能 | custom-skills 對應 | 建議整合方式 |
|------------|-------------------|--------------|
| `third-party-feature-1` | `existing-skill-1` | 🔄 可替換使用 |
| `third-party-feature-2` | ❌ 無對應功能 | ✅ 建議新增 |
| `third-party-feature-3` | `existing-skill-2` | 🔀 互補使用 |

### 整合建議

1. **完全整合** (建議提議加入 `upstream/`)
   - 功能: [列出建議整合的功能]
   - 理由: [說明為何適合納入核心]

2. **選擇性採用** (個人環境使用)
   - 功能: [列出可選功能]
   - 理由: [說明適用於特定情境]

3. **不建議整合**
   - 功能: [列出不適合的功能]
   - 理由: [說明重複或衝突原因]

### 已知相容性問題

- [ ] 問題 1: [描述問題與解決方案]
- [ ] 問題 2: [描述問題與解決方案]

## 替代方案

如果此專案不適合您的需求,可考慮以下替代方案:

| 專案名稱 | GitHub | 主要差異 |
|----------|--------|----------|
| [alternative-1] | [link] | [說明差異] |
| [alternative-2] | [link] | [說明差異] |

## 學習資源

- 📖 [官方文件](https://example.com/docs)
- 🎥 [教學影片](https://example.com/video)
- 💬 [Discord 社群](https://discord.gg/example)
- 📝 [部落格文章](https://example.com/blog)

## 評估結論

### 優點

- ✅ 優點 1
- ✅ 優點 2
- ✅ 優點 3

### 缺點

- ❌ 缺點 1
- ❌ 缺點 2

### 推薦度

- **整體評分**: ⭐⭐⭐⭐⭐ (X/5)
- **學習曲線**: 🟢 容易 / 🟡 中等 / 🔴 困難
- **維護負擔**: 🟢 低 / 🟡 中 / 🔴 高

### 推薦給

適合 [描述目標使用者特徵] 的開發者使用。

---

**貢獻者**: 如發現資訊過時或有誤,歡迎提交 PR 更新本文件。
