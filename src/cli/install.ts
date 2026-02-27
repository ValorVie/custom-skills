import type { Command } from "commander";

import { type InstallResult, runInstall } from "../core/installer";
import { printTable } from "../utils/formatter";
import { t } from "../utils/i18n";
import { formatProgress } from "../utils/progress-formatter";

function itemStatus(success: boolean): string {
  return success ? t("common.success") : t("common.failed");
}

export function renderInstallSummary(result: InstallResult): void {
  const claudeStatus = result.claudeCode.installed
    ? `${t("install.installed")}${result.claudeCode.version ? ` (${result.claudeCode.version})` : ""}`
    : t("install.missing");

  printTable(
    [t("sync.col_field"), t("sync.col_value")],
    [
      [
        t("install.prerequisites"),
        `node=${result.prerequisites.node}, git=${result.prerequisites.git}, gh=${result.prerequisites.gh}, bun=${result.prerequisites.bun}`,
      ],
      [t("install.claude_code"), claudeStatus],
    ],
    { title: t("install.summary") },
  );

  if (result.npmPackages.length > 0) {
    printTable(
      [t("status.col_name"), t("status.col_status"), t("sync.col_value")],
      result.npmPackages.map((item) => [
        item.name,
        itemStatus(item.success),
        item.message ?? item.version ?? t("common.none"),
      ]),
      { title: t("install.section_npm_packages") },
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
      { title: t("install.section_bun_packages") },
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
      { title: t("install.section_repositories") },
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
      { title: t("install.section_custom_repositories") },
    );
  }

  if (result.skills.installed.length > 0) {
    printTable(
      [t("sync.col_field"), t("sync.col_value")],
      [[t("install.skills_installed"), result.skills.installed.join(", ")]],
    );
  }

  if (result.skills.conflicts.length > 0) {
    printTable(
      [t("sync.col_field"), t("sync.col_value")],
      [[t("install.skills_conflicts"), result.skills.conflicts.join(", ")]],
    );
  }

  if (result.npmHint) {
    printTable(
      [t("sync.col_field"), t("sync.col_value")],
      [[t("install.hint"), result.npmHint]],
    );
  }

  if (result.shellCompletion.message) {
    printTable(
      [t("sync.col_field"), t("sync.col_value")],
      [[t("install.shell_completion"), result.shellCompletion.message]],
    );
  }

  if (result.errors.length > 0) {
    printTable(
      [t("status.col_status"), t("sync.col_value")],
      result.errors.map((error) => [t("common.failed"), error]),
      { title: t("install.errors") },
    );
  }
}

export interface InstallCommandOptions {
  skipNpm?: boolean;
  skipBun?: boolean;
  skipRepos?: boolean;
  skipSkills?: boolean;
  syncProject?: boolean;
  json?: boolean;
}

interface InstallCommandDependencies {
  runInstallFn?: typeof runInstall;
  formatProgressFn?: typeof formatProgress;
  logFn?: typeof console.log;
}

export async function handleInstallCommand(
  options: InstallCommandOptions,
  dependencies: InstallCommandDependencies = {},
): Promise<void> {
  const runInstallFn = dependencies.runInstallFn ?? runInstall;
  const formatProgressFn =
    dependencies.formatProgressFn ?? formatProgress;
  const logFn = dependencies.logFn ?? console.log;
  const onProgress = options.json ? undefined : formatProgressFn;

  const result = await runInstallFn({
    skipNpm: options.skipNpm,
    skipBun: options.skipBun,
    skipRepos: options.skipRepos,
    skipSkills: options.skipSkills,
    syncProject: options.syncProject,
    stream: !options.json,
    onProgress,
  });

  if (options.json) {
    logFn(JSON.stringify(result, null, 2));
    return;
  }

  renderInstallSummary(result);
  formatProgressFn("安裝完成！");
}

export function registerInstallCommand(program: Command): void {
  program
    .command("install")
    .description(t("cmd.install"))
    .option("--skip-npm", t("opt.skip_npm"))
    .option("--skip-bun", t("opt.skip_bun"))
    .option("--skip-repos", t("opt.skip_repos"))
    .option("--skip-skills", t("opt.skip_skills"))
    .option("--sync-project", t("opt.sync_project"))
    .option("--json", t("opt.json"))
    .action(async (options: InstallCommandOptions) => {
      await handleInstallCommand(options);
    });
}
