import type { Command } from "commander";

import { runInstall } from "../core/installer";

export function registerInstallCommand(program: Command): void {
  program
    .command("install")
    .description("Install AI development environment")
    .option("--skip-npm", "Skip global NPM package installation")
    .option("--skip-bun", "Skip Bun package installation")
    .option("--skip-repos", "Skip repository cloning")
    .option("--json", "Output result as JSON")
    .action(
      async (options: {
        skipNpm?: boolean;
        skipBun?: boolean;
        skipRepos?: boolean;
        json?: boolean;
      }) => {
        const result = await runInstall({
          skipNpm: options.skipNpm,
          skipBun: options.skipBun,
          skipRepos: options.skipRepos,
        });

        if (options.json) {
          console.log(JSON.stringify(result, null, 2));
          return;
        }

        console.log("Install Summary");
        console.log(
          `- Prerequisites: node=${result.prerequisites.node}, git=${result.prerequisites.git}, bun=${result.prerequisites.bun}`,
        );

        if (result.npmPackages.length > 0) {
          console.log("- NPM Packages:");
          for (const item of result.npmPackages) {
            console.log(`  - ${item.name}: ${item.success ? "OK" : "FAIL"}`);
          }
        }

        if (result.bunPackages.length > 0) {
          console.log("- Bun Packages:");
          for (const item of result.bunPackages) {
            console.log(`  - ${item.name}: ${item.success ? "OK" : "FAIL"}`);
          }
        }

        if (result.repos.length > 0) {
          console.log("- Repositories:");
          for (const item of result.repos) {
            const message = item.message ? ` (${item.message})` : "";
            console.log(
              `  - ${item.name}: ${item.success ? "OK" : "FAIL"}${message}`,
            );
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
