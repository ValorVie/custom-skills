import { access, cp, mkdir, readdir, rm, symlink } from "node:fs/promises";
import { join } from "node:path";

import { backupFile, computeDirHash, computeFileHash } from "../utils/manifest";
import { paths } from "../utils/paths";
import {
  COPY_TARGETS,
  type ResourceType,
  type TargetType,
} from "../utils/shared";

export interface DistributeOptions {
  force?: boolean;
  skipConflicts?: boolean;
  backup?: boolean;
  devMode?: boolean;
  sourceRoot?: string;
  targets?: TargetType[];
  onProgress?: (message: string) => void;
}

export interface DistributedItem {
  name: string;
  target: TargetType;
  type: ResourceType;
}

export interface ConflictItem {
  name: string;
  target: TargetType;
  type: ResourceType;
  sources: string[];
}

export interface DistributeResult {
  distributed: DistributedItem[];
  conflicts: ConflictItem[];
  errors: string[];
  unchanged: number;
}

const RESOURCE_TYPES: ResourceType[] = [
  "skills",
  "commands",
  "agents",
  "workflows",
];

async function pathExists(pathValue: string): Promise<boolean> {
  try {
    await access(pathValue);
    return true;
  } catch {
    return false;
  }
}

function sourceDirectory(
  sourceRoot: string,
  target: TargetType,
  type: ResourceType,
): string {
  if (type === "skills") {
    return join(sourceRoot, "skills");
  }

  if (type === "commands") {
    return join(sourceRoot, "commands", target);
  }

  if (type === "agents") {
    return join(sourceRoot, "agents", target);
  }

  if (target === "claude") {
    return join(sourceRoot, "commands", "workflows");
  }

  if (target === "antigravity") {
    return join(sourceRoot, "commands", "antigravity");
  }

  return join(sourceRoot, "workflows", target);
}

async function listResources(
  sourceDir: string,
  type: ResourceType,
): Promise<string[]> {
  try {
    const entries = await readdir(sourceDir, { withFileTypes: true });

    if (type === "skills") {
      return entries
        .filter((entry) => entry.isDirectory() && !entry.name.startsWith("."))
        .map((entry) => entry.name)
        .sort((a, b) => a.localeCompare(b));
    }

    return entries
      .filter((entry) => entry.isFile())
      .map((entry) => entry.name)
      .sort((a, b) => a.localeCompare(b));
  } catch {
    return [];
  }
}

async function resourceHash(
  resourcePath: string,
  type: ResourceType,
): Promise<string> {
  if (type === "skills") {
    return await computeDirHash(resourcePath);
  }

  return await computeFileHash(resourcePath);
}

async function sameResource(
  sourcePath: string,
  destinationPath: string,
  type: ResourceType,
): Promise<boolean> {
  try {
    const [sourceHash, destinationHash] = await Promise.all([
      resourceHash(sourcePath, type),
      resourceHash(destinationPath, type),
    ]);
    return sourceHash === destinationHash;
  } catch {
    return false;
  }
}

async function linkOrCopy(
  sourcePath: string,
  destinationPath: string,
  type: ResourceType,
  devMode: boolean,
): Promise<void> {
  if (devMode) {
    await symlink(
      sourcePath,
      destinationPath,
      type === "skills" ? "dir" : "file",
    );
    return;
  }

  await cp(sourcePath, destinationPath, { recursive: true, force: true });
}

export async function distributeSkills(
  options: DistributeOptions = {},
): Promise<DistributeResult> {
  const sourceRoot = options.sourceRoot ?? process.cwd();
  const force = options.force ?? false;
  const skipConflicts = options.skipConflicts ?? false;
  const backup = options.backup ?? false;
  const devMode = options.devMode ?? false;
  const targets =
    options.targets ?? (Object.keys(COPY_TARGETS) as TargetType[]);
  const onProgress = options.onProgress ?? (() => {});

  const result: DistributeResult = {
    distributed: [],
    conflicts: [],
    errors: [],
    unchanged: 0,
  };

  for (const target of targets) {
    const targetMap = COPY_TARGETS[target];

    for (const type of RESOURCE_TYPES) {
      const destinationBase = targetMap[type];
      if (!destinationBase) {
        continue;
      }

      const sourceDir = sourceDirectory(sourceRoot, target, type);
      const resources = await listResources(sourceDir, type);

      if (resources.length === 0) {
        continue;
      }

      await mkdir(destinationBase, { recursive: true });

      for (const name of resources) {
        const sourcePath = join(sourceDir, name);
        const destinationPath = join(destinationBase, name);

        try {
          const exists = await pathExists(destinationPath);
          if (exists) {
            const unchanged = await sameResource(
              sourcePath,
              destinationPath,
              type,
            );
            if (unchanged) {
              result.unchanged += 1;
              continue;
            }

            if (!force) {
              result.conflicts.push({
                name,
                target,
                type,
                sources: [sourcePath, destinationPath],
              });

              if (skipConflicts) {
                continue;
              }

              continue;
            }

            if (backup) {
              await backupFile(
                destinationPath,
                join(paths.aiDevConfig, "backups", target, type),
              );
            }

            await rm(destinationPath, { recursive: true, force: true });
          }

          await mkdir(join(destinationPath, ".."), { recursive: true });
          await linkOrCopy(sourcePath, destinationPath, type, devMode);
          onProgress(`Distributed ${target}/${type}: ${name}`);

          result.distributed.push({
            name,
            target,
            type,
          });
        } catch (error) {
          const message =
            error instanceof Error ? error.message : String(error);
          result.errors.push(`${target}/${type}/${name}: ${message}`);
        }
      }
    }
  }

  return result;
}
