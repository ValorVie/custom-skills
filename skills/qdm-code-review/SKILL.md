---
name: qdm-code-review
description: Use when code changes are ready for PR submission and need a final quality gate. Runs dual-perspective review (diff-only vs full-context) to catch issues a CI-only reviewer would miss or misunderstand, then generates PR title and body with documented review decisions.
---

# QDM Code Review

## Overview

PR 提交前的最後一道關卡。派出兩個平行 agent 審查同一份變更：

- **change-only**：模擬 GitHub Action 的侷限視角（只看 diff）
- **full-think**：帶入完整專案脈絡（讀取原始碼、慣例、架構）

兩者使用同一套 7 維度評分系統。分歧由主 LLM 仲裁，決策理由寫入 PR 內文。

## When to Use

- 程式碼變更已完成，準備發 PR
- 想在本地預覽 GitHub Action Claude 會給出什麼評價
- 變更涉及專案慣例或刻意沿用的舊模式，擔心被 CI 審查誤判

## When NOT to Use

- 還在開發中、程式碼不穩定
- 只是 typo 或單行修正（直接發 PR）
- 想要自動修正問題（用 `/simplify` 替代）

## Place in Workflow

```
implement → simplify（可選清理） → qdm-code-review（最後關卡） → PR
```

---

## Workflow

### Phase 1: 識別變更

判斷 diff 來源，定義 `$DIFF_REF`（diff 的比較參照）和 `$DIFF_TEXT`：

```
IF 使用者指定 --base <ref>:
    DIFF_REF = <ref>...HEAD
ELIF 當前分支非主分支，且 origin/main（或 origin/master）存在:
    DIFF_REF = $(git merge-base HEAD origin/$MAIN_BRANCH)..HEAD
ELIF git diff --cached 有內容:
    DIFF_REF = --cached（僅審查已暫存的變更）
ELSE:
    DIFF_REF =（無參照，使用 git diff 審查工作目錄變更）
```

取得 diff 文字和變更檔案清單：

```bash
DIFF_TEXT=$(git diff $DIFF_REF)
ADDED_FILES=$(git diff --name-only --diff-filter=A $DIFF_REF)
MODIFIED_FILES=$(git diff --name-only --diff-filter=M $DIFF_REF)
DELETED_FILES=$(git diff --name-only --diff-filter=D $DIFF_REF)
```

若無變更 → 告知使用者並結束。

### Phase 2: 準備 agent 輸入

1. 讀取 `references/scoring-system.md` → 暫存為 `SCORING_CONTENT`
2. 讀取 `references/change-only-reviewer.md`，將 `{SCORING_SYSTEM}` 替換為 `SCORING_CONTENT`，`{DIFF_CONTENT}` 替換為 `DIFF_TEXT` → 暫存為 `PROMPT_CHANGE_ONLY`
3. 讀取 `references/full-think-reviewer.md`，將 `{SCORING_SYSTEM}` 替換為 `SCORING_CONTENT`，`{DIFF_CONTENT}` 替換為 `DIFF_TEXT`，`{CHANGED_FILES}` 替換為檔案清單 → 暫存為 `PROMPT_FULL_THINK`

### Phase 3: 平行派出兩個 agent

在**同一輪**中發出兩個 Agent 呼叫：

**change-only agent**：
- 類型：general-purpose
- prompt：`PROMPT_CHANGE_ONLY`
- 此 agent 的 prompt 明確禁止使用任何工具，只根據 prompt 中的 diff 內容審查

**full-think agent**：
- 類型：general-purpose
- prompt：`PROMPT_FULL_THINK`
- 此 agent 可自由使用 Read、Grep、Glob 等工具探索專案
- 若專案有 atlas MCP 工具，可用來查詢依賴和影響範圍

兩者都是唯讀審查，不編輯任何檔案。

### Phase 4: 仲裁

收到雙方結果後，逐項比較：

**4.1 解析兩份 SCORES 行**

提取每個維度的分數，計算差距。

**4.2 逐維度仲裁**

| 差距 | 分類 | 處理 |
|------|------|------|
| 0 | 一致 | 直接採用該分數 |
| 1 | 輕微分歧 | 採用 full-think 分數，備註差異原因 |
| ≥2 | 顯著分歧 | 讀取雙方 RATIONALE，做出仲裁決定並記錄理由 |

**4.3 比較 findings 並形成最終清單**

逐一比對雙方的 BLOCKING 和 SUGGESTIONS：

- 兩者都有同一項 BLOCKING → 確認納入最終 BLOCKING 清單
- change-only 有 BLOCKING 但 full-think 沒有 → 主 LLM 判定：若為脈絡不足的誤判則降級為 SUGGESTION 或移除；若確為問題則保留
- full-think 有 BLOCKING 但 change-only 沒有 → 主 LLM 判定：若為深層問題則保留；若過度嚴格則降級
- SUGGESTIONS 和 HIGHLIGHTS 取雙方聯集，去重

最終產出三份清單：`FINAL_BLOCKING`、`FINAL_SUGGESTIONS`、`FINAL_HIGHLIGHTS`。

**4.4 整合 CONTEXT_NOTES**

- 若 full-think 的 CONTEXT_NOTES 有內容 → 全部納入 PR 內文的 Design Notes 段落
- 若 CONTEXT_NOTES 為「（無）」→ PR 內文中省略 Design Notes 段落

**4.5 計算最終評分**

使用仲裁後的各維度分數：

```
最終分數 = (security×0.20) + (functionality×0.20) + (quality×0.15)
         + (architecture×0.15) + (testing×0.15) + (error_handling×0.10)
         + (documentation×0.05)
```

### Phase 5: 生成 PR 內容

**PR 標題**：分析 `$DIFF_REF` 範圍內的 commit 歷史，遵循 conventional commits 格式。

```bash
git log --pretty=format:"%s" $DIFF_REF
```

分析主要變更類型，生成 `<type>(<scope>): <概括性描述>` 格式標題。若 `$DIFF_REF` 不含 commit 範圍（如 `--cached`），則從 diff 內容分析生成。

**PR 內文**：使用以下模板，各段落按條件填充。

```markdown
## Summary

[基於 commit messages 和 diff 分析的 1-3 句變更摘要]

## Pre-Review Summary

**綜合評分**: X.X / 5.0 | **建議**: [合併建議文字]

| 維度 | 分數 | 權重 | 加權分 |
|------|------|------|--------|
| 🔒 安全性 | X/5 | 20% | X.XX |
| ✅ 功能正確性 | X/5 | 20% | X.XX |
| 📝 程式碼品質 | X/5 | 15% | X.XX |
| 🏗️ 架構設計 | X/5 | 15% | X.XX |
| 🧪 測試覆蓋 | X/5 | 15% | X.XX |
| ⚠️ 錯誤處理 | X/5 | 10% | X.XX |
| 📚 文件完整性 | X/5 | 5% | X.XX |

### Design Notes

<!-- full-think 主動辨識的專案脈絡說明 -->
<!-- 供審查者（人類或 CI）理解專案決策 -->
- **[模式/寫法]**：[為什麼這樣寫] — 參考 [具體檔案/慣例]

### Review Decisions

<!-- 僅在有顯著分歧（差距 ≥2）時出現此段落；無分歧時整段省略 -->
以下項目在雙視角審查中出現分歧，經主審仲裁後決定：

| 維度 | 片段視角（分數） | 全局視角（分數） | 最終（分數） | 仲裁理由 |
|------|----------------|----------------|-------------|---------|
| 架構設計 | 2/5 | 4/5 | 4/5 | 沿用專案既有 MVC 分層，符合團隊慣例 |

## Changes

[從 commit messages 提取的主要變更項目]

- [變更項目 1]
- [變更項目 2]

## Files Changed

**Added:** [清單]
**Modified:** [清單]
**Deleted:** [清單]
```

### Phase 6: 輸出結果

**終端顯示**（給使用者看）：

1. 雙視角評分對比表（change-only vs full-think vs 最終）
2. 分歧項目的仲裁理由
3. 合併後的 BLOCKING / SUGGESTIONS / HIGHLIGHTS
4. PR 標題和內文預覽
5. 最終建議：

| 最終分數 | 建議 |
|----------|------|
| 4.5 - 5.0 | ✅ 強烈建議合併 |
| 4.0 - 4.4 | ✅ 建議合併 |
| 3.5 - 3.9 | ⚠️ 有條件合併，建議處理標記問題後再發 |
| 3.0 - 3.4 | ⚠️ 建議修改後合併 |
| 2.0 - 2.9 | ❌ 不建議合併，需修正後重新審查 |
| 1.0 - 1.9 | ❌ 強烈不建議合併 |

**不自動發 PR**。使用者看完結果後自行決定。

---

## Quick Reference

| 面向 | change-only | full-think |
|------|------------|-----------|
| 視角 | 僅 diff 片段 | 完整專案脈絡 |
| 工具 | 禁止 | Read/Grep/Glob（若有 atlas 亦可使用） |
| 模擬對象 | GitHub Action Claude | 熟悉專案的資深開發者 |
| 獨特產出 | — | CONTEXT_NOTES |
| 評分系統 | 相同 7 維度 | 相同 7 維度 |

## Common Mistakes

- 讓 agent 編輯檔案（兩者都是唯讀，修正交給使用者或 `/simplify`）
- 忽略 CONTEXT_NOTES（這些是預防 CI 誤判的關鍵資訊）
- 分歧時無條件採信 full-think（它有更多脈絡但不代表永遠正確，主 LLM 必須獨立判斷）
- 對小型 diff 也走完整流程（1-2 行的 typo 修正不需要這個 skill）
