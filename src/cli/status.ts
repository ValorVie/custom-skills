import type { Command } from "commander";

import { checkEnvironment, type RepoStatus } from "../core/status-checker";
import { printTable } from "../utils/formatter";
import { t } from "../utils/i18n";

function formatVersionPath(
  version: string | null,
  path: string | null,
): string {
  const versionText = version ?? "";
  const pathText = path ?? "";

  if (versionText && pathText) {
    return `${versionText} / ${pathText}`;
  }

  return versionText || pathText || t("common.none");
}

function mapRepoStatus(repo: RepoStatus): string {
  switch (repo.syncState) {
    case "updates-available":
      return t("status.behind_n", { count: String(repo.behind) });
    case "up-to-date":
      return t("status.up_to_date");
    case "local-ahead":
      return t("status.local_ahead");
    case "diverged":
      return t("status.diverged");
    case "not-git":
      return t("status.not_git");
    case "missing":
      return t("status.missing");
    default:
      return t("status.unknown");
  }
}

export function registerStatusCommand(program: Command): void {
  program
    .command("status")
    .description(t("cmd.status"))
    .option("--json", t("opt.json"))
    .action(async (options: { json?: boolean }) => {
      const status = await checkEnvironment();

      if (options.json) {
        console.log(JSON.stringify(status, null, 2));
        return;
      }

      console.log(t("status.title"));

      printTable(
        [
          t("status.col_tool"),
          t("status.col_status"),
          t("status.col_version_path"),
        ],
        [
          [
            "Node.js",
            status.node.installed ? t("status.installed") : t("status.missing"),
            formatVersionPath(status.node.version, status.node.path),
          ],
          [
            "Git",
            status.git.installed ? t("status.installed") : t("status.missing"),
            formatVersionPath(status.git.version, status.git.path),
          ],
          [
            "Bun",
            status.bun.installed ? t("status.installed") : t("status.missing"),
            formatVersionPath(status.bun.version, status.bun.path),
          ],
          [
            "gh",
            status.gh.installed ? t("status.installed") : t("status.missing"),
            formatVersionPath(status.gh.version, status.gh.path),
          ],
        ],
        { title: t("status.table_core_tools") },
      );

      printTable(
        [t("status.col_package"), t("status.col_status")],
        status.npmPackages.length > 0
          ? status.npmPackages.map((pkg) => [
              pkg.name,
              pkg.installed ? t("status.installed") : t("status.missing"),
            ])
          : [[t("common.none"), t("common.none")]],
        { title: t("status.table_npm_packages") },
      );

      printTable(
        [t("status.col_name"), t("status.col_local_status")],
        status.repos.length > 0
          ? status.repos.map((repo) => [repo.name, mapRepoStatus(repo)])
          : [[t("common.none"), t("common.none")]],
        { title: t("status.table_repos") },
      );

      printTable(
        [
          t("status.col_name"),
          t("status.col_synced_at"),
          t("status.col_status"),
        ],
        status.upstreamSync.length > 0
          ? status.upstreamSync.map((item) => {
              let upstreamStatus = t("status.unknown");
              if (item.status === "behind") {
                upstreamStatus = t("status.behind_n", {
                  count: String(item.behind),
                });
              } else if (item.status === "synced") {
                upstreamStatus = t("status.up_to_date");
              } else if (item.status === "uninstalled") {
                upstreamStatus = t("status.missing");
              }

              return [
                item.name,
                item.syncedAt ? item.syncedAt.slice(5, 10) : t("common.none"),
                upstreamStatus,
              ];
            })
          : [[t("common.none"), t("common.none"), t("common.none")]],
        { title: t("status.table_upstream") },
      );
    });
}
