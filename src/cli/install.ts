import type { Command } from "commander";

import { runInstall } from "../core/installer";

export function registerInstallCommand(program: Command): void {
  program
    .command("install")
    .description("Install AI development environment")
    .option("--skip-npm", "Skip global NPM package installation")
    .option("--skip-bun", "Skip Bun package installation")
    .option("--skip-repos", "Skip repository cloning")
    .option("--skip-skills", "Skip skill distribution")
    .option("--sync-project", "Sync project template files")
    .option("--json", "Output result as JSON")
    .action(
      async (options: {
        skipNpm?: boolean;
        skipBun?: boolean;
        skipRepos?: boolean;
        skipSkills?: boolean;
        syncProject?: boolean;
        json?: boolean;
      }) => {
        const result = await runInstall({
          skipNpm: options.skipNpm,
          skipBun: options.skipBun,
          skipRepos: options.skipRepos,
          skipSkills: options.skipSkills,
          syncProject: options.syncProject,
          onProgress: options.json ? undefined : (msg) => console.log(msg),
        });

        if (options.json) {
          console.log(JSON.stringify(result, null, 2));
          return;
        }

        console.log("Install Summary");
        console.log(
          `- Prerequisites: node=${result.prerequisites.node}, git=${result.prerequisites.git}, gh=${result.prerequisites.gh}, bun=${result.prerequisites.bun}`,
        );
        console.log(
          `- Claude Code: ${result.claudeCode.installed ? "installed" : "missing"}${result.claudeCode.version ? ` (${result.claudeCode.version})` : ""}`,
        );

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

        if (result.skills.installed.length > 0) {
          console.log(
            `- Installed skills: ${result.skills.installed.join(", ")}`,
          );
        }

        if (result.skills.conflicts.length > 0) {
          console.log(
            `- Skill conflicts: ${result.skills.conflicts.join(", ")}`,
          );
        }

        if (result.npmHint) {
          console.log(`- Hint: ${result.npmHint}`);
        }

        if (result.shellCompletion.message) {
          console.log(`- Shell completion: ${result.shellCompletion.message}`);
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
