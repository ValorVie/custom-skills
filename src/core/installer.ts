import { access, mkdir } from "node:fs/promises";
import { dirname, join } from "node:path";

import { BUN_PACKAGES, NPM_PACKAGES, REPOS } from "../utils/shared";
import { commandExists, getBunVersion, runCommand } from "../utils/system";

export interface InstallOptions {
  skipNpm?: boolean;
  skipBun?: boolean;
  skipRepos?: boolean;
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
): Promise<InstallItemResult> {
  const result = await runCommand(["npm", "install", "-g", packageName], {
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
): Promise<InstallItemResult> {
  const result = await runCommand(["bun", "install", "-g", packageName], {
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
  const result = await runCommand(["git", "clone", repoUrl, repoDir], {
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
  const skipNpm = options.skipNpm ?? false;
  const skipBun = options.skipBun ?? false;
  const skipRepos = options.skipRepos ?? false;

  const prerequisites = {
    node: commandExists("node"),
    git: commandExists("git"),
    bun: commandExists("bun"),
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
    for (const pkg of NPM_PACKAGES) {
      result.npmPackages.push(await installNpmPackage(pkg));
    }
  }

  if (!skipBun) {
    if (!prerequisites.bun) {
      result.errors.push(
        "Bun is not installed; skipped Bun package installation",
      );
    } else {
      await getBunVersion();
      for (const pkg of BUN_PACKAGES) {
        result.bunPackages.push(await installBunPackage(pkg));
      }
    }
  }

  if (!skipRepos && prerequisites.git) {
    for (const repo of REPOS) {
      result.repos.push(await ensureRepo(repo.name, repo.url, repo.dir));
    }
  }

  return result;
}
