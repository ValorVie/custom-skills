# Superpowers 技能系統介紹

> Superpowers 5.0 是一套**強制執行**的 AI 軟體開發紀律框架，由 14 個可組合技能構成。
>
> 核心理念：**「鐵律非建議」**——每個技能都有無例外的規則。

---

## 技能總覽

| 技能 | 類型 | 觸發方式 | 核心職責 |
|------|------|---------|---------|
| using-superpowers | 入口 | 自動（對話開始） | 技能路由、優先順序判斷 |
| brainstorming | 設計 | 自動（創意工作前） | 蘇格拉底式需求釐清 |
| writing-plans | 規劃 | 自動（brainstorming 後） | 細粒度任務分解 |
| using-git-worktrees | 環境 | 自動（實作前） | 隔離工作區建立 |
| subagent-driven-development | 執行 | 自動（有 subagent 能力時） | 子代理逐任務執行 + 雙重審查 |
| executing-plans | 執行 | 備選（無 subagent 時） | 順序執行計畫任務 |
| test-driven-development | 紀律 | 強制（任何程式碼變更） | RED-GREEN-REFACTOR 循環 |
| systematic-debugging | 紀律 | 強制（遇到 bug 時） | 四階段根本原因調查 |
| verification-before-completion | 紀律 | 強制（聲稱完成前） | 新鮮驗證證據 |
| finishing-a-development-branch | 收尾 | 自動（所有任務完成後） | 測試→選項→清理 |
| dispatching-parallel-agents | 優化 | 手動（多獨立問題時） | 平行子代理分派 |
| requesting-code-review | 品質 | 強制（SDD 中）/ 手動 | 派遣審查子代理 |
| receiving-code-review | 品質 | 手動（收到反饋時） | 技術評估反饋 |
| writing-skills | 元技能 | 手動 | 用 TDD 方法撰寫新技能 |

---

## 完整調用鏈

### 主流程：從需求到交付

```
使用者提出需求
  │
  ▼
[自動] using-superpowers ─── 判斷該調用哪些技能
  │
  ▼
[自動] brainstorming ─── 探索上下文→逐一提問→提議方案→編寫設計文件
  │                       產出：docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md
  │                       包含：規格審查迴圈（審查者子代理驗證完整性）
  ▼
[自動] writing-plans ─── 作用域檢查→檔案結構→任務分解（2-5 分鐘/任務）
  │                      產出：docs/superpowers/plans/YYYY-MM-DD-<feature>.md
  │                      包含：計畫審查迴圈（審查者子代理驗證對齊）
  ▼
[自動] using-git-worktrees ─── 偵測/建立隔離工作區→專案設定→基線測試
  │
  ▼
  ┌─ 有 subagent 能力？（Claude Code、Codex）
  │   ▼
  │  [自動] subagent-driven-development (SDD)
  │   │  對每個任務：
  │   │  ├─ 派遣實作者子代理 ──────────────────┐
  │   │  │   └─ [強制] test-driven-development  │
  │   │  │       RED → GREEN → REFACTOR         │
  │   │  │   └─ [強制] systematic-debugging     │ 遇到 bug 時
  │   │  ├─ 派遣規格合規審查者 ←────────────────┘
  │   │  │   └─ 不合規？→ 實作者修復 → 重新審查
  │   │  └─ 派遣代碼品質審查者
  │   │       └─ 有問題？→ 實作者修復 → 重新審查
  │   ▼
  └─ 無 subagent？
      ▼
     [備選] executing-plans ─── 逐個任務順序執行
         └─ 同樣強制 TDD + debugging + verification
  │
  ▼
[強制] verification-before-completion ─── 執行驗證命令→讀取完整輸出→確認聲明
  │
  ▼
[自動] finishing-a-development-branch
       ├─ 1. 合併回基礎分支（本地）
       ├─ 2. 推送並建立 PR
       ├─ 3. 保持原樣
       └─ 4. 放棄
```

### 輔助流程：Bug 修復

```
使用者報告 bug 或測試失敗
  │
  ▼
[強制] systematic-debugging ─── 四階段調查（不猜測）
  │
  ▼
[強制] test-driven-development ─── 先寫失敗測試重現 bug → 修復 → 通過
  │
  ▼
[強制] verification-before-completion ─── 新鮮驗證
```

### 輔助流程：多個獨立問題

```
多個問題同時爆發（例如 3+ 個測試檔案各自失敗）
  │
  ▼
[手動] dispatching-parallel-agents
  ├─ Agent A：修復 auth.test.ts
  ├─ Agent B：修復 payment.test.ts
  └─ Agent C：修復 notification.test.ts
  │
  ▼
主代理整合結果 → 完整測試驗證
```

---

## 核心技能詳解

### Brainstorming：設計先行

**鐵律：沒有批准的設計，就沒有程式碼。**

流程 7 步：
1. **探索專案上下文**（檔案、文件、最近提交）
2. **提供視覺伴侶**（如有視覺內容）
3. **逐一提問澄清**（每次一個問題，多選題優於開放題）
4. **提議 2-3 種方案**（各有權衡，含推薦方案）
5. **分段呈現設計**（每段 200-300 字）
6. **編寫設計文件** → 規格審查迴圈
7. **過渡到 writing-plans**

### Writing Plans：細粒度任務分解

**鐵律：假設工程師對專案一無所知，提供一切所需。**

每個任務必須是 2-5 分鐘的具體動作：
- 確切的檔案路徑
- 完整的程式碼（非「新增驗證」的模糊指示）
- 驗證命令與預期輸出

### Test-Driven Development：紅-綠-重構

**鐵律：沒有失敗的測試，就沒有生產程式碼。**

```
┌─────────┐     ┌─────────┐     ┌─────────┐
│   RED   │────→│  GREEN  │────→│REFACTOR │
│寫失敗測試│     │最小實作  │     │清理重構  │
└─────────┘     └─────────┘     └────┬────┘
     ▲                                │
     └────────────────────────────────┘
               下一個行為
```

| 階段 | 做什麼 | 不做什麼 |
|------|--------|---------|
| RED | 寫一個測試、描述一個行為、確認失敗 | 同時寫多個測試、測試實作細節 |
| GREEN | 最小程式碼讓測試通過 | 加額外功能、預先優化 |
| REFACTOR | 移除重複、改善命名 | 加新行為（那是下一個 RED） |

### Systematic Debugging：四階段根因調查

**鐵律：沒有根本原因調查，就沒有修復。症狀修復是失敗。**

```
階段 1：根本原因調查
  ├─ 仔細讀錯誤訊息（含警告）
  ├─ 一致性再現
  ├─ 檢查最近變更（git diff）
  └─ 追蹤資料流（向後追到不良值來源）

階段 2：模式分析
  ├─ 找到正常運作的範例
  ├─ 與參考實作逐行比較
  └─ 識別關鍵差異

階段 3：假設與測試
  ├─ 形成單一假設：「我認為 X 是根因，因為 Y」
  ├─ 最小變更測試（一次一個變數）
  └─ 驗證結果

階段 4：實作
  ├─ 建立失敗測試案例
  ├─ 實作單一修復（只針對根因）
  └─ 若 ≥3 次嘗試失敗 → 停下來質疑架構
```

**紅旗（立即停止）：**
- 「先改 X 看看是否有效」——猜測不是除錯
- 「一次改多處再跑測試」——無法判斷哪個有效
- 「不完全理解但可能行」——這是最危險的修復

### Verification Before Completion：新鮮證據

**鐵律：沒有新鮮驗證證據，就沒有完成聲明。**

閘門函數：
```
1. 識別：什麼命令能證明此聲明？
2. 執行：完整執行（不是引用之前的結果）
3. 讀取：完整輸出 + exit code
4. 驗證：輸出確認聲明嗎？
   ├─ 否 → 陳述實際狀態 + 證據
   └─ 是 → 陳述聲明 + 證據
```

| 聲明 | 需要的證據 | 不夠的證據 |
|------|----------|----------|
| 「測試通過」 | 測試命令輸出 0 failures | 之前的執行、「應該通過」 |
| 「構建成功」 | build 命令 exit 0 | linter 通過不代表構建通過 |
| 「Bug 修復了」 | 原始症狀測試通過 | 「程式碼改了應該沒問題」 |

### Subagent-Driven Development (SDD)

**核心：每個任務新鮮子代理 + 雙重審查 = 高品質快速迭代**

```
對每個計畫任務：

實作者子代理 ──→ 狀態回報
  │                ├─ DONE → 進入審查
  │                ├─ DONE_WITH_CONCERNS → 先處理疑慮
  │                ├─ NEEDS_CONTEXT → 提供資訊後重新派遣
  │                └─ BLOCKED → 評估並處理
  ▼
規格合規審查者 ──→ 合規？
  │                ├─ 是 → 繼續
  │                └─ 否 → 實作者修復 → 重新審查
  ▼
代碼品質審查者 ──→ 通過？
                   ├─ 是 → 任務完成 → 下一個
                   └─ 否 → 實作者修復 → 重新審查
```

**模型選擇策略：**

| 任務類型 | 建議模型 | 範例 |
|---------|---------|------|
| 機械實作 | 快速模型（haiku） | 獨立函數、清晰規格、1-2 檔案 |
| 整合任務 | 標準模型（sonnet） | 多檔案協調、模式匹配 |
| 架構/審查 | 最強模型（opus） | 設計決策、品質審查 |

### Finishing a Development Branch

完成所有任務後，強制呈現 4 個選項：

1. **合併回基礎分支**（本地 merge + 刪除 feature branch + 清理 worktree）
2. **推送並建立 PR**（push + gh pr create + 保留 worktree）
3. **保持原樣**（保留 branch 和 worktree）
4. **放棄**（需確認輸入 `discard`，刪除並清理）

### Dispatching Parallel Agents

**使用時機：** 2+ 個獨立問題，修一個不影響其他。

```
何時用：
  ├─ 3+ 測試檔案各自失敗，根因不同 ✅
  ├─ 多個獨立子系統各自壞了 ✅
  └─ 每個問題不需要其他問題的上下文 ✅

何時不用：
  ├─ 失敗互相關聯（修一個可能修其他）❌
  ├─ 需要理解完整系統狀態 ❌
  └─ 代理人會互相修改同一檔案 ❌
```

---

## 常見理由駁斥

| 你心裡想的 | 現實 |
|-----------|------|
| 「太簡單了不用測試」 | 簡單程式碼也會壞。測試花 30 秒。 |
| 「我會之後補測試」 | 之後的測試立刻通過，證明不了什麼。 |
| 「已經手動測試過了」 | 臨時測試無記錄、無法重新執行。 |
| 「先寫程式碼當參考」 | 刪掉。TDD 的重點是測試驅動設計。 |
| 「這只是個簡單問題」 | 問題也是任務。檢查技能。 |
| 「讓我先探索一下」 | 技能告訴你如何探索。先檢查技能。 |
| 「再試一次修復」（已試 2+ 次） | 停下來質疑架構，別繼續猜。 |

---

## 技能觸發快速參考

| 情境 | 觸發的技能 | 觸發方式 |
|------|----------|---------|
| 「讓我們建立 X」 | brainstorming | 自動 |
| 規格已批准 | writing-plans | 自動 |
| 有計畫要執行 | using-git-worktrees + SDD | 自動 |
| 實作功能或修復 | test-driven-development | 強制 |
| 遇到 bug 或測試失敗 | systematic-debugging | 強制 |
| 聲稱完成前 | verification-before-completion | 強制 |
| 所有任務完成 | finishing-a-development-branch | 自動 |
| 多個獨立問題同時出現 | dispatching-parallel-agents | 手動 |
| 收到 code review 反饋 | receiving-code-review | 手動 |
| 建立新技能 | writing-skills | 手動 |

---

## 參考資源

- [Superpowers GitHub](https://github.com/obra/superpowers) — 原始碼與文件（v5.0）
- [高見龍的 Superpowers 心得](https://kaochenlong.com/ai-superpowers-skills) — 實戰經驗分享
- [TOOL-DECISION-GUIDE.md](TOOL-DECISION-GUIDE.md) — 本專案工具選擇決策指南
