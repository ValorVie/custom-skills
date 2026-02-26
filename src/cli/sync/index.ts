import type { Command } from "commander";

import { createDefaultSyncEngine } from "../../core/sync-engine";

export function registerSyncCommands(program: Command): void {
  const sync = program.command("sync").description("Manage cross-device sync");
  const engine = createDefaultSyncEngine();

  sync
    .command("init")
    .description("Initialize sync config")
    .option("--remote <url>", "Remote git URL")
    .option("--json", "Output as JSON")
    .action(async (options: { remote?: string; json?: boolean }) => {
      const config = await engine.init(options.remote ?? "");

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
    .description("Push local sync directories into repo dir")
    .option("--force", "Force push to remote")
    .option("--json", "Output as JSON")
    .action(async (options: { force?: boolean; json?: boolean }) => {
      const summary = await engine.push({ force: options.force });

      if (options.json) {
        console.log(JSON.stringify(summary, null, 2));
        return;
      }

      console.log("Sync push complete");
      console.log(
        `- Added: ${summary.added}, Updated: ${summary.updated}, Deleted: ${summary.deleted}`,
      );
    });

  sync
    .command("pull")
    .description("Pull from repo dir into local directories")
    .option("--no-delete", "Keep local extra files")
    .option("--force", "Overwrite local changes without prompt")
    .option("--json", "Output as JSON")
    .action(
      async (options: {
        delete?: boolean;
        force?: boolean;
        json?: boolean;
      }) => {
        const summary = await engine.pull({
          deleteExtra: options.delete,
          noDelete: options.delete === false,
          force: options.force,
        });

        if (options.json) {
          console.log(JSON.stringify(summary, null, 2));
          return;
        }

        console.log("Sync pull complete");
        console.log(
          `- Added: ${summary.added}, Updated: ${summary.updated}, Deleted: ${summary.deleted}`,
        );
      },
    );

  sync
    .command("status")
    .description("Show sync status")
    .option("--json", "Output as JSON")
    .action(async (options: { json?: boolean }) => {
      const status = await engine.status();

      if (options.json) {
        console.log(JSON.stringify(status, null, 2));
        return;
      }

      console.log("Sync status");
      console.log(`- Initialized: ${status.initialized}`);
      console.log(`- Repo: ${status.repoDir}`);
      console.log(`- Local changes: ${status.localChanges}`);
      console.log(`- Remote behind: ${status.remoteBehind}`);
      if (status.config) {
        console.log(
          `- Tracked directories: ${status.config.directories.length}`,
        );
      }
    });

  sync
    .command("add")
    .description("Add a directory to sync")
    .argument("<path>", "Directory path")
    .option("--profile <profile>", "Ignore profile", "custom")
    .option("--ignore <pattern...>", "Custom ignore patterns")
    .option("--json", "Output as JSON")
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
    .description("Remove directory from sync")
    .argument("<path>", "Directory path")
    .option("--json", "Output as JSON")
    .action(async (path: string, options: { json?: boolean }) => {
      const config = await engine.removeDirectory(path);

      if (options.json) {
        console.log(JSON.stringify(config, null, 2));
        return;
      }

      console.log(`Removed sync directory: ${path}`);
      console.log(`- Total tracked directories: ${config.directories.length}`);
    });
}
