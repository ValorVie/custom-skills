import { readFileSync } from "node:fs";
import { access, cp, mkdir, readdir, rename, rm, symlink } from "node:fs/promises";
import { homedir } from "node:os";
import { dirname, join } from "node:path";

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
  TARGET_NAMES,
  type TargetType,
} from "../utils/shared";

export type ConflictAction = "force" | "skip" | "backup" | "abort";

export interface DistributeOptions {
  force?: boolean;
  skipConflicts?: boolean;
  backup?: boolean;
  devMode?: boolean;
  sourceRoot?: string;
  targets?: TargetType[];
  onProgress?: (message: string) => void;
  onConflict?: (conflicts: ConflictInfo[]) => Promise<ConflictAction>;
}

export interface DistributedItem {
  name: string;
  target: TargetType;
  type: ResourceType | "plugins";
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
  aborted?: boolean;
}

const RESOURCE_TYPES: ResourceType[] = [
  "skills",
  "commands",
  "agents",
  "workflows",
];

const OPENCODE_PLUGIN_SOURCE_NAME = "ecc-hooks-opencode";

function shortenPath(p: string): string {
  const home = homedir();
  return p.startsWith(home) ? p.replace(home, "~") : p;
}

async function pathExists(pathValue: string): Promise<boolean> {
  try {
    await access(pathValue);
    return true;
  } catch {
    return false;
  }
}

async function migrateOpencodePluginDirIfNeeded(
  targetMap: Partial<Record<ResourceType | "plugins", string>>,
  onProgress: (message: string) => void,
): Promise<void> {
  const modernDir = targetMap.plugins;
  if (!modernDir) {
    return;
  }

  const legacyDir = join(dirname(modernDir), "plugin");
  if (!(await pathExists(legacyDir))) {
    return;
  }

  await mkdir(dirname(modernDir), { recursive: true });

  if (!(await pathExists(modernDir))) {
    await rename(legacyDir, modernDir);
    onProgress(
      `偵測到 OpenCode legacy plugin 路徑，已遷移：${shortenPath(legacyDir)} → ${shortenPath(modernDir)}`,
    );
    return;
  }

  onProgress(
    `偵測到 OpenCode 新舊 plugin 路徑並存：${shortenPath(legacyDir)} 與 ${shortenPath(modernDir)}。將以 plugins 路徑為主要目標並保留 legacy 相容。`,
  );
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
    const targetName = TARGET_NAMES[target] ?? target;

    try {
      if (target === "opencode") {
        await migrateOpencodePluginDirIfNeeded(targetMap, onProgress);
      }

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

      // Track which conflicts were skipped (to preserve old hash in new manifest)
      const skippedConflicts = new Map<string, ConflictInfo>();

      // Step 5: Handle conflicts
      if (conflicts.length > 0) {
        let action: ConflictAction;

        if (force) {
          action = "force";
        } else if (skipConflicts) {
          action = "skip";
        } else if (backup) {
          action = "backup";
        } else if (options.onConflict) {
          action = await options.onConflict(conflicts);
        } else {
          // No callback and no flag → default skip (CLI should provide onConflict)
          action = "skip";
        }

        if (action === "abort") {
          result.aborted = true;
          continue; // Skip this target, proceed to next
        }

        for (const conflict of conflicts) {
          const key = `${conflict.resourceType}:${conflict.name}`;
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
              join(targetMap[conflict.resourceType] ?? "", conflict.name),
            ],
          });

          if (action === "skip") {
            skippedConflicts.set(key, conflict);
          } else if (action === "backup") {
            const destinationBase = targetMap[conflict.resourceType];
            if (destinationBase) {
              await backupFile(
                join(destinationBase, conflict.name),
                join(paths.aiDevConfig, "backups", target, conflict.resourceType),
              );
            }
          }
          // action === "force": do nothing, copy phase will overwrite
        }
      }

      // Step 6: Execute copies and build new manifest tracker
      const copyTracker = new ManifestTracker(target);

      for (const type of RESOURCE_TYPES) {
        const destinationBase = targetMap[type];
        if (!destinationBase) continue;

        const sourceDir = sourceDirectory(sourceRoot, target, type);
        const resources = await listResources(sourceDir, type);

        if (resources.length === 0) continue;

        // Emit resource-level progress (v1 format: type → target name, source → dest)
        onProgress(`${type} → ${targetName}`);
        onProgress(`  ${shortenPath(sourceDir)} → ${shortenPath(destinationBase)}`);

        await mkdir(destinationBase, { recursive: true });

        for (const name of resources) {
          const key = `${type}:${name}`;
          const sourcePath = join(sourceDir, name);
          const destinationPath = join(destinationBase, name);

          try {
            // If this resource was marked as skipped conflict, skip copy
            if (skippedConflicts.has(key)) {
              onProgress(`  跳過（衝突）: ${name}`);
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

      if (target === "opencode" && targetMap.plugins) {
        const sourcePluginsDir = join(
          sourceRoot,
          "plugins",
          OPENCODE_PLUGIN_SOURCE_NAME,
        );

        if (await pathExists(sourcePluginsDir)) {
          try {
            onProgress(`plugins → ${targetName}`);
            onProgress(
              `  ${shortenPath(sourcePluginsDir)} → ${shortenPath(targetMap.plugins)}`,
            );

            await mkdir(targetMap.plugins, { recursive: true });
            await cp(sourcePluginsDir, targetMap.plugins, {
              recursive: true,
              force: true,
            });

            result.distributed.push({
              name: OPENCODE_PLUGIN_SOURCE_NAME,
              target,
              type: "plugins",
            });
          } catch (error) {
            const message =
              error instanceof Error ? error.message : String(error);
            result.errors.push(
              `${target}/plugins/${OPENCODE_PLUGIN_SOURCE_NAME}: ${message}`,
            );
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
            onProgress(`移除孤兒 ${targetName}/${type}: ${name}`);
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
