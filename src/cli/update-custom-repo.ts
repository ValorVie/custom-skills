import { access } from "node:fs/promises";

import type { Command } from "commander";

import { loadCustomRepos } from "../utils/custom-repos";
import { runCommand } from "../utils/system";

export function registerUpdateCustomRepoCommand(program: Command): void {
  program
    .command("update-custom-repo")
    .description("Update all custom repositories")
    .action(async () => {
      const config = await loadCustomRepos();
      const entries = Object.entries(config.repos);

      if (entries.length === 0) {
        console.log("No custom repositories configured.");
        return;
      }

      for (const [name, repo] of entries) {
        try {
          await access(`${repo.localPath}/.git`);
        } catch {
          console.log(`- ${name}: skipped (not cloned)`);
          continue;
        }

        const pull = await runCommand(
          ["git", "-C", repo.localPath, "pull", "origin", repo.branch],
          {
            check: false,
          },
        );
        console.log(`- ${name}: ${pull.exitCode === 0 ? "OK" : "FAIL"}`);
      }
    });
}
