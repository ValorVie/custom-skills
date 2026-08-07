---
title: 通用 Agent Router 設計
type: plan/rfc
topic: agent-orchestration
date: 2026080710-01
author: ValorVie
status: implemented
rfc_id: custom-agent-router-001
tracking: custom-skills-v00
---

# 通用 Agent Router 設計

## 高階摘要

- 提案內容：建立一套以政策為主的通用 Agent Router。通用核心只判斷任務模式、
  能力層級、風險、派工形狀、審查與失敗升級；實際模型由執行環境設定綁定，
  專案規則由專案適配層加上。
- 目前狀態：通用 Skill、Codex runtime profile、QDM adapter、跨 repo 契約測試與
  文件型角色試行都已完成。
- 實作位置：通用政策在 `SKILL.md`，Codex 綁定在 `profiles/codex.md`；
  `qdm-agent-team` 只保留 QDM 差異。
- 明確不做：第一版不寫排程器、佇列、Agent 登錄表、Hook 或新任務追蹤器，也不
  安裝第三方調度框架。
- 採納條件：使用同一組案例驗證路由結果；替換執行環境設定時不改通用核心；
  QDM 適配層能保留現有 Beads、Git、批准與環境安全規則。

```text
使用者請求與既有規則
        ↓
專案適配層提供專案限制
        ↓
通用路由政策 ← 執行環境設定提供可用能力
  mode → tier → risk → shape → review → fallback
        ↓
執行環境原生 Agent／工具
        ↓
驗證與路由紀錄
```

這個順序不是權限階層。系統、使用者授權與專案規則仍優先；Agent Router 只能在既有權限
內選擇執行方式，不能因為換模型、派工或備援擴大範圍。

## 動機

現有 `qdm-arch/.agents/skills/qdm-agent-team/SKILL.md` 已包含完整的
QDM 工作樹、Beads、Git、批准與審查安全邊界，但它把專案限制與 Sol／Terra
角色綁在同一份 Skill。直接拿它當通用母體，需要先刪除大量 QDM 規則，也容易讓
通用版本與 QDM 版本各自演化。

外部方案提供了可借用的路由語意，但完整安裝通常連帶加入角色、全域設定、Hook
或自己的工作流。這些不是目前缺少的部分。現在需要的是一份可移植的決策規則，
讓不同執行環境和專案用自己的模型綁定與安全邊界接入。

### 與既有工作流路由的關係

[WORKFLOW-ROUTING.md](../../docs/dev-guide/workflow/WORKFLOW-ROUTING.md) 已經是通用工作流入口，
負責判斷是否啟動高階流程、選擇最小必要 Skill，以及沿用專案任務追蹤器。Agent Router
接在它後面，只處理已獲授權且邊界可判斷的工作：主 Agent 是否直接做、要用哪個
能力層級、是否委派、如何審查。

```text
既有工作流路由
  直接處理／基礎 Skill／使用者指定的高階流程
        ↓
形成一個可執行的工作
        ↓
Agent Router
  直接執行／單一工作代理／有限平行 ＋ 能力層級／審查
```

因此不建立第二份工作流政策，也不把 Agent Router 的完整內容塞進每個專案
永遠載入的 `ai-dev-project` 管理區塊。該區塊只保留能準確觸發 Skill 的短指標。

## 目標與非目標

### 目標

- 小工作留在主 Agent；只有獨立且值得委派的工作才建立工作代理。
- 路由政策使用能力名稱，不把產品模型名稱散落在核心 Prompt。
- 提示規則、設定與程式碼各自負責適合的問題，避免用提示規則假裝安全控制。
- 失敗後有限修正與升級，不無限重試，也不擴張授權。
- 通用核心可以被 QDM 和非 QDM 專案共用。

### 非目標

- 不取代 Codex、Claude 或其他執行環境的原生子代理工具。
- 不負責跨機佇列、工作持久化、排程服務或成本帳務系統。
- 不建立通用任務追蹤器；專案適配層使用專案已選定的系統。
- 不以 Hook 當作第一版相依，也不以 Hook 取代 sandbox、工具允許清單或 OS 權限。
- 不在本 RFC 決定哪個模型永遠優於另一個模型；模型綁定必須以當前執行環境能力
  與實測結果為準。

## 設計原則

### 最小形狀

Agent Router 先問主 Agent 能否更便宜、可靠地直接完成。能直接完成就不派工。一個獨立
工作流只需要一個工作代理；只有兩個以上已就緒的工作彼此獨立、寫入責任不重疊，
才使用有限平行。

### 分離決策與綁定

通用核心輸出 `light / standard / frontier`。執行環境設定才知道這三層目前對應
哪些模型、effort、角色與能力。更換模型不應改寫 intent、risk 或 review 規則。

### 限權繼承

專案適配層可以增加限制，不能放寬上層規則。派工、重試或升級只改變執行者，
不改變允許修改的檔案、可用工具、外部 mutation 或批准範圍。

### 可追溯但不另建系統

每次非直覺路由留下一行路由紀錄，寫進現有工作紀錄、任務追蹤器或階段報告。
Agent Router 不保存另一份任務狀態。

## 元件設計

### 通用路由政策

形式是一份供 Agent 讀取的提示規則／Skill。它負責：

- 判斷互動模式、能力 tier、風險與派工形狀。
- 產生派工說明、寫入責任、驗收條件與停止條件。
- 選擇審查強度與有限備援。
- 輸出路由紀錄。

它不知道 Beads、GitHub Issues、QDM 路徑或實際模型 ID，也不直接建立權限。

### 執行環境設定

執行環境設定（runtime profile）是小型設定或 Agent 可讀的模型對照表，內容只包含
當前執行環境能驗證的
事實：

目前已驗證的 Codex 設定在 [profiles/codex.md](profiles/codex.md)：`light` 綁
`terra_worker`、`standard` 綁 `terra_builder`、`frontier` 綁 Sol Lead，fresh review
綁 `sol_reviewer`。Luna 在目前 runtime 不可用；`light` 與 `standard` 使用同一個
Terra 模型與 effort，只以工作契約區分。

第一版仍由 Agent 讀取 profile，不寫載入程式。Reviewer 的唯讀能力必須由 runtime
metadata 證明；角色檔或 Prompt 文字不能代替證據。

### 專案適配層

專案適配層（project adapter）是專案提示規則與既有硬性保護的組合。它負責：

- 何時載入通用 Agent Router，以及哪些工作維持直接執行。
- 專案的任務追蹤器、文件真相、寫入責任與 Git 規則。
- mutation、機密、正式環境、費用與人工批准邊界。
- 專案需要的驗證與完成聲明標準。

專案適配層只寫差異，通用 mode、tier、dispatch 與 fallback 定義仍以通用路由政策
為單一真相來源。

### 執行環境原生執行層

第一版直接使用平台提供的 Agent、工具、sandbox 與批准能力。Agent Router 不包裝
它們，也不假設所有執行環境有相同的 Hook 生命週期。若執行環境無法證明某項必要
能力，例如全新上下文的唯讀審查者，設定檔應標成不可用並停止或使用備援，
不能只靠 Prompt 宣稱成立。

## 路由流程

### 1. 確認 authority 與工作邊界

讀取使用者要求、專案規則與必要上下文。缺少的資訊只有在會改變結果、權限或
風險時才詢問。完成條件是目標、允許範圍、驗收方式和停止條件足以選擇下一步。

### 2. 選擇互動模式

| Mode | 判斷條件 | 第一個動作 |
|------|----------|------------|
| `execute` | 結果、範圍與驗收清楚 | 直接做，或交給最低可勝任 tier |
| `explore_then_plan` | 方向清楚，但證據不足、跨元件或回復昂貴 | 做有限唯讀調查，形成一個可驗證 slice |
| `co_discover` | 問題、產品選擇或驗收仍不清楚 | 釐清會改變方向的問題，只做低成本探查 |

mode 描述互動方式，不代表風險。清楚的高風險操作仍須通過風險閘門。

### 3. 選擇能力 tier

| Tier | 工作形狀 |
|------|----------|
| `light` | 搜尋、列舉、重現、測試、格式與規則固定的機械工作 |
| `standard` | 邊界清楚但需要工程判斷的實作、除錯、整合與審查 |
| `frontier` | 歧義、架構、跨元件根因、安全、不可逆決策與最終仲裁 |

高能力層級可以暫代低能力層級，但要在路由紀錄中標示模型綁定偏差。低能力層級不替代必要的
安全、架構或高風險判斷。

### 4. 套用風險閘門

| Risk | 典型條件 | 最低驗證 |
|------|----------|----------|
| `low` | 局部、可回復、驗收直接 | 執行者自測；主 Agent 回查 |
| `material` | 跨檔案／元件，或會改變使用者可見行為 | 主 Agent 整合驗證；依不確定性使用全新上下文審查 |
| `high` | 資安、發布、外部狀態或回復昂貴 | 明確計畫／批准閘門；完成後使用全新上下文審查 |
| `critical` | 資料遺失、正式流量、不可逆或重大權限影響 | 停止自動執行，取得明確批准與獨立驗證 |

risk 控制批准與審查，不直接決定使用幾個 Agent。

### 5. 通過派工煞車

派工前必須能回答：

1. 每個工作代理的完成結果是否可以一句話說清楚？
2. 主 Agent 直接做是否更便宜可靠？
3. 工作是否能在沒有等待另一個工作代理的情況下前進？
4. 每個可寫工件是否只有一個負責者？
5. 誰負責整合與最後驗證？

無法回答時維持 `direct` 或先調查，不展開平行派工。通過後只選以下三種形狀：

| Shape | 適用條件 |
|-------|----------|
| `direct` | 小工作、緊密耦合問題、方向仍需主 Agent 判斷 |
| `single_worker` | 一個邊界和驗收都清楚的獨立工作流 |
| `bounded_parallel` | 至少兩個已就緒工作獨立且寫入責任不重疊 |

### 6. 審查與有限備援

- `low` 預設由主 Agent 回查，不為形式建立審查者。
- `material` 在跨模組、不確定性高或作者偏誤可能影響結果時，使用全新上下文審查者。
- `high / critical` 的完成聲明需要全新上下文審查；批准本身不等於驗證。
- 第一次失敗先修正派工說明、證據或環境問題，同一能力層級最多重試一次。
- 同原因再失敗時最多升一個 tier。升級後仍失敗，或必要能力不可用，就交回主
  Agent／使用者，不再自動重跑。

## 路由紀錄契約

非 trivial 的派工、升級或高風險直接執行，都留下一行：

```text
mode=execute risk=material tier=standard shape=single_worker owner=builder review=fresh fallback=one-tier-max
```

| 欄位 | 允許值或內容 |
|------|--------------|
| `mode` | `execute`、`explore_then_plan`、`co_discover` |
| `risk` | `low`、`material`、`high`、`critical` |
| `tier` | `light`、`standard`、`frontier` |
| `shape` | `direct`、`single_worker`、`bounded_parallel` |
| `owner` | 負責交付的角色或 Agent 名稱 |
| `review` | `lead`、`fresh`、`approval+fresh` |
| `fallback` | `none`、`same-tier-once`、`one-tier-max` |

路由紀錄只保存決策，不取代派工說明、測試證據或任務追蹤器狀態。第一版只要求格式
一致，不寫解析程式或資料庫。

## 提示規則、設定與程式碼邊界

| 問題 | 第一版位置 | 原因 |
|------|------------|------|
| intent、tier、risk、拆分與審查判斷 | 提示規則 | 需要理解語意和上下文 |
| tier 對應模型、執行環境能力與並行上限 | 執行環境設定 | 會隨環境改變，不屬於通用政策 |
| 任務追蹤器、Git、路徑和批准規則 | 專案適配層 | 每個專案不同 |
| Agent 建立、逾時、sandbox、權限 | 執行環境原生能力 | 必須由實際執行層保證 |
| 路由紀錄的說明 | 提示規則 | 是決策輸出的一部分 |
| 路由紀錄結構、成本統計、跨執行環境自動備援 | 暫不實作 | 有真實自動化需求後才值得寫程式 |

## 第一版不加入 Hook

Hook 會綁定特定執行環境的事件名稱、執行順序與攔截範圍。通用邊界尚未從真實使用
中長出來前，維護 Hook 的成本高於收益，也可能讓使用者誤以為所有執行路徑都受到
保護。

日後只有同時符合以下條件，才把檢查點實作成執行環境適配層中可阻擋操作的 Hook：

- 要保護的是可機械判定、違反後有明確損失的不變條件。
- 執行環境能證明 Hook 在所有相關路徑都會觸發，而且可以阻擋操作。
- 原生權限、sandbox 或既有 wrapper 無法更直接地解決問題。
- 可以測試正常路徑、拒絕路徑、旁路與 Hook 失效時的停止行為。
- Hook 留在執行環境適配層，不污染通用路由政策。

可能的檢查點只有 `before_dispatch`、`before_mutation` 與
`before_complete`。其中資安、DB、機密或正式環境限制仍應由權限層保護，Hook 只
補工作流程，不能成為唯一安全邊界。

## 建議的第一版包裝

正式來源就是 `skills/custom-agent-router/`，沿用本專案現有的技能分發與投影
機制，不另開一個通用規則 repo：

```text
custom-agent-router/
├── SKILL.md                 # 通用路由政策與路由紀錄契約
├── DESIGN.md                # 分層、邊界與演進依據
└── profiles/
    └── codex.md             # Codex 模型綁定與可驗證能力
```

專案 adapter 留在各專案，避免通用 repo 反向擁有專案規則。第二個 runtime 出現時，
再新增另一份 profile。

## QDM 接入方式

QDM 適配層引用通用 Agent Router，再保留現有 QDM 規則：

- 使用者明確要求 agent team／multi-agent 時才啟用團隊路徑。
- Beads 是唯一持久任務追蹤器，Lead 獨占任務追蹤器與 Git 暫存區。
- 共用工作樹維持單一寫入者，未預期變更立即停止。
- DB、正式環境、OFS、機密、付費與外部 mutation 依 repo 規則取得批准。
- 全新上下文審查者必須以執行環境資訊證明上下文與唯讀能力。

這個接入已完成：`qdm-agent-team` 現在是薄 adapter，引用通用 Router 與 Codex profile，
不再保存 mode、tier、dispatch、fallback 或模型對照。QDM 安全規則仍留在 qdm-arch。

## 驗證案例

第一版以固定案例搭配小型 pytest 契約測試回歸；測試只檢查分層與固定不變條件，
不把語意路由硬編成調度程式：

| 案例 | 預期路由 |
|------|----------|
| 回答單一事實或唯讀確認 | `execute / light / low / direct / lead` |
| 邊界清楚的單一工程修改 | `execute / standard / material / single_worker / lead` |
| 兩個獨立且不寫同檔的盤點 | `execute / light / low / bounded_parallel / lead` |
| 需求與驗收仍有產品歧義 | `co_discover / frontier / direct` |
| 跨元件、證據不足但方向清楚 | `explore_then_plan / frontier / material / direct` |
| DB 或正式環境 mutation | `explore_then_plan / frontier / critical / approval+fresh` |
| 低能力層級不可用 | 記錄模型綁定偏差後升一層，或由主 Agent 直接處理 |
| 必要的全新上下文審查者不可用 | 停止高風險完成聲明，不以自審冒充 |

完成標準是每個案例能得到可解釋且符合預期約束的路由紀錄；替換執行環境設定只能改變
實際模型，不改變 mode、risk、shape 與安全邊界。

## 實作順序

### 階段 1：通用提示規則（已完成）

已在 `custom-skills` 建立最小 `SKILL.md`，並讓既有工作流路由只增加一個觸發
指標。上述案例、Skill 結構與模板同步通過驗證；Skill 內沒有 QDM 名稱或特定
任務追蹤器規則。

### 階段 2：執行環境設定（已完成）

Codex profile 已核對模型、effort、全新上下文、sandbox 與並行限制。三種 binding
都完成角色前向測試；Luna 不可用與 read-only parent 限制已明列，不依名稱推測能力。

### 階段 3：QDM 適配層（已完成）

`qdm-agent-team` 已刪除重複路由語意，保留 QDM 差異。跨 repo 契約測試、Builder、
Worker 與獨立 read-only Sol Reviewer 的文件型試行都已通過。

### 階段 4：依失敗證據演進

記錄路由偏差、重試、成本與被跳過的閘門。只有提示規則／設定無法穩定保護的機械
不變條件，才評估程式碼或 Hook。完成條件是新增機制對應已觀察到的失敗，而不是
預想中的框架需求。

本次試行的缺陷都能由 Router、handoff 與 Reviewer 契約攔截，沒有出現需要 Hook 才能
阻擋的旁路，因此現階段不新增 Hook 或常駐調度程式。

## 替代方案

### 直接修改 qdm-agent-team

短期檔案最少，但通用核心會帶著 QDM 例外開始，之後還要反向拆除。保留它做 QDM
適配層，責任比較清楚。

### 衍生 pilotfish-codex

能快速得到完整角色與 Hook，但會接收全域設定和既有執行環境假設。這次只借用
intent、risk、review 與 escalation 的語意。

### 第一版就寫調度程式

可以強制結構、逾時和成本限制，但目前原生執行環境已能執行派工，尚無跨
執行環境自動化需求支持這份維護成本。

## 影響與邊界

| 面向 | 影響 |
|------|------|
| 向下相容 | 新核心只透過精準指標按需載入；QDM Skill 改成薄 adapter，安全邊界不變 |
| 程式碼 | 不新增調度程式；只新增可重跑的契約測試 |
| 安全性 | 不新增權限；專案適配層只能收緊規則，不能放寬 |
| 效能與成本 | 第一版沒有常駐服務；模型成本由執行環境設定與最小派工形狀控制 |
| 維護 | 通用定義只保留一份，執行環境與專案只寫差異 |
| 正式環境 | 不安裝、不部署、不接流量，也不執行 DB 或服務 mutation |

## 後續可選工作

- 路由紀錄在非 QDM 專案寫到哪裡，由各適配層使用既有任務追蹤器或工作紀錄
  決定。
- 有第二個 runtime 時，新增對應 profile 並重跑同一組契約案例。
- 只有累積可重現的 Prompt／原生 sandbox 旁路證據後，才另案評估 Hook。

這些工作不阻擋目前的通用 Router、Codex profile 或 QDM adapter 使用。

## 參考資料

- [AI 工作流路由與專案覆寫指南](../../docs/dev-guide/workflow/WORKFLOW-ROUTING.md)
- [Baton](https://github.com/cablate/baton)
- [pilotfish](https://github.com/Nanako0129/pilotfish)
- [pilotfish-codex](https://github.com/miyago9267/pilotfish-codex)
- [orchestrate-sol-terra-luna](https://github.com/irons163/orchestrate-sol-terra-luna)
- [Open GSD Core](https://github.com/open-gsd/gsd-core)
- QDM 比較與適配來源：
  - `qdm-arch/docs/research/20260807-lightweight-agent-routing-framework-comparison.md`
  - `qdm-arch/docs/plans/codex/agent/2026080615-16-codex-sol-terra-agent-team-design.md`
  - `qdm-arch/.agents/skills/qdm-agent-team/SKILL.md`
