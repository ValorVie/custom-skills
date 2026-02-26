import { access } from "node:fs/promises";
import { homedir } from "node:os";
import { join } from "node:path";

import type { Command } from "commander";

import {
  fixRepoStructure,
  validateRepoStructure,
} from "../core/custom-repo-manager";
import { addCustomRepo, parseRepoUrl } from "../utils/custom-repos";
import { printSuccess, printTable, printWarning } from "../utils/formatter";
import { t } from "../utils/i18n";
import { runCommand } from "../utils/system";

async function exists(path: string): Promise<boolean> {
  try {
    await access(path);
    return true;
  } catch {
    return false;
  }
}

export function registerAddCustomRepoCommand(program: Command): void {
  program
    .command("add-custom-repo")
    .description("Add custom repository to ~/.config/ai-dev/repos.yaml")
    .argument("<repo>", "GitHub repo (owner/name) or URL")
    .option("--name <name>", "Custom repo name")
    .option("--branch <branch>", "Tracked branch", "main")
    .option("--no-clone", "Do not clone repository before registering")
    .option("--fix", "Create missing standard directories")
    .action(
      async (
        repoInput: string,
        options: {
          name?: string;
          branch: string;
          clone?: boolean;
          fix?: boolean;
        },
      ) => {
        const parsed = parseRepoUrl(repoInput);
        const name = options.name ?? parsed.name;
        const localPath = join(homedir(), ".config", name);

        if (options.clone !== false && !(await exists(localPath))) {
          const clone = await runCommand(
            ["git", "clone", parsed.url, localPath],
            {
              check: false,
            },
          );
          if (clone.exitCode !== 0) {
            console.error(`Clone failed: ${clone.stderr}`);
            process.exitCode = 1;
            return;
          }
        }

        let validation = await validateRepoStructure(localPath);
        let fixedDirs: string[] = [];

        if (!validation.valid && options.fix) {
          const fixed = await fixRepoStructure(localPath);
          fixedDirs = fixed.created;
          validation = await validateRepoStructure(localPath);
        }

        await addCustomRepo(name, parsed.url, options.branch, localPath);

        printSuccess(t("add_custom.added", { name }));
        printTable(
          ["Field", "Value"],
          [
            ["Repository", parsed.repoPath],
            ["Branch", options.branch],
            ["Path", localPath],
            ["Structure valid", String(validation.valid)],
          ],
        );

        if (fixedDirs.length > 0) {
          printWarning(
            t("add_custom.created_dirs", { dirs: fixedDirs.join(", ") }),
          );
        }

        if (validation.missing.length > 0) {
          printWarning(
            t("add_custom.missing_dirs", {
              dirs: validation.missing.join(", "),
            }),
          );
        }
      },
    );
}
