# custom-notify 設計文件

> Claude Code 通知系統 — 透過 Telegram 接收長時間任務的狀態通知

**日期：** 2026-02-26
**狀態：** 設計完成

---

## 1. 目標

讓使用者在離開電腦時，仍能透過 Telegram 接收 Claude Code 的重要事件通知：

- 任務完成
- 任務執行失敗
- 需要使用者決策（權限請求、閒置提示等）
- 工具呼叫被拒絕

## 2. 架構

### 2.1 組件

| 組件 | 位置 | 職責 |
|------|------|------|
| **Skill** | `skills/custom-notify/SKILL.md` | 提供 `/notify` 手動指令 |
| **Plugin** | `plugins/custom-notify/` | 載入 hook 自動通知 |
| **通知腳本** | `skills/custom-notify/scripts/notify.js` | 共用通知邏輯 |
| **設定檔** | `~/.config/claude-notify/config.json` | 存放 credentials |

### 2.2 資料流

```
自動通知：
  Claude Code 事件 → Hook (hooks.json) → notify.js → 讀取 config.json → Telegram API

手動通知：
  使用者 /notify → Skill → AI 呼叫 Bash → notify.js → 讀取 config.json → Telegram API
```

### 2.3 檔案結構

```
skills/custom-notify/
├── SKILL.md              # /notify 指令定義
└── scripts/
    └── notify.js         # 共用通知腳本（Node.js，使用 fetch API）

plugins/custom-notify/
├── .claude-plugin/
│   └── plugin.json       # Plugin 中繼資料
└── hooks/
    └── hooks.json        # Hook 事件設定

~/.config/claude-notify/
└── config.json           # 使用者 credentials（不進 git）
```

## 3. 設定檔格式

**路徑：** `~/.config/claude-notify/config.json`

```json
{
  "channels": {
    "telegram": {
      "enabled": true,
      "bot_token": "123456:ABC-DEF...",
      "chat_id": "-1001234567890"
    }
  },
  "events": {
    "task_complete": true,
    "task_failed": true,
    "needs_input": true,
    "tool_rejected": true
  }
}
```

- `channels` 物件結構，未來可擴展支援其他管道（Slack、Discord 等）
- `events` 讓使用者選擇性開關特定通知類型
- 整個檔案不進 git，只存在使用者本機

## 4. Hook 自動通知

### 4.1 使用的事件

| Hook 事件 | 對應需求 | stdin 關鍵欄位 | async |
|-----------|----------|----------------|-------|
| `Notification` | 需要決策、工具被拒 | `message`, `title`, `notification_type` | true |
| `Stop` | 任務完成 | `last_assistant_message`, `stop_hook_active` | true |
| `PostToolUseFailure` | 任務執行失敗 | `tool_name`, `error`, `is_interrupt` | true |

### 4.2 hooks.json 設定

```json
{
  "description": "Claude Code 通知系統 — 自動發送 Telegram 通知",
  "hooks": {
    "Notification": [
      {
        "hooks": [{
          "type": "command",
          "command": "node \"${CLAUDE_PLUGIN_ROOT}/../skills/custom-notify/scripts/notify.js\"",
          "async": true
        }]
      }
    ],
    "Stop": [
      {
        "hooks": [{
          "type": "command",
          "command": "node \"${CLAUDE_PLUGIN_ROOT}/../skills/custom-notify/scripts/notify.js\"",
          "async": true
        }]
      }
    ],
    "PostToolUseFailure": [
      {
        "hooks": [{
          "type": "command",
          "command": "node \"${CLAUDE_PLUGIN_ROOT}/../skills/custom-notify/scripts/notify.js\"",
          "async": true
        }]
      }
    ]
  }
}
```

### 4.3 stdin JSON 格式（官方文件確認）

所有 hook 共用欄位：
- `session_id` — 當前 session ID
- `transcript_path` — 對話 JSON 路徑
- `cwd` — 當前工作目錄
- `permission_mode` — 權限模式
- `hook_event_name` — 事件名稱

各事件特有欄位：

**Notification:**
```json
{
  "hook_event_name": "Notification",
  "message": "Claude needs your permission to use Bash",
  "title": "Permission needed",
  "notification_type": "permission_prompt"
}
```

**Stop:**
```json
{
  "hook_event_name": "Stop",
  "stop_hook_active": false,
  "last_assistant_message": "I've completed the refactoring..."
}
```

**PostToolUseFailure:**
```json
{
  "hook_event_name": "PostToolUseFailure",
  "tool_name": "Bash",
  "tool_input": { "command": "npm test" },
  "error": "Command exited with non-zero status code 1",
  "is_interrupt": false
}
```

## 5. Skill 手動通知

### 5.1 指令

| 指令 | 功能 |
|------|------|
| `/notify <訊息>` | 手動發送指定訊息到 Telegram |
| `/notify init` | 引導建立設定檔 |
| `/notify test` | 發送測試訊息驗證連線 |

### 5.2 SKILL.md 行為

- `/notify init`：AI 引導使用者輸入 Bot Token 和 Chat ID，寫入 config.json
- `/notify test`：AI 呼叫 `notify.js --test` 發送測試訊息
- `/notify <訊息>`：AI 呼叫 `notify.js --manual --message "<訊息>"` 發送

## 6. notify.js 腳本設計

### 6.1 執行模式

腳本支援兩種輸入方式：

1. **stdin JSON**（Hook 觸發）— 從 stdin 讀取 hook 事件資料
2. **CLI 參數**（Skill 觸發）：
   - `--test` — 發送測試訊息
   - `--manual --message "text"` — 發送手動訊息

### 6.2 核心邏輯

```
1. 讀取 ~/.config/claude-notify/config.json
2. 若設定檔不存在或 channel 未啟用 → stderr 輸出提示 → exit 0
3. 判斷輸入來源（stdin vs CLI 參數）
4. 根據 hook_event_name 對照 events 設定，過濾不需通知的事件
5. 組合 Telegram 訊息（含 emoji + 事件摘要 + 專案路徑 + 時間戳記）
6. 呼叫 Telegram Bot API（使用 Node.js 原生 fetch）
7. 成功: exit 0 / 失敗: stderr 輸出錯誤 → exit 0（不阻塞 Claude）
```

### 6.3 事件到訊息的映射

| hook_event_name | events 設定 | emoji | 訊息標題 |
|----------------|-------------|-------|----------|
| `Stop` | `task_complete` | ✅ | 任務完成 |
| `PostToolUseFailure` | `task_failed` | ❌ | 工具執行失敗 |
| `Notification` (permission_prompt) | `needs_input` | ⚠️ | 需要你的決策 |
| `Notification` (idle_prompt) | `needs_input` | 💤 | Claude 閒置中 |
| `Notification` (elicitation_dialog) | `needs_input` | ❓ | 需要回答問題 |
| 手動 (--manual) | 總是發送 | 📢 | 手動通知 |
| 測試 (--test) | 總是發送 | 🧪 | 連線測試 |

### 6.4 訊息格式

```
{emoji} Claude Code 通知

📋 事件: {事件標題}
📁 專案: {cwd 最後兩層路徑}
💬 {事件摘要，截取前 200 字}

---
⏰ {YYYY-MM-DD HH:mm:ss}
```

## 7. 安裝流程

1. 啟用 plugin：`/plugins` → 啟用 `custom-notify`
2. 執行 `/notify init` 建立設定檔
3. 執行 `/notify test` 驗證連線
4. 完成，自動通知開始運作

## 8. 設計決策

| 決策 | 選擇 | 原因 |
|------|------|------|
| Token 存放 | `~/.config/claude-notify/config.json` | 不進 git，集中管理，可擴展 |
| 腳本語言 | Node.js | 使用者偏好，原生 fetch 無需依賴 |
| Hook 執行模式 | `async: true` | 不阻塞 Claude 執行 |
| 通知管道 | 僅 Telegram | YAGNI，config 結構已預留擴展 |
| 觸發方式 | Hook + Skill 並行 | 自動 + 手動完整覆蓋 |
| 失敗處理 | 總是 exit 0 | 通知失敗不應中斷 Claude 工作 |

## 9. 不包含（YAGNI）

- 多管道實作（Slack、Discord）— config 結構已預留
- 訊息模板自訂
- 通知歷史記錄
- 通知頻率限制
- 訊息加密

## 10. 參考來源

- [Claude Code Hooks 官方文件](https://code.claude.com/docs/en/hooks)
- [Claude Code Hooks 入門指南](https://code.claude.com/docs/en/hooks-guide)
- [Claude Code Plugins 文件](https://code.claude.com/docs/en/plugins)
