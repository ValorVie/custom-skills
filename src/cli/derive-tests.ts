import { readdir, readFile } from "node:fs/promises";
import { basename, dirname, extname, join, resolve } from "node:path";

import type { Command } from "commander";

import { t } from "../utils/i18n";

async function collectMarkdownFiles(path: string): Promise<string[]> {
  const stats = await Bun.file(path).stat();

  if (stats.isFile() && extname(path) === ".md") {
    return [path];
  }

  if (!stats.isDirectory()) {
    return [];
  }

  const entries = await readdir(path, { withFileTypes: true });
  const files: string[] = [];

  for (const entry of entries) {
    const fullPath = join(path, entry.name);
    if (entry.isDirectory()) {
      files.push(...(await collectMarkdownFiles(fullPath)));
      continue;
    }
    if (entry.isFile() && extname(entry.name) === ".md") {
      files.push(fullPath);
    }
  }

  return files;
}

function shouldUseColor(): boolean {
  if (process.env.NO_COLOR) {
    return false;
  }

  const forced = process.env.FORCE_COLOR ?? process.env.CLICOLOR_FORCE ?? "0";
  return forced !== "0";
}

function formatDisplayPath(path: string): string {
  if (!shouldUseColor()) {
    return path;
  }

  const base = basename(path);
  const dir = dirname(path);

  if (!dir || dir === ".") {
    return `\u001b[95m${base}\u001b[0m`;
  }

  if (dir === "/") {
    return `\u001b[35m/\u001b[0m\u001b[95m${base}\u001b[0m`;
  }

  return `\u001b[35m${dir}/\u001b[0m\u001b[95m${base}\u001b[0m`;
}

export function registerDeriveTestsCommand(program: Command): void {
  program
    .command("derive-tests")
    .description(t("cmd.derive_tests"))
    .argument("<path>", "Spec file or directory")
    .action(async (path: string) => {
      let files: string[] = [];
      try {
        files = await collectMarkdownFiles(path);
      } catch (error) {
        if (
          error &&
          typeof error === "object" &&
          "code" in error &&
          error.code === "ENOENT"
        ) {
          process.stderr.write(`Error: 路徑不存在: ${path}\n`);
          process.exitCode = 1;
          return;
        }
        throw error;
      }

      if (files.length === 0) {
        process.stderr.write(`No markdown spec files found at: ${path}\n`);
        process.exitCode = 1;
        return;
      }

      for (const filePath of files.sort((a, b) => a.localeCompare(b))) {
        const content = await readFile(filePath, "utf8");
        const displayPath = resolve(filePath) || basename(filePath);
        console.log(`\n--- ${formatDisplayPath(displayPath)} ---\n`);
        console.log(content);
      }
    });
}
