import {
  cp,
  mkdir,
  readFile,
  readdir,
  rm,
  stat,
  writeFile,
} from "node:fs/promises";
import { basename, dirname, join, relative } from "node:path";

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
  skipped?: boolean;
  git?: SyncGitDetails;
}

export interface SyncGitCommandDetail {
  command: string[];
  exitCode: number;
  stdout: string;
  stderr: string;
}

export interface SyncGitDetails {
  status?: SyncGitCommandDetail;
  add?: SyncGitCommandDetail;
  commit?: SyncGitCommandDetail;
  pull?: SyncGitCommandDetail;
  push?: SyncGitCommandDetail;
  lfsPush?: SyncGitCommandDetail;
}

export interface SyncStatus {
  initialized: boolean;
  config: SyncConfig | null;
  repoDir: string;
  localChanges: number;
  remoteBehind: number;
}

export type PullConflictChoice = "push_then_pull" | "force_pull" | "cancel";

export interface SyncEngineDeps {
  runCommandFn?: typeof runCommand;
  pullConflictChoiceFn?: () => Promise<PullConflictChoice>;
  confirmForcePushFn?: () => Promise<boolean>;
  confirmReinitFn?: () => Promise<boolean>;
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

function readStringField(
  source: Record<string, unknown>,
  camelKey: string,
  snakeKey: string,
  fallback = "",
): string {
  const camelValue = source[camelKey];
  if (typeof camelValue === "string") {
    return camelValue;
  }

  const snakeValue = source[snakeKey];
  if (typeof snakeValue === "string") {
    return snakeValue;
  }

  return fallback;
}

function readStringArrayField(
  source: Record<string, unknown>,
  camelKey: string,
  snakeKey: string,
): string[] {
  const value = source[camelKey] ?? source[snakeKey];
  if (!Array.isArray(value)) {
    return [];
  }
  return value.filter((item): item is string => typeof item === "string");
}

function readNullableStringField(
  source: Record<string, unknown>,
  camelKey: string,
  snakeKey: string,
): string | null {
  const camelValue = source[camelKey];
  if (typeof camelValue === "string" || camelValue === null) {
    return camelValue;
  }

  const snakeValue = source[snakeKey];
  if (typeof snakeValue === "string" || snakeValue === null) {
    return snakeValue;
  }

  return null;
}

function normalizeIgnoreProfile(value: string): "claude" | "custom" {
  return value === "claude" ? "claude" : "custom";
}

function normalizeLegacySyncConfig(raw: unknown): SyncConfig | null {
  if (!raw || typeof raw !== "object") {
    return null;
  }

  const source = raw as Record<string, unknown>;
  const rawDirectories = Array.isArray(source.directories)
    ? source.directories
    : [];

  const directories = rawDirectories
    .map((entry): SyncDirectory | null => {
      if (!entry || typeof entry !== "object") {
        return null;
      }

      const directory = entry as Record<string, unknown>;
      const path = readStringField(directory, "path", "path");
      const repoSubdir = readStringField(
        directory,
        "repoSubdir",
        "repo_subdir",
      );
      if (!path || !repoSubdir) {
        return null;
      }

      const ignoreProfile = normalizeIgnoreProfile(
        readStringField(directory, "ignoreProfile", "ignore_profile", "custom"),
      );

      return {
        path,
        repoSubdir,
        ignoreProfile,
        customIgnore: readStringArrayField(
          directory,
          "customIgnore",
          "custom_ignore",
        ),
      };
    })
    .filter((item): item is SyncDirectory => item !== null);

  return {
    version: readStringField(source, "version", "version", "1"),
    remote: readStringField(source, "remote", "remote"),
    lastSync: readNullableStringField(source, "lastSync", "last_sync"),
    directories,
  };
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

async function directoryHasContents(pathValue: string): Promise<boolean> {
  try {
    const entries = await readdir(pathValue);
    return entries.length > 0;
  } catch {
    return false;
  }
}

const GLOBAL_IGNORE_PATTERNS = [".DS_Store", "Thumbs.db", "desktop.ini"];
const CLAUDE_IGNORE_PATTERNS = [
  "debug/",
  "cache/",
  "paste-cache/",
  "downloads/",
  "shell-snapshots/",
  "session-env/",
  "ide/",
  "statsig/",
  "telemetry/",
  "stats-cache.json",
  "plugins/cache/",
  "plugins/marketplaces/",
  "plugins/repos/",
  "plugins/install-counts-cache.json",
  "plugins/installed_plugins.json",
  "plugins/known_marketplaces.json",
  ".credentials.json",
];

function normalizePathForMatch(value: string): string {
  return value
    .replace(/\\/g, "/")
    .replace(/^\.\/+/, "")
    .replace(/^\/+/, "")
    .replace(/\/+/g, "/")
    .replace(/\/$/, "");
}

function escapeForRegExp(value: string): string {
  return value.replace(/[.+^${}()|[\]\\]/g, "\\$&");
}

function globToRegExp(glob: string): RegExp {
  let pattern = "";
  for (let index = 0; index < glob.length; index += 1) {
    const char = glob[index];
    if (char === "*") {
      if (glob[index + 1] === "*") {
        pattern += ".*";
        index += 1;
      } else {
        pattern += "[^/]*";
      }
      continue;
    }
    if (char === "?") {
      pattern += "[^/]";
      continue;
    }
    pattern += escapeForRegExp(char);
  }
  return new RegExp(`^${pattern}$`);
}

function matchesIgnorePattern(relativePath: string, rawPattern: string): boolean {
  const pathValue = normalizePathForMatch(relativePath);
  const normalizedPattern = normalizePathForMatch(rawPattern.trim());
  if (!pathValue || !normalizedPattern) {
    return false;
  }

  if (rawPattern.trim().endsWith("/")) {
    const dirPattern = normalizePathForMatch(normalizedPattern);
    if (!dirPattern.includes("/")) {
      return pathValue.split("/").includes(dirPattern);
    }
    return pathValue === dirPattern || pathValue.startsWith(`${dirPattern}/`);
  }

  const hasGlob = /[*?]/.test(normalizedPattern);
  if (!hasGlob) {
    if (!normalizedPattern.includes("/")) {
      return pathValue.split("/").includes(normalizedPattern);
    }
    return pathValue === normalizedPattern;
  }

  const matcher = globToRegExp(normalizedPattern);
  if (!normalizedPattern.includes("/")) {
    return pathValue.split("/").some((segment) => matcher.test(segment));
  }
  return matcher.test(pathValue);
}

function resolveIgnorePatterns(
  profile: SyncDirectory["ignoreProfile"],
  customIgnore: string[],
): string[] {
  const patterns = new Set<string>(GLOBAL_IGNORE_PATTERNS);
  if (profile === "claude") {
    for (const pattern of CLAUDE_IGNORE_PATTERNS) {
      patterns.add(pattern);
    }
  }
  for (const pattern of customIgnore) {
    if (pattern.trim().length > 0) {
      patterns.add(pattern.trim());
    }
  }
  return [...patterns];
}

function shouldIgnorePath(
  sourceRoot: string,
  currentSourcePath: string,
  ignorePatterns: string[],
): boolean {
  if (ignorePatterns.length === 0) {
    return false;
  }

  const relativePath = normalizePathForMatch(
    relative(sourceRoot, currentSourcePath),
  );
  if (!relativePath || relativePath === ".") {
    return false;
  }

  return ignorePatterns.some((pattern) =>
    matchesIgnorePattern(relativePath, pattern),
  );
}

async function syncDirectory(
  sourcePath: string,
  destinationPath: string,
  deleteExtra: boolean,
  ignorePatterns: string[] = [],
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
  await cp(sourcePath, destinationPath, {
    recursive: true,
    force: true,
    filter: (currentSourcePath) =>
      !shouldIgnorePath(sourcePath, currentSourcePath, ignorePatterns),
  });

  return { added: 1, updated: 1, deleted };
}

type PluginManifest = {
  version: number;
  marketplaces: Record<string, unknown>;
  plugins: Array<Record<string, unknown>>;
  enabledPlugins: string[];
};

async function readJsonObject(
  pathValue: string,
): Promise<Record<string, unknown> | null> {
  try {
    const raw = await readFile(pathValue, "utf8");
    const parsed = JSON.parse(raw) as unknown;
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
      return null;
    }
    return parsed as Record<string, unknown>;
  } catch {
    return null;
  }
}

async function generatePluginManifest(
  localClaudePath: string,
): Promise<PluginManifest | null> {
  const installedPath = join(localClaudePath, "plugins", "installed_plugins.json");
  const marketplacesPath = join(
    localClaudePath,
    "plugins",
    "known_marketplaces.json",
  );
  const settingsPath = join(localClaudePath, "settings.json");

  const [installed, marketplaces, settings] = await Promise.all([
    readJsonObject(installedPath),
    readJsonObject(marketplacesPath),
    readJsonObject(settingsPath),
  ]);

  if (!installed && !marketplaces) {
    return null;
  }

  const manifest: PluginManifest = {
    version: 1,
    marketplaces: {},
    plugins: [],
    enabledPlugins: [],
  };

  if (marketplaces) {
    for (const [name, info] of Object.entries(marketplaces)) {
      if (!info || typeof info !== "object" || Array.isArray(info)) {
        continue;
      }
      const source = (info as Record<string, unknown>).source;
      manifest.marketplaces[name] = source ?? {};
    }
  }

  const pluginsField = installed?.plugins;
  if (
    pluginsField &&
    typeof pluginsField === "object" &&
    !Array.isArray(pluginsField)
  ) {
    for (const [pluginName, entries] of Object.entries(pluginsField)) {
      if (!Array.isArray(entries) || entries.length === 0) {
        continue;
      }
      const latest = entries[entries.length - 1];
      if (!latest || typeof latest !== "object" || Array.isArray(latest)) {
        continue;
      }
      const latestRecord = latest as Record<string, unknown>;
      manifest.plugins.push({
        name: pluginName,
        version:
          typeof latestRecord.version === "string" ? latestRecord.version : "",
        scope: typeof latestRecord.scope === "string" ? latestRecord.scope : "user",
      });
    }
  }

  const enabled = settings?.enabledPlugins;
  if (enabled && typeof enabled === "object" && !Array.isArray(enabled)) {
    manifest.enabledPlugins = Object.keys(enabled);
  }

  return manifest;
}

async function restorePluginsFromManifest(
  manifestPath: string,
  localClaudePath: string,
  runCommandFn: typeof runCommand = runCommand,
): Promise<void> {
  const manifest = await readJsonObject(manifestPath);
  if (!manifest) {
    return;
  }

  const knownMarketplaces: Record<
    string,
    { source: Record<string, unknown>; path: string }
  > = {};
  const marketplaces = manifest.marketplaces;
  if (marketplaces && typeof marketplaces === "object" && !Array.isArray(marketplaces)) {
    for (const [name, sourceValue] of Object.entries(marketplaces)) {
      if (!sourceValue || typeof sourceValue !== "object" || Array.isArray(sourceValue)) {
        continue;
      }

      const source = sourceValue as Record<string, unknown>;
      const sourceType = typeof source.source === "string" ? source.source : "";
      let cloneUrl = "";
      if (sourceType === "github") {
        const owner = typeof source.owner === "string" ? source.owner : "";
        const repo = typeof source.repo === "string" ? source.repo : "";
        if (owner && repo) {
          cloneUrl = `https://github.com/${owner}/${repo}.git`;
        }
      } else if (sourceType === "git") {
        cloneUrl = typeof source.url === "string" ? source.url : "";
      }

      const marketplaceDir = join(localClaudePath, "plugins", "marketplaces", name);
      if (cloneUrl && !(await pathExists(marketplaceDir))) {
        await mkdir(dirname(marketplaceDir), { recursive: true });
        const cloneResult = await runCommandFn(
          ["git", "clone", "--depth", "1", cloneUrl, marketplaceDir],
          {
            check: false,
            timeoutMs: 120_000,
          },
        );
        if (cloneResult.exitCode !== 0) {
          continue;
        }
      }

      if (await pathExists(marketplaceDir)) {
        knownMarketplaces[name] = {
          source,
          path: marketplaceDir,
        };
      }
    }
  }

  if (Object.keys(knownMarketplaces).length > 0) {
    const knownMarketplacesPath = join(
      localClaudePath,
      "plugins",
      "known_marketplaces.json",
    );
    await mkdir(dirname(knownMarketplacesPath), { recursive: true });
    await writeFile(
      knownMarketplacesPath,
      `${JSON.stringify(knownMarketplaces, null, 2)}\n`,
      "utf8",
    );
  }

  const pluginsValue = manifest.plugins;
  const plugins = Array.isArray(pluginsValue) ? pluginsValue : [];
  for (const plugin of plugins) {
    if (!plugin || typeof plugin !== "object" || Array.isArray(plugin)) {
      continue;
    }
    const record = plugin as Record<string, unknown>;
    const pluginName = typeof record.name === "string" ? record.name : "";
    if (!pluginName) {
      continue;
    }

    const pluginDir = join(localClaudePath, "plugins", pluginName);
    if (!(await pathExists(pluginDir))) {
      await mkdir(pluginDir, { recursive: true });
    }

    const metadata = {
      name: pluginName,
      version: typeof record.version === "string" ? record.version : "",
      scope: typeof record.scope === "string" ? record.scope : "user",
    };
    await writeFile(
      join(pluginDir, ".claude-plugin"),
      JSON.stringify(metadata, null, 2),
      "utf8",
    );
  }

  const settingsPath = join(localClaudePath, "settings.json");
  const settings = (await readJsonObject(settingsPath)) ?? {};
  const enabledRaw = manifest.enabledPlugins;
  const enabledPlugins = Array.isArray(enabledRaw)
    ? enabledRaw.filter(
        (item): item is string => typeof item === "string" && item.length > 0,
      )
    : [];

  if (enabledPlugins.length > 0) {
    const existingEnabled = settings.enabledPlugins;
    const enabledRecord =
      existingEnabled &&
      typeof existingEnabled === "object" &&
      !Array.isArray(existingEnabled)
        ? ({ ...existingEnabled } as Record<string, unknown>)
        : {};

    for (const pluginName of enabledPlugins) {
      enabledRecord[pluginName] = {};
    }
    settings.enabledPlugins = enabledRecord;
    await mkdir(dirname(settingsPath), { recursive: true });
    await writeFile(settingsPath, `${JSON.stringify(settings, null, 2)}\n`, "utf8");
  }
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

async function defaultPullConflictChoice(): Promise<PullConflictChoice> {
  const answer = await inquirer.prompt<{ choice: PullConflictChoice }>([
    {
      type: "list",
      name: "choice",
      message: "偵測到本地變更，請選擇後續操作：",
      choices: [
        { name: "先 push 再 pull（推薦）", value: "push_then_pull" },
        { name: "強制 pull 並覆蓋本地變更", value: "force_pull" },
        { name: "取消", value: "cancel" },
      ],
    },
  ]);

  return answer.choice;
}

async function defaultForcePushConfirmation(): Promise<boolean> {
  const answer = await inquirer.prompt<{ confirmed: boolean }>([
    {
      type: "confirm",
      name: "confirmed",
      message:
        "Force push may overwrite remote history. Continue with sync push --force?",
      default: false,
    },
  ]);

  return Boolean(answer.confirmed);
}

async function defaultReinitConfirmation(): Promise<boolean> {
  const answer = await inquirer.prompt<{ confirmed: boolean }>([
    {
      type: "confirm",
      name: "confirmed",
      message: "已存在 sync.yaml，是否重新初始化（覆蓋設定）？",
      default: false,
    },
  ]);

  return Boolean(answer.confirmed);
}

export class SyncEngine {
  private readonly runCommandFn: typeof runCommand;

  private readonly pullConflictChoiceFn: () => Promise<PullConflictChoice>;

  private readonly confirmForcePushFn: () => Promise<boolean>;

  private readonly confirmReinitFn: () => Promise<boolean>;

  constructor(
    private readonly configPath: string = paths.syncConfig,
    private readonly repoDir: string = paths.syncRepo,
    deps: SyncEngineDeps = {},
  ) {
    this.runCommandFn = deps.runCommandFn ?? runCommand;
    this.pullConflictChoiceFn =
      deps.pullConflictChoiceFn ?? defaultPullConflictChoice;
    this.confirmForcePushFn =
      deps.confirmForcePushFn ?? defaultForcePushConfirmation;
    this.confirmReinitFn = deps.confirmReinitFn ?? defaultReinitConfirmation;
  }

  async loadConfig(): Promise<SyncConfig | null> {
    try {
      const content = await readFile(this.configPath, "utf8");
      return normalizeLegacySyncConfig(YAML.parse(content));
    } catch {
      return null;
    }
  }

  async saveConfig(config: SyncConfig): Promise<void> {
    await mkdir(dirname(this.configPath), { recursive: true });
    await writeFile(this.configPath, YAML.stringify(config), "utf8");
  }

  async init(remote = ""): Promise<SyncConfig> {
    const existingConfig = await this.loadConfig();
    if (existingConfig) {
      const confirmed = await this.confirmReinitFn();
      if (!confirmed) {
        throw new Error("sync init cancelled by user");
      }
    }

    await mkdir(dirname(this.repoDir), { recursive: true });

    let clonedFromRemote = false;
    if (remote) {
      if (await pathExists(join(this.repoDir, ".git"))) {
        const setRemoteResult = await this.runCommandFn(
          ["git", "-C", this.repoDir, "remote", "set-url", "origin", remote],
          {
            check: false,
            timeoutMs: 60_000,
          },
        );
        if (setRemoteResult.exitCode !== 0) {
          const addRemoteResult = await this.runCommandFn(
            ["git", "-C", this.repoDir, "remote", "add", "origin", remote],
            {
              check: false,
              timeoutMs: 60_000,
            },
          );
          if (addRemoteResult.exitCode !== 0) {
            throw new Error("git remote 設定失敗");
          }
        }

        const fetchResult = await this.runCommandFn(
          ["git", "-C", this.repoDir, "fetch", "origin"],
          {
            check: false,
            timeoutMs: 60_000,
          },
        );
        if (fetchResult.exitCode !== 0) {
          throw new Error("git fetch 失敗");
        }
      } else {
        await rm(this.repoDir, { recursive: true, force: true });
        const cloneResult = await this.runCommandFn(
          ["git", "clone", remote, this.repoDir],
          {
            check: false,
            timeoutMs: 120_000,
          },
        );
        if (cloneResult.exitCode !== 0) {
          throw new Error("git clone 失敗");
        }
        clonedFromRemote = true;
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

    if (remote) {
      for (const directory of config.directories) {
        const repoPath = join(this.repoDir, directory.repoSubdir);
        const localPath = expandHome(directory.path);
        const ignorePatterns = resolveIgnorePatterns(
          directory.ignoreProfile,
          directory.customIgnore,
        );
        const hasRemoteContent = await directoryHasContents(repoPath);

        if (clonedFromRemote && hasRemoteContent) {
          await syncDirectory(repoPath, localPath, false, ignorePatterns);
        }
        if (directory.ignoreProfile === "claude" && hasRemoteContent) {
          await restorePluginsFromManifest(
            join(repoPath, "plugins", "plugin-manifest.json"),
            localPath,
            this.runCommandFn,
          );
        }

        await syncDirectory(localPath, repoPath, true, ignorePatterns);
      }

      await this.writePluginManifest(config);

      await this.runCommandFn(["git", "-C", this.repoDir, "add", "-A"], {
        check: false,
        timeoutMs: 60_000,
      });
      const commit = await this.runCommandFn(
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
      const commitOutput = `${commit.stdout}\n${commit.stderr}`.toLowerCase();
      const noChanges =
        commit.exitCode !== 0 &&
        (commitOutput.includes("nothing to commit") ||
          commitOutput.includes("no changes added to commit"));
      if (commit.exitCode !== 0 && !noChanges) {
        throw new Error("git commit 失敗");
      }

      const pullResult = await this.runCommandFn(
        ["git", "-C", this.repoDir, "pull", "--rebase"],
        {
          check: false,
          timeoutMs: 60_000,
        },
      );
      if (pullResult.exitCode !== 0) {
        throw new Error("git pull --rebase 失敗");
      }

      const pushResult = await this.runCommandFn(
        ["git", "-C", this.repoDir, "push"],
        {
          check: false,
          timeoutMs: 60_000,
        },
      );
      if (pushResult.exitCode !== 0) {
        throw new Error("git push 失敗");
      }

      config.lastSync = new Date().toISOString();
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
    const resolvedPath = expandHome(normalizedPath);
    try {
      const stats = await stat(resolvedPath);
      if (!stats.isDirectory()) {
        throw new Error("目錄不存在");
      }
    } catch {
      throw new Error("目錄不存在");
    }
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

  async removeDirectory(
    pathValue: string,
    options: { skipMinCheck?: boolean; deleteRepoSubdir?: boolean } = {},
  ): Promise<SyncConfig> {
    const config = await this.loadConfig();
    if (!config) {
      throw new Error("sync not initialized");
    }

    // Minimum 1 directory validation (v1 parity)
    if (!options.skipMinCheck && config.directories.length <= 1) {
      throw new Error("至少保留一個同步目錄");
    }

    const targetIndex = config.directories.findIndex(
      (item) => item.path === pathValue,
    );
    if (targetIndex === -1) {
      throw new Error("該目錄不在同步清單中");
    }

    const removed = config.directories[targetIndex];
    config.directories.splice(targetIndex, 1);

    // Attempt to clean up repo subdirectory
    const shouldDeleteRepoSubdir = options.deleteRepoSubdir ?? true;
    if (shouldDeleteRepoSubdir) {
      const repoSubdirPath = join(this.repoDir, removed.repoSubdir);
      if (await pathExists(repoSubdirPath)) {
        try {
          await rm(repoSubdirPath, { recursive: true, force: true });
        } catch {
          // ignore cleanup failures
        }
      }
    }

    // Update gitignore to reflect current directories
    await ensureFileContains(join(this.repoDir, ".gitignore"), [
      ".DS_Store",
      "*.swp",
    ]);

    await this.saveConfig(config);
    return config;
  }

  private async writePluginManifest(config: SyncConfig): Promise<void> {
    const claudeDirectory = config.directories.find(
      (directory) => directory.ignoreProfile === "claude",
    );
    if (!claudeDirectory) {
      return;
    }

    const localClaudePath = expandHome(claudeDirectory.path);
    const manifest = await generatePluginManifest(localClaudePath);
    if (!manifest) {
      return;
    }

    const manifestPath = join(
      this.repoDir,
      claudeDirectory.repoSubdir,
      "plugins",
      "plugin-manifest.json",
    );
    await mkdir(dirname(manifestPath), { recursive: true });
    await writeFile(manifestPath, JSON.stringify(manifest, null, 2), "utf8");
  }

  async push(options: { force?: boolean } = {}): Promise<SyncSummary> {
    const config = await this.loadConfig();
    if (!config) {
      throw new Error("sync not initialized");
    }

    const gitDetails: SyncGitDetails = {};

    if (options.force) {
      const confirmed = await this.confirmForcePushFn();
      if (!confirmed) {
        return { added: 0, updated: 0, deleted: 0, skipped: true, git: gitDetails };
      }
    }

    const total: SyncSummary = { added: 0, updated: 0, deleted: 0 };
    for (const directory of config.directories) {
      const sourcePath = expandHome(directory.path);
      const destinationPath = join(this.repoDir, directory.repoSubdir);
      const summary = await syncDirectory(
        sourcePath,
        destinationPath,
        true,
        resolveIgnorePatterns(directory.ignoreProfile, directory.customIgnore),
      );
      total.added += summary.added;
      total.updated += summary.updated;
      total.deleted += summary.deleted;
    }

    await this.writePluginManifest(config);

    if (!options.force) {
      const localStatus = await this.runCommandFn(
        ["git", "-C", this.repoDir, "status", "--porcelain"],
        {
          check: false,
          timeoutMs: 60_000,
        },
      );
      gitDetails.status = {
        command: ["git", "-C", this.repoDir, "status", "--porcelain"],
        exitCode: localStatus.exitCode,
        stdout: localStatus.stdout,
        stderr: localStatus.stderr,
      };
      if (localStatus.exitCode === 0 && localStatus.stdout.trim().length === 0) {
        return { added: 0, updated: 0, deleted: 0, git: gitDetails };
      }
    }

    const addResult = await this.runCommandFn(["git", "-C", this.repoDir, "add", "-A"], {
      check: false,
      timeoutMs: 60_000,
    });
    gitDetails.add = {
      command: ["git", "-C", this.repoDir, "add", "-A"],
      exitCode: addResult.exitCode,
      stdout: addResult.stdout,
      stderr: addResult.stderr,
    };
    const commitMessage = `sync update ${new Date().toISOString()}`;
    const commitCommand = [
      "git",
      "-C",
      this.repoDir,
      "commit",
      "-m",
      commitMessage,
    ] as const;
    const commit = await this.runCommandFn([...commitCommand], {
      check: false,
      timeoutMs: 60_000,
    });
    gitDetails.commit = {
      command: [...commitCommand],
      exitCode: commit.exitCode,
      stdout: commit.stdout,
      stderr: commit.stderr,
    };

    const commitOutput = `${commit.stdout}\n${commit.stderr}`.toLowerCase();
    const noChanges =
      commit.exitCode !== 0 &&
      (commitOutput.includes("nothing to commit") ||
        commitOutput.includes("no changes added to commit"));
    if (noChanges) {
      if (!options.force) {
        return { added: 0, updated: 0, deleted: 0, git: gitDetails };
      }
    } else if (commit.exitCode !== 0) {
      throw new Error("git commit 失敗");
    }

    if (!options.force) {
      const prePushPull = await this.runCommandFn(
        ["git", "-C", this.repoDir, "pull", "--rebase"],
        {
          check: false,
          timeoutMs: 60_000,
        },
      );
      gitDetails.pull = {
        command: ["git", "-C", this.repoDir, "pull", "--rebase"],
        exitCode: prePushPull.exitCode,
        stdout: prePushPull.stdout,
        stderr: prePushPull.stderr,
      };
      if (prePushPull.exitCode !== 0) {
        const reason = `${prePushPull.stderr}\n${prePushPull.stdout}`.trim();
        throw new Error(
          reason ? `git pull --rebase 失敗: ${reason}` : "git pull --rebase 失敗",
        );
      }
    }

    const pushResult = await this.runCommandFn(
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
    gitDetails.push = {
      command: [
        "git",
        "-C",
        this.repoDir,
        "push",
        ...(options.force ? ["--force"] : []),
      ],
      exitCode: pushResult.exitCode,
      stdout: pushResult.stdout,
      stderr: pushResult.stderr,
    };
    if (pushResult.exitCode !== 0) {
      throw new Error("git push 失敗");
    }

    const lfsPushResult = await this.runCommandFn(
      ["git", "-C", this.repoDir, "lfs", "push", "--all", "origin"],
      {
        check: false,
        timeoutMs: 60_000,
      },
    );
    gitDetails.lfsPush = {
      command: ["git", "-C", this.repoDir, "lfs", "push", "--all", "origin"],
      exitCode: lfsPushResult.exitCode,
      stdout: lfsPushResult.stdout,
      stderr: lfsPushResult.stderr,
    };
    if (lfsPushResult.exitCode !== 0) {
      throw new Error("git lfs push 失敗");
    }

    config.lastSync = new Date().toISOString();
    await this.saveConfig(config);
    return { ...total, git: gitDetails };
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

    const gitDetails: SyncGitDetails = {};

    if (!options.force && (await this.hasPullConflicts(config))) {
      const choice = await this.pullConflictChoiceFn();
      if (choice === "cancel") {
        throw new Error("sync pull cancelled by user");
      }
      if (choice === "push_then_pull") {
        await this.push({ force: false });
      }
    }

    const pullResult = await this.runCommandFn(
      ["git", "-C", this.repoDir, "pull", "--rebase"],
      {
        check: false,
        timeoutMs: 60_000,
      },
    );
    gitDetails.pull = {
      command: ["git", "-C", this.repoDir, "pull", "--rebase"],
      exitCode: pullResult.exitCode,
      stdout: pullResult.stdout,
      stderr: pullResult.stderr,
    };
    if (pullResult.exitCode !== 0) {
      const reason = `${pullResult.stderr}\n${pullResult.stdout}`.trim();
      throw new Error(
        reason ? `git pull --rebase 失敗: ${reason}` : "git pull --rebase 失敗",
      );
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
        resolveIgnorePatterns(directory.ignoreProfile, directory.customIgnore),
      );
      total.added += summary.added;
      total.updated += summary.updated;
      total.deleted += summary.deleted;
    }

    config.lastSync = new Date().toISOString();
    await this.saveConfig(config);
    return { ...total, git: gitDetails };
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
