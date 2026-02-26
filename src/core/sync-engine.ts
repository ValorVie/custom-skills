import { cp, mkdir, readFile, rm, stat, writeFile } from "node:fs/promises";
import { basename, dirname, join } from "node:path";

import inquirer from "inquirer";
import YAML from "yaml";

import { computeDirHash } from "../utils/manifest";
import { paths } from "../utils/paths";
import { runCommand } from "../utils/system";

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
  localChanges: number;
  remoteBehind: number;
}

export interface SyncEngineDeps {
  runCommandFn?: typeof runCommand;
  pullConflictChoiceFn?: () => Promise<"overwrite" | "backup" | "cancel">;
}

export function defaultDirectories(): SyncDirectory[] {
  return [
    {
      path: "~/.claude",
      repoSubdir: "claude",
      ignoreProfile: "claude",
      customIgnore: [],
    },
  ];
}

export function expandHome(pathValue: string): string {
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
    await stat(pathValue);
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

  let deleted = 0;
  if (deleteExtra) {
    const existed = await pathExists(destinationPath);
    await rm(destinationPath, { recursive: true, force: true });
    if (existed) {
      deleted += 1;
    }
  }

  await mkdir(destinationPath, { recursive: true });
  await cp(sourcePath, destinationPath, { recursive: true, force: true });

  return { added: 1, updated: 1, deleted };
}

async function ensureFileContains(
  pathValue: string,
  lines: string[],
): Promise<void> {
  let content = "";
  try {
    content = await readFile(pathValue, "utf8");
  } catch {
    content = "";
  }

  const existing = new Set(
    content.split(/\r?\n/).filter((line) => line.length > 0),
  );
  const merged = [...existing];

  for (const line of lines) {
    if (!existing.has(line)) {
      merged.push(line);
    }
  }

  await mkdir(dirname(pathValue), { recursive: true });
  await writeFile(pathValue, `${merged.join("\n")}\n`, "utf8");
}

async function defaultPullConflictChoice(): Promise<
  "overwrite" | "backup" | "cancel"
> {
  const answer = await inquirer.prompt<{
    choice: "overwrite" | "backup" | "cancel";
  }>([
    {
      type: "list",
      name: "choice",
      message: "Local changes detected. Choose how to continue:",
      choices: [
        { name: "Overwrite local changes", value: "overwrite" },
        { name: "Backup then overwrite", value: "backup" },
        { name: "Cancel", value: "cancel" },
      ],
    },
  ]);

  return answer.choice;
}

export class SyncEngine {
  private readonly runCommandFn: typeof runCommand;

  private readonly pullConflictChoiceFn: () => Promise<
    "overwrite" | "backup" | "cancel"
  >;

  constructor(
    private readonly configPath: string = paths.syncConfig,
    private readonly repoDir: string = paths.syncRepo,
    deps: SyncEngineDeps = {},
  ) {
    this.runCommandFn = deps.runCommandFn ?? runCommand;
    this.pullConflictChoiceFn =
      deps.pullConflictChoiceFn ?? defaultPullConflictChoice;
  }

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
    await mkdir(dirname(this.configPath), { recursive: true });
    await writeFile(this.configPath, YAML.stringify(config), "utf8");
  }

  async init(remote = ""): Promise<SyncConfig> {
    await mkdir(dirname(this.repoDir), { recursive: true });

    if (remote) {
      const cloneResult = await this.runCommandFn(
        ["git", "clone", remote, this.repoDir],
        {
          check: false,
          timeoutMs: 120_000,
        },
      );
      if (cloneResult.exitCode !== 0 && !(await pathExists(this.repoDir))) {
        await mkdir(this.repoDir, { recursive: true });
      }
    } else {
      await mkdir(this.repoDir, { recursive: true });
      await this.runCommandFn(["git", "-C", this.repoDir, "init"], {
        check: false,
        timeoutMs: 60_000,
      });
    }

    await this.runCommandFn(["git", "-C", this.repoDir, "lfs", "install"], {
      check: false,
      timeoutMs: 60_000,
    });

    await ensureFileContains(join(this.repoDir, ".gitignore"), [
      ".DS_Store",
      "node_modules/",
      "*.log",
    ]);

    await ensureFileContains(join(this.repoDir, ".gitattributes"), [
      "*.sqlite3 filter=lfs diff=lfs merge=lfs -text",
      "*.db filter=lfs diff=lfs merge=lfs -text",
    ]);

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

  private async compareDirectoryPair(
    sourcePath: string,
    destinationPath: string,
  ): Promise<boolean> {
    if (
      !(await pathExists(sourcePath)) ||
      !(await pathExists(destinationPath))
    ) {
      return false;
    }

    try {
      const [sourceHash, destinationHash] = await Promise.all([
        computeDirHash(sourcePath),
        computeDirHash(destinationPath),
      ]);
      return sourceHash !== destinationHash;
    } catch {
      return false;
    }
  }

  private async hasPullConflicts(config: SyncConfig): Promise<boolean> {
    for (const directory of config.directories) {
      const sourcePath = join(this.repoDir, directory.repoSubdir);
      const destinationPath = expandHome(directory.path);
      if (await this.compareDirectoryPair(sourcePath, destinationPath)) {
        return true;
      }
    }
    return false;
  }

  private async backupDestinations(config: SyncConfig): Promise<void> {
    const backupRoot = join(
      paths.aiDevConfig,
      "sync-backups",
      new Date().toISOString().replace(/[:.]/g, "-"),
    );

    for (const directory of config.directories) {
      const destinationPath = expandHome(directory.path);
      if (!(await pathExists(destinationPath))) {
        continue;
      }

      const backupPath = join(backupRoot, directory.repoSubdir);
      await mkdir(dirname(backupPath), { recursive: true });
      await cp(destinationPath, backupPath, { recursive: true, force: true });
    }
  }

  async status(): Promise<SyncStatus> {
    const config = await this.loadConfig();
    if (!config) {
      return {
        initialized: false,
        config: null,
        repoDir: this.repoDir,
        localChanges: 0,
        remoteBehind: 0,
      };
    }

    const localStatus = await this.runCommandFn(
      ["git", "-C", this.repoDir, "status", "--porcelain"],
      {
        check: false,
        timeoutMs: 60_000,
      },
    );

    const branch = await resolveCurrentBranch(this.repoDir, this.runCommandFn);
    const remoteDiff = await this.runCommandFn(
      [
        "git",
        "-C",
        this.repoDir,
        "rev-list",
        "--left-right",
        "--count",
        `HEAD...origin/${branch}`,
      ],
      {
        check: false,
        timeoutMs: 60_000,
      },
    );

    let remoteBehind = 0;
    if (remoteDiff.exitCode === 0) {
      const [, behindRaw] = remoteDiff.stdout.trim().split(/\s+/);
      remoteBehind = Number.parseInt(behindRaw ?? "0", 10) || 0;
    }

    return {
      initialized: true,
      config,
      repoDir: this.repoDir,
      localChanges: localStatus.stdout
        .split(/\r?\n/)
        .filter((line) => line.trim().length > 0).length,
      remoteBehind,
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

  private async writePluginManifest(config: SyncConfig): Promise<void> {
    const manifest = {
      generatedAt: new Date().toISOString(),
      directories: config.directories.map((directory) => ({
        path: directory.path,
        repoSubdir: directory.repoSubdir,
      })),
    };

    await writeFile(
      join(this.repoDir, "plugin-manifest.json"),
      JSON.stringify(manifest, null, 2),
      "utf8",
    );
  }

  async push(options: { force?: boolean } = {}): Promise<SyncSummary> {
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

    await this.writePluginManifest(config);

    await this.runCommandFn(["git", "-C", this.repoDir, "add", "-A"], {
      check: false,
      timeoutMs: 60_000,
    });
    await this.runCommandFn(
      [
        "git",
        "-C",
        this.repoDir,
        "commit",
        "-m",
        `sync update ${new Date().toISOString()}`,
      ],
      {
        check: false,
        timeoutMs: 60_000,
      },
    );
    await this.runCommandFn(
      [
        "git",
        "-C",
        this.repoDir,
        "push",
        ...(options.force ? ["--force"] : []),
      ],
      {
        check: false,
        timeoutMs: 60_000,
      },
    );
    await this.runCommandFn(
      ["git", "-C", this.repoDir, "lfs", "push", "--all", "origin"],
      {
        check: false,
        timeoutMs: 60_000,
      },
    );

    config.lastSync = new Date().toISOString();
    await this.saveConfig(config);
    return total;
  }

  async pull(
    options: {
      deleteExtra?: boolean;
      noDelete?: boolean;
      force?: boolean;
    } = {},
  ): Promise<SyncSummary> {
    const config = await this.loadConfig();
    if (!config) {
      throw new Error("sync not initialized");
    }

    await this.runCommandFn(["git", "-C", this.repoDir, "pull", "--ff-only"], {
      check: false,
      timeoutMs: 60_000,
    });

    if (!options.force && (await this.hasPullConflicts(config))) {
      const choice = await this.pullConflictChoiceFn();
      if (choice === "cancel") {
        throw new Error("sync pull cancelled by user");
      }
      if (choice === "backup") {
        await this.backupDestinations(config);
      }
    }

    const deleteExtra = options.noDelete
      ? false
      : (options.deleteExtra ?? true);
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

async function resolveCurrentBranch(
  repoDir: string,
  runCommandFn: typeof runCommand,
): Promise<string> {
  const result = await runCommandFn(
    ["git", "-C", repoDir, "rev-parse", "--abbrev-ref", "HEAD"],
    {
      check: false,
      timeoutMs: 60_000,
    },
  );

  if (result.exitCode !== 0) {
    return "main";
  }

  return result.stdout.trim() || "main";
}

export function createDefaultSyncEngine(): SyncEngine {
  return new SyncEngine(paths.syncConfig, paths.syncRepo);
}
