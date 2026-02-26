# 測試品質審計報告：「假測試」問題調查

**日期**: 2026-02-26
**觸發原因**: 發現 `defaultMemDbPath()` 指向錯誤路徑 (`~/.claude/statsig/statsig.db`)，但 281 個測試全部通過。根因是所有 mem-sync 測試都透過 DI 注入 temp 路徑，繞過了 default 值的驗證。
**審計範圍**: 28 個測試檔案（tests/ 目錄下全部 .test.ts）
**審計方式**: 4 個 agent 平行審計，比對每個測試檔案與對應源碼

---

## 執行摘要

| 風險等級 | 數量 | 涉及模組 |
|---------|------|---------|
| **高** | 5 | mem-sync, i18n, copy-skills, clone.integration, sync-engine |
| **中** | 9 | installer, updater, custom-repo-updater, upstream-repo-manager, skill-distributor, status-checker, shared, paths, system, manifest-tracker, phase3.integration, smoke |
| **低** | 6 | claude-code-manager, custom-repo-manager, standards-manager, test-runner, config, git |
| **無問題** | 4 | backup, formatter, manifest(hash), install-update-format |

**核心發現**: 存在一個系統性問題 — **default 路徑/設定被 DI 繞過而從未驗證**。這不是個別測試的疏忽，而是整個測試策略的盲區。

---

## 高風險問題（5 項）

### 1. mem-sync — default 路徑全被繞過 ⚠️ 已修復一項
**檔案**: `tests/core/mem-sync.test.ts` → `src/core/mem-sync.ts`

| Default 函式 | 回傳值 | 測試覆蓋 |
|-------------|--------|---------|
| `defaultMemDbPath()` | `~/.claude-mem/claude-mem.db` | ❌ 全被 `dbPath` 注入繞過（**已修復**） |
| `defaultMemSyncConfigPath()` | `~/.config/ai-dev/mem-sync.yaml` | ❌ 全被 `configPath` 注入繞過 |
| `defaultChromaDbPath()` | `~/.claude-mem/chroma/chroma.sqlite3` | ❌ 全被 `chromaDbPath` 注入繞過 |

額外問題:
- `countObservations()` 有 better-sqlite3 → bun:sqlite 的 fallback 邏輯，測試只走 bun:sqlite 路徑
- `WORKER_URL = "http://localhost:37777"` 的 reindex 路徑從未被測試
- `registerDevice` 的遠端 API 成功路徑未被測試（測試都走 fallback）

### 2. i18n — DEFAULT_LOCALE 假測試
**檔案**: `tests/utils/i18n.test.ts` → `src/utils/i18n.ts`

源碼 default: `DEFAULT_LOCALE = "zh-TW"`
測試行為: `beforeEach` 強制 `setLocale("en")`，然後斷言 `getLocale() === "en"` 並命名為 "defaults to english locale"

**問題**: 測試名稱與實際行為不符。如果有人把 `DEFAULT_LOCALE` 改錯，測試不會發現。

### 3. copy-skills — COPY_TARGETS 被 monkey-patch
**檔案**: `tests/utils/copy-skills.test.ts` → `src/utils/shared.ts`

測試直接修改全域 `COPY_TARGETS.claude.skills` 為 temp 路徑。生產環境的真實路徑（`~/.claude/skills` 等）從未被驗證。

### 4. clone.integration — 同樣的 COPY_TARGETS 問題
**檔案**: `tests/cli/clone.integration.test.ts` → `src/cli/clone.ts`

`redirectTargets()` 將所有 target 路徑指向 temp 目錄，`paths.ts` 的正確性從未被驗證。

### 5. sync-engine — default paths + factory 零覆蓋
**檔案**: `tests/core/sync-engine.test.ts` → `src/core/sync-engine.ts`

| Default 值 | 說明 | 測試覆蓋 |
|-----------|------|---------|
| `paths.syncConfig` | `~/.config/ai-dev/sync.yaml` | ❌ |
| `paths.syncRepo` | `~/.config/ai-dev/sync-repo` | ❌ |
| `defaultDirectories()` | `~/.claude` | ❌ 被測試刻意移除 |
| `createDefaultSyncEngine()` | 工廠函數 | ❌ 零覆蓋 |

---

## 中風險問題（9 項）

### 6. installer / updater — 共用常數未驗證
`NPM_PACKAGES`, `BUN_PACKAGES`, `REPOS` 的實際內容（URL 格式、路徑正確性）從未在測試中被驗證。所有測試都注入自訂清單。

### 7. paths.ts — 只測了 4/30+ 路徑
`paths` 匯出 30+ 個路徑，但 `tests/utils/paths.test.ts` 只驗證了 `home`, `config`, `claudeSkills`, `opencodeConfig` 四個。

### 8. status-checker — 環境依賴型測試
第一個測試使用真實的 `commandExists`，結果取決於開發者機器上安裝的工具。

### 9. shared.test.ts — 路徑斷言太寬鬆
只檢查 `endsWith("/.claude/skills")`，不驗證完整路徑。

### 10. system.test.ts — timeoutMs 未測試
`runCommand` 的 timeout 邏輯完全沒有測試覆蓋。`check=true` 的 default 行為也沒有明確測試。

### 11. manifest-tracker — 資源類型不完整
`recordAgent` 和 `recordWorkflow` 方法完全沒有測試。`source` default 參數未驗證。

### 12. custom-repo-updater — edge cases 遺漏
`loadCustomRepos` 的 default 載入路徑被繞過。`compareRemote` 的 parse 失敗路徑未測。

### 13. upstream-repo-manager — configDir default 未驗證
`configDir = join(homedir(), ".config")` 的 default 從未在測試中驗證。

### 14. skill-distributor — backup + default targets 未測
`backup: true` 路徑未覆蓋。所有測試都只傳 `targets: ["claude"]`，default（全部 targets）未測。

### 15. smoke.test.ts — 非 deterministic
使用真實 HOME，結果取決於開發者環境。版本號硬編碼。

### 16. phase3.integration — plugin source 覆蓋不完整
`pluginSourceCandidates()` 的 fallback 路徑未測。`homedir()` 是否受 `HOME` env 影響未驗證。

---

## 系統性根因分析

### 模式：DI 注入繞過 default 值

```
源碼: function foo(options = { path: DEFAULT_PATH }) { ... }
測試: foo({ path: "/tmp/test" })  // DEFAULT_PATH 從未被執行
```

這個模式出現在 **18/28 個測試檔案** 中。DI 是好的測試實踐，但缺少了一層「驗證 default 值本身」的測試。

### 模式：全域可變物件被 monkey-patch

`COPY_TARGETS` 是可變的全域物件，測試直接修改再還原。如果生產環境的值有誤，測試無法發現。

### 模式：paths.ts 是單點故障

幾乎所有模組都依賴 `paths.ts` 提供路徑，但 `paths.test.ts` 只覆蓋了 ~13% 的匯出路徑。如果 `paths.ts` 有任何計算錯誤，影響範圍極廣但測試不會告警。

---

## 建議修復優先級

### P0 — 立即修復（影響生產正確性）

1. **paths.ts 完整覆蓋測試**: 驗證所有 30+ 路徑的前綴和格式正確性
2. **default path 函式驗證**: 為 `defaultMemSyncConfigPath()`, `defaultChromaDbPath()`, `createDefaultSyncEngine()` 加 unit test
3. **COPY_TARGETS snapshot 測試**: 凍結 default 值，任何變更需要顯式更新 snapshot

### P1 — 短期修復（防止未來回歸）

4. **i18n DEFAULT_LOCALE 測試**: 驗證初始 locale 為 `zh-TW`
5. **shared constants 驗證**: `NPM_PACKAGES` URL 格式、`REPOS` dir 路徑前綴
6. **runCommand timeoutMs 測試**: 覆蓋 timeout 邏輯

### P2 — 中期改善（提升測試品質）

7. **smoke.test.ts 隔離 HOME**: 對有副作用的指令使用隔離環境
8. **manifest-tracker 補齊**: 覆蓋 agent/workflow 資源類型
9. **status-checker 標記 integration**: 環境依賴測試明確標記

### P3 — 長期改善（架構層面）

10. **COPY_TARGETS 改為 DI 參數**: 讓 `distributeSkills` 接受 targets map 注入，避免 monkey-patch
11. **建立 "default value validation" 測試類別**: 專門驗證所有 default 值的正確性
