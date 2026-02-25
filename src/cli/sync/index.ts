import type { Command } from "commander";

import { createDefaultSyncEngine } from "../../core/sync-engine";

export function registerSyncCommands(program: Command): void {
  const sync = program.command("sync").description("Manage cross-device sync");
  const engine = createDefaultSyncEngine();

  sync
    .command("init")
    .description("Initialize sync config")
    .requiredOption("--remote <url>", "Remote git URL")
    .action(async (options: { remote: string }) => {
      const config = await engine.init(options.remote);
      console.log(JSON.stringify(config, null, 2));
    });

  sync
    .command("push")
    .description("Push local sync directories into repo dir")
    .action(async () => {
      const summary = await engine.push();
      console.log(JSON.stringify(summary, null, 2));
    });

  sync
    .command("pull")
    .description("Pull from repo dir into local directories")
    .option("--no-delete", "Keep local extra files")
    .action(async (options: { delete?: boolean }) => {
      const summary = await engine.pull({ deleteExtra: options.delete });
      console.log(JSON.stringify(summary, null, 2));
    });

  sync
    .command("status")
    .description("Show sync status")
    .action(async () => {
      const status = await engine.status();
      console.log(JSON.stringify(status, null, 2));
    });

  sync
    .command("add")
    .description("Add a directory to sync")
    .argument("<path>", "Directory path")
    .option("--profile <profile>", "Ignore profile", "custom")
    .option("--ignore <pattern...>", "Custom ignore patterns")
    .action(
      async (
        path: string,
        options: { profile?: "claude" | "custom"; ignore?: string[] },
      ) => {
        const config = await engine.addDirectory(path, {
          profile: options.profile,
          ignore: options.ignore,
        });
        console.log(JSON.stringify(config, null, 2));
      },
    );

  sync
    .command("remove")
    .description("Remove directory from sync")
    .argument("<path>", "Directory path")
    .action(async (path: string) => {
      const config = await engine.removeDirectory(path);
      console.log(JSON.stringify(config, null, 2));
    });
}
