# V2 OpenCode Plugin Legacy Path Fix Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 補齊 v2 `ai-dev clone` 的 OpenCode plugin 路徑遷移與分發行為，恢復 v1 既有的 legacy 相容提示與 `plugins/` 主路徑策略。

**Architecture:** 在分發核心 `skill-distributor` 增加 OpenCode 專屬前置步驟：偵測 `plugin/` legacy 路徑並在必要時遷移到 `plugins/`，同時補上 `plugins/ecc-hooks-opencode/` 到目標 `opencode/plugins/` 的實際拷貝。維持現有 manifest/conflict 模型不擴張到 plugins，以最小改動達成 parity。CLI 僅調整輸出解析，讓 `plugins → OpenCode` 顯示格式一致。

**Tech Stack:** TypeScript、Bun test、Commander CLI、Node fs/promises

---

### Task 1: 建立失敗測試（OpenCode plugin 分發 + 並存提示）

**Files:**
- Modify: `tests/cli/clone.integration.test.ts`
- Test: `tests/cli/clone.integration.test.ts`

**Step 1: Write the failing test**

```ts
test("clone prints coexist warning and copies opencode plugins", async () => {
  // 建立 source plugins/ecc-hooks-opencode/plugin.ts
  // 建立 target legacy + modern 目錄，模擬並存
  // 執行 runClone([])
  // 斷言輸出包含「偵測到 OpenCode 新舊 plugin 路徑並存」
  // 斷言 modern plugins 目錄存在來源檔案
});
```

**Step 2: Run test to verify it fails**

Run: `bun test tests/cli/clone.integration.test.ts -t "clone prints coexist warning and copies opencode plugins"`
Expected: FAIL（目前 v2 尚未分發 opencode plugin，也不會印並存提示）

**Step 3: Commit (test only)**

```bash
git add tests/cli/clone.integration.test.ts
git commit -m "測試(clone): 新增 opencode plugin 並存遷移行為測試"
```

### Task 2: 實作遷移與分發核心邏輯

**Files:**
- Modify: `src/core/skill-distributor.ts`

**Step 1: Write minimal implementation for migration helper**

```ts
async function migrateOpencodePluginDirIfNeeded(...): Promise<void> {
  // legacy: <opencode>/plugin
  // modern: <opencode>/plugins
  // 若 only legacy: move 到 modern 並輸出「已遷移」
  // 若兩者並存: 輸出「將以 plugins 為主並保留 legacy 相容」
}
```

**Step 2: Add plugin copy step for opencode target**

```ts
// source: <sourceRoot>/plugins/ecc-hooks-opencode
// destination: COPY_TARGETS.opencode.plugins
// 使用 cp(..., { recursive: true, force: true })
// 進度輸出：plugins → OpenCode、source → destination
// 追加 result.distributed 項目 type="plugins"
```

**Step 3: Keep behavior bounded (DRY/YAGNI)**

```ts
// 不改 manifest schema（skills/commands/agents/workflows）
// plugins 不走 conflict/orphan 管理，只補齊 v1 parity 必要行為
```

**Step 4: Commit**

```bash
git add src/core/skill-distributor.ts
git commit -m "修正(clone): 補上 opencode plugin legacy 遷移與分發"
```

### Task 3: 補齊 CLI 輸出解析與型別相容

**Files:**
- Modify: `src/cli/clone.ts`

**Step 1: Allow plugin header formatting**

```ts
const headerMatch = msg.match(/^(skills|commands|agents|workflows|plugins) → (.+)$/);
```

**Step 2: Verify output unchanged for existing resource types**

Run: `bun test tests/cli/clone.integration.test.ts -t "clone non-json prints updated item details"`
Expected: PASS（原既有輸出不回歸）

**Step 3: Commit**

```bash
git add src/cli/clone.ts
git commit -m "樣式(clone): 支援 plugins 進度標頭輸出格式"
```

### Task 4: 驗證全流程

**Files:**
- Test: `tests/cli/clone.integration.test.ts`
- Test: `tests/core/skill-distributor.test.ts`

**Step 1: Run targeted test suite**

Run: `bun test tests/cli/clone.integration.test.ts tests/core/skill-distributor.test.ts`
Expected: PASS

**Step 2: Run optional broader regression check**

Run: `bun test`
Expected: PASS（若耗時過長，可先回報 targeted pass 並說明未跑全量）

**Step 3: Final commit**

```bash
git add src/core/skill-distributor.ts src/cli/clone.ts tests/cli/clone.integration.test.ts
git commit -m "修正(opencode): 恢復 clone plugin legacy 路徑相容與分發"
```
