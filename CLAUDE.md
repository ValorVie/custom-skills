<!-- >>> ai-dev:ai-dev-project | ⚠️ 以下為 ai-dev 管理的專案規則，必須遵守 -->
---

# Language

預設情況下，所有回應皆使用**繁體中文**
1. 敘述句一律用自然中文。
2. 英文只保留在必要處：
   - 專有名詞
   - 產品名
   - 設定名
   - 檔名
   - 路徑
   - 程式碼
   - 少數該領域已固定存在的術語（如 DB mutation、rollout、rollback）
3. 禁止把英文普通詞直接嵌入中文句法中，例如：
   - prerequisite
   - required
   - exact probe
   - live evidence
   - override 到
   - fixed 成
4. 優先改寫成自然中文，例如：
   - prerequisite → 前置條件
   - required → 本輪要求
   - live evidence → 工具實測 / 現場實測
   - exact probe → 直接驗證 / 精確探測
   - override 到 → 改指向 / 覆寫為
5. 風格以工程維運文件為準：短句、明確、可執行，不要文案腔。

# Rules

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.


<!-- <<< ai-dev:ai-dev-project | 以上規則結束，確認已理解再開始任務 -->

# MP 工作入口層

mp-* skills 是本 repo 的工作入口層，負責把模糊需求壓成專案語言、分流工作項目、轉成 PRD 或 OpenSpec 前置素材。

何時使用：需求語意未對齊、工作堆積待分流、討論要轉成可追蹤項目、想 stress-test plan 而非直接動手。

何時不使用：要寫實作交給 `openspec-*`、`superpowers:executing-plans`、`superpowers:test-driven-development`；除錯交給 `superpowers:systematic-debugging`。

共同規則統一放在 `docs/agents/`：
- `docs/agents/issue-tracker.md` — canonical 工作出口
- `docs/agents/triage-states.md` — canonical 狀態與外部 mapping
- `docs/agents/domain.md` — context 模型與 lazy creation 規則
- `docs/agents/mp-workflow.md` — MP 入口層職責與邊界

