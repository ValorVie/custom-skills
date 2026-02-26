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

      if (result.pushed === 0 && result.errors === 0) {
        console.log(t("mem.push_nothing"));
        return;
      }

      console.log(
        t("mem.push_sending", {
          sessions: String(result.sent.sessions),
          observations: String(result.sent.observations),
          summaries: String(result.sent.summaries),
          prompts: String(result.sent.prompts),
        }),
      );
      console.log(
        t("mem.push_dedup", {
          pulled: String(result.dedupExcluded.pulled),
          preflight: String(result.dedupExcluded.preflight),
        }),
      );
      console.log(
        t("mem.push_done", {
          si: String(result.imported.sessions),
          oi: String(result.imported.observations),
          smi: String(result.imported.summaries),
          pi: String(result.imported.prompts),
          ss: String(result.skippedDetail.sessions),
          os: String(result.skippedDetail.observations),
          sms: String(result.skippedDetail.summaries),
          ps: String(result.skippedDetail.prompts),
        }),
      );
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

      console.log(
        t("mem.pull_received", {
          sessions: String(result.received.sessions),
          observations: String(result.received.observations),
          summaries: String(result.received.summaries),
          prompts: String(result.received.prompts),
        }),
      );
      console.log(
        t("mem.pull_done", {
          si: String(result.imported.sessions),
          oi: String(result.imported.observations),
          smi: String(result.imported.summaries),
          pi: String(result.imported.prompts),
          ss: String(result.skippedDetail.sessions),
          os: String(result.skippedDetail.observations),
          sms: String(result.skippedDetail.summaries),
          ps: String(result.skippedDetail.prompts),
        }),
      );
      if (result.pulled > 0) {
        console.log(t("mem.chromadb_syncing"));
      }
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

      const remoteAvailable = result.remoteStatus != null;
      const r = result.remoteStatus ?? {};
      const na = t("mem.remote_unavailable");

      const rows: string[][] = [
        // Server section (5 items)
        [
          t("mem.remote_sessions"),
          remoteAvailable ? String(r.sessions ?? 0) : na,
        ],
        [
          t("mem.remote_obs"),
          remoteAvailable ? String(r.observations ?? 0) : na,
        ],
        [
          t("mem.remote_summaries"),
          remoteAvailable ? String(r.summaries ?? 0) : na,
        ],
        [
          t("mem.remote_prompts"),
          remoteAvailable ? String(r.prompts ?? 0) : na,
        ],
        [
          t("mem.remote_devices"),
          remoteAvailable ? String(r.devices ?? 0) : na,
        ],
        // Local section (3 items)
        [t("mem.local_obs"), String(result.localObservations)],
        [t("mem.local_dups"), String(result.localDuplicates)],
        [t("mem.pulled_hashes"), String(result.pulledHashesTracked)],
        // Epoch info
        [t("mem.last_push"), String(result.config.lastPushEpoch)],
        [t("mem.last_pull"), String(result.config.lastPullEpoch)],
      ];

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

      console.log(t("mem.reindex_scanning"));

      if (result.synced === 0 && result.errors === 0) {
        console.log(t("mem.reindex_complete", { total: String(result.total) }));
      } else {
        console.log(
          t("mem.reindex_done", {
            synced: String(result.synced),
            errors: String(result.errors),
            total: String(result.total),
            missing: String(result.missing),
          }),
        );
      }

      if (result.duplicatesRemoved > 0) {
        console.log(
          t("mem.cleanup_auto", { count: String(result.duplicatesRemoved) }),
        );
      }
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
