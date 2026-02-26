import type { Command } from "commander";

import { runUpdate } from "../core/updater";

export function registerUpdateCommand(program: Command): void {
  program
    .command("update")
    .description("Update packages and repositories")
    .option("--skip-npm", "Skip global NPM package updates")
    .option("--skip-bun", "Skip Bun package updates")
    .option("--skip-repos", "Skip repository updates")
    .option("--skip-plugins", "Skip plugin marketplace update")
    .option("--json", "Output result as JSON")
    .action(
      async (options: {
        skipNpm?: boolean;
        skipBun?: boolean;
        skipRepos?: boolean;
        skipPlugins?: boolean;
        json?: boolean;
      }) => {
        const result = await runUpdate({
          skipNpm: options.skipNpm,
          skipBun: options.skipBun,
          skipRepos: options.skipRepos,
          skipPlugins: options.skipPlugins,
          onProgress: options.json ? undefined : (msg) => console.log(msg),
        });

        if (options.json) {
          console.log(JSON.stringify(result, null, 2));
          return;
        }

        console.log("Update Summary");

        console.log(
          `- Claude Code: ${result.claudeCode.success ? "OK" : "FAIL"}${result.claudeCode.message ? ` (${result.claudeCode.message})` : ""}`,
        );

        if (result.tools.length > 0) {
          console.log("- Tool Updates:");
          for (const item of result.tools) {
            const status = item.success ? "OK" : "FAIL";
            const msg = item.message ? ` (${item.message})` : "";
            console.log(`  - ${item.name}: ${status}${msg}`);
          }
        }

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

        if (result.customRepos.length > 0) {
          console.log("- Custom Repositories:");
          for (const item of result.customRepos) {
            const status = item.success ? "OK" : "FAIL";
            const msg = item.message ? ` (${item.message})` : "";
            console.log(`  - ${item.name}: ${status}${msg}`);
          }
        }

        console.log(
          `- Plugin marketplace: ${result.plugins.success ? "OK" : "FAIL"}${result.plugins.message ? ` (${result.plugins.message})` : ""}`,
        );

        if (result.summary.updated.length > 0) {
          console.log(`- Updated repos: ${result.summary.updated.join(", ")}`);
        }
        if (result.summary.upToDate.length > 0) {
          console.log(
            `- Up-to-date repos: ${result.summary.upToDate.join(", ")}`,
          );
        }
        if (result.summary.missing.length > 0) {
          console.log(`- Missing repos: ${result.summary.missing.join(", ")}`);
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
