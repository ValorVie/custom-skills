import chalk from "chalk";
import type { Command } from "commander";

import { initProject, updateProject } from "../../core/project-manager";
import { t } from "../../utils/i18n";

export function registerProjectCommands(program: Command): void {
  const project = program.command("project").description(t("cmd.project"));

  project
    .command("init")
    .description(t("cmd.project_init"))
    .argument("[target]", "Target directory")
    .option("-f, --force", t("opt.force"))
    .option("--json", t("opt.json"))
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

        console.log(chalk.bold.green("專案初始化完成！"));
        console.log(chalk.dim(`  目標：${result.targetDir}`));
        console.log(chalk.dim(`  模板：${result.templateDir}`));
        console.log(chalk.dim(`  複製：${result.copied} 項`));
        if (result.backupDir) {
          console.log(chalk.dim(`  備份：${result.backupDir}`));
        }
        if (result.reverseSynced) {
          console.log(chalk.dim("  反向同步：已啟用"));
        }
        if (result.message) {
          console.log(chalk.yellow(`  注意：${result.message}`));
        }
      },
    );

  project
    .command("update")
    .description(t("cmd.project_update"))
    .option("-o, --only <tool>", t("opt.only"))
    .option("--json", t("opt.json"))
    .action(async (options: { only?: "openspec" | "uds"; json?: boolean }) => {
      const result = await updateProject({ only: options.only });

      if (options.json) {
        console.log(JSON.stringify(result, null, 2));
      } else {
        console.log(chalk.bold.green("專案更新完成！"));
        if (result.openspec !== undefined) {
          const status = result.openspec ? chalk.green("OK") : chalk.red("FAIL");
          console.log(`  openspec: ${status}`);
        }
        if (result.uds !== undefined) {
          const status = result.uds ? chalk.green("OK") : chalk.red("FAIL");
          console.log(`  uds: ${status}`);
        }
        if (result.errors.length > 0) {
          console.log(chalk.red(`  錯誤：${result.errors.join(", ")}`));
        }
      }

      if (result.errors.length > 0) {
        process.exitCode = 1;
      }
    });
}
