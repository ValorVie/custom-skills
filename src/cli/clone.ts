import type { Command } from "commander";

import { runInstall } from "../core/installer";

export function registerCloneCommand(program: Command): void {
  program
    .command("clone")
    .description("Clone required repositories without package installation")
    .option("--json", "Output result as JSON")
    .action(async (options: { json?: boolean }) => {
      const result = await runInstall({
        skipNpm: true,
        skipBun: true,
        skipRepos: false,
      });

      if (options.json) {
        console.log(JSON.stringify(result, null, 2));
        return;
      }

      console.log("Clone Summary");
      for (const repo of result.repos) {
        const message = repo.message ? ` (${repo.message})` : "";
        console.log(
          `- ${repo.name}: ${repo.success ? "OK" : "FAIL"}${message}`,
        );
      }
      if (result.errors.length > 0) {
        for (const error of result.errors) {
          console.log(`- error: ${error}`);
        }
      }
    });
}
