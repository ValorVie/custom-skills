import { access } from "node:fs/promises";
import { basename, join } from "node:path";
import chalk from "chalk";
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
  onProgress?: (message: string) => void;
}): Promise<CloneCommandResult> {
  const cwd = process.cwd();
  const devMode = await detectDeveloperMode(cwd);
  const distribution = await distributeSkills({
    force: options.force,
    skipConflicts: options.skipConflicts,
    backup: options.backup,
    devMode,
    sourceRoot: cwd,
    onProgress: options.onProgress,
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
          onProgress: options.json ? undefined : (msg) => console.log(chalk.dim(`  ${msg}`)),
        });

        if (options.json) {
          console.log(JSON.stringify(result, null, 2));
          return;
        }

        // Dev mode hints
        if (result.devMode && result.syncProject) {
          console.log(chalk.bold.blue("開發者模式：整合外部來源到開發目錄"));
        } else if (result.devMode) {
          console.log(chalk.dim("提示：使用 --sync-project 可整合外部來源到開發目錄"));
        }

        console.log(chalk.bold.blue("\n分發 Skills 到各工具目錄..."));

        // Distribution results
        if (result.distributed.length > 0) {
          for (const item of result.distributed) {
            console.log(chalk.green(`  ✓ ${item.target}/${item.type}: ${item.name}`));
          }
        }

        console.log(chalk.bold.green(`\n分發完成！共 ${result.metadata.updated} 項更新，${result.metadata.unchanged} 項未變更`));

        // Conflicts
        if (result.conflicts.length > 0) {
          console.log(chalk.yellow("\n衝突："));
          for (const conflict of result.conflicts) {
            console.log(chalk.yellow(`  ! ${conflict.target}/${conflict.type}: ${conflict.name}`));
          }
        }

        // Errors
        if (result.errors.length > 0) {
          console.log(chalk.red("\n錯誤："));
          for (const error of result.errors) {
            console.log(chalk.red(`  ✗ ${error}`));
          }
        }

        // TODO placeholders for future features
        if (result.devMode && result.syncProject) {
          console.log(chalk.dim("\n[TODO] integrate_to_dev_project: 外部來源整合功能尚未實作"));
        }
        if (result.devMode) {
          console.log(chalk.dim("[TODO] detect_metadata_changes: metadata 變更偵測功能尚未實作"));
        }
      },
    );
}
