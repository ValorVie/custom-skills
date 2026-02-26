import { access } from "node:fs/promises";
import { basename, join } from "node:path";
import type { Command } from "commander";

import {
  type DistributeResult,
  distributeSkills,
} from "../core/skill-distributor";
import { t } from "../utils/i18n";

interface CloneCommandResult extends DistributeResult {
  devMode: boolean;
  syncProject: boolean;
  metadata: {
    updated: number;
    unchanged: number;
    changed: boolean;
  };
}

async function pathExists(pathValue: string): Promise<boolean> {
  try {
    await access(pathValue);
    return true;
  } catch {
    return false;
  }
}

async function detectDeveloperMode(cwd: string): Promise<boolean> {
  if (basename(cwd) !== "custom-skills") {
    return false;
  }

  return (
    (await pathExists(join(cwd, "skills"))) &&
    (await pathExists(join(cwd, "commands"))) &&
    (await pathExists(join(cwd, "agents")))
  );
}

async function runClone(options: {
  force?: boolean;
  skipConflicts?: boolean;
  backup?: boolean;
  syncProject?: boolean;
}): Promise<CloneCommandResult> {
  const cwd = process.cwd();
  const devMode = await detectDeveloperMode(cwd);
  const distribution = await distributeSkills({
    force: options.force,
    skipConflicts: options.skipConflicts,
    backup: options.backup,
    devMode,
    sourceRoot: cwd,
  });

  return {
    ...distribution,
    devMode,
    syncProject: options.syncProject ?? false,
    metadata: {
      updated: distribution.distributed.length,
      unchanged: distribution.unchanged,
      changed: distribution.distributed.length > 0,
    },
  };
}

export function registerCloneCommand(program: Command): void {
  program
    .command("clone")
    .description(t("cmd.clone"))
    .option("--force", t("opt.force"))
    .option("--skip-conflicts", t("opt.skip_conflicts"))
    .option("--backup", t("opt.backup"))
    .option("--sync-project", t("opt.sync_project"))
    .option("--no-sync-project", t("opt.no_sync_project"))
    .option("--json", t("opt.json"))
    .action(
      async (options: {
        force?: boolean;
        skipConflicts?: boolean;
        backup?: boolean;
        syncProject?: boolean;
        json?: boolean;
      }) => {
        const result = await runClone({
          force: options.force,
          skipConflicts: options.skipConflicts,
          backup: options.backup,
          syncProject: options.syncProject,
        });

        if (options.json) {
          console.log(JSON.stringify(result, null, 2));
          return;
        }

        console.log("Clone Summary");
        console.log(
          `- Developer mode: ${result.devMode ? "enabled" : "disabled"}`,
        );
        console.log(
          `- Metadata: updated=${result.metadata.updated}, unchanged=${result.metadata.unchanged}`,
        );

        if (result.distributed.length > 0) {
          console.log("- Distributed:");
          for (const item of result.distributed) {
            console.log(`  - ${item.target}/${item.type}: ${item.name}`);
          }
        }

        if (result.conflicts.length > 0) {
          console.log("- Conflicts:");
          for (const conflict of result.conflicts) {
            console.log(
              `  - ${conflict.target}/${conflict.type}: ${conflict.name}`,
            );
          }
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
