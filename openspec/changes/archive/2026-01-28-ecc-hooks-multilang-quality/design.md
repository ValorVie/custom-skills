## Context

ecc-hooks 目前的 PostToolUse hooks 僅處理 PR URL 提取，Stop hook 僅檢查 JS/TS 的 console.log。上游 everything-claude-code 已擴展支援多語言的程式碼品質檢查，包含自動格式化、靜態分析和 debug 程式碼警告。

現有架構：
- hooks.json 使用 matcher 條件過濾觸發時機
- 現有腳本混用 Python（memory persistence）和 Python one-liner（其他 hooks）
- 上游已改用 Node.js 實作品質檢查 hooks

## Goals / Non-Goals

**Goals:**
- 在編輯檔案後即時提供程式碼品質回饋
- 支援 JS/TS、PHP、Python 三種語言
- 保持工具可選性（未安裝則靜默跳過）
- 與上游 everything-claude-code 保持程式碼一致性

**Non-Goals:**
- 不強制使用者安裝任何格式化或靜態分析工具
- 不將現有 Python 腳本（memory persistence）轉換為 Node.js
- 不實作動態開關機制（matcher 已提供語言過濾）
- 不修改 PreToolUse hooks

## Decisions

### Decision 1: 使用 Node.js 實作新 hooks

**選擇**: Node.js one-liner

**替代方案考量**:
| 方案 | 優點 | 缺點 |
|------|------|------|
| Node.js one-liner | 與上游一致、易同步更新 | 可讀性較差 |
| Node.js 獨立腳本 | 可讀性好 | 增加檔案數量 |
| Python one-liner | 與現有 hooks 一致 | 需手動轉換上游程式碼 |

**理由**: 優先考量與上游同步的便利性，one-liner 雖可讀性差但功能簡單，未來可視需求抽成獨立腳本。

### Decision 2: 工具偵測策略

**選擇**: 專案根目錄向上搜尋配置檔

**偵測邏輯**:
```
編輯檔案路徑 → 向上搜尋專案根 → 檢查工具配置/執行檔是否存在 → 存在則執行
```

| 語言 | 格式化工具偵測 | 靜態分析偵測 |
|------|---------------|-------------|
| JS/TS | npx prettier（假設可用） | tsconfig.json 存在 |
| PHP | vendor/bin/pint 或 .php-cs-fixer.php | vendor/bin/phpstan |
| Python | 先嘗試 ruff，失敗則 black | pyproject.toml 或 mypy.ini |

**理由**: 避免在未配置工具的專案執行失敗，同時支援多種常見工具選擇。

### Decision 3: Stop Hook 統一實作

**選擇**: 單一 Node.js hook 處理所有語言

**替代方案**: 每語言獨立 Stop hook

**理由**: 減少配置複雜度，統一邏輯便於維護。Stop hook 僅做最終檢查，不執行外部工具。

### Decision 4: Debug 程式碼偵測模式

**選擇**: 正規表達式匹配

| 語言 | 偵測模式 |
|------|---------|
| JS/TS | `/console\.log/` |
| PHP | `/\b(var_dump|print_r|dd|dump|error_log|ray)\s*\(/` |
| Python | `/^(?!\s*#).*\b(print|pprint|breakpoint)\s*\(/`, `/\bpdb\./`, `/\bic\s*\(/` |

**Python 特殊處理**: 排除註解行（`^(?!\s*#)`），避免誤報文件中的範例。

## Risks / Trade-offs

**[效能影響]** 每次編輯都執行格式化和靜態分析可能拖慢回應
→ 緩解: 工具僅在配置存在時執行，且錯誤時靜默失敗不阻斷流程

**[誤報風險]** Debug 偵測可能誤報合法程式碼（如 logging 框架）
→ 緩解: 僅輸出警告訊息，不阻斷操作；限制顯示前 5 筆

**[上游同步維護]** one-liner 程式碼難以閱讀和修改
→ 緩解: 保留上游原始格式，需修改時再考慮抽成獨立腳本

**[工具版本相容]** 不同版本工具可能有不同行為
→ 緩解: 使用各工具的基本功能，避免依賴特定版本特性
