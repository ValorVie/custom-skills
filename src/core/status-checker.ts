import { access } from "node:fs/promises";
import { join } from "node:path";

import { NPM_PACKAGES, REPOS } from "../utils/shared";
import {
  commandExists,
  getBunVersion,
  getOS,
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
}

export interface EnvironmentStatus {
  git: ToolStatus;
  node: ToolStatus;
  bun: ToolStatus;
  gh: ToolStatus;
  npmPackages: NpmPackageStatus[];
  repos: RepoStatus[];
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
): Promise<string | null> {
  const result = await runCommand([command, ...args], {
    check: false,
    timeoutMs: 5000,
  });
  if (result.exitCode !== 0) {
    return null;
  }
  const line = result.stdout.split(/\r?\n/)[0];
  return line?.trim() || null;
}

async function checkTool(command: string): Promise<ToolStatus> {
  if (!commandExists(command)) {
    return { installed: false, version: null, path: null };
  }

  const version =
    command === "bun" ? await getBunVersion() : await resolveVersion(command);

  return {
    installed: true,
    version,
    path: await resolveCommandPath(command),
  };
}

async function checkNpmPackage(packageName: string): Promise<NpmPackageStatus> {
  const normalized = normalizePackageName(packageName);
  const result = await runCommand(
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

async function checkRepoStatus(
  repoName: string,
  repoPath: string,
): Promise<RepoStatus> {
  let exists = false;
  let isGitRepo = false;

  try {
    await access(repoPath);
    exists = true;
    await access(join(repoPath, ".git"));
    isGitRepo = true;
  } catch {
    isGitRepo = false;
  }

  return {
    name: repoName,
    path: repoPath,
    exists,
    isGitRepo,
  };
}

export async function checkEnvironment(): Promise<EnvironmentStatus> {
  const [git, node, bun, gh] = await Promise.all([
    checkTool("git"),
    checkTool("node"),
    checkTool("bun"),
    checkTool("gh"),
  ]);

  const npmPackages = await Promise.all(
    NPM_PACKAGES.map(async (pkg) => await checkNpmPackage(pkg)),
  );

  const repos = await Promise.all(
    REPOS.map(async (repo) => await checkRepoStatus(repo.name, repo.dir)),
  );

  return {
    git,
    node,
    bun,
    gh,
    npmPackages,
    repos,
  };
}
