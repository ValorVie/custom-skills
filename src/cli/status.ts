import type { Command } from "commander";

import { checkEnvironment } from "../core/status-checker";

function mark(installed: boolean): string {
  return installed ? "OK" : "MISSING";
}

export function registerStatusCommand(program: Command): void {
  program
    .command("status")
    .description("Check environment status")
    .option("--json", "Output status as JSON")
    .action(async (options: { json?: boolean }) => {
      const status = await checkEnvironment();

      if (options.json) {
        console.log(JSON.stringify(status, null, 2));
        return;
      }

      console.log("Core Tools");
      console.log(
        `- Git: ${mark(status.git.installed)} ${status.git.version ?? ""}`.trim(),
      );
      console.log(
        `- Node: ${mark(status.node.installed)} ${status.node.version ?? ""}`.trim(),
      );
      console.log(
        `- Bun: ${mark(status.bun.installed)} ${status.bun.version ?? ""}`.trim(),
      );
      console.log(
        `- gh: ${mark(status.gh.installed)} ${status.gh.version ?? ""}`.trim(),
      );

      console.log("\nNPM Packages");
      for (const pkg of status.npmPackages) {
        const suffix = pkg.version ? ` (${pkg.version})` : "";
        console.log(`- ${pkg.name}: ${mark(pkg.installed)}${suffix}`);
      }

      console.log("\nRepositories");
      for (const repo of status.repos) {
        const state = repo.exists
          ? repo.isGitRepo
            ? "git"
            : "dir"
          : "missing";
        console.log(`- ${repo.name}: ${state} (${repo.path})`);
      }
    });
}
