import { readdir, readFile } from "node:fs/promises";
import { basename, extname, join, resolve } from "node:path";

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
          console.error(`Error: 路徑不存在: ${path}`);
          process.exitCode = 1;
          return;
        }
        throw error;
      }

      if (files.length === 0) {
        console.error(`No markdown spec files found at: ${path}`);
        process.exitCode = 1;
        return;
      }

      for (const filePath of files.sort((a, b) => a.localeCompare(b))) {
        const content = await readFile(filePath, "utf8");
        const displayPath = resolve(filePath) || basename(filePath);
        console.log(`\n--- ${displayPath} ---\n`);
        console.log(content);
      }
    });
}
