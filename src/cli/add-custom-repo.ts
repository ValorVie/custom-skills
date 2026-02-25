import { access } from "node:fs/promises";
import { homedir } from "node:os";
import { join } from "node:path";

import type { Command } from "commander";

import { addCustomRepo, parseRepoUrl } from "../utils/custom-repos";
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
    .action(
      async (
        repoInput: string,
        options: { name?: string; branch: string; clone?: boolean },
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

        await addCustomRepo(name, parsed.url, options.branch, localPath);
        console.log(`Custom repo registered: ${name}`);
      },
    );
}
