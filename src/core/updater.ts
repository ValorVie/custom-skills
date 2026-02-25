import { access } from "node:fs/promises";
import { join } from "node:path";

import { BUN_PACKAGES, NPM_PACKAGES, REPOS } from "../utils/shared";
import { commandExists, runCommand } from "../utils/system";

type RepoConfig = (typeof REPOS)[number];

export interface UpdateDependencies {
  commandExistsFn?: typeof commandExists;
  runCommandFn?: typeof runCommand;
  accessFn?: typeof access;
  npmPackages?: readonly string[];
  bunPackages?: readonly string[];
  repos?: readonly RepoConfig[];
}

export interface UpdateOptions {
  skipNpm?: boolean;
  skipBun?: boolean;
  skipRepos?: boolean;
  deps?: UpdateDependencies;
  onProgress?: (message: string) => void;
}

export interface UpdateItemResult {
  name: string;
  success: boolean;
  message?: string;
}

export interface UpdateResult {
  npmPackages: UpdateItemResult[];
  bunPackages: UpdateItemResult[];
  repos: UpdateItemResult[];
  errors: string[];
}

export async function runUpdate(
  options: UpdateOptions = {},
): Promise<UpdateResult> {
  const deps = options.deps ?? {};
  const skipNpm = options.skipNpm ?? false;
  const skipBun = options.skipBun ?? false;
  const skipRepos = options.skipRepos ?? false;
  const commandExistsFn = deps.commandExistsFn ?? commandExists;
  const runCommandFn = deps.runCommandFn ?? runCommand;
  const accessFn = deps.accessFn ?? access;
  const npmPackages = deps.npmPackages ?? NPM_PACKAGES;
  const bunPackages = deps.bunPackages ?? BUN_PACKAGES;
  const repos = deps.repos ?? REPOS;
  const onProgress = options.onProgress ?? (() => {});

  const result: UpdateResult = {
    npmPackages: [],
    bunPackages: [],
    repos: [],
    errors: [],
  };

  if (!skipNpm) {
    if (!commandExistsFn("npm")) {
      result.errors.push("npm is not installed");
    } else {
      for (const pkg of npmPackages) {
        onProgress(`Updating npm package: ${pkg}...`);
        const updateResult = await runCommandFn(["npm", "install", "-g", pkg], {
          check: false,
          timeoutMs: 60_000,
        });
        result.npmPackages.push({
          name: pkg,
          success: updateResult.exitCode === 0,
          message:
            updateResult.exitCode === 0 ? undefined : updateResult.stderr,
        });
      }
    }
  }

  if (!skipBun) {
    if (!commandExistsFn("bun")) {
      result.errors.push("bun is not installed");
    } else {
      for (const pkg of bunPackages) {
        onProgress(`Updating bun package: ${pkg}...`);
        const updateResult = await runCommandFn(["bun", "install", "-g", pkg], {
          check: false,
          timeoutMs: 60_000,
        });
        result.bunPackages.push({
          name: pkg,
          success: updateResult.exitCode === 0,
          message:
            updateResult.exitCode === 0 ? undefined : updateResult.stderr,
        });
      }
    }
  }

  if (!skipRepos) {
    for (const repo of repos) {
      try {
        await accessFn(join(repo.dir, ".git"));
      } catch {
        result.repos.push({
          name: repo.name,
          success: false,
          message: "repository not found",
        });
        continue;
      }

      onProgress(`Updating repository: ${repo.name}...`);
      const updateResult = await runCommandFn(
        ["git", "-C", repo.dir, "pull", "--ff-only"],
        {
          check: false,
          timeoutMs: 60_000,
        },
      );
      result.repos.push({
        name: repo.name,
        success: updateResult.exitCode === 0,
        message: updateResult.exitCode === 0 ? undefined : updateResult.stderr,
      });
    }
  }

  return result;
}
