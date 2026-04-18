# Upstream Ops Refactor — Design

**日期**：2026-04-18
**作者**：Arlen
**狀態**：Draft（待實作計畫）

## 背景

本專案以 4 個 skill 處理「上游 repo 同步維護」：

| Skill | 現況 |
|-------|------|
| `custom-skills-upstream-sync` | 1284 行 Python，解析 commit 類型、打 High/Medium/Low 分，輸出結構化 YAML |
| `custom-skills-upstream-compare` | AI 讀 sync 輸出的 YAML，產出自然語言整合建議 |
| `custom-skills-uds-update` | 新建（本次對話），SHA-256 比對 `.standards/` 與 UDS 鏡像 `skills/` |
| `custom-skills-tool-overlap-analyzer` | 分析本地工具（agents/skills/commands）之間的重疊 |

### 問題

1. **機制脆弱**：sync 的 Python 用 regex 解析 commit subject 與檔案分類，上游 commit 格式變動後就失準，維護成本高
2. **決策層冗餘**：sync → compare 是二段管線，compare 實質只在「把 YAML 翻成 markdown 建議」，AI 能直接做
3. **漂移嚴重的現實**：5 個上游全部停在 `2026-04-03`（同一天大同步後就沒動），UDS 已累積 53 commits。現有工具跑完一次後使用者不想再跑
4. **skill 入口過多**：4 個 skill 負責相近的事，使用者要記憶多個入口；每新增一個上游需求就多一個 skill

### 結論

結構化報告對「變動快的上游」是錯誤的抽象層——把**偵測性、脆弱、低頻**的工作套在**機械性、剛性、高頻**的框架上。改用：**腳本只做確定性機械勞動（SHA-256 比對），判斷性工作交給 AI 當下跑**。

## 目標

統一所有「上游 repo 檢查、更新、維護」功能為單一 skill `custom-skills-upstream-ops`，內部以 mode 子目錄區分功能，降低 surface area 與維護負擔。

## 架構

### Skill 清單變化

| 動作 | Skill | 理由 |
|------|-------|------|
| **新建** | `custom-skills-upstream-ops` | 統一入口 |
| **刪除** | `custom-skills-upstream-sync` | 行為併入 `modes/audit.md`，Python 廢棄 |
| **刪除** | `custom-skills-upstream-compare` | reading guide 併入 `references/decision-patterns.md` |
| **刪除** | `custom-skills-uds-update` | SKILL.md 併入 `modes/uds-check.md`，`check_uds.py` 搬到 `scripts/` |
| **保留** | `custom-skills-tool-overlap-analyzer` | 分析本專案內部工具重疊，與上游無關 |

### 目錄結構

```
skills/custom-skills-upstream-ops/
├── SKILL.md                      # 入口：說明 4 個 mode 與路由規則
├── modes/
│   ├── audit.md                  # 上游 commit 差異 + 同步決策
│   ├── uds-check.md              # UDS 檔案級漂移
│   ├── overlap.md                # 任一 repo vs 本專案重疊度偵測
│   └── maintenance.md            # last-sync 更新、歸檔、列孤兒檔等
├── references/
│   ├── install-methods.md        # install_method 決策表 + 同步命令 one-liner
│   └── decision-patterns.md      # audit 結果判讀 reading guide（取代 upstream-compare）
└── scripts/
    └── check_uds.py              # 唯一保留的 Python，做 SHA-256 檔案比對
```

### 職責邊界

- **upstream-ops**：所有跟「上游 repo」相關的操作（audit / uds-check / overlap / maintenance）
- **tool-overlap-analyzer**：分析**本專案內部**工具重疊，不進 upstream-ops
- **ai-dev CLI**：繼續負責實際的拉取 / 分發（`ai-dev update`、`ai-dev clone`），upstream-ops 只指示要跑什麼命令，不代跑

## Modes 行為

### Mode 1：audit（預設）

**觸發**
```
/custom-skills-upstream-ops
/custom-skills-upstream-ops audit [--source <name>] [--archive]
```

**實作**：純 AI workflow，無 Python
1. 讀 `upstream/sources.yaml`、`upstream/last-sync.yaml`
2. 對每個上游執行：
   - `git -C <local_path> rev-parse HEAD`
   - 若 HEAD ≠ last_sync：`git log --oneline --no-merges last_sync..HEAD`
   - 需要細節時：`git diff --stat last_sync..HEAD`
3. 套用 `references/install-methods.md` 的決策表，對每個上游產出：
   - 進度（behind N commits）
   - 主要變更（AI 讀 commit subjects 摘要，3 句內）
   - 建議的同步命令（one-liner）
4. 輸出單一 Markdown 摘要到對話

**輸出格式**
```markdown
## Upstream Audit — 2026-04-18

### universal-dev-standards (standards)
- 53 commits behind
- 主要變更：XSPEC-035~044、DEC-043 Wave 1、anti-sycophancy-prompting
- 同步：`ai-dev update --only repos` → 執行 `upstream-ops uds-check` 處理檔案合併

### superpowers (plugin)
- 12 commits behind
- 主要變更：...
- 同步：`claude plugin update superpowers@superpowers-marketplace` + 重啟 Claude Code
```

**可選歸檔**：`--archive` flag 把 Markdown 寫到 `upstream/reports/audit/audit-YYYY-MM-DD.md`。預設不寫檔。

**明確排除**
- ❌ 不解析 commit subject 分類 feat/fix/refactor
- ❌ 不計算 High/Medium/Low/Skip 數值評分
- ❌ 不輸出 YAML 結構化報告

### Mode 2：uds-check

**觸發**
```
/custom-skills-upstream-ops uds-check [--verbose] [--report]
```

**實作**：執行 `scripts/check_uds.py`（從舊 `custom-skills-uds-update/scripts/` 原樣搬移）

**範圍**：UDS 上游的 `.standards/` 與 UDS 鏡像 `skills/<id>/` 的 SHA-256 檔案級漂移

**為何這個 mode 保留 Python**
- `.standards/` 有 75 檔、UDS 鏡像 skills 有 25 個目錄，SHA-256 比對是確定性機械勞動，腳本快且穩定
- UDS 的 `install_method: standards` 需要逐檔 diff 合併，檔案級精度必需
- 這是唯一還需要腳本的場景

### Mode 3：overlap

**觸發**
```
/custom-skills-upstream-ops overlap <repo-path-or-source-name>
```

接受已註冊來源名稱（讀 sources.yaml 取路徑）或任意本地目錄路徑。

**實作**：純 AI workflow
1. 掃描目標 repo 的 `skills/`、`agents/`、`commands/` 等目錄
2. 對照本專案對應目錄的項目
3. 以名稱相似度 + 功能關鍵字 + 描述語意判斷重疊
4. 輸出：
   - 重疊清單（本專案 X ↔ 目標 Y，說明重疊類型）
   - 全新項目清單（目標有、本地無）
   - 可複製的 `overlaps.yaml` YAML 片段（對話內輸出，不寫檔）

**為何不寫 YAML 到檔案**
- `.standards/profiles/overlaps.yaml` 是 Profile 切換配置檔，由人維護
- overlap mode 只是協助產生 YAML 片段草稿，使用者複製貼上
- 避免自動寫檔造成意外覆寫

### Mode 4：maintenance

**觸發**
```
/custom-skills-upstream-ops maintenance <sub>
```

子命令：
- `update-last-sync <source>`：互動式確認後更新 `last-sync.yaml` 該來源的 commit 為當前 HEAD
- `archive-reports`：把 `upstream/reports/` 下過期（> 90 天）的報告移到 `upstream/reports/archive/`
- `list-orphans`：列出 `last-sync.yaml` 有、但 `sources.yaml` 沒有的孤兒條目，反之亦然

**實作**：AI workflow + 必要時輔以 shell 命令

## 遷移計畫

### 步驟

1. **建立新 skill**：`skills/custom-skills-upstream-ops/` 完整結構（SKILL.md + modes/ + references/ + scripts/）
2. **遷移腳本**：`check_uds.py` 從 `custom-skills-uds-update/scripts/` 搬到 `custom-skills-upstream-ops/scripts/`
3. **新增 slash command**：`commands/{claude,opencode}/custom-skills-upstream-ops.md`
4. **刪除舊 skill 目錄**：
   - `skills/custom-skills-upstream-sync/`
   - `skills/custom-skills-upstream-compare/`
   - `skills/custom-skills-uds-update/`
5. **刪除舊 slash commands**：
   - `commands/{claude,opencode}/custom-skills-upstream-sync.md`
   - `commands/{claude,opencode}/custom-skills-upstream-compare.md`
   - `commands/{claude,opencode}/uds-update.md`
6. **修 `script/commands/add_repo.py:246-258`**：
   - 提示文字改為建議使用 `/custom-skills-upstream-ops overlap <name>` 與 `audit`
   - `--analyze` flag 行為改為：不呼叫 Python 腳本，僅輸出「建議下一步」提示（flag 本身保留以相容 CLI API）
7. **更新 openspec specs**：
   - `upstream-skills/spec.md`：upstream-sync/compare 名稱改為 upstream-ops
   - `overlap-detection/spec.md`：重寫——移除「自動寫 `overlaps.yaml.draft`」行為；保留「偵測重疊、輸出建議 YAML 片段到對話」核心意圖；`/upstream-compare` 相關語句改為 `/custom-skills-upstream-ops overlap`
   - `status-upstream-sync/spec.md`：不動（僅讀 last-sync.yaml）
8. **更新文件**：
   - `docs/AI開發環境設定指南.md:1473-1476`：使用範例
   - `docs/dev-guide/workflow/copy-architecture.md:60`：推薦工具
   - `docs/ai-dev指令與資料流參考.md`：因改了 `add_repo.py`（專案規則要求必同步）
9. **CHANGELOG.md**：記錄合併與刪除
10. **Commit 驗證**：改完後跑 `git grep -E "analyze_upstream|sync_upstream|upstream-compare|upstream-sync|uds-update" -- . ':!openspec/changes/archive' ':!upstream/reports' ':!CHANGELOG.md'` 確認沒殘留

### 歷史輸出處理

| 路徑 | 處理 |
|------|------|
| `upstream/reports/structured/*.yaml` | 保留（git 歷史） |
| `upstream/reports/new-repos/*.md` | 保留 |
| `upstream/reports/analysis/*.md` | 保留 |
| `upstream/reports/uds-update/*.yaml` | 保留；未來改由 audit `--archive` 寫到 `upstream/reports/audit/` |
| `openspec/changes/archive/**` | 不動 |

## 風險與緩解

| 風險 | 影響 | 緩解 |
|------|------|------|
| 外部腳本/CI 呼叫 `analyze_upstream.py` | 遷移後會失敗 | 執行前全專案 grep；對話中發現外部呼叫再決定是否留 shim |
| `ai-dev add-repo --analyze` 既有使用者行為改變 | 使用者困惑 | flag 保留但行為改為提示；CHANGELOG 記錄 |
| overlap mode 的 AI 重疊偵測品質比舊腳本低 | 使用者體驗倒退 | 範本明確要求列出比較依據（名稱、關鍵字、描述），結果可人工覆核；`.standards/profiles/overlaps.yaml` 本身仍是人工維護，AI 只是協助 |
| 歷史 YAML 結構化報告被其他地方讀取 | 讀取失敗 | grep 驗證無活依賴；僅 `add_repo.py` 用到，已在遷移步驟處理 |
| openspec `overlap-detection` spec 改寫幅度大 | 可能遺漏 scenario | 新 spec 保留原 Requirement 骨架，僅改 GIVEN/WHEN 的觸發入口 |

## 不在本設計範圍內（Out of Scope）

- 不改 `upstream/sources.yaml` 或 `last-sync.yaml` schema
- 不動 `ai-dev` CLI 本身的 `update` / `clone` / `status` 指令
- 不動 `tool-overlap-analyzer`（本專案內部工具重疊，職責與 upstream-ops 不同）
- 不處理 `.standards/profiles/overlaps.yaml` 現有內容的重構（僅改草稿產生器的實作方式）
- 不新增主動通知機制（cron / hook 提醒漂移）——使用者驅動，不自動
- 不處理 `docs/ecc/*` 下的多份參考文件更新（僅當 audit/overlap 範例有變動時順手帶到）

## 驗收標準

實作後應滿足：

1. 單一 `/custom-skills-upstream-ops` slash command 能執行 audit / uds-check / overlap / maintenance 四種 mode
2. `skills/` 下不再存在 `custom-skills-upstream-sync`、`custom-skills-upstream-compare`、`custom-skills-uds-update` 目錄
3. `script/commands/add_repo.py` 不再直接呼叫 Python 腳本
4. `git grep` 上述舊 skill 名稱，僅剩 `CHANGELOG.md`、`openspec/changes/archive/`、`upstream/reports/` 三處歷史紀錄
5. `ai-dev status` 顯示「上游同步狀態」表格功能不變（status-upstream-sync spec 未動）
6. `.standards/profiles/overlaps.yaml` 內容與格式未變
7. UDS 檔案級漂移檢測（原 uds-update 行為）透過 `uds-check` mode 仍可正常執行

## 後續

設計通過後，透過 superpowers:writing-plans skill 建立實作計畫。
