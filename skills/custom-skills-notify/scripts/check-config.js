#!/usr/bin/env node

/**
 * custom-skills-notify — SessionStart 設定檢查
 *
 * 檢查 config.json 是否存在且完整，若未設定則輸出提醒。
 */

const fs = require("fs");
const path = require("path");

const CONFIG_PATH = path.join(
  process.env.HOME || process.env.USERPROFILE || "~",
  ".config",
  "claude-notify",
  "config.json"
);

function check() {
  try {
    const raw = fs.readFileSync(CONFIG_PATH, "utf-8");
    const config = JSON.parse(raw);
    const telegram = config.channels?.telegram;

    if (!telegram?.bot_token || !telegram?.chat_id) {
      console.log(
        "⚠️ custom-skills-notify Telegram 設定不完整，請執行 /custom-skills-notify init 完成設定"
      );
      return;
    }

    if (!telegram?.enabled) {
      console.log(
        "ℹ️ custom-skills-notify Telegram 通知已停用，如需啟用請執行 /custom-skills-notify config"
      );
      return;
    }

    // 設定完整，靜默通過
  } catch {
    console.log(
      "⚠️ custom-skills-notify 尚未設定，請執行 /custom-skills-notify init 完成 Telegram 設定"
    );
  }
}

check();
