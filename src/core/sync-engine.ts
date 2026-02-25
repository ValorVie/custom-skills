import { cp, mkdir, readFile, rm, writeFile } from "node:fs/promises";
import { basename, join } from "node:path";

import YAML from "yaml";

import { paths } from "../utils/paths";

export interface SyncDirectory {
  path: string;
  repoSubdir: string;
  ignoreProfile: "claude" | "custom";
  customIgnore: string[];
}

export interface SyncConfig {
  version: string;
  remote: string;
  lastSync: string | null;
  directories: SyncDirectory[];
}

export interface SyncSummary {
  added: number;
  updated: number;
  deleted: number;
}

export interface SyncStatus {
  initialized: boolean;
  config: SyncConfig | null;
  repoDir: string;
}

function defaultDirectories(): SyncDirectory[] {
  return [
    {
      path: "~/.claude",
      repoSubdir: "claude",
      ignoreProfile: "claude",
      customIgnore: [],
    },
  ];
}

function expandHome(pathValue: string): string {
  if (!pathValue.startsWith("~/")) {
    return pathValue;
  }
  return join(paths.home, pathValue.slice(2));
}

function makeRepoSubdir(pathValue: string, existing: Set<string>): string {
  const base = basename(pathValue.replace(/[\\/]+$/, "")) || "sync-dir";
  const normalized = base.replace(/[^a-zA-Z0-9._-]/g, "-").toLowerCase();
  let candidate = normalized;
  let index = 2;
  while (existing.has(candidate)) {
    candidate = `${normalized}-${index}`;
    index += 1;
  }
  return candidate;
}

async function pathExists(pathValue: string): Promise<boolean> {
  try {
    await Bun.file(pathValue).stat();
    return true;
  } catch {
    return false;
  }
}

async function syncDirectory(
  sourcePath: string,
  destinationPath: string,
  deleteExtra: boolean,
): Promise<SyncSummary> {
  if (!(await pathExists(sourcePath))) {
    return { added: 0, updated: 0, deleted: 0 };
  }

  if (deleteExtra) {
    await rm(destinationPath, { recursive: true, force: true });
  }

  await mkdir(destinationPath, { recursive: true });
  await cp(sourcePath, destinationPath, { recursive: true, force: true });

  return { added: 0, updated: 0, deleted: 0 };
}

export class SyncEngine {
  constructor(
    private readonly configPath: string = paths.syncConfig,
    private readonly repoDir: string = paths.syncRepo,
  ) {}

  async loadConfig(): Promise<SyncConfig | null> {
    try {
      const content = await readFile(this.configPath, "utf8");
      const parsed = YAML.parse(content) as SyncConfig | null;
      if (!parsed || typeof parsed !== "object") {
        return null;
      }
      return parsed;
    } catch {
      return null;
    }
  }

  async saveConfig(config: SyncConfig): Promise<void> {
    await mkdir(join(this.configPath, ".."), { recursive: true });
    await writeFile(this.configPath, YAML.stringify(config), "utf8");
  }

  async init(remote: string): Promise<SyncConfig> {
    await mkdir(this.repoDir, { recursive: true });

    const config: SyncConfig = {
      version: "1",
      remote,
      lastSync: null,
      directories: defaultDirectories(),
    };

    for (const directory of config.directories) {
      await mkdir(join(this.repoDir, directory.repoSubdir), {
        recursive: true,
      });
    }

    await this.saveConfig(config);
    return config;
  }

  async status(): Promise<SyncStatus> {
    const config = await this.loadConfig();
    return {
      initialized: config !== null,
      config,
      repoDir: this.repoDir,
    };
  }

  async addDirectory(
    pathValue: string,
    options: { profile?: "claude" | "custom"; ignore?: string[] } = {},
  ): Promise<SyncConfig> {
    const config = await this.loadConfig();
    if (!config) {
      throw new Error("sync not initialized");
    }

    const normalizedPath = pathValue.startsWith("~")
      ? pathValue
      : expandHome(pathValue);
    const existingSubdirs = new Set(
      config.directories.map((item) => item.repoSubdir),
    );
    const repoSubdir = makeRepoSubdir(normalizedPath, existingSubdirs);

    config.directories.push({
      path: normalizedPath,
      repoSubdir,
      ignoreProfile: options.profile ?? "custom",
      customIgnore: options.ignore ?? [],
    });

    await mkdir(join(this.repoDir, repoSubdir), { recursive: true });
    await this.saveConfig(config);
    return config;
  }

  async removeDirectory(pathValue: string): Promise<SyncConfig> {
    const config = await this.loadConfig();
    if (!config) {
      throw new Error("sync not initialized");
    }

    config.directories = config.directories.filter(
      (item) => item.path !== pathValue,
    );
    await this.saveConfig(config);
    return config;
  }

  async push(): Promise<SyncSummary> {
    const config = await this.loadConfig();
    if (!config) {
      throw new Error("sync not initialized");
    }

    const total: SyncSummary = { added: 0, updated: 0, deleted: 0 };
    for (const directory of config.directories) {
      const sourcePath = expandHome(directory.path);
      const destinationPath = join(this.repoDir, directory.repoSubdir);
      const summary = await syncDirectory(sourcePath, destinationPath, true);
      total.added += summary.added;
      total.updated += summary.updated;
      total.deleted += summary.deleted;
    }

    config.lastSync = new Date().toISOString();
    await this.saveConfig(config);
    return total;
  }

  async pull(options: { deleteExtra?: boolean } = {}): Promise<SyncSummary> {
    const config = await this.loadConfig();
    if (!config) {
      throw new Error("sync not initialized");
    }

    const deleteExtra = options.deleteExtra ?? true;
    const total: SyncSummary = { added: 0, updated: 0, deleted: 0 };
    for (const directory of config.directories) {
      const sourcePath = join(this.repoDir, directory.repoSubdir);
      const destinationPath = expandHome(directory.path);
      const summary = await syncDirectory(
        sourcePath,
        destinationPath,
        deleteExtra,
      );
      total.added += summary.added;
      total.updated += summary.updated;
      total.deleted += summary.deleted;
    }

    config.lastSync = new Date().toISOString();
    await this.saveConfig(config);
    return total;
  }
}

export function createDefaultSyncEngine(): SyncEngine {
  return new SyncEngine(paths.syncConfig, paths.syncRepo);
}
