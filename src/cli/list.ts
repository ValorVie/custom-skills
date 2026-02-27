import { readdir } from "node:fs/promises";

import chalk from "chalk";
import type { Command } from "commander";

import {
  collectSourceIndex,
  resolveResourceSource,
} from "../tui/utils/source-index";
import { printError, printTable } from "../utils/formatter";
import { t } from "../utils/i18n";
import { COPY_TARGETS, type ResourceType, type TargetType } from "../utils/shared";

type ResourceItem = {
  name: string;
  target: TargetType;
  type: ResourceType;
  enabled: boolean;
  source: string;
};

const DISABLED_SUFFIX = ".disabled";

type ResourceEntry = {
  name: string;
  enabled: boolean;
};

function formatTargetLabel(target: TargetType): string {
  switch (target) {
    case "claude":
      return "Claude Code";
    case "antigravity":
      return "Antigravity";
    case "opencode":
      return "OpenCode";
    case "codex":
      return "Codex";
    case "gemini":
      return "Gemini";
    default:
      return target;
  }
}

function formatTypeLabel(type: ResourceType): string {
  switch (type) {
    case "skills":
      return "Skills";
    case "commands":
      return "Commands";
    case "agents":
      return "Agents";
    case "workflows":
      return "Workflows";
    default:
      return type;
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

function validateListOptions(
  target: string | undefined,
  type: string | undefined,
):
  | { ok: true; target?: TargetType; type?: ResourceType }
  | { ok: false; message: string } {
  if (target && !isTarget(target)) {
    return { ok: false, message: t("toggle.invalid_target", { target }) };
  }

  if (type && !isResourceType(type)) {
    return { ok: false, message: t("toggle.invalid_type", { type }) };
  }

  if (target && type && !COPY_TARGETS[target][type]) {
    return { ok: false, message: t("toggle.invalid_combo", { target, type }) };
  }

  return { ok: true, target, type };
}

function parseResourceEntry(
  rawName: string,
  type: ResourceType,
): ResourceEntry {
  const enabled = !rawName.endsWith(DISABLED_SUFFIX);
  const withoutDisabled = enabled
    ? rawName
    : rawName.slice(0, -DISABLED_SUFFIX.length);

  if (type === "skills") {
    return { name: withoutDisabled, enabled };
  }

  const name = withoutDisabled.endsWith(".md")
    ? withoutDisabled.slice(0, -3)
    : withoutDisabled;
  return { name, enabled };
}

async function getResourceEntries(
  resourcePath: string,
  resourceType: ResourceType,
): Promise<ResourceEntry[]> {
  try {
    const entries = await readdir(resourcePath, { withFileTypes: true });

    const picked = entries.filter((entry) => {
      if (entry.name.startsWith(".")) {
        return false;
      }

      if (resourceType === "skills") {
        return entry.isDirectory();
      }

      return entry.isFile();
    });

    return picked
      .map((entry) => parseResourceEntry(entry.name, resourceType))
      .sort((a, b) => a.name.localeCompare(b.name));
  } catch {
    return [];
  }
}

export function registerListCommand(program: Command): void {
  program
    .command("list")
    .description(t("cmd.list"))
    .option("-t, --target <target>", t("opt.target"))
    .option("-T, --type <type>", t("opt.type"))
    .option("-H, --hide-disabled", t("opt.hide_disabled"))
    .option("--json", t("opt.json"))
    .action(
      async (options: {
        target?: string;
        type?: string;
        hideDisabled?: boolean;
        json?: boolean;
      }) => {
        const validated = validateListOptions(options.target, options.type);
        if (!validated.ok) {
          printError(validated.message);
          process.exitCode = 1;
          return;
        }

        const targets = validated.target
          ? [validated.target]
          : (Object.keys(COPY_TARGETS) as TargetType[]);

        const output: ResourceItem[] = [];
        const sourceIndex = await collectSourceIndex();

        for (const target of targets) {
          const targetMap = COPY_TARGETS[target];
          const resourceTypes = validated.type
            ? [validated.type]
            : (["skills", "commands", "agents", "workflows"] as const).filter(
                (type) => Boolean(targetMap[type]),
              );

          for (const resourceType of resourceTypes) {
            const resourcePath = targetMap[resourceType];
            if (!resourcePath) {
              continue;
            }

            const entries = await getResourceEntries(
              resourcePath,
              resourceType,
            );
            for (const entry of entries) {
              if (options.hideDisabled && !entry.enabled) {
                continue;
              }

              output.push({
                name: entry.name,
                target,
                type: resourceType,
                enabled: entry.enabled,
                source: resolveResourceSource(
                  sourceIndex,
                  resourceType,
                  entry.name,
                ),
              });
            }
          }
        }

        output.sort((a, b) => {
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

        if (options.json) {
          console.log(JSON.stringify(output, null, 2));
          return;
        }

        if (output.length === 0) {
          console.log(t("list.no_resources"));
          return;
        }

        const groups = new Map<string, ResourceItem[]>();
        for (const item of output) {
          const key = `${item.target}:${item.type}`;
          const items = groups.get(key) ?? [];
          items.push(item);
          groups.set(key, items);
        }

        for (const [key, items] of groups) {
          const [target, type] = key.split(":") as [TargetType, ResourceType];
          const title = `${formatTargetLabel(target)} - ${formatTypeLabel(type)}`;

          printTable(
            [t("list.col_name"), t("list.col_source"), t("list.col_status")],
            items.map((item) => [
              item.name,
              item.source,
              item.enabled
                ? chalk.green(t("list.status_enabled"))
                : chalk.red(t("list.status_disabled")),
            ]),
            { title },
          );
        }
      },
    );
}
