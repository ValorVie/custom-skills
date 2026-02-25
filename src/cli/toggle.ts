import { access, readdir, rename } from "node:fs/promises";
import { join } from "node:path";

import type { Command } from "commander";

import {
  COPY_TARGETS,
  type ResourceType,
  type TargetType,
} from "../utils/shared";

const DISABLED_SUFFIX = ".disabled";

async function pathExists(path: string): Promise<boolean> {
  try {
    await access(path);
    return true;
  } catch {
    return false;
  }
}

function resourceBasePath(
  target: TargetType,
  type: ResourceType,
): string | null {
  const value = COPY_TARGETS[target][type];
  return value ?? null;
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
  const base = resourceBasePath(target, type);
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
  const base = resourceBasePath(target, type);
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

async function listDisabledResources(
  target: TargetType,
  type: ResourceType,
): Promise<string[]> {
  const base = resourceBasePath(target, type);
  if (!base) {
    return [];
  }

  try {
    const entries = await readdir(base, { withFileTypes: true });
    return entries
      .filter((entry) => entry.name.endsWith(DISABLED_SUFFIX))
      .map((entry) =>
        entry.name.replace(DISABLED_SUFFIX, "").replace(/\.md$/, ""),
      )
      .sort((a, b) => a.localeCompare(b));
  } catch {
    return [];
  }
}

export function registerToggleCommand(program: Command): void {
  program
    .command("toggle")
    .description("Enable or disable installed resources")
    .requiredOption("--target <target>", "Target platform")
    .requiredOption("--type <type>", "Resource type")
    .option("--name <name>", "Resource name")
    .option("--enable", "Enable resource")
    .option("--disable", "Disable resource")
    .option("--list", "List disabled resources")
    .action(
      async (options: {
        target: TargetType;
        type: ResourceType;
        name?: string;
        enable?: boolean;
        disable?: boolean;
        list?: boolean;
      }) => {
        if (options.list) {
          const items = await listDisabledResources(
            options.target,
            options.type,
          );
          if (items.length === 0) {
            console.log("No disabled resources.");
            return;
          }
          for (const item of items) {
            console.log(item);
          }
          return;
        }

        if (!options.name) {
          console.error("Missing --name option");
          process.exitCode = 1;
          return;
        }

        if (options.enable === options.disable) {
          console.error("Choose exactly one: --enable or --disable");
          process.exitCode = 1;
          return;
        }

        const success = options.enable
          ? await enableResource(options.target, options.type, options.name)
          : await disableResource(options.target, options.type, options.name);

        if (!success) {
          console.error("Resource toggle failed.");
          process.exitCode = 1;
          return;
        }

        console.log(options.enable ? "Enabled" : "Disabled");
      },
    );
}
