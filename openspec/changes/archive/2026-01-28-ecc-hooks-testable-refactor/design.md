## Context

ecc-hooks 在 `ecc-hooks-multilang-quality` 變更中新增了 10 個程式碼品質 hooks（3 個 JS/TS + 3 個 PHP + 3 個 Python + 1 個 Stop hook）。這些 hooks 使用 Node.js one-liner 格式直接嵌入 hooks.json，導致：

1. **可測試性差**：無法對 one-liner 進行單元測試
2. **可維護性低**：JSON 字串中的程式碼難以閱讀和修改
3. **與上游不一致**：上游 everything-claude-code 已將複雜邏輯抽為獨立腳本

現有架構：
```
plugins/ecc-hooks/
├── hooks/
│   └── hooks.json          # 包含 one-liner 的配置
└── scripts/
    ├── memory-persistence/  # Python 獨立腳本（已存在）
    └── strategic-compact/   # Python 獨立腳本（已存在）
```

## Goals / Non-Goals

**Goals:**
- 將程式碼品質 hooks 重構為獨立 Node.js 腳本
- 建立 Jest 測試框架覆蓋所有獨立腳本
- 與上游 everything-claude-code 的架構保持一致
- 維持功能行為完全相同

**Non-Goals:**
- 不修改現有 Python 腳本（memory-persistence、strategic-compact）
- 不變更 hooks 的功能邏輯
- 不新增新的 hooks 功能
- 不重構 PreToolUse hooks（保持簡單的 one-liner）

## Decisions

### Decision 1: 腳本目錄結構

**選擇**: 新增 `scripts/code-quality/` 子目錄

```
plugins/ecc-hooks/
├── hooks/
│   └── hooks.json
├── scripts/
│   ├── memory-persistence/   # 現有 Python
│   ├── strategic-compact/    # 現有 Python
│   └── code-quality/         # 新增 Node.js
│       ├── format-js.js
│       ├── check-typescript.js
│       ├── warn-console-log.js
│       ├── format-php.js
│       ├── check-phpstan.js
│       ├── warn-php-debug.js
│       ├── format-python.js
│       ├── check-mypy.js
│       ├── warn-python-debug.js
│       └── check-debug-code.js  # Stop hook
└── tests/
    └── code-quality/
        ├── format-js.test.js
        └── ...
```

**替代方案**: 放在 `scripts/hooks/`（與上游相同）

**理由**: 按功能分類比按技術分類更清晰，且不與現有 Python 腳本混淆。

### Decision 2: 測試框架選擇

**選擇**: Jest

**替代方案**:
| 框架 | 優點 | 缺點 |
|------|------|------|
| Jest | 零配置、內建 mock、廣泛使用 | 較大的 bundle |
| Vitest | 更快、更小 | 較新、需額外配置 |
| Node Test Runner | 內建、無依賴 | API 較原始 |

**理由**: Jest 生態系成熟，內建 mock 功能適合測試依賴外部工具的 hooks。

### Decision 3: Mock 策略

**選擇**: Mock `child_process.execSync` 和 `fs` 模組

```javascript
// 測試範例
jest.mock('child_process', () => ({
  execSync: jest.fn()
}));
jest.mock('fs', () => ({
  existsSync: jest.fn(),
  readFileSync: jest.fn()
}));
```

**理由**: 避免依賴實際的 Prettier、tsc、PHPStan 等工具，測試可在任何環境執行。

### Decision 4: 腳本介面標準化

**選擇**: 統一的輸入/輸出格式

```javascript
// 所有腳本遵循相同模式
let data = '';
process.stdin.on('data', chunk => data += chunk);
process.stdin.on('end', () => {
  const input = JSON.parse(data);
  // ... 處理邏輯 ...
  console.log(data);  // 必須輸出原始輸入
});
```

**理由**: 與 Claude Code hook 協議一致，便於測試和維護。

### Decision 5: 錯誤處理策略

**選擇**: 靜默失敗，確保輸出原始輸入

```javascript
try {
  // ... 執行邏輯 ...
} catch (error) {
  // 靜默捕捉，不中斷流程
} finally {
  console.log(data);  // 必須輸出
}
```

**理由**: hooks 不應阻斷 Claude Code 的正常運作，工具不存在時應靜默跳過。

## Risks / Trade-offs

**[測試覆蓋範圍]** 測試 mock 外部工具可能無法覆蓋真實整合問題
→ 緩解：在 CI 中加入整合測試（需安裝對應工具）

**[維護成本增加]** 獨立腳本比 one-liner 需要更多檔案維護
→ 緩解：換取可測試性和可讀性的提升是值得的

**[路徑處理]** `${CLAUDE_PLUGIN_ROOT}` 變數在不同環境可能有差異
→ 緩解：使用相對路徑或在腳本中處理路徑解析

**[Node.js 版本相容]** 部分語法可能在舊版 Node.js 不支援
→ 緩解：使用 ES2020 語法，相容 Node.js 14+
