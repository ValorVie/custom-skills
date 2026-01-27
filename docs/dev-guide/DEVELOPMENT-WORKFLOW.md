# 開發工作流程指南

本指南說明如何使用 OpenSpec 和相關工具進行功能開發。

---

## 快速參考（熟練開發者）

| 階段 | 命令 | 說明 |
|------|------|------|
| 探索想法 | 直接對話 | 與 AI 討論想法、釐清方向 |
| 調研目標 | `/opsx:explore` | 探索程式碼、理解現狀 |
| 建立提案 | `/opsx:new <name>` | 建立 change 和 proposal |
| 建立規格 | `/opsx:continue` | 依序建立 design、specs、tasks |
| 實作 | `/opsx:apply` | 執行 tasks 中的任務 |
| 生成測試 | `/custom-skills-{lang}-derive-tests` | 從 specs 生成測試程式碼 |
| 執行測試 | `/custom-skills-{lang}-test` | 執行測試並分析結果 |
| 覆蓋率 | `/custom-skills-{lang}-coverage` | 檢查測試覆蓋率 |
| 生成報告 | `/custom-skills-report` | 生成測試報告供人工審閱 |
| 驗證 | `/opsx:verify` | 驗證實作符合規格 |
| 歸檔 | `/opsx:archive` | 歸檔 change 到主規格 |

> **語言標識 `{lang}`**: `python` 或 `php`

### 完整 TDD 流程

```
想法 → /opsx:explore → /opsx:new → /opsx:continue (×N)
    → /custom-skills-{lang}-derive-tests → /custom-skills-{lang}-test (Red)
    → /opsx:apply → /custom-skills-{lang}-test (Green)
    → /custom-skills-{lang}-coverage → /custom-skills-report
    → 人工審閱 → /opsx:verify → /opsx:archive
```

**語言命令對照：**

| 步驟 | Python | PHP |
|------|--------|-----|
| 生成測試 | `/custom-skills-python-derive-tests` | `/custom-skills-php-derive-tests` |
| 執行測試 | `/custom-skills-python-test` | `/custom-skills-php-test` |
| 覆蓋率 | `/custom-skills-python-coverage` | `/custom-skills-php-coverage` |

### 何時不適用 TDD 流程

TDD 流程適用於有明確輸入/輸出的程式邏輯。以下情況**不適用 TDD**：

| 變更類型 | 說明 | 建議流程 |
|----------|------|----------|
| 純文件變更 | README、CHANGELOG、開發指南等 | spec-driven（跳過測試階段） |
| 配置檔案 | .yaml、.json、環境設定等 | spec-driven |
| AI 命令定義 | Claude Code 命令（.md） | spec-driven |
| 重新命名/搬移 | 檔案重新命名、目錄重組 | spec-driven |
| 樣式調整 | CSS、UI 微調 | 直接實作 |

**判斷原則**：
- ✓ 適合 TDD：可寫自動化測試驗證的功能邏輯
- ✗ 不適合 TDD：無程式邏輯、純文件、AI 指引定義

### 常用命令速查

```bash
# 查看所有 changes
openspec list

# 查看 change 狀態
openspec status --change <name>

# 執行測試
uv run ai-dev test

# 檢查覆蓋率
uv run ai-dev coverage
```

---

## 完整開發流程

### Phase 0: 對話探索 — 釐清想法

在使用任何工具之前，先與 AI 對話釐清你的想法。這個階段不需要特定命令，只需要自然對話。

**目標**：從模糊的想法變成明確的方向

**對話範例**：

```
你：我想讓測試流程更自動化

AI：你目前的測試流程是怎樣的？有什麼痛點？

你：每次寫完 spec 後，還要手動寫測試，很容易遺漏場景

AI：所以你希望從 spec 自動生成測試程式碼？
    這樣可以確保每個場景都有對應的測試。

你：對，而且生成的測試要能直接執行，不是只有骨架

AI：了解。這個功能需要：
    1. 解析 spec 中的 WHEN/THEN 場景
    2. 生成完整的 pytest 測試程式碼
    3. 整合到現有的 TDD 工作流程

    要開始正式規劃嗎？
```

**這個階段的產出**：
- 問題陳述：「目前 XX 有 YY 問題」
- 解決方向：「希望能 ZZ」
- 大致範圍：「需要做 A、B、C」

**何時進入下一階段**：
當你能用 1-2 句話清楚描述「要解決什麼問題」和「大致怎麼解決」時，就可以進入調研階段。

---

### Phase 1: 調研目標 — 理解現狀

使用 `/opsx:explore` 進入探索模式，深入了解程式碼現狀和相關實作。

**命令**：
```
/opsx:explore
```

**用途**：
- 探索現有程式碼結構
- 理解相關模組如何運作
- 找出需要修改或擴充的位置
- 確認技術可行性

**對話範例**：

```
你：/opsx:explore

AI：進入探索模式。你想探索什麼？

你：我想了解現有的測試執行流程是怎麼實作的

AI：讓我搜尋相關程式碼...

    找到以下相關檔案：
    - script/commands/test.py - 測試執行 CLI
    - script/utils/test_runner/ - TestRunner 架構
    - commands/claude/custom-skills-test.md - Claude Code 命令

    現有架構採用「腳本只負責執行，AI 負責分析」的原則...
```

**這個階段的產出**：
- 對現有架構的理解
- 需要修改/新增的檔案清單
- 可能的技術方案

**提示**：
- 可以請 AI 繪製架構圖幫助理解
- 如果發現現有設計有問題，可以在這個階段討論
- 探索完成後，會對實作範圍有更清楚的認識

---

### Phase 2: 建立提案 — 正式規劃

當你對目標和範圍有足夠了解後，使用 `/opsx:new` 建立正式的 change 提案。

**命令**：
```
/opsx:new <change-name>
```

**範例**：
```
/opsx:new tdd-test-generation
```

**這個命令會**：
1. 建立 `openspec/changes/<change-name>/` 目錄
2. 引導你建立 `proposal.md`

**Proposal 內容**：
- **Summary**：一句話描述這個 change
- **Motivation**：為什麼需要這個功能（痛點）
- **Scope**：In Scope / Out of Scope
- **Design**：高層架構設計
- **Capabilities**：這個 change 要提供的能力（重要！每個能力會對應一個 spec）

**提示**：
- Capabilities 要列清楚，後續會根據這個建立 specs
- 如果不確定範圍，可以先列出來再討論調整
- Proposal 是「為什麼做」和「做什麼」，不是「怎麼做」

**確認或修改提案**：
建立後可以繼續與 AI 討論，修改 proposal.md 直到滿意為止。

---

### Phase 3: 建立規格 — 完善設計

使用 `/opsx:continue` 依序建立其他 artifacts：design、specs、tasks。

**命令**：
```
/opsx:continue
```

**Artifacts 順序**（spec-driven schema）：
1. `proposal.md` - 提案（Phase 2 已完成）
2. `design.md` - 技術設計決策
3. `specs/*.md` - 詳細規格（WHEN/THEN 場景）
4. `tasks.md` - 實作任務清單

**Design.md 內容**：
- **Context**：背景和現狀
- **Goals / Non-Goals**：目標和非目標
- **Decisions**：技術決策和理由
- **Risks / Trade-offs**：風險和取捨

**Specs 內容**：
每個 capability 對應一個 spec 檔案，包含：
```markdown
### Requirement: 需求名稱
需求描述

#### Scenario: 場景名稱
- **WHEN** 前置條件
- **AND** 附加條件
- **THEN** 預期結果
```

**Tasks.md 內容**：
```markdown
## 1. 任務群組名稱

- [ ] 1.1 具體任務描述
- [ ] 1.2 具體任務描述

## 2. 另一個任務群組

- [ ] 2.1 具體任務描述
```

**提示**：
- 每次執行 `/opsx:continue` 建立一個 artifact
- 可以隨時查看進度：`openspec status --change <name>`
- 如果發現需要修改已完成的 artifact，直接編輯即可

---

### Phase 4: 實作 — 執行任務

當所有 artifacts 完成後，使用 `/opsx:apply` 開始實作。

**命令**：
```
/opsx:apply
```
或指定 change：
```
/opsx:apply <change-name>
```

**這個命令會**：
1. 讀取 tasks.md 中的任務清單
2. 依序執行每個任務
3. 完成後自動勾選 `- [ ]` → `- [x]`

**TDD 流程**（建議）：

**Python:**
```
# 1. 從 specs 生成測試
/custom-skills-python-derive-tests openspec/changes/<name>/specs/

# 2. Red Phase - 執行測試（預期失敗）
/custom-skills-python-test

# 3. 實作功能程式碼
/opsx:apply

# 4. Green Phase - 執行測試（預期通過）
/custom-skills-python-test
```

**PHP:**
```
# 1. 從 specs 生成測試
/custom-skills-php-derive-tests openspec/changes/<name>/specs/

# 2. Red Phase - 執行測試（預期失敗）
/custom-skills-php-test

# 3. 實作功能程式碼
/opsx:apply

# 4. Green Phase - 執行測試（預期通過）
/custom-skills-php-test
```

**提示**：
- 可以隨時暫停，下次執行 `/opsx:apply` 會從上次停止的地方繼續
- 如果發現任務描述不清楚，可以先更新 tasks.md
- 實作過程中發現設計問題，可以回頭更新 design.md 或 specs

---

### Phase 5: 測試 — 驗證實作

使用測試相關命令驗證實作正確性。

#### 通用流程

1. 從 specs 生成測試
2. 執行測試（Red Phase）
3. 實作功能
4. 執行測試（Green Phase）
5. 檢查覆蓋率

#### Python 命令

| 步驟 | 命令 | 說明 |
|------|------|------|
| 生成測試 | `/custom-skills-python-derive-tests <specs-path>` | 生成 pytest 測試程式碼 |
| 執行測試 | `/custom-skills-python-test` | 執行 pytest 並分析結果 |
| 覆蓋率 | `/custom-skills-python-coverage` | 執行 pytest-cov 覆蓋率分析 |

**Python 選項**：
- `--verbose`, `-v`：顯示詳細輸出
- `--fail-fast`, `-x`：失敗時立即停止
- `-k <keyword>`：過濾測試名稱

#### PHP 命令

| 步驟 | 命令 | 說明 |
|------|------|------|
| 生成測試 | `/custom-skills-php-derive-tests <specs-path>` | 生成 PHPUnit 測試程式碼 |
| 執行測試 | `/custom-skills-php-test` | 執行 PHPUnit 並分析結果 |
| 覆蓋率 | `/custom-skills-php-coverage` | 執行 PHPUnit 覆蓋率分析 |

**PHP 選項**：
- `--verbose`, `-v`：顯示詳細輸出
- `--stop-on-failure`：失敗時立即停止
- `--filter <method>`：過濾測試方法

#### 輸出格式

**測試輸出**：
- 測試摘要（通過/失敗/跳過數量）
- 失敗測試分析（錯誤原因、修復建議）
- 整體評估

**覆蓋率輸出**：
- 覆蓋率百分比
- 未覆蓋的檔案和行數
- 改善建議

---

### Phase 5.5: 報告 — 人工審閱

使用 `/custom-skills-report` 生成測試報告供人工審閱。

**命令**：
```
/custom-skills-report <change-name>
```

**這個命令會**：
1. 收集測試結果、覆蓋率、任務完成狀態
2. 生成結構化資料（YAML 格式）
3. 生成 AI 自然語言分析報告
4. 輸出到 `openspec/changes/<change-name>/report.md`

**報告內容**：
- 結構化摘要（測試/覆蓋率/任務）
- AI 分析（整體評估、問題、建議）
- Specs 對照表
- 審閱確認清單

**人工審閱檢查點**：
- [ ] 測試結果是否符合預期
- [ ] 覆蓋率是否達標
- [ ] 未覆蓋區塊的原因是否合理
- [ ] AI 分析的建議是否需要處理

**審閱通過後**：
進入驗證階段，執行 `/opsx:verify`

---

### Phase 6: 驗證 — 確認完成

使用 `/opsx:verify` 驗證實作符合規格。

**命令**：
```
/opsx:verify
```

**這個命令會**：
1. 檢查所有 tasks 是否完成
2. 比對實作與 specs 是否一致
3. 確認測試通過
4. 回報驗證結果

**驗證通過的條件**：
- [ ] 所有 tasks 已勾選完成
- [ ] 測試全部通過
- [ ] 覆蓋率達標
- [ ] 實作符合 specs 定義

---

### Phase 7: 歸檔 — 完成收尾

當驗證通過後，使用 `/opsx:archive` 歸檔 change。

**命令**：
```
/opsx:archive
```
或指定 change：
```
/opsx:archive <change-name>
```

**這個命令會**：
1. 將 change 的 specs 合併到主規格 (`openspec/specs/`)
2. 將 change 目錄移到 `openspec/archive/`
3. 更新相關索引

**歸檔後**：
- Change 完成，不再出現在 `openspec list` 中
- Specs 已整合到專案的主規格
- 可在 `openspec/archive/` 查看歷史記錄

---

## 附錄

### A. 常見問題

**Q: 可以跳過某些 Phase 嗎？**

A: 可以，但不建議。每個 Phase 都有其目的：
- 跳過 Phase 0-1：可能導致方向錯誤，做白工
- 跳過 Phase 2-3：沒有規格，難以追蹤和驗證
- 跳過 Phase 5-6：沒有測試，品質無法保證

**Q: 實作過程中發現設計有問題怎麼辦？**

A: OpenSpec 支援流動式工作流程：
1. 暫停實作
2. 回頭修改 design.md 或 specs
3. 必要時更新 tasks.md
4. 繼續實作

**Q: 多個 changes 可以同時進行嗎？**

A: 可以。使用 `openspec list` 查看所有 changes，執行命令時指定 change 名稱即可。

**Q: 如何判斷一個 change 是否適用 TDD 流程？**

A: 問自己：「這個變更有可以寫自動化測試驗證的程式邏輯嗎？」

- **適合 TDD**：新增 CLI 命令、API 端點、工具函式、資料處理邏輯
- **不適合 TDD**：純文件變更、配置檔案、AI 命令定義（.md）、重新命名

不適合 TDD 的變更仍可使用 spec-driven 流程（proposal → design → specs → tasks），但跳過測試生成和覆蓋率檢查階段。

### B. 命令總覽

**OpenSpec 命令：**

| 命令 | 說明 |
|------|------|
| `/opsx:explore` | 進入探索模式 |
| `/opsx:new <name>` | 建立新的 change |
| `/opsx:continue` | 繼續建立下一個 artifact |
| `/opsx:apply` | 執行實作任務 |
| `/opsx:verify` | 驗證實作 |
| `/opsx:archive` | 歸檔 change |

**Python 測試命令：**

| 命令 | 說明 |
|------|------|
| `/custom-skills-python-derive-tests` | 從 specs 生成 pytest 測試 |
| `/custom-skills-python-test` | 執行 pytest 測試 |
| `/custom-skills-python-coverage` | 檢查 pytest 覆蓋率 |

**PHP 測試命令：**

| 命令 | 說明 |
|------|------|
| `/custom-skills-php-derive-tests` | 從 specs 生成 PHPUnit 測試 |
| `/custom-skills-php-test` | 執行 PHPUnit 測試 |
| `/custom-skills-php-coverage` | 檢查 PHPUnit 覆蓋率 |

**通用命令：**

| 命令 | 說明 |
|------|------|
| `/custom-skills-report` | 生成測試報告（自動偵測語言） |

### C. CLI 命令

```bash
# OpenSpec CLI
openspec list                    # 列出所有 changes
openspec status --change <name>  # 查看 change 狀態
openspec show <name>             # 顯示 change 內容

# ai-dev CLI
uv run ai-dev test              # 執行測試
uv run ai-dev coverage          # 檢查覆蓋率
uv run ai-dev derive-tests      # 讀取 specs 內容
```

### D. 目錄結構

```
openspec/
├── changes/           # 進行中的 changes
│   └── <change-name>/
│       ├── proposal.md
│       ├── design.md
│       ├── specs/
│       │   └── <feature>/spec.md
│       └── tasks.md
├── specs/             # 主規格（歸檔後合併至此）
└── archive/           # 已完成的 changes
```

---

## 下一步

完成 OpenSpec 開發流程後，請參考 **[Git 工作流程指南](GIT-WORKFLOW.md)** 進行程式碼提交與 PR 流程：

1. 從 main 建立開發分支
2. 開發（commit 可隨意）
3. Rebase/Merge main
4. `/git-commit pr` 建立 PR
5. Code Review → 合併 → 刪除分支
