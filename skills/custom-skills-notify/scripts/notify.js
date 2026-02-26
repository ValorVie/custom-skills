#!/usr/bin/env node

/**
 * custom-notify — Claude Code 通知腳本
 *
 * 使用方式：
 *   Hook 模式：stdin 接收 JSON（由 Claude Code hook 自動觸發）
 *   CLI 模式：
 *     --test                     發送測試訊息
 *     --manual --message "text"  發送手動訊息
 */

const fs = require("fs");
const path = require("path");

const CONFIG_PATH = path.join(
  process.env.HOME || process.env.USERPROFILE || "~",
  ".config",
  "claude-notify",
  "config.json"
);

// 事件映射：hook_event_name + notification_type → 設定 key、emoji、標題
const EVENT_MAP = {
  Stop: {
    configKey: "task_complete",
    emoji: "✅",
    title: "任務完成",
  },
  PostToolUseFailure: {
    configKey: "task_failed",
    emoji: "❌",
    title: "工具執行失敗",
  },
  "Notification:permission_prompt": {
    configKey: "needs_input",
    emoji: "⚠️",
    title: "需要你的決策",
  },
  "Notification:idle_prompt": {
    configKey: "needs_input",
    emoji: "💤",
    title: "Claude 閒置中",
  },
  "Notification:elicitation_dialog": {
    configKey: "needs_input",
    emoji: "❓",
    title: "需要回答問題",
  },
  "Notification:auth_success": {
    configKey: "needs_input",
    emoji: "🔑",
    title: "認證成功",
  },
};

function loadConfig() {
  try {
    const raw = fs.readFileSync(CONFIG_PATH, "utf-8");
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

function formatPath(cwd) {
  if (!cwd) return "unknown";
  return cwd;
}

function truncate(text, maxLen = 200) {
  if (!text) return "";
  return text.length > maxLen ? text.slice(0, maxLen) + "..." : text;
}

function buildMessage(eventInfo, detail, cwd) {
  const now = new Date()
    .toLocaleString("zh-TW", {
      timeZone: "Asia/Taipei",
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: false,
    })
    .replace(/\//g, "-");

  const lines = [
    `${eventInfo.emoji} Claude Code 通知`,
    "",
    `📋 事件: ${eventInfo.title}`,
    `📁 專案: ${formatPath(cwd)}`,
  ];

  if (detail) {
    lines.push(`💬 ${truncate(detail)}`);
  }

  lines.push("", "---", `⏰ ${now}`);

  return lines.join("\n");
}

function extractDetail(hookData) {
  const event = hookData.hook_event_name;

  if (event === "Stop") {
    const msg = hookData.last_assistant_message;
    if (!msg) return "Claude 已完成回應";
    return truncate(msg, 2000);
  }

  if (event === "PostToolUseFailure") {
    const tool = hookData.tool_name || "unknown";
    const error = hookData.error || "未知錯誤";
    return `${tool}: ${error}`;
  }

  if (event === "Notification") {
    return hookData.message || hookData.title || "收到通知";
  }

  return null;
}

function resolveEventInfo(hookData) {
  const event = hookData.hook_event_name;

  if (event === "Notification" && hookData.notification_type) {
    const key = `${event}:${hookData.notification_type}`;
    if (EVENT_MAP[key]) return EVENT_MAP[key];
  }

  if (EVENT_MAP[event]) return EVENT_MAP[event];

  // 未知事件仍發送
  return { configKey: null, emoji: "🔔", title: event };
}

function isEventEnabled(config, configKey) {
  if (!configKey) return true; // 未知事件預設發送
  const events = config.events || {};
  return events[configKey] !== false; // 預設啟用
}

async function sendTelegram(botToken, chatId, text) {
  const url = `https://api.telegram.org/bot${botToken}/sendMessage`;
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      chat_id: chatId,
      text,
    }),
  });

  if (!res.ok) {
    const body = await res.text();
    throw new Error(`Telegram API error ${res.status}: ${body}`);
  }
}

async function sendDiscord(webhookUrl, text) {
  // Discord content 上限 2000 字元
  const content = text.length > 2000 ? text.slice(0, 1997) + "..." : text;
  const res = await fetch(webhookUrl, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content }),
  });

  if (!res.ok) {
    const body = await res.text();
    throw new Error(`Discord API error ${res.status}: ${body}`);
  }
}

async function sendToAllChannels(config, text) {
  const errors = [];

  // Telegram
  const telegram = config.channels?.telegram;
  if (telegram?.enabled && telegram?.bot_token && telegram?.chat_id) {
    try {
      await sendTelegram(telegram.bot_token, telegram.chat_id, text);
    } catch (err) {
      errors.push(`Telegram: ${err.message}`);
    }
  }

  // Discord
  const discord = config.channels?.discord;
  if (discord?.enabled && discord?.webhook_url) {
    try {
      await sendDiscord(discord.webhook_url, text);
    } catch (err) {
      errors.push(`Discord: ${err.message}`);
    }
  }

  if (errors.length > 0) {
    throw new Error(errors.join("; "));
  }
}

function hasAnyChannel(config) {
  const telegram = config.channels?.telegram;
  const discord = config.channels?.discord;
  const hasTelegram =
    telegram?.enabled && telegram?.bot_token && telegram?.chat_id;
  const hasDiscord = discord?.enabled && discord?.webhook_url;
  return hasTelegram || hasDiscord;
}

async function handleHookMode(hookData) {
  const config = loadConfig();
  if (!config) {
    process.stderr.write(
      "[custom-notify] 設定檔不存在，請執行 /custom-skills-notify init\n"
    );
    return;
  }

  if (!hasAnyChannel(config)) {
    process.stderr.write("[custom-notify] 沒有啟用任何通知頻道\n");
    return;
  }

  const eventInfo = resolveEventInfo(hookData);

  if (!isEventEnabled(config, eventInfo.configKey)) {
    return; // 使用者停用了這個事件類型
  }

  const detail = extractDetail(hookData);
  const message = buildMessage(eventInfo, detail, hookData.cwd);

  await sendToAllChannels(config, message);
}

function requireConfig() {
  const config = loadConfig();
  if (!config) {
    process.stderr.write(
      `[custom-notify] 設定檔不存在: ${CONFIG_PATH}\n請執行 /custom-skills-notify init 建立設定檔\n`
    );
    process.exit(1);
  }

  if (!hasAnyChannel(config)) {
    process.stderr.write(
      "[custom-notify] 沒有啟用任何通知頻道，請執行 /custom-skills-notify init\n"
    );
    process.exit(1);
  }

  return config;
}

async function handleTestMode() {
  const config = requireConfig();

  const message = buildMessage(
    { emoji: "🧪", title: "連線測試" },
    "這是一則測試訊息，如果你看到了就代表設定正確！",
    process.cwd()
  );

  await sendToAllChannels(config, message);
  process.stderr.write("[custom-notify] 測試訊息已發送！\n");
}

async function handleManualMode(text) {
  const config = requireConfig();

  const message = buildMessage(
    { emoji: "📢", title: "手動通知" },
    text,
    process.cwd()
  );

  await sendToAllChannels(config, message);
  process.stderr.write("[custom-notify] 訊息已發送！\n");
}

async function main() {
  const args = process.argv.slice(2);

  // CLI 模式
  if (args.includes("--test")) {
    await handleTestMode();
    return;
  }

  if (args.includes("--manual")) {
    const msgIdx = args.indexOf("--message");
    const text =
      msgIdx !== -1 && args[msgIdx + 1] ? args[msgIdx + 1] : "（無訊息內容）";
    await handleManualMode(text);
    return;
  }

  // Hook 模式：從 stdin 讀取 JSON
  let data = "";
  process.stdin.setEncoding("utf-8");

  await new Promise((resolve) => {
    process.stdin.on("data", (chunk) => {
      data += chunk;
    });
    process.stdin.on("end", resolve);

    // 如果 stdin 已經結束（非 pipe 模式）
    if (process.stdin.isTTY) {
      resolve();
    }
  });

  if (!data.trim()) {
    process.stderr.write("[custom-notify] 無 stdin 資料且無 CLI 參數\n");
    return;
  }

  let hookData;
  try {
    hookData = JSON.parse(data);
  } catch {
    process.stderr.write("[custom-notify] 無法解析 stdin JSON\n");
    return;
  }

  await handleHookMode(hookData);
}

main().catch((err) => {
  process.stderr.write(`[custom-notify] 錯誤: ${err.message}\n`);
  process.exit(0); // 通知失敗不阻塞 Claude
});
