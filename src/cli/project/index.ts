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
    .action(
      async (target: string | undefined, options: { force?: boolean }) => {
        const result = await initProject({
          targetDir: target,
          force: options.force,
        });

        if (!result.success) {
          console.error(result.message ?? "project init failed");
          process.exitCode = 1;
          return;
        }

        if (!result.copied) {
          console.log(result.message ?? "already initialized");
          return;
        }

        console.log(`Project initialized at ${result.targetDir}`);
      },
    );

  project
    .command("update")
    .description("Run project update commands")
    .option("--only <tool>", "Only run one tool (openspec|uds)")
    .action(async (options: { only?: "openspec" | "uds" }) => {
      const result = await updateProject({ only: options.only });
      console.log(JSON.stringify(result, null, 2));
      if (result.errors.length > 0) {
        process.exitCode = 1;
      }
    });
}
