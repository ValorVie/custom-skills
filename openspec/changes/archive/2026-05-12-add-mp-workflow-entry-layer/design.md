## Context

本 change 來自對 `mattpocock/skills` 的定位分析與第一性原理裁切。

已確認的基礎事實：

- `superpowers` 應保留為任務內執行紀律：TDD、除錯、review、完成前驗證。
- `openspec` 應保留為正式變更生命週期：proposal、design、tasks、spec、verify、archive。
- `mattpocock/skills` 不應整包導入；真正有價值的是工作入口鏈路。
- Claude Code 與 Codex 都是本專案的主要使用面，導入不可只服務其中一方。
- 技能內容應以繁體中文撰寫，英文保留於技能名稱、路徑、產品名、固定術語與真實設定鍵。

參考文件：

- `docs/report/2026050612-01-mattpocock-skills-workflow-positioning.md`
- 上游快照：`mattpocock/skills@b843cb5`
- `docs/dev-guide/workflow/copy-architecture.md`
- `README.md` 的 `ai-dev install/update/clone` 行為說明

## Goals / Non-Goals

**Goals:**

- 建立一組 `mp-*` 技能，補足需求進入 `openspec` 前的對齊與成形流程。
- 同時支援 Claude Code 與 Codex 的技能投影與專案入口文件。
- 讓 `mp-to-issues` 預設能輸出 OpenSpec `tasks.md` 友善的垂直切片。
- 讓 `mp-triage` 使用狀態模型，而不是綁死特定 issue tracker label。
- 讓 `mp-improve-codebase-architecture` 只產出架構候選，不直接實作或重構。
- 建立 `mattpocock/skills` 上游追蹤資料，保留來源技能與本地 `mp-*` 技能的固定對照。
- 避免導入與 `superpowers` 重疊的上游 `tdd`、`diagnose`。

**Non-Goals:**

- 不替換 `superpowers`。
- 不替換 `openspec`。
- 不直接用 `npx skills add mattpocock/skills` 安裝整包上游技能。
- 不在本 change 中導入上游 personal、misc、deprecated 技能。
- 不要求所有專案立即建立 `CONTEXT.md` 或 `docs/adr/`；由 `mp-grill-with-docs` 在真正需要時建立。

## Architecture

MP 工作入口層位於 `openspec` 與 `superpowers` 前方：

```text
模糊需求 / 新想法
        │
        ▼
┌──────────────────────────────┐
│ MP 工作入口層                 │
│ - setup                       │
│ - grill                       │
│ - slice                       │
│ - triage                      │
│ - architecture review          │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│ OpenSpec 變更生命週期         │
│ proposal / design / tasks / spec│
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│ Superpowers 任務內紀律        │
│ TDD / 除錯 / review / verify  │
└──────────────────────────────┘
```

### 技能分層

| 階段 | 本地技能 | 來源技能 | 職責 | 優先級 |
|---|---|---|---|---|
| 儲存庫設定 | `mp-setup-matt-pocock-skills` | `setup-matt-pocock-skills` | 建立 `docs/agents/` 與 Claude / Codex 入口規則 | P0 |
| 需求澄清 | `mp-grill-with-docs` | `grill-with-docs` | 追問、校準詞彙、沉澱 `CONTEXT.md` / ADR | P0 |
| 任務切片 | `mp-to-issues` | `to-issues` | 將需求切成可驗證垂直切片 | P0 |
| 任務分流 | `mp-triage` | `triage` | 判斷 `needs-info` / `ready-for-agent` / `ready-for-human` 等狀態 | P1 |
| 架構回看 | `mp-improve-codebase-architecture` | `improve-codebase-architecture` | 找出架構摩擦與 deep module 候選 | P1 |
| 需求摘要 | `mp-to-prd` | `to-prd` | 將既有對話整理成 PRD / OpenSpec proposal 前置素材 | P2 |

### Claude / Codex 投影

本 change 不接受單一工具假設。實作完成後至少要滿足：

```text
skills/mp-*              ← canonical skill source
        │
        ├── .claude/skills/mp-*   ← Claude Code projection
        └── .codex/skills/mp-*    ← Codex projection

CLAUDE.md  ← Claude Code 入口提示
AGENTS.md  ← Codex 入口提示
docs/agents/* ← 共同真實來源
```

`docs/agents/` 是共同真實來源。`CLAUDE.md` 與 `AGENTS.md` 只應放入口提示與讀取規則，不應各自維護一份不同的工作流定義。

## Decisions

### D1: 本地命名保留上游辨識度

**選擇：** 以 `mattpocock/skills@b843cb5` 為參考，重寫成本專案技能，命名採 `mp-<來源技能名>`。

**理由：**

- 上游正式技能包含 `tdd`、`diagnose`，與 `superpowers` 重疊。
- 上游 setup 以 Claude Code 假設為主，不符合本專案至少要支援 Claude Code 與 Codex 的要求。
- 本專案技能需要繁體中文、既有目錄慣例與多投影同步。
- 保留來源技能名可降低維護成本；未來上游更新時，可直接用 mapping 找到對應的本地技能。

### D2: 不直接安裝上游整包

**選擇：** 不使用 `npx skills add mattpocock/skills` 作為導入方式。

**理由：**

- 需要裁切，而不是整包導入。
- 需要保留 `superpowers` 與 `openspec` 邊界。
- 需要維持本地 `mp-*` 客製內容。

### D3: P0 只放最大空白

**選擇：** P0 為 `mp-setup-matt-pocock-skills`、`mp-grill-with-docs`、`mp-to-issues`。

**理由：**

- `setup` 解決儲存庫工作規則與多工具入口。
- `grill` 解決需求澄清與專案語言沉澱。
- `slice` 解決大需求進入實作前沒有垂直切片的問題。

### D4: triage 從 label 改成狀態模型

**選擇：** `mp-triage` 先定義狀態，再由 adapter 映射到 GitHub issue、OpenSpec tasks 或本地 Markdown。

**理由：**

上游 `triage` 綁 issue tracker label。對本專案來說，工作項目可能存在於 OpenSpec、GitHub issue 或本地文件。核心需求是判斷任務是否可交給 agent，不是管理 label。

### D5: architecture review 只產候選

**選擇：** `mp-improve-codebase-architecture` 只能輸出候選、理由、受影響檔案與測試方向，不得直接修改程式碼。

**理由：**

架構回看應避免在原任務中擴大範圍。若使用者選定候選，應另開 OpenSpec change 或明確納入既有 change。

### D6: intake brief 延後

**選擇：** `mp-to-prd` 納入 P2，不阻塞 P0/P1。

**理由：**

PRD 摘要有價值，但它可由 `mp-grill-with-docs` 的輸出暫時替代。先完成 setup、grill、slice 才能立即補空白。

### D7: 上游更新採人工審核，不自動覆蓋

**選擇：** 將 `mattpocock/skills` 登記到 `upstream/sources.yaml`，但 `install_method` 使用 `manual`；本地技能透過 `upstream/mattpocock-skills/mapping.yaml` 記錄來源對照。

**理由：**

- 本地 `mp-*` 技能是改寫版，不是上游檔案的直接複製。
- 上游更新可能改變 prompt 結構、Claude Code 假設或技能邊界，不能自動覆蓋。
- mapping 可讓維護者只審核選定來源技能，而不是每次掃整包。

維護流程：

```text
ai-dev update
  -> 拉取 ~/.config/mattpocock-skills
  -> /custom-skills-upstream-ops audit --source mattpocock-skills
  -> 依 upstream/mattpocock-skills/mapping.yaml 檢查選定技能差異
  -> 人工決定是否更新 skills/mp-*/
  -> 更新 upstream/mattpocock-skills/last-sync.yaml
```

`upstream/sources.yaml` 應新增的來源形狀：

```yaml
mattpocock-skills:
  repo: mattpocock/skills
  branch: main
  local_path: ~/.config/mattpocock-skills/
  format: claude-code-native
  install_method: manual
```

`upstream/mattpocock-skills/last-sync.yaml` 應至少記錄：

```yaml
source: mattpocock-skills
repo: mattpocock/skills
commit: b843cb5ea74b1fe5e58a0fc23cddef9e66076fb8
status: manually-adapted
```

`upstream/mattpocock-skills/mapping.yaml` 應明確分成已採用與已排除兩類，避免未來更新時把整包上游當成待同步清單：

```yaml
source: mattpocock-skills
skills:
  setup-matt-pocock-skills:
    local_skill: skills/mp-setup-matt-pocock-skills/
    priority: P0
    adaptation: rewritten
  grill-with-docs:
    local_skill: skills/mp-grill-with-docs/
    priority: P0
    adaptation: rewritten
  to-issues:
    local_skill: skills/mp-to-issues/
    priority: P0
    adaptation: rewritten
  triage:
    local_skill: skills/mp-triage/
    priority: P1
    adaptation: rewritten
  improve-codebase-architecture:
    local_skill: skills/mp-improve-codebase-architecture/
    priority: P1
    adaptation: rewritten
  to-prd:
    local_skill: skills/mp-to-prd/
    priority: P2
    adaptation: rewritten
excluded:
  tdd:
    reason: covered-by-superpowers
  diagnose:
    reason: covered-by-superpowers
```

## Skill Contracts

### `mp-setup-matt-pocock-skills`

- MUST inspect existing `AGENTS.md`, `CLAUDE.md`, `docs/agents/`, `CONTEXT.md`, `CONTEXT-MAP.md`, `docs/adr/`.
- MUST update both Claude Code and Codex entrypoints when both exist.
- MUST write shared rules under `docs/agents/`.
- MUST NOT duplicate divergent workflow descriptions in `CLAUDE.md` and `AGENTS.md`.

### `mp-grill-with-docs`

- MUST 在需要使用者輸入時，一次只問一個決策問題。
- MUST inspect code when the answer can be found locally.
- MUST 只在專案語言不只對單一實作細節有意義時更新 `CONTEXT.md`。
- MUST create ADR only when the decision is hard to reverse, surprising without context, and based on real trade-offs.

### `mp-to-issues`

- MUST produce vertical slices.
- MUST mark slices as `AFK` or `HITL`.
- MUST support at least three output modes: OpenSpec tasks, GitHub issue draft, local Markdown.
- MUST 在來源素材是 OpenSpec change 時，優先輸出 OpenSpec tasks 格式。

### `mp-triage`

- MUST use a shared state model:
  - `needs-triage`
  - `needs-info`
  - `ready-for-agent`
  - `ready-for-human`
  - `wontfix`
- MUST keep state names independent from external label names.
- MUST preserve prior triage findings and avoid re-asking resolved questions.

### `mp-improve-codebase-architecture`

- MUST read `CONTEXT.md` / `CONTEXT-MAP.md` and relevant ADRs before proposing candidates.
- MUST use consistent architecture terms: module、interface、implementation、depth、seam、adapter、leverage、locality。
- MUST present candidates before proposing interfaces.
- MUST NOT edit application code.

### `mp-to-prd`

- MUST 從既有對話與儲存庫脈絡整理內容。
- MUST NOT restart a full interview.
- MUST output content that can feed OpenSpec proposal/design/tasks.

## Risks / Trade-offs

| 風險 | 緩解 |
|---|---|
| 與 `superpowers` 重疊 | 不導入上游 `tdd`、`diagnose`，只在文件中記錄可吸收原則 |
| 與 `openspec` 邊界混淆 | 明確規定 MP 只處理入口、切片、分流與架構候選 |
| Claude / Codex 入口分歧 | `docs/agents/` 作為共同真實來源，兩個入口只引用 |
| 過度文件化 | `CONTEXT.md` 與 ADR 採 lazy creation，只有需要時才建立 |
| skill 名稱衝突 | 全部使用 `mp-*` 前綴，不覆寫上游或既有技能 |
| 上游更新覆蓋本地客製 | `mattpocock/skills` 使用 `manual` 追蹤與 mapping 審核，不自動覆蓋 |

## Validation Plan

- `openspec validate add-mp-workflow-entry-layer --strict`
- 檢查 `skills/mp-*/SKILL.md` 都有有效 frontmatter。
- 檢查 `CLAUDE.md` 與 `AGENTS.md` 都引用同一組 `docs/agents/` 文件。
- 檢查 `.claude/skills/mp-*` 與 `.codex/skills/mp-*` 投影存在。
- 執行 skill 觸發案例文字檢查，確保 `tdd` / `diagnose` 不會被 MP 技能覆蓋。
