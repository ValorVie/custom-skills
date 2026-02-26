import { createHash } from "node:crypto";
import { cp, mkdir, readdir, readFile, rm, stat, writeFile } from "node:fs/promises";
import { homedir } from "node:os";
import { basename, join, relative } from "node:path";
import YAML from "yaml";

const IGNORED_DIRS = new Set([".git", "node_modules", "__pycache__"]);
const IGNORED_FILE_SUFFIXES = new Set([".pyc", ".pyo"]);

export async function computeFileHash(filePath: string): Promise<string> {
  const content = await readFile(filePath);
  const hash = createHash("sha256").update(content).digest("hex");
  return `sha256:${hash}`;
}

async function collectFiles(
  rootPath: string,
  currentPath: string,
): Promise<string[]> {
  const entries = await readdir(currentPath, { withFileTypes: true });
  const files: string[] = [];

  for (const entry of entries) {
    if (entry.isDirectory()) {
      if (IGNORED_DIRS.has(entry.name)) {
        continue;
      }
      const childPath = join(currentPath, entry.name);
      const childFiles = await collectFiles(rootPath, childPath);
      files.push(...childFiles);
      continue;
    }

    if (!entry.isFile()) {
      continue;
    }

    const hasIgnoredSuffix = [...IGNORED_FILE_SUFFIXES].some((suffix) =>
      entry.name.endsWith(suffix),
    );
    if (hasIgnoredSuffix) {
      continue;
    }

    const fullPath = join(currentPath, entry.name);
    files.push(relative(rootPath, fullPath));
  }

  return files;
}

export async function computeDirHash(path: string): Promise<string> {
  const pathStat = await stat(path);
  if (pathStat.isFile()) {
    return await computeFileHash(path);
  }

  const filePaths = (await collectFiles(path, path)).sort((a, b) =>
    a.localeCompare(b),
  );
  const digest = createHash("sha256");

  for (const relativePath of filePaths) {
    const fullPath = join(path, relativePath);
    const fileHash = await computeFileHash(fullPath);
    digest.update(relativePath);
    digest.update(fileHash);
  }

  return `sha256:${digest.digest("hex")}`;
}

export type ResourceType = "skills" | "commands" | "agents" | "workflows";

export interface FileRecord {
  name: string;
  hash: string;
  source: string;
  sourcePath: string;
}

export interface ConflictInfo {
  name: string;
  resourceType: ResourceType;
  oldHash: string;
  newHash: string;
}

export interface ManifestFiles {
  skills: Record<string, { hash: string; source: string }>;
  commands: Record<string, { hash: string; source: string }>;
  agents: Record<string, { hash: string; source: string }>;
  workflows: Record<string, { hash: string; source: string }>;
}

export interface ManifestData {
  managedBy: "ai-dev";
  version: string;
  lastSync: string;
  target: string;
  files: ManifestFiles;
}

export class ManifestTracker {
  readonly skills = new Map<string, FileRecord>();
  readonly commands = new Map<string, FileRecord>();
  readonly agents = new Map<string, FileRecord>();
  readonly workflows = new Map<string, FileRecord>();

  constructor(public readonly target: string) {}

  async recordSkill(
    name: string,
    sourcePath: string,
    source = "custom-skills",
  ): Promise<void> {
    this.skills.set(name, {
      name,
      hash: await computeDirHash(sourcePath),
      source,
      sourcePath,
    });
  }

  async recordCommand(
    name: string,
    sourcePath: string,
    source = "custom-skills",
  ): Promise<void> {
    this.commands.set(name, {
      name,
      hash: await computeFileHash(sourcePath),
      source,
      sourcePath,
    });
  }

  async recordAgent(
    name: string,
    sourcePath: string,
    source = "custom-skills",
  ): Promise<void> {
    this.agents.set(name, {
      name,
      hash: await computeFileHash(sourcePath),
      source,
      sourcePath,
    });
  }

  async recordWorkflow(
    name: string,
    sourcePath: string,
    source = "custom-skills",
  ): Promise<void> {
    this.workflows.set(name, {
      name,
      hash: await computeFileHash(sourcePath),
      source,
      sourcePath,
    });
  }

  toManifest(version: string): ManifestData {
    const toObject = (records: Map<string, FileRecord>) =>
      Object.fromEntries(
        [...records.entries()].map(([name, record]) => [
          name,
          {
            hash: record.hash,
            source: record.source,
          },
        ]),
      );

    return {
      managedBy: "ai-dev",
      version,
      lastSync: new Date().toISOString(),
      target: this.target,
      files: {
        skills: toObject(this.skills),
        commands: toObject(this.commands),
        agents: toObject(this.agents),
        workflows: toObject(this.workflows),
      },
    };
  }
}

function trackerRecords(
  tracker: ManifestTracker,
  resourceType: ResourceType,
): Map<string, FileRecord> {
  switch (resourceType) {
    case "skills":
      return tracker.skills;
    case "commands":
      return tracker.commands;
    case "agents":
      return tracker.agents;
    default:
      return tracker.workflows;
  }
}

export function detectConflicts(
  oldManifest: ManifestData | null,
  tracker: ManifestTracker,
): ConflictInfo[] {
  if (!oldManifest) {
    return [];
  }

  const conflicts: ConflictInfo[] = [];

  for (const resourceType of [
    "skills",
    "commands",
    "agents",
    "workflows",
  ] as const) {
    const oldRecords = oldManifest.files[resourceType] ?? {};
    const newRecords = trackerRecords(tracker, resourceType);

    for (const [name, record] of newRecords.entries()) {
      const oldRecord = oldRecords[name];
      if (!oldRecord) {
        continue;
      }
      if (oldRecord.hash !== record.hash) {
        conflicts.push({
          name,
          resourceType,
          oldHash: oldRecord.hash,
          newHash: record.hash,
        });
      }
    }
  }

  return conflicts;
}

export function findOrphans(
  oldManifest: ManifestData | null,
  newManifest: ManifestData,
): Record<ResourceType, string[]> {
  const empty: Record<ResourceType, string[]> = {
    skills: [],
    commands: [],
    agents: [],
    workflows: [],
  };

  if (!oldManifest) {
    return empty;
  }

  for (const resourceType of [
    "skills",
    "commands",
    "agents",
    "workflows",
  ] as const) {
    const oldNames = new Set(
      Object.keys(oldManifest.files[resourceType] ?? {}),
    );
    const newNames = new Set(
      Object.keys(newManifest.files[resourceType] ?? {}),
    );

    empty[resourceType] = [...oldNames]
      .filter((name) => !newNames.has(name))
      .sort((a, b) => a.localeCompare(b));
  }

  return empty;
}

function orphanPath(
  basePath: string,
  resourceType: ResourceType,
  name: string,
): string {
  if (resourceType === "skills") {
    return join(basePath, name);
  }
  return join(basePath, `${name}.md`);
}

export async function cleanupOrphans(
  targetPaths: Partial<Record<ResourceType, string>>,
  orphans: Record<ResourceType, string[]>,
): Promise<number> {
  let removed = 0;

  for (const resourceType of [
    "skills",
    "commands",
    "agents",
    "workflows",
  ] as const) {
    const basePath = targetPaths[resourceType];
    if (!basePath) {
      continue;
    }

    for (const name of orphans[resourceType]) {
      const path = orphanPath(basePath, resourceType, name);
      await rm(path, { recursive: true, force: true });
      removed += 1;
    }
  }

  return removed;
}

export async function backupFile(
  sourcePath: string,
  backupRoot: string,
): Promise<string | null> {
  try {
    const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
    const backupPath = join(
      backupRoot,
      `${basename(sourcePath)}.${timestamp}.bak`,
    );
    await mkdir(backupRoot, { recursive: true });
    await cp(sourcePath, backupPath, { recursive: true, force: true });
    return backupPath;
  } catch {
    return null;
  }
}

function getManifestDir(): string {
  return join(homedir(), ".config", "ai-dev", "manifests");
}

function getManifestPath(target: string): string {
  return join(getManifestDir(), `${target}.yaml`);
}

function toSnakeCaseManifest(manifest: ManifestData): Record<string, unknown> {
  return {
    managed_by: manifest.managedBy,
    version: manifest.version,
    last_sync: manifest.lastSync,
    target: manifest.target,
    files: manifest.files,
  };
}

function fromSnakeCaseManifest(raw: Record<string, unknown>): ManifestData {
  return {
    managedBy: (raw.managed_by ?? raw.managedBy) as "ai-dev",
    version: raw.version as string,
    lastSync: (raw.last_sync ?? raw.lastSync) as string,
    target: raw.target as string,
    files: raw.files as ManifestFiles,
  };
}

export async function readManifest(
  target: string,
): Promise<ManifestData | null> {
  try {
    const content = await readFile(getManifestPath(target), "utf8");
    const raw = YAML.parse(content);
    if (!raw || typeof raw !== "object" || !raw.files) {
      return null;
    }
    return fromSnakeCaseManifest(raw as Record<string, unknown>);
  } catch {
    return null;
  }
}

export async function writeManifest(
  target: string,
  manifest: ManifestData,
): Promise<void> {
  const dir = getManifestDir();
  await mkdir(dir, { recursive: true });
  const content = YAML.stringify(toSnakeCaseManifest(manifest));
  await writeFile(getManifestPath(target), content, "utf8");
}

export const detect_conflicts = detectConflicts;
export const find_orphans = findOrphans;
export const cleanup_orphans = cleanupOrphans;
export const backup_file = backupFile;
export const read_manifest = readManifest;
export const write_manifest = writeManifest;
