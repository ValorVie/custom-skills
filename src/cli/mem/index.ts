import type { Command } from "commander";

import {
  cleanupDuplicates,
  getMemSyncStatus,
  pullMemData,
  pushMemData,
  registerDevice,
  reindexMemData,
} from "../../core/mem-sync";

export function registerMemCommands(program: Command): void {
  const mem = program.command("mem").description("Manage claude-mem sync");

  mem
    .command("register")
    .description("Register this device to sync server")
    .requiredOption("--server <url>", "Sync server URL")
    .requiredOption("--name <name>", "Device name")
    .requiredOption("--admin-secret <secret>", "Admin secret")
    .action(
      async (options: {
        server: string;
        name: string;
        adminSecret: string;
      }) => {
        const config = await registerDevice({
          server: options.server,
          name: options.name,
          adminSecret: options.adminSecret,
        });
        console.log(JSON.stringify(config, null, 2));
      },
    );

  mem
    .command("push")
    .description("Push local data to sync server")
    .action(async () => {
      const result = await pushMemData();
      console.log(JSON.stringify(result, null, 2));
    });

  mem
    .command("pull")
    .description("Pull remote data from sync server")
    .action(async () => {
      const result = await pullMemData();
      console.log(JSON.stringify(result, null, 2));
    });

  mem
    .command("status")
    .description("Show mem sync status")
    .action(async () => {
      const result = await getMemSyncStatus();
      console.log(JSON.stringify(result, null, 2));
    });

  mem
    .command("reindex")
    .description("Reindex local observations (auto-cleans duplicates)")
    .action(async () => {
      const result = await reindexMemData();
      console.log(JSON.stringify(result, null, 2));
    });

  mem
    .command("cleanup")
    .description("Remove duplicate observations from local database")
    .action(async () => {
      const result = await cleanupDuplicates();
      console.log(JSON.stringify(result, null, 2));
    });
}
