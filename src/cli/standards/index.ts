import type { Command } from "commander";

import {
  detectOverlaps,
  getStandardsStatus,
  listProfiles,
  showProfile,
  switchProfile,
} from "../../core/standards-manager";

export function registerStandardsCommands(program: Command): void {
  const standards = program
    .command("standards")
    .description("Manage standards profiles");

  standards
    .command("status")
    .description("Show current standards status")
    .action(async () => {
      const status = await getStandardsStatus();
      console.log(JSON.stringify(status, null, 2));
    });

  standards
    .command("list")
    .description("List available profiles")
    .action(async () => {
      const profiles = await listProfiles();
      for (const profile of profiles) {
        console.log(profile);
      }
    });

  standards
    .command("switch")
    .description("Switch active profile")
    .argument("<profile>", "Profile name")
    .option("--dry-run", "Preview only")
    .action(async (profile: string, options: { dryRun?: boolean }) => {
      const result = await switchProfile(profile, { dryRun: options.dryRun });
      if (!result.success) {
        console.error(result.message ?? "switch failed");
        process.exitCode = 1;
        return;
      }
      console.log(JSON.stringify(result, null, 2));
    });

  standards
    .command("show")
    .description("Show profile content")
    .argument("<profile>", "Profile name")
    .action(async (profile: string) => {
      const data = await showProfile(profile);
      if (!data) {
        console.error(`profile not found: ${profile}`);
        process.exitCode = 1;
        return;
      }
      console.log(JSON.stringify(data, null, 2));
    });

  standards
    .command("overlaps")
    .description("Show overlapping definitions across profiles")
    .action(async () => {
      const overlaps = await detectOverlaps();
      console.log(JSON.stringify(overlaps, null, 2));
    });
}
