---
name: custom-notify
description: 發送通知到 Telegram。支援手動發送、初始化設定、測試連線。長時間任務時搭配 plugin hooks 自動通知。
---

# custom-notify — Claude Code 通知系統

透過 Telegram 接收 Claude Code 的重要事件通知。

## 指令

### `/notify init` — 初始化設定

引導使用者建立通知設定檔。

**步驟：**

1. 請使用者提供 Telegram Bot Token（從 @BotFather 取得）
2. 請使用者提供 Chat ID（可用 @userinfobot 取得）
3. 將設定寫入 `~/.config/claude-notify/config.json`：

```json
{
  "channels": {
    "telegram": {
      "enabled": true,
      "bot_token": "<使用者提供的 token>",
      "chat_id": "<使用者提供的 chat_id>"
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

4. 建立完成後，自動執行 `/notify test` 驗證連線

**注意：** 確保目錄存在：`mkdir -p ~/.config/claude-notify`

### `/notify test` — 測試連線

執行以下命令發送測試訊息：

```bash
node "<skill_path>/scripts/notify.js" --test
```

- 成功：告知使用者「測試訊息已發送，請檢查 Telegram」
- 失敗：顯示錯誤訊息並協助排查

### `/notify <訊息>` — 手動發送通知

當使用者輸入 `/notify` 後面接任何文字時，發送該文字作為通知：

```bash
node "<skill_path>/scripts/notify.js" --manual --message "<使用者的訊息>"
```

**範例：**
- `/notify 部署完成，請來檢查`
- `/notify 測試全部通過`

### `/notify config` — 查看目前設定

讀取並顯示 `~/.config/claude-notify/config.json` 的內容（隱藏 bot_token 的中間部分）。

### `/notify toggle <event>` — 開關事件通知

修改 `~/.config/claude-notify/config.json` 中的 `events` 設定。

可用的 event 名稱：
- `task_complete` — 任務完成通知
- `task_failed` — 工具執行失敗通知
- `needs_input` — 需要使用者決策通知
- `tool_rejected` — 工具被拒絕通知

**範例：** `/notify toggle task_complete` — 切換任務完成通知的開關狀態

## 自動通知

自動通知由 `plugins/custom-notify` plugin 處理，監聽以下 Claude Code hook 事件：

| 事件 | 觸發時機 |
|------|----------|
| `Notification` | 需要權限、閒置提示、需要回答問題 |
| `Stop` | Claude 完成回應 |
| `PostToolUseFailure` | 工具執行失敗 |

啟用方式：在 Claude Code 中執行 `/plugins` → 啟用 `custom-notify`。

## 腳本路徑

通知腳本位於：`skills/custom-notify/scripts/notify.js`

使用 `<skill_path>` 代表此 skill 的根目錄路徑。在執行命令時，用實際的絕對路徑替換。
