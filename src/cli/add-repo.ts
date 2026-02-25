import { access } from "node:fs/promises";
import { homedir } from "node:os";
import { join } from "node:path";

import type { Command } from "commander";

import { addCustomRepo, parseRepoUrl } from "../utils/custom-repos";
import { runCommand } from "../utils/system";

async function pathExists(path: string): Promise<boolean> {
  try {
    await access(path);
    return true;
  } catch {
    return false;
  }
}

export function registerAddRepoCommand(program: Command): void {
  program
    .command("add-repo")
    .description("Add and optionally clone a tracked repository")
    .argument("<repo>", "GitHub repo (owner/name) or URL")
    .option("--name <name>", "Custom repo name")
    .option("--branch <branch>", "Tracked branch", "main")
    .option("--skip-clone", "Skip cloning and only register config")
    .action(
      async (
        repoInput: string,
        options: { name?: string; branch: string; skipClone?: boolean },
      ) => {
        const parsed = parseRepoUrl(repoInput);
        const name = options.name ?? parsed.name;
        const localPath = join(homedir(), ".config", name);

        if (!options.skipClone) {
          if (!(await pathExists(localPath))) {
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
        }

        await addCustomRepo(name, parsed.url, options.branch, localPath);
        console.log(`Tracked repo added: ${name} (${parsed.repoPath})`);
      },
    );
}
