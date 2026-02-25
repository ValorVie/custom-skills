import { readdir } from "node:fs/promises";
import { extname } from "node:path";

import type { Command } from "commander";

import {
  COPY_TARGETS,
  type ResourceType,
  type TargetType,
} from "../utils/shared";

type ResourceItem = {
  name: string;
  target: TargetType;
  type: ResourceType;
};

async function getResourceNames(
  resourcePath: string,
  resourceType: ResourceType,
): Promise<string[]> {
  try {
    const entries = await readdir(resourcePath, { withFileTypes: true });
    if (resourceType === "skills") {
      return entries
        .filter((entry) => entry.isDirectory() && !entry.name.startsWith("."))
        .map((entry) => entry.name)
        .sort((a, b) => a.localeCompare(b));
    }

    return entries
      .filter((entry) => entry.isFile())
      .map((entry) =>
        extname(entry.name) === ".md" ? entry.name.slice(0, -3) : entry.name,
      )
      .sort((a, b) => a.localeCompare(b));
  } catch {
    return [];
  }
}

export function registerListCommand(program: Command): void {
  program
    .command("list")
    .description("List installed resources")
    .option("--target <target>", "Target platform")
    .option("--type <type>", "Resource type: skills|commands|agents|workflows")
    .option("--json", "Output as JSON")
    .action(
      async (options: {
        target?: TargetType;
        type?: ResourceType;
        json?: boolean;
      }) => {
        const targets = options.target
          ? [options.target]
          : (Object.keys(COPY_TARGETS) as TargetType[]);

        const output: ResourceItem[] = [];

        for (const target of targets) {
          const targetMap = COPY_TARGETS[target];
          const resourceTypes = options.type
            ? [options.type]
            : (Object.keys(targetMap) as ResourceType[]);

          for (const resourceType of resourceTypes) {
            const resourcePath = targetMap[resourceType];
            if (!resourcePath) {
              continue;
            }
            const names = await getResourceNames(resourcePath, resourceType);
            for (const name of names) {
              output.push({
                name,
                target,
                type: resourceType,
              });
            }
          }
        }

        if (options.json) {
          console.log(JSON.stringify(output, null, 2));
          return;
        }

        if (output.length === 0) {
          console.log("No resources found.");
          return;
        }

        for (const item of output) {
          console.log(`${item.target}/${item.type}: ${item.name}`);
        }
      },
    );
}
