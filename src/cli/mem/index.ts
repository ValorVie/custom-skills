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
import { printTable } from "../../utils/formatter";
import { t } from "../../utils/i18n";

export function registerMemCommands(program: Command): void {
  const mem = program.command("mem").description(t("cmd.mem"));

  mem
    .command("register")
    .description(t("cmd.mem_register"))
    .requiredOption("--server <url>", t("opt.server"))
    .requiredOption("--name <name>", t("opt.device_name"))
    .requiredOption("--admin-secret <secret>", t("opt.admin_secret"))
    .option("--json", t("opt.json"))
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
    .description(t("cmd.mem_push"))
    .option("--json", t("opt.json"))
    .action(async (options: { json?: boolean }) => {
      const result = await pushMemData();

      if (options.json) {
        console.log(JSON.stringify(result, null, 2));
        return;
      }

      console.log("Memory push complete");
      console.log(`- Pushed: ${result.pushed}`);
      console.log(`- Skipped: ${result.skipped}`);
      if (result.errors > 0) {
        console.log(`- Errors: ${result.errors}`);
      }
      console.log(`- Server: ${result.serverUrl || "(not configured)"}`);
    });

  mem
    .command("pull")
    .description(t("cmd.mem_pull"))
    .option("--json", t("opt.json"))
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
    .description(t("cmd.mem_status"))
    .option("--json", t("opt.json"))
    .action(async (options: { json?: boolean }) => {
      const result = await getMemSyncStatus();

      if (options.json) {
        console.log(JSON.stringify(result, null, 2));
        return;
      }

      const rows: string[][] = [
        [t("mem.device"), result.config.deviceName || t("mem.unregistered")],
        [t("mem.local_obs"), String(result.localObservations)],
        [t("mem.pending_push"), String(result.pendingPushCount)],
      ];

      if (result.remoteStatus) {
        rows.push([
          t("mem.remote_obs"),
          String(result.remoteStatus.observations ?? 0),
        ]);
      } else {
        rows.push([t("mem.remote_obs"), t("mem.remote_unavailable")]);
      }

      printTable([t("mem.col_field"), t("mem.col_value")], rows);
    });

  mem
    .command("reindex")
    .description(t("cmd.mem_reindex"))
    .option("--json", t("opt.json"))
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
    .description(t("cmd.mem_cleanup"))
    .option("--json", t("opt.json"))
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
    .description(t("cmd.mem_auto"))
    .option("--enable", t("opt.enable"))
    .option("--disable", t("opt.disable"))
    .option("--status", t("opt.status"))
    .option("--interval <minutes>", t("opt.interval"))
    .option("--json", t("opt.json"))
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
