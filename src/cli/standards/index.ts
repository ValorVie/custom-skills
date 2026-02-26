import type { Command } from "commander";

import {
  computeDisabledItems,
  detectOverlaps,
  getStandardsStatus,
  listProfiles,
  showProfile,
  switchProfile,
  syncStandards,
} from "../../core/standards-manager";
import {
  printError,
  printSuccess,
  printTable,
  printWarning,
} from "../../utils/formatter";
import { t } from "../../utils/i18n";

export function registerStandardsCommands(program: Command): void {
  const standards = program
    .command("standards")
    .description(t("cmd.standards"));

  standards
    .command("status")
    .description(t("cmd.standards_status"))
    .option("--json", t("opt.json"))
    .action(async (options: { json?: boolean }) => {
      const status = await getStandardsStatus();
      if (options.json) {
        console.log(JSON.stringify(status, null, 2));
        return;
      }

      printTable(
        [t("standards.col_field"), t("standards.col_value")],
        [
          [
            t("standards.initialized"),
            status.initialized ? t("standards.yes") : t("standards.no"),
          ],
          [
            t("standards.active_profile"),
            status.activeProfile ?? t("common.none"),
          ],
          [
            t("standards.available_profiles"),
            String(status.availableProfiles.length),
          ],
        ],
      );
    });

  standards
    .command("list")
    .description(t("cmd.standards_list"))
    .option("--json", t("opt.json"))
    .action(async (options: { json?: boolean }) => {
      const profiles = await listProfiles();
      if (options.json) {
        console.log(JSON.stringify(profiles, null, 2));
        return;
      }

      const status = await getStandardsStatus();
      const rows = profiles.map((profile) => [
        profile,
        status.activeProfile === profile ? t("standards.active_yes") : "",
      ]);
      printTable([t("standards.col_profile"), t("standards.col_active")], rows);
    });

  standards
    .command("switch")
    .description(t("cmd.standards_switch"))
    .argument("<profile>", t("standards.arg_profile"))
    .option("--dry-run", t("opt.dry_run"))
    .option("--json", t("opt.json"))
    .action(
      async (
        profile: string,
        options: { dryRun?: boolean; json?: boolean },
      ) => {
        const result = await switchProfile(profile, { dryRun: options.dryRun });
        if (!result.success) {
          printError(result.message ?? t("standards.switch_failed"));
          process.exitCode = 1;
          return;
        }

        if (options.json) {
          console.log(JSON.stringify(result, null, 2));
          return;
        }

        if (result.dryRun) {
          const disabled = await computeDisabledItems(profile);
          printSuccess(t("standards.dry_run_complete", { profile }));
          printTable(
            [t("standards.col_metric"), t("standards.col_value")],
            [
              [
                t("standards.metric_disabled"),
                String(disabled.standards.length),
              ],
            ],
          );
          return;
        }

        printSuccess(t("standards.switched_to_profile", { profile }));
        printTable(
          [t("standards.col_metric"), t("standards.col_value")],
          [
            [t("standards.metric_disabled"), String(result.disabledCount ?? 0)],
            [
              t("standards.metric_moved_disabled"),
              String(result.movedToDisabled ?? 0),
            ],
            [
              t("standards.metric_restored_active"),
              String(result.restoredToActive ?? 0),
            ],
          ],
        );
      },
    );

  standards
    .command("show")
    .description(t("cmd.standards_show"))
    .argument("<profile>", t("standards.arg_profile"))
    .option("--json", t("opt.json"))
    .action(async (profile: string, options: { json?: boolean }) => {
      const data = await showProfile(profile);
      if (!data) {
        printError(t("standards.profile_not_found", { profile }));
        process.exitCode = 1;
        return;
      }

      if (options.json) {
        console.log(JSON.stringify(data, null, 2));
        return;
      }

      const rows = Object.entries(data).map(([key, value]) => {
        if (Array.isArray(value)) {
          return [key, value.join(", ")];
        }
        if (value && typeof value === "object") {
          return [key, JSON.stringify(value)];
        }
        return [key, String(value)];
      });
      printTable([t("standards.col_field"), t("standards.col_value")], rows);
    });

  standards
    .command("overlaps")
    .description(t("cmd.standards_overlaps"))
    .option("--json", t("opt.json"))
    .action(async (options: { json?: boolean }) => {
      const overlaps = await detectOverlaps();

      if (options.json) {
        console.log(JSON.stringify(overlaps, null, 2));
        return;
      }

      const rows = Object.entries(overlaps).map(([item, owners]) => [
        item,
        owners.join(", "),
        t("standards.conflict_profiles", { count: String(owners.length) }),
      ]);

      if (rows.length === 0) {
        printWarning(t("standards.no_overlaps"));
        return;
      }

      printTable(
        [
          t("standards.col_item"),
          t("standards.col_profiles"),
          t("standards.col_conflict"),
        ],
        rows,
      );
    });

  standards
    .command("sync")
    .description(t("cmd.standards_sync"))
    .option("--json", t("opt.json"))
    .action(async (options: { json?: boolean }) => {
      const result = await syncStandards();

      if (options.json) {
        console.log(JSON.stringify(result, null, 2));
        return;
      }

      printSuccess(t("standards.sync_complete"));
      printTable(
        [t("standards.col_metric"), t("standards.col_value")],
        [
          [
            t("standards.metric_moved_disabled"),
            String(result.movedToDisabled),
          ],
          [
            t("standards.metric_restored_active"),
            String(result.restoredToActive),
          ],
          [t("standards.metric_missing"), String(result.missing.length)],
        ],
      );

      if (result.missing.length > 0) {
        printWarning(
          t("standards.missing_files", { files: result.missing.join(", ") }),
        );
      }
    });
}
