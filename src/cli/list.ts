import { readdir } from "node:fs/promises";
import { join } from "node:path";

import chalk from "chalk";
import type { Command } from "commander";

import { loadCustomRepos } from "../utils/custom-repos";
import { printTable } from "../utils/formatter";
import { t } from "../utils/i18n";
import { paths } from "../utils/paths";
import {
  COPY_TARGETS,
  REPOS,
  type ResourceType,
  type TargetType,
} from "../utils/shared";

type ResourceItem = {
  name: string;
  target: TargetType;
  type: ResourceType;
  enabled: boolean;
  source: string;
};

type SourceIndex = Record<ResourceType, Map<string, string>>;

const DISABLED_SUFFIX = ".disabled";

type SourceRoot = {
  source: string;
  root: string;
};

type ResourceEntry = {
  name: string;
  enabled: boolean;
};

function createSourceIndex(): SourceIndex {
  return {
    skills: new Map<string, string>(),
    commands: new Map<string, string>(),
    agents: new Map<string, string>(),
    workflows: new Map<string, string>(),
  };
}

async function listFilesRecursive(
  baseDir: string,
  relativeDir = "",
): Promise<string[]> {
  const currentDir = relativeDir ? join(baseDir, relativeDir) : baseDir;
  const entries = await readdir(currentDir, { withFileTypes: true });
  const files: string[] = [];

  for (const entry of entries) {
    if (entry.name.startsWith(".")) {
      continue;
    }

    const relativePath = relativeDir
      ? `${relativeDir}/${entry.name}`
      : entry.name;

    if (entry.isDirectory()) {
      files.push(...(await listFilesRecursive(baseDir, relativePath)));
      continue;
    }

    files.push(relativePath);
  }

  return files;
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

function addToIndex(
  index: SourceIndex,
  resourceType: ResourceType,
  name: string,
  source: string,
): void {
  if (!index[resourceType].has(name)) {
    index[resourceType].set(name, source);
  }
}

async function indexSourceRoot(
  index: SourceIndex,
  sourceRoot: SourceRoot,
): Promise<void> {
  const skillDir = join(sourceRoot.root, "skills");
  try {
    const skillEntries = await readdir(skillDir, { withFileTypes: true });
    for (const entry of skillEntries) {
      if (entry.isDirectory() && !entry.name.startsWith(".")) {
        addToIndex(index, "skills", entry.name, sourceRoot.source);
      }
    }
  } catch {
    // ignore missing skills
  }

  for (const type of ["commands", "agents", "workflows"] as const) {
    const typeDir = join(sourceRoot.root, type);
    try {
      const files = await listFilesRecursive(typeDir);
      for (const file of files) {
        if (!file.endsWith(".md")) {
          continue;
        }
        const name = file.split("/").at(-1)?.replace(/\.md$/, "");
        if (!name) {
          continue;
        }
        addToIndex(index, type, name, sourceRoot.source);
      }
    } catch {
      // ignore missing type directories
    }
  }
}

async function collectSourceIndex(): Promise<SourceIndex> {
  const index = createSourceIndex();
  const roots: SourceRoot[] = [
    { source: "custom-skills", root: process.cwd() },
  ];

  for (const repo of REPOS) {
    if (repo.dir === process.cwd()) {
      continue;
    }
    roots.push({ source: repo.name, root: repo.dir });
  }

  const custom = await loadCustomRepos();
  for (const [name, repo] of Object.entries(custom.repos)) {
    roots.push({ source: name, root: repo.localPath });
  }

  roots.push({
    source: "everything-claude-code",
    root: paths.everythingClaudeCodeRepo,
  });
  roots.push({ source: "anthropic-skills", root: paths.anthropicSkillsRepo });
  roots.push({ source: "obsidian-skills", root: paths.obsidianSkillsRepo });
  roots.push({ source: "auto-skill", root: paths.autoSkillRepo });

  for (const root of roots) {
    await indexSourceRoot(index, root);
  }

  return index;
}

export function registerListCommand(program: Command): void {
  program
    .command("list")
    .description("List installed resources")
    .option("--target <target>", "Target platform")
    .option("--type <type>", "Resource type: skills|commands|agents|workflows")
    .option("--hide-disabled", "Hide disabled resources")
    .option("--json", "Output as JSON")
    .action(
      async (options: {
        target?: TargetType;
        type?: ResourceType;
        hideDisabled?: boolean;
        json?: boolean;
      }) => {
        const targets = options.target
          ? [options.target]
          : (Object.keys(COPY_TARGETS) as TargetType[]);

        const output: ResourceItem[] = [];
        const sourceIndex = await collectSourceIndex();

        for (const target of targets) {
          const targetMap = COPY_TARGETS[target];
          const resourceTypes = options.type
            ? [options.type]
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
                source:
                  sourceIndex[resourceType].get(entry.name) ?? "user-custom",
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

        printTable(
          ["Target", "Type", "Name", "Status", "Source"],
          output.map((item) => [
            item.target,
            item.type,
            item.name,
            item.enabled
              ? chalk.green(t("list.status_enabled"))
              : chalk.red(t("list.status_disabled")),
            item.source,
          ]),
        );
      },
    );
}
