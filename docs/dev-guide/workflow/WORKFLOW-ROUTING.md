# AI 工作流路由與專案覆寫指南

本文件定義 ai-dev 通用 prompt 如何選擇技能與工作流，以及專案如何加上自己的
tracker、安全與交付規則。

目標不是建立另一套完整流程，而是避免代理在一般任務中自行啟動 Superpowers、
OpenSpec 或 Matt Pocock skills 的高階流程。

## 高階流程

```text
使用者提出任務
    ↓
先讀取專案規則與既有工件
    ↓
使用者是否明確指定高階工作流，或直接接續既有工件？
    ├─ 是：使用該工作流，並遵守專案覆寫
    └─ 否：選擇最小必要的模型呼叫型技能
             ├─ 不需要技能：直接處理與驗證
             ├─ 調查／除錯／測試／審查：使用對應 primitive
             ├─ 需要選擇能力層級、派工形狀或審查：使用 custom-agent-router
             └─ 需要持久追蹤：使用專案已宣告的 tracker
```

通用 prompt 只決定「是否能啟動流程」。tracker、Git、正式環境與資料庫等具體
權限，由每個專案自己的 `AGENTS.md`、`CLAUDE.md` 或其他入口文件決定。

## 四層責任

| 層級 | 責任 | 典型位置 |
|------|------|----------|
| 通用執行規則 | 最小技能選擇、高階流程呼叫權、專案規則優先 | `project-template/AGENTS.md` 等 managed block |
| 通用操作指南 | 解釋流程差異、選擇原則與工具用法 | `docs/dev-guide/workflow/` |
| 整合介面 | 將 spec、ticket、claim 等動作映射到專案 tracker | 專案的 `docs/agents/issue-tracker.md` |
| 專案覆寫 | 專案安全、環境、資料、Git 與交付規則 | 專案自己的 `AGENTS.md`／`CLAUDE.md` |

通用層不得寫入只適用單一 repo 的路徑、帳號、tracker 名稱或部署規則。

## 呼叫權

### 可由模型按需選擇

模型可以從已安裝的 primitive skills 中選擇最小必要組合，例如：

- 調查：`research`
- 除錯：`diagnosing-bugs`
- 測試驅動實作：`tdd`
- 完成前審查：`code-review`
- 程式邊界：`codebase-design`
- 領域模型：`domain-modeling`
- 合併衝突：`resolving-merge-conflicts`

這不是強制每個任務都要使用技能。簡單問答、唯讀確認與可直接驗證的小修改可以
直接完成。

工作目標、範圍與授權已明確，但還需要在主 Agent 直接處理、單一工作代理或有限
平行間選擇，或需要依複雜度與風險決定能力層級、審查與備援時，使用
`custom-agent-router`。它接在本文件的流程判斷之後，不得自行啟動高階工作流、
建立任務追蹤器或擴大專案授權。

### 必須由使用者啟動

下列流程會建立規格、票券、工作樹、提交或其他持久狀態，只能在使用者明確指定時
啟動：

- Superpowers 高階流程
- OpenSpec change 生命週期
- Matt 的 `ask-matt`、`grill-with-docs`、`to-spec`、`to-tickets`、
  `implement`、`triage`、`wayfinder` 等使用者呼叫型流程

使用者直接指定既有 plan、change、proposal、spec 或 ticket，也視為明確要求接續
該工件。代理必須沿用原本的真相來源，不得另外建立另一份 spec。

## Tracker 是專案介面

通用 prompt 不指定 GitHub Issues、Beads、Jira、Linear 或 Markdown ticket。

專案若已宣告 canonical tracker：

1. Matt setup 與其他技能必須沿用它。
2. 不得因 remote 類型推導並建立第二套 tracker。
3. spec、ticket、dependency、claim、comment、close 必須依專案 adapter 執行。
4. 外部 issue 可作為輸入，但是否轉入內部 tracker 由專案規則決定。

專案未宣告 tracker 時：

- 單一 session 可完成的工作，不因形式需要新增 tracker。
- 確實需要跨 session、依賴或多人認領時，再由使用者或專案初始化流程選擇 tracker。

## Matt setup 的正確順序

`setup-matt-pocock-skills` 是 repo 一次性整合工具，不是每個任務的啟動步驟。

```text
先確認專案是否已有 tracker 與入口規則
    ↓
已有：沿用現況，只在缺少 adapter 時執行 setup
    ↓
沒有：先決定 tracker，再執行 setup
    ↓
審閱草稿後才允許寫入
```

若專案採 Beads，應先完成 Beads 初始化，再於 setup 選擇 `Other: Beads`。若專案
已有人工作業的 Beads adapter，可以完全不執行 setup。

## OpenSpec 與 Superpowers

通用 harness 可以安裝兩者，但安裝不代表每個任務都要使用。

| 情境 | 建議 |
|------|------|
| 使用者明確指定 OpenSpec | 依 change 工件執行與驗證 |
| 使用者指定既有 OpenSpec change | 接續原 change，不建立 Matt spec |
| 使用者明確指定 Superpowers | 執行指定技能或既有 plan |
| 未指定高階流程 | 使用最小技能或直接處理 |
| 專案規則要求特定流程 | 依專案規則，必要時先取得批准 |

代理可以建議使用高階流程，但不能把建議當成已取得授權。

## Harness 原生記憶的邊界

經驗學習與持久記憶交由各 harness agent tool 的原生能力處理。記憶或經驗被載入，
不代表已取得啟動高階流程、修改 tracker、Git、正式環境、服務、資料庫或機密的權限；
這些行為仍須依使用者指令與專案規則判斷。已退役機制見
[`archive/auto-skill/`](../../../archive/auto-skill/README.md)。

## 專案覆寫範例

```markdown
## 專案工作流覆寫

- 本 repo 的 canonical tracker 是 <tracker>。
- 高階工作流只有使用者明確指定或接續既有工件時使用。
- <正式環境、資料庫、機密與 Git 規則> 優先於任何技能。
- 若技能與本節衝突，說明跳過或調整的步驟。
```

專案覆寫應放在 ai-dev managed block 之外，避免模板更新時覆蓋；若專案同時維護
`AGENTS.md` 與 `CLAUDE.md`，實質規則必須同步。

## 本 repo 的設定

custom-skills 本身使用：

- Beads：執行狀態、認領、依賴與 ready。
- OpenSpec：使用者明確指定或接續既有 change 時的正式工件。
- GitHub Issues：外部需求入口。

具體映射以 [`docs/agents/issue-tracker.md`](../../agents/issue-tracker.md) 為準。
這是 custom-skills 的專案覆寫，不會寫入通用 project template。

## 維護位置

| 內容 | 修改位置 |
|------|----------|
| 通用 runtime 規則 | repo 根目錄 `AGENTS.md`、`CLAUDE.md`、`GEMINI.md`、`INSTRUCTIONS.md` 的 managed block |
| 分發模板 | 執行 `uv run python -m script.main maintain template` 同步 `project-template/` |
| 通用流程說明 | 本文件 |
| OpenSpec 詳細操作 | `DEVELOPMENT-WORKFLOW.md` |
| Matt 技能說明 | `MATTPOCOCK-SKILLS-GUIDE.md` |
| 新人安裝入口 | `docs/AI開發環境設定指南.md` |
| tracker 與安全覆寫 | 各專案自己的入口文件與 `docs/agents/` |

修改通用 runtime 規則後，至少執行：

```bash
uv run python -m script.main maintain template --check
uv run pytest tests/test_project_command.py tests/test_project_template_manifest.py
```
