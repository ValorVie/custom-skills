## Context

ECC Hooks Plugin 的 `format-*.js`（format-js, format-php, format-python）已在前次安全修正中從 `execSync` 遷移至 `execFileSync`。但 `check-*.js` 系列（check-mypy, check-phpstan, check-typescript, check-debug-code）仍殘留 `execSync` 用法。

現有 hook-system spec 已定義「安全命令執行」requirement，明確要求使用 `execFileSync` 並禁止 `execSync` 搭配字串模板。當前程式碼違反此 spec。

## Goals / Non-Goals

**Goals:**
- 將 4 個 `check-*.js` 從 `execSync` 遷移至 `execFileSync`
- 同步修正 `ecc-hooks` 和 `ecc-hooks-opencode` 兩個 plugin（共 8 個檔案）
- 更新對應 Jest 測試以匹配新 API
- 遷移後所有測試通過

**Non-Goals:**
- 不新增測試（僅更新現有測試的 mock 介面）
- 不重構 check-*.js 的業務邏輯
- 不處理 Python `shell=True` 問題（屬 ci-testing-and-scripts-dedup change）
- 不處理 scripts 去重問題

## Decisions

### Decision 1: 逐檔遷移 execSync → execFileSync

**選擇**：直接將每個 `check-*.js` 的 `execSync` 改為 `execFileSync`，參數改為陣列形式。

**替代方案**：
- 建立共用 `safeExec()` wrapper — 過度工程，4 個檔案的用法各不同
- 使用 `spawn` — `execFileSync` 已足夠，且與 `format-*.js` 一致

**理由**：與已修正的 `format-*.js` 保持一致的 pattern，最小改動。

### Decision 2: check-debug-code.js 特殊處理

`check-debug-code.js` 執行的是固定命令（`git rev-parse`, `git diff`），無使用者輸入。但為一致性和符合 spec，仍統一遷移。

`git diff` 的 `2>&1` 重導向在 `execFileSync` 下不可用（無 shell），改用 `stdio` 選項處理 stderr。

### Decision 3: check-typescript.js 特殊處理

`check-typescript.js` 執行 `npx tsc --noEmit 2>&1`，同樣有 `2>&1` 重導向。改為：
```javascript
execFileSync('npx', ['tsc', '--noEmit'], { stdio: ['pipe', 'pipe', 'pipe'] })
```
stderr 不需要合併到 stdout，因為只檢查 exit code 和 stdout 輸出。

### Decision 4: 依賴注入介面變更

現有 check-*.js 使用 `deps.execSync` 注入。遷移後改為 `deps.execFileSync`，與 format-*.js 一致。測試也需相應更新 mock。

## Risks / Trade-offs

- **[Risk] check-debug-code.js 的 git 命令行為可能不同** → execFileSync 不透過 shell，但 git 命令不依賴 shell 功能，風險極低
- **[Risk] 測試 mock 變更可能遺漏** → 透過 `npm test` 驗證全部測試通過
- **[Risk] ecc-hooks-opencode 不同步** → 修改後用 `diff` 驗證兩個 plugin 的 lib 目錄一致
