## Context

ECC Hooks 有兩個版本，共用相同的 scripts 實作：

| Plugin | 目標平台 | 格式 |
|--------|----------|------|
| `plugins/ecc-hooks/` | Claude Code | hooks.json + Node.js scripts |
| `plugins/ecc-hooks-opencode/` | OpenCode | plugin.ts + 相同 Node.js scripts |

兩者的 `scripts/code-quality/lib/` 目錄內容相同（各自維護副本），提供 PostToolUse hooks 在編輯檔案後自動執行格式化工具（Prettier, Pint, Ruff 等）。

目前實作使用 `execSync` 搭配字串串接執行命令：

```javascript
// 目前寫法
execSync(`npx prettier --write ${JSON.stringify(filePath)}`, {...})
```

雖然 `JSON.stringify` 提供了部分保護，但這不是防止命令注入的標準做法。上游 everything-claude-code 已在 PR #102 中修復此問題。

## Goals / Non-Goals

**Goals:**
- 消除命令注入風險，使用 `execFileSync` + 陣列參數
- 同時修復 `ecc-hooks` 和 `ecc-hooks-opencode` 兩個版本
- 改進 session ID fallback，使用 project name 而非 PPID
- 保持完全向後相容，不改變功能行為
- 更新對應單元測試

**Non-Goals:**
- 不改變 hook 觸發邏輯或 matcher 規則
- 不新增功能或改變使用者介面
- 不整合上游的 CI/CD pipeline（與本專案結構不同）

## Decisions

### 1. 使用 `execFileSync` 取代 `execSync`

**選擇**: `execFileSync(command, [args], options)`

**理由**:
- `execFileSync` 直接執行檔案，不經過 shell 解析
- 參數以陣列傳遞，避免 shell 特殊字元被解析
- 這是 Node.js 官方建議的安全做法

**替代方案**:
- ❌ 繼續使用 `execSync` + 更嚴格的 escape：仍有邊界情況風險
- ❌ 使用 `spawn`：非同步 API，需要大幅重構

**程式碼範例**:
```javascript
// Before
execSync(`npx prettier --write ${JSON.stringify(filePath)}`, {...})

// After
const { execFileSync } = require('child_process');
execFileSync('npx', ['prettier', '--write', filePath], {...})
```

### 2. Session ID Fallback 改用 Project Name

**選擇**: 使用 `getProjectName()` 作為 fallback

**理由**:
- PPID 在不同執行環境下不穩定
- Project name 更有意義，便於識別 session 檔案
- 與上游保持一致

**實作**:
```python
# Before
session_id = os.environ.get('CLAUDE_SESSION_ID', os.environ.get('PPID', 'default'))

# After
session_id = os.environ.get('CLAUDE_SESSION_ID') or get_project_name() or 'default'
```

### 3. 保留 `JSON.stringify` 作為額外保護

**選擇**: 移除 `JSON.stringify`，純粹使用陣列參數

**理由**:
- `execFileSync` 的陣列參數已經安全
- 移除不必要的處理，程式碼更清晰

### 4. 雙版本同步策略

**選擇**: 同時修改兩個 plugin 的 scripts，保持副本一致

**理由**:
- 目前兩個 plugin 的 scripts 是獨立副本（非 symlink）
- 維持現有架構，避免引入額外複雜度
- 未來可考慮抽取為共用模組，但不在本次範圍

**影響檔案**:
```
plugins/ecc-hooks/scripts/code-quality/lib/
├── format-js.js
├── format-php.js
└── format-python.js

plugins/ecc-hooks-opencode/scripts/code-quality/lib/
├── format-js.js      (相同修改)
├── format-php.js     (相同修改)
└── format-python.js  (相同修改)
```

## Risks / Trade-offs

| 風險 | 緩解措施 |
|------|----------|
| `npx` 在某些環境找不到 | 使用 `which npx` 預先檢查，失敗時靜默跳過 |
| Windows 相容性 | `execFileSync` 跨平台支援良好，無需特殊處理 |
| 測試未覆蓋所有情況 | 補充 mock `execFileSync` 的單元測試 |
| PHP/Python formatter 路徑問題 | 保持現有路徑查找邏輯不變 |
| 雙版本不同步 | 本次修改後執行 diff 確認一致 |
