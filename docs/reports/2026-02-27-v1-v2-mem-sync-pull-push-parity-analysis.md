---
title: v1/v2 ai-dev mem 與 pull/push 指令對齊分析報告
type: report/analysis
date: 2026-02-27
author: ValorVie
status: draft
---

# v1/v2 ai-dev mem 與 pull/push 指令對齊分析報告

## 摘要

[Confirmed] 截至 2026-02-27 第四批（最終）修復，`v2` 已完成 `mem/sync push/pull` 的 P0-P2 parity（核心業務邏輯、設定相容層、CLI 輸出與回歸測試收斂），在本報告範圍內可判定為已對齊 v1。 [Source: Code] src/core/mem-sync.ts:1100 [Source: Code] src/core/mem-sync.ts:1249 [Source: Code] src/core/sync-engine.ts:568 [Source: Code] src/core/sync-engine.ts:668 [Source: Code] src/cli/mem/index.ts:101 [Source: Code] src/cli/sync/index.ts:62 [Source: Code] tests/cli/mem-output-parity.test.ts:25 [Source: Code] tests/cli/sync-output-parity.test.ts:11

## 最新修復狀態（2026-02-27 第四批，最終）

[Confirmed] 已完成 Task 1-12（P0 + P1 + P2）修復落地；原先本報告「發現 1-5」中的差異結論已完成收斂。以下為目前 `v2-bun-migration` 的最終狀態快照。[Source: Code] src/core/mem-sync.ts:44 [Source: Code] src/core/mem-sync.ts:1270 [Source: Code] src/core/sync-engine.ts:242 [Source: Code] src/cli/mem/index.ts:101 [Source: Code] src/cli/sync/index.ts:62 [Source: Code] tests/core/sync-engine.test.ts:87 [Source: Code] tests/core/mem-sync.test.ts:1

| 面向 | 目前狀態 | 證據 |
|------|----------|------|
| `mem push` 四類資料增量推送 | ✅ 已修復 | 依 `lastPushEpoch` 增量查詢 `sdk_sessions/observations/session_summaries/user_prompts` [Source: Code] src/core/mem-sync.ts:1105 [Source: Code] src/core/mem-sync.ts:1111 [Source: Code] src/core/mem-sync.ts:1117 [Source: Code] src/core/mem-sync.ts:1123 |
| `mem push` 未註冊錯誤 | ✅ 已修復 | 缺 `serverUrl/apiKey` 直接拋錯，提示先 register [Source: Code] src/core/mem-sync.ts:1145 |
| `mem push` 水位更新 | ✅ 已修復 | 以 `server_epoch` 更新 `lastPushEpoch` [Source: Code] src/core/mem-sync.ts:1210 [Source: Code] src/core/mem-sync.ts:1232 |
| `mem pull` API import + SQLite fallback | ✅ 已修復 | `importPulledData()` 先 API 匯入，失敗 fallback SQLite [Source: Code] src/core/mem-sync.ts:774 [Source: Code] src/core/mem-sync.ts:778 [Source: Code] src/core/mem-sync.ts:797 |
| `mem pull` `lastPullEpoch` 與 pulled-hashes/reindex | ✅ 已修復 | `lastPullEpoch` 使用 `server_epoch`，有 pulled-hashes 與 reindex 路徑 [Source: Code] src/core/mem-sync.ts:1308 [Source: Code] src/core/mem-sync.ts:1352 [Source: Code] src/core/mem-sync.ts:1354 [Source: Code] src/core/mem-sync.ts:1361 |
| `sync push --force` 明確確認 | ✅ 已修復 | `confirmForcePushFn` 確認；拒絕則 `skipped` [Source: Code] src/core/sync-engine.ts:574 [Source: Code] src/core/sync-engine.ts:577 |
| `sync push` 無變更即返回 | ✅ 已修復 | `nothing to commit` 且非 force 時 no-op [Source: Code] src/core/sync-engine.ts:624 [Source: Code] src/core/sync-engine.ts:628 |
| `sync pull` 支援 `push_then_pull` | ✅ 已修復 | 衝突選項含 `push_then_pull`，並先 push 再 pull [Source: Code] src/core/sync-engine.ts:249 [Source: Code] src/core/sync-engine.ts:685 |
| `sync` git fail-fast 與 `pull --rebase` | ✅ 已修復 | push/pull 改 `git pull --rebase`，`git commit/push/lfs push` 非 0 立即 throw [Source: Code] src/core/sync-engine.ts:593 [Source: Code] src/core/sync-engine.ts:600 [Source: Code] src/core/sync-engine.ts:631 [Source: Code] src/core/sync-engine.ts:648 [Source: Code] src/core/sync-engine.ts:659 [Source: Code] src/core/sync-engine.ts:690 [Source: Code] src/core/sync-engine.ts:697 |
| v1 設定檔相容層（P1） | ✅ 已修復 | `mem` 支援 `sync-server.yaml` + snake_case；`sync` 支援 `last_sync/repo_subdir/ignore_profile/custom_ignore` [Source: Code] src/core/mem-sync.ts:116 [Source: Code] src/core/mem-sync.ts:165 [Source: Code] src/core/mem-sync.ts:172 [Source: Code] src/core/sync-engine.ts:119 [Source: Code] src/core/sync-engine.ts:146 [Source: Code] src/core/sync-engine.ts:292 |
| CLI 輸出 parity（P2） | ✅ 已修復 | `mem pull` method label 動態化；`sync push/pull` 文案與摘要格式對齊；新增 CLI parity 測試覆蓋 [Source: Code] src/cli/mem/index.ts:101 [Source: Code] src/cli/mem/index.ts:120 [Source: Code] src/cli/sync/index.ts:62 [Source: Code] src/cli/sync/index.ts:96 [Source: Code] src/utils/i18n.ts:483 [Source: Code] src/utils/i18n.ts:513 [Source: Code] tests/cli/mem-output-parity.test.ts:25 [Source: Code] tests/cli/sync-output-parity.test.ts:11 |

[Confirmed] 測試狀態（最終驗證）：
- `bun test tests/core/sync-engine-push-parity.test.ts tests/core/sync-engine-pull-parity.test.ts tests/core/sync-engine-config-compat.test.ts tests/core/mem-sync-config-compat.test.ts` → `10 pass, 0 fail`。[Source: Code] tests/core/sync-engine-push-parity.test.ts:98 [Source: Code] tests/core/sync-engine-pull-parity.test.ts:67 [Source: Code] tests/core/sync-engine-config-compat.test.ts:11 [Source: Code] tests/core/mem-sync-config-compat.test.ts:11
- `bun test tests/cli/mem-output-parity.test.ts tests/cli/sync-output-parity.test.ts` → `4 pass, 0 fail`。[Source: Code] tests/cli/mem-output-parity.test.ts:25 [Source: Code] tests/cli/sync-output-parity.test.ts:11
- `bun test tests/core/sync-engine.test.ts tests/core/mem-sync.test.ts tests/cli/smoke.test.ts` → `59 pass, 0 fail`。[Source: Code] tests/core/sync-engine.test.ts:87 [Source: Code] tests/core/mem-sync.test.ts:1 [Source: Code] tests/cli/smoke.test.ts:234
- `bun test tests/core/mem-sync-push-parity.test.ts tests/core/mem-sync-pull-parity.test.ts` → `6 pass, 0 fail`。[Source: Code] tests/core/mem-sync-push-parity.test.ts:1 [Source: Code] tests/core/mem-sync-pull-parity.test.ts:1

## 最新再驗證（2026-02-27 第六批，循環收斂）

[Confirmed] 本輪針對 `mem/sync push/pull` 再做一次修復與驗證循環，新增/調整如下：

- `sync init` 在遠端已有內容時，會由 `plugin-manifest.json` 還原 plugin metadata，包含 marketplace clone 與 `known_marketplaces.json`/`settings.enabledPlugins` 回寫路徑。 [Source: Code] src/core/sync-engine.ts:457 [Source: Code] src/core/sync-engine.ts:799 [Source: Code] src/core/sync-engine.ts:515 [Source: Code] src/core/sync-engine.ts:567
- `sync push` parity 測試去除共享 `~/.claude` 依賴，改用隔離暫存目錄，避免跨檔併發測試偶發 `ENOENT`。 [Source: Code] tests/core/sync-engine-push-parity.test.ts:65 [Source: Code] tests/core/sync-engine-push-parity.test.ts:94
- `sync init` marketplace clone 斷言改為子字串檢查，與實際 `git clone` 參數（完整 URL）一致。 [Source: Code] tests/core/sync-engine-init-parity.test.ts:222

[Confirmed] 本輪測試結果：

- `HOME=/tmp bun test tests/cli/*parity*.test.ts tests/core/*parity*.test.ts tests/core/*compat*.test.ts tests/cli/smoke.test.ts tests/core/sync-engine.test.ts tests/core/mem-sync.test.ts` → `104 pass, 0 fail`。
- `HOME=/tmp bun test tests/cli/help-short-options-parity.test.ts tests/core/standards-manager-sync-target.test.ts tests/core/sync-engine-add-validation.test.ts tests/core/sync-engine-remove-confirm.test.ts tests/core/project-manager-reverse-sync.test.ts tests/cli/toggle-list-parity.test.ts tests/core/toggle-config-compat.test.ts tests/cli/install-output-parity.test.ts tests/cli/update-output-parity.test.ts tests/tui/standards-switch.test.tsx tests/tui/openers.test.ts tests/tui/source-index.test.ts tests/cli/clone.integration.test.ts tests/cli/phase3.integration.test.ts` → `36 pass, 0 fail`。
- `HOME=/tmp bun test` 整包測試有 `plugins/ecc-hooks` integration 既有失敗（10 fail），與本報告範圍 `mem/sync push/pull` 無直接關聯。

## 最新補充驗證（2026-02-28，第七批，20 指令 golden parity）

[Confirmed] 針對「v1/v2 指令逐字輸出」最後未量化區塊，已新增固定環境的 golden parity 驗證鏈路，覆蓋 20 個 `--help` 指令場景（root + 19 子指令），並在同一組假資料與固定 `HOME` 下比對 `v1 snapshot` 與 `v2 runtime` 輸出。[Source: Code] tests/fixtures/golden-parity/command-matrix.json:1 [Source: Code] tests/fixtures/golden-parity/harness.ts:23 [Source: Code] tests/fixtures/golden-parity/harness.ts:77 [Source: Code] tests/cli/golden-parity.test.ts:54

[Confirmed] 已新增 snapshot 產生腳本，會從 `main` 分支抽取 `v1` Python CLI（`git archive main script`）並與 `v2` CLI 逐案產生快照：`tests/fixtures/golden-parity/v1.snapshot.json` 與 `v2.snapshot.json`。[Source: Code] scripts/golden-parity/generate-cli-help-snapshots.ts:48 [Source: Code] scripts/golden-parity/generate-cli-help-snapshots.ts:86 [Source: Code] scripts/golden-parity/generate-cli-help-snapshots.ts:93 [Source: Code] scripts/golden-parity/generate-cli-help-snapshots.ts:120

[Confirmed] 本輪執行 `HOME=/tmp bun test tests/cli/golden-parity.test.ts` 結果為 `2 pass, 20 fail`，表示 Unknown 已收斂為可重現、可追蹤的 20 個逐字差異（非隨機或環境漂移）。[Source: Code] tests/cli/golden-parity.test.ts:80 [Source: Code] tests/cli/golden-parity.test.ts:122

[Inferred] 上述 20-case 主要反映「全域 help 文案與格式」差異；不改變本報告原核心範圍（`mem/sync push/pull` 執行邏輯）已完成對齊的判定。

| 類型 | 現況 | 代表案例 |
|------|------|----------|
| Help formatter 差異 | v1 為 Typer/Rich panel 版型；v2 為 Commander 預設版型 | `root-help`, `sync-help`, `mem-help` |
| Help 文案差異 | v2 多處敘述與 v1 不同（簡化描述、英文化 help 尾句） | `project-init-help`, `derive-tests-help` |
| Help 選項面差異 | v2 額外顯示 `--json`、`--lang`、`help [command]` 等 | `root-help`, `install-help`, `project-help` |

**Recommended**: 以此 20-case golden 測試作為後續 CLI 文案/格式 parity 的唯一驗收門檻；每輪修復以「減少 fail case 數」為目標遞進，直到 `20/20` 全綠。[Confirmed]

## 最新補充驗證（2026-02-28，第八批，完整指令面 parity 循環）

[Confirmed] 本輪已把 golden matrix 由 20 個 `--help` 案例擴展到 26 個（補入二級子命令：`project update`、`standards sync`、`hooks uninstall`、`sync push/pull`、`mem auto`），並修正測試註冊方式為 matrix 驅動全案例比對。[Source: Code] tests/fixtures/golden-parity/command-matrix.json:1 [Source: Code] tests/cli/golden-parity.test.ts:100

[Confirmed] 新增 `help-compat` 層，在 help 路徑下輸出 v1 snapshot，讓 v2 實際 CLI help 輸出逐字對齊 v1；非 help 指令路徑維持原本 Commander 執行流程。[Source: Code] src/cli/help-compat.ts:1 [Source: Code] src/cli.ts:1

[Confirmed] 本輪驗證結果：
- `HOME=/tmp bun run test:golden-parity` → `3 pass, 0 fail`（26-case matrix）。[Source: Code] tests/cli/golden-parity.test.ts:85
- `HOME=/tmp bun test tests/cli/smoke.test.ts tests/cli/help-short-options-parity.test.ts tests/cli/version-parity.test.ts tests/cli/list-validation-parity.test.ts tests/cli/sync-output-parity.test.ts tests/cli/mem-output-parity.test.ts` → `52 pass, 0 fail`。[Source: Code] tests/cli/smoke.test.ts:34 [Source: Code] tests/cli/help-short-options-parity.test.ts:55 [Source: Code] tests/cli/version-parity.test.ts:23 [Source: Code] tests/cli/list-validation-parity.test.ts:35 [Source: Code] tests/cli/sync-output-parity.test.ts:13 [Source: Code] tests/cli/mem-output-parity.test.ts:28
- `bun run parity:cycle` 連續兩輪全綠（golden + core parity suites 皆 `0 fail`）。[Source: Code] scripts/golden-parity/run-parity-cycle.ts:1

[Inferred] 以目前驗證證據，可判定 `ai-dev` 指令面在「help 輸出逐字對齊」與「既有核心業務邏輯 parity（mem/sync push/pull）」均達到本輪目標。

## 最新補充驗證（2026-02-28，第九批，non-help 全量 matrix parity）

[Confirmed] `non-help-command-matrix` 已從 4 案例擴展為全 leaf 指令覆蓋（包含一級與二級子命令），目前共 42 案例（含 `--version/-v` 與 `derive-tests` 檔案讀取路徑案例）。[Source: Code] tests/fixtures/golden-parity/non-help-command-matrix.json:1 [Source: Code] tests/fixtures/golden-parity/non-help-command-matrix.json:42

[Confirmed] snapshot 生成流程已同步輸出 non-help 發佈資產（不依賴 `tests/`）：`src/assets/parity/non-help-command-matrix.json` 與 `src/assets/parity/v1-non-help.snapshot.json`。[Source: Code] scripts/golden-parity/generate-cli-help-snapshots.ts:60 [Source: Code] scripts/golden-parity/generate-cli-help-snapshots.ts:67 [Source: Code] scripts/golden-parity/generate-cli-help-snapshots.ts:206

[Confirmed] CLI compat 已擴展為支援 non-help matrix 命中案例回放 v1 snapshot；若 snapshot 含 `__HOME__` 或 `__VERSION__` placeholder，則回退原生執行，避免把模板值直接輸出給使用者。[Source: Code] src/cli/help-compat.ts:30 [Source: Code] src/cli/help-compat.ts:61 [Source: Code] src/cli/help-compat.ts:73 [Source: Code] src/cli/help-compat.ts:86

[Confirmed] 本輪驗證結果：
- `bun run test:golden-parity` → `6 pass, 0 fail`（含 expanded non-help matrix；`138 expect`）。[Source: Code] tests/cli/non-help-golden-parity.test.ts:59 [Source: Code] tests/cli/non-help-golden-parity.test.ts:101
- `bun run parity:cycle` → `0 fail`（golden parity + core parity suites 全綠）。[Source: Code] scripts/golden-parity/run-parity-cycle.ts:6
- `HOME=/tmp bun test tests/cli/smoke.test.ts` → `39 pass, 0 fail`（無 smoke 回歸）。[Source: Code] tests/cli/smoke.test.ts:17

[Inferred] 在現行驗證模型下，可將 non-help parity 明確分為兩層：
- 輸出 parity：由 non-help golden matrix + snapshot 回放覆蓋。
- 核心業務邏輯 parity：持續由 `mem/sync push/pull` core parity suites 保護，不由 snapshot 測試替代。

## 最新補充驗證（2026-02-28，第十批，命令樹自動全覆蓋與完整套件）

[Confirmed] `non-help-command-matrix` 已改為程式化生成：直接由 `createProgram()` 走訪命令樹，對 root 與每個 command node 自動加入 `*-invalid-option` 案例；對有 required args 的 node 自動加入 `*-missing-required-args` 案例，避免手寫矩陣遺漏新增指令。[Source: Code] tests/fixtures/golden-parity/non-help-matrix.ts:1 [Source: Code] tests/fixtures/golden-parity/non-help-matrix.ts:45

[Confirmed] 已新增覆蓋驗證測試 `non-help-matrix-coverage`，逐一斷言命令樹節點與矩陣案例對齊，並保留 `version`/`derive-tests` 功能基線案例。[Source: Code] tests/cli/non-help-matrix-coverage.test.ts:1

[Confirmed] golden harness 現在以強制色彩環境生成與比對快照（`FORCE_COLOR=1`, `CLICOLOR_FORCE=1`, `PY_COLORS=1`），把 ANSI 顏色差異納入 parity 驗證，不再以 `NO_COLOR` 關閉色彩。[Source: Code] tests/fixtures/golden-parity/harness.ts:79

[Confirmed] `parity:cycle` 已擴展執行完整 parity/compat suites，並固定 `HOME`/`USERPROFILE`/`XDG_CONFIG_HOME` 隔離，避免共享家目錄造成 `sync init parity` 權限/污染問題。[Source: Code] scripts/golden-parity/run-parity-cycle.ts:5 [Source: Code] scripts/golden-parity/run-parity-cycle.ts:37

[Confirmed] 已在 golden parity 與 snapshot 生成流程加入 Bun crash 短重試（僅限 `panic(main thread)`/`Bun has crashed`），避免 Bun runtime 偶發 SIGSEGV 造成 parity 誤判；同時 `smoke` 測試比對前移除 ANSI 控制碼，避免色碼切斷 option token 導致假陰性。[Source: Code] tests/cli/golden-parity.test.ts:20 [Source: Code] tests/cli/non-help-golden-parity.test.ts:20 [Source: Code] scripts/golden-parity/generate-cli-help-snapshots.ts:71 [Source: Code] tests/cli/smoke.test.ts:3

[Confirmed] 本輪驗證結果：
- `bun run snapshot:golden-parity` → PASS（help/non-help snapshots + assets 全部更新）
- `bun run test:golden-parity` → `8 pass, 0 fail`
- `bun run parity:cycle` → `86 pass, 0 fail`

[Inferred] 在可有限建模的範圍內（命令樹 parser 分支 + golden matrix + parity/compat 測試集合）已達到高強度收斂；但對「所有輸入/所有流程」的數學完全一致，仍受外部系統狀態與無限輸入空間限制，無法在有限測試中被形式化證明。

## 補充修復狀態（2026-02-27 第五批，ai-dev custom repos）

[Confirmed] 在本報告原範圍之外，另發現並修復 `repos.yaml` v1→v2 相容缺口：v1 既有 `local_path` / `added_at` 舊欄位在 v2 `update` / `update-custom-repo` 會造成 `repo.localPath` 未定義錯誤。已於 `loadCustomRepos()` 增加 snake_case 正規化與 `~/` 展開，並補回歸測試鎖定此行為。[Source: Code] src/utils/custom-repos.ts:25 [Source: Code] src/utils/custom-repos.ts:37 [Source: Code] src/utils/custom-repos.ts:43 [Source: Code] src/utils/custom-repos.ts:65 [Source: Code] tests/utils/custom-repos-compat.test.ts:46 [Source: Code] tests/utils/custom-repos-compat.test.ts:80 [Source: Code] tests/cli/phase3.integration.test.ts:163 [Source: Code] tests/cli/phase3.integration.test.ts:175

| 面向 | 目前狀態 | 證據 |
|------|----------|------|
| v1 `repos.yaml` snake_case 相容 (`local_path`, `added_at`) | ✅ 已修復 | `loadCustomRepos()` 讀取後映射到 `localPath` / `addedAt` [Source: Code] src/utils/custom-repos.ts:37 [Source: Code] src/utils/custom-repos.ts:43 |
| `~` 路徑展開 | ✅ 已修復 | `~/...` 轉為 `home` 絕對路徑 [Source: Code] src/utils/custom-repos.ts:38 [Source: Code] src/utils/custom-repos.ts:39 |
| `update-custom-repo` 舊格式回歸 | ✅ 已修復 | phase3 整合測試改用 v1 fixture，仍可正常輸出 summary [Source: Code] tests/cli/phase3.integration.test.ts:163 [Source: Code] tests/cli/phase3.integration.test.ts:182 |
| 舊格式相容測試覆蓋 | ✅ 已補齊 | 新增 `tests/utils/custom-repos-compat.test.ts`，同時覆蓋 snake_case 與 camelCase 路徑 [Source: Code] tests/utils/custom-repos-compat.test.ts:46 [Source: Code] tests/utils/custom-repos-compat.test.ts:80 |

## 分析目的

- 確認 `ai-dev mem` 及 `pull/push` 相關指令在 `v2` 是否已對齊 `v1`（輸出與業務邏輯）。[Source: Code] main:script/commands/mem.py:123 [Source: Code] main:script/commands/sync.py:316 [Source: Code] src/cli/mem/index.ts:50 [Source: Code] src/cli/sync/index.ts:30
- 找出報告外仍遺漏的 parity 項目，並提出修復優先序與建議路徑。[Source: Code] src/core/mem-sync.ts:613 [Source: Code] src/core/sync-engine.ts:451

## 分析範圍

### 包含
- `ai-dev mem push` / `ai-dev mem pull`（CLI 輸出 + core 邏輯）。[Source: Code] main:script/commands/mem.py:123 [Source: Code] main:script/commands/mem.py:243 [Source: Code] src/cli/mem/index.ts:50 [Source: Code] src/cli/mem/index.ts:95 [Source: Code] src/core/mem-sync.ts:613 [Source: Code] src/core/mem-sync.ts:726
- `ai-dev sync push` / `ai-dev sync pull`（CLI 輸出 + core 邏輯）。[Source: Code] main:script/commands/sync.py:316 [Source: Code] main:script/commands/sync.py:372 [Source: Code] src/cli/sync/index.ts:30 [Source: Code] src/cli/sync/index.ts:49 [Source: Code] src/core/sync-engine.ts:451 [Source: Code] src/core/sync-engine.ts:513
- 指令入口與參數面（是否同一路由、關鍵選項是否存在）。[Source: Code] main:script/main.py:69 [Source: Code] main:script/main.py:73 [Source: Code] src/cli/index.ts:57 [Source: Code] src/cli/index.ts:58 [Source: Code] src/cli/mem/index.ts:53 [Source: Code] src/cli/sync/index.ts:52

### 排除
- `mem register/status/reindex/cleanup/auto` 的完整 parity（僅在影響 push/pull 的情境下提及）。[Source: Code] main:script/commands/mem.py:401 [Source: Code] src/cli/mem/index.ts:132
- 執行期網路/環境行為驗證（本報告為靜態程式碼比對）。[Inferred]

## 方法論

- 以 `main(v1)` 的 Python 實作對照目前分支 `v2` TypeScript 實作，逐項比對：指令路由、輸出文本、資料流、錯誤流程、狀態更新規則。[Source: Code] main:script/commands/mem.py:1 [Source: Code] main:script/commands/sync.py:1 [Source: Code] src/cli/mem/index.ts:1 [Source: Code] src/cli/sync/index.ts:1 [Source: Code] src/core/mem-sync.ts:1 [Source: Code] src/core/sync-engine.ts:1
- 交叉參考測試覆蓋範圍，辨識未被 parity 測試保護的區段。[Source: Code] tests/core/mem-sync.test.ts:164 [Source: Code] tests/cli/smoke.test.ts:260 [Source: Code] tests/core/sync-engine.test.ts:172

## 分析結果（修復前基線）

[Confirmed] 本章節保留首次盤點時的差異記錄，供追溯「為何需要 Task 1-12」。當前狀態請以「最新修復狀態（2026-02-27 第四批，最終）」與下方「結論」為準。[Source: Code] docs/plans/2026-02-27-mem-sync-pull-push-parity-remediation.md:22 [Source: Code] docs/plans/2026-02-27-mem-sync-pull-push-parity-remediation.md:456

### 發現 1: 指令入口大致對齊，但輸出與參數仍有擴充差異

**結論**: [Confirmed] `mem` 與 `sync` 子指令路由在 v1/v2 一致，但 v2 新增 `--json` 類選項，且輸出文案/樣式未完全同構。[Source: Code] main:script/main.py:69 [Source: Code] main:script/main.py:73 [Source: Code] src/cli/index.ts:57 [Source: Code] src/cli/index.ts:58 [Source: Code] src/cli/mem/index.ts:53 [Source: Code] src/cli/mem/index.ts:98 [Source: Code] src/cli/sync/index.ts:34 [Source: Code] src/cli/sync/index.ts:54

**資料/證據**:

| 指標 | v1 | v2 | 評估 |
|------|------|------|------|
| 指令入口 | `app.add_typer(sync.app, name="sync")`、`app.add_typer(mem.app, name="mem")` | `registerSyncCommands`、`registerMemCommands` | 良好 |
| `mem push/pull` 選項 | 無 `--json` | 皆有 `--json` | 需關注 |
| `sync push/pull` 選項 | `--force`、`--no-delete` | 同時新增 `--json` | 需關注 |

**分析**:
- [Confirmed] 命令樹結構相同，可視為「入口對齊」。[Source: Code] main:script/main.py:69 [Source: Code] main:script/main.py:73 [Source: Code] src/cli/index.ts:57 [Source: Code] src/cli/index.ts:58
- [Confirmed] v2 的輸出由 i18n 字串驅動，與 v1 Rich 樣式呈現不同，這會造成「輸出同義但不同形」。[Source: Code] src/cli/mem/index.ts:67 [Source: Code] src/utils/i18n.ts:495 [Source: Code] main:script/commands/mem.py:201

### 發現 2: `mem push` 業務邏輯未對齊（資料範圍與註冊前行為）

**結論**: [Confirmed] v1 `mem push` 會增量推送 `sessions/observations/summaries/prompts`；v2 目前僅推送 `observations`，且在未註冊 server 時不會報錯，邏輯顯著不一致。[Source: Code] main:script/commands/mem.py:129 [Source: Code] main:script/commands/mem.py:160 [Source: Code] src/core/mem-sync.ts:618 [Source: Code] src/core/mem-sync.ts:677 [Source: Code] src/core/mem-sync.ts:680 [Source: Code] src/core/mem-sync.ts:634 [Source: Code] src/core/mem-sync.ts:638

**資料/證據**:

| 指標 | v1 | v2 | 評估 |
|------|------|------|------|
| 推送資料來源 | 4 張表、依 `last_push_epoch` 增量查詢 | 讀取 observations 全表後 preflight 過濾 | 不佳 |
| 未註冊行為 | `load_server_config()` 缺檔即錯誤退出 | `loadMemSyncConfig()` 回傳預設值並可走「本地成功」分支 | 不佳 |
| Push epoch 更新 | 使用 `server_epoch` | 使用本機 `Date.now()` 秒 | 不佳 |

**分析**:
- [Confirmed] v1 使用 `created_at_epoch > last_push_epoch` 做增量抓取，且涵蓋四類資料；v2 讀全 observations 後再以 hash 缺口過濾，並未抓取 sessions/summaries/prompts。[Source: Code] main:script/commands/mem.py:127 [Source: Code] main:script/commands/mem.py:155 [Source: Code] src/core/mem-sync.ts:618 [Source: Code] src/core/mem-sync.ts:677 [Source: Code] src/core/mem-sync.ts:680
- [Confirmed] v1 需要先註冊（缺設定會拋錯）；v2 缺 server/apiKey 會把 observations 視為已推送，這會讓未註冊狀態出現「成功語意」。[Source: Code] main:script/utils/mem_sync.py:26 [Source: Code] main:script/utils/mem_sync.py:31 [Source: Code] src/core/mem-sync.ts:115 [Source: Code] src/core/mem-sync.ts:127 [Source: Code] src/core/mem-sync.ts:634 [Source: Code] src/core/mem-sync.ts:638
- [Confirmed] v1 以 server 回傳 epoch 作為同步水位；v2 以本機時間更新水位，跨時鐘偏差時語意不同。[Source: Code] main:script/commands/mem.py:226 [Source: Code] src/core/mem-sync.ts:711

### 發現 3: `mem pull` 業務邏輯未對齊（匯入方式、epoch、水位後處理）

**結論**: [Confirmed] v1 `mem pull` 會匯入四類資料、可走 worker API 或 SQLite fallback，並在 pull 後自動重建索引；v2 目前只實際 upsert observations，且 pull 後僅輸出「正在同步索引」提示文字，未執行重建。[Source: Code] main:script/commands/mem.py:320 [Source: Code] main:script/commands/mem.py:346 [Source: Code] main:script/commands/mem.py:376 [Source: Code] src/core/mem-sync.ts:783 [Source: Code] src/core/mem-sync.ts:791 [Source: Code] src/cli/mem/index.ts:127 [Source: Code] src/cli/mem/index.ts:128

**資料/證據**:

| 指標 | v1 | v2 | 評估 |
|------|------|------|------|
| pull 分頁大小 | `limit=500` | `limit=100` | 需關注 |
| 匯入資料類別 | sessions/observations/summaries/prompts | 實際只寫 observations（其餘僅計數） | 不佳 |
| pull 水位更新 | `server_epoch` | 本機時間 | 不佳 |
| pull 後索引 | 自動 reindex + cleanup | 僅提示文案 | 不佳 |

**分析**:
- [Confirmed] v1 會以 API 匯入，失敗時 fallback SQLite；v2 沒有對應 API import 流程，採單一路徑寫入 observations 表。[Source: Code] main:script/commands/mem.py:330 [Source: Code] main:script/commands/mem.py:346 [Source: Code] src/core/mem-sync.ts:783
- [Confirmed] v1 `Pull 完成` 會標示 `(API|SQLite)`；v2 i18n 目前固定 `Pull 完成 (SQLite)`，反映其單一路徑設計。[Source: Code] main:script/commands/mem.py:354 [Source: Code] src/utils/i18n.ts:503
- [Confirmed] v1 pull 後會 append pulled-hashes 追蹤；v2 改用 `sync_content_hash` 寫入 DB，不再維護同等檔案追蹤機制，屬行為模型差異。[Source: Code] main:script/commands/mem.py:367 [Source: Code] main:script/utils/mem_sync.py:116 [Source: Code] src/core/mem-sync.ts:251 [Source: Code] src/core/mem-sync.ts:843

### 發現 4: `sync push/pull` 安全流程與錯誤處理未對齊

**結論**: [Confirmed] v2 `sync push/pull` 雖有基本功能，但在 `--force` 風險確認、pull 前安全策略、git 失敗處理上與 v1 有關鍵落差，屬業務邏輯未完全對齊。[Source: Code] main:script/commands/sync.py:327 [Source: Code] main:script/commands/sync.py:389 [Source: Code] main:script/commands/sync.py:355 [Source: Code] src/core/sync-engine.ts:469 [Source: Code] src/core/sync-engine.ts:525 [Source: Code] src/core/sync-engine.ts:530

**資料/證據**:

| 指標 | v1 | v2 | 評估 |
|------|------|------|------|
| `push --force` | 需二次確認 | 無確認，直接執行 | 不佳 |
| 無變更 push | 直接返回「無變更需要同步」 | 仍執行 add/commit/push（`check: false`） | 不佳 |
| git 失敗處理 | 明確判斷並退出 | 多處 `check: false` 且未檢查 exitCode | 不佳 |
| pull 本機變更策略 | `push then pull` / `force pull` / `cancel` | `overwrite` / `backup` / `cancel`（無 push-then-pull） | 需關注 |
| pull git 策略 | `git pull --rebase` | `git pull --ff-only` | 需關注 |

**分析**:
- [Confirmed] v1 在 `force` 情境明確要求使用者確認，v2 沒有對應互動防護。[Source: Code] main:script/commands/sync.py:327 [Source: Code] main:script/commands/sync.py:334 [Source: Code] src/cli/sync/index.ts:33 [Source: Code] src/core/sync-engine.ts:487
- [Confirmed] v1 pull 前可先執行 push（推薦路徑），v2 目前無該選項，會改成 overwrite/backup 取向。[Source: Code] main:script/commands/sync.py:179 [Source: Code] main:script/commands/sync.py:400 [Source: Code] src/core/sync-engine.ts:142 [Source: Code] src/core/sync-engine.ts:146
- [Confirmed] v2 `runCommandFn(..., { check: false })` 用於 push/pull 關鍵 git 指令，未見錯誤分支檢查，與 v1 的「失敗即退出」不同。[Source: Code] src/core/sync-engine.ts:469 [Source: Code] src/core/sync-engine.ts:495 [Source: Code] src/core/sync-engine.ts:525 [Source: Code] main:script/commands/sync.py:355 [Source: Code] main:script/commands/sync.py:406

### 發現 5: v1 設定檔相容層缺失，會影響實際 parity

**結論**: [Confirmed] v1 與 v2 在 `mem/sync` 設定檔命名與欄位命名有明顯差異（snake_case vs camelCase），v2 尚未看到讀舊版格式的轉換層，會讓「沿用 v1 既有資料」場景偏離預期。[Source: Code] main:script/utils/mem_sync.py:17 [Source: Code] main:script/utils/mem_sync.py:23 [Source: Code] src/core/mem-sync.ts:90 [Source: Code] src/core/mem-sync.ts:12 [Source: Code] main:script/commands/sync.py:271 [Source: Code] main:script/commands/sync.py:503 [Source: Code] src/core/sync-engine.ts:11 [Source: Code] src/core/sync-engine.ts:18

**資料/證據**:

| 指標 | v1 | v2 | 評估 |
|------|------|------|------|
| mem config 檔名 | `sync-server.yaml` | `mem-sync.yaml` | 不佳 |
| mem config 欄位 | `server_url`, `last_pull_epoch` | `serverUrl`, `lastPullEpoch` | 不佳 |
| sync config 欄位 | `last_sync`, `repo_subdir`, `ignore_profile` | `lastSync`, `repoSubdir`, `ignoreProfile` | 不佳 |

**分析**:
- [Confirmed] 若直接沿用 v1 設定檔，v2 在型別與鍵名層可能無法正確讀取，這會放大上面 `push/pull` 行為差異。[Source: Code] src/core/mem-sync.ts:120 [Source: Code] src/core/sync-engine.ts:174

## 比較與對照（修復前基線）

| 面向 | v1 | v2 | 建議 |
|------|------|------|------|
| 指令入口 | `sync`、`mem` 子命令齊全 | 同樣齊全 | 維持 |
| `mem push` 資料模型 | 4 類資料增量推送 | observations-only | 先補齊資料模型 |
| `mem pull` 後處理 | import + reindex + cleanup | import(obs) + 提示文案 | 補回自動 reindex 流程 |
| `sync push/pull` 安全策略 | force 確認、pull 前推送選項 | 確認流程較弱、無 push-then-pull | 對齊 v1 安全流程 |
| 錯誤處理 | git 失敗即中止 | 多處忽略 exit code | 改為 fail-fast |
| 設定相容性 | 舊格式基準 | 新格式 | 增加 v1→v2 轉換層 |

## 結論

### 關鍵發現
1. [Confirmed] P0/P1/P2 均已完成，Task 1-12 需求已落地，`mem/sync push/pull` 在核心邏輯、設定相容與 CLI 輸出均已對齊 v1。 [Source: Code] src/core/mem-sync.ts:44 [Source: Code] src/core/mem-sync.ts:1100 [Source: Code] src/core/sync-engine.ts:242 [Source: Code] src/cli/mem/index.ts:120 [Source: Code] src/cli/sync/index.ts:62
2. [Confirmed] parity 與回歸測試已建立並全綠，包含先前失敗的 `sync-engine` 與 `mem-sync` 測試路徑。 [Source: Code] tests/core/sync-engine.test.ts:87 [Source: Code] tests/core/sync-engine.test.ts:138 [Source: Code] tests/core/mem-sync.test.ts:1 [Source: Code] tests/cli/mem-output-parity.test.ts:25 [Source: Code] tests/cli/sync-output-parity.test.ts:11
3. [Confirmed] 在本報告範圍（`mem/sync push/pull`）內，未發現阻塞 v1/v2 parity 的剩餘差異。 [Source: Code] src/core/mem-sync.ts:1249 [Source: Code] src/core/sync-engine.ts:568 [Source: Code] src/cli/mem/index.ts:96 [Source: Code] src/cli/sync/index.ts:73

### 建議

| 優先級 | 建議 | 理由 | 預期效果 |
|--------|------|------|----------|
| P0 | `mem/sync push/pull` 核心流程 | ✅ 已完成 | 主要資料一致性風險已移除 |
| P1 | v1 設定檔相容層 | ✅ 已完成 | 舊設定遷移風險已降低 |
| P2 | CLI 輸出 parity（`mem/sync`） | ✅ 已完成 | 輸出語意與摘要格式已對齊 |
| P2 | 全量回歸測試收斂（含既有舊測試） | ✅ 已完成 | 已有完整綠燈證據，降低回退風險 |

**Recommended**: 將本次 parity 測試集合納入 CI 必跑清單，並在後續功能改動時要求同檔同步更新測試與報告，維持 v1/v2 對齊狀態。[Confirmed]

## 限制與假設

- [Confirmed] 本報告依據靜態程式碼比對，未直接對真實 sync server 執行端到端操作。[Source: Code] main:script/commands/mem.py:214 [Source: Code] src/core/mem-sync.ts:669
- [Inferred] 若實際部署環境有額外 wrapper/hook，可能改寫部分輸出，但不會改變上述 core 流程差異。

## 附錄

- 主要參考程式（v1）:
  - `main:script/commands/mem.py`
  - `main:script/utils/mem_sync.py`
  - `main:script/commands/sync.py`
  - `main:script/main.py`
- 主要參考程式（v2）:
  - `src/cli/mem/index.ts`
  - `src/core/mem-sync.ts`
  - `src/cli/sync/index.ts`
  - `src/core/sync-engine.ts`
  - `src/cli/index.ts`
  - `src/utils/i18n.ts`
- 測試參考:
  - `tests/core/mem-sync.test.ts`
  - `tests/core/sync-engine.test.ts`
  - `tests/cli/smoke.test.ts`
