import type { Command } from "commander";

import { addUpstreamRepo } from "../core/upstream-repo-manager";
import {
  printError,
  printSuccess,
  printTable,
  printWarning,
} from "../utils/formatter";
import { t } from "../utils/i18n";

export function registerAddRepoCommand(program: Command): void {
  program
    .command("add-repo")
    .description("Add and optionally clone a tracked repository")
    .argument("<repo>", "GitHub repo (owner/name) or URL")
    .option("--name <name>", "Custom repo name")
    .option("--branch <branch>", "Tracked branch", "main")
    .option("--skip-clone", "Skip cloning and only register config")
    .option("--analyze", "Analyze repository structure and suggest approach")
    .action(
      async (
        repoInput: string,
        options: {
          name?: string;
          branch: string;
          skipClone?: boolean;
          analyze?: boolean;
        },
      ) => {
        const result = await addUpstreamRepo({
          repoInput,
          name: options.name,
          branch: options.branch,
          skipClone: options.skipClone,
          analyze: options.analyze,
        });

        if (!result.success) {
          if (result.duplicate) {
            printWarning(result.message ?? t("add_repo.duplicate"));
          } else {
            printError(result.message ?? t("add_repo.failed"));
          }
          process.exitCode = 1;
          return;
        }

        printSuccess(
          t("add_repo.added", { name: result.name, repo: result.repo }),
        );
        printTable(
          ["Field", "Value"],
          [
            ["Format", result.format],
            ["Branch", result.branch],
            ["Path", result.localPath],
          ],
        );

        if (result.analysis) {
          printTable(
            ["Analysis", "Value"],
            [
              ["Recommendation", result.analysis.recommendation],
              ["Has standards", String(result.analysis.hasStandards)],
              ["Has skills", String(result.analysis.hasSkills)],
              ["Has commands", String(result.analysis.hasCommands)],
              ["Has agents", String(result.analysis.hasAgents)],
              ["Has workflows", String(result.analysis.hasWorkflows)],
            ],
          );
        }
      },
    );
}
