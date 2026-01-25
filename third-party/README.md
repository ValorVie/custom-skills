# 第三方資源目錄 (Third-Party Resource Catalog)

> **定位**: 參考資源庫 - 供使用者探索、評估和選擇性採用的外部專案資訊

## 目錄用途

本目錄收錄值得關注的第三方 AI 輔助開發專案資訊,為使用者提供:

1. **探索管道**: 發現更多可用的 AI 輔助開發工具和資源
2. **標準化資訊**: 統一格式呈現專案功能、安裝方式、適用場景
3. **評估指引**: 提供檢查清單幫助判斷是否適合整合
4. **手動整合指南**: 說明如何從 GitHub 取得並配置到自己的環境

## 與 upstream/ 系統的關係

本專案採用**雙層資源管理策略**:

### `third-party/` (本目錄)
- **性質**: 參考資源庫,僅提供資訊
- **內容**: 第三方專案的介紹、評估和手動安裝指南
- **維護方式**: 手動更新,社群貢獻
- **整合方式**: 使用者自行決定是否採用,並手動安裝

### `upstream/` (已整合資源)
- **性質**: 核心整合系統,自動同步
- **內容**: 已決定納入的精選第三方資源 (如 ECC, superpowers 等)
- **維護方式**: 自動追蹤上游變更,定期同步
- **整合方式**: 透過 `ai-dev clone` 自動分發到各工具目錄

### 整合路徑

```
┌─────────────────────────────────────────────────────────┐
│                  資源採用流程                            │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  1. 探索階段 (third-party/)                              │
│     └─ 發現專案 → 閱讀資訊 → 初步評估                    │
│                        ↓                                 │
│  2. 評估階段 (手動測試)                                  │
│     └─ 手動 Clone → 本地測試 → 填寫評估清單              │
│                        ↓                                 │
│  3. 決策階段                                             │
│     ├─ 個人使用 → 保留在本地環境                         │
│     └─ 團隊採用 → 提議整合                               │
│                        ↓                                 │
│  4. 整合階段 (upstream/)                                 │
│     └─ 建立 OpenSpec proposal → 加入 sources.yaml       │
│        → 納入自動同步機制                                │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## 已收錄專案

### 摘要表格

| 專案名稱 | 規模 | 主要功能 | 推薦度 | 詳細資訊 |
|---------|------|---------|--------|---------|
| **wshobson/agents** | 超大型 (108 代理 + 129 技能) | Plugin 市場、多代理編排、全端開發工作流 | ⭐⭐⭐⭐ | [查看詳情](catalog/wshobson-agents.md) |

### 依功能領域分類

#### 🤖 多代理系統
- **[wshobson/agents](catalog/wshobson-agents.md)** - 108 個專業代理與 15 個工作流編排器

#### 🛠️ 開發工具
- (待收錄)

#### 📚 技能庫
- (待收錄)

#### 🔧 基礎設施
- (待收錄)

## 使用指南

### 如何探索專案

1. **瀏覽摘要表格**: 快速了解各專案的規模和主要功能
2. **閱讀詳細資訊**: 點擊連結查看完整的專案介紹
3. **檢查適用場景**: 確認是否符合您的需求
4. **查看安裝方式**: 了解該專案建議的安裝方法

### 如何評估專案

1. **使用評估檢查清單**: 參考 [templates/evaluation-checklist.md](templates/evaluation-checklist.md)
2. **實際測試功能**: 依照專案建議的方式安裝並測試
3. **考慮整合成本**: 評估學習曲線、維護負擔和相容性
4. **決定採用方式**: 個人使用 vs 提議納入 upstream/

### 如何安裝使用

**重要原則**: 優先使用各專案的**原生安裝方式**,而非手動複製檔案。

每個專案資訊文件都會說明該專案建議的安裝方法,常見方式包括:

#### 方式 1: Plugin 市場機制 (推薦)

適用於有 Plugin 市場的專案 (如 wshobson/agents):

```bash
# 1. 新增市場來源
/plugin marketplace add owner/repo

# 2. 安裝特定 plugin
/plugin install plugin-name

# 3. 驗證安裝
/agents  # 或 /skills
```

#### 方式 2: NPM 套件安裝

適用於發布為 NPM 套件的專案:

```bash
# 安裝套件
npx skills add <package-name>

# 驗證安裝
/skills
```

#### 方式 3: 手動整合 (僅在必要時)

僅在專案**沒有提供**上述方式時才使用:

```bash
# 1. Clone 專案
git clone https://github.com/owner/repo.git ~/.config/third-party-name

# 2. 依照專案文件說明配置
# (每個專案的配置方式可能不同)

# 3. 測試功能
/skills  # 驗證是否載入
```

**注意**:
- **優先依照專案文件的建議方式**安裝,不要假設所有專案都用同樣的方法
- 使用原生安裝方式可獲得更好的版本管理和更新體驗
- 建議先在測試環境中驗證,再正式使用
- 透過原生方式安裝的內容通常有自己的更新機制

## 提交新專案

歡迎社群貢獻更多優質的第三方專案資訊!

### 提交條件

專案需符合以下條件才適合收錄:

- [ ] **開源授權**: MIT, Apache 2.0, BSD 等寬鬆授權
- [ ] **活躍維護**: 最近 6 個月內有提交記錄
- [ ] **文件完整**: 有清晰的 README 和使用說明
- [ ] **功能明確**: 有明確的使用場景和目標使用者
- [ ] **Claude Code 相容**: 適用於 Claude Code 或類似 AI 輔助開發工具

### 提交流程

1. **複製模板**: 使用 [templates/project-entry.md](templates/project-entry.md) 作為起點

2. **填寫專案資訊**:
   ```bash
   # 複製模板
   cp third-party/templates/project-entry.md third-party/catalog/owner-repo.md

   # 編輯檔案,填寫完整資訊
   vim third-party/catalog/owner-repo.md
   ```

3. **完成評估檢查清單** (可選但建議):
   ```bash
   # 複製評估清單
   cp third-party/templates/evaluation-checklist.md evaluation-owner-repo.md

   # 完成評估
   vim evaluation-owner-repo.md
   ```

4. **提交 Pull Request**:
   ```bash
   git checkout -b add-third-party-owner-repo
   git add third-party/catalog/owner-repo.md
   git commit -m "文件(第三方): 新增 owner/repo 專案資訊"
   git push origin add-third-party-owner-repo

   # 在 GitHub 建立 PR
   ```

5. **PR 審核標準**:
   - 資訊完整性 (是否填寫所有必要欄位)
   - 客觀性 (避免過度宣傳或主觀評價)
   - 準確性 (GitHub 連結有效、授權資訊正確)
   - 格式一致性 (遵循模板結構)

### 提交範例

參考現有專案資訊作為範例:
- [wshobson/agents](catalog/wshobson-agents.md) - 大型多代理系統專案

## 文件模板

本目錄提供以下模板協助您評估和撰寫專案資訊:

- **[project-entry.md](templates/project-entry.md)** - 專案資訊文件模板
  - 包含專案基本資訊、功能清單、安裝指南、整合建議等章節

- **[evaluation-checklist.md](templates/evaluation-checklist.md)** - 專案評估檢查清單
  - 從功能適配性、授權、維護狀態、技術品質、安全性等 10 個面向評估專案

## 維護原則

### 資訊更新

- **更新頻率**: 建議每 6 個月檢查一次專案狀態
- **觸發更新**: 當專案有重大更新 (大版本發布、重大功能變更) 時
- **社群更新**: 鼓勵使用者提交 PR 更新過時資訊

### 專案移除

以下情況可考慮移除或標註為「存檔」:

- 專案已超過 12 個月無更新
- 專案已明確標註為不維護
- 專案授權變更為不相容的授權
- 專案功能已被更好的替代方案取代

### 品質控制

- **客觀描述**: 避免主觀評價,基於事實陳述
- **完整資訊**: 確保必要欄位皆已填寫
- **準確連結**: 定期檢查 GitHub 連結和外部資源
- **一致格式**: 遵循模板結構,保持風格統一

## 常見問題

### Q1: third-party/ 與 upstream/ 有何不同?

- **third-party/**
  - 參考資訊,使用者自行探索和評估
  - **依照各專案的原生方式安裝** (如 Plugin 市場、NPM 套件等)
  - 使用者自行管理更新

- **upstream/**
  - 已整合的精選資源
  - 透過 `ai-dev clone` 自動同步到本專案目錄
  - 統一追蹤和管理

### Q2: 如何決定專案應放在哪裡?

- **third-party/**: 初次發現、待評估、個人使用的專案
- **upstream/**: 經團隊評估認可、決定長期維護的精選資源

### Q3: 我可以同時使用 third-party/ 和 upstream/ 的資源嗎?

可以。兩者不衝突:
- `upstream/` 資源透過 `ai-dev clone` 自動同步
- `third-party/` 資源使用原生方式安裝,各自獨立管理

### Q4: 如何提議將 third-party/ 專案納入 upstream/?

1. 先在 third-party/ 中收錄專案資訊
2. 手動測試並完成評估檢查清單
3. 建立 OpenSpec proposal 說明整合理由和方案
4. 經審核通過後加入 `upstream/sources.yaml`

### Q5: 專案資訊會自動更新嗎?

不會。third-party/ 的資訊需手動更新。我們鼓勵:
- 原提交者定期更新自己提交的專案
- 社群使用者發現過時資訊時提交 PR 更新

### Q6: 我可以提交自己的專案嗎?

可以,但需符合以下條件:
- 專案確實對 AI 輔助開發有價值
- 保持客觀描述,避免過度宣傳
- 誠實說明優缺點和適用場景

## 相關資源

- **專案主目錄**: [custom-skills](../README.md)
- **上游整合系統**: [upstream/](../upstream/README.md)
- **開發規範**: [.standards/](.././standards/)
- **OpenSpec 系統**: [openspec/](../openspec/)

---

**維護者**: custom-skills 專案團隊
**最後更新**: 2026-01-25
**聯絡方式**: [GitHub Issues](https://github.com/ValorVie/custom-skills/issues)
