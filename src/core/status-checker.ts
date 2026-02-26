import { access, readFile } from "node:fs/promises";
import { homedir } from "node:os";
import { join } from "node:path";

import YAML from "yaml";

import { paths } from "../utils/paths";
import { NPM_PACKAGES, REPOS } from "../utils/shared";
import {
  commandExists,
  getBunVersion,
  getOS,
  type RunCommandOptions,
  runCommand,
} from "../utils/system";

export interface ToolStatus {
  installed: boolean;
  version: string | null;
  path: string | null;
}

export interface NpmPackageStatus {
  name: string;
  installed: boolean;
  version: string | null;
}

export interface RepoStatus {
  name: string;
  path: string;
  exists: boolean;
  isGitRepo: boolean;
  branch: string | null;
  ahead: number;
  behind: number;
  syncState:
    | "missing"
    | "not-git"
    | "up-to-date"
    | "updates-available"
    | "local-ahead"
    | "diverged"
    | "unknown";
}

export interface UpstreamSyncStatus {
  name: string;
  path: string;
  format: string | null;
  syncedAt: string | null;
  status: "synced" | "behind" | "uninstalled" | "unknown";
  behind: number;
}

export interface EnvironmentStatus {
  git: ToolStatus;
  node: ToolStatus;
  bun: ToolStatus;
  gh: ToolStatus;
  npmPackages: NpmPackageStatus[];
  repos: RepoStatus[];
  upstreamSync: UpstreamSyncStatus[];
}

interface UpstreamSourceEntry {
  repo?: string;
  branch?: string;
  local_path?: string;
  format?: string;
}

interface LastSyncEntry {
  commit?: string;
  synced_at?: string;
}

export interface StatusCheckerDependencies {
  commandExistsFn?: typeof commandExists;
  runCommandFn?: (
    command: string[],
    options?: RunCommandOptions,
  ) => Promise<{ stdout: string; stderr: string; exitCode: number }>;
  accessFn?: typeof access;
  resolveCommandPathFn?: (command: string) => Promise<string | null>;
  resolveVersionFn?: (
    command: string,
    args?: string[],
  ) => Promise<string | null>;
  npmPackages?: readonly string[];
  repos?: readonly (typeof REPOS)[number][];
  upstreamSourcesPath?: string;
  upstreamLastSyncPath?: string;
}

export interface CheckEnvironmentOptions {
  deps?: StatusCheckerDependencies;
}

function normalizePackageName(packageName: string): string {
  if (packageName.startsWith("@")) {
    const slashIndex = packageName.indexOf("/");
    const atIndex = packageName.indexOf("@", slashIndex + 1);
    return atIndex === -1 ? packageName : packageName.slice(0, atIndex);
  }
  const atIndex = packageName.indexOf("@");
  return atIndex === -1 ? packageName : packageName.slice(0, atIndex);
}

async function resolveCommandPath(command: string): Promise<string | null> {
  const checker = getOS() === "windows" ? "where" : "which";
  const result = await runCommand([checker, command], { check: false });
  if (result.exitCode !== 0) {
    return null;
  }
  const firstLine = result.stdout
    .split(/\r?\n/)
    .find((line) => line.trim().length > 0);
  return firstLine?.trim() ?? null;
}

async function resolveVersion(
  command: string,
  args: string[] = ["--version"],
  runCommandFn: StatusCheckerDependencies["runCommandFn"] = runCommand,
): Promise<string | null> {
  const result = await runCommandFn([command, ...args], {
    check: false,
    timeoutMs: 5000,
  });
  if (result.exitCode !== 0) {
    return null;
  }
  const line = result.stdout.split(/\r?\n/)[0];
  return line?.trim() || null;
}

async function checkTool(
  command: string,
  deps: {
    commandExistsFn: typeof commandExists;
    resolveCommandPathFn: (command: string) => Promise<string | null>;
    resolveVersionFn: (
      command: string,
      args?: string[],
    ) => Promise<string | null>;
  },
): Promise<ToolStatus> {
  if (!deps.commandExistsFn(command)) {
    return { installed: false, version: null, path: null };
  }

  const version =
    command === "bun"
      ? await getBunVersion()
      : await deps.resolveVersionFn(command);

  return {
    installed: true,
    version,
    path: await deps.resolveCommandPathFn(command),
  };
}

async function checkNpmPackage(
  packageName: string,
  runCommandFn: NonNullable<StatusCheckerDependencies["runCommandFn"]>,
): Promise<NpmPackageStatus> {
  const normalized = normalizePackageName(packageName);
  const result = await runCommandFn(
    ["npm", "list", "-g", normalized, "--depth=0", "--json"],
    {
      check: false,
      timeoutMs: 15000,
    },
  );

  if (result.exitCode !== 0) {
    return { name: packageName, installed: false, version: null };
  }

  try {
    const parsed = JSON.parse(result.stdout) as {
      dependencies?: Record<string, { version?: string }>;
    };
    const dependency = parsed.dependencies?.[normalized];
    return {
      name: packageName,
      installed: Boolean(dependency),
      version: dependency?.version ?? null,
    };
  } catch {
    return { name: packageName, installed: false, version: null };
  }
}

async function compareRemote(
  repoPath: string,
  branch: string,
  runCommandFn: NonNullable<StatusCheckerDependencies["runCommandFn"]>,
): Promise<{ ahead: number; behind: number; ok: boolean }> {
  const compareWithUpstream = await runCommandFn(
    [
      "git",
      "-C",
      repoPath,
      "rev-list",
      "--left-right",
      "--count",
      "HEAD...@{upstream}",
    ],
    {
      check: false,
      timeoutMs: 60_000,
    },
  );

  let compareResult = compareWithUpstream;
  if (compareWithUpstream.exitCode !== 0) {
    compareResult = await runCommandFn(
      [
        "git",
        "-C",
        repoPath,
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
  }

  if (compareResult.exitCode !== 0) {
    return { ahead: 0, behind: 0, ok: false };
  }

  const [aheadRaw, behindRaw] = compareResult.stdout.trim().split(/\s+/);
  const ahead = Number.parseInt(aheadRaw ?? "0", 10);
  const behind = Number.parseInt(behindRaw ?? "0", 10);

  return {
    ahead: Number.isFinite(ahead) ? ahead : 0,
    behind: Number.isFinite(behind) ? behind : 0,
    ok: true,
  };
}

async function checkRepoStatus(
  repoName: string,
  repoPath: string,
  deps: {
    accessFn: typeof access;
    runCommandFn: NonNullable<StatusCheckerDependencies["runCommandFn"]>;
  },
): Promise<RepoStatus> {
  let exists = false;
  let isGitRepo = false;
  let branch: string | null = null;
  let ahead = 0;
  let behind = 0;
  let syncState: RepoStatus["syncState"] = "missing";

  try {
    await deps.accessFn(repoPath);
    exists = true;
    await deps.accessFn(join(repoPath, ".git"));
    isGitRepo = true;
  } catch {
    if (!exists) {
      syncState = "missing";
    } else {
      syncState = "not-git";
    }
  }

  if (exists && isGitRepo) {
    const branchResult = await deps.runCommandFn(
      ["git", "-C", repoPath, "rev-parse", "--abbrev-ref", "HEAD"],
      {
        check: false,
        timeoutMs: 30_000,
      },
    );

    if (branchResult.exitCode === 0) {
      branch = branchResult.stdout.trim() || null;
    }

    if (branch) {
      const diff = await compareRemote(repoPath, branch, deps.runCommandFn);
      ahead = diff.ahead;
      behind = diff.behind;

      if (!diff.ok) {
        syncState = "unknown";
      } else if (ahead > 0 && behind > 0) {
        syncState = "diverged";
      } else if (behind > 0) {
        syncState = "updates-available";
      } else if (ahead > 0) {
        syncState = "local-ahead";
      } else {
        syncState = "up-to-date";
      }
    } else {
      syncState = "unknown";
    }
  }

  return {
    name: repoName,
    path: repoPath,
    exists,
    isGitRepo,
    branch,
    ahead,
    behind,
    syncState,
  };
}

async function pathExists(
  accessFn: typeof access,
  pathValue: string,
): Promise<boolean> {
  try {
    await accessFn(pathValue);
    return true;
  } catch {
    return false;
  }
}

function normalizeHomePath(pathValue: string): string {
  if (pathValue.startsWith("~/")) {
    return join(homedir(), pathValue.slice(2));
  }
  return pathValue;
}

async function loadUpstreamSources(
  sourcesPath: string,
): Promise<Record<string, UpstreamSourceEntry>> {
  try {
    const content = await readFile(sourcesPath, "utf8");
    const parsed =
      (YAML.parse(content) as {
        sources?: Record<string, UpstreamSourceEntry>;
      } | null) ?? {};
    return parsed.sources ?? {};
  } catch {
    return {};
  }
}

async function loadLastSync(
  lastSyncPath: string,
): Promise<Record<string, LastSyncEntry>> {
  try {
    const content = await readFile(lastSyncPath, "utf8");
    return (YAML.parse(content) as Record<string, LastSyncEntry> | null) ?? {};
  } catch {
    return {};
  }
}

async function collectUpstreamSyncStatus(deps: {
  accessFn: typeof access;
  runCommandFn: NonNullable<StatusCheckerDependencies["runCommandFn"]>;
  sourcesPath: string;
  lastSyncPath: string;
}): Promise<UpstreamSyncStatus[]> {
  const sources = await loadUpstreamSources(deps.sourcesPath);
  const lastSync = await loadLastSync(deps.lastSyncPath);

  const result: UpstreamSyncStatus[] = [];

  for (const [name, source] of Object.entries(sources)) {
    const localPath = normalizeHomePath(source.local_path ?? "");
    const record = lastSync[name];

    if (
      !localPath ||
      !(await pathExists(deps.accessFn, join(localPath, ".git")))
    ) {
      result.push({
        name,
        path: localPath,
        format: source.format ?? null,
        syncedAt: record?.synced_at ?? null,
        status: "uninstalled",
        behind: 0,
      });
      continue;
    }

    const commit = record?.commit;
    if (!commit) {
      result.push({
        name,
        path: localPath,
        format: source.format ?? null,
        syncedAt: record?.synced_at ?? null,
        status: "unknown",
        behind: 0,
      });
      continue;
    }

    const containsResult = await deps.runCommandFn(
      ["git", "-C", localPath, "branch", "--contains", commit],
      {
        check: false,
        timeoutMs: 30_000,
      },
    );

    if (containsResult.exitCode !== 0) {
      result.push({
        name,
        path: localPath,
        format: source.format ?? null,
        syncedAt: record?.synced_at ?? null,
        status: "unknown",
        behind: 0,
      });
      continue;
    }

    const behindResult = await deps.runCommandFn(
      ["git", "-C", localPath, "rev-list", "--count", `${commit}..HEAD`],
      {
        check: false,
        timeoutMs: 30_000,
      },
    );

    if (behindResult.exitCode !== 0) {
      result.push({
        name,
        path: localPath,
        format: source.format ?? null,
        syncedAt: record?.synced_at ?? null,
        status: "unknown",
        behind: 0,
      });
      continue;
    }

    const behind = Number.parseInt(behindResult.stdout.trim() || "0", 10);
    result.push({
      name,
      path: localPath,
      format: source.format ?? null,
      syncedAt: record?.synced_at ?? null,
      status: behind > 0 ? "behind" : "synced",
      behind: Number.isFinite(behind) ? behind : 0,
    });
  }

  return result.sort((a, b) => a.name.localeCompare(b.name));
}

export async function checkEnvironment(
  options: CheckEnvironmentOptions = {},
): Promise<EnvironmentStatus> {
  const deps = options.deps ?? {};
  const commandExistsFn = deps.commandExistsFn ?? commandExists;
  const runCommandFn = deps.runCommandFn ?? runCommand;
  const accessFn = deps.accessFn ?? access;
  const resolvePathFn = deps.resolveCommandPathFn ?? resolveCommandPath;
  const resolveVersionFn =
    deps.resolveVersionFn ??
    (async (command: string, args?: string[]) => {
      return await resolveVersion(command, args, runCommandFn);
    });
  const npmPackagesInput = deps.npmPackages ?? NPM_PACKAGES;
  const reposInput = deps.repos ?? REPOS;
  const upstreamSourcesPath =
    deps.upstreamSourcesPath ??
    join(paths.projectRoot, "upstream", "sources.yaml");
  const upstreamLastSyncPath =
    deps.upstreamLastSyncPath ??
    join(paths.projectRoot, "upstream", "last-sync.yaml");

  const [git, node, bun, gh] = await Promise.all([
    checkTool("git", {
      commandExistsFn,
      resolveCommandPathFn: resolvePathFn,
      resolveVersionFn,
    }),
    checkTool("node", {
      commandExistsFn,
      resolveCommandPathFn: resolvePathFn,
      resolveVersionFn,
    }),
    checkTool("bun", {
      commandExistsFn,
      resolveCommandPathFn: resolvePathFn,
      resolveVersionFn,
    }),
    checkTool("gh", {
      commandExistsFn,
      resolveCommandPathFn: resolvePathFn,
      resolveVersionFn,
    }),
  ]);

  const npmPackages = await Promise.all(
    npmPackagesInput.map(
      async (pkg) => await checkNpmPackage(pkg, runCommandFn),
    ),
  );

  const repos = await Promise.all(
    reposInput.map(
      async (repo) =>
        await checkRepoStatus(repo.name, repo.dir, {
          accessFn,
          runCommandFn,
        }),
    ),
  );

  const upstreamSync = await collectUpstreamSyncStatus({
    accessFn,
    runCommandFn,
    sourcesPath: upstreamSourcesPath,
    lastSyncPath: upstreamLastSyncPath,
  });

  return {
    git,
    node,
    bun,
    gh,
    npmPackages,
    repos,
    upstreamSync,
  };
}
