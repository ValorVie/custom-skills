import chalk from "chalk";
import Table from "cli-table3";
import ora, { type Ora } from "ora";

const RICH_CHARS: Table.TableConstructorOptions["chars"] = {
  top: "━",
  "top-mid": "┳",
  "top-left": "┏",
  "top-right": "┓",
  bottom: "━",
  "bottom-mid": "┻",
  "bottom-left": "┗",
  "bottom-right": "┛",
  left: "┃",
  "left-mid": "┣",
  mid: "━",
  "mid-mid": "╋",
  right: "┃",
  "right-mid": "┫",
  middle: "┃",
};

export interface TableOptions {
  title?: string;
}

export function printTable(
  headers: string[],
  rows: string[][],
  options?: TableOptions,
): void {
  if (options?.title) {
    console.log(chalk.bold(options.title));
  }

  const table = new Table({
    head: headers,
    chars: RICH_CHARS,
    style: { head: ["bold"] },
  });

  for (const row of rows) {
    table.push(row);
  }

  console.log(table.toString());
}

export function printSuccess(message: string): void {
  console.log(chalk.green(`✓ ${message}`));
}

export function printError(message: string): void {
  console.log(chalk.red(`✗ ${message}`));
}

export function printWarning(message: string): void {
  console.log(chalk.yellow(`! ${message}`));
}

export function createSpinner(text: string): Ora {
  return ora({ text });
}

export function printPanel(title: string, content: string): void {
  const lines = content.split(/\r?\n/);
  const width = Math.max(title.length, ...lines.map((line) => line.length));
  const border = `+${"-".repeat(width + 2)}+`;

  console.log(border);
  console.log(`| ${title.padEnd(width)} |`);
  console.log(border);

  for (const line of lines) {
    console.log(`| ${line.padEnd(width)} |`);
  }

  console.log(border);
}
