import chalk from "chalk";

export function formatProgress(msg: string): void {
  if (msg.trim().length === 0) {
    console.log("");
    return;
  }

  // 標題: "開始安裝..." / "開始更新..." / "檢查..."
  if (msg.startsWith("開始") || msg.startsWith("檢查")) {
    console.log(chalk.bold.blue(msg));
    return;
  }

  // 計數器: "[1/6] 正在安裝..."
  const counterMatch = msg.match(/^\[(\d+)\/(\d+)\]\s+(.+)$/);
  if (counterMatch) {
    console.log(
      `${chalk.bold.cyan(`[${counterMatch[1]}/${counterMatch[2]}]`)} ${counterMatch[3]}`,
    );
    return;
  }

  // Clone/更新: "Cloning..." / "正在..."
  if (msg.startsWith("Cloning") || msg.startsWith("正在")) {
    console.log(chalk.green(msg));
    return;
  }

  // 警告: "⚠" 開頭
  if (msg.startsWith("⚠")) {
    console.log(chalk.yellow(msg));
    return;
  }

  // 跳過
  if (msg.startsWith("跳過")) {
    console.log(chalk.dim(msg));
    return;
  }

  // 提示/資訊
  if (msg.startsWith("提示") || msg.startsWith("ℹ")) {
    console.log(chalk.dim(msg));
    return;
  }

  // 成功 / 完成
  if (msg.startsWith("✓") || msg.includes("完成")) {
    console.log(chalk.bold.green(msg));
    return;
  }

  // 列表項: "  • xxx"
  if (msg.trimStart().startsWith("•")) {
    console.log(chalk.cyan(msg));
    return;
  }

  // 其他
  console.log(chalk.dim(msg));
}
