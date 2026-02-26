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

export function registerStandardsCommands(program: Command): void {
  const standards = program
    .command("standards")
    .description("Manage standards profiles");

  standards
    .command("status")
    .description("Show current standards status")
    .option("--json", "Output as JSON")
    .action(async (options: { json?: boolean }) => {
      const status = await getStandardsStatus();
      if (options.json) {
        console.log(JSON.stringify(status, null, 2));
        return;
      }

      printTable(
        ["Field", "Value"],
        [
          ["Initialized", String(status.initialized)],
          ["Active profile", status.activeProfile ?? "(none)"],
          ["Available profiles", String(status.availableProfiles.length)],
        ],
      );
    });

  standards
    .command("list")
    .description("List available profiles")
    .option("--json", "Output as JSON")
    .action(async (options: { json?: boolean }) => {
      const profiles = await listProfiles();
      if (options.json) {
        console.log(JSON.stringify(profiles, null, 2));
        return;
      }

      const status = await getStandardsStatus();
      const rows = profiles.map((profile) => [
        profile,
        status.activeProfile === profile ? "yes" : "",
      ]);
      printTable(["Profile", "Active"], rows);
    });

  standards
    .command("switch")
    .description("Switch active profile")
    .argument("<profile>", "Profile name")
    .option("--dry-run", "Preview only")
    .option("--json", "Output as JSON")
    .action(
      async (
        profile: string,
        options: { dryRun?: boolean; json?: boolean },
      ) => {
        const result = await switchProfile(profile, { dryRun: options.dryRun });
        if (!result.success) {
          printError(result.message ?? "switch failed");
          process.exitCode = 1;
          return;
        }

        if (options.json) {
          console.log(JSON.stringify(result, null, 2));
          return;
        }

        if (result.dryRun) {
          const disabled = await computeDisabledItems(profile);
          printSuccess(`Dry run complete for profile: ${profile}`);
          printTable(
            ["Metric", "Value"],
            [["Disabled standards", String(disabled.standards.length)]],
          );
          return;
        }

        printSuccess(`Switched to profile: ${profile}`);
        printTable(
          ["Metric", "Value"],
          [
            ["Disabled standards", String(result.disabledCount ?? 0)],
            ["Moved to .disabled", String(result.movedToDisabled ?? 0)],
            ["Restored to active", String(result.restoredToActive ?? 0)],
          ],
        );
      },
    );

  standards
    .command("show")
    .description("Show profile content")
    .argument("<profile>", "Profile name")
    .option("--json", "Output as JSON")
    .action(async (profile: string, options: { json?: boolean }) => {
      const data = await showProfile(profile);
      if (!data) {
        printError(`profile not found: ${profile}`);
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
      printTable(["Field", "Value"], rows);
    });

  standards
    .command("overlaps")
    .description("Show overlapping definitions across profiles")
    .option("--json", "Output as JSON")
    .action(async (options: { json?: boolean }) => {
      const overlaps = await detectOverlaps();

      if (options.json) {
        console.log(JSON.stringify(overlaps, null, 2));
        return;
      }

      const rows = Object.entries(overlaps).map(([item, owners]) => [
        item,
        owners.join(", "),
        `${owners.length} profiles`,
      ]);

      if (rows.length === 0) {
        printWarning("No overlaps detected.");
        return;
      }

      printTable(["Item", "Profiles", "Conflict"], rows);
    });

  standards
    .command("sync")
    .description("Sync standards state to .disabled directory")
    .option("--json", "Output as JSON")
    .action(async (options: { json?: boolean }) => {
      const result = await syncStandards();

      if (options.json) {
        console.log(JSON.stringify(result, null, 2));
        return;
      }

      printSuccess("Standards sync complete");
      printTable(
        ["Metric", "Value"],
        [
          ["Moved to .disabled", String(result.movedToDisabled)],
          ["Restored to active", String(result.restoredToActive)],
          ["Missing", String(result.missing.length)],
        ],
      );

      if (result.missing.length > 0) {
        printWarning(`Missing files: ${result.missing.join(", ")}`);
      }
    });
}
