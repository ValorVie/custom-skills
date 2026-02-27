import type { Command } from "commander";

import { runUpdate, type UpdateResult } from "../core/updater";
import { printTable } from "../utils/formatter";
import { t } from "../utils/i18n";
import { formatProgress } from "../utils/progress-formatter";

function itemStatus(success: boolean): string {
  return success ? t("common.success") : t("common.failed");
}

export function renderUpdateSummary(result: UpdateResult): void {
  const pluginsSummary =
    result.plugins.length === 0
      ? t("common.none")
      : result.plugins
          .map(
            (p) =>
              `${p.name}: ${itemStatus(p.success)}${p.message ? ` (${p.message})` : ""}`,
          )
          .join(", ");

  printTable(
    [t("sync.col_field"), t("sync.col_value")],
    [
      [
        t("update.claude_code"),
        `${itemStatus(result.claudeCode.success)}${result.claudeCode.message ? ` (${result.claudeCode.message})` : ""}`,
      ],
      [t("update.plugin_marketplace"), pluginsSummary],
    ],
    { title: t("update.summary") },
  );

  if (result.tools.length > 0) {
    printTable(
      [t("status.col_name"), t("status.col_status"), t("sync.col_value")],
      result.tools.map((item) => [
        item.name,
        itemStatus(item.success),
        item.message ?? t("common.none"),
      ]),
      { title: t("update.section_tools") },
    );
  }

  if (result.npmPackages.length > 0) {
    printTable(
      [t("status.col_name"), t("status.col_status"), t("sync.col_value")],
      result.npmPackages.map((item) => [
        item.name,
        itemStatus(item.success),
        item.message ?? t("common.none"),
      ]),
      { title: t("update.section_npm_packages") },
    );
  }

  if (result.bunPackages.length > 0) {
    printTable(
      [t("status.col_name"), t("status.col_status"), t("sync.col_value")],
      result.bunPackages.map((item) => [
        item.name,
        itemStatus(item.success),
        item.message ?? t("common.none"),
      ]),
      { title: t("update.section_bun_packages") },
    );
  }

  if (result.repos.length > 0) {
    printTable(
      [t("status.col_name"), t("status.col_status"), t("sync.col_value")],
      result.repos.map((item) => [
        item.name,
        itemStatus(item.success),
        item.message ?? t("common.none"),
      ]),
      { title: t("update.section_repositories") },
    );
  }

  if (result.customRepos.length > 0) {
    printTable(
      [t("status.col_name"), t("status.col_status"), t("sync.col_value")],
      result.customRepos.map((item) => [
        item.name,
        itemStatus(item.success),
        item.message ?? t("common.none"),
      ]),
      { title: t("update.section_custom_repositories") },
    );
  }

  printTable(
    [t("sync.col_field"), t("sync.col_value")],
    [
      [
        t("update.updated_repos"),
        result.summary.updated.join(", ") || t("common.none"),
      ],
      [
        t("update.up_to_date_repos"),
        result.summary.upToDate.join(", ") || t("common.none"),
      ],
      [
        t("update.missing_repos"),
        result.summary.missing.join(", ") || t("common.none"),
      ],
    ],
  );

  if (result.errors.length > 0) {
    printTable(
      [t("status.col_status"), t("sync.col_value")],
      result.errors.map((error) => [t("common.failed"), error]),
      { title: t("update.errors") },
    );
  }
}

export interface UpdateCommandOptions {
  skipNpm?: boolean;
  skipBun?: boolean;
  skipRepos?: boolean;
  skipPlugins?: boolean;
  json?: boolean;
}

interface UpdateCommandDependencies {
  runUpdateFn?: typeof runUpdate;
  formatProgressFn?: typeof formatProgress;
  logFn?: typeof console.log;
}

export async function handleUpdateCommand(
  options: UpdateCommandOptions,
  dependencies: UpdateCommandDependencies = {},
): Promise<void> {
  const runUpdateFn = dependencies.runUpdateFn ?? runUpdate;
  const formatProgressFn =
    dependencies.formatProgressFn ?? formatProgress;
  const logFn = dependencies.logFn ?? console.log;
  const onProgress = options.json ? undefined : formatProgressFn;

  const result = await runUpdateFn({
    skipNpm: options.skipNpm,
    skipBun: options.skipBun,
    skipRepos: options.skipRepos,
    skipPlugins: options.skipPlugins,
    stream: !options.json,
    onProgress,
  });

  if (options.json) {
    logFn(JSON.stringify(result, null, 2));
    return;
  }

  renderUpdateSummary(result);
  formatProgressFn("更新完成！");
  formatProgressFn("提示：如需分發 Skills 到各工具目錄，請執行：ai-dev clone");
}

export function registerUpdateCommand(program: Command): void {
  program
    .command("update")
    .description(t("cmd.update"))
    .option("--skip-npm", t("opt.skip_npm"))
    .option("--skip-bun", t("opt.skip_bun"))
    .option("--skip-repos", t("opt.skip_repos"))
    .option("--skip-plugins", t("opt.skip_plugins"))
    .option("--json", t("opt.json"))
    .action(async (options: UpdateCommandOptions) => {
      await handleUpdateCommand(options);
    });
}
