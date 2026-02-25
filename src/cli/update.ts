import type { Command } from "commander";

import { runUpdate } from "../core/updater";

export function registerUpdateCommand(program: Command): void {
  program
    .command("update")
    .description("Update packages and repositories")
    .option("--skip-npm", "Skip global NPM package updates")
    .option("--skip-bun", "Skip Bun package updates")
    .option("--skip-repos", "Skip repository updates")
    .option("--json", "Output result as JSON")
    .action(
      async (options: {
        skipNpm?: boolean;
        skipBun?: boolean;
        skipRepos?: boolean;
        json?: boolean;
      }) => {
        const result = await runUpdate({
          skipNpm: options.skipNpm,
          skipBun: options.skipBun,
          skipRepos: options.skipRepos,
          onProgress: options.json ? undefined : (msg) => console.log(msg),
        });

        if (options.json) {
          console.log(JSON.stringify(result, null, 2));
          return;
        }

        console.log("Update Summary");

        if (result.npmPackages.length > 0) {
          console.log("- NPM Packages:");
          for (const item of result.npmPackages) {
            const status = item.success ? "OK" : "FAIL";
            const msg = item.message ? ` (${item.message})` : "";
            console.log(`  - ${item.name}: ${status}${msg}`);
          }
        }

        if (result.bunPackages.length > 0) {
          console.log("- Bun Packages:");
          for (const item of result.bunPackages) {
            const status = item.success ? "OK" : "FAIL";
            const msg = item.message ? ` (${item.message})` : "";
            console.log(`  - ${item.name}: ${status}${msg}`);
          }
        }

        if (result.repos.length > 0) {
          console.log("- Repositories:");
          for (const item of result.repos) {
            const status = item.success ? "OK" : "FAIL";
            const msg = item.message ? ` (${item.message})` : "";
            console.log(`  - ${item.name}: ${status}${msg}`);
          }
        }

        if (result.errors.length > 0) {
          console.log("- Errors:");
          for (const error of result.errors) {
            console.log(`  - ${error}`);
          }
        }
      },
    );
}
