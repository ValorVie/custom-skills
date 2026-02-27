# Custom Repos Legacy Config Parity Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 讓 v2 完整相容 v1 的 `repos.yaml` 舊格式（`local_path`/`added_at`），避免 `ai-dev update` 與 `ai-dev update-custom-repo` 在舊資料上崩潰。

**Architecture:** 在 `loadCustomRepos()` 增加 v1→v2 相容正規化層，只在讀取時轉換欄位命名與 `~` 路徑，不改寫既有檔案格式。以 TDD 先補失敗測試（utils + CLI integration），再做最小實作，最後跑回歸測試確保 `update` 與 `update-custom-repo` 路徑不回退。

**Tech Stack:** Bun, TypeScript, YAML, Bun test

---

### Task 1: 建立舊格式相容失敗測試（utils 層）

**Files:**
- Create: `tests/utils/custom-repos-compat.test.ts`
- Test: `src/utils/custom-repos.ts`

**Step 1: Write the failing test**

```ts
import { describe, expect, test } from "bun:test";
import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import YAML from "yaml";

import { loadCustomRepos } from "../../src/utils/custom-repos";

describe("utils/custom-repos legacy compatibility", () => {
  test("loadCustomRepos maps snake_case keys and expands ~ path", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-custom-repos-compat-"));
    const configPath = join(root, "repos.yaml");
    const prevHome = process.env.HOME;

    try {
      await writeFile(
        configPath,
        YAML.stringify({
          repos: {
            legacy: {
              url: "https://example.com/legacy.git",
              branch: "main",
              local_path: "~/.config/legacy-repo/",
              added_at: "2026-01-01T00:00:00+00:00",
            },
          },
        }),
        "utf8",
      );

      process.env.HOME = root;
      const config = await loadCustomRepos(configPath);

      expect(config.repos.legacy.localPath).toBe(
        join(root, ".config", "legacy-repo"),
      );
      expect(config.repos.legacy.addedAt).toBe("2026-01-01T00:00:00+00:00");
    } finally {
      process.env.HOME = prevHome;
      await rm(root, { recursive: true, force: true });
    }
  });
});
```

**Step 2: Run test to verify it fails**

Run: `bun test tests/utils/custom-repos-compat.test.ts`
Expected: FAIL（目前 `loadCustomRepos()` 不處理 `local_path` / `added_at`）

**Step 3: Write minimal implementation**

先不要做完整重構，只讓測試暴露真實缺口（snake_case + `~` 展開）。

**Step 4: Run test to verify baseline remains failing for right reason**

Run: `bun test tests/utils/custom-repos-compat.test.ts`
Expected: FAIL（訊息集中於欄位缺失或路徑未展開）

**Step 5: Commit**

```bash
git add tests/utils/custom-repos-compat.test.ts
git commit -m "測試(custom-repos): 新增舊版 repos.yaml 相容失敗測試"
```

### Task 2: 實作 `loadCustomRepos()` 舊格式正規化

**Files:**
- Modify: `src/utils/custom-repos.ts`
- Test: `tests/utils/custom-repos-compat.test.ts`

**Step 1: Write the failing test (if not yet red)**

確認 Task 1 測試為紅燈，避免先改碼後補測試。

**Step 2: Run test to verify it fails**

Run: `bun test tests/utils/custom-repos-compat.test.ts`
Expected: FAIL

**Step 3: Write minimal implementation**

```ts
type RawCustomRepoEntry = {
  url?: unknown;
  branch?: unknown;
  localPath?: unknown;
  local_path?: unknown;
  addedAt?: unknown;
  added_at?: unknown;
};

function expandHomePath(pathValue: string): string {
  if (pathValue === "~") return homedir();
  if (pathValue.startsWith("~/")) return join(homedir(), pathValue.slice(2));
  return pathValue;
}

export async function loadCustomRepos(
  configPath = getCustomReposConfigPath(),
): Promise<CustomRepoConfig> {
  // parse YAML
  // map local_path -> localPath, added_at -> addedAt
  // expand ~ in localPath
  // keep backward compatibility for camelCase input
}
```

實作要求：
- 保留既有 camelCase 路徑不變。
- 僅在讀取時轉換，不改寫檔案內容。
- 回傳型別仍是 `CustomRepoConfig`（camelCase）。

**Step 4: Run test to verify it passes**

Run: `bun test tests/utils/custom-repos-compat.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add src/utils/custom-repos.ts tests/utils/custom-repos-compat.test.ts
git commit -m "修正(custom-repos): 相容 v1 repos.yaml snake_case 欄位"
```

### Task 3: 補 CLI 迴歸測試，防止 `update-custom-repo` 回退

**Files:**
- Modify: `tests/cli/phase3.integration.test.ts`
- Test: `src/cli/update-custom-repo.ts`, `src/core/custom-repo-updater.ts`

**Step 1: Write the failing test**

把既有 `update-custom-repo --json returns summary` 測試資料改成 v1 舊格式：

```yaml
repos:
  missing-repo:
    url: https://example.com/missing.git
    branch: main
    local_path: /tmp/.../missing-repo
    added_at: '2026-02-08T00:00:00.000Z'
```

**Step 2: Run test to verify it fails**

Run: `bun test tests/cli/phase3.integration.test.ts -t "update-custom-repo --json returns summary"`
Expected: FAIL（修復前會出現 `repo.localPath` undefined）

**Step 3: Write minimal implementation**

若 Task 2 已完成，這步通常不需再改產品碼；僅確認測試資料與期望值。

**Step 4: Run test to verify it passes**

Run: `bun test tests/cli/phase3.integration.test.ts -t "update-custom-repo --json returns summary"`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/cli/phase3.integration.test.ts
git commit -m "測試(update-custom-repo): 覆蓋 v1 repos.yaml 舊格式相容性"
```

### Task 4: 回歸 `update` 路徑並驗證無崩潰

**Files:**
- Modify (if needed): `tests/core/updater.test.ts`
- Test: `src/core/updater.ts`

**Step 1: Write the failing test**

新增一個 updater 測試，驗證 custom repos 路徑可正確執行到 `missing` 分支（不拋異常）：

```ts
test("runUpdate handles custom repos loaded from legacy config shape", async () => {
  // deps.loadCustomReposFn 可回傳已正規化結果，
  // 重點驗證 runUpdate 不因 custom repo 欄位崩潰
});
```

**Step 2: Run test to verify it fails (if needed)**

Run: `bun test tests/core/updater.test.ts -t "legacy config shape"`
Expected: FAIL（若仍有未覆蓋錯誤）或 PASS（若 Task 2 已完全修復）

**Step 3: Write minimal implementation**

僅在必要時補小修正，避免過度設計。

**Step 4: Run test to verify it passes**

Run: `bun test tests/core/updater.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/core/updater.test.ts src/core/updater.ts
git commit -m "測試(updater): 補 custom repos 舊格式相容回歸"
```

### Task 5: 全量驗證與文件對齊

**Files:**
- Modify: `docs/reports/2026-02-27-v1-v2-mem-sync-pull-push-parity-analysis.md`（補充本次額外修復）

**Step 1: Run focused regression suite**

Run:

```bash
bun test \
  tests/utils/custom-repos-compat.test.ts \
  tests/core/custom-repo-updater.test.ts \
  tests/core/updater.test.ts \
  tests/cli/phase3.integration.test.ts
```

Expected: PASS

**Step 2: Run CLI smoke/format regression**

Run:

```bash
bun test tests/cli/smoke.test.ts tests/cli/install-update-format.test.ts
```

Expected: PASS

**Step 3: Manual parity sanity check (legacy file)**

Run (manual):
1. 建立含 `local_path`/`added_at` 的 `~/.config/ai-dev/repos.yaml`
2. 執行 `ai-dev update-custom-repo --json`
3. 執行 `ai-dev update --skip-npm --skip-bun --skip-plugins --json`

Expected: 不拋 `TypeError`，輸出為正常 JSON 結果。

**Step 4: Update report note**

在報告新增「custom repos legacy config compatibility」修復記錄（問題、修復點、測試證據）。

**Step 5: Final commit**

```bash
git add src/utils/custom-repos.ts tests docs/reports/2026-02-27-v1-v2-mem-sync-pull-push-parity-analysis.md
git commit -m "修正(parity): 補齊 custom repos 舊設定相容並完成回歸驗證"
```
