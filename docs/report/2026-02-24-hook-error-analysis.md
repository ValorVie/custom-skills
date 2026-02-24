# Claude Code Hook Error 分析報告

**日期**: 2026-02-24
**環境**: Claude Code v2.1.50 → v2.1.51, macOS Darwin 25.2.0
**Debug Log**: `85e69298-8d65-471d-abe6-98f62d2bc1f2`

---

## 症狀

啟動 Claude Code 時以及使用過程中，UI 顯示多個 hook error：

```
SessionStart:startup hook error     ×2
UserPromptSubmit hook error         ×2
PostToolUse:Read hook error         ×3（間歇性）
PostToolUse:Bash hook error         ×2（間歇性）
```

錯誤始終**成對出現**（每次 2 個），且不影響正常功能。

---

## 根本原因

**[Confirmed] 所有 hook error 均來自 `claude-mem@thedotmack` plugin (v10.4.0)**

### 證據鏈

#### 1. Hook 載入與匹配

[Source: Code] `~/.claude/debug/85e69298...txt:139-141`

```
SessionStart: Found 5 hook matchers → Matched 6 unique hooks
```

5 個 matcher 來自 4 個 plugin：

| Plugin | Hook Matcher | Commands | 結果 |
|--------|-------------|----------|------|
| auto-skill-hooks | `*` | inject-knowledge-index.py | success |
| superpowers | `startup\|resume\|clear\|compact` | run-hook.cmd session-start | success |
| ecc-hooks | `*` | session-start.py | success |
| claude-mem (1) | `startup\|clear\|compact` | smart-install.js | **error** |
| claude-mem (2) | `startup\|clear\|compact` | bun-runner start + context | **error** |

#### 2. Debug Log 確認成功的 hook

[Source: Code] `~/.claude/debug/85e69298...txt:238,254,306`

Debug log 明確記錄了 3 個成功的 SessionStart hooks，格式為 `Hook SessionStart:startup (SessionStart) success:`。
**claude-mem 的 hooks 沒有對應的 success 或 error debug 記錄** — Claude Code 對失敗的 hooks 不寫 debug entry。

#### 3. UserPromptSubmit 只有 claude-mem 有 hooks

[Source: Code] `~/.claude/plugins/cache/thedotmack/claude-mem/10.4.0/hooks/hooks.json:43-57`

```json
"UserPromptSubmit": [{
  "hooks": [
    { "command": "node bun-runner.js worker-service.cjs start" },
    { "command": "node bun-runner.js worker-service.cjs hook claude-code session-init" }
  ]
}]
```

2 個命令 = 2 個 error，與 UI 顯示完全吻合。

#### 4. PostToolUse 間歇性失敗

[Source: Code] `~/.claude/debug/85e69298...txt:546-561`

PostToolUse:Bash 在 session 開始時成功（05:58:42），返回正確的 JSON：
```json
{"continue":true,"suppressOutput":true,"status":"ready"}
{"continue":true,"suppressOutput":true}
```

但 PostToolUse:Read 在後續操作中失敗：
[Source: Code] `~/.claude/debug/85e69298...txt:4101,4266,4494` — 3 次 render 出現 `PostToolUse:Read hook error`

#### 5. 手動測試全部成功

```bash
# 所有以下測試均返回正確 JSON 且 exit code 0
CLAUDE_PLUGIN_ROOT="...10.4.0" node scripts/smart-install.js          # exit 0, no output
CLAUDE_PLUGIN_ROOT="...10.4.0" node scripts/bun-runner.js ... start    # {"continue":true,...}
CLAUDE_PLUGIN_ROOT="...10.4.0" node scripts/bun-runner.js ... context  # large JSON output
CLAUDE_PLUGIN_ROOT="...10.4.0" node scripts/bun-runner.js ... session-init  # {"continue":true,...}
```

---

## 失敗機制

### [Confirmed] 確切錯誤訊息

Session 結束時 Stop hooks 顯示了完整錯誤：

```
Stop hook error: Failed with non-blocking status code: No stderr output
```

**這揭示了所有 hook error 的共同機制：**
1. hook 程序以**非零 exit code** 退出（失敗）
2. **沒有任何 stderr 輸出**解釋失敗原因
3. Claude Code 將其歸類為 "non-blocking" 錯誤（不中斷流程，但顯示 error）

Stop hooks 的 3 個錯誤對應 claude-mem 的 3 個命令：
- `bun-runner.js worker-service.cjs start`
- `bun-runner.js worker-service.cjs hook claude-code summarize`
- `bun-runner.js worker-service.cjs hook claude-code session-complete`

### 根本觸發條件

`bun-runner.js` (Node.js) 在 `child.on('close')` 中轉發子進程 exit code：
```js
// bun-runner.js:146-148
child.on('close', (code) => {
  process.exit(code || 0);
});
```

[Source: Code] `~/.claude/plugins/cache/thedotmack/claude-mem/10.4.0/scripts/bun-runner.js:146-148`

**因此，Bun 子進程（worker-service.cjs）以非零 exit code 靜默退出。**
可能原因（按可能性排序）：

### 假設 1：Bun worker 連線失敗（最可能）

worker-service.cjs 需要連接到 HTTP worker（預設 port 37777）。
如果 worker 未啟動或啟動中：
- `start` 命令可能成功啟動 worker，但後續命令在 worker 尚未就緒時到達
- 或 worker 在某些環境下根本無法啟動
- Bun 程序靜默退出，不寫 stderr

### 假設 2：stdin 管道處理差異

`bun-runner.js:96-121` 使用 `collectStdin()` 收集 stdin，有 5 秒超時。
在 Claude Code hook runner 環境中 stdin 行為可能不同，導致 Bun 收到不完整或無效的輸入。

### 假設 3：環境變數差異

[Source: Code] `~/.claude/debug/85e69298...txt:1`
```
Failed to check enabledPlatforms: TypeError: undefined is not an object (evaluating 'pK.join')
```

Claude Code hook runner 的環境可能與使用者 shell 不同。

### 為什麼手動測試成功？

手動測試時：
- worker 已經在背景運行（被之前的成功 hook 啟動）
- stdin 來自正常的 shell pipe（非 Claude Code hook runner）
- 環境變數完整（使用者 shell profile 已載入）

---

## 附帶發現：其他啟動錯誤

| 問題 | 來源 | 影響 |
|------|------|------|
| LSP: intelephense not found | php-lsp plugin | 無 PHP 語言支援 |
| LSP: typescript-language-server not found | typescript-lsp plugin | 無 TS 語言支援 |
| LSP: rust-analyzer not found | rust-analyzer-lsp plugin | 無 Rust 語言支援 |
| `compdef:153: _comps` | zsh 補全系統 | 純裝飾性，不影響功能 |

LSP 問題是因為這些語言伺服器未全域安裝。可考慮停用不需要的 LSP plugins。

---

## 建議行動

### 短期（立即）

1. **忽略 hook errors** — 不影響功能，claude-mem 的 MCP server 仍正常運作
2. **停用不需要的 LSP plugins**：
   ```json
   // ~/.claude/settings.json → enabledPlugins
   "php-lsp@claude-plugins-official": false,
   "rust-analyzer-lsp@claude-plugins-official": false,
   "typescript-lsp@claude-plugins-official": false
   ```

### 中期

3. **回報 issue 給 claude-mem** — 關鍵資訊：
   - Error: `Failed with non-blocking status code: No stderr output`
   - Bun child process exits with non-zero code silently (no stderr)
   - Hooks fail intermittently in Claude Code hook runner
   - Works perfectly when tested manually from shell
   - PostToolUse:Bash sometimes succeeds, PostToolUse:Read consistently fails
   - Node v24.13.0, Bun 1.3.8, macOS Darwin 25.2.0, Claude Code v2.1.50

### 長期

4. **等待 claude-mem 或 Claude Code 更新** — 這可能是 hook runner 環境的已知限制

---

## 調查方法紀錄

1. 從 debug log 定位 hook 載入路徑（`Loaded hooks from standard location`）
2. 比對 `installed_plugins.json` 與實際載入版本（cache vs installed）
3. 讀取各 plugin 的 `hooks.json` 識別 hook 結構
4. 從 debug log 的 `Matched N unique hooks` 計算預期數量
5. 比對 `Hook ... success:` 數量與預期數量，確認缺少的是 claude-mem
6. 手動測試所有 hook commands 確認環境差異
7. 從 terminal render debug (`next: "..."`) 確認 UI 顯示的錯誤文字
