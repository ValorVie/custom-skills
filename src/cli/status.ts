import chalk from "chalk";
import type { Command } from "commander";

import { checkEnvironment } from "../core/status-checker";
import { printTable } from "../utils/formatter";
import { t } from "../utils/i18n";

function mark(installed: boolean): string {
  return installed ? "OK" : "MISSING";
}

export function registerStatusCommand(program: Command): void {
  program
    .command("status")
    .description("Check environment status")
    .option("--json", "Output status as JSON")
    .action(async (options: { json?: boolean }) => {
      const status = await checkEnvironment();

      if (options.json) {
        console.log(JSON.stringify(status, null, 2));
        return;
      }

      printTable(
        ["Core Tool", "Status", "Version", "Path"],
        [
          [
            "Git",
            mark(status.git.installed),
            status.git.version ?? "",
            status.git.path ?? "",
          ],
          [
            "Node",
            mark(status.node.installed),
            status.node.version ?? "",
            status.node.path ?? "",
          ],
          [
            "Bun",
            mark(status.bun.installed),
            status.bun.version ?? "",
            status.bun.path ?? "",
          ],
          [
            "gh",
            mark(status.gh.installed),
            status.gh.version ?? "",
            status.gh.path ?? "",
          ],
        ],
      );

      printTable(
        ["NPM Package", "Status", "Version"],
        status.npmPackages.map((pkg) => [
          pkg.name,
          mark(pkg.installed),
          pkg.version ?? "",
        ]),
      );

      const repoRows = status.repos.map((repo) => {
        let syncText: string = repo.syncState;
        if (repo.syncState === "updates-available") {
          syncText = t("status.updates_available", {
            count: String(repo.behind),
          });
        }
        if (repo.syncState === "up-to-date") {
          syncText = chalk.green("up-to-date");
        }

        return [
          repo.name,
          repo.branch ?? "",
          syncText,
          String(repo.behind),
          String(repo.ahead),
          repo.path,
        ];
      });

      printTable(
        ["Repository", "Branch", "Sync", "Behind", "Ahead", "Path"],
        repoRows,
      );

      if (status.upstreamSync.length > 0) {
        printTable(
          ["Upstream", "Status", "Behind", "Synced", "Format", "Path"],
          status.upstreamSync.map((item) => [
            item.name,
            item.status === "behind"
              ? t("status.upstream_behind", { count: String(item.behind) })
              : item.status,
            String(item.behind),
            item.syncedAt ? item.syncedAt.slice(5, 10) : "",
            item.format ?? "",
            item.path,
          ]),
        );
      }
    });
}
