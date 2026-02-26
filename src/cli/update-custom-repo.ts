import type { Command } from "commander";

import { updateCustomRepos } from "../core/custom-repo-updater";
import { printSuccess, printTable, printWarning } from "../utils/formatter";
import { t } from "../utils/i18n";

export function registerUpdateCustomRepoCommand(program: Command): void {
  program
    .command("update-custom-repo")
    .description(t("cmd.update_custom_repo"))
    .option("--json", t("opt.json"))
    .action(async (options: { json?: boolean }) => {
      const result = await updateCustomRepos();

      if (options.json) {
        console.log(JSON.stringify(result, null, 2));
        return;
      }

      if (result.items.length === 0) {
        printWarning(t("update_custom.no_repos"));
        return;
      }

      printSuccess(t("update_custom.done"));
      printTable(
        ["Name", "Status", "Backup", "Message"],
        result.items.map((item) => [
          item.name,
          item.status,
          item.backupDir ?? "",
          item.message ?? "",
        ]),
      );

      printTable(
        ["Summary", "Repos"],
        [
          ["Updated", result.summary.updated.join(", ") || "(none)"],
          ["Up-to-date", result.summary.upToDate.join(", ") || "(none)"],
          ["Missing", result.summary.missing.join(", ") || "(none)"],
        ],
      );

      if (result.errors.length > 0) {
        printWarning(
          t("update_custom.errors", { errors: result.errors.join(" | ") }),
        );
        process.exitCode = 1;
      }
    });
}
