import { access, mkdir } from "node:fs/promises";
import { dirname, join } from "node:path";

import { BUN_PACKAGES, NPM_PACKAGES, REPOS } from "../utils/shared";
import { commandExists, getBunVersion, runCommand } from "../utils/system";

type RepoConfig = (typeof REPOS)[number];

export interface InstallDependencies {
  commandExistsFn?: typeof commandExists;
  runCommandFn?: typeof runCommand;
  getBunVersionFn?: typeof getBunVersion;
  npmPackages?: readonly string[];
  bunPackages?: readonly string[];
  repos?: readonly RepoConfig[];
}

export interface InstallOptions {
  skipNpm?: boolean;
  skipBun?: boolean;
  skipRepos?: boolean;
  deps?: InstallDependencies;
}

export interface InstallItemResult {
  name: string;
  success: boolean;
  message?: string;
}

export interface InstallResult {
  prerequisites: {
    node: boolean;
    git: boolean;
    bun: boolean;
  };
  npmPackages: InstallItemResult[];
  bunPackages: InstallItemResult[];
  repos: InstallItemResult[];
  errors: string[];
}

async function installNpmPackage(
  packageName: string,
  runCommandFn: typeof runCommand,
): Promise<InstallItemResult> {
  const result = await runCommandFn(["npm", "install", "-g", packageName], {
    check: false,
  });

  return {
    name: packageName,
    success: result.exitCode === 0,
    message: result.exitCode === 0 ? undefined : result.stderr,
  };
}

async function installBunPackage(
  packageName: string,
  runCommandFn: typeof runCommand,
): Promise<InstallItemResult> {
  const result = await runCommandFn(["bun", "install", "-g", packageName], {
    check: false,
  });

  return {
    name: packageName,
    success: result.exitCode === 0,
    message: result.exitCode === 0 ? undefined : result.stderr,
  };
}

async function ensureRepo(
  repoName: string,
  repoUrl: string,
  repoDir: string,
  runCommandFn: typeof runCommand,
): Promise<InstallItemResult> {
  try {
    await access(join(repoDir, ".git"));
    return {
      name: repoName,
      success: true,
      message: "already cloned",
    };
  } catch {
    // continue cloning
  }

  await mkdir(dirname(repoDir), { recursive: true });
  const result = await runCommandFn(["git", "clone", repoUrl, repoDir], {
    check: false,
  });

  return {
    name: repoName,
    success: result.exitCode === 0,
    message: result.exitCode === 0 ? undefined : result.stderr,
  };
}

export async function runInstall(
  options: InstallOptions = {},
): Promise<InstallResult> {
  const deps = options.deps ?? {};
  const skipNpm = options.skipNpm ?? false;
  const skipBun = options.skipBun ?? false;
  const skipRepos = options.skipRepos ?? false;
  const commandExistsFn = deps.commandExistsFn ?? commandExists;
  const runCommandFn = deps.runCommandFn ?? runCommand;
  const getBunVersionFn = deps.getBunVersionFn ?? getBunVersion;
  const npmPackages = deps.npmPackages ?? NPM_PACKAGES;
  const bunPackages = deps.bunPackages ?? BUN_PACKAGES;
  const repos = deps.repos ?? REPOS;

  const prerequisites = {
    node: commandExistsFn("node"),
    git: commandExistsFn("git"),
    bun: commandExistsFn("bun"),
  };

  const result: InstallResult = {
    prerequisites,
    npmPackages: [],
    bunPackages: [],
    repos: [],
    errors: [],
  };

  if (!prerequisites.node) {
    result.errors.push("Node.js is required");
  }
  if (!prerequisites.git) {
    result.errors.push("Git is required");
  }

  if (!skipNpm && prerequisites.node) {
    for (const pkg of npmPackages) {
      result.npmPackages.push(await installNpmPackage(pkg, runCommandFn));
    }
  }

  if (!skipBun) {
    if (!prerequisites.bun) {
      result.errors.push(
        "Bun is not installed; skipped Bun package installation",
      );
    } else {
      await getBunVersionFn();
      for (const pkg of bunPackages) {
        result.bunPackages.push(await installBunPackage(pkg, runCommandFn));
      }
    }
  }

  if (!skipRepos && prerequisites.git) {
    for (const repo of repos) {
      result.repos.push(
        await ensureRepo(repo.name, repo.url, repo.dir, runCommandFn),
      );
    }
  }

  return result;
}
