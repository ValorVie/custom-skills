import { access, cp, mkdir, rm } from "node:fs/promises";
import { homedir } from "node:os";
import { join } from "node:path";

import type { Command } from "commander";
import inquirer from "inquirer";

import { printError, printSuccess, printWarning } from "../../utils/formatter";
import { t } from "../../utils/i18n";

function hooksPluginDir(): string {
  return join(homedir(), ".claude", "plugins", "ecc-hooks");
}

function pluginSourceCandidates(): string[] {
  return [
    join(process.cwd(), "plugins", "ecc-hooks"),
    join(homedir(), ".config", "custom-skills", "plugins", "ecc-hooks"),
    join(
      homedir(),
      ".config",
      "everything-claude-code",
      "plugins",
      "ecc-hooks",
    ),
  ];
}

async function pluginInstalled(): Promise<boolean> {
  try {
    await access(hooksPluginDir());
    return true;
  } catch {
    return false;
  }
}

async function resolvePluginSource(): Promise<string | null> {
  for (const candidate of pluginSourceCandidates()) {
    try {
      await access(candidate);
      return candidate;
    } catch {
      // try next candidate
    }
  }

  return null;
}

async function copyIfExists(source: string, target: string): Promise<void> {
  try {
    await access(source);
  } catch {
    return;
  }

  await cp(source, target, { recursive: true, force: true });
}

async function installHooksPlugin(): Promise<{
  target: string;
  source: string | null;
}> {
  const target = hooksPluginDir();
  const source = await resolvePluginSource();

  if (!source) {
    return { target, source: null };
  }

  await rm(target, { recursive: true, force: true });
  await mkdir(target, { recursive: true });

  await copyIfExists(join(source, "README.md"), join(target, "README.md"));
  await copyIfExists(
    join(source, "package.json"),
    join(target, "package.json"),
  );
  await copyIfExists(
    join(source, ".claude-plugin"),
    join(target, ".claude-plugin"),
  );
  await copyIfExists(join(source, "hooks"), join(target, "hooks"));
  await copyIfExists(join(source, "scripts"), join(target, "scripts"));

  return { target, source };
}

async function confirmUninstall(): Promise<boolean> {
  const answer = await inquirer.prompt([
    {
      type: "confirm",
      name: "confirmed",
      message: t("hooks.uninstall_confirm"),
      default: false,
    },
  ]);

  return Boolean(answer.confirmed);
}

export function registerHooksCommands(program: Command): void {
  const hooks = program.command("hooks").description(t("cmd.hooks"));

  hooks
    .command("install")
    .description(t("cmd.hooks_install"))
    .action(async () => {
      const installed = await installHooksPlugin();
      if (!installed.source) {
        printError(t("hooks.source_not_found"));
        process.exitCode = 1;
        return;
      }

      printSuccess(t("hooks.installed", { path: installed.target }));
      printWarning(t("hooks.source", { path: installed.source }));
    });

  hooks
    .command("uninstall")
    .description(t("cmd.hooks_uninstall"))
    .option("--yes", t("opt.yes"))
    .action(async (options: { yes?: boolean }) => {
      const installed = await pluginInstalled();
      if (!installed) {
        printWarning(t("hooks.not_installed"));
        return;
      }

      const proceed = options.yes ? true : await confirmUninstall();
      if (!proceed) {
        printWarning(t("hooks.uninstall_cancelled"));
        return;
      }

      const dir = hooksPluginDir();
      await rm(dir, { recursive: true, force: true });
      printSuccess(t("hooks.removed", { path: dir }));
    });

  hooks
    .command("status")
    .description(t("cmd.hooks_status"))
    .action(async () => {
      printSuccess(`installed=${await pluginInstalled()}`);
    });
}
