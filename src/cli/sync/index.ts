import type { Command } from "commander";
import inquirer from "inquirer";

import { createDefaultSyncEngine } from "../../core/sync-engine";
import { printTable } from "../../utils/formatter";
import { t } from "../../utils/i18n";

export function registerSyncCommands(program: Command): void {
  const sync = program.command("sync").description(t("cmd.sync"));
  const engine = createDefaultSyncEngine();

  sync
    .command("init")
    .description(t("cmd.sync_init"))
    .requiredOption("--remote <url>", t("opt.remote"))
    .option("--json", t("opt.json"))
    .action(async (options: { remote: string; json?: boolean }) => {
      const config = await engine.init(options.remote);

      if (options.json) {
        console.log(JSON.stringify(config, null, 2));
        return;
      }

      console.log("Sync initialized");
      console.log(`- Remote: ${config.remote || "(local)"}`);
      console.log(`- Directories: ${config.directories.length}`);
    });

  sync
    .command("push")
    .description(t("cmd.sync_push"))
    .option("--force", t("opt.force"))
    .option("--json", t("opt.json"))
    .action(async (options: { force?: boolean; json?: boolean }) => {
      const summary = await engine.push({ force: options.force });

      if (options.json) {
        console.log(JSON.stringify(summary, null, 2));
        return;
      }

      if (summary.skipped) {
        if (options.force) {
          console.log("Sync push cancelled");
        } else {
          console.log("No changes to sync");
        }
        return;
      }

      if (
        !options.force &&
        summary.added === 0 &&
        summary.updated === 0 &&
        summary.deleted === 0
      ) {
        console.log("No changes to sync");
        return;
      }

      console.log(t("sync.push_done"));
      console.log(
        t("sync.summary", {
          added: String(summary.added),
          updated: String(summary.updated),
          deleted: String(summary.deleted),
        }),
      );
    });

  sync
    .command("pull")
    .description(t("cmd.sync_pull"))
    .option("--no-delete", t("opt.no_delete"))
    .option("--force", t("opt.force"))
    .option("--json", t("opt.json"))
    .action(
      async (options: {
        delete?: boolean;
        force?: boolean;
        json?: boolean;
      }) => {
        try {
          const summary = await engine.pull({
            deleteExtra: options.delete,
            noDelete: options.delete === false,
            force: options.force,
          });

          if (options.json) {
            console.log(JSON.stringify(summary, null, 2));
            return;
          }

          console.log(t("sync.pull_done"));
          console.log(
            t("sync.summary", {
              added: String(summary.added),
              updated: String(summary.updated),
              deleted: String(summary.deleted),
            }),
          );
        } catch (error: unknown) {
          const message =
            error instanceof Error ? error.message : String(error);
          console.error(message);
          process.exitCode = 1;
        }
      },
    );

  sync
    .command("status")
    .description(t("cmd.sync_status"))
    .option("--json", t("opt.json"))
    .action(async (options: { json?: boolean }) => {
      const status = await engine.status();

      if (options.json) {
        console.log(JSON.stringify(status, null, 2));
        return;
      }

      printTable(
        [t("sync.col_field"), t("sync.col_value")],
        [
          [t("sync.initialized"), String(status.initialized)],
          [t("sync.repo_dir"), status.repoDir],
          [t("sync.local_changes"), String(status.localChanges)],
          [t("sync.remote_behind"), String(status.remoteBehind)],
          ...(status.config
            ? [
                [
                  t("sync.tracked_dirs"),
                  String(status.config.directories.length),
                ],
              ]
            : []),
        ],
      );
    });

  sync
    .command("add")
    .description(t("cmd.sync_add"))
    .argument("<path>", "Directory path")
    .option("--profile <profile>", t("opt.profile"), "custom")
    .option("--ignore <pattern...>", t("opt.ignore"))
    .option("--json", t("opt.json"))
    .action(
      async (
        path: string,
        options: {
          profile?: "claude" | "custom";
          ignore?: string[];
          json?: boolean;
        },
      ) => {
        const config = await engine.addDirectory(path, {
          profile: options.profile,
          ignore: options.ignore,
        });

        if (options.json) {
          console.log(JSON.stringify(config, null, 2));
          return;
        }

        console.log(`Added sync directory: ${path}`);
        console.log(
          `- Total tracked directories: ${config.directories.length}`,
        );
      },
    );

  sync
    .command("remove")
    .description(t("cmd.sync_remove"))
    .argument("<path>", "Directory path")
    .option("--json", t("opt.json"))
    .action(async (path: string, options: { json?: boolean }) => {
      try {
        const answer = await inquirer.prompt<{ deleteRepoSubdir: boolean }>([
          {
            type: "confirm",
            name: "deleteRepoSubdir",
            message: "是否刪除 sync repo 的對應子目錄？",
            default: false,
          },
        ]);
        const config = await engine.removeDirectory(path, {
          deleteRepoSubdir: Boolean(answer.deleteRepoSubdir),
        });

        if (options.json) {
          console.log(JSON.stringify(config, null, 2));
          return;
        }

        console.log(`Removed sync directory: ${path}`);
        console.log(
          `- Total tracked directories: ${config.directories.length}`,
        );
      } catch (error: unknown) {
        const message =
          error instanceof Error ? error.message : String(error);
        console.error(message);
        process.exitCode = 1;
      }
    });
}
