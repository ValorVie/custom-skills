import { readFileSync } from "node:fs";
import { access, cp, mkdir, readdir, rm, symlink } from "node:fs/promises";
import { join } from "node:path";

import {
  type ConflictInfo,
  ManifestTracker,
  type ResourceType as ManifestResourceType,
  backupFile,
  cleanupOrphans,
  computeDirHash,
  computeFileHash,
  detectConflicts,
  findOrphans,
  readManifest,
  writeManifest,
} from "../utils/manifest";
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
  orphansRemoved: number;
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

function getProjectVersion(): string {
  try {
    const pkgPath = join(import.meta.dirname ?? ".", "..", "..", "package.json");
    const content = readFileSync(pkgPath, "utf8");
    const pkg = JSON.parse(content);
    return pkg.version ?? "0.0.0";
  } catch {
    return "0.0.0";
  }
}

async function recordResource(
  tracker: ManifestTracker,
  type: ResourceType,
  name: string,
  path: string,
  source = "custom-skills",
): Promise<void> {
  switch (type) {
    case "skills":
      await tracker.recordSkill(name, path, source);
      break;
    case "commands":
      await tracker.recordCommand(name, path, source);
      break;
    case "agents":
      await tracker.recordAgent(name, path, source);
      break;
    case "workflows":
      await tracker.recordWorkflow(name, path, source);
      break;
  }
}

/**
 * Build a prescan tracker that records DESTINATION hashes.
 * This is used for conflict detection: compare old manifest hash vs current destination hash.
 */
async function prescanDestinations(
  target: TargetType,
  targetMap: Partial<Record<ResourceType | "plugins", string>>,
  sourceRoot: string,
): Promise<ManifestTracker> {
  const tracker = new ManifestTracker(target);

  for (const type of RESOURCE_TYPES) {
    const destinationBase = targetMap[type];
    if (!destinationBase) continue;

    const sourceDir = sourceDirectory(sourceRoot, target, type);
    const resources = await listResources(sourceDir, type);

    for (const name of resources) {
      const destinationPath = join(destinationBase, name);
      if (await pathExists(destinationPath)) {
        // Record destination hash for conflict detection
        await recordResource(tracker, type, name, destinationPath);
      }
    }
  }

  return tracker;
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
  const version = getProjectVersion();

  const result: DistributeResult = {
    distributed: [],
    conflicts: [],
    errors: [],
    unchanged: 0,
    orphansRemoved: 0,
  };

  for (const target of targets) {
    const targetMap = COPY_TARGETS[target];

    try {
      // Step 1: Read old manifest
      const oldManifest = await readManifest(target);

      // Step 2-3: Prescan destinations to get current destination hashes
      const prescanTracker = await prescanDestinations(
        target,
        targetMap,
        sourceRoot,
      );

      // Step 4: Detect conflicts (old manifest hash vs current destination hash)
      // A conflict means the user modified the destination file after our last distribution
      const conflicts = detectConflicts(oldManifest, prescanTracker);

      // Build a set of conflicting resource names for quick lookup
      const conflictSet = new Set(
        conflicts.map((c) => `${c.resourceType}:${c.name}`),
      );
      // Track which conflicts were skipped (to preserve old hash in new manifest)
      const skippedConflicts = new Map<string, ConflictInfo>();

      // Step 5: Handle conflicts
      for (const conflict of conflicts) {
        const key = `${conflict.resourceType}:${conflict.name}`;

        if (!force) {
          const sourceDir = sourceDirectory(
            sourceRoot,
            target,
            conflict.resourceType,
          );
          result.conflicts.push({
            name: conflict.name,
            target,
            type: conflict.resourceType,
            sources: [
              join(sourceDir, conflict.name),
              join(
                targetMap[conflict.resourceType] ?? "",
                conflict.name,
              ),
            ],
          });

          if (skipConflicts) {
            skippedConflicts.set(key, conflict);
          } else {
            skippedConflicts.set(key, conflict);
          }
        } else if (backup) {
          const destinationBase = targetMap[conflict.resourceType];
          if (destinationBase) {
            await backupFile(
              join(destinationBase, conflict.name),
              join(paths.aiDevConfig, "backups", target, conflict.resourceType),
            );
          }
        }
        // If force=true, conflict is resolved by overwriting (no skip)
      }

      // Step 6: Execute copies and build new manifest tracker
      const copyTracker = new ManifestTracker(target);

      for (const type of RESOURCE_TYPES) {
        const destinationBase = targetMap[type];
        if (!destinationBase) continue;

        const sourceDir = sourceDirectory(sourceRoot, target, type);
        const resources = await listResources(sourceDir, type);

        if (resources.length === 0) continue;

        await mkdir(destinationBase, { recursive: true });

        for (const name of resources) {
          const key = `${type}:${name}`;
          const sourcePath = join(sourceDir, name);
          const destinationPath = join(destinationBase, name);

          try {
            // If this resource has a conflict and we're not forcing, skip copy
            if (conflictSet.has(key) && !force) {
              // Record source hash in tracker anyway (for manifest)
              await recordResource(copyTracker, type, name, sourcePath);
              continue;
            }

            const exists = await pathExists(destinationPath);

            if (exists) {
              // Check if source and destination are the same (unchanged)
              const [sourceH, destH] = await Promise.all([
                resourceHash(sourcePath, type),
                resourceHash(destinationPath, type),
              ]);

              if (sourceH === destH) {
                result.unchanged += 1;
                // Record source hash in tracker
                await recordResource(copyTracker, type, name, sourcePath);
                continue;
              }

              // Remove old destination before copy
              await rm(destinationPath, { recursive: true, force: true });
            }

            await mkdir(join(destinationPath, ".."), { recursive: true });
            await linkOrCopy(sourcePath, destinationPath, type, devMode);
            onProgress(`Distributed ${target}/${type}: ${name}`);

            // Record source hash in tracker
            await recordResource(copyTracker, type, name, sourcePath);

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

      // Step 7: Generate new manifest
      const newManifest = copyTracker.toManifest(version);

      // Step 8: For skipped conflicts, preserve the old manifest hash
      // so that the conflict is detected again next time
      if (oldManifest) {
        for (const [, conflict] of skippedConflicts.entries()) {
          const oldRecord =
            oldManifest.files[conflict.resourceType]?.[conflict.name];
          if (oldRecord) {
            // Preserve old hash so the conflict persists on next run
            newManifest.files[conflict.resourceType][conflict.name] = {
              hash: oldRecord.hash,
              source: oldRecord.source,
            };
          }
        }
      }

      // Step 9-10: Find and cleanup orphans
      const orphans = findOrphans(oldManifest, newManifest);
      const targetPaths: Partial<Record<ManifestResourceType, string>> = {};
      for (const type of RESOURCE_TYPES) {
        if (targetMap[type]) {
          targetPaths[type] = targetMap[type];
        }
      }
      const removed = await cleanupOrphans(targetPaths, orphans);
      result.orphansRemoved += removed;

      if (removed > 0) {
        for (const type of RESOURCE_TYPES) {
          for (const name of orphans[type]) {
            onProgress(`Removed orphan ${target}/${type}: ${name}`);
          }
        }
      }

      // Step 11: Write new manifest
      await writeManifest(target, newManifest);
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      result.errors.push(`${target}: ${message}`);
    }
  }

  return result;
}
