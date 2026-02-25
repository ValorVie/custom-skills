# 建置與驗證指令

> **適用版本**: ai-dev v2.0.0+
> **Runtime**: Bun 1.3+

---

## 一鍵驗證指令

```bash
bun test && bun run lint && bunx tsc --noEmit
```

這條指令串聯三道檢查，使用 `&&` 確保前一步成功才會繼續。任何一步失敗就會立即停止，不會浪費時間跑後續檢查。

| 順序 | 指令 | 用途 | 失敗代表什麼 |
|------|------|------|-------------|
| 1 | `bun test` | 執行所有單元/整合測試 | 邏輯錯誤、功能回退 |
| 2 | `bun run lint` | Biome 靜態分析與格式檢查 | 程式碼風格不一致、潛在問題 |
| 3 | `bunx tsc --noEmit` | TypeScript 型別檢查（不產生輸出檔） | 型別錯誤、介面不匹配 |

**建議在以下時機執行：**
- 提交前（commit 之前）
- 合併分支前（merge/PR 之前）
- 修改核心模組後

---

## 第一步：`bun test`

### 作用

使用 Bun 內建測試框架（相容 Jest API）執行 `tests/` 和 `services/**/tests/` 下所有 `*.test.ts` / `*.test.js` 檔案。

### 輸出解讀

```
tests/utils/shared.test.ts:
✓ utils/shared > NPM_PACKAGES includes OpenSpec [4.31ms]
✓ utils/shared > BUN_PACKAGES includes codex [0.14ms]
```

| 符號 | 意義 |
|------|------|
| `✓` | 測試通過 |
| `✗` | 測試失敗（會顯示錯誤詳情與 diff） |
| `»` | 測試被跳過（通常是需要外部服務的整合測試） |

### 覆蓋率報表

測試完成後會顯示覆蓋率表格：

```
---------------------------------------------------------|---------|---------|-------------------
File                                                     | % Funcs | % Lines | Uncovered Line #s
---------------------------------------------------------|---------|---------|-------------------
All files                                                |   94.67 |   93.69 |
 src/core/installer.ts                                   |  100.00 |  100.00 |
 src/core/mem-sync.ts                                    |   94.12 |   88.97 | 51,55,140,...
 src/utils/paths.ts                                      |  100.00 |  100.00 |
```

| 欄位 | 意義 |
|------|------|
| `% Funcs` | 函式覆蓋率 — 被測試呼叫過的函式比例 |
| `% Lines` | 行覆蓋率 — 被執行過的程式碼行比例 |
| `Uncovered Line #s` | 未被覆蓋的行號，可據此補寫測試 |

### 摘要行

```
 169 pass
 17 skip
 0 fail
 320 expect() calls
Ran 186 tests across 29 files. [11.27s]
```

| 欄位 | 意義 |
|------|------|
| `pass` | 通過的測試數 |
| `skip` | 跳過的測試數（標記 `»` 的項目） |
| `fail` | 失敗的測試數（**必須為 0 才算通過**） |
| `expect() calls` | 總斷言次數 |
| `Ran N tests across M files` | 測試檔案涵蓋範圍 |

### 跳過的測試

```
17 tests skipped:
» Health > GET /api/health returns ok
» Sync > POST /api/sync/push requires auth
...
```

這些是 `services/claude-mem-sync/` 的整合測試，需要啟動伺服器才能執行。在一般開發流程中跳過是正常的。如需執行，請參考 `services/claude-mem-sync/README.md`。

---

## 第二步：`bun run lint`

### 作用

執行 `package.json` 中定義的 lint 腳本：

```json
"lint": "biome check src tests package.json tsconfig.json bunfig.toml biome.json"
```

使用 [Biome](https://biomejs.dev/) 對指定檔案進行靜態分析與格式檢查，規則定義在 `biome.json`。

### 輸出解讀

**全部通過：**

```
Checked 67 files in 73ms. No fixes applied.
```

表示 67 個檔案都符合 Biome 規則，沒有問題。

**有錯誤時：**

```
src/core/mem-sync.ts:140:5 lint/style/useConst ━━━━━━━━━━━━━━━━━━━━━
  ✖ This variable is never reassigned. Use const instead.

    139 │   const db = getDb();
  > 140 │   let result = db.query(...);
        │   ^^^
    141 │   return result;

  ℹ Suggested fix: Use const instead of let
```

| 部分 | 意義 |
|------|------|
| `src/core/mem-sync.ts:140:5` | 檔案路徑:行號:列號 |
| `lint/style/useConst` | Biome 規則名稱 |
| `✖` | 問題描述 |
| `>` 標記行 | 問題所在位置 |
| `ℹ Suggested fix` | 建議的修正方式 |

### 自動修正

大部分格式問題可以自動修正：

```bash
bun run format
```

---

## 第三步：`bunx tsc --noEmit`

### 作用

執行 TypeScript 編譯器進行型別檢查，但不產生任何輸出檔案（`--noEmit`）。配置來自 `tsconfig.json`。

### 輸出解讀

**全部通過：** 沒有任何輸出，直接返回 exit code 0。

**有錯誤時：**

```
src/core/status-checker.ts(45,10): error TS2339: Property 'foo' does not exist on type 'StatusResult'.
src/utils/git.ts(12,5): error TS2322: Type 'string' is not assignable to type 'number'.
```

| 部分 | 意義 |
|------|------|
| `src/core/status-checker.ts(45,10)` | 檔案路徑(行號,列號) |
| `error TS2339` | TypeScript 錯誤代碼（可搜尋此代碼查找解法） |
| 後方訊息 | 具體的型別不匹配說明 |

### 常見 TS 錯誤代碼

| 代碼 | 意義 |
|------|------|
| `TS2339` | 物件上不存在該屬性 |
| `TS2322` | 型別不相容 |
| `TS2345` | 參數型別不匹配 |
| `TS2304` | 找不到名稱（未 import 或未宣告） |
| `TS7006` | 參數隱含 `any` 型別 |

---

## 成功標準

三道檢查全部通過的輸出看起來像這樣：

```
 169 pass                          ← 所有測試通過
 17 skip                           ← 跳過的整合測試（正常）
 0 fail                            ← 沒有失敗
Ran 186 tests across 29 files.
Checked 67 files in 73ms. No fixes applied.  ← Lint 全過
                                   ← tsc 無輸出 = 型別正確
```

**判定規則：**
- `fail` 必須為 `0`
- Biome 顯示 `No fixes applied`
- `tsc` 沒有任何錯誤輸出

三道全過後即可放心提交。
