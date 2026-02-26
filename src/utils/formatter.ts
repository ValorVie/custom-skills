import chalk from "chalk";
import Table from "cli-table3";
import ora, { type Ora } from "ora";

export function printTable(headers: string[], rows: string[][]): void {
  const table = new Table({ head: headers });
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
