# FileGuard — 路徑存取控制 Plugin 設計文件

> Date: 2026-03-13
> Status: Draft

## 概述

FileGuard 是一個 Claude Code plugin，透過 PreToolUse hook 攔截工具呼叫，根據路徑規則阻止 AI 存取特定檔案或目錄。採用防火牆模型（first-match-wins），支援 deny/allow 混合規則。

## Plugin 結構

```
plugins/fileguard/
├── .claude-plugin/
│   └── plugin.json
├── hooks/
│   └── hooks.json
├── scripts/
│   └── fileguard.py          # 主攔截邏輯（純 stdlib）
├── fileguard-rules.json      # 規則設定檔
└── README.md
```

## 攔截範圍

### 攔截工具

| 工具 | 路徑來源 | 可靠度 |
|------|----------|--------|
| Read | `tool_input.file_path` | 高 — 絕對路徑 |
| Write | `tool_input.file_path` | 高 — 絕對路徑 |
| Edit | `tool_input.file_path` | 高 — 絕對路徑 |
| Grep | `tool_input.path`（可選，空值取 `cwd`） | 高 — 正規化後比對 |
| Glob | `tool_input.path`（可選，空值取 `cwd`） | 高 — 正規化後比對 |
| Bash | `tool_input.command`（字串） | 中 — 明文路徑可攔截 |

### 不攔截

- Agent（路徑藏在自然語言 prompt 中，無法可靠提取；子代理的工具呼叫仍會觸發 hook）
- MCP 工具（各有不同 schema，不在本版範圍）

## hooks.json

```json
{
  "description": "FileGuard - Path-based access control for Claude Code",
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Read|Write|Edit|Grep|Glob|Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/scripts/fileguard.py\"",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

## 規則設定檔 `fileguard-rules.json`

### 格式

```json
{
  "rules": [
    {
      "action": "deny",
      "pattern": "/Users/arlen/.ssh",
      "type": "directory",
      "reason": "SSH private keys"
    },
    {
      "action": "deny",
      "pattern": "\\.env($|\\.)",
      "type": "regex",
      "reason": "Environment secrets"
    },
    {
      "action": "deny",
      "pattern": "\\.pem$",
      "type": "regex",
      "reason": "Certificate private keys"
    },
    {
      "action": "allow",
      "pattern": "/Users/arlen/.config/claude",
      "type": "directory",
      "reason": "Claude config is safe to access"
    }
  ],
  "default": "allow"
}
```

### 欄位定義

| 欄位 | 說明 |
|------|------|
| `action` | `deny` 或 `allow` |
| `pattern` | 路徑字串或正則表達式 |
| `type` | `directory`（前綴匹配）、`file`（完全匹配）、`regex`（正則匹配） |
| `reason` | 攔截時顯示的原因說明 |
| `default` | 所有規則都未命中時的預設行為（`allow` 或 `deny`） |

### 匹配模型

**防火牆模型（first-match-wins）：** 規則按陣列順序逐條評估，第一條命中即決定結果，不再往下。全未命中則套用 `default`。

## fileguard.py 核心流程

```
stdin (JSON)
    │
    ├─ 解析 tool_name, tool_input, cwd
    │
    ├─ 硬編碼保護（不可繞過）：
    │   ├─ 保護 .disable-fileguard
    │   ├─ 保護整個 ${CLAUDE_PLUGIN_ROOT} 目錄
    │   │
    │   ├─ Read/Write/Edit → file_path 包含保護路徑 → deny
    │   ├─ Grep/Glob → path 或 pattern 包含保護路徑 → deny
    │   └─ Bash → command 包含保護路徑 → deny
    │
    ├─ 檢查 .disable-fileguard 是否存在於 cwd
    │   └─ 存在 → exit 0（全部放行）
    │
    ├─ 載入 fileguard-rules.json
    │   └─ 失敗（不存在或 JSON 無效）→ deny all
    │      輸出: "[FileGuard] ⚠️ fileguard-rules.json 不存在，
    │             所有路徑存取被拒絕。請手動建立規則檔或
    │             touch .disable-fileguard 停用保護。"
    │
    ├─ 提取路徑：
    │   ├─ Read/Write/Edit → file_path
    │   ├─ Grep/Glob → path（空值取 cwd）
    │   └─ Bash → command 字串（不做路徑正規化）
    │
    ├─ 路徑正規化（非 Bash）：
    │   ├─ 相對路徑 → os.path.join(cwd, path)
    │   ├─ realpath（解析 ../、符號連結）
    │   └─ 統一轉小寫（macOS 大小寫不敏感）
    │
    ├─ 防火牆匹配（first match wins）：
    │   │
    │   │ 【非 Bash 工具】正規化後的路徑逐條比對：
    │   │   ├─ directory → path.startswith(pattern)
    │   │   ├─ file → path == pattern
    │   │   └─ regex → re.search(pattern, path)
    │   │
    │   │ 【Bash】對 command 字串做匹配（大小寫不敏感）：
    │   │   ├─ directory → pattern in command（子字串搜尋）
    │   │   ├─ file → pattern in command（子字串搜尋）
    │   │   └─ regex → re.search(pattern, command, re.IGNORECASE)
    │   │
    │   ├─ 命中 allow → exit 0
    │   ├─ 命中 deny → 輸出 deny JSON，exit 2
    │   └─ 全未命中 → 套用 default
    │
    ├─ 錯誤處理：
    │   ├─ stdin 非合法 JSON → exit 0（放行，避免阻斷正常操作）
    │   ├─ tool_input 缺少預期欄位 → exit 0（非目標工具呼叫）
    │   └─ 規則檔案 JSON 格式錯誤 → deny all（同檔案不存在處理）
    │
    └─ 結束
```

## 輸出格式

### 攔截（exit 2）

```json
{
  "hookSpecificOutput": {
    "permissionDecision": "deny"
  },
  "systemMessage": "[FileGuard] 🚫 存取被拒絕\n路徑: /Users/arlen/.ssh/id_rsa\n規則: SSH private keys"
}
```

### 硬編碼攔截（exit 2）

```json
{
  "hookSpecificOutput": {
    "permissionDecision": "deny"
  },
  "systemMessage": "[FileGuard] 🔒 系統保護檔案，禁止存取"
}
```

### Rules 載入失敗（exit 2）

```json
{
  "hookSpecificOutput": {
    "permissionDecision": "deny"
  },
  "systemMessage": "[FileGuard] ⚠️ fileguard-rules.json 不存在，所有路徑存取被拒絕。請手動建立規則檔或 touch .disable-fileguard 停用保護。"
}
```

### 放行

`exit 0`，不輸出任何內容。

## 停用機制

在專案目錄下建立 `.disable-fileguard` flag 檔案：

```bash
touch .disable-fileguard    # 停用 FileGuard
rm .disable-fileguard       # 恢復保護
```

- `.disable-fileguard` 本身受硬編碼保護，AI 無法建立、刪除或讀取此檔案
- 只能由使用者在自己的終端機手動操作

## 已知限制

### Bash 攔截邊界

**可攔截（路徑明文出現在 command 字串中）：**
- `cat /secret/file.txt`
- `cat $(echo /secret/file.txt)`
- `cd /secret && ls`
- `grep "keyword" /secret/file`
- `cp /secret/a.txt /tmp/`
- `echo "data" > /secret/file`
- 含空白的引號路徑 `cat "/my secret/file"`

**無法攔截（路徑不以明文存在）：**
- 變數間接引用：`p="/secret"; cat $p`
- 檔案讀取路徑：`cat $(head -1 paths.txt)`
- 編碼繞過：`echo L3NlY3JldA== | base64 -d | xargs cat`
- 環境變數：`cat $SECRET_PATH`
- eval 拼接：`eval "cat /sec" + "ret/file"`
- 萬用字元展開：`cat /sec*/file`（若規則是完整路徑 `/secret`）

### 其他限制

- **python3 不存在**：hook command 執行失敗，Claude Code 視為非阻斷錯誤，靜默放行。FileGuard 需要 python3 作為執行前提。
- **Bash 中的符號連結**：命令字串中的符號連結路徑無法被 `realpath` 解析，只能做字串匹配。
- **Agent 子代理**：Agent 本身的 prompt 無法攔截路徑，但子代理內的工具呼叫（Read/Write 等）會正常觸發 hook 攔截。
- **MCP 工具**：不在本版攔截範圍，各 MCP 工具有不同的 input schema。
- **Hook 熱更新**：hooks.json 修改後需重啟 Claude Code 才生效。
