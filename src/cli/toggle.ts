import { access, readdir, rename } from "node:fs/promises";
import { join } from "node:path";

import type { Command } from "commander";
import chalk from "chalk";

import { printError, printTable } from "../utils/formatter";
import { t } from "../utils/i18n";
import {
  COPY_TARGETS,
  type ResourceType,
  TARGET_NAMES,
  type TargetType,
} from "../utils/shared";

const DISABLED_SUFFIX = ".disabled";

type ToggleStateItem = {
  target: TargetType;
  type: ResourceType;
  name: string;
  enabled: boolean;
};

async function pathExists(path: string): Promise<boolean> {
  try {
    await access(path);
    return true;
  } catch {
    return false;
  }
}

function isTarget(value: string): value is TargetType {
  return value in COPY_TARGETS;
}

function isResourceType(value: string): value is ResourceType {
  return (
    value === "skills" ||
    value === "commands" ||
    value === "agents" ||
    value === "workflows"
  );
}

function validateTargetType(
  target: string | undefined,
  type: string | undefined,
):
  | { ok: true; target: TargetType; type: ResourceType; basePath: string }
  | { ok: false; message: string } {
  if (!target || !type) {
    return { ok: false, message: t("toggle.missing_target_type") };
  }

  if (!isTarget(target)) {
    return { ok: false, message: t("toggle.invalid_target", { target }) };
  }

  if (!isResourceType(type)) {
    return { ok: false, message: t("toggle.invalid_type", { type }) };
  }

  const basePath = COPY_TARGETS[target][type];
  if (!basePath) {
    return {
      ok: false,
      message: t("toggle.invalid_combo", { target, type }),
    };
  }

  return { ok: true, target, type, basePath };
}

function resourceFileName(type: ResourceType, name: string): string {
  if (type === "skills") {
    return name;
  }
  return name.endsWith(".md") ? name : `${name}.md`;
}

async function disableResource(
  target: TargetType,
  type: ResourceType,
  name: string,
): Promise<boolean> {
  const base = COPY_TARGETS[target][type];
  if (!base) {
    return false;
  }

  const activePath = join(base, resourceFileName(type, name));
  const disabledPath = `${activePath}${DISABLED_SUFFIX}`;

  if (!(await pathExists(activePath))) {
    return false;
  }

  await rename(activePath, disabledPath);
  return true;
}

async function enableResource(
  target: TargetType,
  type: ResourceType,
  name: string,
): Promise<boolean> {
  const base = COPY_TARGETS[target][type];
  if (!base) {
    return false;
  }

  const activePath = join(base, resourceFileName(type, name));
  const disabledPath = `${activePath}${DISABLED_SUFFIX}`;

  if (!(await pathExists(disabledPath))) {
    return false;
  }

  await rename(disabledPath, activePath);
  return true;
}

function parseToggleEntry(
  type: ResourceType,
  rawName: string,
): ToggleStateItem["name"] {
  const withoutDisabled = rawName.endsWith(DISABLED_SUFFIX)
    ? rawName.slice(0, -DISABLED_SUFFIX.length)
    : rawName;

  if (type === "skills") {
    return withoutDisabled;
  }

  return withoutDisabled.endsWith(".md")
    ? withoutDisabled.slice(0, -3)
    : withoutDisabled;
}

async function listToggleState(
  target: TargetType,
  type: ResourceType,
): Promise<ToggleStateItem[]> {
  const base = COPY_TARGETS[target][type];
  if (!base) {
    return [];
  }

  try {
    const entries = await readdir(base, { withFileTypes: true });
    return entries
      .filter((entry) => {
        if (entry.name.startsWith(".")) {
          return false;
        }
        return type === "skills" ? entry.isDirectory() : entry.isFile();
      })
      .map((entry) => ({
        target,
        type,
        name: parseToggleEntry(type, entry.name),
        enabled: !entry.name.endsWith(DISABLED_SUFFIX),
      }))
      .sort((a, b) => a.name.localeCompare(b.name));
  } catch {
    return [];
  }
}

async function listAllToggleStates(
  target?: string,
  type?: string,
): Promise<ToggleStateItem[] | { error: string }> {
  if (target || type) {
    const validated = validateTargetType(target, type);
    if (!validated.ok) {
      return { error: validated.message };
    }
    return await listToggleState(validated.target, validated.type);
  }

  const items: ToggleStateItem[] = [];

  for (const targetKey of Object.keys(COPY_TARGETS) as TargetType[]) {
    for (const typeKey of [
      "skills",
      "commands",
      "agents",
      "workflows",
    ] as const) {
      if (!COPY_TARGETS[targetKey][typeKey]) {
        continue;
      }
      items.push(...(await listToggleState(targetKey, typeKey)));
    }
  }

  return items.sort((a, b) => {
    const byTarget = a.target.localeCompare(b.target);
    if (byTarget !== 0) {
      return byTarget;
    }
    const byType = a.type.localeCompare(b.type);
    if (byType !== 0) {
      return byType;
    }
    return a.name.localeCompare(b.name);
  });
}

export function registerToggleCommand(program: Command): void {
  program
    .command("toggle")
    .description(t("cmd.toggle"))
    .option("-t, --target <target>", t("opt.target"))
    .option("-T, --type <type>", t("opt.type"))
    .option("-n, --name <name>", t("opt.name"))
    .option("-e, --enable", t("opt.enable"))
    .option("-d, --disable", t("opt.disable"))
    .option("-l, --list", t("opt.list"))
    .option("--all", t("opt.toggle_all"))
    .action(
      async (options: {
        target?: string;
        type?: string;
        name?: string;
        enable?: boolean;
        disable?: boolean;
        list?: boolean;
        all?: boolean;
      }) => {
        if (options.list) {
          const listed = await listAllToggleStates(
            options.target,
            options.type,
          );
          if (!Array.isArray(listed)) {
            printError(listed.error);
            process.exitCode = 1;
            return;
          }

          if (listed.length === 0) {
            console.log(t("list.no_resources"));
            return;
          }

          printTable(
            ["Target", "Type", "Name", "Status"],
            listed.map((item) => [
              item.target,
              item.type,
              item.name,
              item.enabled ? "Enabled" : "Disabled",
            ]),
          );
          return;
        }

        const validated = validateTargetType(options.target, options.type);
        if (!validated.ok) {
          printError(validated.message);
          process.exitCode = 1;
          return;
        }

        const targetName = TARGET_NAMES[validated.target] ?? validated.target;

        // --all 批次模式
        if (options.all && !options.name) {
          if (options.enable === options.disable) {
            printError(t("toggle.choose_one"));
            process.exitCode = 1;
            return;
          }

          const resources = await listToggleState(validated.target, validated.type);
          let count = 0;
          for (const r of resources) {
            if (options.enable && !r.enabled) {
              const ok = await enableResource(validated.target, validated.type, r.name);
              if (ok) count++;
            } else if (options.disable && r.enabled) {
              const ok = await disableResource(validated.target, validated.type, r.name);
              if (ok) count++;
            }
          }

          const action = options.enable ? t("common.enabled") : t("common.disabled");
          console.log(chalk.green(`✓ ${t("toggle.batch_done", { action, count: String(count), target: targetName, type: validated.type })}`));
          console.log(chalk.dim(t("toggle.restart_hint", { target: targetName })));
          return;
        }

        // 單一資源模式
        if (!options.name) {
          printError(t("toggle.missing_name"));
          process.exitCode = 1;
          return;
        }

        if (options.enable === options.disable) {
          printError(t("toggle.choose_one"));
          process.exitCode = 1;
          return;
        }

        const success = options.enable
          ? await enableResource(validated.target, validated.type, options.name)
          : await disableResource(validated.target, validated.type, options.name);

        if (!success) {
          // 可能是已經在目標狀態
          if (options.enable) {
            console.log(chalk.dim(t("toggle.already_enabled", { name: options.name })));
          } else {
            console.log(chalk.dim(t("toggle.already_disabled", { name: options.name })));
          }
          return;
        }

        if (options.enable) {
          console.log(chalk.green(`✓ ${t("toggle.enabled", { target: targetName, type: validated.type, name: options.name })}`));
        } else {
          console.log(chalk.yellow(`✓ ${t("toggle.disabled", { target: targetName, type: validated.type, name: options.name })}`));
        }
        console.log(chalk.dim(t("toggle.restart_hint", { target: targetName })));
      },
    );
}
