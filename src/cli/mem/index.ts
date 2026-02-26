import type { Command } from "commander";

import {
  cleanupDuplicates,
  configureAutoSync,
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
    .option("--json", "Output as JSON")
    .action(
      async (options: {
        server: string;
        name: string;
        adminSecret: string;
        json?: boolean;
      }) => {
        const config = await registerDevice({
          server: options.server,
          name: options.name,
          adminSecret: options.adminSecret,
        });

        if (options.json) {
          console.log(JSON.stringify(config, null, 2));
          return;
        }

        console.log("Device registered");
        console.log(`- Server: ${config.serverUrl}`);
        console.log(`- Device: ${config.deviceName}`);
        console.log(`- Device ID: ${config.deviceId}`);
      },
    );

  mem
    .command("push")
    .description("Push local data to sync server")
    .option("--json", "Output as JSON")
    .action(async (options: { json?: boolean }) => {
      const result = await pushMemData();

      if (options.json) {
        console.log(JSON.stringify(result, null, 2));
        return;
      }

      console.log("Memory push complete");
      console.log(`- Pushed: ${result.pushed}`);
      console.log(`- Skipped: ${result.skipped}`);
      console.log(`- Server: ${result.serverUrl || "(not configured)"}`);
    });

  mem
    .command("pull")
    .description("Pull remote data from sync server")
    .option("--json", "Output as JSON")
    .action(async (options: { json?: boolean }) => {
      const result = await pullMemData();

      if (options.json) {
        console.log(JSON.stringify(result, null, 2));
        return;
      }

      console.log("Memory pull complete");
      console.log(`- Pulled: ${result.pulled}`);
      console.log(`- Server: ${result.serverUrl || "(not configured)"}`);
    });

  mem
    .command("status")
    .description("Show mem sync status")
    .option("--json", "Output as JSON")
    .action(async (options: { json?: boolean }) => {
      const result = await getMemSyncStatus();

      if (options.json) {
        console.log(JSON.stringify(result, null, 2));
        return;
      }

      console.log("Memory sync status");
      console.log(`- Device: ${result.config.deviceName || "(unregistered)"}`);
      console.log(`- Local observations: ${result.localObservations}`);
      console.log(`- Pending push: ${result.pendingPushCount}`);
      if (result.remoteStatus) {
        console.log(
          `- Remote observations: ${result.remoteStatus.observations ?? 0}`,
        );
      } else {
        console.log("- Remote status: unavailable");
      }
    });

  mem
    .command("reindex")
    .description("Reindex local observations (auto-cleans duplicates)")
    .option("--json", "Output as JSON")
    .action(async (options: { json?: boolean }) => {
      const result = await reindexMemData();

      if (options.json) {
        console.log(JSON.stringify(result, null, 2));
        return;
      }

      console.log("Memory reindex complete");
      console.log(`- Total: ${result.total}`);
      console.log(`- Synced: ${result.synced}`);
      console.log(`- Errors: ${result.errors}`);
      console.log(`- Duplicates removed: ${result.duplicatesRemoved}`);
    });

  mem
    .command("cleanup")
    .description("Remove duplicate observations from local database")
    .option("--json", "Output as JSON")
    .action(async (options: { json?: boolean }) => {
      const result = await cleanupDuplicates();

      if (options.json) {
        console.log(JSON.stringify(result, null, 2));
        return;
      }

      console.log("Memory cleanup complete");
      console.log(`- Duplicates removed: ${result.duplicatesRemoved}`);
    });

  mem
    .command("auto")
    .description("Configure automatic memory sync")
    .option("--enable", "Enable automatic sync")
    .option("--disable", "Disable automatic sync")
    .option("--status", "Show auto-sync status")
    .option("--interval <minutes>", "Auto-sync interval in minutes")
    .option("--json", "Output as JSON")
    .action(
      async (options: {
        enable?: boolean;
        disable?: boolean;
        status?: boolean;
        interval?: string;
        json?: boolean;
      }) => {
        const interval = options.interval
          ? Number.parseInt(options.interval, 10)
          : undefined;

        const result = await configureAutoSync({
          enable: options.enable,
          disable: options.disable,
          status: options.status,
          intervalMinutes: interval,
        });

        if (options.json) {
          console.log(JSON.stringify(result, null, 2));
          return;
        }

        console.log("Memory auto-sync");
        console.log(`- Enabled: ${result.enabled}`);
        console.log(`- Scheduler: ${result.scheduler}`);
        console.log(`- ${result.message}`);
      },
    );
}
