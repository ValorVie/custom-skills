import type { Command } from "commander";

import { initProject, updateProject } from "../../core/project-manager";

export function registerProjectCommands(program: Command): void {
  const project = program
    .command("project")
    .description("Project template and standards operations");

  project
    .command("init")
    .description("Initialize project from template")
    .argument("[target]", "Target directory")
    .option("--force", "Force overwrite existing files")
    .option("--json", "Output as JSON")
    .action(
      async (
        target: string | undefined,
        options: { force?: boolean; json?: boolean },
      ) => {
        const result = await initProject({
          targetDir: target,
          force: options.force,
        });

        if (options.json) {
          console.log(JSON.stringify(result, null, 2));
          return;
        }

        if (!result.success) {
          console.error(result.message ?? "project init failed");
          process.exitCode = 1;
          return;
        }

        console.log("Project init complete");
        console.log(`- Target: ${result.targetDir}`);
        console.log(`- Template: ${result.templateDir}`);
        console.log(`- Copied: ${result.copied}`);
        if (result.backupDir) {
          console.log(`- Backup: ${result.backupDir}`);
        }
        if (result.reverseSynced) {
          console.log("- Reverse sync: enabled");
        }
        if (result.message) {
          console.log(`- Note: ${result.message}`);
        }
      },
    );

  project
    .command("update")
    .description("Run project update commands")
    .option("--only <tool>", "Only run one tool (openspec|uds)")
    .option("--json", "Output as JSON")
    .action(async (options: { only?: "openspec" | "uds"; json?: boolean }) => {
      const result = await updateProject({ only: options.only });

      if (options.json) {
        console.log(JSON.stringify(result, null, 2));
      } else {
        console.log("Project update complete");
        if (result.openspec !== undefined) {
          console.log(`- openspec: ${result.openspec ? "OK" : "FAIL"}`);
        }
        if (result.uds !== undefined) {
          console.log(`- uds: ${result.uds ? "OK" : "FAIL"}`);
        }
        if (result.errors.length > 0) {
          console.log(`- Errors: ${result.errors.join(", ")}`);
        }
      }

      if (result.errors.length > 0) {
        process.exitCode = 1;
      }
    });
}
