# v1/v2 Mem Sync Pull Push Parity Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 完整修復 `ai-dev mem` 與 `ai-dev sync` 的 `push/pull` parity，使 v2 在輸出、錯誤處理與業務邏輯都對齊 v1（P0-P2 全修）。

**Architecture:** 先以 TDD 建立 parity 回歸測試，優先修正 P0 的資料一致性與同步安全，再補 P1 的 v1 設定相容層，最後完成 P2 的 CLI 輸出細節與文件收斂。核心邏輯集中在 `src/core/mem-sync.ts`、`src/core/sync-engine.ts`，CLI 輸出集中在 `src/cli/mem/index.ts`、`src/cli/sync/index.ts`、`src/utils/i18n.ts`。

**Tech Stack:** TypeScript, Bun, Commander.js, inquirer, YAML, Bun test

---

## 執行前提（必做）

- 在專用 worktree 執行本計畫（避免污染當前分支）。
- 每個 Task 都採「先紅燈測試，再最小實作，再綠燈」。
- 每個 Task 結束立即 commit，不要累積過大變更。
- 參考技能：`@javascript-testing-patterns` `@bun-development` `@typescript-advanced-types`

---

### Task 1: P0-1 — `mem push` 改為四類資料增量推送

**Files:**
- Create: `tests/core/mem-sync-push-parity.test.ts`
- Modify: `src/core/mem-sync.ts`
- Test: `tests/core/mem-sync-push-parity.test.ts`

**Step 1: Write the failing test**

```ts
test("pushMemData pushes sessions/observations/summaries/prompts since lastPushEpoch", async () => {
  // 建立 sqlite 測試 DB: sdk_sessions/observations/session_summaries/user_prompts
  // lastPushEpoch = 100，僅 epoch > 100 的資料應被送出
  // mock /api/sync/push-preflight 與 /api/sync/push
  // 斷言 push payload 四類資料都有正確筆數
});
```

**Step 2: Run test to verify it fails**

Run: `bun test tests/core/mem-sync-push-parity.test.ts -t "pushMemData pushes sessions/observations/summaries/prompts since lastPushEpoch"`
Expected: FAIL（目前 payload 僅有 `observations`）

**Step 3: Write minimal implementation**

在 `src/core/mem-sync.ts` 增加查詢函式，依 `lastPushEpoch` 組裝四類 payload：

```ts
const sessions = querySince(dbPath, "sdk_sessions", "started_at_epoch", lastPushEpoch);
const observations = querySince(dbPath, "observations", "created_at_epoch", lastPushEpoch);
const summaries = querySince(dbPath, "session_summaries", "created_at_epoch", lastPushEpoch);
const prompts = querySince(dbPath, "user_prompts", "created_at_epoch", lastPushEpoch);
```

**Step 4: Run test to verify it passes**

Run: `bun test tests/core/mem-sync-push-parity.test.ts -t "pushMemData pushes sessions/observations/summaries/prompts since lastPushEpoch"`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/core/mem-sync-push-parity.test.ts src/core/mem-sync.ts
git commit -m "修正(mem): push 對齊 v1 四類資料增量推送"
```

---

### Task 2: P0-2 — `mem push` 未註冊行為與 `server_epoch` 水位對齊

**Files:**
- Modify: `tests/core/mem-sync-push-parity.test.ts`
- Modify: `src/core/mem-sync.ts`
- Test: `tests/core/mem-sync-push-parity.test.ts`

**Step 1: Write the failing test**

```ts
test("pushMemData throws when server config is missing", async () => {
  await expect(pushMemData({ configPath, dbPath })).rejects.toThrow("請先執行 ai-dev mem register");
});

test("pushMemData updates lastPushEpoch from server_epoch", async () => {
  // mock /api/sync/push 回傳 { server_epoch: 1234567890, stats: ... }
  // 斷言 save 後 config.lastPushEpoch === 1234567890
});
```

**Step 2: Run test to verify it fails**

Run: `bun test tests/core/mem-sync-push-parity.test.ts -t "missing"`
Expected: FAIL（目前未註冊不會拋錯）

Run: `bun test tests/core/mem-sync-push-parity.test.ts -t "server_epoch"`
Expected: FAIL（目前使用本機 `Date.now()`）

**Step 3: Write minimal implementation**

```ts
if (!config.serverUrl || !config.apiKey) {
  throw new Error("找不到 sync server 設定，請先執行 `ai-dev mem register`");
}
config.lastPushEpoch = payload.server_epoch ?? config.lastPushEpoch;
```

**Step 4: Run test to verify it passes**

Run: `bun test tests/core/mem-sync-push-parity.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/core/mem-sync-push-parity.test.ts src/core/mem-sync.ts
git commit -m "修正(mem): push 未註冊錯誤與 server_epoch 水位對齊"
```

---

### Task 3: P0-3 — `mem pull` 匯入路徑對齊（API 優先、SQLite fallback）

**Files:**
- Create: `tests/core/mem-sync-pull-parity.test.ts`
- Modify: `src/core/mem-sync.ts`
- Test: `tests/core/mem-sync-pull-parity.test.ts`

**Step 1: Write the failing test**

```ts
test("pullMemData imports sessions/observations/summaries/prompts via worker API then fallback sqlite", async () => {
  // case A: mock worker /api/import 可用，斷言四類 imported 統計
  // case B: worker 不可用，走 sqlite fallback，統計仍正確
});
```

**Step 2: Run test to verify it fails**

Run: `bun test tests/core/mem-sync-pull-parity.test.ts -t "imports sessions/observations/summaries/prompts"`
Expected: FAIL（目前僅 observations 進 DB，未走 API import/fallback）

**Step 3: Write minimal implementation**

在 `src/core/mem-sync.ts` 新增 `importPulledData()`：

```ts
// 1) 嘗試 POST http://localhost:37777/api/import
// 2) 失敗時 fallback 直接寫 SQLite
// 3) 回傳 { method: "api" | "sqlite", stats: ... }
```

**Step 4: Run test to verify it passes**

Run: `bun test tests/core/mem-sync-pull-parity.test.ts -t "imports sessions/observations/summaries/prompts"`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/core/mem-sync-pull-parity.test.ts src/core/mem-sync.ts
git commit -m "修正(mem): pull 匯入路徑對齊 v1 API+SQLite fallback"
```

---

### Task 4: P0-4 — `mem pull` 水位、去重追蹤與自動索引對齊

**Files:**
- Modify: `tests/core/mem-sync-pull-parity.test.ts`
- Modify: `src/core/mem-sync.ts`
- Test: `tests/core/mem-sync-pull-parity.test.ts`

**Step 1: Write the failing test**

```ts
test("pullMemData updates lastPullEpoch from server_epoch and tracks pulled hashes", async () => {
  // mock pull response with server_epoch + observations.sync_content_hash
  // 斷言 config.lastPullEpoch 使用 server_epoch
  // 斷言 pulled hash tracking 已更新
});

test("pullMemData triggers reindex+cleanup when imported observations > 0 and worker available", async () => {
  // mock worker health true
  // 斷言有呼叫 reindex + cleanup 路徑
});
```

**Step 2: Run test to verify it fails**

Run: `bun test tests/core/mem-sync-pull-parity.test.ts -t "lastPullEpoch"`
Expected: FAIL（目前使用本機時間）

Run: `bun test tests/core/mem-sync-pull-parity.test.ts -t "reindex+cleanup"`
Expected: FAIL（目前僅輸出提示）

**Step 3: Write minimal implementation**

```ts
config.lastPullEpoch = serverEpochFromResponse ?? config.lastPullEpoch;
await appendPulledHashes(hashes);
if (imported.observations > 0 && (await workerAvailable())) {
  const reindex = await reindexMemData({ dbPath, chromaDbPath });
  // reindexMemData 內部已做 cleanupDuplicates
}
```

**Step 4: Run test to verify it passes**

Run: `bun test tests/core/mem-sync-pull-parity.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/core/mem-sync-pull-parity.test.ts src/core/mem-sync.ts
git commit -m "修正(mem): pull 水位與索引後處理對齊 v1"
```

---

### Task 5: P0-5 — `sync push` 強制確認與「無變更即返回」對齊

**Files:**
- Create: `tests/core/sync-engine-push-parity.test.ts`
- Modify: `src/core/sync-engine.ts`
- Modify: `src/cli/sync/index.ts`
- Test: `tests/core/sync-engine-push-parity.test.ts`

**Step 1: Write the failing test**

```ts
test("push with force requires explicit confirmation", async () => {
  // 模擬 force=true 但使用者拒絕
  // 斷言不會執行 git push
});

test("push returns early when no changes and force=false", async () => {
  // 模擬 add/commit 無變更
  // 斷言回傳 no-op，不執行 git push
});
```

**Step 2: Run test to verify it fails**

Run: `bun test tests/core/sync-engine-push-parity.test.ts`
Expected: FAIL（目前 force 無確認、無變更仍會 push）

**Step 3: Write minimal implementation**

```ts
if (options.force) {
  const confirmed = await this.confirmForcePushFn();
  if (!confirmed) return { added: 0, updated: 0, deleted: 0, skipped: true };
}
if (!committed && !options.force) {
  return total;
}
```

**Step 4: Run test to verify it passes**

Run: `bun test tests/core/sync-engine-push-parity.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/core/sync-engine-push-parity.test.ts src/core/sync-engine.ts src/cli/sync/index.ts
git commit -m "修正(sync): push force 確認與無變更短路對齊 v1"
```

---

### Task 6: P0-6 — `sync pull` 安全策略加入 `push-then-pull`

**Files:**
- Create: `tests/core/sync-engine-pull-parity.test.ts`
- Modify: `src/core/sync-engine.ts`
- Modify: `src/cli/sync/index.ts`
- Test: `tests/core/sync-engine-pull-parity.test.ts`

**Step 1: Write the failing test**

```ts
test("pull conflict choice supports push-then-pull path", async () => {
  // 模擬本地衝突，選擇 push_then_pull
  // 斷言先呼叫 push() 再呼叫 git pull
});
```

**Step 2: Run test to verify it fails**

Run: `bun test tests/core/sync-engine-pull-parity.test.ts -t "push-then-pull"`
Expected: FAIL（目前選項無 push_then_pull）

**Step 3: Write minimal implementation**

```ts
type PullConflictChoice = "push_then_pull" | "force_pull" | "cancel";
if (choice === "push_then_pull") {
  await this.push({ force: false });
}
```

**Step 4: Run test to verify it passes**

Run: `bun test tests/core/sync-engine-pull-parity.test.ts -t "push-then-pull"`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/core/sync-engine-pull-parity.test.ts src/core/sync-engine.ts src/cli/sync/index.ts
git commit -m "修正(sync): pull 本機衝突策略加入先 push 再 pull"
```

---

### Task 7: P0-7 — `sync push/pull` git 失敗改為 fail-fast，`pull --rebase` 對齊

**Files:**
- Modify: `tests/core/sync-engine-push-parity.test.ts`
- Modify: `tests/core/sync-engine-pull-parity.test.ts`
- Modify: `src/core/sync-engine.ts`
- Test: `tests/core/sync-engine-push-parity.test.ts`
- Test: `tests/core/sync-engine-pull-parity.test.ts`

**Step 1: Write the failing test**

```ts
test("push throws when git pull --rebase fails", async () => {
  // mock git pull --rebase exitCode=1
  // expect engine.push() throws "git pull --rebase 失敗"
});

test("pull uses git pull --rebase and throws on failure", async () => {
  // assert command contains --rebase
  // assert non-zero exit code causes throw
});
```

**Step 2: Run test to verify it fails**

Run: `bun test tests/core/sync-engine-push-parity.test.ts tests/core/sync-engine-pull-parity.test.ts`
Expected: FAIL（目前多處 `check: false` 且未判斷 exitCode；pull 為 `--ff-only`）

**Step 3: Write minimal implementation**

```ts
const pull = await this.runCommandFn(["git", "-C", this.repoDir, "pull", "--rebase"], { check: false });
if (pull.exitCode !== 0) throw new Error("git pull --rebase 失敗");
```

同樣套用在 `git push`、`git commit`、`git lfs push` 失敗處理。

**Step 4: Run test to verify it passes**

Run: `bun test tests/core/sync-engine-push-parity.test.ts tests/core/sync-engine-pull-parity.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/core/sync-engine-push-parity.test.ts tests/core/sync-engine-pull-parity.test.ts src/core/sync-engine.ts
git commit -m "修正(sync): git 失敗改 fail-fast 並對齊 pull --rebase"
```

---

### Task 8: P1-1 — `mem` v1 設定檔相容（舊檔名 + snake_case）

**Files:**
- Create: `tests/core/mem-sync-config-compat.test.ts`
- Modify: `src/core/mem-sync.ts`
- Test: `tests/core/mem-sync-config-compat.test.ts`

**Step 1: Write the failing test**

```ts
test("loadMemSyncConfig reads legacy sync-server.yaml and maps snake_case keys", async () => {
  // 建立 legacy 檔：server_url/api_key/last_pull_epoch...
  // 斷言 load 後得到 serverUrl/apiKey/lastPullEpoch...
});
```

**Step 2: Run test to verify it fails**

Run: `bun test tests/core/mem-sync-config-compat.test.ts`
Expected: FAIL（目前僅讀 `mem-sync.yaml` 且不做 key 映射）

**Step 3: Write minimal implementation**

```ts
const legacyPath = join(paths.aiDevConfig, "sync-server.yaml");
// 優先 mem-sync.yaml，不存在時 fallback legacyPath
// 加入 snake_case -> camelCase 映射函式
```

**Step 4: Run test to verify it passes**

Run: `bun test tests/core/mem-sync-config-compat.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/core/mem-sync-config-compat.test.ts src/core/mem-sync.ts
git commit -m "修正(mem): 相容 v1 sync-server.yaml 與 snake_case 欄位"
```

---

### Task 9: P1-2 — `sync.yaml` v1 欄位相容（`repo_subdir`/`ignore_profile`/`last_sync`）

**Files:**
- Create: `tests/core/sync-engine-config-compat.test.ts`
- Modify: `src/core/sync-engine.ts`
- Test: `tests/core/sync-engine-config-compat.test.ts`

**Step 1: Write the failing test**

```ts
test("loadConfig maps legacy sync.yaml snake_case fields", async () => {
  // directories: [{ repo_subdir, ignore_profile, custom_ignore }]
  // 斷言載入後為 repoSubdir/ignoreProfile/customIgnore
});
```

**Step 2: Run test to verify it fails**

Run: `bun test tests/core/sync-engine-config-compat.test.ts`
Expected: FAIL（目前未做 legacy key 映射）

**Step 3: Write minimal implementation**

```ts
function normalizeLegacySyncConfig(raw: any): SyncConfig {
  // 將 last_sync -> lastSync, repo_subdir -> repoSubdir, ignore_profile -> ignoreProfile
}
```

**Step 4: Run test to verify it passes**

Run: `bun test tests/core/sync-engine-config-compat.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/core/sync-engine-config-compat.test.ts src/core/sync-engine.ts
git commit -m "修正(sync): 相容 v1 sync.yaml snake_case 欄位"
```

---

### Task 10: P2-1 — `mem` CLI 輸出對齊（method label、錯誤訊息、文案）

**Files:**
- Create: `tests/cli/mem-output-parity.test.ts`
- Modify: `src/cli/mem/index.ts`
- Modify: `src/utils/i18n.ts`
- Test: `tests/cli/mem-output-parity.test.ts`

**Step 1: Write the failing test**

```ts
test("mem pull prints method label API or SQLite dynamically", () => {
  // 透過 mock result.importMethod = "api" | "sqlite"
  // 斷言輸出為 "Pull 完成 (API|SQLite)"
});

test("mem push without register returns v1-aligned guidance", () => {
  // 斷言錯誤訊息包含「請先執行 ai-dev mem register」
});
```

**Step 2: Run test to verify it fails**

Run: `bun test tests/cli/mem-output-parity.test.ts`
Expected: FAIL（目前 pull 文案固定 SQLite、未註冊提示不完整）

**Step 3: Write minimal implementation**

```ts
console.log(t("mem.pull_done", { method: result.importMethod, ...counts }));
// i18n: "Pull 完成 ({method}) imported: ..."
```

並在 CLI action 包裝錯誤輸出（對齊 v1 register 提示）。

**Step 4: Run test to verify it passes**

Run: `bun test tests/cli/mem-output-parity.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/cli/mem-output-parity.test.ts src/cli/mem/index.ts src/utils/i18n.ts
git commit -m "修正(mem): pull/push CLI 輸出與錯誤提示對齊 v1"
```

---

### Task 11: P2-2 — `sync` CLI 輸出與互動文案對齊

**Files:**
- Create: `tests/cli/sync-output-parity.test.ts`
- Modify: `src/cli/sync/index.ts`
- Modify: `src/utils/i18n.ts`
- Test: `tests/cli/sync-output-parity.test.ts`

**Step 1: Write the failing test**

```ts
test("sync push complete output uses v1-aligned wording and summary format", () => {
  // 斷言包含 "sync push 完成" 與 "+X ~Y -Z"
});

test("sync pull conflict prompt contains push-then-pull option", () => {
  // 斷言選單文字含「先 push 再 pull（推薦）」選項
});
```

**Step 2: Run test to verify it fails**

Run: `bun test tests/cli/sync-output-parity.test.ts`
Expected: FAIL（目前文案與選項格式未對齊）

**Step 3: Write minimal implementation**

```ts
console.log(t("sync.push_done"));
console.log(t("sync.summary", { added, updated, deleted })); // +{added} ~{updated} -{deleted}
```

並補齊 pull 衝突提示 i18n。

**Step 4: Run test to verify it passes**

Run: `bun test tests/cli/sync-output-parity.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/cli/sync-output-parity.test.ts src/cli/sync/index.ts src/utils/i18n.ts
git commit -m "修正(sync): CLI 輸出與互動文案對齊 v1"
```

---

### Task 12: P2-3 — Parity 回歸測試組裝（整體防回退）

**Files:**
- Modify: `tests/core/mem-sync.test.ts`
- Modify: `tests/core/sync-engine.test.ts`
- Modify: `tests/cli/smoke.test.ts`
- Test: `tests/core/mem-sync.test.ts`
- Test: `tests/core/sync-engine.test.ts`
- Test: `tests/cli/smoke.test.ts`

**Step 1: Write the failing test**

新增/調整以下回歸斷言：

```ts
// mem: auto, push, pull 關鍵輸出/錯誤語意
// sync: push force、pull 衝突、git 失敗時 exitCode
// smoke: help 與選項對齊（含 push-then-pull 提示）
```

**Step 2: Run test to verify it fails**

Run: `bun test tests/core/mem-sync.test.ts tests/core/sync-engine.test.ts tests/cli/smoke.test.ts`
Expected: FAIL（舊斷言不涵蓋新 parity 行為）

**Step 3: Write minimal implementation**

補齊測試 fixture 與 mock（不新增多餘抽象，維持 DRY/YAGNI）。

**Step 4: Run test to verify it passes**

Run: `bun test tests/core/mem-sync.test.ts tests/core/sync-engine.test.ts tests/cli/smoke.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/core/mem-sync.test.ts tests/core/sync-engine.test.ts tests/cli/smoke.test.ts
git commit -m "測試(parity): 補齊 mem 與 sync pull/push 回歸測試"
```

---

### Task 13: 文件收斂 — 更新 parity 報告與修復紀錄

**Files:**
- Modify: `docs/reports/2026-02-27-v1-v2-mem-sync-pull-push-parity-analysis.md`
- Modify: `docs/v1-v2-parity-report.md`

**Step 1: 更新報告狀態**

將本次 P0-P2 的實作結果填入：
- 已修復項目（含 commit hash）
- 保留差異（若有）
- 驗證命令與結果

**Step 2: 補上驗證章節**

新增「如何重跑 parity 測試」區塊：

```bash
bun test tests/core/mem-sync-push-parity.test.ts
bun test tests/core/mem-sync-pull-parity.test.ts
bun test tests/core/sync-engine-push-parity.test.ts
bun test tests/core/sync-engine-pull-parity.test.ts
bun test tests/cli/mem-output-parity.test.ts
bun test tests/cli/sync-output-parity.test.ts
```

**Step 3: Commit**

```bash
git add docs/reports/2026-02-27-v1-v2-mem-sync-pull-push-parity-analysis.md docs/v1-v2-parity-report.md
git commit -m "文件(parity): 更新 mem/sync pull push 對齊修復結果"
```

---

## 完整驗證（最後一次）

依序執行：

```bash
bun test tests/core/mem-sync-push-parity.test.ts
bun test tests/core/mem-sync-pull-parity.test.ts
bun test tests/core/sync-engine-push-parity.test.ts
bun test tests/core/sync-engine-pull-parity.test.ts
bun test tests/core/mem-sync-config-compat.test.ts
bun test tests/core/sync-engine-config-compat.test.ts
bun test tests/cli/mem-output-parity.test.ts
bun test tests/cli/sync-output-parity.test.ts
bun test tests/core/mem-sync.test.ts tests/core/sync-engine.test.ts tests/cli/smoke.test.ts
bun run build
```

預期：
- 全部 PASS
- `bun run build` 成功
- `ai-dev mem`、`ai-dev sync` 的 `push/pull` 行為與 v1 對齊

---

## 交付標準（Done Definition）

- P0：`mem push/pull` 與 `sync push/pull` 核心業務邏輯對齊 v1（資料範圍、水位、安全策略、失敗處理）。
- P1：v1 legacy 設定可被 v2 正確讀取並映射。
- P2：CLI 輸出與 parity 測試完整覆蓋，文件已更新並可重現驗證。
